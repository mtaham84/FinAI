"""
Provider abstraction layer.

No real integrations exist yet -- these are interfaces so that
future connections (Nobitex for crypto, Milli-style platforms for
gold/silver, Iranian brokerages for stocks, Digikala/SnappShop/Torob
for shopping, Digipay/SnappPay/TorobPay for BNPL) can be added
without reshaping the rest of the app.

Rules for any future concrete implementation:
  * Never store raw bank passwords, CVV2, dynamic passwords, or card
    PINs. Use tokenized OAuth-style authorization instead.
  * A provider only ever returns data for the account it was
    authorized against -- callers must not trust a provider to
    self-enforce user scoping; the calling service must always also
    filter by the local user id.
  * Providers must not be called from templates or from the AI layer
    directly -- always go through apps.finance.engine or a
    dedicated sync service so results land in the deterministic
    database records.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class ProviderAccountSnapshot:
    external_id: str
    display_name: str
    balance: Decimal
    currency: str = "IRT"


@dataclass
class ProviderTransactionSnapshot:
    external_id: str
    amount: Decimal
    occurred_at: str
    description: str = ""
    category_hint: str = ""


class BaseProvider(ABC):
    """Common contract every provider integration must implement."""

    provider_key: str = "base"

    @abstractmethod
    def is_connected(self, connection) -> bool:
        ...

    @abstractmethod
    def fetch_accounts(self, connection) -> list[ProviderAccountSnapshot]:
        ...


class BankProvider(BaseProvider):
    """Iranian banking aggregation providers, where official APIs exist."""

    provider_key = "bank"

    @abstractmethod
    def fetch_transactions(self, connection, since) -> list[ProviderTransactionSnapshot]:
        ...


class InvestmentProvider(BaseProvider):
    """Iranian brokerage / market-data providers for stock holdings."""

    provider_key = "investment"


class CryptoProvider(BaseProvider):
    """e.g. Nobitex."""

    provider_key = "crypto"


class GoldProvider(BaseProvider):
    """e.g. Milli-style gold platforms, where an official partnership exists."""

    provider_key = "gold"


class SilverProvider(BaseProvider):
    provider_key = "silver"


class ShoppingProvider(BaseProvider):
    """e.g. Digikala, SnappShop, Torob."""

    provider_key = "shopping"

    @abstractmethod
    def fetch_orders(self, connection, since) -> list[ProviderTransactionSnapshot]:
        ...


class CreditProvider(BaseProvider):
    """BNPL / installment providers, e.g. Digipay, SnappPay, TorobPay."""

    provider_key = "credit"


class MarketDataProvider(ABC):
    """Read-only market price feeds -- no user account context needed."""

    provider_key = "market_data"

    @abstractmethod
    def get_latest_price(self, symbol: str) -> Decimal:
        ...


PROVIDER_REGISTRY: dict[str, type] = {
    # Populated as real providers are implemented, e.g.:
    # "nobitex": NobitexCryptoProvider,
}
