# LLM comparison: qwen3:8b vs qwen3:4b

**Question:** can a smaller local model run the investigator agent faster and cheaper?

**Setup:** the same LangGraph agent, prompt and tools, run on 3 fixed cases (card testing, foreign ATM withdrawal, normal payment) with `make compare-llms`. Both models run locally with Ollama on a MacBook Air M5 (24 GB). Every run is logged to MLflow (experiment `llm-comparison`), together with its report.

Cost is an **estimate** of what the same tokens would cost on a paid API (illustrative rates: $0.15 per 1M input tokens, $0.60 per 1M output tokens). Running locally costs nothing.

## Results (mean of 3 cases)

| Model | Seconds | Input tokens | Output tokens | Used policy search | Est. cost per case |
|---|---|---|---|---|---|
| qwen3:8b | **26.6** | 3,559 | **555** | **3 / 3** | **$0.0009** |
| qwen3:4b | 159.0 | 4,290 | 4,128 | 1 / 3 | $0.0031 |

## Findings

- **The smaller model was 6× slower.** It is faster per token, but it produced 7× more output tokens: it leaked its reasoning even with reasoning off, and lost track of the agent loop.
- **Quality:** qwen3:4b skipped the policy search in 2 of 3 cases, so its reports cite no rules.
- **qwen3:8b still hallucinates:** in the card-testing case it cited R4 (structuring) for payments of about 1 EGP, but R4 is about payments just below 10,000 EUR. The evaluation harness (next task) checks for this.
- **The guardrail worked:** when a model sent a malformed account ID, the tool rejected it and the model corrected itself.

## Decision

Keep **qwen3:8b**. Compare models per completed task (latency, tokens, cost and quality together), not on model size or per-token speed.

Limitation: 3 cases, 1 run each. Enough to show a clear gap, not to measure small differences.
