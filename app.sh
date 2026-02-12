#!/bin/bash
# Entry point — starts MCP server + agent
# Traces go to MLFLOW_TRACKING_URI (RHOAI or local)

set -e

PORT="${PORT:-8080}"
HOST="${HOST:-0.0.0.0}"
MCP_PORT="${MCP_PORT:-3005}"
PYTHON="${PYTHON:-python3}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load .env if present
if [ -f "$SCRIPT_DIR/.env" ]; then
    set -a
    source "$SCRIPT_DIR/.env"
    set +a
fi

# Start MCP server in background
echo "Starting MCP server on :$MCP_PORT"
$PYTHON nps_mcp_server.py --transport sse --port "$MCP_PORT" &
MCP_PID=$!
sleep 2

# Package agent.py into a temp dir (instant, no network)
MODEL_DIR=$(mktemp -d)

$PYTHON -c "
import mlflow
mlflow.pyfunc.save_model(python_model='agent.py', path='$MODEL_DIR')
"

echo "Traces:    ${MLFLOW_TRACKING_URI:-(not set)}"
echo "Listening: http://$HOST:$PORT"

exec mlflow models serve \
    -m "$MODEL_DIR" \
    -p "$PORT" \
    --host "$HOST" \
    --env-manager local
