import asyncio
import os

import mlflow
from agents import Agent, Runner
from agents.mcp import MCPServerSse
from mlflow.models import set_model
from mlflow.pyfunc import ResponsesAgent
from mlflow.types.responses import ResponsesAgentRequest, ResponsesAgentResponse

mlflow.openai.autolog()

NPS_MCP_URL = os.environ.get("NPS_MCP_URL", "http://localhost:3005/sse/")
MODEL_ID = os.environ.get("OPENAI_MODEL_NAME", "gpt-4o-mini")

AGENT_INSTRUCTIONS = (
    "You are a helpful National Parks Service assistant. "
    "Use the available tools to answer questions about national parks, "
    "events, activities, campgrounds, and visitor information. "
)


async def run_nps_agent(prompt: str) -> str:
    """Run the NPS agent with MCP tools and return the text response."""
    async with MCPServerSse(params={"url": NPS_MCP_URL}) as mcp_server:
        agent = Agent(
            name="NPS Agent",
            instructions=AGENT_INSTRUCTIONS,
            mcp_servers=[mcp_server],
            model=MODEL_ID,
        )
        result = await Runner.run(agent, prompt)
        return result.final_output


# ---------------------------------------------------------------------------
# MLflow ResponsesAgent — wraps the agent into an HTTP API for deployment
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
                    return " ".join(c.text for c in content if hasattr(c, "text"))
        return ""


set_model(NPSResponsesAgent())
