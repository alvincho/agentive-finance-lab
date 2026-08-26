"""Demo-specific contracts shared by the two Personas and the data adapter."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Protocol


ALLOWED_PERIODS = ("1mo", "3mo", "6mo", "1y", "2y", "5y")
MINIMUM_OBSERVATIONS = {
    "1mo": 15,
    "3mo": 45,
    "6mo": 90,
    "1y": 180,
    "2y": 360,
    "5y": 900,
}
MINIMUM_SPAN_DAYS = {
    "1mo": 21,
    "3mo": 73,
    "6mo": 146,
    "1y": 292,
    "2y": 584,
    "5y": 1460,
}
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9^][A-Z0-9.\-=^]{0,19}$")


def normalize_symbol(value: str) -> str:
    """Normalize and validate the small ticker syntax accepted by the demo."""

    symbol = value.strip().upper()
    if not SYMBOL_PATTERN.fullmatch(symbol):
        raise ValueError(
            "Use a ticker such as AAPL, BRK-B, ^GSPC, BTC-USD, or EURUSD=X."
        )
    return symbol


@dataclass(frozen=True, slots=True)
class PriceObservation:
    date: str
    close: float
    volume: int | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class MarketHistory:
    symbol: str
    name: str
    currency: str | None
    exchange: str | None
    instrument_type: str | None
    timezone: str | None
    period: str
    interval: str
    auto_adjust: bool
    fetched_at_utc: str
    rows_received: int
    rows_dropped: int
    observations: tuple[PriceObservation, ...]
    warnings: tuple[str, ...] = ()

    def provenance(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "name": self.name,
            "currency": self.currency,
            "exchange": self.exchange,
            "instrument_type": self.instrument_type,
            "timezone": self.timezone,
            "query": {
                "method": "yfinance.Ticker.history",
                "period": self.period,
                "interval": self.interval,
                "auto_adjust": self.auto_adjust,
                "actions": False,
                "repair": False,
            },
            "fetched_at_utc": self.fetched_at_utc,
            "rows_received": self.rows_received,
            "rows_used": len(self.observations),
            "rows_dropped": self.rows_dropped,
            "warnings": list(self.warnings),
        }


class MarketDataError(RuntimeError):
    """Normalized provider failure returned without inventing fallback data."""

    def __init__(self, *, symbol: str, code: str, message: str) -> None:
        super().__init__(message)
        self.symbol = symbol
        self.code = code
        self.message = message

    def to_dict(self) -> dict[str, str]:
        return {"symbol": self.symbol, "code": self.code, "message": self.message}


class MarketDataSource(Protocol):
    """Testing seam; the only runtime implementation is YFinanceSource."""

    provider_name: str
    provider_version: str

    def fetch_history(self, *, symbol: str, period: str) -> MarketHistory:
        """Fetch one adjusted daily price history."""
