# Develop

Walks through the agent development process alongside MLflow.

Shows basic tracing, autologging, instrumenting an agent, and performing/storing inner loop evaluations.

- The viewer learns how to install MLflow and access the UI running locally.
- The viewer learns how to instrument their agent for MLflow using any of the following:
  - Auto logging via the MLflow tracing SDK
  - Manually logging specific events via the MLflow tracing SDK
  - Manually logging specific events via the OTEL SDK(and the user has some sense of the pros and cons of these three options)
- The viewer learns how to set up an AaaJ with either a generic AaaJ prompt or a specific one designed for their agent.
- The viewer learns how to run an experiment locally ("inner loop eval") using one of those AaaJ's.
- The viewer learns how to navigate the MLflow UI, find the traces for an experiment, and view the results of the AaaJ. They see enough of the results to understand why an AaaJ is useful and what kind of insights they might get about their agent from this technology.