import random
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timedelta
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

    def foreign_atm_withdrawal(self, timestamp: datetime) -> tuple[Transaction, bool]:
        """Fraud pattern: a large ATM cash withdrawal abroad (stolen or skimmed card)."""
        account = self._rng.choice(self.accounts)

        # Any country EXCEPT the customer's home country
        foreign_countries = [c for c in COUNTRY_CURRENCY if c != account.home_country]
        country = self._rng.choice(foreign_countries)

        # 5 to 10 times the customer's typical spend
        multiplier = self._rng.uniform(5, 10)
        amount = Decimal(str(round(account.typical_amount * multiplier, 2)))

        transaction = self._build_transaction(account, amount, timestamp, "atm", country)
        return transaction, True

    def card_testing_burst(self, start: datetime, n: int = 8) -> list[tuple[Transaction, bool]]:
        """Fraud pattern: many tiny online payments seconds apart, testing a stolen card."""
        account = self._rng.choice(self.accounts)
        burst: list[tuple[Transaction, bool]] = []
        timestamp = start

        for _ in range(n):
            amount = Decimal(str(round(self._rng.uniform(0.50, 2.00), 2)))
            transaction = self._build_transaction(
                account, amount, timestamp, "online", account.home_country
            )
            burst.append((transaction, True))
            timestamp += timedelta(seconds=self._rng.randint(5, 40))

        return burst

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

    def stream(
        self, start: datetime, n: int, fraud_rate: float = 0.01
    ) -> Iterator[tuple[Transaction, bool]]:
        timestamp = start
        produced = 0

        while produced < n:
            timestamp += timedelta(seconds=self._rng.expovariate(0.5))  # random gap, about 2s

            if self._rng.random() < fraud_rate:
                if self._rng.random() < 0.5:
                    events = [self.foreign_atm_withdrawal(timestamp)]
                else:
                    events = self.card_testing_burst(timestamp)
            else:
                events = [self.normal_transaction(timestamp)]

            for event in events:
                yield event
                produced += 1
                if produced == n:
                    return
