"""Opt-in provider smoke test; normal test runs never make network requests."""

from __future__ import annotations

import os

import pytest

from data_agent_network_demo.yfinance_source import YFinanceSource


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_YFINANCE_TESTS") != "1",
    reason="set RUN_LIVE_YFINANCE_TESTS=1 to exercise the live yfinance boundary",
)


def test_live_yfinance_returns_real_adjusted_daily_histories() -> None:
    source = YFinanceSource(timeout_seconds=15)

    aapl = source.fetch_history(symbol="AAPL", period="1mo")
    spy = source.fetch_history(symbol="SPY", period="1mo")

    assert source.provider_name == "yfinance"
    assert source.provider_version
    assert len(aapl.observations) >= 2
    assert len(spy.observations) >= 2
    assert aapl.provenance()["query"] == {
        "method": "yfinance.Ticker.history",
        "period": "1mo",
        "interval": "1d",
        "auto_adjust": True,
        "actions": False,
        "repair": False,
    }
