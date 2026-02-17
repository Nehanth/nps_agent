import asyncio
import os

import nest_asyncio
nest_asyncio.apply()

from dotenv import load_dotenv
load_dotenv()

import mlflow
from mlflow.models import set_model
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse

from openai import AsyncClient
from agents import Agent, Runner
from agents.mcp import MCPServerStdio
from agents import set_default_openai_client, set_default_openai_api, set_tracing_disabled

# ---------------------------------------------------------------------------
# Create an NPS Agent  (same pattern as 1_develop/2_evaluate.ipynb)
# ---------------------------------------------------------------------------
AGENT_INSTRUCTIONS = (
    "You are a helpful National Parks Service assistant. "
    "Use the available tools to answer questions about national parks, "
    "events, activities, campgrounds, and visitor information. "
)


async def run_nps_agent(prompt: str) -> str:
    """Run the NPS agent with MCP tools and return the text response."""
    command = "uv"
    args = ["run", "fastmcp", "run", "./nps_mcp_server.py"]
    env = {**os.environ, "NPS_API_KEY": os.environ.get("NPS_API_KEY", "")}
    async with MCPServerStdio(params={"command": command, "args": args, "env": env}) as mcp_server:
        # Configure OpenAI-compatible endpoint
        async_client = AsyncClient(
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            api_key=os.environ.get("OPENAI_API_KEY", ""),
        )
        set_default_openai_client(client=async_client)
        set_default_openai_api("chat_completions")
        set_tracing_disabled(disabled=True)

        # Create the agent
        agent = Agent(
            name="NPS Agent",
            instructions=AGENT_INSTRUCTIONS,
            mcp_servers=[mcp_server],
            model=os.environ.get("OPENAI_MODEL_NAME", "gpt-4o"),
        )

        # Run the agent
        result = await Runner.run(agent, prompt)
        return result.final_output


# ---------------------------------------------------------------------------
# MLflow ResponsesAgent — wraps run_nps_agent into an HTTP API for deployment
# ---------------------------------------------------------------------------
class NPSResponsesAgent(ResponsesAgent):
    def predict(self, request: ResponsesAgentRequest) -> ResponsesAgentResponse:
        user_message = self._extract_user_message(request)
        try:
            result = asyncio.run(run_nps_agent(user_message))
        except Exception as e:
            result = f"Error: {e}"
        return ResponsesAgentResponse(
            output=[self.create_text_output_item(text=result, id="msg_1")]
        )

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
# MLflow model registration
# ---------------------------------------------------------------------------
mlflow.openai.autolog()
set_model(NPSResponsesAgent())
