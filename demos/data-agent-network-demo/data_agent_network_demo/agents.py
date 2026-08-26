"""The two collaborating Persona roles in the Data Agent Network demo."""

from __future__ import annotations

import math

from phemacast_lite import Persona, PersonaProfile, PulseSpec
from prompits_lite import CallContext, Plaza
from prompits_lite.models import JsonObject

from .analytics import compare_histories
from .contracts import (
    ALLOWED_PERIODS,
    MINIMUM_OBSERVATIONS,
    MINIMUM_SPAN_DAYS,
    MarketDataError,
    MarketDataSource,
    MarketHistory,
    normalize_symbol,
)


class DataConsultant(Persona):
    """Specialist Persona that owns retrieval, normalization, and analysis."""

    def __init__(self, source: MarketDataSource) -> None:
        super().__init__(
            name="Data Consultant",
            pit_id="data-consultant",
            description="Retrieves and compares market histories through the yfinance boundary.",
            profile=PersonaProfile(
                role="data-consultant",
                purpose="Turn a structured comparison request into inspectable market-data evidence.",
                instructions=(
                    "Use yfinance as the only external financial-data source.",
                    "Return descriptive calculations, provenance, quality checks, and provider failures.",
                    "Never generate substitute prices or make an investment recommendation.",
                ),
            ),
        )
        self.source = source
        self.register_pulse(
            PulseSpec(
                name="analyze_market_history",
                description="Fetch and compare adjusted daily histories for two symbols.",
                required_inputs=("primary_symbol", "benchmark_symbol", "period"),
                output_fields=(
                    "status",
                    "source",
                    "coverage",
                    "metrics",
                    "relative",
                    "series",
                    "latest_observations",
                    "quality",
                    "provenance",
                    "errors",
                ),
                input_types={
                    "primary_symbol": str,
                    "benchmark_symbol": str,
                    "period": str,
                },
                output_types={
                    "status": str,
                    "source": dict,
                    "coverage": dict,
                    "metrics": dict,
                    "relative": dict,
                    "series": list,
                    "latest_observations": list,
                    "quality": dict,
                    "provenance": list,
                    "errors": list,
                },
            ),
            self._analyze,
        )

    def _analyze(self, payload: JsonObject, context: CallContext) -> JsonObject:
        primary_symbol = normalize_symbol(str(payload["primary_symbol"]))
        benchmark_symbol = normalize_symbol(str(payload["benchmark_symbol"]))
        period = str(payload["period"])
        if period not in ALLOWED_PERIODS:
            raise ValueError(f"Unsupported period: {period}")

        symbols = (primary_symbol, benchmark_symbol)
        context.trace.emit(
            stage="consultant.plan",
            actor=self.name,
            target=self.source.provider_name,
            summary="Plan two bounded adjusted-daily history requests.",
            detail={
                "symbols": list(symbols),
                "period": period,
                "interval": "1d",
                "auto_adjust": True,
            },
        )

        histories: dict[str, MarketHistory] = {}
        errors: list[dict[str, str]] = []
        for symbol in symbols:
            context.trace.emit(
                stage="yfinance.request",
                actor=self.name,
                target="yfinance",
                summary=f"Request adjusted daily history for {symbol}.",
                detail={
                    "symbol": symbol,
                    "period": period,
                    "interval": "1d",
                    "auto_adjust": True,
                },
            )
            try:
                history = self.source.fetch_history(symbol=symbol, period=period)
            except MarketDataError as exc:
                normalized_error = exc.to_dict()
                errors.append(normalized_error)
                context.trace.emit(
                    stage="yfinance.error",
                    actor="yfinance",
                    target=self.name,
                    summary=f"Return a normalized provider failure for {symbol}.",
                    detail={"symbol": symbol, "code": exc.code},
                )
                if exc.code == "rate_limited":
                    remaining = [item for item in symbols if item not in histories and item != symbol]
                    for skipped in remaining:
                        errors.append(
                            {
                                "symbol": skipped,
                                "code": "not_attempted",
                                "message": "Request not attempted after the provider rate limit.",
                            }
                        )
                    break
                continue

            histories[symbol] = history
            context.trace.emit(
                stage="yfinance.response",
                actor="yfinance",
                target=self.name,
                summary=f"Return {len(history.observations)} usable closes for {symbol}.",
                detail={
                    "symbol": symbol,
                    "rows_received": history.rows_received,
                    "rows_used": len(history.observations),
                    "fetched_at_utc": history.fetched_at_utc,
                },
            )

        source = {
            "provider": self.source.provider_name,
            "version": self.source.provider_version,
            "upstream": "Yahoo Finance",
            "method": "yfinance.Ticker.history",
            "interval": "1d",
            "auto_adjust": True,
            "usage": "Research and educational demo; Yahoo Finance data is intended for personal use.",
        }
        provenance = [histories[symbol].provenance() for symbol in symbols if symbol in histories]
        if len(histories) != 2:
            status = "partial" if histories else "unavailable"
            context.trace.emit(
                stage="consultant.stop",
                actor=self.name,
                target="Data User",
                summary="Stop without a comparison because both requested histories are required.",
                detail={
                    "status": status,
                    "successful_symbols": list(histories),
                    "error_codes": [item["code"] for item in errors],
                },
            )
            return {
                "status": status,
                "source": source,
                "coverage": {},
                "metrics": {},
                "relative": {},
                "series": [],
                "latest_observations": [],
                "quality": {
                    "checks": [
                        {
                            "name": "required histories",
                            "status": "fail",
                            "detail": f"Retrieved {len(histories)} of 2 requested histories.",
                        }
                    ],
                    "warnings": [item["message"] for item in errors],
                },
                "provenance": provenance,
                "errors": errors,
            }

        context.trace.emit(
            stage="consultant.calculate",
            actor=self.name,
            target="Data User",
            summary="Align closes and calculate descriptive comparison metrics.",
            detail={
                "primary_symbol": primary_symbol,
                "benchmark_symbol": benchmark_symbol,
                "minimum_observations": MINIMUM_OBSERVATIONS[period],
                "minimum_span_days": MINIMUM_SPAN_DAYS[period],
            },
        )
        analysis = compare_histories(
            histories[primary_symbol],
            histories[benchmark_symbol],
            minimum_observations=MINIMUM_OBSERVATIONS[period],
            minimum_span_days=MINIMUM_SPAN_DAYS[period],
        )
        return {
            "status": analysis["status"],
            "source": source,
            "coverage": analysis["coverage"],
            "metrics": analysis["metrics"],
            "relative": analysis["relative"],
            "series": analysis["series"],
            "latest_observations": analysis["latest_observations"],
            "quality": analysis["quality"],
            "provenance": provenance,
            "errors": errors,
        }


class DataUser(Persona):
    """User-facing Persona that owns intent, delegation, and acceptance."""

    def __init__(self, plaza: Plaza) -> None:
        super().__init__(
            name="Data User",
            pit_id="data-user",
            description="Turns a comparison intent into a contract and accepts specialist evidence.",
            profile=PersonaProfile(
                role="data-user",
                purpose="Preserve user intent while delegating financial-data work to a specialist.",
                instructions=(
                    "Validate and normalize the comparison contract before delegation.",
                    "Discover the consultant through Plaza rather than a fixed address.",
                    "Accept results only when their source, coverage, metrics, and provenance are explicit.",
                ),
            ),
        )
        self.plaza = plaza
        self.register_pulse(
            PulseSpec(
                name="compare_market_data",
                description="Validate, delegate, accept, and present one market-data comparison.",
                required_inputs=("primary_symbol", "benchmark_symbol", "period"),
                output_fields=(
                    "status",
                    "request",
                    "consultant",
                    "acceptance",
                    "answer",
                    "benefit",
                ),
                input_types={
                    "primary_symbol": str,
                    "benchmark_symbol": str,
                    "period": str,
                },
                output_types={
                    "status": str,
                    "request": dict,
                    "consultant": dict,
                    "acceptance": dict,
                    "answer": dict,
                    "benefit": dict,
                },
            ),
            self._compare,
        )

    def _compare(self, payload: JsonObject, context: CallContext) -> JsonObject:
        request = self._normalize_request(payload)
        context.trace.emit(
            stage="data-user.validate",
            actor=self.name,
            target="Data Consultant role",
            summary="Validate the user intent and publish a bounded comparison contract.",
            detail=dict(request),
        )
        matches = self.plaza.search(
            pit_type="Persona",
            capability="analyze_market_history",
            labels={"role": "data-consultant"},
            caller=self,
            trace=context.trace,
        )

        if not matches:
            consultant = _unavailable_consultant(
                code="consultant_unavailable",
                message="No Data Consultant advertises the required Pulse.",
            )
            acceptance = self._accept(consultant, request)
            context.trace.emit(
                stage="data-user.present",
                actor=self.name,
                target="Demo UI",
                summary="Present a transparent unavailable result without substitute data.",
                detail={"status": "unavailable"},
            )
            return self._result(
                status="unavailable",
                request=request,
                consultant=consultant,
                acceptance=acceptance,
            )

        consultant = self.plaza.invoke(
            caller=self,
            target=matches[0],
            capability="analyze_market_history",
            payload=request,
            trace=context.trace,
        )
        acceptance = self._accept(consultant, request)
        status = str(consultant["status"])
        if status == "complete" and acceptance["status"] != "pass":
            status = "needs-review"
        context.trace.emit(
            stage="data-user.accept",
            actor=self.name,
            target="Data Consultant",
            summary="Check source identity, coverage, metrics, and provenance before acceptance.",
            detail={
                "accepted": acceptance["accepted"],
                "acceptance_status": acceptance["status"],
                "failed_checks": acceptance["failed_checks"],
                "warning_count": len(acceptance["warnings"]),
            },
        )
        context.trace.emit(
            stage="data-user.present",
            actor=self.name,
            target="Demo UI",
            summary="Present evidence and limitations with the shared trace intact.",
            detail={"status": status},
        )
        return self._result(
            status=status,
            request=request,
            consultant=consultant,
            acceptance=acceptance,
        )

    @staticmethod
    def _normalize_request(payload: JsonObject) -> JsonObject:
        primary_symbol = normalize_symbol(str(payload["primary_symbol"]))
        benchmark_symbol = normalize_symbol(str(payload["benchmark_symbol"]))
        period = str(payload["period"])
        if primary_symbol == benchmark_symbol:
            raise ValueError("Primary and benchmark symbols must be different.")
        if period not in ALLOWED_PERIODS:
            raise ValueError(f"Unsupported period: {period}")
        return {
            "primary_symbol": primary_symbol,
            "benchmark_symbol": benchmark_symbol,
            "period": period,
            "interval": "1d",
            "auto_adjust": True,
            "task": "Compare adjusted price history and descriptive risk/return statistics.",
        }

    @staticmethod
    def _accept(consultant: JsonObject, request: JsonObject) -> JsonObject:
        raw_coverage = consultant.get("coverage")
        coverage = raw_coverage if isinstance(raw_coverage, dict) else {}
        raw_metrics = consultant.get("metrics")
        metrics = raw_metrics if isinstance(raw_metrics, dict) else {}
        provenance = consultant.get("provenance") or []
        raw_errors = consultant.get("errors")
        errors = raw_errors if isinstance(raw_errors, list) else ["invalid error contract"]
        raw_quality = consultant.get("quality")
        quality = raw_quality if isinstance(raw_quality, dict) else {}
        raw_source = consultant.get("source")
        source = raw_source if isinstance(raw_source, dict) else {}
        quality_checks = quality.get("checks") or []
        quality_valid = (
            isinstance(quality_checks, list)
            and bool(quality_checks)
            and all(
                isinstance(item, dict)
                and isinstance(item.get("name"), str)
                and item.get("status") in {"pass", "warn", "fail"}
                for item in quality_checks
            )
        )
        quality_warnings = quality.get("warnings") or []
        if not isinstance(quality_warnings, list):
            quality_warnings = []
        symbols = (str(request["primary_symbol"]), str(request["benchmark_symbol"]))
        period = str(request["period"])
        observations = _safe_int(coverage.get("observations"))
        provenance_valid = _valid_provenance(
            provenance=provenance,
            symbols=symbols,
            period=period,
            minimum_rows=observations,
        )
        metrics_valid = observations > 0 and all(
            _valid_metrics(metrics.get(symbol), symbol=symbol, observations=observations)
            for symbol in symbols
        )
        hard_quality_failures = [
            str(item.get("detail") or item.get("name") or "Unspecified quality failure")
            for item in quality_checks
            if isinstance(item, dict) and item.get("status") == "fail"
        ]
        acceptance_warnings = _unique_strings(
            [
                *(
                    str(item.get("detail") or item.get("name"))
                    for item in quality_checks
                    if isinstance(item, dict) and item.get("status") == "warn"
                ),
                *(str(item) for item in quality_warnings if item),
            ]
        )
        checks = [
            {
                "name": "consultant completed without provider errors",
                "passed": consultant.get("status") == "complete" and not errors,
            },
            {
                "name": "yfinance source",
                "passed": source.get("provider") == "yfinance",
            },
            {
                "name": "adjusted daily contract",
                "passed": (
                    source.get("interval") == "1d"
                    and source.get("auto_adjust") is True
                ),
            },
            {
                "name": "complete finite metrics",
                "passed": metrics_valid,
            },
            {
                "name": "requested coverage",
                "passed": (
                    coverage.get("sufficient") is True
                    and observations >= MINIMUM_OBSERVATIONS[period]
                    and _safe_int(coverage.get("span_days")) >= MINIMUM_SPAN_DAYS[period]
                ),
            },
            {
                "name": "exact query provenance",
                "passed": provenance_valid,
            },
            {
                "name": "no hard quality failures",
                "passed": quality_valid and not hard_quality_failures,
            },
        ]
        failed_checks = [str(item["name"]) for item in checks if not item["passed"]]
        if failed_checks:
            status = "fail"
        elif acceptance_warnings:
            status = "pass-with-warnings"
        else:
            status = "pass"
        return {
            "status": status,
            "accepted": not failed_checks,
            "checks": checks,
            "failed_checks": failed_checks,
            "warnings": acceptance_warnings,
        }

    @staticmethod
    def _result(
        *,
        status: str,
        request: JsonObject,
        consultant: JsonObject,
        acceptance: JsonObject,
    ) -> JsonObject:
        primary_symbol = str(request["primary_symbol"])
        benchmark_symbol = str(request["benchmark_symbol"])
        metrics = consultant.get("metrics", {})
        relative = consultant.get("relative", {})
        comparison = _safe_comparison_values(
            metrics=metrics,
            relative=relative,
            primary_symbol=primary_symbol,
            benchmark_symbol=benchmark_symbol,
            coverage=consultant.get("coverage") or {},
        )
        if comparison is not None:
            primary_return, benchmark_return, spread, start, end = comparison
            headline = (
                f"{primary_symbol} returned {primary_return:.2f}% vs "
                f"{benchmark_symbol} at {benchmark_return:.2f}%."
            )
            summary = (
                f"The aligned adjusted-close comparison spans "
                f"{start} to {end}; "
                f"the relative return spread is {spread:.2f} percentage points."
            )
        elif status == "partial":
            headline = "The comparison is incomplete because one requested history failed."
            summary = "The successful retrieval provenance and normalized provider error are both preserved."
        elif status == "needs-review":
            headline = "The consultant evidence did not pass the Data User acceptance boundary."
            summary = "Inspect the failed checks, quality evidence, and provenance before relying on this comparison."
        else:
            headline = "No comparison is available from yfinance for this request."
            summary = "The demo stopped explicitly instead of substituting generated or cached market prices."
        return {
            "status": status,
            "request": request,
            "consultant": consultant,
            "acceptance": acceptance,
            "answer": {
                "headline": headline,
                "summary": summary,
                "caveat": "Descriptive educational output only; not investment advice.",
            },
            "benefit": {
                "separation": "Data User owns intent and acceptance; Data Consultant owns retrieval and analysis.",
                "discoverability": "Plaza finds the specialist by Persona role and typed Pulse capability.",
                "inspectability": "A correlation id follows validation, discovery, routing, provider calls, calculations, and acceptance.",
                "failure_isolation": "Provider failures cross the agent boundary as typed evidence; neither role invents fallback prices.",
                "replaceability": "Another consultant can implement the same Pulse without changing Data User.",
            },
        }


def _unavailable_consultant(*, code: str, message: str) -> JsonObject:
    return {
        "status": "unavailable",
        "source": {
            "provider": "yfinance",
            "version": "unavailable",
            "upstream": "Yahoo Finance",
            "method": "yfinance.Ticker.history",
            "interval": "1d",
            "auto_adjust": True,
            "usage": "Research and educational demo; Yahoo Finance data is intended for personal use.",
        },
        "coverage": {},
        "metrics": {},
        "relative": {},
        "series": [],
        "latest_observations": [],
        "quality": {
            "checks": [{"name": "consultant discovery", "status": "fail", "detail": message}],
            "warnings": [message],
        },
        "provenance": [],
        "errors": [{"symbol": "network", "code": code, "message": message}],
    }


def _valid_provenance(
    *,
    provenance: object,
    symbols: tuple[str, str],
    period: str,
    minimum_rows: int,
) -> bool:
    if not isinstance(provenance, list) or len(provenance) != 2:
        return False
    entries = {
        item.get("symbol"): item
        for item in provenance
        if isinstance(item, dict) and isinstance(item.get("symbol"), str)
    }
    if set(entries) != set(symbols):
        return False
    for symbol in symbols:
        entry = entries[symbol]
        query = entry.get("query")
        if not isinstance(query, dict):
            return False
        expected_query = {
            "method": "yfinance.Ticker.history",
            "period": period,
            "interval": "1d",
            "auto_adjust": True,
            "actions": False,
            "repair": False,
        }
        if any(query.get(key) != value for key, value in expected_query.items()):
            return False
        if _safe_int(entry.get("rows_used")) < minimum_rows:
            return False
        if not isinstance(entry.get("fetched_at_utc"), str) or not entry["fetched_at_utc"]:
            return False
    return True


def _valid_metrics(value: object, *, symbol: str, observations: int) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("symbol") != symbol or _safe_int(value.get("observations")) != observations:
        return False
    required_finite = (
        "latest_close",
        "start_close",
        "total_return_pct",
        "annualized_volatility_pct",
        "max_drawdown_pct",
        "period_high",
        "period_low",
    )
    return all(_finite_number(value.get(field)) for field in required_finite)


def _safe_comparison_values(
    *,
    metrics: object,
    relative: object,
    primary_symbol: str,
    benchmark_symbol: str,
    coverage: object,
) -> tuple[float, float, float, str, str] | None:
    if not isinstance(metrics, dict) or not isinstance(relative, dict) or not isinstance(coverage, dict):
        return None
    primary = metrics.get(primary_symbol)
    benchmark = metrics.get(benchmark_symbol)
    if not isinstance(primary, dict) or not isinstance(benchmark, dict):
        return None
    values = (
        primary.get("total_return_pct"),
        benchmark.get("total_return_pct"),
        relative.get("return_spread_pct_points"),
    )
    if not all(_finite_number(value) for value in values):
        return None
    start = coverage.get("start")
    end = coverage.get("end")
    if not isinstance(start, str) or not isinstance(end, str) or not start or not end:
        return None
    return (float(values[0]), float(values[1]), float(values[2]), start, end)


def _finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _safe_int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError, OverflowError):
        return 0


def _unique_strings(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


__all__ = ["DataConsultant", "DataUser"]
