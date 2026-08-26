"""FastAPI surface for the Data Agent Network demo and its static UI."""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Self

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .contracts import MarketDataSource, normalize_symbol
from .workflow import build_network, run_demo
from .yfinance_source import YFinanceSource


STATIC_DIR = Path(__file__).resolve().parent / "static"
Period = Literal["1mo", "3mo", "6mo", "1y", "2y", "5y"]


class DemoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    primary_symbol: str = Field(min_length=1, max_length=20)
    benchmark_symbol: str = Field(min_length=1, max_length=20)
    period: Period

    @field_validator("primary_symbol", "benchmark_symbol", mode="before")
    @classmethod
    def validate_symbol(cls, value: object) -> object:
        if not isinstance(value, str):
            return value
        return normalize_symbol(value)

    @model_validator(mode="after")
    def require_distinct_symbols(self) -> Self:
        if self.primary_symbol == self.benchmark_symbol:
            raise ValueError("Primary and benchmark symbols must be different.")
        return self


def create_app(source: MarketDataSource | None = None) -> FastAPI:
    market_source = source if source is not None else YFinanceSource()
    application = FastAPI(
        title="Agentive Finance Lab — Data Agent Network Demo",
        version="0.2.0",
        description="A real yfinance comparison routed between two specialized Personas.",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @application.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @application.get("/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "mode": "live-yfinance",
            "provider": market_source.provider_name,
            "provider_version": market_source.provider_version,
        }

    @application.get("/api/about")
    def about() -> dict[str, object]:
        return {
            "name": "Agentive Finance Lab",
            "demo": "Data Agent Network",
            "description": "Data User delegates a real security-versus-benchmark comparison to a Data Consultant discovered through Plaza.",
            "concepts": {
                "Pit": "The smallest addressable identity; intentionally not expanded as an acronym.",
                "Plaza": "The discovery and routing plane between addressable roles.",
                "Pulser": "A Pit that advertises named, typed Pulse handlers.",
                "Persona": "A role-aware Pulser with explicit purpose and instructions.",
            },
            "limits": [
                "yfinance is the only external financial-data source.",
                "Adjusted daily price history and descriptive statistics only.",
                "No LLM, trading, forecasts, investment advice, persistence, or synthetic fallback.",
                "Local educational use; Yahoo Finance data is intended for personal use.",
            ],
        }

    @application.get("/api/network")
    def network() -> dict[str, object]:
        return build_network(source=market_source).describe()

    @application.get("/api/examples")
    def examples() -> dict[str, object]:
        return {
            "comparisons": [
                {"primary_symbol": "AAPL", "benchmark_symbol": "SPY", "period": "1y"},
                {"primary_symbol": "MSFT", "benchmark_symbol": "QQQ", "period": "6mo"},
                {"primary_symbol": "BTC-USD", "benchmark_symbol": "SPY", "period": "1y"},
            ],
            "periods": ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
        }

    @application.post("/api/run")
    def run(request: DemoRequest) -> dict[str, object]:
        return run_demo(
            request.primary_symbol,
            request.benchmark_symbol,
            request.period,
            source=market_source,
        )

    return application


app = create_app()


__all__ = ["DemoRequest", "app", "create_app"]
