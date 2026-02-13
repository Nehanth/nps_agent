# Deploy

Walks through the agent deployment journey with MLflow.

Shows how to deploy an agent in MLflow, inference against it, and view traces.

- The viewer learns how to containerize their agent and deploy it onto OpenShift with the right environment, variable set so that it knows how to talk to the MLflow instance running in RHOAI.  (note that there are a lot of plans to add new features to RHOAI to provide an agent-specific deployment mechanism but since none of that exists for now it would stay out of this version of the demo -- in a few months we'd probably want to re-record the demo with this part of it overhauled to show off all the newest technology).
- The viewer sees at least one sample request sent to that deployed agent.



OLD README

# NPS Agent

An AI agent that answers questions about U.S. National Parks, deployed to Red Hat OpenShift AI via s2i with MLflow tracing and Agent-as-a-Judge evaluation.

## Architecture

```
curl POST /invocations
        │
        ▼
  MLflow ResponsesAgent  (agent.py — port 8080)
        │
        ▼
  OpenAI Agents SDK  ──►  OpenAI GPT-4o
        │
        ▼
  MCP Server  (nps_mcp_server.py — port 3005, same pod)
        │
        ▼
  NPS API  (search_parks, get_park_events, get_park_alerts, …)
        │
        ▼
  MLflow Tracing + Agent-as-a-Judge  ──►  RHOAI MLflow
```

## Files

| File | Purpose |
|---|---|
| `agent.py` | NPS agent + MLflow ResponsesAgent + Agent-as-a-Judge |
| `app.sh` | Entry point — starts MCP server + `mlflow models serve` |
| `nps_mcp_server.py` | MCP server exposing NPS API tools over SSE |
| `requirements.txt` | Python dependencies |
| `.s2i/environment` | s2i config (`APP_SCRIPT=app.sh`) |
| `nps-agent.yaml` | OpenShift manifests (BuildConfig, Deployment, Service, Route) |
| `instructions.md` | Step-by-step deployment guide |

## API

| Endpoint | Method | Description |
|---|---|---|
| `/invocations` | POST | Query the agent |
| `/ping` | GET | Health check |

**Request:**

```json
{
  "input": [
    {"role": "user", "content": "Tell me about parks in Rhode Island"}
  ]
}
```

**Response:**

```json
{
  "object": "response",
  "output": [
    {
      "type": "message",
      "id": "msg_1",
      "content": [{"text": "...", "type": "output_text"}],
      "role": "assistant"
    }
  ]
}
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `NPS_API_KEY` | Yes | NPS API key |
| `NPS_MCP_URL` | No | MCP server URL (default: `http://localhost:3005/sse/`) |
| `MODEL_ID` | No | OpenAI model (default: `gpt-4o`) |
| `JUDGE_MODEL` | No | Judge model (default: `openai:/gpt-4o`) |
| `MLFLOW_TRACKING_URI` | Yes | RHOAI MLflow endpoint |
| `MLFLOW_TRACKING_TOKEN` | Yes | OpenShift auth token |
| `MLFLOW_WORKSPACE` | Yes | RHOAI namespace |
| `MLFLOW_EXPERIMENT_NAME` | No | MLflow experiment (default: `nps-agent`) |

## Deploy

See [instructions.md](instructions.md) for the full step-by-step guide.
