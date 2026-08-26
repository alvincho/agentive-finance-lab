"""Deterministic checks for the consultant's descriptive calculations."""

from __future__ import annotations

from datetime import date

import pytest

from data_agent_network_demo.analytics import compare_histories


def test_comparison_aligns_adjusted_closes_and_reports_useful_metrics(
    history_factory: object,
) -> None:
    dates = (
        "2024-01-02",
        "2024-01-03",
        "2024-01-04",
        "2024-01-05",
        "2024-01-08",
    )
    primary = history_factory("AAPL", (100, 110, 99, 120, 126), dates=dates)
    benchmark = history_factory("SPY", (100, 105, 102, 108, 110), dates=dates)

    result = compare_histories(
        primary,
        benchmark,
        minimum_observations=5,
        minimum_span_days=5,
        as_of_date=date(2024, 1, 10),
    )

    assert result["status"] == "complete"
    assert result["coverage"] == {
        "start": "2024-01-02",
        "end": "2024-01-08",
        "observations": 5,
        "minimum_required": 5,
        "span_days": 6,
        "minimum_span_days": 5,
        "sufficient": True,
        "primary_rows": 5,
        "benchmark_rows": 5,
    }
    assert result["metrics"]["AAPL"] == {
        "symbol": "AAPL",
        "name": "AAPL test instrument",
        "currency": "USD",
        "exchange": "TEST",
        "instrument_type": "EQUITY",
        "latest_close": 126.0,
        "start_close": 100.0,
        "total_return_pct": 26.0,
        "annualized_volatility_pct": 205.591,
        "max_drawdown_pct": -10.0,
        "period_high": 126.0,
        "period_low": 99.0,
        "average_volume": 1002,
        "observations": 5,
    }
    assert result["metrics"]["SPY"]["total_return_pct"] == 10.0
    assert result["relative"] == {
        "return_spread_pct_points": 16.0,
        "daily_return_correlation": 0.964,
        "beta_to_benchmark": 3.16,
    }
    assert result["series"][0] == {
        "date": "2024-01-02",
        "AAPL": 100.0,
        "SPY": 100.0,
    }
    assert result["series"][-1] == {
        "date": "2024-01-08",
        "AAPL": 126.0,
        "SPY": 110.0,
    }
    assert {check["status"] for check in result["quality"]["checks"]} == {"pass"}
    assert result["quality"]["warnings"] == []


def test_comparison_surfaces_alignment_currency_freshness_and_overlap_warnings(
    history_factory: object,
) -> None:
    primary = history_factory(
        "AAPL",
        (90, 100, 105, 110),
        dates=("2023-12-29", "2024-01-02", "2024-01-03", "2024-01-04"),
        currency="USD",
        warnings=("Primary provider warning.",),
    )
    benchmark = history_factory(
        "^N225",
        (30_000, 30_100, 30_050),
        dates=("2024-01-02", "2024-01-03", "2024-01-04"),
        currency="JPY",
    )

    result = compare_histories(
        primary,
        benchmark,
        minimum_observations=4,
        minimum_span_days=3,
        as_of_date=date(2024, 2, 1),
    )

    assert result["status"] == "needs-review"
    assert result["coverage"]["observations"] == 3
    checks = {check["name"]: check for check in result["quality"]["checks"]}
    assert checks["overlap"]["status"] == "fail"
    assert checks["requested window"]["status"] == "fail"
    assert checks["currency"]["status"] == "warn"
    assert checks["freshness"]["status"] == "warn"
    assert checks["alignment"]["status"] == "warn"
    assert "Primary provider warning." in result["quality"]["warnings"]
    assert result["metrics"]["AAPL"]["start_close"] == 100.0


def test_comparison_refuses_to_calculate_from_insufficient_overlap(
    history_factory: object,
) -> None:
    primary = history_factory("AAPL", (100,), dates=("2024-01-02",))
    benchmark = history_factory("SPY", (200,), dates=("2024-01-02",))

    result = compare_histories(
        primary,
        benchmark,
        minimum_observations=2,
        minimum_span_days=1,
        as_of_date=date(2024, 1, 3),
    )

    assert result["status"] == "needs-review"
    assert result["coverage"]["observations"] == 1
    assert result["metrics"] == {}
    assert result["relative"] == {}
    assert result["series"] == []
    assert "Fewer than two overlapping sessions." in result["quality"]["warnings"]


def test_observation_count_cannot_substitute_for_the_requested_calendar_window(
    history_factory: object,
) -> None:
    dates = ("2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05")
    result = compare_histories(
        history_factory("AAPL", (100, 101, 102, 103), dates=dates),
        history_factory("SPY", (200, 201, 202, 203), dates=dates),
        minimum_observations=4,
        minimum_span_days=10,
        as_of_date=date(2024, 1, 5),
    )

    assert result["coverage"]["observations"] == 4
    assert result["coverage"]["span_days"] == 3
    assert result["coverage"]["sufficient"] is False
    assert result["status"] == "needs-review"
    checks = {check["name"]: check for check in result["quality"]["checks"]}
    assert checks["overlap"]["status"] == "pass"
    assert checks["requested window"] == {
        "name": "requested window",
        "status": "fail",
        "detail": "3 calendar days covered; 10 required.",
    }


def test_comparison_omits_invalid_close_pairs_and_does_not_invent_volatility(
    history_factory: object,
) -> None:
    dates = ("2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05")
    primary = history_factory("AAPL", (100, float("nan"), 110, 120), dates=dates)
    benchmark = history_factory("SPY", (200, 210, 0, 230), dates=dates)

    result = compare_histories(
        primary,
        benchmark,
        minimum_observations=2,
        minimum_span_days=3,
        as_of_date=date(2024, 1, 5),
    )

    assert result["status"] == "complete"
    assert result["coverage"]["observations"] == 2
    assert [item["date"] for item in result["series"]] == [
        "2024-01-02",
        "2024-01-05",
    ]
    assert result["metrics"]["AAPL"]["total_return_pct"] == 20.0
    assert result["metrics"]["SPY"]["total_return_pct"] == 15.0
    assert result["metrics"]["AAPL"]["annualized_volatility_pct"] is None
    assert result["metrics"]["SPY"]["annualized_volatility_pct"] is None
    assert result["relative"]["daily_return_correlation"] is None
    assert result["relative"]["beta_to_benchmark"] is None
    checks = {check["name"]: check for check in result["quality"]["checks"]}
    assert checks["valid adjusted closes"] == {
        "name": "valid adjusted closes",
        "status": "warn",
        "detail": "Omitted 2 aligned session(s) with invalid closes.",
    }


@pytest.mark.parametrize(
    ("primary", "benchmark", "expected_beta"),
    (
        ((100, 100, 100), (200, 201, 202), 0.0),
        ((100, 101, 102), (200, 200, 200), None),
    ),
)
def test_correlation_needs_both_variances_but_beta_only_needs_benchmark_variance(
    history_factory: object,
    primary: tuple[int, ...],
    benchmark: tuple[int, ...],
    expected_beta: float | None,
) -> None:
    dates = ("2024-01-02", "2024-01-03", "2024-01-04")
    result = compare_histories(
        history_factory("AAPL", primary, dates=dates),
        history_factory("SPY", benchmark, dates=dates),
        minimum_observations=3,
        minimum_span_days=2,
        as_of_date=date(2024, 1, 4),
    )

    assert result["relative"]["daily_return_correlation"] is None
    assert result["relative"]["beta_to_benchmark"] == expected_beta
