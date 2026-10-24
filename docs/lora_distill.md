# LoRA distillation: can a 1.7B model learn the policy?

**Question:** can a small fine-tuned model cite the right policy rule from payment facts, without the rules in its prompt, and how does it compare with the same model prompted with the rules?

## Setup

- **Data** (`make lora-data`): payment facts computed point in time from the warehouse (amount, channel, country, payments in the last 10 minutes, home country, typical amount). Labels follow the policy thresholds: R1 (online, under 5, more than 5 payments in 10 minutes), R2 (ATM abroad, more than 5× the typical amount), otherwise none. Balanced: all R1 and R2 cases plus 800 normal ones, split 80/10/10 into 1,273 train, 159 validation and 160 test examples.
- **Training** (`make lora-train`): LoRA (rank 8, 16 layers, 0.29% of the weights trainable) on `mlx-community/Qwen3-1.7B-4bit` with MLX-LM on a MacBook Air M5. 600 iterations at batch size 4, with the prompt masked so the loss only counts answer tokens. Runs locally and costs nothing.
- **Evaluation** (`make lora-eval`): both models answer the 160 held-out test cases. The base model gets the rules in its prompt; the LoRA model gets only the facts. Logged to the MLflow experiment `lora-distill`.

## Results

| Model | Accuracy | Seconds per case | Prompt tokens |
|---|---|---|---|
| Qwen3-1.7B, rules in the prompt | 52.5% | 0.27 | 140 |
| **Qwen3-1.7B + LoRA, facts only** | **98.1%** | **0.20** | **56** |

- Validation loss fell from 10.4 to about 0.01 by iteration 200, then levelled off: 200 iterations would have been enough.
- The base model often listed every rule ("Rules: R1, Rules: R2") instead of choosing one.
- 60% fewer prompt tokens: the policy lives in the weights, not the prompt. That means a lower cost per call on a paid API, and lower latency.

## Honest limitations

- The labels come from our own SQL rules, and that SQL is 100% correct and runs in microseconds. Fine-tuning does not beat code here. The experiment shows that a small model can absorb a written policy into its weights, which is worth it when rules are fuzzy or natural-language and hard to code.
- The model only answers the classification step. The 8B agent still gathers the evidence with tools and writes the report.
- The adapter is tied to the facts format it was trained on; a new rule means rebuilding the data and retraining.
