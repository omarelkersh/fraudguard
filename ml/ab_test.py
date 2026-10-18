import duckdb
import mlflow
import numpy as np
import pandas as pd
from scipy.stats import norm

ALPHA = 0.05  # B1: significance level (the usual one)
FEATURES = ["amount", "amount_vs_account_avg", "tx_last_10min", "is_foreign", "channel"]

mlflow.set_tracking_uri("http://localhost:5050")
models = {
    "A (champion)": mlflow.sklearn.load_model("models:/fraud-detector@champion"),
    "B (challenger)": mlflow.sklearn.load_model("models:/fraud-detector@challenger"),
}

df = (
    duckdb.connect("pipelines/dbt/warehouse.duckdb", read_only=True)
    .sql("select * from ml_training_set order by transaction_at")
    .df()
)
test = df[int(len(df) * 0.75) :].reset_index(drop=True)  # newest 25% = "live traffic"
arm = np.random.default_rng(42).choice(list(models), len(test))  # random 50/50 split


def flagged(model, frame: pd.DataFrame) -> int:
    """How many rows the model flags as fraud."""
    X = pd.get_dummies(frame[FEATURES], columns=["channel"])
    X = X.reindex(columns=model.feature_names_in_, fill_value=0).astype(float)
    return int((model.predict_proba(X)[:, 1] >= 0.5).sum())


def z_test(x1: int, n1: int, x2: int, n2: int) -> float:
    """Two-proportion z-test. Returns the p-value."""
    pooled = (x1 + x2) / (n1 + n2)
    z = (x1 / n1 - x2 / n2) / np.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    return float(2 * (1 - norm.cdf(abs(z))))


for metric, rows in [
    ("recall", lambda f: f[f.is_fraud]),
    ("false-positive rate", lambda f: f[~f.is_fraud]),
]:
    counts = []
    for name, model in models.items():
        part = rows(test[arm == name])
        counts.append((flagged(model, part), len(part)))
        print(
            f"{metric:20s} {name:15s} {counts[-1][0]}/{counts[-1][1]} = "
            f"{counts[-1][0] / counts[-1][1]:.1%}"
        )
    p = z_test(*counts[0], *counts[1])
    print(f"{'':20s} p-value = {p:.4f} -> {'SIGNIFICANT' if p < ALPHA else 'not significant'}\n")
