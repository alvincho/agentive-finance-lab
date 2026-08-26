"""Make all three source roots importable from a clean checkout."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import replace
from datetime import date, timedelta
from pathlib import Path
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]

for relative_root in (
    "prompits-lite",
    "phemacast-lite",
    "demos/data-agent-network-demo",
):
    source_root = str(REPO_ROOT / relative_root)
    if source_root not in sys.path:
        sys.path.insert(0, source_root)


from data_agent_network_demo.contracts import (  # noqa: E402
    MarketDataError,
    MarketHistory,
    PriceObservation,
)


HistoryFactory = Callable[..., MarketHistory]


def build_history(
    symbol: str,
    closes: Iterable[float],
    *,
    dates: Iterable[str] | None = None,
    currency: str | None = "USD",
    period: str = "1y",
    warnings: tuple[str, ...] = (),
) -> MarketHistory:
    """Build a deterministic adjusted-close history for unit tests."""

    close_values = tuple(closes)
    date_values = tuple(dates or (
        "2024-01-02",
        "2024-01-03",
        "2024-01-04",
        "2024-01-05",
        "2024-01-08",
    ))
    if len(close_values) != len(date_values):
        raise ValueError("closes and dates must have the same length")
    observations = tuple(
        PriceObservation(date=item_date, close=float(close), volume=1_000 + index)
        for index, (item_date, close) in enumerate(zip(date_values, close_values))
    )
    return MarketHistory(
        symbol=symbol,
        name=f"{symbol} test instrument",
        currency=currency,
        exchange="TEST",
        instrument_type="EQUITY",
        timezone="America/New_York",
        period=period,
        interval="1d",
        auto_adjust=True,
        fetched_at_utc="2024-01-08T22:00:00+00:00",
        rows_received=len(observations),
        rows_dropped=0,
        observations=observations,
        warnings=warnings,
    )


class FakeMarketDataSource:
    """Deterministic provider seam; it performs no I/O and never invents a fallback."""

    provider_name = "yfinance"
    provider_version = "test-double"

    def __init__(self, histories: Iterable[MarketHistory]) -> None:
        self.histories = {history.symbol: history for history in histories}
        self.failures: dict[str, MarketDataError] = {}
        self.calls: list[tuple[str, str]] = []

    def fetch_history(self, *, symbol: str, period: str) -> MarketHistory:
        self.calls.append((symbol, period))
        if symbol in self.failures:
            raise self.failures[symbol]
        try:
            history = self.histories[symbol]
        except KeyError as error:
            raise MarketDataError(
                symbol=symbol,
                code="not-configured",
                message=f"No deterministic history configured for {symbol}.",
            ) from error
        return replace(history, period=period)


@pytest.fixture
def history_factory() -> HistoryFactory:
    return build_history


@pytest.fixture
def fake_source() -> FakeMarketDataSource:
    first_date = date.today() - timedelta(days=34)
    dates = tuple(
        (first_date + timedelta(days=index * 2)).isoformat()
        for index in range(18)
    )
    return FakeMarketDataSource(
        (
            build_history(
                "AAPL",
                (
                    100, 102, 101, 104, 106, 108, 107, 110, 112,
                    111, 114, 116, 115, 118, 120, 119, 122, 124,
                ),
                dates=dates,
            ),
            build_history(
                "SPY",
                (
                    100, 101, 100, 102, 103, 104, 104, 105, 106,
                    106, 107, 108, 108, 109, 110, 110, 111, 112,
                ),
                dates=dates,
            ),
        )
    )
