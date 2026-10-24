"""Score the base model (rules in the prompt) and the LoRA adapter (facts only) on the test set."""

import json
import re
import time
from pathlib import Path

import mlflow
from mlx_lm import generate, load

BASE = "mlx-community/Qwen3-1.7B-4bit"
RULES = (
    "Policy: R1 card testing = online payment under 5 with more than 5 payments in 10 minutes. "
    "R2 foreign ATM = ATM withdrawal outside the home country, more than 5 times the typical "
    "amount. Answer with exactly two lines: 'Verdict: suspicious' or 'Verdict: not suspicious', "
    "then 'Rules: R1', 'Rules: R2' or 'Rules: none'.\n\n"
)
RULE = re.compile(r"Rules:\s*(R1|R2|none)")
cases = [json.loads(line) for line in Path("ml/lora/data/test.jsonl").read_text().splitlines()]


def evaluate(name: str, adapter: str | None, prefix: str) -> dict:
    model, tokenizer = load(BASE, adapter_path=adapter)
    correct, tokens, start = 0, 0, time.perf_counter()
    for case in cases:
        messages = [{"role": "user", "content": prefix + case["prompt"]}]
        prompt = tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, tokenize=False, enable_thinking=False
        )
        tokens += len(tokenizer.encode(prompt))
        found = RULE.findall(generate(model, tokenizer, prompt=prompt, max_tokens=40))
        expected = case["completion"].split("Rules: ")[1]
        correct += int(bool(found) and found[0] == expected)
    seconds = time.perf_counter() - start
    return {
        f"{name}_accuracy": correct / len(cases),
        f"{name}_seconds_per_case": seconds / len(cases),
        f"{name}_prompt_tokens": tokens / len(cases),
    }


mlflow.set_tracking_uri("http://localhost:5050")
mlflow.set_experiment("lora-distill")
with mlflow.start_run():
    metrics = evaluate("base", None, RULES) | evaluate("lora", "ml/lora/adapters", "")
    mlflow.log_params({"base_model": BASE, "test_cases": len(cases)})
    mlflow.log_metrics(metrics)
for key, value in metrics.items():
    print(f"{key}: {value:.3f}")
