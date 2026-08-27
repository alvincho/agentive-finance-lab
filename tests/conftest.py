"""Shared import setup and a deterministic yfinance-shaped provider seam."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import sys
from typing import Any

import pandas as pd
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


class FakeTicker:
    """Ticker test double whose three supported operations are independently failable."""

    def __init__(self, provider: "FakeYFinanceProvider", symbol: str) -> None:
        self._provider = provider
        self._symbol = symbol

    def history(self, **kwargs: Any) -> pd.DataFrame:
        self._provider.record("history", self._symbol, kwargs=kwargs)
        self._provider.raise_if_configured("history", self._symbol)
        frame = self._provider.histories.get(self._symbol)
        if frame is None:
            return pd.DataFrame()
        return frame.copy(deep=True)

    @property
    def fast_info(self) -> Mapping[str, Any]:
        self._provider.record("fast_info", self._symbol)
        self._provider.raise_if_configured("fast_info", self._symbol)
        return dict(self._provider.fast_info_values.get(self._symbol, {}))

    @property
    def info(self) -> Mapping[str, Any]:
        self._provider.record("info", self._symbol)
        self._provider.raise_if_configured("info", self._symbol)
        return dict(self._provider.info_values.get(self._symbol, {}))


class FakeYFinanceProvider:
    """No-network replacement for the small yfinance module surface used by the demo."""

    __version__ = "test-double-1.0"

    def __init__(self) -> None:
        index = pd.DatetimeIndex(
            ["2026-08-24", "2026-08-25", "2026-08-26"], name="Date"
        )
        self.histories: dict[str, pd.DataFrame] = {
            "AAPL": pd.DataFrame(
                {
                    "Open": [226.1, 227.2, 228.3],
                    "High": [228.0, 229.5, 231.0],
                    "Low": [225.2, 226.7, 227.9],
                    "Close": [227.4, 228.8, 230.2],
                    "Volume": [41_000_000, 39_500_000, 42_250_000],
                    "Dividends": [0.0, 0.0, 0.0],
                    "Stock Splits": [0.0, 0.0, 0.0],
                },
                index=index,
            )
        }
        self.fast_info_values: dict[str, dict[str, Any]] = {
            "AAPL": {
                "symbol": "AAPL",
                "lastPrice": 230.2,
                "currency": "USD",
                "exchange": "NMS",
                "marketCap": 3_420_000_000_000,
                "dayHigh": 231.0,
                "dayLow": 227.9,
                "previousClose": 228.8,
                "lastVolume": 42_250_000,
            }
        }
        self.info_values: dict[str, dict[str, Any]] = {
            "AAPL": {
                "symbol": "AAPL",
                "longName": "Apple Inc.",
                "quoteType": "EQUITY",
                "sector": "Technology",
                "industry": "Consumer Electronics",
                "country": "United States",
                "website": "https://www.apple.com",
                "longBusinessSummary": "A deterministic test profile.",
                "marketCap": 3_420_000_000_000,
                "currency": "USD",
                "exchange": "NMS",
            }
        }
        self.calls: list[dict[str, Any]] = []
        self.failures: dict[tuple[str, str], Exception] = {}

    def Ticker(self, symbol: str) -> FakeTicker:  # noqa: N802 - yfinance API name
        self.record("Ticker", symbol)
        self.raise_if_configured("Ticker", symbol)
        return FakeTicker(self, symbol)

    def record(self, operation: str, symbol: str, **detail: Any) -> None:
        self.calls.append({"operation": operation, "symbol": symbol, **detail})

    def raise_if_configured(self, operation: str, symbol: str) -> None:
        failure = self.failures.get((operation, symbol))
        if failure is not None:
            raise failure

    def fail(self, operation: str, symbol: str, error: Exception) -> None:
        self.failures[(operation, symbol)] = error


@pytest.fixture
def fake_provider() -> FakeYFinanceProvider:
    return FakeYFinanceProvider()
