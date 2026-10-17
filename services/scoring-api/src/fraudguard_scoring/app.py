import os
from contextlib import asynccontextmanager

import mlflow
import pandas as pd
from fastapi import FastAPI
from prometheus_client import Counter, Histogram, make_asgi_app

from fraudguard_scoring.schemas import ScoreRequest, ScoreResponse

MODEL_NAME = "fraud-detector"
THRESHOLD = 0.5
PREDICTIONS = Counter("fraudguard_predictions_total", "Scored transactions", ["is_fraud"])
LATENCY = Histogram("fraudguard_score_latency_seconds", "Time to score one transaction")
SCORES = Histogram(
    "fraudguard_fraud_probability",
    "Fraud score distribution",
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)
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
app.mount("/metrics", make_asgi_app())


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model_version": state.get("version")}


@app.post("/score", response_model=ScoreResponse)
def score(request: ScoreRequest) -> ScoreResponse:
    with LATENCY.time():  # measures how long the block takes
        model = state["model"]
        row = pd.get_dummies(pd.DataFrame([request.model_dump()]), columns=["channel"])
        features = row.reindex(columns=model.feature_names_in_, fill_value=0).astype(float)
        probability = float(model.predict_proba(features)[0, 1])
    is_fraud = probability >= THRESHOLD
    PREDICTIONS.labels(is_fraud=str(is_fraud)).inc()  # B1: a counter goes up by one
    SCORES.observe(probability)  # B2: record one value in a histogram
    return ScoreResponse(
        fraud_probability=probability,
        is_fraud=is_fraud,
        model_version=state["version"],
    )
