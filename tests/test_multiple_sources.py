"""Multiple-source Data Agent Network and provider-boundary tests."""

from __future__ import annotations

import json
from typing import Any

from phemacast_lite import Persona, Pulser

from data_agent_network_demo.contracts import (
    DATA_AVAILABILITY_PULSE_NAME,
    DATA_FETCH_PULSE_NAME,
    DATA_SPEC_PULSE_NAME,
)
from data_agent_network_demo.multiple_sources_workflow import (
    MultipleSourceDataAgentNetworkDemo,
)
from data_agent_network_demo.provider_sources import (
    AlphaVantageDataSource,
    FREDDataSource,
)
from data_agent_network_demo.workflow import DemoQuestion


class RecordingHttpClient:
    """Deterministic JSON client that records the source-owned provider call."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def get_json(self, url: str, *, params: dict[str, Any]) -> dict[str, Any]:
        self.calls.append({"url": url, "params": dict(params)})
        if "alphavantage" in url:
            if params.get("function") == "TIME_SERIES_DAILY":
                return {
                    "Meta Data": {"2. Symbol": params["symbol"]},
                    "Time Series (Daily)": {
                        "2026-08-26": {
                            "1. open": "228.30",
                            "2. high": "231.00",
                            "3. low": "227.90",
                            "4. close": "230.20",
                            "5. volume": "42250000",
                        }
                    },
                }
            return {"Global Quote": {"01. symbol": params.get("symbol", "")}}
        return {
            "observations": [
                {
                    "realtime_start": "2026-08-27",
                    "realtime_end": "2026-08-27",
                    "date": "2026-07-01",
                    "value": "322.132",
                }
            ]
        }


def pulse_names(agent: Pulser) -> set[str]:
    return {
        str(item.get("pulse_name") or item.get("name"))
        for item in agent.supported_pulses
    }


def test_alpha_vantage_and_fred_are_data_source_pulsers_with_original_pulses() -> None:
    sources = [AlphaVantageDataSource(), FREDDataSource()]

    for source in sources:
        assert isinstance(source, Pulser)
        assert not isinstance(source, Persona)
        assert source.agent_card["pit_type"] == "DataSource"
        assert source.agent_card["party"] == "attas"
        assert source.agent_card["meta"]["data_agent_role"] == "source"
        assert pulse_names(source) == {
            DATA_SPEC_PULSE_NAME,
            DATA_AVAILABILITY_PULSE_NAME,
            DATA_FETCH_PULSE_NAME,
        }

    assert [endpoint.endpoint_id for endpoint in sources[0].endpoint_catalog] == [
        "alpha_vantage.time_series_daily",
        "alpha_vantage.global_quote",
        "alpha_vantage.overview",
    ]
    assert [endpoint.endpoint_id for endpoint in sources[1].endpoint_catalog] == [
        "fred.fred_series_observations",
        "fred.fred_series_vintagedates",
    ]


def test_catalog_advice_is_offline_and_syncs_all_three_sources(
    fake_provider: Any,
) -> None:
    alpha_client = RecordingHttpClient()
    fred_client = RecordingHttpClient()
    demo = MultipleSourceDataAgentNetworkDemo(
        provider=fake_provider,
        alpha_vantage_http_client=alpha_client,
        fred_http_client=fred_client,
    )

    demo.build_local_network()

    assert [(item["name"], item["pit_type"]) for item in demo.plaza.directory()] == [
        ("YFinanceDataSource", "DataSource"),
        ("AlphaVantageDataSource", "DataSource"),
        ("FREDDataSource", "DataSource"),
        ("DataConsultant", "Persona"),
        ("DataUser", "Persona"),
    ]
    assert set(demo.data_sources) == {"yfinance", "alpha_vantage", "fred"}
    assert demo.data_consultant.source_memory_status()["source_count"] == 3
    assert demo.data_consultant.source_memory_status()["dataset_count"] == 8
    assert fake_provider.calls == []
    assert alpha_client.calls == []
    assert fred_client.calls == []

    cases = (
        (
            "Which sources provide daily AAPL prices and volume, and how do their contracts differ?",
            ["yfinance", "alpha_vantage"],
        ),
        (
            "Which source provides U.S. CPI observations and revision vintage dates?",
            ["fred"],
        ),
        (
            "Compare AAPL company profile, sector, industry, and market-cap data across sources.",
            ["yfinance", "alpha_vantage"],
        ),
    )
    for query, expected_sources in cases:
        result = demo.ask(DemoQuestion(query=query))
        assert [source["source_id"] for source in result["sources"]] == expected_sources
        assert result["llm"]["used"] is False

    assert fake_provider.calls == []
    assert alpha_client.calls == []
    assert fred_client.calls == []


def test_missing_source_owned_credentials_are_explicit_and_raw_keys_are_rejected() -> None:
    alpha = AlphaVantageDataSource()
    fred = FREDDataSource()

    alpha_result = alpha.get_pulse_data(
        {
            "endpoint_id": "alpha_vantage.time_series_daily",
            "parameters": {"symbol": "AAPL"},
        },
        pulse_name=DATA_FETCH_PULSE_NAME,
    )
    fred_result = fred.get_pulse_data(
        {
            "endpoint_id": "fred.fred_series_observations",
            "parameters": {"series_id": "CPIAUCSL"},
        },
        pulse_name=DATA_FETCH_PULSE_NAME,
    )
    raw_key_result = fred.get_pulse_data(
        {
            "endpoint_id": "fred.fred_series_observations",
            "parameters": {"series_id": "CPIAUCSL", "api_key": "not-allowed"},
        },
        pulse_name=DATA_FETCH_PULSE_NAME,
    )

    assert alpha_result["status"] == "authentication_required"
    assert fred_result["status"] == "authentication_required"
    assert alpha_result["data"] == fred_result["data"] == {}
    assert raw_key_result["status"] == "failed"
    assert raw_key_result["error"] == (
        "Raw API credentials are not accepted in data_fetch pulses."
    )


def test_source_owned_http_execution_uses_keys_without_returning_them() -> None:
    alpha_client = RecordingHttpClient()
    fred_client = RecordingHttpClient()
    alpha = AlphaVantageDataSource(
        http_client=alpha_client,
        api_key="alpha-server-secret",
    )
    fred = FREDDataSource(
        http_client=fred_client,
        api_key="fred-server-secret",
    )

    alpha_result = alpha.get_pulse_data(
        {
            "endpoint_id": "alpha_vantage.time_series_daily",
            "parameters": {"symbol": "AAPL", "outputsize": "compact"},
        },
        pulse_name=DATA_FETCH_PULSE_NAME,
    )
    fred_result = fred.get_pulse_data(
        {
            "endpoint_id": "fred.fred_series_observations",
            "parameters": {"series_id": "CPIAUCSL", "limit": 1},
        },
        pulse_name=DATA_FETCH_PULSE_NAME,
    )

    assert alpha_result["status"] == "completed"
    assert alpha_client.calls == [
        {
            "url": "https://www.alphavantage.co/query",
            "params": {
                "function": "TIME_SERIES_DAILY",
                "symbol": "AAPL",
                "outputsize": "compact",
                "datatype": "json",
                "apikey": "alpha-server-secret",
            },
        }
    ]
    assert alpha_result["canonical_data"]["Time Series (Daily)"]["2026-08-26"] == {
        "open": "228.30",
        "high": "231.00",
        "low": "227.90",
        "close": "230.20",
        "volume": "42250000",
    }

    assert fred_result["status"] == "completed"
    assert fred_client.calls == [
        {
            "url": "https://api.stlouisfed.org/fred/series/observations",
            "params": {
                "file_type": "json",
                "series_id": "CPIAUCSL",
                "limit": 1,
                "api_key": "fred-server-secret",
            },
        }
    ]
    assert fred_result["canonical_data"]["observations"][0]["timestamp"] == (
        "2026-07-01"
    )
    serialized = json.dumps({"alpha": alpha_result, "fred": fred_result})
    assert "alpha-server-secret" not in serialized
    assert "fred-server-secret" not in serialized


def test_data_user_resolves_then_calls_the_selected_source_directly(
    fake_provider: Any,
    monkeypatch: Any,
) -> None:
    demo = MultipleSourceDataAgentNetworkDemo(provider=fake_provider)
    demo.build_local_network()
    alpha = demo.data_sources["alpha_vantage"]
    events: list[tuple[str, str]] = []
    original_status = demo.data_consultant.data_source_status
    original_spec = alpha.data_spec

    def record_status(input_data=None):
        events.append(("DataConsultant", "data_source_status"))
        return original_status(input_data)

    def record_spec(input_data):
        events.append(("AlphaVantageDataSource", "data_spec"))
        return original_spec(input_data)

    monkeypatch.setattr(demo.data_consultant, "data_source_status", record_status)
    monkeypatch.setattr(alpha, "data_spec", record_spec)

    result = demo.data_user.get_pulse_data(
        {
            "source_id": "alpha_vantage",
            "endpoint_id": "alpha_vantage.overview",
        },
        pulse_name=DATA_SPEC_PULSE_NAME,
    )

    assert events == [
        ("DataConsultant", "data_source_status"),
        ("AlphaVantageDataSource", "data_spec"),
    ]
    assert result["count"] == 1
    assert result["endpoints"][0]["endpoint_id"] == "alpha_vantage.overview"
    assert fake_provider.calls == []
