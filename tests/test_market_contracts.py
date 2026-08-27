"""The reduced demo keeps the original Data Agent Pulse contract names."""

from __future__ import annotations

from data_agent_network_demo.contracts import (
    ACCESS_MODE_PULSE,
    DATA_ADVICE_PULSE,
    DATA_AVAILABILITY_PULSE,
    DATA_FETCH_PULSE,
    DATA_REQUEST_PULSE,
    DATA_SOURCE_STATUS_PULSE,
    DATA_SPEC_PULSE,
    ENDPOINT_BY_ID,
    YFINANCE_ENDPOINTS,
)


def test_six_canonical_network_pulses_are_plain_original_shaped_dicts() -> None:
    pulses = (
        DATA_REQUEST_PULSE,
        DATA_ADVICE_PULSE,
        DATA_SOURCE_STATUS_PULSE,
        DATA_SPEC_PULSE,
        DATA_AVAILABILITY_PULSE,
        DATA_FETCH_PULSE,
    )

    assert all(isinstance(pulse, dict) for pulse in pulses)
    assert {pulse["name"] for pulse in pulses} == {
        "data_request",
        "data_advice",
        "data_source_status",
        "data_spec",
        "data_availability",
        "data_fetch",
    }
    for pulse in pulses:
        assert pulse["pulse_name"] == pulse["name"]
        assert pulse["pulse_address"] == f"plaza://pulse/attas/{pulse['name']}"
        assert pulse["input_schema"]["type"] == "object"
        assert pulse["output_schema"]["type"] == "object"


def test_yfinance_catalog_contains_only_three_documented_operations() -> None:
    assert len(YFINANCE_ENDPOINTS) == 3
    assert set(ENDPOINT_BY_ID) == {
        "yfinance.ticker.fast_info",
        "yfinance.ticker.history",
        "yfinance.ticker.info",
    }
    assert {endpoint.vendor_id for endpoint in YFINANCE_ENDPOINTS} == {"yfinance"}
    assert {endpoint.operation for endpoint in YFINANCE_ENDPOINTS} == {
        "yfinance.Ticker.fast_info",
        "yfinance.Ticker.history",
        "yfinance.Ticker.info",
    }
    assert all(endpoint.executable for endpoint in YFINANCE_ENDPOINTS)
    assert all(
        any(parameter.name == "symbol" and parameter.required for parameter in endpoint.parameters)
        for endpoint in YFINANCE_ENDPOINTS
    )


def test_direct_source_access_mode_is_not_a_consultant_proxy() -> None:
    assert ACCESS_MODE_PULSE == "data_source_pulse"
    assert DATA_FETCH_PULSE["input_schema"]["properties"]["access_mode"]["enum"] == [
        "data_source_pulse"
    ]
