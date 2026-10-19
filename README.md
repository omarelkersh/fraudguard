# FraudGuard

![CI](https://github.com/omarelkersh/fraudguard/actions/workflows/ci.yml/badge.svg)

A real-time financial-crime platform: banking transactions stream through Kafka and Spark into a lakehouse, a fraud model scores them, and an LLM-powered investigator agent explains suspicious activity.

This is a portfolio project, built in phases, to demonstrate production-style data engineering, MLOps and AI engineering end to end: stream processing, data quality, model deployment and monitoring, AI agents with tool calling, and cloud infrastructure as code. Each phase is runnable on its own.

## Architecture

Target architecture (see [Status](#status) for what's built so far):

```mermaid
flowchart LR
    G[Transaction generator] --> K[(Kafka)]
    K --> S[Spark Structured Streaming]
    S --> L[(Delta Lake on RustFS)]
    L --> D[dbt models]
    D --> M[Fraud model API<br/>FastAPI + MLflow<br/>Prometheus + Grafana]
    M --> A[AI investigator agent<br/>LangGraph + MCP + RAG]
    A --> B[Dashboards]
```

## Status

| Phase | Scope | Status |
|---|---|---|
| 0 | Foundation: monorepo, tests, Docker, CI/CD | ✅ Done |
| 1 | Data platform: Kafka → Spark → Delta Lake → dbt | ✅ Done |
| 2 | ML + MLOps: MLflow, FastAPI, monitoring, A/B test | ✅ Done |
| 3 | AI investigator: LangGraph, MCP, RAG, LLM evaluation | ⏳ Next |
| 4 | Cloud: Kubernetes, Terraform, Azure | Planned |
| 5 | Analytics dashboards | Planned |

## Tech stack (so far)

- **Python 3.12** with **uv** workspaces: one monorepo, one lockfile, one package per service
- **Pydantic v2**: transaction data contract with validation at the source
- **pytest** for unit tests; **ruff** for linting and formatting; **pre-commit** hooks
- **Docker** (non-root, cache-friendly layered images) and **Docker Compose**
- **Apache Kafka 4.3** in KRaft mode (no ZooKeeper)
- **GitHub Actions** CI: lint, format check, tests and image build on every push and PR
- **Spark 4.1 Structured Streaming**: Kafka → Delta bronze table, checkpointed (exactly-once)
- **Delta Lake** on **RustFS** (S3-compatible object storage)
- **dbt + DuckDB**: staging and star schema with data-quality tests
- **Make**: one-command pipeline
- **scikit-learn + MLflow 3**: experiment tracking, model registry with `champion` / `challenger` aliases
- **FastAPI**: scoring microservice loading the champion model from MLflow
- **Prometheus + Grafana**: API metrics and a dashboard provisioned as code (throughput, fraud rate, p95 latency)
- **Drift monitoring** with a tested PSI implementation; **A/B testing** with a two-proportion z-test

## Quickstart

Prerequisites: [uv](https://docs.astral.sh/uv/) and [Docker](https://www.docker.com/).
Before the first run: `docker compose up -d storage`, then create a bucket named `lakehouse` at http://localhost:9001/rustfs/console/.

```bash
cp .env.example .env          # then set your own storage password
uv sync --all-packages        # install dependencies (exact versions from uv.lock)
make test                     # run the unit tests
make pipeline                 # Kafka → Spark → Delta → dbt, end to end
docker compose up -d mlflow   # MLflow UI at http://localhost:5050
make train && make promote    # train a model, give the best version the champion alias
docker compose up -d --build scoring-api prometheus grafana
                              # API docs: http://localhost:8000/docs
                              # dashboard: http://localhost:3000/d/fraudguard-api
make drift                    # PSI drift check (exits 1 on significant drift)
make challenger && make ab-test   # train a challenger and run the A/B test
make down                     # stop everything
```

The A/B test result and decision are written up in [docs/ab_test.md](docs/ab_test.md).

## Project structure

```
services/
  generator/          # synthetic transactions + fraud patterns → Kafka (Pydantic contract, tests)
  streaming/          # Spark Structured Streaming jobs: Kafka → Delta bronze tables
  scoring-api/        # FastAPI scoring service with Prometheus metrics (tests use a fake model)
pipelines/
  dbt/                # dbt staging, star schema and ML training set with data-quality tests
ml/                   # training, model promotion, drift check (PSI), A/B test
infra/                # Prometheus config, Grafana datasource + dashboard as code
docs/                 # A/B test write-up
compose.yaml          # local stack: Kafka, S3 storage, Spark, MLflow, API, Prometheus, Grafana
Makefile              # one-command pipeline and ML workflow
.github/workflows/    # CI pipeline
```

## Engineering practices

- **Data contracts:** every transaction is validated with Pydantic at the source (ID formats, positive amounts with 2 decimal places, timezone-aware timestamps), covered by unit tests including boundary cases (42 tests across the repo).
- **No label leakage:** fraud labels arrive on a separate topic, days later (chargebacks); features are point-in-time correct and models are evaluated on a time-based split with PR-AUC.
- **Data quality in the warehouse:** 12 dbt tests (not_null, unique, accepted_values, relationships); staging deduplicates Kafka's at-least-once deliveries.
- **Pre-commit hooks:** ruff linting and formatting plus file hygiene checks run automatically before every commit.
- **CI on every push and PR:** lint, format check, tests, and a Docker build that only runs once the tests pass.
- **Protected `main`:** changes land only via pull requests, and merging requires green CI. No direct pushes or force pushes.
- **Reproducible builds:** pinned dependencies (`uv.lock`), pinned CI actions, and Conventional Commits for a readable history.
