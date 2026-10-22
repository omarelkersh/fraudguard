"""Compare two local LLMs as the investigator: latency, tokens and estimated API cost."""

import asyncio

import mlflow

from fraudguard_investigator.agent import investigate

MODELS = ["qwen3:8b", "qwen3:4b"]
CASES = {
    "card_testing": "24df6dcc-490c-4f97-ab0c-456b8ab20bf4",
    "foreign_atm": "fe7ee362-8a89-40f0-9052-91d3b34c6c73",
    "normal": "e97fb025-a2e1-4798-ab65-450b5c75352c",
}
# Illustrative paid-API prices in USD per 1M tokens (we pay nothing: models run locally).
PRICE_IN, PRICE_OUT = 0.15, 0.60


def estimated_cost(outcome: dict) -> float:
    return (outcome["input_tokens"] * PRICE_IN + outcome["output_tokens"] * PRICE_OUT) / 1_000_000


def main() -> None:
    mlflow.set_tracking_uri("http://localhost:5050")
    mlflow.set_experiment("llm-comparison")
    for model in MODELS:
        for case, transaction_id in CASES.items():
            outcome = asyncio.run(investigate(transaction_id, model))
            with mlflow.start_run(run_name=f"{model} {case}"):
                mlflow.log_params({"model": model, "case": case})
                mlflow.log_metrics(
                    {
                        "seconds": outcome["seconds"],
                        "input_tokens": outcome["input_tokens"],
                        "output_tokens": outcome["output_tokens"],
                        "used_policy": int("search_policy" in outcome["tool_calls"]),
                        "est_cost_usd": estimated_cost(outcome),
                    }
                )
                mlflow.log_text(outcome["report"], "report.md")
            print(model, case, outcome["seconds"], "s")


if __name__ == "__main__":
    main()
