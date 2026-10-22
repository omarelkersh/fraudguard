# Investigator agent evaluation

**Question:** does the agent reach the right verdict, cite the right policy rules, and only use real evidence?

**Run:** `make eval-agent` (needs Ollama, Qdrant and MLflow running). Results go to the MLflow experiment `agent-eval`, one run per case, with the report and the judge's reasoning attached.

## How it is graded

The test set lives in `ml/eval_cases.json`. Each case states the correct verdict, the rules a report **must** cite and the rules it **must not** cite.

| Check | Type | What it catches |
|---|---|---|
| Verdict correct | deterministic (regex) | false alarms and missed fraud |
| Missing / forbidden rules | deterministic | rules that are not cited, or cited without their conditions being met |
| Made-up IDs | deterministic (warehouse lookup) | transaction IDs that do not belong to the account (hallucinated evidence) |
| Judge score 1–5 | local LLM-as-judge (qwen3:8b, structured output) | whether each cited rule fits the evidence |

The deterministic checks are the ground truth. The judge is only a secondary signal: it was wrong more than once (for example, it called R1 and R4 "supported" for a single ATM withdrawal).

The agent must end every report with one line, `Rules: R1, R3` or `Rules: none`, and the grader reads only that line. Without this output contract, "R1 is not applicable" was counted as citing R1.

## Eval-driven iterations (qwen3:8b)

| Version | card_testing | foreign_atm | normal |
|---|---|---|---|
| Baseline prompt | cites R4 ❌ | cites R1 ❌ | false alarm, cites R1 ❌ |
| + "cite a rule only if all its conditions are met" | ✅ | cites R1 ❌ | false alarm, cites R1 ❌ |
| + "do not invent a pattern" + `Rules:` line | ✅ | no wrong rules, verdict "not suspicious" | false alarm, cites R2 ❌ |

No run ever cited a made-up transaction ID.

## Findings

- **Example priming:** the prompt's example ("many small online payments within minutes") was copied into reports as evidence for accounts that had only one transaction. Removing it stopped the invented patterns.
- **The test set must be fair:** R2 needs the customer's home country and usual spend. The warehouse has neither for this account (accounts average 1.7 transactions), so the agent cannot prove R2. The case now expects "suspicious" but no specific rule.
- **The remaining errors are a data gap, not a prompt problem:** without a home country or usual spend, the agent guesses. With the evidence missing, "not suspicious" for the ATM case is honest, but wrong.

## Next improvements

1. Give the agent an account-profile tool (home country, typical amount) and generate richer account histories.
2. Grow the test set beyond 3 cases and run each case several times, since LLM outputs vary.
3. Run the deterministic checks in CI against recorded reports, so prompt changes cannot silently regress.
