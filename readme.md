# MLflow Developer Experience on RHOAI

Want to learn how to take your agent from development to production with MLflow?
Look no further, for this repo has you covered.
By following along with the tutorials in this repo, you will learn how to:

- Instrument an agent for full observability over each action it takes
- Evaluate an agent in development, to get insights about its performance and catch errors before reach your users
- Deploy an agent to production and inference against it
- Observe and evaluate an agent's performance in production, to catch changes in agent behavior or data drift

## Quick Start

### 1. Install uv (if not already installed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Create virtual environment and install dependencies

```bash
cd nps_agent
uv venv --python 3.12
uv pip install -r requirements.txt
```

> **Note:** Python 3.10+ is required. Use `--python 3.12` (or 3.10, 3.11) to specify the version.

### 3. Set up environment variables

```bash
cp env.sample .env
# Edit .env with your API keys and settings
```

### 4. Activate the environment

```bash
source .venv/bin/activate
```

You're now ready to follow any of the tutorials below!

## Prerequisites

For the develop step, you will need to have the following:
- An OpenAI-compatible endpoint from your local machine, e.g. OpenAI, vLLM, llama.cpp, Ollama, etc.
- Space on your device to run a local MLflow server (~5 MB)
- RHOAI version a.b.c or later, with the MLflow server enabled

For the deploy and observe steps, you will need to have the following:
- An OpenAI-compatible endpoint accessible to your cluster, e.g. OpenAI, RHAIIS, vLLM, etc.
- RHOAI version a.b.c or later, with the MLflow server enabled

## Structure

This repo is split into three tutorials:

1. [**Develop**](./1_develop/README.md): Instrument an agent for observability and evaluate its performance.
2. [**Deploy**](./2_deploy/README.md): Deploy an agent to production and inference against it.
3. [**Observe**](./3_observe/README.md): Evaluate an agent's performance in production.

It is recommended that you follow these tutorials in order, but each one does stand on its own if you are only looking to learn more about a specific topic.
