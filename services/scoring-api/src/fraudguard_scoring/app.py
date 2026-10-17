import os
from contextlib import asynccontextmanager

import mlflow
import pandas as pd
from fastapi import FastAPI

from fraudguard_scoring.schemas import ScoreRequest, ScoreResponse

MODEL_NAME = "fraud-detector"
THRESHOLD = 0.5
state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once at startup: load the champion model from MLflow."""
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5050"))
    state["model"] = mlflow.sklearn.load_model(f"models:/{MODEL_NAME}@champion")
    state["version"] = (
        mlflow.MlflowClient().get_model_version_by_alias(MODEL_NAME, "champion").version
    )
    yield


app = FastAPI(title="FraudGuard scoring API", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_version": state.get("version")}


@app.post("/score", response_model=ScoreResponse)
def score(request: ScoreRequest) -> ScoreResponse:
    model = state["model"]
    row = pd.get_dummies(pd.DataFrame([request.model_dump()]), columns=["channel"])
    features = row.reindex(columns=model.feature_names_in_, fill_value=0).astype(float)
    probability = float(model.predict_proba(features)[0, 1])
    return ScoreResponse(
        fraud_probability=probability,
        is_fraud=probability >= THRESHOLD,
        model_version=state["version"],
    )
