"""Reduced copy of FinMAS ``YFinanceDataSource``.

The production class owns catalog ingestion, repositories, credentials, and
many documented yfinance operations.  This copy retains its three network
Pulses, bundled snapshot semantics, source-owned execution, and original
provider/canonical response contract for three representative operations.
"""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from datetime import date, datetime, timezone
import math
import re
from typing import Any

from phemacast_lite import Pulser
from prompits_lite import Plaza

from .contracts import (
    ACCESS_MODE_PULSE,
    DATA_AVAILABILITY_PULSE,
    DATA_AVAILABILITY_PULSE_NAME,
    DATA_FETCH_PULSE,
    DATA_FETCH_PULSE_NAME,
    DATA_SOURCE_ID,
    DATA_SOURCE_PARTY,
    DATA_SOURCE_PIT_TYPE,
    DATA_SPEC_PULSE,
    DATA_SPEC_PULSE_NAME,
    ENDPOINT_BY_ID,
    EndpointExecutionResult,
    EndpointSpec,
    EndpointSpecSnapshot,
    JsonObject,
    YFINANCE_ENDPOINTS,
    YFinanceProvider,
)


SNAPSHOT = EndpointSpecSnapshot(
    vendor_id="yfinance",
    retrieved_at="2026-08-12T16:50:26.855956+00:00",
    content_hash="307b9400244c314cd5109359d68c29239296cfef6bd07eef45711458067adf84",
    parser_version="YFinanceSpecParser:3",
    endpoints=YFINANCE_ENDPOINTS,
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")

_FIELD_MAP: dict[str, tuple[tuple[str, str, str], ...]] = {
    "yfinance.ticker.history": (
        ("Date", "timestamp", "string"),
        ("Open", "open", "number"),
        ("High", "high", "number"),
        ("Low", "low", "number"),
        ("Close", "close", "number"),
        ("Adj Close", "adjusted_close", "number"),
        ("Volume", "volume", "number"),
        ("Dividends", "dividends", "number"),
        ("Stock Splits", "stock_splits", "number"),
    ),
    "yfinance.ticker.fast_info": (
        ("symbol", "symbol", "string"),
        ("lastPrice", "last_price", "number"),
        ("currency", "currency", "string"),
        ("exchange", "exchange", "string"),
        ("marketCap", "market_cap", "number"),
        ("dayHigh", "day_high", "number"),
        ("dayLow", "day_low", "number"),
        ("previousClose", "previous_close", "number"),
        ("lastVolume", "last_volume", "number"),
    ),
    "yfinance.ticker.info": (
        ("symbol", "symbol", "string"),
        ("longName", "company_name", "string"),
        ("quoteType", "instrument_type", "string"),
        ("sector", "sector", "string"),
        ("industry", "industry", "string"),
        ("country", "country", "string"),
        ("website", "website", "string"),
        ("longBusinessSummary", "business_summary", "string"),
        ("marketCap", "market_cap", "number"),
        ("currency", "currency", "string"),
        ("exchange", "exchange", "string"),
    ),
}


class YFinanceDataSource(Pulser):
    """YFinance Data Source Pulser with the original Data Source behavior."""

    NETWORK_PULSES = (
        DATA_SPEC_PULSE_NAME,
        DATA_AVAILABILITY_PULSE_NAME,
        DATA_FETCH_PULSE_NAME,
    )

    def __init__(
        self,
        config: Mapping[str, Any] | None = None,
        *,
        provider: YFinanceProvider | Any | None = None,
        plaza: Plaza | None = None,
        name: str = "YFinanceDataSource",
        auto_register: bool = False,
        **kwargs: Any,
    ) -> None:
        if provider is None:
            import yfinance as provider_module

            provider = provider_module
        self.provider = provider
        self.vendor_id = DATA_SOURCE_ID
        self.provider_version = str(getattr(provider, "__version__", ""))
        self.spec_snapshot = SNAPSHOT
        self.data_catalog = [self._dataset_payload(item) for item in SNAPSHOT.endpoints]

        card = copy.deepcopy(dict(kwargs.pop("agent_card", {}) or {}))
        card.update(
            {
                "name": name,
                "description": (
                    "Documents the public yfinance API and executes supported "
                    "library operations directly."
                ),
                "pit_type": DATA_SOURCE_PIT_TYPE,
                "type": DATA_SOURCE_PIT_TYPE,
                "party": DATA_SOURCE_PARTY,
                "tags": ["attas", "data-agent", "data-source", "yfinance"],
            }
        )
        meta = copy.deepcopy(dict(card.get("meta") or {}))
        meta["data_source"] = self.source_profile()
        meta["data_agent_role"] = "source"
        card["meta"] = meta

        super().__init__(
            config=config,
            name=name,
            plaza_url=plaza,
            agent_card=card,
            supported_pulses=[
                copy.deepcopy(DATA_SPEC_PULSE),
                copy.deepcopy(DATA_AVAILABILITY_PULSE),
                copy.deepcopy(DATA_FETCH_PULSE),
            ],
            auto_register=auto_register,
            **kwargs,
        )
        self._apply_runtime_address()

    @property
    def endpoint_catalog(self) -> tuple[EndpointSpec, ...]:
        return self.spec_snapshot.endpoints

    def source_profile(self) -> JsonObject:
        """Return the original normalized public YFinance source profile."""

        return {
            "source_id": self.vendor_id,
            "source_name": getattr(self, "name", "YFinanceDataSource"),
            "provider": "Yahoo Finance via yfinance",
            "provider_version": self.provider_version,
            "description": (
                "Documents the public yfinance API and executes supported "
                "library operations directly."
            ),
            "connectivity": {
                "status": "ready",
                "transport": "python_library",
                "address": self._address_ref(),
                "practice_id": "get_pulse_data",
                "pulse_name": DATA_AVAILABILITY_PULSE_NAME,
                "authentication": (
                    "No user credential required; provider terms and limits apply."
                ),
                "configuration_required": [],
                "notes": ["Live results remain provider- and symbol-dependent."],
            },
        }

    def data_access_status(self) -> JsonObject:
        return {
            "status": "ready",
            "fetch_ready": True,
            "attempt_ready": True,
            "access_mode": ACCESS_MODE_PULSE,
            "credential_required": False,
            "credential_configured": False,
            "verification": "public",
            "verified_at": "",
            "reason": (
                "The installed yfinance runtime can fetch public provider data "
                "without a user credential."
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
        """Reduced copy of ``JsonEndpointSpecRepository.search``."""

        bounded = _bounded_limit(limit, default=20)
        exact = str(endpoint_id or "").strip().lower()
        if exact:
            endpoint = ENDPOINT_BY_ID.get(exact)
            return (endpoint,) if endpoint else ()
        tokens = tuple(
            dict.fromkeys(
                token for token in _TOKEN_RE.findall(str(query or "").lower()) if len(token) > 1
            )
        )
        if not tokens:
            return self.endpoint_catalog[:bounded]

        ranked: list[tuple[int, int, int, EndpointSpec]] = []
        for index, endpoint in enumerate(self.endpoint_catalog):
            identifier = endpoint.endpoint_id.lower()
            name = endpoint.name.lower()
            category = endpoint.category.lower()
            parameter_names = " ".join(item.name.lower() for item in endpoint.parameters)
            searchable = " ".join(
                (
                    identifier,
                    name,
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
                if token in name:
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
        limit = _bounded_limit(input_data.get("limit"), default=20)
        endpoints = self.search_catalog(
            query=query,
            endpoint_id=endpoint_id,
            limit=limit,
        )
        return {
            "query": query,
            "endpoint_id": endpoint_id,
            "source": self._public_source(),
            "endpoints": [self._endpoint_payload(item) for item in endpoints],
            "count": len(endpoints),
            "snapshot": self._snapshot_metadata(),
            "warnings": [],
        }

    def data_availability(self, input_data: Mapping[str, Any]) -> JsonObject:
        query = str(input_data.get("query") or "").strip()
        limit = _bounded_limit(input_data.get("limit"), default=10)
        endpoints = self.search_catalog(query=query, limit=limit)
        datasets = [self._dataset_payload(item) for item in endpoints]
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
                "description": "Documented yfinance access routes.",
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
        try:
            endpoint = self.resolve_endpoint(endpoint_id=endpoint_id)
            result = self.execute_endpoint(endpoint, parameters, {})
        except Exception as exc:
            endpoint = ENDPOINT_BY_ID.get(endpoint_id)
            result = EndpointExecutionResult(
                status="failed",
                endpoint_id=endpoint_id,
                data_schema=endpoint.response_schema if endpoint else {},
                cost=endpoint.cost if endpoint else {},
                error=str(exc),
            )

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
            str(item)
            for item in input_data.get("fields") or []
            if str(item).strip()
        ]
        attas_pulse = _attas_pulse(dataset, requested_fields=requested_fields)
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
            "attas_pulse": attas_pulse,
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
        """Reduced copy of the production source-owned yfinance executor."""

        del auth_context
        if not endpoint.executable:
            return EndpointExecutionResult(
                status="not_executable",
                endpoint_id=endpoint.endpoint_id,
                data_schema=endpoint.response_schema,
                cost=endpoint.cost,
                error="This documented yfinance operation is not enabled for direct execution.",
            )
        try:
            operation = endpoint.operation.removeprefix("yfinance.")
            call_parameters = dict(parameters)
            class_name, member_name = operation.split(".", 1)
            if class_name != "Ticker":
                raise ValueError(f"Direct execution is not enabled for yfinance.{class_name}")
            symbol = str(call_parameters.pop("symbol", "") or "").strip().upper()
            if not symbol:
                raise ValueError("symbol is required")
            instance = self.provider.Ticker(symbol)
            target = getattr(instance, member_name)
            if callable(target):
                raw = target(**call_parameters)
            else:
                if call_parameters:
                    raise ValueError(
                        f"{endpoint.operation} is a property and accepts no call parameters"
                    )
                raw = target
            normalized = _json_safe(raw)
            data = normalized if isinstance(normalized, Mapping) else {"items": normalized}
            return EndpointExecutionResult(
                status="completed",
                endpoint_id=endpoint.endpoint_id,
                data=dict(data),
                data_schema=endpoint.response_schema,
                cost=endpoint.cost,
            )
        except Exception as exc:  # provider boundary
            return EndpointExecutionResult(
                status="failed",
                endpoint_id=endpoint.endpoint_id,
                data_schema=endpoint.response_schema,
                cost=endpoint.cost,
                error=str(exc),
            )

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

    def _public_source(self) -> JsonObject:
        profile = self.source_profile()
        data_access = self.data_access_status()
        connectivity = copy.deepcopy(dict(profile.get("connectivity") or {}))
        connectivity["data_access"] = copy.deepcopy(data_access)
        profile["connectivity"] = connectivity
        profile["data_access"] = copy.deepcopy(data_access)
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
        input_schema = {
            "type": "object",
            "properties": {
                item.name: copy.deepcopy(dict(item.schema)) for item in endpoint.parameters
            },
            "required": [item.name for item in endpoint.parameters if item.required],
        }
        fields = _fields(endpoint)
        mappings = _field_mappings(endpoint, fields)
        canonical_schema = _canonical_schema(endpoint.response_schema, mappings)
        dataset: JsonObject = {
            "dataset_id": endpoint.endpoint_id,
            "endpoint_id": endpoint.endpoint_id,
            "name": endpoint.name,
            "description": endpoint.description,
            "source": endpoint.vendor_id,
            "provider": "Yahoo Finance via yfinance",
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
            "executable": endpoint.executable,
            "credential_required": False,
            "credential_configured": False,
            "fetch_ready": bool(endpoint.executable),
            "attempt_ready": bool(endpoint.executable),
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
    ) -> JsonObject:
        endpoint = ENDPOINT_BY_ID.get(endpoint_id)
        dataset = self._dataset_payload(endpoint) if endpoint else {}
        return {
            "status": "failed",
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
                dataset or {"dataset_id": endpoint_id, "input_schema": {}},
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


def _bounded_limit(value: object, *, default: int) -> int:
    try:
        return max(1, min(int(value), 500)) if value is not None else default
    except (TypeError, ValueError):
        return default


def _fields(endpoint: EndpointSpec) -> list[JsonObject]:
    prefix = "items[]." if endpoint.endpoint_id == "yfinance.ticker.history" else ""
    result: list[JsonObject] = []
    for vendor_name, canonical_name, field_type in _FIELD_MAP[endpoint.endpoint_id]:
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


def _field_mappings(
    endpoint: EndpointSpec,
    fields: Sequence[Mapping[str, Any]],
) -> list[JsonObject]:
    del endpoint
    result: list[JsonObject] = []
    for field in fields:
        provider_path = str(field["path"])
        prefix = provider_path.rsplit(".", 1)[0] + "." if "." in provider_path else ""
        canonical_path = f"{prefix}{field['canonical_name']}"
        result.append(
            {
                "canonical_name": field["canonical_name"],
                "vendor_field_name": field["vendor_name"],
                "provider_path": f"data.{provider_path}",
                "canonical_path": f"canonical_data.{canonical_path}",
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
            return {name_map.get(str(key), str(key)): visit(item) for key, item in value.items()}
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
    if hasattr(value, "reset_index") and hasattr(value, "to_dict"):
        try:
            return [
                _json_safe(item)
                for item in value.reset_index().to_dict(orient="records")
            ]
        except (TypeError, ValueError):
            pass
    if hasattr(value, "to_dict"):
        try:
            return _json_safe(value.to_dict())
        except (TypeError, ValueError):
            pass
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except (TypeError, ValueError):
            pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except (TypeError, ValueError):
            pass
    return str(value)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


YFinanceSource = YFinanceDataSource


__all__ = ["SNAPSHOT", "YFinanceDataSource", "YFinanceSource"]
