import duckdb
import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow import MlflowClient
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score

FEATURES = ["amount", "amount_vs_account_avg", "is_foreign", "channel"]  # no tx_last_10min!

df = (
    duckdb.connect("pipelines/dbt/warehouse.duckdb", read_only=True)
    .sql("select * from ml_training_set order by transaction_at")
    .df()
)
X = pd.get_dummies(df[FEATURES], columns=["channel"]).astype(float)
y = df["is_fraud"].astype(int)
cut = int(len(df) * 0.75)
X_train, X_test, y_train, y_test = X[:cut], X[cut:], y[:cut], y[cut:]

mlflow.set_tracking_uri("http://localhost:5050")
mlflow.set_experiment("fraud-model")

with mlflow.start_run(run_name="challenger-logreg"):
    model = LogisticRegression(class_weight="balanced", max_iter=1000).fit(X_train, y_train)
    mlflow.log_metric("pr_auc", average_precision_score(y_test, model.predict_proba(X_test)[:, 1]))
    info = mlflow.sklearn.log_model(
        model, name="model", input_example=X_test.head(3), registered_model_name="fraud-detector"
    )
    MlflowClient().set_registered_model_alias(
        "fraud-detector", "challenger", info.registered_model_version
    )
    print(f"challenger-> version {info.registered_model_version}")
