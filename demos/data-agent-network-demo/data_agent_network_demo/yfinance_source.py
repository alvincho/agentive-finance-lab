"""The demo's sole external financial-data adapter."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any

import yfinance as yf
from yfinance.exceptions import (
    YFDataException,
    YFException,
    YFInvalidPeriodError,
    YFRateLimitError,
    YFTickerMissingError,
)

from .contracts import MarketDataError, MarketHistory, PriceObservation


class YFinanceSource:
    """Fetch adjusted daily histories through yfinance and nothing else."""

    provider_name = "yfinance"

    def __init__(self, *, timeout_seconds: float = 8.0) -> None:
        self.timeout_seconds = timeout_seconds
        self.provider_version = yf.__version__
        # Keep retries bounded and surface provider exceptions when supported.
        yf.config.network.retries = 1
        yf.config.debug.hide_exceptions = False

    def fetch_history(self, *, symbol: str, period: str) -> MarketHistory:
        try:
            ticker = yf.Ticker(symbol)
            frame = ticker.history(
                period=period,
                interval="1d",
                auto_adjust=True,
                actions=False,
                repair=False,
                keepna=False,
                timeout=self.timeout_seconds,
            )
        except YFRateLimitError as exc:
            raise MarketDataError(
                symbol=symbol,
                code="rate_limited",
                message="yfinance was rate-limited by its upstream service.",
            ) from exc
        except YFTickerMissingError as exc:
            raise MarketDataError(
                symbol=symbol,
                code="ticker_missing",
                message=f"yfinance could not resolve ticker {symbol}.",
            ) from exc
        except YFInvalidPeriodError as exc:
            raise MarketDataError(
                symbol=symbol,
                code="invalid_period",
                message=f"yfinance does not support the requested period for {symbol}.",
            ) from exc
        except (YFDataException, YFException) as exc:
            raise MarketDataError(
                symbol=symbol,
                code="provider_error",
                message=f"yfinance could not retrieve {symbol}.",
            ) from exc
        except Exception as exc:
            raise MarketDataError(
                symbol=symbol,
                code="network_error",
                message=f"The yfinance request for {symbol} failed.",
            ) from exc

        try:
            return self._normalize_history(
                ticker=ticker,
                frame=frame,
                symbol=symbol,
                period=period,
            )
        except MarketDataError:
            raise
        except Exception as exc:
            raise MarketDataError(
                symbol=symbol,
                code="provider_response_error",
                message=f"yfinance returned an unusable response for {symbol}.",
            ) from exc

    def _normalize_history(
        self,
        *,
        ticker: Any,
        frame: Any,
        symbol: str,
        period: str,
    ) -> MarketHistory:
        if frame is None or frame.empty or "Close" not in frame:
            raise MarketDataError(
                symbol=symbol,
                code="no_history",
                message=f"yfinance returned no daily price history for {symbol}.",
            )

        metadata, metadata_warning = self._metadata(ticker)
        observations = self._observations(frame)
        if len(observations) < 2:
            raise MarketDataError(
                symbol=symbol,
                code="insufficient_history",
                message=f"yfinance returned fewer than two usable closes for {symbol}.",
            )

        rows_received = len(frame)
        fetched_at = datetime.now(timezone.utc).isoformat()
        warnings = (metadata_warning,) if metadata_warning else ()
        return MarketHistory(
            symbol=symbol,
            name=str(metadata.get("longName") or metadata.get("shortName") or symbol),
            currency=_optional_text(metadata.get("currency")),
            exchange=_optional_text(
                metadata.get("fullExchangeName") or metadata.get("exchangeName")
            ),
            instrument_type=_optional_text(metadata.get("instrumentType")),
            timezone=_optional_text(
                metadata.get("exchangeTimezoneName") or metadata.get("timezone")
            ),
            period=period,
            interval="1d",
            auto_adjust=True,
            fetched_at_utc=fetched_at,
            rows_received=rows_received,
            rows_dropped=max(rows_received - len(observations), 0),
            observations=tuple(observations),
            warnings=warnings,
        )

    @staticmethod
    def _metadata(ticker: Any) -> tuple[dict[str, Any], str | None]:
        try:
            metadata = ticker.get_history_metadata(repair=False)
            return (dict(metadata or {}), None)
        except Exception:
            return ({}, "yfinance price history succeeded, but metadata was unavailable.")

    @staticmethod
    def _observations(frame: Any) -> list[PriceObservation]:
        closes = frame["Close"]
        volumes = frame["Volume"] if "Volume" in frame else None
        by_date: dict[str, PriceObservation] = {}
        for timestamp, raw_close in closes.items():
            try:
                close = float(raw_close)
            except (TypeError, ValueError):
                continue
            if not math.isfinite(close) or close <= 0:
                continue

            date_value = timestamp.date().isoformat()
            raw_volume = volumes.get(timestamp) if volumes is not None else None
            volume = _optional_volume(raw_volume)
            by_date[date_value] = PriceObservation(
                date=date_value,
                close=round(close, 6),
                volume=volume,
            )
        return [by_date[key] for key in sorted(by_date)]


def _optional_text(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _optional_volume(value: object) -> int | None:
    if value is None:
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric) or numeric < 0:
        return None
    return int(numeric)


__all__ = ["YFinanceSource"]
