# Deploy NPS Agent to RHOAI

## Prerequisites

- OpenShift cluster with RHOAI and MLflow
- `oc` CLI logged in
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [NPS API key](https://www.nps.gov/subjects/developer/get-started.htm)
- Your MLflow tracking route URL

## Step 1 — Create an OpenShift project

> Use `nps-agent-[yourname]` to avoid conflicts with other users on the same cluster.

```bash
oc new-project nps-agent-[yourname]
```

## Step 2 — Create the Secret with API keys

```bash
oc create secret generic nps-agent-secrets \
  --from-literal=OPENAI_API_KEY='your-openai-key' \
  --from-literal=NPS_API_KEY='your-nps-key' \
  -n nps-agent-[yourname]
```

## Step 3 — Update nps-agent.yaml

Edit the env vars in `nps-agent.yaml` to match your cluster:

| Variable | What to set |
|---|---|
| `MLFLOW_TRACKING_URI` | Your MLflow tracking route URL |
| `MLFLOW_TRACKING_AUTH` | `kubernetes` (uses pod service account — no personal creds) |
| `MLFLOW_EXPERIMENT_ID` | Your MLflow experiment ID |
| `image` | Replace `nps-agent-[yourname]` with your actual project name |

## Step 4 — Apply the manifests

```bash
oc apply -f nps-agent.yaml -n nps-agent-nehanth
```

This creates:
- **BuildConfig** — s2i build from the `deploy` branch of this repo
- **ImageStream** — stores the built container image
- **Deployment** — runs the agent pod (MCP server + MLflow serve)
- **Service** — internal cluster networking
- **Route** — external HTTPS endpoint

## Step 5 — Wait for the s2i build

The BuildConfig triggers automatically. Watch the build:

```bash
oc logs -f build/nps-agent-1 -n nps-agent-nehanth
```

Once it says `Push successful`, the image is ready.

## Step 6 — Verify the pod is running

```bash
oc get pods -n nps-agent-nehanth
```

You should see:

```
NAME                         READY   STATUS    RESTARTS   AGE
nps-agent-xxxxxxxxx-xxxxx    1/1     Running   0          60s
```

## Step 7 — Get the route URL

```bash
oc get route nps-agent -n nps-agent-[yourname] -o jsonpath='{.spec.host}'
```

## Step 8 — Test the agent

```bash
ROUTE=$(oc get route nps-agent -n nps-agent-nehanth -o jsonpath='{.spec.host}')

curl -s -X POST "https://$ROUTE/invocations" \
  -H "Content-Type: application/json" \
  -d '{"input": [{"role": "user", "content": "What national parks are in California?"}]}' \
  | python3 -m json.tool
```

## Step 9 — View traces in MLflow

Open your RHOAI MLflow UI and navigate to your experiment. Every request is auto-traced and auto-evaluated by the Agent-as-a-Judge.

## Rebuilding after code changes

Push changes to the `deploy` branch, then:

```bash
oc start-build nps-agent -n nps-agent-[yourname]
oc logs -f build/nps-agent-2 -n nps-agent-[yourname]
```

The Deployment will automatically pick up the new image.

## How to delete and restart from scratch

```bash
oc delete project nps-agent-[yourname]
```

Wait for the project to fully terminate, then start over from Step 1.
