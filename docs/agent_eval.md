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

Then the data gap was fixed (20,000 transactions, about 20 per account) and the agent got an account-profile tool. The test set moved to new cases that have a real history:

| Version | card_testing | foreign_atm | normal |
|---|---|---|---|
| + profile tool | verdict wrong ❌ | misses R2 ❌ | gave up on the account ID ❌ |
| + profile returns `account_id`, "one tool at a time" | misses R1 | ✅ R2 | ✅ |

No run ever cited a made-up transaction ID.

## Findings

- **Example priming:** the prompt's example ("many small online payments within minutes") was copied into reports as evidence for accounts that had only one transaction. Removing it stopped the invented patterns.
- **The test set must be fair:** R2 needs the customer's home country and usual spend. The warehouse has neither for this account (accounts average 1.7 transactions), so the agent cannot prove R2. The case now expects "suspicious" but no specific rule.
- **The data gap came first:** without a home country or usual spend, the agent guessed. The account-profile tool computes both point in time (only payments before this one), so the agent can now prove R2: 695.64 is 9.3× the typical 74.81, and the payment is in the US while the home country is DE.
- **Tool design matters as much as the prompt:** the agent called the profile and history tools in parallel and guessed the account ID from the transaction UUID. The guardrail rejected it 3 times, and then the agent gave up. Returning `account_id` from the profile, so the next tool's input comes from a tool result, fixed this.

## Next improvements

1. Card testing: the agent sees the 9 tiny payments but does not cite R1. Try a count tool ("payments in the last 10 minutes") so the threshold check is not left to the LLM.
2. Grow the test set beyond 3 cases and run each case several times, since LLM outputs vary.
3. Run the deterministic checks in CI against recorded reports, so prompt changes cannot silently regress.
