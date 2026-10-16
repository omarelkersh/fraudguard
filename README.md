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
    D --> M[Fraud model API<br/>FastAPI + MLflow]
    M --> A[AI investigator agent<br/>LangGraph + MCP + RAG]
    A --> B[Dashboards]
```

## Status

| Phase | Scope | Status |
|---|---|---|
| 0 | Foundation: monorepo, tests, Docker, CI/CD | ✅ Done |
| 1 | Data platform: Kafka → Spark → Delta Lake → dbt | ✅ Done |
| 2 | ML + MLOps: MLflow, FastAPI, monitoring, A/B test | ⏳ Next |
| 3 | AI investigator: LangGraph, MCP, RAG, LLM evaluation | Planned |
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

## Quickstart

Prerequisites: [uv](https://docs.astral.sh/uv/) and [Docker](https://www.docker.com/).
Before the first run: `docker compose up -d storage`, then create a bucket named `lakehouse` at http://localhost:9001/rustfs/console/.

```bash
cp .env.example .env          # then set your own storage password
uv sync --all-packages        # install dependencies (exact versions from uv.lock)
make test                     # run the unit tests
make pipeline                 # Kafka → Spark → Delta → dbt, end to end
make down                     # stop everything
```

## Project structure

```
services/
  generator/          # synthetic transactions + fraud patterns → Kafka (Pydantic contract, tests)
  streaming/          # Spark Structured Streaming job: Kafka → Delta bronze table
pipelines/
  dbt/                # dbt staging + star schema with data-quality tests
compose.yaml          # local infrastructure (Kafka, S3 storage, generator, Spark)
Makefile              # one-command pipeline (make pipeline)
.github/workflows/    # CI pipeline
```

## Engineering practices

- **Data contracts:** every transaction is validated with Pydantic at the source (ID formats, positive amounts with 2 decimal places, timezone-aware timestamps), covered by 37 unit tests including boundary cases.
- **Data quality in the warehouse:** 8 dbt tests (not_null, unique, accepted_values, relationships); staging deduplicates Kafka's at-least-once deliveries.
- **Pre-commit hooks:** ruff linting and formatting plus file hygiene checks run automatically before every commit.
- **CI on every push and PR:** lint, format check, tests, and a Docker build that only runs once the tests pass.
- **Protected `main`:** changes land only via pull requests, and merging requires green CI. No direct pushes or force pushes.
- **Reproducible builds:** pinned dependencies (`uv.lock`), pinned CI actions, and Conventional Commits for a readable history.
