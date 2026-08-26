"""Pure descriptive calculations over histories delivered by yfinance."""

from __future__ import annotations

from datetime import date
import math
from statistics import mean, stdev

from .contracts import MarketHistory, PriceObservation


TRADING_DAYS_PER_YEAR = 252
MAX_CHART_POINTS = 180


def compare_histories(
    primary: MarketHistory,
    benchmark: MarketHistory,
    *,
    minimum_observations: int,
    minimum_span_days: int,
    as_of_date: date | None = None,
) -> dict[str, object]:
    """Align two adjusted-close histories and calculate descriptive statistics."""

    primary_by_date = {item.date: item for item in primary.observations}
    benchmark_by_date = {item.date: item for item in benchmark.observations}
    candidate_dates = sorted(primary_by_date.keys() & benchmark_by_date.keys())
    common_dates = [
        item
        for item in candidate_dates
        if _valid_close(primary_by_date[item].close)
        and _valid_close(benchmark_by_date[item].close)
    ]
    aligned_primary = [primary_by_date[item] for item in common_dates]
    aligned_benchmark = [benchmark_by_date[item] for item in common_dates]
    observations = len(common_dates)

    checks: list[dict[str, str]] = []
    invalid_pairs = len(candidate_dates) - observations
    checks.append(
        {
            "name": "valid adjusted closes",
            "status": "pass" if invalid_pairs == 0 else "warn",
            "detail": (
                "All aligned adjusted closes are finite and positive."
                if invalid_pairs == 0
                else f"Omitted {invalid_pairs} aligned session(s) with invalid closes."
            ),
        }
    )
    enough_observations = observations >= minimum_observations
    checks.append(
        {
            "name": "overlap",
            "status": "pass" if enough_observations else "fail",
            "detail": f"{observations} aligned sessions; {minimum_observations} required.",
        }
    )

    span_days = (
        (date.fromisoformat(common_dates[-1]) - date.fromisoformat(common_dates[0])).days
        if observations >= 2
        else 0
    )
    enough_span = span_days >= minimum_span_days
    checks.append(
        {
            "name": "requested window",
            "status": "pass" if enough_span else "fail",
            "detail": f"{span_days} calendar days covered; {minimum_span_days} required.",
        }
    )

    if observations < 2:
        return {
            "status": "needs-review",
            "coverage": {
                "start": common_dates[0] if common_dates else None,
                "end": common_dates[-1] if common_dates else None,
                "observations": observations,
                "minimum_required": minimum_observations,
                "span_days": span_days,
                "minimum_span_days": minimum_span_days,
                "sufficient": False,
            },
            "metrics": {},
            "relative": {},
            "series": [],
            "latest_observations": [],
            "quality": {
                "checks": checks,
                "warnings": _unique(
                    [
                        *(check["detail"] for check in checks if check["status"] != "pass"),
                        *primary.warnings,
                        *benchmark.warnings,
                        "Fewer than two overlapping sessions.",
                    ]
                ),
            },
        }

    primary_closes = [item.close for item in aligned_primary]
    benchmark_closes = [item.close for item in aligned_benchmark]
    primary_returns = _returns(primary_closes)
    benchmark_returns = _returns(benchmark_closes)
    primary_metrics = _metrics(primary, aligned_primary, primary_returns)
    benchmark_metrics = _metrics(benchmark, aligned_benchmark, benchmark_returns)
    correlation, beta = _relationship(primary_returns, benchmark_returns)

    currency_match = bool(primary.currency and primary.currency == benchmark.currency)
    checks.append(
        {
            "name": "currency",
            "status": "pass" if currency_match else "warn",
            "detail": (
                f"Both histories report {primary.currency}."
                if currency_match
                else f"Currencies differ or are missing: {primary.currency or 'unknown'} / "
                f"{benchmark.currency or 'unknown'}. Returns remain dimensionless."
            ),
        }
    )

    today = as_of_date or date.today()
    latest_date = date.fromisoformat(common_dates[-1])
    age_days = max((today - latest_date).days, 0)
    fresh = age_days <= 7
    checks.append(
        {
            "name": "freshness",
            "status": "pass" if fresh else "warn",
            "detail": f"Latest aligned close is {age_days} calendar day{'s' if age_days != 1 else ''} old.",
        }
    )

    dropped_primary = len(primary.observations) - observations
    dropped_benchmark = len(benchmark.observations) - observations
    checks.append(
        {
            "name": "alignment",
            "status": "pass" if dropped_primary == 0 and dropped_benchmark == 0 else "warn",
            "detail": (
                f"Alignment omitted {dropped_primary} {primary.symbol} and "
                f"{dropped_benchmark} {benchmark.symbol} unmatched sessions."
            ),
        }
    )

    warnings = [
        check["detail"] for check in checks if check["status"] in {"warn", "fail"}
    ]
    warnings.extend(primary.warnings)
    warnings.extend(benchmark.warnings)
    sufficient = enough_observations and enough_span
    status = "complete" if sufficient else "needs-review"

    return {
        "status": status,
        "coverage": {
            "start": common_dates[0],
            "end": common_dates[-1],
            "observations": observations,
            "minimum_required": minimum_observations,
            "span_days": span_days,
            "minimum_span_days": minimum_span_days,
            "sufficient": sufficient,
            "primary_rows": len(primary.observations),
            "benchmark_rows": len(benchmark.observations),
        },
        "metrics": {
            primary.symbol: primary_metrics,
            benchmark.symbol: benchmark_metrics,
        },
        "relative": {
            "return_spread_pct_points": _rounded(
                float(primary_metrics["total_return_pct"])
                - float(benchmark_metrics["total_return_pct"])
            ),
            "daily_return_correlation": _rounded(correlation),
            "beta_to_benchmark": _rounded(beta),
        },
        "series": _chart_series(
            common_dates,
            primary.symbol,
            primary_closes,
            benchmark.symbol,
            benchmark_closes,
        ),
        "latest_observations": [
            {
                "date": item,
                primary.symbol: primary_by_date[item].close,
                benchmark.symbol: benchmark_by_date[item].close,
            }
            for item in common_dates[-8:]
        ],
        "quality": {"checks": checks, "warnings": _unique(warnings)},
    }


def _returns(closes: list[float]) -> list[float]:
    return [current / previous - 1 for previous, current in zip(closes, closes[1:])]


def _metrics(
    history: MarketHistory,
    observations: list[PriceObservation],
    daily_returns: list[float],
) -> dict[str, object]:
    closes = [item.close for item in observations]
    total_return = closes[-1] / closes[0] - 1
    volatility = (
        stdev(daily_returns) * math.sqrt(TRADING_DAYS_PER_YEAR)
        if len(daily_returns) > 1
        else None
    )
    running_peak = closes[0]
    max_drawdown = 0.0
    for close in closes:
        running_peak = max(running_peak, close)
        max_drawdown = min(max_drawdown, close / running_peak - 1)
    available_volumes = [item.volume for item in observations if item.volume is not None]
    return {
        "symbol": history.symbol,
        "name": history.name,
        "currency": history.currency,
        "exchange": history.exchange,
        "instrument_type": history.instrument_type,
        "latest_close": _rounded(closes[-1], digits=4),
        "start_close": _rounded(closes[0], digits=4),
        "total_return_pct": _rounded(total_return * 100),
        "annualized_volatility_pct": (
            _rounded(volatility * 100) if volatility is not None else None
        ),
        "max_drawdown_pct": _rounded(max_drawdown * 100),
        "period_high": _rounded(max(closes), digits=4),
        "period_low": _rounded(min(closes), digits=4),
        "average_volume": int(mean(available_volumes)) if available_volumes else None,
        "observations": len(observations),
    }


def _relationship(primary: list[float], benchmark: list[float]) -> tuple[float | None, float | None]:
    if len(primary) < 2 or len(primary) != len(benchmark):
        return (None, None)
    primary_mean = mean(primary)
    benchmark_mean = mean(benchmark)
    denominator = len(primary) - 1
    covariance = sum(
        (left - primary_mean) * (right - benchmark_mean)
        for left, right in zip(primary, benchmark)
    ) / denominator
    primary_variance = sum((item - primary_mean) ** 2 for item in primary) / denominator
    benchmark_variance = sum((item - benchmark_mean) ** 2 for item in benchmark) / denominator
    if benchmark_variance <= 0:
        return (None, None)
    beta = covariance / benchmark_variance
    correlation = (
        covariance / math.sqrt(primary_variance * benchmark_variance)
        if primary_variance > 0
        else None
    )
    return (correlation, beta)


def _chart_series(
    dates: list[str],
    primary_symbol: str,
    primary_closes: list[float],
    benchmark_symbol: str,
    benchmark_closes: list[float],
) -> list[dict[str, object]]:
    indices = _sample_indices(len(dates), MAX_CHART_POINTS)
    primary_base = primary_closes[0]
    benchmark_base = benchmark_closes[0]
    return [
        {
            "date": dates[index],
            primary_symbol: _rounded(primary_closes[index] / primary_base * 100),
            benchmark_symbol: _rounded(benchmark_closes[index] / benchmark_base * 100),
        }
        for index in indices
    ]


def _sample_indices(length: int, maximum: int) -> list[int]:
    if length <= maximum:
        return list(range(length))
    step = (length - 1) / (maximum - 1)
    return sorted({round(index * step) for index in range(maximum)})


def _rounded(value: float | None, *, digits: int = 3) -> float | None:
    return None if value is None or not math.isfinite(value) else round(value, digits)


def _valid_close(value: float) -> bool:
    return math.isfinite(value) and value > 0


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))


__all__ = ["compare_histories"]
