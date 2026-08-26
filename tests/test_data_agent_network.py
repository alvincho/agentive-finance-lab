"""End-to-end behavior of the Data User and Data Consultant network."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json

from data_agent_network_demo.agents import DataUser
from data_agent_network_demo.contracts import MarketDataError
from data_agent_network_demo.workflow import build_network, run_demo


def test_complete_path_delegates_one_structured_comparison_to_the_consultant(
    fake_source: object,
) -> None:
    result = run_demo(
        primary_symbol=" aapl ",
        benchmark_symbol="spy",
        period="1mo",
        source=fake_source,
    )

    assert fake_source.calls == [("AAPL", "1mo"), ("SPY", "1mo")]
    assert result["status"] == "complete"
    assert result["request"]["primary_symbol"] == "AAPL"
    assert result["request"]["benchmark_symbol"] == "SPY"
    assert result["request"]["period"] == "1mo"

    consultant = result["consultant"]
    assert consultant["status"] == "complete"
    assert consultant["source"]["provider"] == "yfinance"
    assert consultant["source"]["version"] == "test-double"
    assert set(consultant["metrics"]) == {"AAPL", "SPY"}
    assert consultant["coverage"]["observations"] == 18
    assert consultant["relative"]["return_spread_pct_points"] == 12.0
    assert len(consultant["series"]) == 18
    assert consultant["errors"] == []

    assert result["acceptance"]["status"] == "pass"
    assert result["answer"]["headline"]
    assert "investment advice" in result["answer"]["caveat"].lower()
    assert result["network"]["dependency_direction"] == (
        "demo -> phemacast-lite -> prompits-lite"
    )


def test_result_preserves_yfinance_provenance_and_one_routed_trace(
    fake_source: object,
) -> None:
    result = run_demo(
        primary_symbol="AAPL",
        benchmark_symbol="SPY",
        period="1mo",
        source=fake_source,
    )

    serialized_provenance = json.dumps(result["consultant"]["provenance"])
    assert "yfinance.Ticker.history" in serialized_provenance
    assert '"symbol": "AAPL"' in serialized_provenance
    assert '"symbol": "SPY"' in serialized_provenance
    assert '"interval": "1d"' in serialized_provenance
    assert '"auto_adjust": true' in serialized_provenance

    stages = [event["stage"] for event in result["trace"]]
    assert stages[0] == "client.submit"
    assert stages.count("plaza.discover") == 1
    assert stages.count("plaza.matches") == 1
    assert stages.count("plaza.route") == 2
    assert stages.count("pulse.execute") == 2
    assert stages.count("pulse.complete") == 2
    assert stages.count("plaza.return") == 2
    assert "yfinance.request" in stages
    assert "yfinance.response" in stages
    assert "consultant.calculate" in stages
    assert "data-user.validate" in stages
    assert "data-user.accept" in stages
    assert [event["sequence"] for event in result["trace"]] == list(
        range(1, len(result["trace"]) + 1)
    )
    assert result["correlation_id"]


def test_data_user_rejects_a_comparison_that_misses_the_period_minimum(
    fake_source: object,
) -> None:
    result = run_demo(
        primary_symbol="AAPL",
        benchmark_symbol="SPY",
        period="1y",
        source=fake_source,
    )

    assert result["consultant"]["status"] == "needs-review"
    assert result["consultant"]["coverage"]["observations"] == 18
    assert result["consultant"]["coverage"]["minimum_required"] == 180
    assert set(result["consultant"]["metrics"]) == {"AAPL", "SPY"}
    assert result["status"] == "needs-review"
    assert result["acceptance"]["status"] == "fail"
    assert result["acceptance"]["failed_checks"] == [
        "consultant completed without provider errors",
        "requested coverage",
        "no hard quality failures",
    ]


def test_quality_warning_is_accepted_with_warnings_but_not_presented_as_complete(
    fake_source: object,
) -> None:
    fake_source.histories["AAPL"] = replace(
        fake_source.histories["AAPL"],
        warnings=("yfinance metadata was incomplete.",),
    )

    result = run_demo(
        primary_symbol="AAPL",
        benchmark_symbol="SPY",
        period="1mo",
        source=fake_source,
    )

    assert result["consultant"]["status"] == "complete"
    assert result["acceptance"]["accepted"] is True
    assert result["acceptance"]["status"] == "pass-with-warnings"
    assert result["acceptance"]["failed_checks"] == []
    assert "yfinance metadata was incomplete." in result["acceptance"]["warnings"]
    assert result["status"] == "needs-review"


def test_acceptance_rejects_tampered_provenance_metrics_and_hard_quality_failures(
    fake_source: object,
) -> None:
    result = run_demo(
        primary_symbol="AAPL",
        benchmark_symbol="SPY",
        period="1mo",
        source=fake_source,
    )
    request = result["request"]
    consultant = result["consultant"]

    bad_provenance = deepcopy(consultant)
    bad_provenance["provenance"][0]["query"]["actions"] = True
    provenance_acceptance = DataUser._accept(bad_provenance, request)
    assert "exact query provenance" in provenance_acceptance["failed_checks"]

    bad_metrics = deepcopy(consultant)
    bad_metrics["metrics"]["AAPL"]["total_return_pct"] = float("nan")
    metrics_acceptance = DataUser._accept(bad_metrics, request)
    assert "complete finite metrics" in metrics_acceptance["failed_checks"]

    inconsistent_coverage = deepcopy(consultant)
    inconsistent_coverage["metrics"]["AAPL"]["observations"] -= 1
    coverage_acceptance = DataUser._accept(inconsistent_coverage, request)
    assert "complete finite metrics" in coverage_acceptance["failed_checks"]

    hard_failure = deepcopy(consultant)
    hard_failure["quality"]["checks"].append(
        {"name": "provider evidence", "status": "fail", "detail": "Evidence failed."}
    )
    quality_acceptance = DataUser._accept(hard_failure, request)
    assert "no hard quality failures" in quality_acceptance["failed_checks"]


def test_one_provider_failure_preserves_the_successful_history_without_comparing(
    fake_source: object,
) -> None:
    fake_source.failures["SPY"] = MarketDataError(
        symbol="SPY",
        code="no_history",
        message="yfinance returned no daily price history for SPY.",
    )

    result = run_demo(
        primary_symbol="AAPL",
        benchmark_symbol="SPY",
        period="1mo",
        source=fake_source,
    )

    assert result["status"] == "partial"
    assert result["consultant"]["status"] == "partial"
    assert result["consultant"]["metrics"] == {}
    assert result["consultant"]["series"] == []
    assert result["consultant"]["errors"] == [
        {
            "symbol": "SPY",
            "code": "no_history",
            "message": "yfinance returned no daily price history for SPY.",
        }
    ]
    assert [item["symbol"] for item in result["consultant"]["provenance"]] == ["AAPL"]
    assert result["acceptance"]["status"] == "fail"
    assert "incomplete" in result["answer"]["headline"].lower()
    assert result["consultant"]["source"]["provider"] == "yfinance"
    assert "yfinance.error" in [event["stage"] for event in result["trace"]]


def test_rate_limit_stops_the_second_request_without_inventing_data(
    fake_source: object,
) -> None:
    fake_source.failures["AAPL"] = MarketDataError(
        symbol="AAPL",
        code="rate_limited",
        message="yfinance was rate-limited by its upstream service.",
    )

    result = run_demo(
        primary_symbol="AAPL",
        benchmark_symbol="SPY",
        period="1mo",
        source=fake_source,
    )

    assert fake_source.calls == [("AAPL", "1mo")]
    assert result["status"] == "unavailable"
    assert result["consultant"]["provenance"] == []
    assert result["consultant"]["metrics"] == {}
    assert result["consultant"]["errors"] == [
        {
            "symbol": "AAPL",
            "code": "rate_limited",
            "message": "yfinance was rate-limited by its upstream service.",
        },
        {
            "symbol": "SPY",
            "code": "not_attempted",
            "message": "Request not attempted after the provider rate limit.",
        },
    ]


def test_network_registers_two_personas_with_discoverable_typed_pulses(
    fake_source: object,
) -> None:
    network = build_network(source=fake_source)
    cards = {card.name: card for card in network.plaza.directory()}
    description = network.describe()

    assert set(cards) == {"Data User", "Data Consultant"}
    assert description["route"] == [
        "Data User",
        "Plaza",
        "Data Consultant",
        "yfinance",
    ]
    assert description["provider"] == {
        "name": "yfinance",
        "version": "test-double",
        "only_external_financial_data_source": True,
    }
    assert cards["Data User"].pit_type == "Persona"
    assert cards["Data User"].labels["role"] == "data-user"
    assert cards["Data Consultant"].labels["role"] == "data-consultant"

    user_pulse = cards["Data User"].capabilities[0]
    consultant_pulse = cards["Data Consultant"].capabilities[0]
    assert user_pulse.name == "compare_market_data"
    assert user_pulse.input_schema == {
        "primary_symbol": {"types": ["str"], "required": True},
        "benchmark_symbol": {"types": ["str"], "required": True},
        "period": {"types": ["str"], "required": True},
    }
    assert consultant_pulse.name == "analyze_market_history"
    assert consultant_pulse.input_schema == user_pulse.input_schema
