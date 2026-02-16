"""Agent-as-a-Judge — outer-loop evaluation for deployed NPS Agent.

Runs after every request to auto-evaluate the agent's response and log
feedback to MLflow. Same `make_judge` pattern as 1_develop/2_evaluate.ipynb
but executed per-request rather than in a batch evaluation run.
"""

import os
from typing import Literal

import mlflow
from mlflow.entities import AssessmentSource, AssessmentSourceType
from mlflow.genai.judges import make_judge

JUDGE_MODEL = os.environ.get(
    "JUDGE_MODEL",
    f"openai:/{os.environ.get('OPENAI_MODEL_NAME', 'gpt-4o')}",
)


def create_judge():
    """Create the Agent-as-a-Judge scorer."""
    return make_judge(
        name="nps_agent_evaluator",
        model=JUDGE_MODEL,
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
    )


def evaluate_trace(trace):
    """Run Agent-as-a-Judge evaluation and log feedback to MLflow."""
    judge = create_judge()
    feedback = judge(trace=trace)

    mlflow.log_feedback(
        trace_id=trace.info.trace_id,
        name="nps_agent_evaluation",
        value=feedback.value,
        rationale=feedback.rationale,
        source=AssessmentSource(
            source_type=AssessmentSourceType.LLM_JUDGE,
            source_id=f"agent-as-a-judge/{JUDGE_MODEL}",
        ),
    )
    return feedback
