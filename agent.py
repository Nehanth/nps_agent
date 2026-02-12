"""NPS Agent — served via MLflow ResponsesAgent on RHOAI.

Endpoints (via app.sh → mlflow models serve):
    POST /invocations   query the agent
    GET  /ping          health check

Environment variables (set via OpenShift Secret / Deployment env):
    OPENAI_API_KEY          (required)
    NPS_API_KEY             (required)
    NPS_MCP_URL             default http://localhost:3005/mcp/
    MODEL_ID                default gpt-4o
    MLFLOW_TRACKING_URI     RHOAI MLflow endpoint
    MLFLOW_TRACKING_TOKEN   OpenShift auth token
    MLFLOW_WORKSPACE        RHOAI namespace
    MLFLOW_EXPERIMENT_NAME  default nps-agent
"""

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

import mlflow
from mlflow.models import set_model
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
)

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp

from observe.judge import evaluate_trace

# ---------------------------------------------------------------------------
# Configuration — all via env vars, zero code changes between local and RHOAI
# ---------------------------------------------------------------------------
NPS_MCP_URL = os.environ.get("NPS_MCP_URL", "http://localhost:3005/mcp/")
MODEL_ID = os.environ.get("MODEL_ID", "gpt-4o")

# MLflow tracing — no network calls at import time
# Reads MLFLOW_TRACKING_URI and MLFLOW_EXPERIMENT_NAME from env vars automatically
#
# RHOAI workspace header (no network call, just registers a header provider)
_workspace = os.environ.get("MLFLOW_WORKSPACE")
if _workspace:
    from mlflow.tracking.request_header.registry import _request_header_provider_registry
    from mlflow.tracking.request_header.abstract_request_header_provider import (
        RequestHeaderProvider,
    )

    if not any(
        "WorkspaceHeader" in type(p).__name__
        for p in _request_header_provider_registry
    ):

        class WorkspaceHeader(RequestHeaderProvider):
            def in_context(self):
                return True

            def request_headers(self):
                return {"X-Mlflow-Workspace": os.environ["MLFLOW_WORKSPACE"]}

        _request_header_provider_registry.register(WorkspaceHeader)

AGENT_INSTRUCTIONS = (
    "You are a helpful National Parks Service assistant. "
    "Use the available tools to answer questions about national parks, "
    "events, activities, campgrounds, and visitor information."
)


# ---------------------------------------------------------------------------
# Core agent logic
# ---------------------------------------------------------------------------
async def run_nps_agent(prompt: str, model: str = MODEL_ID) -> str:
    """Run the NPS agent with MCP tools and return the text response."""
    async with MCPServerStreamableHttp(params={"url": NPS_MCP_URL}) as mcp_server:
        agent = Agent(
            name="NPS Agent",
            model=model,
            instructions=AGENT_INSTRUCTIONS,
            mcp_servers=[mcp_server],
        )
        result = await Runner.run(agent, prompt)
        return result.final_output


# ---------------------------------------------------------------------------
# MLflow ResponsesAgent — turns the agent into an HTTP API
# ---------------------------------------------------------------------------
class NPSResponsesAgent(ResponsesAgent):
    """NPS Agent served via MLflow. Auto-traced + auto-evaluated."""

    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        user_message = self._extract_user_message(request)
        try:
            result = asyncio.run(run_nps_agent(user_message))
        except Exception as e:
            result = f"Error: {e}"

        response = ResponsesAgentResponse(
            output=[self.create_text_output_item(text=result, id="msg_1")]
        )

        # Auto-evaluate with Agent-as-a-Judge
        try:
            traces = mlflow.search_traces(
                order_by=["timestamp_ms DESC"],
                max_results=1,
                return_type="list",
            )
            if traces:
                evaluate_trace(traces[0])
        except Exception as e:
            print(f"Judge evaluation skipped: {e}")

        return response

    @staticmethod
    def _extract_user_message(request: ResponsesAgentRequest) -> str:
        for item in reversed(request.input):
            if hasattr(item, "role") and item.role == "user":
                content = item.content
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    return " ".join(
                        c.text for c in content if hasattr(c, "text")
                    )
        return ""


# ---------------------------------------------------------------------------
# MLflow model registration (required by mlflow models serve)
# ---------------------------------------------------------------------------
mlflow.openai.autolog()
agent = NPSResponsesAgent()
set_model(agent)
