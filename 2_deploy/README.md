# Deploy

Walks through the agent deployment journey with MLflow.

Shows how to deploy an agent in MLflow, inference against it, and view traces.

- The viewer learns how to containerize their agent and deploy it onto OpenShift with the right environment, variable set so that it knows how to talk to the MLflow instance running in RHOAI.  (note that there are a lot of plans to add new features to RHOAI to provide an agent-specific deployment mechanism but since none of that exists for now it would stay out of this version of the demo -- in a few months we'd probably want to re-record the demo with this part of it overhauled to show off all the newest technology).
- The viewer sees at least one sample request sent to that deployed agent.