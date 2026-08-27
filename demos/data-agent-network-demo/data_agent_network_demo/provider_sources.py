"""Reduced Alpha Vantage and FRED Data Source agents from FinMAS.

The full Data Agent Network has a shared ``AbstractDataSource`` hierarchy,
catalog repositories, encrypted connection stores, and provider adapters.  The
public demo keeps the same Pulser identity and the same ``data_spec``,
``data_availability``, and ``data_fetch`` Pulse surfaces for a small,
representative endpoint snapshot from each provider. Catalog discovery is
entirely local; provider I/O happens only while handling ``data_fetch``.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import date, datetime, timezone
import json
import math
import os
import re
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from phemacast_lite import Pulser
from prompits_lite import Plaza

from .contracts import (
    ACCESS_MODE_PULSE,
    DATA_AVAILABILITY_PULSE,
    DATA_AVAILABILITY_PULSE_NAME,
    DATA_FETCH_PULSE,
    DATA_FETCH_PULSE_NAME,
    DATA_SOURCE_PARTY,
    DATA_SOURCE_PIT_TYPE,
    DATA_SPEC_PULSE,
    DATA_SPEC_PULSE_NAME,
    EndpointExecutionResult,
    EndpointParameterSpec,
    EndpointSpec,
    EndpointSpecSnapshot,
    JsonObject,
)


ALPHA_VANTAGE_SOURCE_ID = "alpha_vantage"
FRED_SOURCE_ID = "fred"
ALPHA_VANTAGE_DOCS = "https://www.alphavantage.co/documentation/"
FRED_DOCS = "https://fred.stlouisfed.org/docs/api/fred/"

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_SECRET_PARAMETER_NAMES = frozenset(
    {
        "token",
        "api_key",
        "apikey",
        "api-key",
        "api_token",
        "authorization",
        "secret",
        "password",
    }
)


class ProviderHttpClient(Protocol):
    """Small injection seam used by deterministic tests.

    A client may expose ``request(method, url, params=..., headers=...)`` like
    httpx/requests, or ``get_json(url, params=...)``.  The runtime default uses
    only the Python standard library.
    """

    def request(self, method: str, url: str, **kwargs: Any) -> Any:
        """Return a response with ``status_code`` and ``json()``."""


def _parameter(
    name: str,
    *,
    description: str,
    required: bool = False,
    schema_type: str = "string",
    default: Any = None,
    enum: Sequence[Any] = (),
) -> EndpointParameterSpec:
    schema: JsonObject = {"type": schema_type}
    if enum:
        schema["enum"] = list(enum)
    return EndpointParameterSpec(
        name=name,
        description=description,
        required=required,
        schema=schema,
        default=default,
    )


_DELEGATED_API_KEY_AUTH: JsonObject = {
    "required": True,
    "scheme": "delegated_connection",
    "provider_scheme": "api_key",
    "credential_reference": "server_environment",
}
_PROVIDER_QUALITY: JsonObject = {
    "status": "provider_documented",
    "notes": ["Coverage, freshness, and availability remain provider-dependent."],
}
_ALPHA_FREE_COST: JsonObject = {
    "amount": 0,
    "currency": "USD",
    "model": "free_or_subscription",
    "provider_cost": "Free tier or subscription, subject to provider limits.",
    "unit": "request",
    "notes": [],
}
_FRED_COST: JsonObject = {
    "amount": 0,
    "currency": "USD",
    "model": "provider_terms",
    "provider_cost": "Access is subject to the provider's terms and request limits.",
    "unit": "request",
    "notes": [],
}

_ALPHA_DAILY_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {
        "Meta Data": {"type": "object", "additionalProperties": True},
        "Time Series (Daily)": {
            "type": "object",
            "additionalProperties": {
                "type": "object",
                "properties": {
                    "1. open": {"type": "string"},
                    "2. high": {"type": "string"},
                    "3. low": {"type": "string"},
                    "4. close": {"type": "string"},
                    "5. volume": {"type": "string"},
                },
            },
        },
    },
    "additionalProperties": True,
}

_ALPHA_QUOTE_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {
        "Global Quote": {
            "type": "object",
            "properties": {
                "01. symbol": {"type": "string"},
                "02. open": {"type": "string"},
                "03. high": {"type": "string"},
                "04. low": {"type": "string"},
                "05. price": {"type": "string"},
                "06. volume": {"type": "string"},
                "07. latest trading day": {"type": "string"},
                "08. previous close": {"type": "string"},
                "09. change": {"type": "string"},
                "10. change percent": {"type": "string"},
            },
        }
    },
    "additionalProperties": True,
}

_ALPHA_OVERVIEW_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {
        "Symbol": {"type": "string"},
        "Name": {"type": "string"},
        "Description": {"type": "string"},
        "Exchange": {"type": "string"},
        "Currency": {"type": "string"},
        "Country": {"type": "string"},
        "Sector": {"type": "string"},
        "Industry": {"type": "string"},
        "MarketCapitalization": {"type": "string"},
    },
    "additionalProperties": True,
}

_FRED_VINTAGE_DATES_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {
        "vintage_dates": {
            "type": "array",
            "items": {"type": "string"},
        }
    },
    "additionalProperties": True,
}

_FRED_OBSERVATIONS_SCHEMA: JsonObject = {
    "type": "object",
    "properties": {
        "observations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "realtime_start": {"type": "string"},
                    "realtime_end": {"type": "string"},
                    "value": {"type": "string"},
                },
            },
        }
    },
    "additionalProperties": True,
}


ALPHA_VANTAGE_ENDPOINTS: tuple[EndpointSpec, ...] = (
    EndpointSpec(
        endpoint_id="alpha_vantage.time_series_daily",
        vendor_id=ALPHA_VANTAGE_SOURCE_ID,
        name="TIME_SERIES_DAILY",
        description=(
            "Raw daily equity prices and volume: open, high, low, close, and "
            "volume for a global equity, with 20+ years of provider-covered "
            "history. Useful for daily OHLCV and historical price requests."
        ),
        category="Time Series Stock Data APIs",
        transport="https",
        operation="TIME_SERIES_DAILY",
        parameters=(
            _parameter(
                "function",
                description="Alpha Vantage function identifier; fixed by the Data Source.",
                required=True,
                default="TIME_SERIES_DAILY",
                enum=("TIME_SERIES_DAILY",),
            ),
            _parameter("symbol", description="Equity ticker symbol.", required=True),
            _parameter(
                "outputsize",
                description="Provider output depth, normally compact or full.",
            ),
            _parameter("datatype", description="Provider response format; JSON is used."),
        ),
        response_schema=_ALPHA_DAILY_SCHEMA,
        authentication={**_DELEGATED_API_KEY_AUTH, "parameter": "apikey"},
        cost={
            **_ALPHA_FREE_COST,
            "model": "tiered",
            "provider_cost": "Free and premium access vary by output depth.",
            "notes": ["Entitlement depends on request parameters."],
        },
        quality=_PROVIDER_QUALITY,
        documentation_url=ALPHA_VANTAGE_DOCS,
        executable=True,
        extensions={"attas.mixed_tier": True, "attas.vendor_version": ""},
    ),
    EndpointSpec(
        endpoint_id="alpha_vantage.global_quote",
        vendor_id=ALPHA_VANTAGE_SOURCE_ID,
        name="Quote Endpoint",
        description=(
            "Latest price and volume information for one ticker, including the "
            "latest trading day, previous close, and price change."
        ),
        category="Time Series Stock Data APIs",
        transport="https",
        operation="GLOBAL_QUOTE",
        parameters=(
            _parameter(
                "function",
                description="Alpha Vantage function identifier; fixed by the Data Source.",
                required=True,
                default="GLOBAL_QUOTE",
                enum=("GLOBAL_QUOTE",),
            ),
            _parameter("symbol", description="Ticker symbol.", required=True),
            _parameter("datatype", description="Provider response format; JSON is used."),
            _parameter("entitlement", description="Optional provider entitlement selector."),
        ),
        response_schema=_ALPHA_QUOTE_SCHEMA,
        authentication={**_DELEGATED_API_KEY_AUTH, "parameter": "apikey"},
        cost=_ALPHA_FREE_COST,
        quality=_PROVIDER_QUALITY,
        documentation_url=ALPHA_VANTAGE_DOCS,
        executable=True,
        extensions={"attas.mixed_tier": False, "attas.vendor_version": ""},
    ),
    EndpointSpec(
        endpoint_id="alpha_vantage.overview",
        vendor_id=ALPHA_VANTAGE_SOURCE_ID,
        name="Company Overview",
        description=(
            "Company profile, sector, industry, market capitalization, financial "
            "ratios, and other key fundamental metrics for an equity."
        ),
        category="Fundamental Data",
        transport="https",
        operation="OVERVIEW",
        parameters=(
            _parameter(
                "function",
                description="Alpha Vantage function identifier; fixed by the Data Source.",
                required=True,
                default="OVERVIEW",
                enum=("OVERVIEW",),
            ),
            _parameter("symbol", description="Equity ticker symbol.", required=True),
        ),
        response_schema=_ALPHA_OVERVIEW_SCHEMA,
        authentication={**_DELEGATED_API_KEY_AUTH, "parameter": "apikey"},
        cost=_ALPHA_FREE_COST,
        quality=_PROVIDER_QUALITY,
        documentation_url=ALPHA_VANTAGE_DOCS,
        executable=True,
        extensions={"attas.mixed_tier": False, "attas.vendor_version": ""},
    ),
)


_FRED_COMMON_PARAMETERS: tuple[EndpointParameterSpec, ...] = (
    _parameter("realtime_start", description="Start of the real-time period as YYYY-MM-DD."),
    _parameter("realtime_end", description="End of the real-time period as YYYY-MM-DD."),
    _parameter("file_type", description="Response type; the demo forces JSON.", default="json"),
    _parameter("limit", description="Maximum results returned.", schema_type="integer"),
    _parameter("offset", description="Result offset.", schema_type="integer"),
    _parameter("order_by", description="Provider-supported result ordering field."),
    _parameter("sort_order", description="Ascending or descending result order."),
)

FRED_ENDPOINTS: tuple[EndpointSpec, ...] = (
    EndpointSpec(
        endpoint_id="fred.fred_series_observations",
        vendor_id=FRED_SOURCE_ID,
        name="fred/series/observations",
        description=(
            "Observations for a FRED economic time series such as U.S. CPI, GDP, "
            "unemployment, or policy rates, with dates, values, transformations, "
            "frequency aggregation, and vintage-date controls."
        ),
        category="FRED API",
        transport="https",
        operation="/fred/series/observations",
        parameters=(
            _parameter(
                "series_id",
                description="FRED series identifier, for example CPIAUCSL.",
                required=True,
            ),
            _parameter("observation_start", description="First observation date as YYYY-MM-DD."),
            _parameter("observation_end", description="Last observation date as YYYY-MM-DD."),
            _parameter("units", description="Provider transformation such as lin, chg, or pch."),
            _parameter("frequency", description="Requested observation frequency."),
            _parameter("aggregation_method", description="Average, sum, or end-of-period aggregation."),
            _parameter("output_type", description="Provider output layout selector.", schema_type="integer"),
            _parameter("vintage_dates", description="Comma-separated vintage dates."),
            *_FRED_COMMON_PARAMETERS,
        ),
        response_schema=_FRED_OBSERVATIONS_SCHEMA,
        authentication=_DELEGATED_API_KEY_AUTH,
        cost=_FRED_COST,
        quality=_PROVIDER_QUALITY,
        documentation_url=f"{FRED_DOCS}series_observations.html",
        executable=True,
        extensions={
            "attas.http_method": "GET",
            "attas.schema_provenance": "public_provider_documentation",
            "attas.specification_only": False,
        },
    ),
    EndpointSpec(
        endpoint_id="fred.fred_series_vintagedates",
        vendor_id=FRED_SOURCE_ID,
        name="fred/series/vintagedates",
        description=(
            "Vintage dates for a FRED economic series such as U.S. CPI, GDP, "
            "unemployment, or interest rates. Use these revision dates to inspect "
            "when historical observations were first released or later revised."
        ),
        category="FRED API",
        transport="https",
        operation="/fred/series/vintagedates",
        parameters=(
            _parameter(
                "series_id",
                description="FRED series identifier, for example CPIAUCSL.",
                required=True,
            ),
            *_FRED_COMMON_PARAMETERS,
        ),
        response_schema=_FRED_VINTAGE_DATES_SCHEMA,
        authentication=_DELEGATED_API_KEY_AUTH,
        cost=_FRED_COST,
        quality=_PROVIDER_QUALITY,
        documentation_url=f"{FRED_DOCS}series_vintagedates.html",
        executable=True,
        extensions={
            "attas.http_method": "GET",
            "attas.schema_provenance": "public_provider_documentation",
            "attas.specification_only": False,
        },
    ),
)


ALPHA_VANTAGE_SNAPSHOT = EndpointSpecSnapshot(
    vendor_id=ALPHA_VANTAGE_SOURCE_ID,
    retrieved_at="2026-08-12T16:50:30.277272+00:00",
    content_hash="cbf45c7498a7eac28e416d5bb988842ddd90a8716e27d348ead1a5439dddac65",
    parser_version="AlphaVantageSpecParser:3-lite",
    endpoints=ALPHA_VANTAGE_ENDPOINTS,
)
FRED_SNAPSHOT = EndpointSpecSnapshot(
    vendor_id=FRED_SOURCE_ID,
    retrieved_at="2026-08-12T16:52:02.951783+00:00",
    content_hash="cb3111863180b58730b880580236b8952c787e947f57ed0b5d21fbe8a54842b3",
    parser_version="FREDSpecParser:2-lite",
    endpoints=FRED_ENDPOINTS,
)


# (provider field, canonical field, JSON type, provider path prefix)
_FIELD_MAP: dict[str, tuple[tuple[str, str, str, str], ...]] = {
    "alpha_vantage.time_series_daily": (
        ("1. open", "open", "string", "Time Series (Daily).[]."),
        ("2. high", "high", "string", "Time Series (Daily).[]."),
        ("3. low", "low", "string", "Time Series (Daily).[]."),
        ("4. close", "close", "string", "Time Series (Daily).[]."),
        ("5. volume", "volume", "string", "Time Series (Daily).[]."),
    ),
    "alpha_vantage.global_quote": (
        ("01. symbol", "symbol", "string", "Global Quote."),
        ("02. open", "open", "string", "Global Quote."),
        ("03. high", "high", "string", "Global Quote."),
        ("04. low", "low", "string", "Global Quote."),
        ("05. price", "last_price", "string", "Global Quote."),
        ("06. volume", "volume", "string", "Global Quote."),
        ("07. latest trading day", "latest_trading_day", "string", "Global Quote."),
        ("08. previous close", "previous_close", "string", "Global Quote."),
        ("09. change", "change", "string", "Global Quote."),
        ("10. change percent", "change_percent", "string", "Global Quote."),
    ),
    "alpha_vantage.overview": (
        ("Symbol", "symbol", "string", ""),
        ("Name", "company_name", "string", ""),
        ("Description", "business_summary", "string", ""),
        ("Exchange", "exchange", "string", ""),
        ("Currency", "currency", "string", ""),
        ("Country", "country", "string", ""),
        ("Sector", "sector", "string", ""),
        ("Industry", "industry", "string", ""),
        ("MarketCapitalization", "market_cap", "string", ""),
    ),
    "fred.fred_series_observations": (
        ("date", "timestamp", "string", "observations[]."),
        ("realtime_start", "realtime_start", "string", "observations[]."),
        ("realtime_end", "realtime_end", "string", "observations[]."),
        ("value", "value", "string", "observations[]."),
    ),
    "fred.fred_series_vintagedates": (
        ("vintage_dates", "vintage_dates", "array", ""),
    ),
}


class _ProviderRequestError(RuntimeError):
    def __init__(self, message: str, *, status: str = "failed") -> None:
        super().__init__(message)
        self.status = status


class ReducedHttpDataSource(Pulser):
    """Faithful Lite reduction of FinMAS ``AbstractDataSource``.

    Subclasses provide a bundled endpoint snapshot and a source-owned GET
    executor.  Nothing in construction, registration, specification lookup, or
    availability lookup performs provider I/O.
    """

    NETWORK_PULSES = (
        DATA_SPEC_PULSE_NAME,
        DATA_AVAILABILITY_PULSE_NAME,
        DATA_FETCH_PULSE_NAME,
    )
    VENDOR_ID = ""
    PROVIDER_NAME = ""
    DESCRIPTION = ""
    ENV_NAME = ""
    SNAPSHOT: EndpointSpecSnapshot

    def __init__(
        self,
        config: Mapping[str, Any] | None = None,
        *,
        http_client: ProviderHttpClient | Any | None = None,
        api_key: str | None = None,
        plaza: Plaza | None = None,
        name: str = "",
        auto_register: bool = False,
        **kwargs: Any,
    ) -> None:
        self.http_client = http_client
        self._source_api_key = str(api_key or "").strip()
        self._last_access: JsonObject = {}
        self.vendor_id = self.VENDOR_ID
        self.spec_snapshot = self.SNAPSHOT
        self._endpoint_by_id = {
            endpoint.endpoint_id.lower(): endpoint for endpoint in self.SNAPSHOT.endpoints
        }
        self.data_catalog = [
            self._dataset_payload(endpoint) for endpoint in self.SNAPSHOT.endpoints
        ]

        resolved_name = name or self.__class__.__name__
        card = copy.deepcopy(dict(kwargs.pop("agent_card", {}) or {}))
        card.update(
            {
                "name": resolved_name,
                "description": self.DESCRIPTION,
                "pit_type": DATA_SOURCE_PIT_TYPE,
                "type": DATA_SOURCE_PIT_TYPE,
                "party": DATA_SOURCE_PARTY,
                "tags": [
                    "attas",
                    "data-agent",
                    "data-source",
                    self.vendor_id,
                ],
            }
        )
        meta = copy.deepcopy(dict(card.get("meta") or {}))
        meta["data_source"] = self.source_profile(name=resolved_name)
        meta["data_agent_role"] = "source"
        card["meta"] = meta

        # Match the production source lifecycle: apply the DataSource card
        # after Pulser initialization, then register that finalized card.
        super().__init__(
            config=config,
            name=resolved_name,
            plaza_url=plaza,
            agent_card=card,
            supported_pulses=[
                copy.deepcopy(DATA_SPEC_PULSE),
                copy.deepcopy(DATA_AVAILABILITY_PULSE),
                copy.deepcopy(DATA_FETCH_PULSE),
            ],
            auto_register=False,
            **kwargs,
        )
        self._apply_runtime_address()
        if auto_register and self.plaza_url:
            self.register()

    @property
    def endpoint_catalog(self) -> tuple[EndpointSpec, ...]:
        return self.spec_snapshot.endpoints

    def register(self, **kwargs: Any) -> Any:
        self._apply_runtime_address()
        result = super().register(**kwargs)
        self._apply_runtime_address()
        return result

    def source_profile(self, *, name: str = "") -> JsonObject:
        configured = self._credential_configured()
        return {
            "source_id": self.vendor_id,
            "source_name": name or getattr(self, "name", self.__class__.__name__),
            "provider": self.PROVIDER_NAME,
            "description": self.DESCRIPTION,
            "connectivity": {
                "status": "configured",
                "transport": "https",
                "address": self._address_ref(),
                "practice_id": "get_pulse_data",
                "pulse_name": DATA_AVAILABILITY_PULSE_NAME,
                "authentication": (
                    "A source-owned API key is required for live data_fetch access."
                ),
                "configuration_required": []
                if configured
                else [f"Set {self.ENV_NAME} in the server environment"],
                "notes": [
                    "Specification discovery and catalog advice do not require a key.",
                    "Pulse requests never accept raw provider credentials.",
                ],
            },
        }

    def data_access_status(self) -> JsonObject:
        configured = self._credential_configured()
        if self._last_access:
            value = copy.deepcopy(self._last_access)
            value["credential_configured"] = configured
            value["attempt_ready"] = configured
            return value
        return {
            "status": "unknown" if configured else "authentication_required",
            "fetch_ready": configured,
            "attempt_ready": configured,
            "access_mode": ACCESS_MODE_PULSE,
            "credential_required": True,
            "credential_configured": configured,
            "verification": "unverified" if configured else "unknown",
            "verified_at": "",
            "reason": (
                "A source-owned credential is configured; a successful live fetch "
                "is still required to verify access."
                if configured
                else f"Set {self.ENV_NAME} in the server environment before live fetches."
            ),
        }

    def resolve_endpoint(self, *, endpoint_id: str = "", query: str = "") -> EndpointSpec:
        matches = self.search_catalog(query=query, endpoint_id=endpoint_id, limit=2)
        if not matches:
            raise LookupError(f"No endpoint specification matched {endpoint_id or query!r}")
        if not endpoint_id and len(matches) > 1:
            raise LookupError(f"Endpoint query is ambiguous: {query!r}")
        return matches[0]

    def search_catalog(
        self,
        query: str = "",
        *,
        endpoint_id: str = "",
        limit: int = 20,
    ) -> tuple[EndpointSpec, ...]:
        bounded = _bounded_limit(limit, default=20)
        exact = str(endpoint_id or "").strip().lower()
        if exact:
            endpoint = self._endpoint_by_id.get(exact)
            return (endpoint,) if endpoint else ()
        tokens = tuple(
            dict.fromkeys(
                token
                for token in _TOKEN_RE.findall(str(query or "").lower())
                if len(token) > 1
            )
        )
        if not tokens:
            return self.endpoint_catalog[:bounded]

        ranked: list[tuple[int, int, int, EndpointSpec]] = []
        for index, endpoint in enumerate(self.endpoint_catalog):
            identifier = endpoint.endpoint_id.lower()
            endpoint_name = endpoint.name.lower()
            category = endpoint.category.lower()
            parameter_names = " ".join(item.name.lower() for item in endpoint.parameters)
            searchable = " ".join(
                (
                    identifier,
                    endpoint_name,
                    endpoint.description.lower(),
                    category,
                    endpoint.operation.lower(),
                    parameter_names,
                    str(endpoint.extensions).lower(),
                )
            )
            score = 0
            matched_tokens = 0
            for token in tokens:
                matched = False
                if token in identifier:
                    score += 8
                    matched = True
                if token in endpoint_name:
                    score += 6
                    matched = True
                if token in category:
                    score += 4
                    matched = True
                if token in parameter_names:
                    score += 3
                    matched = True
                if token in searchable:
                    score += 1
                    matched = True
                if matched:
                    matched_tokens += 1
            if score:
                ranked.append((matched_tokens, score, -index, endpoint))
        ranked.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)
        return tuple(item[3] for item in ranked[:bounded])

    def data_spec(self, input_data: Mapping[str, Any]) -> JsonObject:
        query = str(input_data.get("query") or "").strip()
        endpoint_id = str(input_data.get("endpoint_id") or "").strip()
        endpoints = self.search_catalog(
            query=query,
            endpoint_id=endpoint_id,
            limit=_bounded_limit(input_data.get("limit"), default=20),
        )
        return {
            "query": query,
            "endpoint_id": endpoint_id,
            "source": self._public_source(),
            "endpoints": [self._endpoint_payload(endpoint) for endpoint in endpoints],
            "count": len(endpoints),
            "snapshot": self._snapshot_metadata(),
            "warnings": [],
        }

    def data_availability(self, input_data: Mapping[str, Any]) -> JsonObject:
        query = str(input_data.get("query") or "").strip()
        endpoints = self.search_catalog(
            query=query,
            limit=_bounded_limit(input_data.get("limit"), default=10),
        )
        datasets = [self._dataset_payload(endpoint) for endpoint in endpoints]
        fields = [
            copy.deepcopy(field)
            for dataset in datasets
            for field in dataset.get("fields", [])
            if isinstance(field, Mapping)
        ]
        result_sets = [
            {
                "format": "endpoint",
                "label": "Endpoint specifications",
                "description": f"Documented {self.PROVIDER_NAME} access routes.",
                "primary": True,
                "count": len(datasets),
                "items": copy.deepcopy(datasets),
            },
            {
                "format": "field",
                "label": "Canonical fields",
                "description": "Provider fields mapped to the Attas data_fetch view.",
                "primary": False,
                "count": len(fields),
                "items": copy.deepcopy(fields),
            },
        ]
        return {
            "query": query,
            "source": self._public_source(),
            "available": bool(datasets),
            "datasets": datasets,
            "fields": fields,
            "field_count": len(fields),
            "endpoint_count": len(datasets),
            "result_formats": ["endpoint", "field"],
            "result_sets": result_sets,
            "count": len(datasets),
            "match_reason": (
                f"Matched {len(fields)} field(s) across {len(datasets)} documented "
                "endpoint access route(s)."
            ),
            "as_of": _utc_now(),
            "warnings": [],
        }

    def data_fetch(self, input_data: Mapping[str, Any]) -> JsonObject:
        endpoint_id = str(
            input_data.get("endpoint_id") or input_data.get("dataset_id") or ""
        ).strip()
        access_mode = str(input_data.get("access_mode") or ACCESS_MODE_PULSE)
        if access_mode != ACCESS_MODE_PULSE:
            return self._fetch_failure(
                endpoint_id,
                error="Unsupported data access mode.",
                access_mode=access_mode,
            )
        parameters = (
            input_data.get("parameters")
            if isinstance(input_data.get("parameters"), Mapping)
            else {}
        )
        auth_context = (
            input_data.get("auth_context")
            if isinstance(input_data.get("auth_context"), Mapping)
            else {}
        )
        if _contains_secret(input_data) or _contains_secret(parameters) or _contains_secret(auth_context):
            return self._fetch_failure(
                endpoint_id,
                error="Raw API credentials are not accepted in data_fetch pulses.",
                access_mode=access_mode,
            )

        try:
            endpoint = self.resolve_endpoint(endpoint_id=endpoint_id)
            result = self.execute_endpoint(endpoint, parameters, auth_context)
        except Exception as exc:
            endpoint = self._endpoint_by_id.get(endpoint_id.lower())
            result = EndpointExecutionResult(
                status="failed",
                endpoint_id=endpoint_id,
                data_schema=endpoint.response_schema if endpoint else {},
                cost=endpoint.cost if endpoint else {},
                error=str(exc),
            )
        self._record_access(result)

        dataset = self._dataset_payload(endpoint) if endpoint else {
            "dataset_id": endpoint_id,
            "input_schema": {},
            "data_schema": dict(result.data_schema),
            "canonical_data_schema": {},
            "fields": [],
            "field_mappings": [],
        }
        data = _json_safe(result.data)
        if not isinstance(data, Mapping):
            data = {"items": data}
        mappings = [
            copy.deepcopy(item)
            for item in dataset.get("field_mappings", [])
            if isinstance(item, Mapping)
        ]
        requested_fields = [
            str(item) for item in input_data.get("fields") or [] if str(item).strip()
        ]
        return {
            "status": result.status,
            "source": self._public_source(),
            "dataset_id": endpoint_id,
            "backend_id": self.vendor_id,
            "data": copy.deepcopy(dict(data)),
            "canonical_data": _canonicalize_data(dict(data), mappings),
            "data_schema": copy.deepcopy(dict(result.data_schema)),
            "canonical_data_schema": copy.deepcopy(
                dict(dataset.get("canonical_data_schema") or {})
            ),
            "fields": copy.deepcopy(list(dataset.get("fields") or [])),
            "field_mappings": mappings,
            "attas_pulse": _attas_pulse(dataset, requested_fields=requested_fields),
            "cost": copy.deepcopy(dict(result.cost)),
            "warnings": list(result.warnings),
            "error": result.error,
            "access_mode": access_mode,
        }

    def execute_endpoint(
        self,
        endpoint: EndpointSpec,
        parameters: Mapping[str, Any],
        auth_context: Mapping[str, Any],
    ) -> EndpointExecutionResult:
        raise NotImplementedError

    def fetch_pulse_payload(
        self,
        pulse_name: str,
        input_data: JsonObject,
        pulse_definition: JsonObject,
    ) -> JsonObject:
        if pulse_name == DATA_SPEC_PULSE_NAME:
            return self.data_spec(input_data or {})
        if pulse_name == DATA_AVAILABILITY_PULSE_NAME:
            return self.data_availability(input_data or {})
        if pulse_name == DATA_FETCH_PULSE_NAME:
            return self.data_fetch(input_data or {})
        return super().fetch_pulse_payload(pulse_name, input_data or {}, pulse_definition)

    def _request_json(self, url: str, parameters: Mapping[str, Any]) -> Any:
        """Make one bounded JSON GET; URL/key details never escape this boundary."""

        headers = {
            "Accept": "application/json",
            "User-Agent": "Agentive-Finance-Lab-Multiple-Sources-Demo/0.1",
        }
        client = self.http_client
        if client is None:
            query = urlencode(
                [(str(key), value) for key, value in parameters.items() if value is not None],
                doseq=True,
            )
            request = Request(f"{url}?{query}" if query else url, headers=headers, method="GET")
            try:
                with urlopen(request, timeout=30) as response:  # noqa: S310 - fixed provider URLs
                    raw = response.read(4 * 1024 * 1024 + 1)
                    if len(raw) > 4 * 1024 * 1024:
                        raise _ProviderRequestError("Provider response exceeded the demo limit.")
                    return json.loads(raw.decode("utf-8"))
            except HTTPError as exc:
                if exc.code in {401, 402, 403}:
                    raise _ProviderRequestError(
                        "The provider rejected the configured credential or entitlement.",
                        status="authentication_required",
                    ) from None
                if exc.code == 429:
                    raise _ProviderRequestError(
                        "The provider rate limit was reached.", status="rate_limited"
                    ) from None
                raise _ProviderRequestError(
                    f"Provider request failed with HTTP status {exc.code}."
                ) from None
            except (URLError, TimeoutError):
                raise _ProviderRequestError(
                    "The provider request could not be completed."
                ) from None
            except (UnicodeDecodeError, json.JSONDecodeError):
                raise _ProviderRequestError("The provider returned a non-JSON response.") from None

        response: Any
        get_json = getattr(client, "get_json", None)
        if callable(get_json):
            response = get_json(url, params=copy.deepcopy(dict(parameters)))
        elif callable(getattr(client, "request", None)):
            response = client.request(
                "GET",
                url,
                params=copy.deepcopy(dict(parameters)),
                headers=headers,
            )
        elif callable(getattr(client, "get", None)):
            response = client.get(
                url,
                params=copy.deepcopy(dict(parameters)),
                headers=headers,
            )
        elif callable(client):
            response = client(url, copy.deepcopy(dict(parameters)))
        else:
            raise _ProviderRequestError("The configured provider client is not callable.")

        if isinstance(response, (Mapping, list, tuple)):
            return _json_safe(response)
        status_code = int(getattr(response, "status_code", 200) or 0)
        if status_code in {401, 402, 403}:
            raise _ProviderRequestError(
                "The provider rejected the configured credential or entitlement.",
                status="authentication_required",
            )
        if status_code == 429:
            raise _ProviderRequestError(
                "The provider rate limit was reached.", status="rate_limited"
            )
        if status_code < 200 or status_code >= 300:
            raise _ProviderRequestError(
                f"Provider request failed with HTTP status {status_code}."
            )
        try:
            value = response.json()
        except Exception:
            raise _ProviderRequestError("The provider returned a non-JSON response.") from None
        return _json_safe(value)

    def _validated_parameters(
        self,
        endpoint: EndpointSpec,
        parameters: Mapping[str, Any],
    ) -> JsonObject:
        if _contains_secret(parameters):
            raise _ProviderRequestError(
                "Raw API credentials are not accepted as endpoint parameters."
            )
        specs = {parameter.name: parameter for parameter in endpoint.parameters}
        unknown = sorted(str(name) for name in set(parameters) - set(specs))
        if unknown:
            raise _ProviderRequestError(
                f"Unsupported endpoint parameter(s): {', '.join(unknown)}"
            )
        resolved: JsonObject = {
            name: copy.deepcopy(parameter.default)
            for name, parameter in specs.items()
            if parameter.default is not None
        }
        resolved.update(
            {
                str(name): copy.deepcopy(value)
                for name, value in parameters.items()
                if value is not None
            }
        )
        missing = [
            name
            for name, parameter in specs.items()
            if parameter.required
            and parameter.default is None
            and resolved.get(name) in (None, "")
        ]
        if missing:
            raise _ProviderRequestError(
                f"Missing required endpoint parameter(s): {', '.join(missing)}"
            )
        return resolved

    def _credential_configured(self) -> bool:
        return bool(self._resolve_api_key())

    def _resolve_api_key(self) -> str:
        return self._source_api_key or str(os.getenv(self.ENV_NAME) or "").strip()

    def _record_access(self, result: EndpointExecutionResult) -> None:
        now = _utc_now()
        if result.status == "completed":
            self._last_access = {
                "status": "ready",
                "fetch_ready": True,
                "attempt_ready": True,
                "access_mode": ACCESS_MODE_PULSE,
                "credential_required": True,
                "credential_configured": True,
                "verification": "verified",
                "verified_at": now,
                "reason": "A live provider fetch succeeded recently.",
            }
        elif result.status == "authentication_required":
            self._last_access = {
                "status": "authentication_required",
                "fetch_ready": False,
                "attempt_ready": self._credential_configured(),
                "access_mode": ACCESS_MODE_PULSE,
                "credential_required": True,
                "credential_configured": self._credential_configured(),
                "verification": "failed",
                "verified_at": now,
                "reason": result.error or "Provider authentication failed.",
            }
        elif result.status == "rate_limited":
            self._last_access = {
                "status": "unavailable",
                "fetch_ready": False,
                "attempt_ready": self._credential_configured(),
                "access_mode": ACCESS_MODE_PULSE,
                "credential_required": True,
                "credential_configured": self._credential_configured(),
                "verification": "failed",
                "verified_at": now,
                "reason": result.error or "The provider is currently rate limited.",
            }

    def _public_source(self) -> JsonObject:
        profile = self.source_profile()
        access = self.data_access_status()
        connectivity = copy.deepcopy(dict(profile.get("connectivity") or {}))
        connectivity["data_access"] = copy.deepcopy(access)
        if access["attempt_ready"]:
            connectivity["configuration_required"] = []
        profile["connectivity"] = connectivity
        # YFinance Lite exposes this convenience field, so retain it here too.
        profile["data_access"] = copy.deepcopy(access)
        return profile

    def _snapshot_metadata(self) -> JsonObject:
        return {
            "status": "ready",
            "vendor_id": self.spec_snapshot.vendor_id,
            "retrieved_at": self.spec_snapshot.retrieved_at,
            "content_hash": self.spec_snapshot.content_hash,
            "parser_version": self.spec_snapshot.parser_version,
            "endpoint_count": len(self.spec_snapshot.endpoints),
        }

    def _endpoint_payload(self, endpoint: EndpointSpec) -> JsonObject:
        payload = _json_safe(asdict(endpoint))
        dataset = self._dataset_payload(endpoint)
        payload["source_pulse_name"] = str(payload.get("pulse_name") or "")
        payload["pulse_name"] = DATA_FETCH_PULSE_NAME
        payload["executable"] = bool(dataset["executable"])
        payload["credential_required"] = bool(dataset["credential_required"])
        payload["credential_configured"] = bool(dataset["credential_configured"])
        payload["fetch_ready"] = bool(dataset["fetch_ready"])
        payload["attempt_ready"] = bool(dataset["attempt_ready"])
        payload["canonical_response_schema"] = copy.deepcopy(
            dict(dataset["canonical_data_schema"])
        )
        payload["field_mappings"] = copy.deepcopy(dataset["field_mappings"])
        payload["attas_pulse"] = copy.deepcopy(dataset["attas_pulse"])
        return payload

    def _dataset_payload(self, endpoint: EndpointSpec) -> JsonObject:
        data_access = self.data_access_status()
        input_schema = {
            "type": "object",
            "properties": {
                parameter.name: copy.deepcopy(dict(parameter.schema))
                for parameter in endpoint.parameters
            },
            "required": [
                parameter.name for parameter in endpoint.parameters if parameter.required
            ],
        }
        fields = _fields(endpoint)
        mappings = _field_mappings(fields)
        canonical_schema = _canonical_schema(endpoint.response_schema, mappings)
        dataset: JsonObject = {
            "dataset_id": endpoint.endpoint_id,
            "endpoint_id": endpoint.endpoint_id,
            "name": endpoint.name,
            "description": endpoint.description,
            "source": endpoint.vendor_id,
            "provider": self.PROVIDER_NAME,
            "source_pulse_name": endpoint.pulse_name,
            "pulse_name": DATA_FETCH_PULSE_NAME,
            "fetch_pulse": DATA_FETCH_PULSE_NAME,
            "tags": [endpoint.vendor_id, endpoint.category, endpoint.transport],
            "input_schema": input_schema,
            "output_schema": copy.deepcopy(dict(endpoint.response_schema)),
            "data_schema": copy.deepcopy(dict(endpoint.response_schema)),
            "canonical_data_schema": canonical_schema,
            "fields": fields,
            "field_mappings": mappings,
            "sample_data": {"illustrative": True, "operation": endpoint.operation},
            "cost": copy.deepcopy(dict(endpoint.cost)),
            "quality": copy.deepcopy(dict(endpoint.quality)),
            "authentication": copy.deepcopy(dict(endpoint.authentication)),
            # Adapter implementation and runtime credential readiness are
            # separate facts. This keeps a missing-key fetch attempt visible
            # while still exposing the exact server-side precondition.
            "executable": bool(endpoint.executable),
            "credential_required": bool(data_access["credential_required"]),
            "credential_configured": bool(data_access["credential_configured"]),
            "fetch_ready": bool(endpoint.executable and data_access["fetch_ready"]),
            "attempt_ready": bool(endpoint.executable and data_access["attempt_ready"]),
            "operation": endpoint.operation,
            "category": endpoint.category,
            "backend_id": endpoint.operation,
        }
        dataset["attas_pulse"] = _attas_pulse(dataset)
        return dataset

    def _fetch_failure(
        self,
        endpoint_id: str,
        *,
        error: str,
        access_mode: str,
        status: str = "failed",
    ) -> JsonObject:
        endpoint = self._endpoint_by_id.get(endpoint_id.lower())
        dataset = self._dataset_payload(endpoint) if endpoint else {}
        return {
            "status": status,
            "source": self._public_source(),
            "dataset_id": endpoint_id,
            "backend_id": self.vendor_id,
            "data": {},
            "canonical_data": {},
            "data_schema": copy.deepcopy(dict(dataset.get("data_schema") or {})),
            "canonical_data_schema": copy.deepcopy(
                dict(dataset.get("canonical_data_schema") or {})
            ),
            "fields": copy.deepcopy(list(dataset.get("fields") or [])),
            "field_mappings": copy.deepcopy(list(dataset.get("field_mappings") or [])),
            "attas_pulse": _attas_pulse(
                dataset or {"dataset_id": endpoint_id, "input_schema": {}}
            ),
            "cost": copy.deepcopy(dict(dataset.get("cost") or {})),
            "warnings": [],
            "error": error,
            "access_mode": access_mode,
        }

    def _apply_runtime_address(self) -> None:
        card = copy.deepcopy(dict(getattr(self, "agent_card", {}) or {}))
        card["pit_type"] = DATA_SOURCE_PIT_TYPE
        card["type"] = DATA_SOURCE_PIT_TYPE
        card["party"] = DATA_SOURCE_PARTY
        card["role"] = "data-source"
        meta = copy.deepcopy(dict(card.get("meta") or {}))
        meta["data_source"] = self.source_profile()
        meta["data_agent_role"] = "source"
        meta["endpoint_count"] = len(self.spec_snapshot.endpoints)
        meta["spec_snapshot"] = self._snapshot_metadata()
        card["meta"] = meta
        self.agent_card = card
        self.meta = meta

    def _address_ref(self) -> str:
        address = getattr(self, "pit_address", None)
        if address is not None and hasattr(address, "to_ref"):
            try:
                return str(address.to_ref())
            except TypeError:
                return str(address.to_ref(reference_plaza=None))
        return ""


class AlphaVantageDataSource(ReducedHttpDataSource):
    """Alpha Vantage Data Source Pulser with source-owned API-key execution."""

    VENDOR_ID = ALPHA_VANTAGE_SOURCE_ID
    PROVIDER_NAME = "Alpha Vantage"
    DESCRIPTION = (
        "Documents Alpha Vantage API functions and executes the reduced "
        "allowlisted endpoints with a source-owned server credential."
    )
    ENV_NAME = "ALPHA_VANTAGE_API_KEY"
    SNAPSHOT = ALPHA_VANTAGE_SNAPSHOT
    BASE_URL = "https://www.alphavantage.co/query"

    def execute_endpoint(
        self,
        endpoint: EndpointSpec,
        parameters: Mapping[str, Any],
        auth_context: Mapping[str, Any],
    ) -> EndpointExecutionResult:
        if _contains_secret(parameters) or _contains_secret(auth_context):
            return _execution_failure(
                endpoint,
                "Raw API credentials are not accepted in Pulse inputs; configure the source server.",
            )
        if not endpoint.executable:
            return _execution_failure(
                endpoint,
                "This Alpha Vantage operation is available as a specification only.",
                status="not_executable",
            )
        key = self._resolve_api_key()
        if not key:
            return _execution_failure(
                endpoint,
                "No usable source-owned Alpha Vantage credential is configured.",
                status="authentication_required",
            )
        try:
            query = self._validated_parameters(endpoint, parameters)
            query["function"] = endpoint.operation
            query["datatype"] = "json"
            query["apikey"] = key
            raw = self._request_json(self.BASE_URL, query)
            if not isinstance(raw, Mapping):
                raise _ProviderRequestError("Alpha Vantage returned an invalid JSON payload.")
            provider_message = str(
                raw.get("Error Message") or raw.get("Information") or raw.get("Note") or ""
            ).strip()
            if provider_message:
                lowered = provider_message.lower()
                status = (
                    "rate_limited"
                    if "rate limit" in lowered or "call frequency" in lowered
                    else "authentication_required"
                    if "api key" in lowered and ("invalid" in lowered or "claim" in lowered)
                    else "failed"
                )
                raise _ProviderRequestError(
                    "Alpha Vantage rejected the credential, request parameters, "
                    "rate limit, or endpoint entitlement.",
                    status=status,
                )
            return EndpointExecutionResult(
                status="completed",
                endpoint_id=endpoint.endpoint_id,
                data=copy.deepcopy(dict(raw)),
                data_schema=endpoint.response_schema,
                cost=endpoint.cost,
            )
        except _ProviderRequestError as exc:
            return _execution_failure(endpoint, str(exc), status=exc.status)
        except Exception:
            return _execution_failure(
                endpoint, "Alpha Vantage request could not be completed."
            )


class FREDDataSource(ReducedHttpDataSource):
    """FRED and ALFRED Data Source Pulser with source-owned API-key execution."""

    VENDOR_ID = FRED_SOURCE_ID
    PROVIDER_NAME = "Federal Reserve Bank of St. Louis"
    DESCRIPTION = (
        "Public FRED and ALFRED endpoint catalog for economic and financial "
        "observations and revision vintage dates."
    )
    ENV_NAME = "FRED_API_KEY"
    SNAPSHOT = FRED_SNAPSHOT
    BASE_URL = "https://api.stlouisfed.org"

    def source_profile(self, *, name: str = "") -> JsonObject:
        profile = super().source_profile(name=name)
        profile["source_name"] = name or getattr(
            self, "name", "FRED and ALFRED Data Source"
        )
        profile["coverage"] = {
            "asset_classes": [
                "macro",
                "interest rates",
                "economic indicators",
                "financial series",
            ]
        }
        return profile

    def execute_endpoint(
        self,
        endpoint: EndpointSpec,
        parameters: Mapping[str, Any],
        auth_context: Mapping[str, Any],
    ) -> EndpointExecutionResult:
        if _contains_secret(parameters) or _contains_secret(auth_context):
            return _execution_failure(
                endpoint,
                "Raw API credentials are not accepted in Pulse inputs; configure the source server.",
            )
        if not endpoint.executable or not endpoint.operation.startswith("/fred/"):
            return _execution_failure(
                endpoint,
                "This FRED operation is available as a specification only.",
                status="not_executable",
            )
        key = self._resolve_api_key()
        if not key:
            return _execution_failure(
                endpoint,
                "No usable source-owned FRED credential is configured.",
                status="authentication_required",
            )
        try:
            query = self._validated_parameters(endpoint, parameters)
            query["file_type"] = "json"
            query["api_key"] = key
            raw = self._request_json(f"{self.BASE_URL}{endpoint.operation}", query)
            if not isinstance(raw, Mapping):
                raise _ProviderRequestError("FRED returned an invalid JSON payload.")
            if raw.get("error_code") or raw.get("error_message"):
                message = str(raw.get("error_message") or "").lower()
                status = (
                    "authentication_required"
                    if "api key" in message or "credential" in message
                    else "failed"
                )
                raise _ProviderRequestError(
                    "FRED rejected the credential or request parameters.", status=status
                )
            return EndpointExecutionResult(
                status="completed",
                endpoint_id=endpoint.endpoint_id,
                data=copy.deepcopy(dict(raw)),
                data_schema=endpoint.response_schema,
                cost=endpoint.cost,
            )
        except _ProviderRequestError as exc:
            return _execution_failure(endpoint, str(exc), status=exc.status)
        except Exception:
            return _execution_failure(endpoint, "FRED request could not be completed.")


def _execution_failure(
    endpoint: EndpointSpec,
    error: str,
    *,
    status: str = "failed",
) -> EndpointExecutionResult:
    return EndpointExecutionResult(
        status=status,
        endpoint_id=endpoint.endpoint_id,
        data_schema=endpoint.response_schema,
        cost=endpoint.cost,
        error=error,
    )


def _contains_secret(value: Mapping[str, Any]) -> bool:
    return any(str(name).strip().lower() in _SECRET_PARAMETER_NAMES for name in value)


def _bounded_limit(value: object, *, default: int) -> int:
    try:
        return max(1, min(int(value), 500)) if value is not None else default
    except (TypeError, ValueError):
        return default


def _fields(endpoint: EndpointSpec) -> list[JsonObject]:
    result: list[JsonObject] = []
    for vendor_name, canonical_name, field_type, prefix in _FIELD_MAP[endpoint.endpoint_id]:
        result.append(
            {
                "name": vendor_name,
                "vendor_name": vendor_name,
                "path": f"{prefix}{vendor_name}",
                "canonical_name": canonical_name,
                "definition": f"Attas canonical field `{canonical_name}`.",
                "provider_definition": "",
                "description": f"Provider field `{vendor_name}`.",
                "type": field_type,
                "unit": "provider-defined",
                "required": False,
                "nullable": True,
                "inferred": False,
                "schema": {"type": field_type},
            }
        )
    return result


def _field_mappings(fields: Sequence[Mapping[str, Any]]) -> list[JsonObject]:
    result: list[JsonObject] = []
    for field in fields:
        provider_path = str(field["path"])
        prefix = provider_path.rsplit(".", 1)[0] + "." if "." in provider_path else ""
        result.append(
            {
                "canonical_name": field["canonical_name"],
                "vendor_field_name": field["vendor_name"],
                "provider_path": f"data.{provider_path}",
                "canonical_path": f"canonical_data.{prefix}{field['canonical_name']}",
                "definition": field["definition"],
                "provider_definition": field["provider_definition"],
                "type": field["type"],
                "unit": field["unit"],
            }
        )
    return result


def _attas_pulse(
    dataset: Mapping[str, Any],
    *,
    requested_fields: Sequence[str] = (),
) -> JsonObject:
    mappings = [
        copy.deepcopy(item)
        for item in dataset.get("field_mappings", [])
        if isinstance(item, Mapping)
    ]
    available = list(
        dict.fromkeys(str(item.get("canonical_name")) for item in mappings)
    )
    selected = [item for item in requested_fields if item in available] or available
    dataset_id = str(dataset.get("dataset_id") or "")
    return {
        "contract_version": "attas.data_fetch.v1",
        "pulse_name": DATA_FETCH_PULSE_NAME,
        "pulse_address": "plaza://pulse/attas/data_fetch",
        "endpoint_id": dataset_id,
        "request": {
            "dataset_id": dataset_id,
            "field_selector": "fields",
            "available_fields": available,
            "fields": selected,
            "parameters_schema": copy.deepcopy(dict(dataset.get("input_schema") or {})),
        },
        "response": {
            "provider_container": "data",
            "canonical_container": "canonical_data",
            "provider_schema": copy.deepcopy(dict(dataset.get("data_schema") or {})),
            "canonical_schema": copy.deepcopy(
                dict(dataset.get("canonical_data_schema") or {})
            ),
            "field_mappings": mappings,
        },
    }


def _canonical_schema(
    schema: Mapping[str, Any],
    mappings: Sequence[Mapping[str, Any]],
) -> JsonObject:
    name_map = {
        str(item["vendor_field_name"]): str(item["canonical_name"])
        for item in mappings
    }

    def visit(value: Mapping[str, Any]) -> JsonObject:
        result = copy.deepcopy(dict(value))
        properties = value.get("properties")
        if isinstance(properties, Mapping):
            result["properties"] = {
                name_map.get(str(key), str(key)): visit(child)
                if isinstance(child, Mapping)
                else copy.deepcopy(child)
                for key, child in properties.items()
            }
        if isinstance(value.get("items"), Mapping):
            result["items"] = visit(value["items"])
        if isinstance(value.get("additionalProperties"), Mapping):
            result["additionalProperties"] = visit(value["additionalProperties"])
        return result

    return visit(schema)


def _canonicalize_data(
    data: Any,
    field_mappings: Sequence[Mapping[str, Any]],
) -> Any:
    name_map = {
        str(item.get("vendor_field_name")): str(item.get("canonical_name"))
        for item in field_mappings
        if item.get("vendor_field_name") and item.get("canonical_name")
    }

    def visit(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {
                name_map.get(str(key), str(key)): visit(item)
                for key, item in value.items()
            }
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
            return [visit(item) for item in value]
        return copy.deepcopy(value)

    return visit(data)


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [_json_safe(item) for item in value]
    return str(value)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


__all__ = [
    "ALPHA_VANTAGE_ENDPOINTS",
    "ALPHA_VANTAGE_SNAPSHOT",
    "ALPHA_VANTAGE_SOURCE_ID",
    "FRED_ENDPOINTS",
    "FRED_SNAPSHOT",
    "FRED_SOURCE_ID",
    "AlphaVantageDataSource",
    "FREDDataSource",
    "ProviderHttpClient",
    "ReducedHttpDataSource",
]
