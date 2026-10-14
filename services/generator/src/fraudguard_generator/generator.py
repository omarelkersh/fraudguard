import random
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from fraudguard_generator.models import Transaction


@dataclass(frozen=True)
class AccountProfile:
    """A simulated customer's habits. Fraud later = behaviour that breaks these habits."""

    account_id: str  # "ACC-" + 8 digits
    home_country: str  # e.g. "DE"
    currency: str  # matches the home country, e.g. "EUR" for DE
    typical_amount: float  # this customer's usual spend, e.g. 45.0


COUNTRY_CURRENCY = {"DE": "EUR", "US": "USD", "EG": "EGP"}
CHANNELS = ["card_present", "online", "atm", "transfer"]
CHANNEL_WEIGHTS = [0.50, 0.35, 0.10, 0.05]  # most people tap cards or shop online


class TransactionGenerator:
    def __init__(
        self, seed: int | None = None, n_accounts: int = 1000, n_merchants: int = 200
    ) -> None:
        """Create a seeded random generator and build the account and merchant pools once."""
        self._rng = random.Random(seed)

        self.accounts: list[AccountProfile] = []
        for n in range(n_accounts):
            country = self._rng.choice(list(COUNTRY_CURRENCY))  # random home country
            self.accounts.append(
                AccountProfile(
                    account_id=f"ACC-{n:08d}",
                    home_country=country,
                    currency=COUNTRY_CURRENCY[country],
                    typical_amount=round(self._rng.uniform(10, 200), 2),
                )
            )

        self.merchant_ids: list[str] = [f"MER-{n:08d}" for n in range(n_merchants)]

    def normal_transaction(self, timestamp: datetime) -> tuple[Transaction, bool]:
        """Return one legitimate transaction for a random account, plus its label (False)."""
        account = self._rng.choice(self.accounts)

        # Amount: close to this customer's typical spend (±30%), never below 1.00
        raw_amount = self._rng.gauss(account.typical_amount, account.typical_amount * 0.3)
        amount = Decimal(str(round(max(raw_amount, 1.0), 2)))

        # Country: home country 95% of the time, otherwise the customer is travelling
        if self._rng.random() < 0.95:
            country = account.home_country
        else:
            country = self._rng.choice(list(COUNTRY_CURRENCY))

        channel = self._rng.choices(CHANNELS, weights=CHANNEL_WEIGHTS)[0]
        transaction = self._build_transaction(account, amount, timestamp, channel, country)
        return transaction, False

    def _build_transaction(
        self,
        account: AccountProfile,
        amount: Decimal,
        timestamp: datetime,
        channel: str,
        country: str,
    ) -> Transaction:
        """Build one Transaction for an account. Shared by normal and fraud transactions."""
        return Transaction(
            transaction_id=uuid.UUID(int=self._rng.getrandbits(128), version=4),
            account_id=account.account_id,
            merchant_id=self._rng.choice(self.merchant_ids),
            amount=amount,
            currency=account.currency,
            timestamp=timestamp,
            channel=channel,
            country=country,
        )
