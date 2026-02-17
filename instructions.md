# Deploy NPS Agent to RHOAI

## Prerequisites

- OpenShift cluster with RHOAI and MLflow
- `oc` CLI logged in
- An [OpenAI API key](https://platform.openai.com/api-keys)
- A [NPS API key](https://www.nps.gov/subjects/developer/get-started.html)

## Step 1 — Create an OpenShift project

Use `nps-agent-<yourname>` to avoid conflicts with other users on the same cluster.

```bash
oc new-project nps-agent-<yourname>
```

## Step 2 — Create the Secret with API keys

```bash
source .env
oc create secret generic nps-agent-secrets \
  --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
  --from-literal=NPS_API_KEY="$NPS_API_KEY" \
  -n nps-agent-<yourname>
```

## Step 3 — Configure environment and update nps-agent.yaml

### 3.1 Create your local .env file (optional, for local development)

Copy the sample environment file and update it with your values:

```bash
cp env.sample .env
```

Edit `.env` with your actual values:

| Variable | What to set | Example |
|---|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-proj-...` |
| `OPENAI_BASE_URL` | OpenAI-compatible endpoint URL | `https://api.openai.com/v1` |
| `OPENAI_MODEL_NAME` | Model name to use | `gpt-4o or any other model` |
| `NPS_API_KEY` | Your NPS API key | From [NPS Developer Portal](https://www.nps.gov/subjects/developer/get-started.html) |
| `MLFLOW_TRACKING_URI` | Your RHOAI MLflow URL | `https://data-science-gateway.apps.<cluster>/mlflow/` |
| `MLFLOW_WORKSPACE` | Your OpenShift project name | `nps-agent-<yourname>` |
| `MLFLOW_EXPERIMENT_NAME` | Experiment name in MLflow | `nps-agent` |
| `MLFLOW_EXPERIMENT_ID` | Experiment ID in MLflow | `0` (default experiment) |
| `MLFLOW_TRACKING_AUTH` | MLflow auth method | `kubernetes` (for RHOAI) |
| `OPENSHIFT_NAMESPACE` | Your OpenShift project name | `nps-agent-<yourname>` |
| `IMAGE_REGISTRY` | OpenShift image registry | `image-registry.openshift-image-registry.svc:5000` |

### 3.2 Update nps-agent.yaml with your cluster values

Replace the following placeholders in `nps-agent.yaml`:

| Placeholder | What to replace with | Example |
|---|---|---|
| `<NAMESPACE>` | Your OpenShift project name | `nps-agent-<yourname>` |
| `<MLFLOW_TRACKING_URI>` | Your RHOAI MLflow URL | `https://data-science-gateway.apps.rosa.xxxxx.openshiftapps.com/mlflow/` |
| `<MLFLOW_WORKSPACE>` | Your OpenShift project name (typically same as namespace) | `nps-agent-<yourname>` |
| `<MLFLOW_EXPERIMENT_NAME>` | Experiment name in MLflow | `nps-agent` |

You can use a find-and-replace or use `sed`:

```bash
# Example using sed (update values as needed)
sed -i.bak \
  -e 's|<NAMESPACE>|nps-agent-<yourname>|g' \
  -e 's|<MLFLOW_TRACKING_URI>|https://data-science-gateway.apps.YOUR-CLUSTER/mlflow/|g' \
  -e 's|<MLFLOW_WORKSPACE>|nps-agent-<yourname>|g' \
  -e 's|<MLFLOW_EXPERIMENT_NAME>|nps-agent|g' \
  nps-agent.yaml
```

## Step 4 — Apply the manifests

The `nps-agent.yaml` is an OpenShift Template that reads your environment variables automatically:

```bash
oc apply -f nps-agent.yaml -n nps-agent-<yourname>
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
oc logs -f build/nps-agent-1 -n nps-agent-<yourname>
```

Once it says `Push successful`, the image is ready.

## Step 6 — Set the MLflow auth token

The RHOAI Data Science Gateway requires an auth token. Set it from your current `oc` session:

```bash
oc set env deployment/nps-agent \
  MLFLOW_TRACKING_TOKEN="$(oc whoami -t)" \
  -n nps-agent-<yourname>
```

> **Note:** `oc` tokens expire. Refresh with the same command when needed.

## Step 7 — Verify the pod is running

```bash
oc get pods -n nps-agent-<yourname>
```

You should see:

```
NAME                         READY   STATUS    RESTARTS   AGE
nps-agent-xxxxxxxxx-xxxxx    1/1     Running   0          60s
```

## Step 8 — Get the route URL

```bash
oc get route nps-agent -n nps-agent-<yourname> -o jsonpath='{.spec.host}'
```

## Step 9 — Test the agent

```bash
ROUTE=$(oc get route nps-agent -n nps-agent-<yourname> -o jsonpath='{.spec.host}')

curl -s -X POST "https://$ROUTE/invocations" \
  -H "Content-Type: application/json" \
  -d '{"input": [{"role": "user", "content": "What national parks are in California?"}]}' \
  | python3 -m json.tool
```

## Step 10 — View traces in MLflow

Open your RHOAI MLflow UI and navigate to the `nps-agent` experiment. Every request is auto-traced and auto-evaluated by the Agent-as-a-Judge.

## Rebuilding after code changes

Push changes to the `deploy` branch, then:

```bash
oc start-build nps-agent -n nps-agent-<yourname>
oc logs -f build/nps-agent-2 -n nps-agent-<yourname>
```

The Deployment will automatically pick up the new image.

## How to delete and restart from scratch

```bash
oc delete project nps-agent-<yourname>
```

Wait for the project to fully terminate, then start over from Step 1.
