"""Opt-in provider smoke test; normal test runs never make network requests."""

from __future__ import annotations

import os

import pytest

from data_agent_network_demo.workflow import DataAgentNetworkDemo, DemoQuestion


pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_YFINANCE_TESTS") != "1",
    reason="set RUN_LIVE_YFINANCE_TESTS=1 to exercise the live yfinance boundary",
)


def test_live_history_uses_data_user_direct_source_path() -> None:
    demo = DataAgentNetworkDemo()

    result = demo.fetch(
        DemoQuestion(
            query="historical AAPL prices",
            fetch_source_id="yfinance",
            fetch_endpoint_id="yfinance.ticker.history",
            fetch_parameters={"symbol": "AAPL", "period": "1mo", "interval": "1d"},
        )
    )

    assert result["status"] == "completed"
    assert result["source"]["source_id"] == "yfinance"
    assert result["source"]["provider_version"]
    assert result["dataset_id"] == "yfinance.ticker.history"
    assert len(result["canonical_data"]["items"]) >= 2
    assert result["attas_pulse"]["pulse_name"] == "data_fetch"
