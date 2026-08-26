"""Contracts that keep the demo's provider request explicit and inspectable."""

from __future__ import annotations

import pytest

from data_agent_network_demo.contracts import (
    ALLOWED_PERIODS,
    MINIMUM_OBSERVATIONS,
    MINIMUM_SPAN_DAYS,
    normalize_symbol,
)


@pytest.mark.parametrize(
    ("raw", "normalized"),
    (
        (" aapl ", "AAPL"),
        ("brk-b", "BRK-B"),
        ("^gspc", "^GSPC"),
        ("btc-usd", "BTC-USD"),
        ("eurusd=x", "EURUSD=X"),
        ("a" * 20, "A" * 20),
    ),
)
def test_symbol_normalization_accepts_common_yfinance_ticker_forms(
    raw: str,
    normalized: str,
) -> None:
    assert normalize_symbol(raw) == normalized


@pytest.mark.parametrize(
    "raw",
    ("", "AAPL SPY", "AAPL/../../secret", "AAPL?x=1", "'AAPL'", "A" * 21),
)
def test_symbol_normalization_rejects_ambiguous_or_unsafe_input(raw: str) -> None:
    with pytest.raises(ValueError, match="Use a ticker"):
        normalize_symbol(raw)


def test_history_provenance_names_the_exact_yfinance_call_contract(
    history_factory: object,
) -> None:
    history = history_factory("AAPL", (100, 110, 99, 120, 126))

    assert history.provenance() == {
        "symbol": "AAPL",
        "name": "AAPL test instrument",
        "currency": "USD",
        "exchange": "TEST",
        "instrument_type": "EQUITY",
        "timezone": "America/New_York",
        "query": {
            "method": "yfinance.Ticker.history",
            "period": "1y",
            "interval": "1d",
            "auto_adjust": True,
            "actions": False,
            "repair": False,
        },
        "fetched_at_utc": "2024-01-08T22:00:00+00:00",
        "rows_received": 5,
        "rows_used": 5,
        "rows_dropped": 0,
        "warnings": [],
    }
    assert ALLOWED_PERIODS == ("1mo", "3mo", "6mo", "1y", "2y", "5y")
    assert MINIMUM_OBSERVATIONS == {
        "1mo": 15,
        "3mo": 45,
        "6mo": 90,
        "1y": 180,
        "2y": 360,
        "5y": 900,
    }
    assert MINIMUM_SPAN_DAYS == {
        "1mo": 21,
        "3mo": 73,
        "6mo": 146,
        "1y": 292,
        "2y": 584,
        "5y": 1460,
    }
