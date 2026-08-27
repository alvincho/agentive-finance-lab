"""Faithful YFinance-only reduction of the original Data Agent Network."""

from __future__ import annotations

from typing import Any

from phemacast_lite import Persona, Pulser
from prompits_lite import BaseAgent, Pit, StandbyAgent

from data_agent_network_demo.agents import DataConsultantPersona, DataUserPersona
from data_agent_network_demo.contracts import (
    DATA_ADVICE_PULSE_NAME,
    DATA_AVAILABILITY_PULSE_NAME,
    DATA_FETCH_PULSE_NAME,
    DATA_REQUEST_PULSE_NAME,
    DATA_SOURCE_STATUS_PULSE_NAME,
    DATA_SPEC_PULSE_NAME,
)
from data_agent_network_demo.workflow import DataAgentNetworkDemo, DemoQuestion
from data_agent_network_demo.yfinance_source import YFinanceDataSource


def pulse_names(agent: Pulser) -> set[str]:
    return {
        str(item.get("pulse_name") or item.get("name"))
        for item in agent.supported_pulses
    }


def test_demo_registers_exactly_three_original_network_participants(
    fake_provider: Any,
) -> None:
    demo = DataAgentNetworkDemo(provider=fake_provider)
    members = demo.build_local_network()

    assert set(members) == {
        "data_user",
        "data_consultant",
        "data_sources",
        "plaza",
    }
    assert set(demo.data_sources) == {"yfinance"}
    source = demo.data_sources["yfinance"]
    assert isinstance(source, YFinanceDataSource)
    assert isinstance(source, Pulser)
    assert not isinstance(source, Persona)
    assert isinstance(demo.data_consultant, DataConsultantPersona)
    assert isinstance(demo.data_user, DataUserPersona)

    directory = demo.plaza.directory()
    assert [(item["name"], item["pit_type"]) for item in directory] == [
        ("YFinanceDataSource", "DataSource"),
        ("DataConsultant", "Persona"),
        ("DataUser", "Persona"),
    ]
    assert len(directory) == 3
    assert all(
        isinstance(participant, (Pit, BaseAgent, StandbyAgent))
        for participant in (source, demo.data_consultant, demo.data_user)
    )

    assert pulse_names(source) == {
        DATA_SPEC_PULSE_NAME,
        DATA_AVAILABILITY_PULSE_NAME,
        DATA_FETCH_PULSE_NAME,
    }
    assert pulse_names(demo.data_consultant) == {
        DATA_ADVICE_PULSE_NAME,
        DATA_SOURCE_STATUS_PULSE_NAME,
    }
    assert pulse_names(demo.data_user) == {
        DATA_REQUEST_PULSE_NAME,
        DATA_SOURCE_STATUS_PULSE_NAME,
        DATA_SPEC_PULSE_NAME,
        DATA_FETCH_PULSE_NAME,
    }


def test_consultant_startup_sync_uses_empty_availability_query_without_provider_io(
    fake_provider: Any,
    monkeypatch: Any,
) -> None:
    calls: list[dict[str, Any]] = []
    original = YFinanceDataSource.data_availability

    def record_availability(
        source: YFinanceDataSource,
        input_data: dict[str, Any],
    ) -> dict[str, Any]:
        calls.append(dict(input_data))
        return original(source, input_data)

    monkeypatch.setattr(YFinanceDataSource, "data_availability", record_availability)
    demo = DataAgentNetworkDemo(provider=fake_provider)
    demo.build_local_network()

    assert len(calls) == 1
    assert calls[0]["query"] == ""
    assert calls[0]["use_case"] == "consultant memory synchronization"
    assert calls[0]["limit"] == 100
    assert fake_provider.calls == []
    assert demo.data_consultant.source_memory_status()["source_count"] == 1
    assert demo.data_consultant.source_memory_status()["dataset_count"] == 3


def test_data_request_routes_from_data_user_to_data_consultant_only(
    fake_provider: Any,
    monkeypatch: Any,
) -> None:
    demo = DataAgentNetworkDemo(provider=fake_provider)
    demo.build_local_network()
    events: list[tuple[str, str]] = []
    original_advice = demo.data_consultant.data_advice

    def record_advice(input_data: dict[str, Any]) -> dict[str, Any]:
        events.append(("DataConsultant", DATA_ADVICE_PULSE_NAME))
        return original_advice(input_data)

    monkeypatch.setattr(demo.data_consultant, "data_advice", record_advice)
    result = demo.ask(
        DemoQuestion(
            query="historical daily prices and volume for AAPL",
            use_case="research prototype",
        )
    )

    assert events == [("DataConsultant", DATA_ADVICE_PULSE_NAME)]
    assert result["request"]["query"] == (
        "historical daily prices and volume for AAPL"
    )
    assert result["source_count"] == 1
    assert result["sources"][0]["source_id"] == "yfinance"
    assert fake_provider.calls == []


def test_data_user_uses_consultant_status_then_calls_source_spec_and_fetch_directly(
    fake_provider: Any,
    monkeypatch: Any,
) -> None:
    demo = DataAgentNetworkDemo(provider=fake_provider)
    demo.build_local_network()
    source = demo.data_sources["yfinance"]
    events: list[tuple[str, str]] = []

    original_status = demo.data_consultant.data_source_status
    original_spec = source.data_spec
    original_fetch = source.data_fetch

    def record_status(input_data=None):
        events.append(("DataConsultant", DATA_SOURCE_STATUS_PULSE_NAME))
        return original_status(input_data)

    def record_spec(input_data):
        events.append(("YFinanceDataSource", DATA_SPEC_PULSE_NAME))
        return original_spec(input_data)

    def record_fetch(input_data):
        events.append(("YFinanceDataSource", DATA_FETCH_PULSE_NAME))
        return original_fetch(input_data)

    monkeypatch.setattr(demo.data_consultant, "data_source_status", record_status)
    monkeypatch.setattr(source, "data_spec", record_spec)
    monkeypatch.setattr(source, "data_fetch", record_fetch)

    specification = demo.data_user.get_pulse_data(
        {"source_id": "yfinance", "query": "historical prices"},
        pulse_name=DATA_SPEC_PULSE_NAME,
    )
    assert events == [
        ("DataConsultant", DATA_SOURCE_STATUS_PULSE_NAME),
        ("YFinanceDataSource", DATA_SPEC_PULSE_NAME),
    ]
    assert specification["endpoints"][0]["endpoint_id"] == (
        "yfinance.ticker.history"
    )
    assert fake_provider.calls == []

    events.clear()
    fetched = demo.fetch(
        DemoQuestion(
            query="historical prices",
            fetch_source_id="yfinance",
            fetch_endpoint_id="yfinance.ticker.history",
            fetch_parameters={"symbol": "AAPL", "period": "1mo"},
        )
    )
    assert events == [
        ("DataConsultant", DATA_SOURCE_STATUS_PULSE_NAME),
        ("YFinanceDataSource", DATA_FETCH_PULSE_NAME),
    ]
    assert fetched["status"] == "completed"
    assert fetched["dataset_id"] == "yfinance.ticker.history"
    assert [item["operation"] for item in fake_provider.calls] == [
        "Ticker",
        "history",
    ]


def test_data_user_requires_an_explicit_consultant_selected_source(
    fake_provider: Any,
) -> None:
    demo = DataAgentNetworkDemo(provider=fake_provider)
    demo.build_local_network()

    specification = demo.data_user.get_pulse_data(
        {"query": "historical prices"},
        pulse_name=DATA_SPEC_PULSE_NAME,
    )
    fetched = demo.data_user.get_pulse_data(
        {
            "endpoint_id": "yfinance.ticker.history",
            "parameters": {"symbol": "AAPL"},
        },
        pulse_name=DATA_FETCH_PULSE_NAME,
    )

    assert specification["count"] == 0
    assert specification["source"]["source_id"] == ""
    assert fetched["status"] == "failed"
    assert fetched["error"] == "source_id is required."
    assert fake_provider.calls == []


def test_consultant_cached_catalog_does_not_claim_an_unregistered_source_is_ready(
    fake_provider: Any,
) -> None:
    demo = DataAgentNetworkDemo(provider=fake_provider)
    demo.build_local_network()
    source = demo.data_sources["yfinance"]

    assert demo.data_consultant.data_source_status()["sources"][0]["available"] is True

    demo.plaza.unregister(source)
    status = demo.data_consultant.data_source_status()

    assert status["source_count"] == 1
    assert status["sources"][0]["available"] is False
    assert status["sources"][0]["stale"] is True
    assert status["sources"][0]["connectivity"] == {
        **status["sources"][0]["connectivity"],
        "status": "unavailable",
        "address": "",
    }
    assert status["discovery"]["discovered_source_count"] == 0
    assert fake_provider.calls == []


def test_every_cross_agent_demo_call_uses_plaza_practice_routing(
    fake_provider: Any,
    monkeypatch: Any,
) -> None:
    demo = DataAgentNetworkDemo(provider=fake_provider)
    demo.build_local_network()
    calls: list[tuple[str, str, str, str]] = []
    original_invoke = demo.plaza.invoke_practice

    def record_invoke(*, caller, target, practice_id, content=None):
        destination = demo.plaza.resolve_agent(target)
        calls.append(
            (
                caller.name,
                destination.name,
                practice_id,
                str((content or {}).get("pulse_name") or ""),
            )
        )
        return original_invoke(
            caller=caller,
            target=target,
            practice_id=practice_id,
            content=content,
        )

    monkeypatch.setattr(demo.plaza, "invoke_practice", record_invoke)

    demo.ask(DemoQuestion(query="historical daily prices for AAPL"))
    demo.data_user.get_pulse_data(
        {"source_id": "yfinance", "endpoint_id": "yfinance.ticker.history"},
        pulse_name=DATA_SPEC_PULSE_NAME,
    )
    demo.fetch(
        DemoQuestion(
            query="historical daily prices for AAPL",
            fetch_source_id="yfinance",
            fetch_endpoint_id="yfinance.ticker.history",
            fetch_parameters={"symbol": "AAPL", "period": "1mo"},
        )
    )

    assert calls == [
        ("DataUser", "DataConsultant", "get_pulse_data", DATA_ADVICE_PULSE_NAME),
        (
            "DataUser",
            "DataConsultant",
            "get_pulse_data",
            DATA_SOURCE_STATUS_PULSE_NAME,
        ),
        (
            "DataUser",
            "YFinanceDataSource",
            "get_pulse_data",
            DATA_SPEC_PULSE_NAME,
        ),
        (
            "DataUser",
            "DataConsultant",
            "get_pulse_data",
            DATA_SOURCE_STATUS_PULSE_NAME,
        ),
        (
            "DataUser",
            "YFinanceDataSource",
            "get_pulse_data",
            DATA_FETCH_PULSE_NAME,
        ),
    ]


def test_original_demo_question_and_run_harness_are_retained(
    fake_provider: Any,
) -> None:
    question = DemoQuestion(
        query="current quote for AAPL",
        use_case="demo",
        preferences={"cost": "free"},
        fetch_source_id="yfinance",
        fetch_endpoint_id="yfinance.ticker.fast_info",
        fetch_parameters={"symbol": "AAPL"},
    )
    demo = DataAgentNetworkDemo(provider=fake_provider)

    results = demo.run([question])

    assert isinstance(results, tuple)
    assert len(results) == 1
    assert results[0]["question"] == {
        "query": "current quote for AAPL",
        "use_case": "demo",
        "preferences": {"cost": "free"},
    }
    assert results[0]["advice"]["source_count"] == 1
    assert results[0]["fetch"]["status"] == "completed"
    assert set(demo.data_sources) == {"yfinance"}
