from typing import Literal

from pydantic import BaseModel, Field


class ScoreRequest(BaseModel):
    """The features of one transaction, computed upstream."""

    amount: float = Field(gt=0)
    amount_vs_account_avg: float = Field(ge=0)
    tx_last_10min: int = Field(ge=1)
    is_foreign: bool
    channel: Literal["card_present", "online", "atm", "transfer"]


class ScoreResponse(BaseModel):
    fraud_probability: float
    is_fraud: bool
    model_version: str
