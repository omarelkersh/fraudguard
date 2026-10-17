import numpy as np
from fastapi.testclient import TestClient

from fraudguard_scoring.app import app, state


class FakeModel:
    """Pretends to be the RandomForest: always says 90% fraud."""

    feature_names_in_ = np.array(
        [
            "amount",
            "amount_vs_account_avg",
            "tx_last_10min",
            "is_foreign",
            "channel_atm",
            "channel_card_present",
            "channel_online",
            "channel_transfer",
        ]
    )

    def predict_proba(self, features):
        return np.array([[0.1, 0.9]])


state["model"] = FakeModel()
state["version"] = "test"
client = TestClient(app)

VALID = {
    "amount": 1.2,
    "amount_vs_account_avg": 1.0,
    "tx_last_10min": 8,
    "is_foreign": False,
    "channel": "online",
}


def test_score_returns_probability_and_decision():
    response = client.post("/score", json=VALID)
    assert response.status_code == 200
    assert response.json() == {"fraud_probability": 0.9, "is_fraud": True, "model_version": "test"}


def test_unknown_channel_is_rejected():
    response = client.post("/score", json={**VALID, "channel": ""})
    assert response.status_code == 422
