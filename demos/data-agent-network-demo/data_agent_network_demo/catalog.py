"""Small fictional catalog used by the deterministic Data Consultant."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DataProduct:
    product_id: str
    name: str
    description: str
    coverage: tuple[str, ...]
    fields: tuple[str, ...]
    freshness: str
    cost: str
    access: str
    reproducibility: str
    limitation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CATALOG: tuple[DataProduct, ...] = (
    DataProduct(
        product_id="demo-market-tape",
        name="Demo Market Tape",
        description="Synthetic end-of-day prices for fictional listed instruments.",
        coverage=("prices", "returns", "volatility"),
        fields=("symbol", "date", "open", "high", "low", "close", "volume"),
        freshness="T+1 fixture",
        cost="free",
        access="no authentication",
        reproducibility="fully checked in",
        limitation="No intraday observations and no real securities.",
    ),
    DataProduct(
        product_id="demo-company-filings",
        name="Demo Company Filings",
        description="Synthetic statements and filing facts for fictional issuers.",
        coverage=("fundamentals", "valuation", "filings", "peers"),
        fields=("issuer", "period", "revenue", "operating_income", "assets", "shares"),
        freshness="quarterly fixture",
        cost="free",
        access="no authentication",
        reproducibility="fully checked in",
        limitation="Sparse history; unsuitable for real valuation work.",
    ),
    DataProduct(
        product_id="demo-macro-series",
        name="Demo Macro Series",
        description="Synthetic policy-rate, inflation, and output time series.",
        coverage=("rates", "inflation", "macro"),
        fields=("series", "period", "value", "unit", "revision"),
        freshness="monthly fixture",
        cost="free",
        access="no authentication",
        reproducibility="fully checked in",
        limitation="Low frequency and intentionally simplified revisions.",
    ),
    DataProduct(
        product_id="demo-premium-terminal",
        name="Demo Premium Terminal",
        description="Fictional low-latency bundle used to expose cost and access tradeoffs.",
        coverage=("prices", "returns", "volatility", "fundamentals", "valuation", "rates"),
        fields=("instrument", "timestamp", "metric", "value", "currency", "provenance"),
        freshness="near-real-time fixture",
        cost="high",
        access="contract required",
        reproducibility="entitlement-dependent",
        limitation="Expensive and deliberately unavailable in this public demo.",
    ),
)


EXAMPLE_PROMPTS: tuple[str, ...] = (
    "Compare ACME's five-day return with the latest policy-rate move and explain the data caveats.",
    "What data should I use to compare ACME valuation with peer BETA on a reproducible, low-cost basis?",
    "Design a volatility check for ACME using daily closes, with clear freshness and field requirements.",
)
