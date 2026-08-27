"""Provider-boundary tests for the copied/reduced YFinance Data Source."""

from __future__ import annotations

from typing import Any

import pytest

from phemacast_lite import Pulser

from data_agent_network_demo.contracts import (
    DATA_AVAILABILITY_PULSE_NAME,
    DATA_FETCH_PULSE_NAME,
    DATA_SPEC_PULSE_NAME,
)
from data_agent_network_demo.yfinance_source import (
    YFinanceDataSource,
    YFinanceSource,
)


def fetch(
    source: YFinanceDataSource,
    endpoint_id: str,
    *,
    parameters: dict[str, Any],
    fields: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "source_id": "yfinance",
        "endpoint_id": endpoint_id,
        "parameters": parameters,
    }
    if fields is not None:
        payload["fields"] = fields
    return source.get_pulse_data(payload, pulse_name=DATA_FETCH_PULSE_NAME)


def test_source_is_yfinance_only_pulser_with_three_original_pulses(
    fake_provider: Any,
) -> None:
    source = YFinanceDataSource(provider=fake_provider)

    assert YFinanceSource is YFinanceDataSource
    assert isinstance(source, Pulser)
    assert source.name == "YFinanceDataSource"
    assert source.agent_card["pit_type"] == "DataSource"
    assert source.agent_card["party"] == "attas"
    assert source.vendor_id == "yfinance"
    assert source.provider_version == "test-double-1.0"
    assert {
        item["pulse_name"] for item in source.supported_pulses
    } == {
        DATA_SPEC_PULSE_NAME,
        DATA_AVAILABILITY_PULSE_NAME,
        DATA_FETCH_PULSE_NAME,
    }
    assert [item.endpoint_id for item in source.endpoint_catalog] == [
        "yfinance.ticker.fast_info",
        "yfinance.ticker.history",
        "yfinance.ticker.info",
    ]


def test_catalog_spec_and_availability_are_metadata_only(
    fake_provider: Any,
) -> None:
    source = YFinanceDataSource(provider=fake_provider)

    availability = source.get_pulse_data(
        {"query": "", "limit": 100},
        pulse_name=DATA_AVAILABILITY_PULSE_NAME,
    )
    specification = source.get_pulse_data(
        {"endpoint_id": "yfinance.ticker.fast_info"},
        pulse_name=DATA_SPEC_PULSE_NAME,
    )

    assert fake_provider.calls == []
    assert availability["source"]["source_id"] == "yfinance"
    assert availability["available"] is True
    assert availability["endpoint_count"] == 3
    assert {item["endpoint_id"] for item in availability["datasets"]} == {
        "yfinance.ticker.fast_info",
        "yfinance.ticker.history",
        "yfinance.ticker.info",
    }
    assert specification["count"] == 1
    assert specification["endpoints"][0]["operation"] == (
        "yfinance.Ticker.fast_info"
    )
    assert specification["snapshot"]["endpoint_count"] == 3


def test_history_fetch_returns_provider_and_canonical_views(
    fake_provider: Any,
) -> None:
    source = YFinanceDataSource(provider=fake_provider)

    result = fetch(
        source,
        "yfinance.ticker.history",
        parameters={"symbol": "aapl", "period": "1mo", "interval": "1d"},
        fields=["timestamp", "open", "close", "volume"],
    )

    assert result["status"] == "completed"
    assert result["error"] == ""
    assert result["dataset_id"] == "yfinance.ticker.history"
    assert result["data"]["items"][0]["Close"] == 227.4
    expected = {
        "timestamp": "2026-08-24T00:00:00",
        "open": 226.1,
        "close": 227.4,
        "volume": 41_000_000,
    }
    assert result["canonical_data"]["items"][0].items() >= expected.items()
    assert result["attas_pulse"]["pulse_name"] == DATA_FETCH_PULSE_NAME
    assert [item["operation"] for item in fake_provider.calls] == [
        "Ticker",
        "history",
    ]
    assert fake_provider.calls[0]["symbol"] == "AAPL"


@pytest.mark.parametrize(
    ("endpoint_id", "operation", "expected"),
    (
        (
            "yfinance.ticker.fast_info",
            "fast_info",
            {"symbol": "AAPL", "last_price": 230.2, "currency": "USD"},
        ),
        (
            "yfinance.ticker.info",
            "info",
            {
                "symbol": "AAPL",
                "company_name": "Apple Inc.",
                "sector": "Technology",
            },
        ),
    ),
)
def test_mapping_fetches_use_only_the_documented_yfinance_operation(
    fake_provider: Any,
    endpoint_id: str,
    operation: str,
    expected: dict[str, Any],
) -> None:
    source = YFinanceDataSource(provider=fake_provider)

    result = fetch(source, endpoint_id, parameters={"symbol": "AAPL"})

    assert result["status"] == "completed"
    assert result["canonical_data"].items() >= expected.items()
    assert [item["operation"] for item in fake_provider.calls] == [
        "Ticker",
        operation,
    ]


def test_provider_failure_is_explicit_and_never_replaced_with_demo_data(
    fake_provider: Any,
) -> None:
    fake_provider.fail(
        "history",
        "AAPL",
        RuntimeError("Yahoo provider unavailable for this test"),
    )
    source = YFinanceDataSource(provider=fake_provider)

    result = fetch(
        source,
        "yfinance.ticker.history",
        parameters={"symbol": "AAPL", "period": "1mo"},
    )

    assert result["status"] == "failed"
    assert result["data"] == {}
    assert result["canonical_data"] == {}
    assert result["error"] == "Yahoo provider unavailable for this test"
    assert result["warnings"] == []
    assert [item["operation"] for item in fake_provider.calls] == [
        "Ticker",
        "history",
    ]
