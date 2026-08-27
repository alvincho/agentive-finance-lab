"""Reduced copies of the FinMAS Data Agent Network contracts.

The production contract module contains many providers, feedback/settings
Pulses, and deeply annotated financial schemas. This demo keeps the original
six network Pulse definitions and three real operations from the original
YFinance endpoint snapshot.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Mapping, Protocol


JsonObject = dict[str, Any]

DATA_SOURCE_PARTY = "attas"
DATA_SOURCE_PIT_TYPE = "DataSource"
DATA_SOURCE_ID = "yfinance"
ACCESS_MODE_PULSE = "data_source_pulse"
ACCESS_MODES = (ACCESS_MODE_PULSE,)
DEFAULT_ACCESS_MODE = ACCESS_MODE_PULSE

DATA_SPEC_PULSE_NAME = "data_spec"
DATA_AVAILABILITY_PULSE_NAME = "data_availability"
DATA_FETCH_PULSE_NAME = "data_fetch"
DATA_ADVICE_PULSE_NAME = "data_advice"
DATA_SOURCE_STATUS_PULSE_NAME = "data_source_status"
DATA_REQUEST_PULSE_NAME = "data_request"


def _pulse(
    name: str,
    description: str,
    *,
    input_schema: Mapping[str, Any],
    output_schema: Mapping[str, Any],
    cost: int = 0,
) -> JsonObject:
    """Build the same public Pulse-definition shape used by FinMAS."""

    return {
        "name": name,
        "pulse_name": name,
        "pulse_address": f"plaza://pulse/attas/{name}",
        "description": description,
        "tags": ["attas", "data-agent", name.replace("_", "-")],
        "input_schema": dict(input_schema),
        "output_schema": dict(output_schema),
        "cost_points": cost,
        "cost": cost,
    }


DATA_SPEC_INPUT_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "endpoint_id": {"type": "string"},
        "limit": {"type": "integer", "minimum": 1, "maximum": 500},
    },
    "anyOf": [{"required": ["query"]}, {"required": ["endpoint_id"]}],
    "additionalProperties": False,
}

DATA_SPEC_OUTPUT_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "endpoint_id": {"type": "string"},
        "source": {"type": "object"},
        "endpoints": {"type": "array"},
        "count": {"type": "integer"},
        "snapshot": {"type": "object"},
        "warnings": {"type": "array"},
    },
    "required": [
        "query",
        "endpoint_id",
        "source",
        "endpoints",
        "count",
        "snapshot",
        "warnings",
    ],
    "additionalProperties": False,
}

DATA_AVAILABILITY_INPUT_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "use_case": {"type": "string"},
        "preferences": {"type": "object"},
        "asset_class": {"type": "string"},
        "asset_classes": {"type": "array"},
        "region": {"type": "string"},
        "regions": {"type": "array"},
        "data_type": {"type": "string"},
        "data_types": {"type": "array"},
        "time": {"type": "object"},
        "fields": {"type": "array"},
        "result_formats": {"type": "array"},
        "limit": {"type": "integer", "minimum": 1, "maximum": 500},
    },
    "required": ["query"],
    "additionalProperties": False,
}

DATA_AVAILABILITY_OUTPUT_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "source": {"type": "object"},
        "available": {"type": "boolean"},
        "datasets": {"type": "array"},
        "fields": {"type": "array"},
        "field_count": {"type": "integer"},
        "endpoint_count": {"type": "integer"},
        "result_formats": {"type": "array"},
        "result_sets": {"type": "array"},
        "count": {"type": "integer"},
        "match_reason": {"type": "string"},
        "as_of": {"type": "string"},
        "warnings": {"type": "array"},
    },
    "required": [
        "query",
        "source",
        "available",
        "datasets",
        "fields",
        "field_count",
        "endpoint_count",
        "result_formats",
        "result_sets",
        "count",
        "as_of",
        "warnings",
    ],
    "additionalProperties": False,
}

DATA_FETCH_INPUT_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {
        "source_id": {"type": "string"},
        "source": {"type": "string"},
        "dataset_id": {"type": "string"},
        "endpoint_id": {"type": "string"},
        "parameters": {"type": "object"},
        "fields": {"type": "array"},
        "access_mode": {"type": "string", "enum": [ACCESS_MODE_PULSE]},
    },
    "required": ["parameters"],
    "anyOf": [{"required": ["dataset_id"]}, {"required": ["endpoint_id"]}],
    "additionalProperties": False,
}

DATA_FETCH_OUTPUT_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {
        "status": {"type": "string"},
        "source": {"type": "object"},
        "dataset_id": {"type": "string"},
        "backend_id": {"type": "string"},
        "data": {"type": "object"},
        "canonical_data": {"type": "object"},
        "data_schema": {"type": "object"},
        "canonical_data_schema": {"type": "object"},
        "fields": {"type": "array"},
        "field_mappings": {"type": "array"},
        "attas_pulse": {"type": "object"},
        "cost": {"type": "object"},
        "warnings": {"type": "array"},
        "error": {"type": "string"},
        "access_mode": {"type": "string"},
    },
    "required": [
        "status",
        "source",
        "dataset_id",
        "backend_id",
        "data",
        "canonical_data",
        "data_schema",
        "canonical_data_schema",
        "fields",
        "field_mappings",
        "attas_pulse",
        "warnings",
    ],
    "additionalProperties": False,
}

DATA_ADVICE_INPUT_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "use_case": {"type": "string"},
        "preferences": {"type": "object"},
        "asset_class": {"type": "string"},
        "asset_classes": {"type": "array"},
        "region": {"type": "string"},
        "regions": {"type": "array"},
        "data_type": {"type": "string"},
        "data_types": {"type": "array"},
        "time": {"type": "object"},
        "fields": {"type": "array"},
        "result_formats": {"type": "array"},
        "limit": {"type": "integer", "minimum": 1},
        "include_sample_data": {"type": "boolean"},
        "advice_mode": {
            "type": "string",
            "enum": ["auto", "comparison", "recommendation"],
        },
    },
    "required": ["query"],
    "additionalProperties": False,
}

DATA_ADVICE_OUTPUT_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {
        "request": {"type": "object"},
        "answer": {"type": "string"},
        "sources": {"type": "array"},
        "source_count": {"type": "integer"},
        "result_formats": {"type": "array"},
        "field_comparisons": {"type": "array"},
        "comparison_sets": {"type": "array"},
        "llm": {"type": "object"},
        "synthesis": {"type": "object"},
        "timing": {"type": "object"},
        "memory": {"type": "object"},
        "as_of": {"type": "string"},
        "warnings": {"type": "array"},
    },
    "required": [
        "request",
        "answer",
        "sources",
        "source_count",
        "llm",
        "as_of",
        "warnings",
    ],
    "additionalProperties": False,
}

DATA_SOURCE_STATUS_INPUT_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {},
    "additionalProperties": False,
}

DATA_SOURCE_STATUS_OUTPUT_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {
        "status": {"type": "string"},
        "enabled": {"type": "boolean"},
        "refreshing": {"type": "boolean"},
        "latest_update_at": {"type": "string"},
        "latest_update_attempt_at": {"type": "string"},
        "last_update_error": {"type": "boolean"},
        "next_update_at": {"type": "string"},
        "refresh_interval_sec": {"type": "number"},
        "source_count": {"type": "integer"},
        "dataset_count": {"type": "integer"},
        "sources": {"type": "array"},
        "discovery": {"type": "object"},
        "errors": {"type": "array"},
        "as_of": {"type": "string"},
    },
    "required": [
        "status",
        "enabled",
        "refreshing",
        "latest_update_at",
        "latest_update_attempt_at",
        "last_update_error",
        "next_update_at",
        "refresh_interval_sec",
        "source_count",
        "dataset_count",
        "sources",
        "discovery",
        "errors",
        "as_of",
    ],
    "additionalProperties": False,
}

DATA_SPEC_PULSE = _pulse(
    DATA_SPEC_PULSE_NAME,
    "Search or retrieve documented vendor API endpoint specifications from a Data Source.",
    input_schema=DATA_SPEC_INPUT_SCHEMA,
    output_schema=DATA_SPEC_OUTPUT_SCHEMA,
)
DATA_AVAILABILITY_PULSE = _pulse(
    DATA_AVAILABILITY_PULSE_NAME,
    "Describe which datasets and fields are available from this Data Source for a natural-language query.",
    input_schema=DATA_AVAILABILITY_INPUT_SCHEMA,
    output_schema=DATA_AVAILABILITY_OUTPUT_SCHEMA,
)
DATA_FETCH_PULSE = _pulse(
    DATA_FETCH_PULSE_NAME,
    "Fetch a selected endpoint through the Attas data_fetch contract.",
    input_schema=DATA_FETCH_INPUT_SCHEMA,
    output_schema=DATA_FETCH_OUTPUT_SCHEMA,
    cost=1,
)
DATA_ADVICE_PULSE = _pulse(
    DATA_ADVICE_PULSE_NAME,
    "Translate a natural-language data request into grounded Data Source advice.",
    input_schema=DATA_ADVICE_INPUT_SCHEMA,
    output_schema=DATA_ADVICE_OUTPUT_SCHEMA,
    cost=1,
)
DATA_SOURCE_STATUS_PULSE = _pulse(
    DATA_SOURCE_STATUS_PULSE_NAME,
    "List Plaza-discovered Data Sources and their latest catalog synchronization state.",
    input_schema=DATA_SOURCE_STATUS_INPUT_SCHEMA,
    output_schema=DATA_SOURCE_STATUS_OUTPUT_SCHEMA,
)
DATA_REQUEST_PULSE = _pulse(
    DATA_REQUEST_PULSE_NAME,
    "Let a Data User submit a natural-language request to a Data Consultant.",
    input_schema=DATA_ADVICE_INPUT_SCHEMA,
    output_schema=DATA_ADVICE_OUTPUT_SCHEMA,
    cost=1,
)


@dataclass(frozen=True)
class EndpointParameterSpec:
    """Original normalized endpoint-parameter model."""

    name: str
    location: str = "query"
    description: str = ""
    required: bool = False
    schema: Mapping[str, Any] = field(default_factory=dict)
    default: Any = None
    examples: tuple[Any, ...] = ()


@dataclass(frozen=True)
class EndpointSpec:
    """Original vendor-neutral endpoint model."""

    endpoint_id: str
    vendor_id: str
    name: str
    description: str
    category: str
    transport: str
    operation: str
    parameters: tuple[EndpointParameterSpec, ...] = ()
    response_schema: Mapping[str, Any] = field(default_factory=dict)
    authentication: Mapping[str, Any] = field(default_factory=dict)
    cost: Mapping[str, Any] = field(default_factory=dict)
    quality: Mapping[str, Any] = field(default_factory=dict)
    documentation_url: str = ""
    executable: bool = False
    pulse_name: str = ""
    extensions: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> JsonObject:
        return asdict(self)


@dataclass(frozen=True)
class EndpointSpecSnapshot:
    """Small immutable snapshot matching the production catalog model."""

    vendor_id: str
    retrieved_at: str
    content_hash: str
    parser_version: str
    endpoints: tuple[EndpointSpec, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class EndpointExecutionResult:
    """Original normalized Data Source execution result."""

    status: str
    endpoint_id: str
    data: Mapping[str, Any] = field(default_factory=dict)
    data_schema: Mapping[str, Any] = field(default_factory=dict)
    cost: Mapping[str, Any] = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    error: str = ""


def _parameter(
    name: str,
    *,
    description: str,
    required: bool = False,
    schema_type: str = "string",
    default: Any = None,
) -> EndpointParameterSpec:
    return EndpointParameterSpec(
        name=name,
        description=description,
        required=required,
        schema={"type": schema_type},
        default=default,
    )


FREE_COST: JsonObject = {
    "amount": 0,
    "currency": "USD",
    "model": "provider_terms",
    "provider_cost": "No direct library fee; Yahoo Finance terms and limits apply.",
    "unit": "request",
    "notes": [],
}
PUBLIC_QUALITY: JsonObject = {
    "status": "provider_dependent",
    "notes": ["Coverage and freshness vary by symbol and operation."],
}
PUBLIC_AUTHENTICATION: JsonObject = {
    "required": False,
    "scheme": "public_provider",
}
YFINANCE_DOCS = "https://ranaroussi.github.io/yfinance/reference/index.html"

HISTORY_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "Date": {"type": "string"},
                    "Open": {"type": "number"},
                    "High": {"type": "number"},
                    "Low": {"type": "number"},
                    "Close": {"type": "number"},
                    "Adj Close": {"type": "number"},
                    "Volume": {"type": "number"},
                    "Dividends": {"type": "number"},
                    "Stock Splits": {"type": "number"},
                },
            },
        }
    },
}

YFINANCE_ENDPOINTS: tuple[EndpointSpec, ...] = (
    EndpointSpec(
        endpoint_id="yfinance.ticker.fast_info",
        vendor_id="yfinance",
        name="Ticker.fast_info",
        description="Documented yfinance operation Ticker.fast_info for a compact current quote snapshot.",
        category="Ticker",
        transport="python_library",
        operation="yfinance.Ticker.fast_info",
        parameters=(
            _parameter(
                "symbol",
                description="Identifier used to construct yfinance.Ticker.",
                required=True,
            ),
        ),
        response_schema={"type": "object", "additionalProperties": True},
        authentication=PUBLIC_AUTHENTICATION,
        cost=FREE_COST,
        quality=PUBLIC_QUALITY,
        documentation_url=YFINANCE_DOCS,
        executable=True,
        extensions={"attas.vendor_version": "1.2.0"},
    ),
    EndpointSpec(
        endpoint_id="yfinance.ticker.history",
        vendor_id="yfinance",
        name="Ticker.history",
        description=(
            "Historical market prices with open, high, low, close, adjusted prices, "
            "and volume; supports daily, intraday, weekly, and monthly intervals for "
            "provider-covered securities. Documented yfinance operation Ticker.history."
        ),
        category="Ticker",
        transport="python_library",
        operation="yfinance.Ticker.history",
        parameters=(
            _parameter(
                "symbol",
                description="Identifier used to construct yfinance.Ticker.",
                required=True,
            ),
            _parameter("period", description="History window such as 5d, 1mo, 1y, ytd, or max.", default="1mo"),
            _parameter("interval", description="Bar interval such as 1d, 1wk, or 1mo.", default="1d"),
            _parameter("start", description="Optional inclusive ISO start date."),
            _parameter("end", description="Optional exclusive ISO end date."),
            _parameter("auto_adjust", description="Adjust OHLC for splits and dividends.", schema_type="boolean", default=True),
        ),
        response_schema=HISTORY_SCHEMA,
        authentication=PUBLIC_AUTHENTICATION,
        cost=FREE_COST,
        quality=PUBLIC_QUALITY,
        documentation_url=YFINANCE_DOCS,
        executable=True,
        extensions={"attas.vendor_version": "1.2.0"},
    ),
    EndpointSpec(
        endpoint_id="yfinance.ticker.info",
        vendor_id="yfinance",
        name="Ticker.info",
        description=(
            "Security profile, quote, valuation, market, and company metadata when "
            "available from the provider. Documented yfinance operation Ticker.info."
        ),
        category="Ticker",
        transport="python_library",
        operation="yfinance.Ticker.info",
        parameters=(
            _parameter(
                "symbol",
                description="Identifier used to construct yfinance.Ticker.",
                required=True,
            ),
        ),
        response_schema={"type": "object", "additionalProperties": True},
        authentication=PUBLIC_AUTHENTICATION,
        cost=FREE_COST,
        quality=PUBLIC_QUALITY,
        documentation_url=YFINANCE_DOCS,
        executable=True,
        extensions={"attas.vendor_version": "1.2.0"},
    ),
)

ENDPOINT_BY_ID = {endpoint.endpoint_id: endpoint for endpoint in YFINANCE_ENDPOINTS}


class YFinanceProvider(Protocol):
    __version__: str

    def Ticker(self, symbol: str) -> Any:  # noqa: N802 - provider API spelling
        """Return a provider ticker object."""


__all__ = [
    "ACCESS_MODE_PULSE",
    "ACCESS_MODES",
    "DATA_ADVICE_INPUT_SCHEMA",
    "DATA_ADVICE_OUTPUT_SCHEMA",
    "DATA_ADVICE_PULSE",
    "DATA_ADVICE_PULSE_NAME",
    "DATA_AVAILABILITY_INPUT_SCHEMA",
    "DATA_AVAILABILITY_OUTPUT_SCHEMA",
    "DATA_AVAILABILITY_PULSE",
    "DATA_AVAILABILITY_PULSE_NAME",
    "DATA_FETCH_INPUT_SCHEMA",
    "DATA_FETCH_OUTPUT_SCHEMA",
    "DATA_FETCH_PULSE",
    "DATA_FETCH_PULSE_NAME",
    "DATA_REQUEST_PULSE",
    "DATA_REQUEST_PULSE_NAME",
    "DATA_SOURCE_ID",
    "DATA_SOURCE_PARTY",
    "DATA_SOURCE_PIT_TYPE",
    "DATA_SOURCE_STATUS_INPUT_SCHEMA",
    "DATA_SOURCE_STATUS_OUTPUT_SCHEMA",
    "DATA_SOURCE_STATUS_PULSE",
    "DATA_SOURCE_STATUS_PULSE_NAME",
    "DATA_SPEC_INPUT_SCHEMA",
    "DATA_SPEC_OUTPUT_SCHEMA",
    "DATA_SPEC_PULSE",
    "DATA_SPEC_PULSE_NAME",
    "DEFAULT_ACCESS_MODE",
    "ENDPOINT_BY_ID",
    "EndpointExecutionResult",
    "EndpointParameterSpec",
    "EndpointSpec",
    "EndpointSpecSnapshot",
    "JsonObject",
    "YFINANCE_ENDPOINTS",
    "YFinanceProvider",
]
