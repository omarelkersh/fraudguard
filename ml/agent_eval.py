"""Evaluate the investigator agent on a fixed test set."""

import asyncio
import json
import re
from pathlib import Path

import duckdb
import mlflow
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from fraudguard_investigator.agent import investigate

VERDICT = re.compile(r"verdict\W*(not suspicious|suspicious)", re.IGNORECASE)
RULES_LINE = re.compile(r"rules:\s*(.*)$", re.IGNORECASE | re.MULTILINE)
RULE = re.compile(r"\bR[1-6]\b")

UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")


def unknown_ids(report: str, known_ids: set[str]) -> list[str]:
    """Transaction IDs in the report that do not belong to the account."""
    return sorted(set(UUID.findall(report)) - known_ids)


def grade(report: str, case: dict) -> dict:
    match = VERDICT.search(report)
    suspicious = match is not None and match.group(1).lower() == "suspicious"
    lines = RULES_LINE.findall(report)  # only the final 'Rules:' line counts as citing
    cited = set(RULE.findall(lines[-1])) if lines else set()
    return {
        "verdict_correct": int(match is not None and suspicious == case["suspicious"]),
        "missing_rules": sorted(set(case["must_cite"]) - cited),
        "forbidden_rules": sorted(cited & set(case["must_not_cite"])),
    }


POLICY = Path("knowledge/aml_policy.md").read_text()


class Judgement(BaseModel):
    score: int = Field(ge=1, le=5, description="1 = rules misapplied, 5 = every cited rule fits")
    reason: str


def judge(report: str, model: str = "qwen3:8b") -> Judgement:
    llm = ChatOllama(model=model, temperature=0, reasoning=False).with_structured_output(Judgement)
    return llm.invoke(
        f"You grade fraud reports. Policy:\n{POLICY}\n\nReport:\n{report}\n\n"
        "Does every cited rule fit the evidence? Penalise rules that do not apply."
    )


def account_transaction_ids(transaction_id: str) -> set[str]:
    con = duckdb.connect("pipelines/dbt/warehouse.duckdb", read_only=True)
    rows = con.execute(
        "select transaction_id from fct_transactions where account_id = "
        "(select account_id from fct_transactions where transaction_id = ?)",
        [transaction_id],
    ).fetchall()
    con.close()
    return {row[0] for row in rows}


def main() -> None:
    mlflow.set_tracking_uri("http://localhost:5050")
    mlflow.set_experiment("agent-eval")
    cases = json.loads(Path("ml/eval_cases.json").read_text())
    for case in cases:
        outcome = asyncio.run(investigate(case["transaction_id"]))
        report = outcome["report"]
        result = grade(report, case)
        made_up = unknown_ids(report, account_transaction_ids(case["transaction_id"]))
        judgement = judge(report)
        with mlflow.start_run(run_name=case["case"]):
            mlflow.log_metrics(
                {
                    "verdict_correct": result["verdict_correct"],
                    "missing_rules": len(result["missing_rules"]),
                    "forbidden_rules": len(result["forbidden_rules"]),
                    "made_up_ids": len(made_up),
                    "judge_score": judgement.score,
                    "seconds": outcome["seconds"],
                }
            )
            mlflow.log_text(f"{report}\n\n---\nJudge: {judgement.reason}", "report.md")
        print(case["case"], result, "made_up:", made_up, "judge:", judgement.score)


if __name__ == "__main__":
    main()
