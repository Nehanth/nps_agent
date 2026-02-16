# Deploy NPS Agent to RHOAI

This directory contains everything needed to deploy the NPS Agent as an HTTP endpoint on **Red Hat OpenShift AI (RHOAI)** with MLflow tracing.

The agent logic is identical to the [Evaluate notebook](../1_develop/2_evaluate.ipynb) — we just wrap it in an MLflow `ResponsesAgent` for serving.

<<<<<<< HEAD
=======
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

>>>>>>> origin/main
## Files

| File | Purpose |
|---|---|
<<<<<<< HEAD
| [`deploy.ipynb`](./deploy.ipynb) | Step-by-step deployment notebook |
| [`npsagent.py`](./npsagent.py) | Agent + MLflow `ResponsesAgent` wrapper for HTTP serving |
| [`nps_mcp_server.py`](./nps_mcp_server.py) | FastMCP server exposing NPS API tools (spawned on-demand per request) |
| [`app.sh`](./app.sh) | Container entry point — packages the agent and starts `mlflow models serve` |
| [`requirements.txt`](./requirements.txt) | Python dependencies for the s2i build |
| [`nps-agent.yaml`](./nps-agent.yaml) | OpenShift Template (BuildConfig, Deployment, Service, Route) |
| [`.s2i/environment`](./.s2i/environment) | Tells s2i to use `app.sh` as the startup script |

## Prerequisites

- An OpenShift cluster with RHOAI and MLflow configured ([Cluster Setup Guide](https://docs.google.com/document/d/1ZzuGAY1gSamOLsznwbaL7xFkJ1JjHWpnyjk0tV12YVg/edit?tab=t.0#heading=h.jgt5ddlrwyvc))
- The `oc` CLI installed and logged in
- A `.env` file in the repo root with:
  ```
  OPENAI_API_KEY=...
  OPENAI_BASE_URL=https://api.openai.com/v1
  OPENAI_MODEL_NAME=gpt-4o-mini
  NPS_API_KEY=...
  MLFLOW_TRACKING_URI=https://data-science-gateway.apps.<cluster>/mlflow/
  ```

## Quick Start

Open [`deploy.ipynb`](./deploy.ipynb) and run through the steps:

1. **Create an OpenShift project** — `oc new-project nps-agent-<yourname>`
2. **Create secrets** — pushes API keys as an OpenShift Secret
3. **Apply the template** — `oc process` creates all resources in one shot
4. **Wait for the build** — s2i clones the repo, installs deps, builds the image
5. **Set the MLflow auth token** — injects your `oc` token for trace routing
6. **Verify the pod** — check it's `Running`
7. **Get the route URL** — grab the public HTTPS endpoint
8. **Test the agent** — send a question to `POST /invocations`
9. **View traces** — open the MLflow UI to see auto-traced LLM calls and tool invocations

See [`deploy.ipynb`](./deploy.ipynb) for the full walkthrough, architecture details, and rebuild/cleanup instructions.
=======
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
>>>>>>> origin/main
