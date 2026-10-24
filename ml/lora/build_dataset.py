"""Build a LoRA dataset: payment facts -> verdict and rule, labelled by the policy thresholds."""

import json
from pathlib import Path

import duckdb
import pandas as pd

OUT = Path("ml/lora/data")

df = (
    duckdb.connect("pipelines/dbt/warehouse.duckdb", read_only=True)
    .sql("""
    with p as (
      select t.transaction_id, any_value(t.amount) as amount, any_value(t.channel) as channel,
             any_value(t.country) as country, count(h.transaction_id) as past,
             mode(h.country) as home_country, median(h.amount) as typical
      from fct_transactions t
      left join fct_transactions h
        on h.account_id = t.account_id and h.transaction_at < t.transaction_at
      group by t.transaction_id
    )
    select p.*, m.tx_last_10min,
      case when p.channel = 'online' and p.amount < 5 and m.tx_last_10min > 5 then 'R1'
           when p.channel = 'atm' and p.country <> p.home_country
                and p.amount > 5 * p.typical then 'R2'
           else 'none' end as rule
    from p join ml_training_set m using (transaction_id)
    where p.past >= 3
    """)
    .df()
)


def facts(r) -> str:
    return (
        f"Payment: {r.amount} via {r.channel} in {r.country}. "
        f"Payments on this account in the last 10 minutes: {r.tx_last_10min}. "
        f"Customer home country: {r.home_country}. Typical amount: {round(r.typical, 2)}."
    )


def answer(r) -> str:
    verdict = "not suspicious" if r.rule == "none" else "suspicious"
    return f"Verdict: {verdict}\nRules: {r.rule}"


normal = df[df.rule == "none"].sample(800, random_state=0)
data = pd.concat([df[df.rule != "none"], normal]).sample(frac=1, random_state=0)
n = len(data)
splits = {
    "train": data[: int(n * 0.8)],
    "valid": data[int(n * 0.8) : int(n * 0.9)],
    "test": data[int(n * 0.9) :],
}
OUT.mkdir(parents=True, exist_ok=True)
for name, part in splits.items():
    with open(OUT / f"{name}.jsonl", "w") as f:
        for r in part.itertuples():
            f.write(json.dumps({"prompt": facts(r), "completion": answer(r)}) + "\n")
    print(name, len(part))
