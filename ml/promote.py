"""Promote the newest model only if it beats the champion on the SAME current test set."""

import duckdb
import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow import MlflowClient
from sklearn.metrics import average_precision_score

MODEL = "fraud-detector"
FEATURES = ["amount", "amount_vs_account_avg", "tx_last_10min", "is_foreign", "channel"]

df = (
    duckdb.connect("pipelines/dbt/warehouse.duckdb", read_only=True)
    .sql("select * from ml_training_set order by transaction_at")
    .df()
)
X = pd.get_dummies(df[FEATURES], columns=["channel"]).astype(float)
y = df["is_fraud"].astype(int)
cut = int(len(df) * 0.75)
X_test, y_test = X[cut:], y[cut:]  # newest 25%: the same rows for every model

mlflow.set_tracking_uri("http://localhost:5050")
client = MlflowClient()


def score(version: str) -> float:
    model = mlflow.sklearn.load_model(f"models:/{MODEL}/{version}")
    return average_precision_score(y_test, model.predict_proba(X_test)[:, 1])


champion = client.get_model_version_by_alias(MODEL, "champion")
newest = max(client.search_model_versions(f"name='{MODEL}'"), key=lambda v: int(v.version))
old, new = score(champion.version), score(newest.version)
print(f"champion v{champion.version}: {old:.4f} | newest v{newest.version}: {new:.4f}")

if new > old:
    client.set_registered_model_alias(MODEL, "champion", newest.version)
    print(f"champion -> version {newest.version}")
else:
    print("champion kept")
