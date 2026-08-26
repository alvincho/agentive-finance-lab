"""Unit tests for the demo's one external financial-data adapter."""

from __future__ import annotations

import math

import pandas as pd
import pytest

from data_agent_network_demo.contracts import MarketDataError
from data_agent_network_demo import yfinance_source
from data_agent_network_demo.yfinance_source import YFinanceSource


class StubTicker:
    def __init__(self, frame: pd.DataFrame) -> None:
        self.frame = frame
        self.history_kwargs: dict[str, object] | None = None

    def history(self, **kwargs: object) -> pd.DataFrame:
        self.history_kwargs = kwargs
        return self.frame

    def get_history_metadata(self, *, repair: bool) -> dict[str, str]:
        assert repair is False
        return {
            "longName": "Apple Inc.",
            "currency": "USD",
            "fullExchangeName": "NasdaqGS",
            "instrumentType": "EQUITY",
            "exchangeTimezoneName": "America/New_York",
        }


def test_adapter_requests_adjusted_daily_history_and_normalizes_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = pd.DataFrame(
        {
            "Close": (100.125, math.nan, -1, 102.5),
            "Volume": (1_000, math.nan, 9, 1_200),
        },
        index=pd.to_datetime(
            ("2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"),
            utc=True,
        ),
    )
    ticker = StubTicker(frame)
    monkeypatch.setattr(yfinance_source.yf, "Ticker", lambda symbol: ticker)
    source = YFinanceSource(timeout_seconds=3.5)

    history = source.fetch_history(symbol="AAPL", period="1mo")

    assert source.provider_name == "yfinance"
    assert source.provider_version == yfinance_source.yf.__version__
    assert ticker.history_kwargs == {
        "period": "1mo",
        "interval": "1d",
        "auto_adjust": True,
        "actions": False,
        "repair": False,
        "keepna": False,
        "timeout": 3.5,
    }
    assert history.symbol == "AAPL"
    assert history.name == "Apple Inc."
    assert history.currency == "USD"
    assert history.interval == "1d"
    assert history.auto_adjust is True
    assert history.rows_received == 4
    assert history.rows_dropped == 2
    assert [(item.date, item.close, item.volume) for item in history.observations] == [
        ("2024-01-02", 100.125, 1000),
        ("2024-01-05", 102.5, 1200),
    ]


def test_adapter_turns_empty_provider_data_into_an_explicit_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ticker = StubTicker(pd.DataFrame())
    monkeypatch.setattr(yfinance_source.yf, "Ticker", lambda symbol: ticker)

    with pytest.raises(MarketDataError) as raised:
        YFinanceSource().fetch_history(symbol="MISSING", period="1mo")

    assert raised.value.to_dict() == {
        "symbol": "MISSING",
        "code": "no_history",
        "message": "yfinance returned no daily price history for MISSING.",
    }


def test_price_history_survives_optional_metadata_failure_with_a_warning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class MetadataFailureTicker(StubTicker):
        def get_history_metadata(self, *, repair: bool) -> dict[str, str]:
            raise RuntimeError("metadata unavailable")

    ticker = MetadataFailureTicker(
        pd.DataFrame(
            {"Close": (100, 101)},
            index=pd.to_datetime(("2024-01-02", "2024-01-03"), utc=True),
        )
    )
    monkeypatch.setattr(yfinance_source.yf, "Ticker", lambda symbol: ticker)

    history = YFinanceSource().fetch_history(symbol="AAPL", period="1mo")

    assert history.name == "AAPL"
    assert history.currency is None
    assert history.warnings == (
        "yfinance price history succeeded, but metadata was unavailable.",
    )


def test_adapter_normalizes_unexpected_provider_failure_without_retrying_elsewhere(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenTicker:
        def history(self, **kwargs: object) -> pd.DataFrame:
            raise RuntimeError("upstream disconnected")

    monkeypatch.setattr(yfinance_source.yf, "Ticker", lambda symbol: BrokenTicker())

    with pytest.raises(MarketDataError) as raised:
        YFinanceSource().fetch_history(symbol="AAPL", period="1mo")

    assert raised.value.code == "network_error"
    assert raised.value.symbol == "AAPL"
    assert raised.value.message == "The yfinance request for AAPL failed."
    assert isinstance(raised.value.__cause__, RuntimeError)


def test_adapter_wraps_a_malformed_provider_frame_as_a_response_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ticker = StubTicker(object())  # type: ignore[arg-type]
    monkeypatch.setattr(yfinance_source.yf, "Ticker", lambda symbol: ticker)

    with pytest.raises(MarketDataError) as raised:
        YFinanceSource().fetch_history(symbol="AAPL", period="1mo")

    assert raised.value.to_dict() == {
        "symbol": "AAPL",
        "code": "provider_response_error",
        "message": "yfinance returned an unusable response for AAPL.",
    }
    assert isinstance(raised.value.__cause__, AttributeError)
