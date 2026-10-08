from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field


class Transaction(BaseModel):
    transaction_id: UUID
    account_id: str = Field(pattern=r"^ACC-\d{8}$")
    merchant_id: str = Field(pattern=r"^MER-\d{8}$")
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: Literal["USD", "EUR", "EGP"]
    timestamp: AwareDatetime
    channel: Literal["atm", "card_present", "online", "transfer"]
    country: str = Field(pattern=r"^[A-Z]{2}$")
