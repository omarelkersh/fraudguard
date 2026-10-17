import mlflow
from mlflow import MlflowClient

MODEL = "fraud-detector"

mlflow.set_tracking_uri("http://localhost:5050")
client = MlflowClient()

versions = client.search_model_versions(f"name='{MODEL}'")
best = max(versions, key=lambda v: client.get_run(v.run_id).data.metrics["pr_auc"])
client.set_registered_model_alias(MODEL, "champion", best.version)
print(f"champion -> version {best.version}")
