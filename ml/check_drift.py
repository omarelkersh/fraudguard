import sys

import duckdb
import mlflow
from drift import psi

FEATURES = ["amount", "amount_vs_account_avg", "tx_last_10min"]
THRESHOLD = 0.25

df = (
    duckdb.connect("pipelines/dbt/warehouse.duckdb", read_only=True)
    .sql("select * from ml_training_set order by transaction_at")
    .df()
)
cut = int(len(df) * 0.75)
reference, current = df[:cut], df[cut:].copy()

if "--simulate-drift" in sys.argv:
    current["amount"] = current["amount"] * 3  # pretend customers suddenly spend 3x more

scores = {
    f"psi_{c}": psi(reference[c].to_numpy(float), current[c].to_numpy(float)) for c in FEATURES
}

mlflow.set_tracking_uri("http://localhost:5050")
mlflow.set_experiment("drift-monitoring")
with mlflow.start_run():
    mlflow.log_metrics(scores)

for name, value in scores.items():
    print(f"{name:30s} {value:6.3f}  {'DRIFT' if value > THRESHOLD else 'ok'}")
sys.exit(1 if any(v > THRESHOLD for v in scores.values()) else 0)
