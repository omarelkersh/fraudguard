import duckdb
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import average_precision_score, precision_score, recall_score

FEATURES = ["amount", "amount_vs_account_avg", "tx_last_10min", "is_foreign", "channel"]

df = (
    duckdb.connect("pipelines/dbt/warehouse.duckdb", read_only=True)
    .sql("select * from ml_training_set order by transaction_at")
    .df()
)
X = pd.get_dummies(df[FEATURES], columns=["channel"]).astype(float)  # text -> 0/1 columns
y = df["is_fraud"].astype(int)  # T1: the label column

cut = int(len(df) * 0.75)  # T2: train on the oldest 75%
X_train, X_test, y_train, y_test = X[:cut], X[cut:], y[:cut], y[cut:]

mlflow.set_tracking_uri("http://localhost:5050")  # T3: your MLflow port
mlflow.set_experiment("fraud-model")

with mlflow.start_run():
    params = {"n_estimators": 200, "max_depth": 6, "class_weight": "balanced", "random_state": 42}
    model = RandomForestClassifier(**params).fit(X_train, y_train)
    scores = model.predict_proba(X_test)[:, 1]

    mlflow.log_params(params)
    mlflow.log_metrics(
        {
            "pr_auc": average_precision_score(y_test, scores),
            "precision": precision_score(y_test, scores > 0.5),
            "recall": recall_score(y_test, scores > 0.5),
        }
    )
    mlflow.sklearn.log_model(
        model,
        name="model",
        input_example=X_test.head(3),
        skops_trusted_types=["sklearn.tree._tree.Tree"],
    )
