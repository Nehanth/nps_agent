import logging
import os
from typing import Literal

import mlflow
from dotenv import load_dotenv
from mlflow import MlflowClient
from mlflow.genai import evaluate
from mlflow.entities import AssessmentSource, AssessmentSourceType
from mlflow.genai.judges import make_judge
from mlflow.genai.scorers import RelevanceToQuery, ToolCallEfficiency

logger = logging.getLogger(__name__)

def search_traces(experiment_ids: list[str], max_traces: int, filter_string: str):
    logging.info("Searching traces: experiment_ids=%s, filter=%s, max_results=%s", experiment_ids, filter_string, max_traces)
    traces = mlflow.search_traces(
        experiment_ids=[experiment_ids],
        filter_string=filter_string,
        max_results=max_traces,
        order_by=["trace.timestamp_ms DESC"],
    )

    if traces is None or traces.empty:
        logging.warning("No traces found. Run the agent and generate some traffic, then re-run.")
        return
    else:
        return traces

def create_judge():
    """Create the Agent-as-a-Judge scorer."""
    judge_model = os.getenv("JUDGE_MODEL","openai:/gpt-4o")
    nps_evaluator = make_judge(
        name="nps_agent_evaluator",
        instructions=(
            "Evaluate the NPS agent's performance in {{ trace }}.\n\n"
            "Check for:\n"
            "1. Response Quality: Did the agent correctly identify parks "
            "and provide accurate information?\n"
            "2. Tool Usage: Were the correct NPS MCP tools used "
            "(search_parks, get_park_events, etc.)?\n"
            "3. Completeness: Did the agent answer all parts of the "
            "user's question?\n\n"
            "Rate as: 'good', 'acceptable', or 'poor'"
        ),
        feedback_value_type=Literal["good", "acceptable", "poor"],
        model=judge_model,
    )
    return nps_evaluator

def get_evaluation_scorers():
    """Build list of scorers: custom NPS judge + built-in RelevanceToQuery and ToolCallEfficiency."""
    judge_model = os.getenv("JUDGE_MODEL", "openai:/gpt-4o")
    return [
        create_judge(),
        RelevanceToQuery(model=judge_model),
        ToolCallEfficiency(model=judge_model),
    ]

def evaluate_traces(traces):
    scorers = get_evaluation_scorers()
    results = evaluate(data=traces, scorers=scorers)
    logger.info("Evaluation results: %s", results.metrics)
    if "eval_results_table" in results.tables:
        logger.info("Eval results table:\n%s", results.tables["eval_results_table"].to_string())

def _register_mlflow_workspace_header() -> None:
    """Register RHOAI workspace header so all MLflow requests use the workspace from env."""
    _workspace = os.getenv("MLFLOW_WORKSPACE")
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

def main() -> None:
    """Load environment variables"""
    load_dotenv()

    """Connect to MLflow (with workspace from .env if MLFLOW_WORKSPACE is set)"""
    _register_mlflow_workspace_header()
    client = MlflowClient()
    exp_name = os.getenv("MLFLOW_EXPERIMENT_NAME")
    experiment = client.get_experiment_by_name(exp_name)
    if not experiment:
        raise SystemExit(f"Experiment '{exp_name}' not found. Create it or set MLFLOW_EXPERIMENT_NAME.")
    experiment_id = experiment.experiment_id

    """Search for traces"""
    traces = search_traces(experiment_id, 5, "trace.status = 'OK'")

    """Evaluate traces by creating Agent-as-a-Judge scorer"""
    evaluate_traces(traces)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    main()