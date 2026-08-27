"""Reduced copies of the FinMAS Data Consultant and Data User Personas."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
import re
import time
from typing import Any, Mapping, Sequence

from phemacast_lite import RAGPersona
from prompits_lite import Plaza

from .contracts import (
    ACCESS_MODE_PULSE,
    DATA_ADVICE_PULSE,
    DATA_ADVICE_PULSE_NAME,
    DATA_AVAILABILITY_PULSE_NAME,
    DATA_FETCH_PULSE,
    DATA_FETCH_PULSE_NAME,
    DATA_REQUEST_PULSE,
    DATA_REQUEST_PULSE_NAME,
    DATA_SOURCE_PARTY,
    DATA_SOURCE_PIT_TYPE,
    DATA_SOURCE_STATUS_PULSE,
    DATA_SOURCE_STATUS_PULSE_NAME,
    DATA_SPEC_PULSE,
    DATA_SPEC_PULSE_NAME,
    JsonObject,
)


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "a",
    "about",
    "and",
    "available",
    "can",
    "data",
    "do",
    "for",
    "from",
    "get",
    "have",
    "i",
    "is",
    "me",
    "of",
    "on",
    "the",
    "to",
    "use",
    "what",
    "with",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _request_payload(input_data: Mapping[str, Any]) -> JsonObject:
    """Reduced copy of the original normalized Data Consultant request."""

    list_fields = (
        "asset_classes",
        "regions",
        "data_types",
        "fields",
        "result_formats",
    )
    request: JsonObject = {
        "query": _text(input_data.get("query")),
        "use_case": _text(input_data.get("use_case")),
        "preferences": copy.deepcopy(dict(input_data.get("preferences") or {}))
        if isinstance(input_data.get("preferences"), Mapping)
        else {},
        "asset_class": _text(input_data.get("asset_class")),
        "region": _text(input_data.get("region")),
        "data_type": _text(input_data.get("data_type")),
        "time": copy.deepcopy(dict(input_data.get("time") or {}))
        if isinstance(input_data.get("time"), Mapping)
        else {},
        "include_sample_data": input_data.get("include_sample_data") is not False,
        "advice_mode": _text(input_data.get("advice_mode") or "auto").lower()
        or "auto",
    }
    for name in list_fields:
        value = input_data.get(name)
        request[name] = (
            [str(item) for item in value if str(item).strip()]
            if isinstance(value, list)
            else []
        )
    return request


class DataConsultantPersona(RAGPersona):
    """Memory-first advisory Persona with Plaza source synchronization.

    Production-only scheduling, SQLite/embedding persistence, LLM routing,
    ratings, learning, and administrative APIs are intentionally omitted.
    """

    def __init__(
        self,
        config: Mapping[str, Any] | None = None,
        *,
        plaza: Plaza | None = None,
        name: str = "DataConsultant",
        auto_register: bool = False,
        **kwargs: Any,
    ) -> None:
        self._source_memory: dict[str, JsonObject] = {}
        self._source_targets: dict[str, Any] = {}
        self._source_memory_refreshed_at = ""
        self._source_memory_attempted_at = ""
        self._source_memory_errors: list[str] = []

        card = copy.deepcopy(dict(kwargs.pop("agent_card", {}) or {}))
        card.update(
            {
                "name": name,
                "description": (
                    "Data Consultant that synchronizes Data Source catalogs and "
                    "answers from that RAG memory."
                ),
                "pit_type": "Persona",
                "type": "Persona",
                "party": DATA_SOURCE_PARTY,
                "tags": ["attas", "data-agent", "data-consultant"],
            }
        )
        meta = copy.deepcopy(dict(card.get("meta") or {}))
        meta["data_agent_role"] = "consultant"
        meta["source_discovery"] = {
            "enabled": True,
            "provider": "plaza",
            "party": DATA_SOURCE_PARTY,
            "pit_type": DATA_SOURCE_PIT_TYPE,
            "pulse_name": DATA_AVAILABILITY_PULSE_NAME,
        }
        card["meta"] = meta

        runtime_config = copy.deepcopy(dict(config or {}))
        runtime_config["persona"] = {
            "name": name,
            "role": "data-consultant",
            "purpose": (
                "Ground source, endpoint, field, cost, quality, and connectivity "
                "advice in synchronized Data Source catalogs."
            ),
            "instructions": [
                "Discover Data Sources through Plaza.",
                "Synchronize with data_availability.",
                "Answer data_advice from RAG memory.",
                "Never fetch provider data for the Data User.",
            ],
        }

        super().__init__(
            config=runtime_config,
            name=name,
            plaza_url=plaza,
            agent_card=card,
            supported_pulses=[
                copy.deepcopy(DATA_ADVICE_PULSE),
                copy.deepcopy(DATA_SOURCE_STATUS_PULSE),
            ],
            auto_register=auto_register,
            **kwargs,
        )

    def discover_sources(self, *, force_discovery: bool = False) -> tuple[JsonObject, ...]:
        """Search Plaza for PIT=DataSource, Party=attas as in FinMAS."""

        del force_discovery  # in-memory Plaza search has no discovery cache
        entries = self.search(
            pit_type=DATA_SOURCE_PIT_TYPE,
            party=DATA_SOURCE_PARTY,
            pulse_name=DATA_AVAILABILITY_PULSE_NAME,
        )
        definitions: list[JsonObject] = []
        seen: set[str] = set()
        for entry in entries:
            normalized = self._normalize_discovered_source(entry)
            source_id = _text(normalized.get("source_id")).lower()
            if not source_id or source_id in seen:
                continue
            seen.add(source_id)
            definitions.append(normalized)

        return tuple(definitions)

    def query_source(
        self,
        source: Mapping[str, Any],
        request: Mapping[str, Any],
    ) -> JsonObject:
        source_id = _text(source.get("source_id") or source.get("name"))
        target = source.get("target") or source.get("pit_address") or source.get("address")
        if not target:
            raise RuntimeError(f"No Plaza route is available for Data Source {source_id}.")
        return self._use_pulse(
            target,
            DATA_AVAILABILITY_PULSE_NAME,
            request,
        )

    def query_sources(
        self,
        sources: Sequence[Mapping[str, Any]],
        request: Mapping[str, Any],
    ) -> tuple[JsonObject, ...]:
        results: list[JsonObject] = []
        for source in sources:
            try:
                results.append(self.query_source(source, request))
            except Exception as exc:
                source_id = _text(source.get("source_id") or source.get("name"))
                results.append(
                    {
                        "source": {
                            "source_id": source_id,
                            "source_name": _text(source.get("source_name") or source_id),
                            "provider": _text(source.get("provider") or source_id),
                            "description": _text(source.get("description")),
                            "connectivity": {
                                "status": "unavailable",
                                "transport": "plaza",
                                "pulse_name": DATA_AVAILABILITY_PULSE_NAME,
                            },
                        },
                        "available": False,
                        "datasets": [],
                        "fields": [],
                        "count": 0,
                        "warnings": [str(exc)],
                        "error": str(exc),
                    }
                )
        return tuple(results)

    def refresh_source_memory(self, *, reason: str = "manual") -> JsonObject:
        """Synchronize the reduced RAG memory through ``data_availability``.

        The empty query is copied from FinMAS: it means complete catalog
        synchronization, not a special newly invented Pulse or workflow.
        """

        started_at = _utc_now()
        self._source_memory_attempted_at = started_at
        definitions = self.discover_sources(force_discovery=True)
        refresh_request = {
            "query": "",
            "use_case": "consultant memory synchronization",
            "preferences": {},
            "asset_class": "",
            "fields": [],
            "limit": 100,
        }
        responses = self.query_sources(definitions, refresh_request)
        memory: dict[str, JsonObject] = {}
        targets: dict[str, Any] = {}
        errors: list[str] = []
        for definition, response in zip(definitions, responses):
            normalized = self._normalize_source_response(definition, response)
            source_id = _text(normalized.get("source_id")).lower()
            if normalized.get("error") or not normalized.get("datasets"):
                detail = _text(normalized.get("error")) or (
                    "The source returned no catalog datasets."
                )
                errors.append(f"{source_id or 'data-source'}: {detail}")
                continue
            memory[source_id] = normalized
            targets[source_id] = (
                definition.get("target")
                or definition.get("pit_address")
                or definition.get("address")
            )
        self._source_memory = memory
        self._source_targets = targets
        self._source_memory_refreshed_at = _utc_now() if memory else ""
        self._source_memory_errors = errors
        status = self.source_memory_status()
        status["reason"] = reason
        return status

    def source_memory_status(self) -> JsonObject:
        dataset_count = sum(
            len(source.get("datasets") or []) for source in self._source_memory.values()
        )
        field_count = sum(
            len(source.get("fields") or []) for source in self._source_memory.values()
        )
        return {
            "mode": "rag_memory",
            "status": (
                "partial"
                if self._source_memory and self._source_memory_errors
                else "ready"
                if self._source_memory
                else "error"
                if self._source_memory_errors
                else "empty"
            ),
            "enabled": True,
            "refreshing": False,
            "source_count": len(self._source_memory),
            "dataset_count": dataset_count,
            "field_count": field_count,
            "chunk_count": dataset_count,
            "refreshed_at": self._source_memory_refreshed_at,
            "last_refresh_started_at": self._source_memory_attempted_at,
            "errors": list(self._source_memory_errors),
        }

    def search_source_memory(
        self,
        request: Mapping[str, Any],
        definitions: Sequence[Mapping[str, Any]] = (),
        learning: Mapping[str, Any] | None = None,
    ) -> tuple[list[JsonObject], JsonObject]:
        del definitions, learning
        started = time.perf_counter()
        query_tokens = _tokens(
            " ".join(
                [
                    _text(request.get("query")),
                    *[str(item) for item in request.get("fields") or []],
                    *[str(item) for item in request.get("data_types") or []],
                ]
            )
        )
        sources: list[JsonObject] = []
        for source in self._source_memory.values():
            matches: list[tuple[int, int, JsonObject]] = []
            for index, dataset in enumerate(source.get("datasets") or []):
                if not isinstance(dataset, Mapping):
                    continue
                document_tokens = _tokens(_dataset_text(dataset))
                overlap = query_tokens & document_tokens
                if not overlap:
                    continue
                score = len(overlap)
                matches.append((score, -index, copy.deepcopy(dict(dataset))))
            matches.sort(key=lambda item: (item[0], item[1]), reverse=True)
            datasets = [item[2] for item in matches[:5]]
            if not datasets:
                continue
            fields = [
                copy.deepcopy(dict(field))
                for dataset in datasets
                for field in dataset.get("fields") or []
                if isinstance(field, Mapping)
            ]
            value = copy.deepcopy(dict(source))
            value["datasets"] = datasets
            value["fields"] = fields
            value["count"] = len(datasets)
            value["endpoint_count"] = len(datasets)
            value["field_count"] = len(fields)
            value["available"] = bool(datasets)
            sources.append(value)

        memory = self.source_memory_status()
        memory.update(
            {
                "hit": bool(sources),
                "search_ms": round((time.perf_counter() - started) * 1000, 3),
                "matched_source_count": len(sources),
                "matched_dataset_count": sum(
                    len(source.get("datasets") or []) for source in sources
                ),
            }
        )
        return sources, memory

    def data_advice(self, input_data: Mapping[str, Any]) -> JsonObject:
        """Search synchronized catalog memory and return grounded advice."""

        started = time.perf_counter()
        request = _request_payload(input_data)
        sources, memory = self.search_source_memory(request)
        answer = self._fallback_answer(request, sources)
        total_ms = round((time.perf_counter() - started) * 1000, 1)
        warnings = list(self._source_memory_errors)
        if not sources:
            warnings.append("No synchronized Data Source endpoint matched the request.")
        return {
            "request": request,
            "answer": answer,
            "sources": sources,
            "source_count": len(sources),
            "result_formats": ["endpoint", "field"] if sources else [],
            "field_comparisons": [],
            "comparison_sets": [],
            "llm": {
                "used": False,
                "attempted": False,
                "fallback_used": True,
                "pulse_name": "llm_chat",
                "error": "",
            },
            "synthesis": {
                "tier": "rag_instant" if sources else "evidence_gap",
                "llm_required": False,
                "reason": (
                    "Synchronized endpoint evidence matched the request."
                    if sources
                    else "No synchronized endpoint evidence matched the request."
                ),
            },
            "timing": {
                "total_ms": total_ms,
                "llm_ms": 0.0,
                "memory_search_ms": memory["search_ms"],
                "evidence_and_orchestration_ms": total_ms,
                "llm_chat_calls": 0,
            },
            "memory": memory,
            "as_of": self._source_memory_refreshed_at or _utc_now(),
            "warnings": list(dict.fromkeys(warnings)),
        }

    def data_source_status(
        self,
        _input_data: Mapping[str, Any] | None = None,
    ) -> JsonObject:
        memory = self.source_memory_status()
        definitions = self.discover_sources()
        definition_by_id = {
            _text(item.get("source_id")).lower(): item for item in definitions
        }
        sources: list[JsonObject] = []
        for source_id, source in self._source_memory.items():
            definition = definition_by_id.get(source_id, {})
            registered = bool(definition)
            public_source = source.get("source") if isinstance(source.get("source"), Mapping) else {}
            connectivity = copy.deepcopy(dict(public_source.get("connectivity") or {}))
            connectivity.update(
                {
                    "status": "ready" if registered else "unavailable",
                    "address": (
                        _target_ref(
                            definition.get("target")
                            or definition.get("pit_address")
                            or definition.get("address")
                        )
                        if registered
                        else ""
                    ),
                    "practice_id": "get_pulse_data",
                    "pulse_name": DATA_AVAILABILITY_PULSE_NAME,
                }
            )
            sources.append(
                {
                    "source_id": source_id,
                    "source_name": _text(public_source.get("source_name") or source_id),
                    "provider": _text(public_source.get("provider") or source_id),
                    "available": registered and bool(source.get("available")),
                    "connectivity": connectivity,
                    "dataset_count": len(source.get("datasets") or []),
                    "last_update_at": self._source_memory_refreshed_at,
                    "last_update_attempt_at": self._source_memory_attempted_at,
                    "last_update_status": "ready" if registered else "unavailable",
                    "last_update_error": not registered,
                    "error": "" if registered else "Source is not registered in Plaza.",
                    "stale": not registered,
                    "included": True,
                    "consultant_rating": 0,
                    "user_rating": 0,
                    "user_rating_average": 0.0,
                    "user_rating_count": 0,
                    "effective_rating": 0.0,
                }
            )
        discovery = {
            "enabled": True,
            "provider": "plaza",
            "status": "ready" if definitions else "empty",
            "plaza_url": str(self.plaza_url or ""),
            "party": DATA_SOURCE_PARTY,
            "pit_type": DATA_SOURCE_PIT_TYPE,
            "pulse_name": DATA_AVAILABILITY_PULSE_NAME,
            "required_tags": [],
            "require_data_source_profile": True,
            "require_trusted": False,
            "include_configured": False,
            "configured_source_count": 0,
            "candidate_count": len(definitions),
            "discovered_source_count": len(definitions),
            "source_ids": sorted(definition_by_id),
            "last_attempt_at": self._source_memory_attempted_at,
            "last_success_at": self._source_memory_refreshed_at,
            "cache_age_seconds": 0.0,
            "error": "",
        }
        return {
            "status": memory["status"],
            "enabled": True,
            "refreshing": False,
            "latest_update_at": self._source_memory_refreshed_at,
            "latest_update_attempt_at": self._source_memory_attempted_at,
            "last_update_error": bool(self._source_memory_errors),
            "next_update_at": "",
            "refresh_interval_sec": 0,
            "source_count": len(sources),
            "dataset_count": memory["dataset_count"],
            "sources": sources,
            "discovery": discovery,
            "errors": list(self._source_memory_errors),
            "as_of": _utc_now(),
        }

    def fetch_pulse_payload(
        self,
        pulse_name: str,
        input_data: JsonObject,
        pulse_definition: JsonObject,
    ) -> JsonObject:
        if pulse_name == DATA_ADVICE_PULSE_NAME:
            return self.data_advice(input_data or {})
        if pulse_name == DATA_SOURCE_STATUS_PULSE_NAME:
            return self.data_source_status(input_data or {})
        return super().fetch_pulse_payload(pulse_name, input_data or {}, pulse_definition)

    def _normalize_discovered_source(self, entry: Any) -> JsonObject:
        value = dict(entry) if isinstance(entry, Mapping) else {}
        card = dict(value.get("card") or {}) if isinstance(value.get("card"), Mapping) else {}
        meta = dict(card.get("meta") or {}) if isinstance(card.get("meta"), Mapping) else {}
        profile = (
            dict(meta.get("data_source") or {})
            if isinstance(meta.get("data_source"), Mapping)
            else {}
        )
        source_id = _text(profile.get("source_id") or meta.get("source_id")).lower()
        target = (
            value.get("pit_address")
            or card.get("pit_address")
            or card.get("address")
            or value.get("address")
        )
        connectivity = copy.deepcopy(dict(profile.get("connectivity") or {}))
        connectivity.update(
            {
                "address": _target_ref(target),
                "practice_id": "get_pulse_data",
                "pulse_name": DATA_AVAILABILITY_PULSE_NAME,
            }
        )
        return {
            "source_id": source_id,
            "source_name": _text(profile.get("source_name") or card.get("name") or source_id),
            "provider": _text(profile.get("provider") or source_id),
            "description": _text(profile.get("description") or card.get("description")),
            "address": _target_ref(target),
            "pit_address": target,
            "target": target,
            "practice_id": "get_pulse_data",
            "pulse_name": DATA_AVAILABILITY_PULSE_NAME,
            "connectivity": connectivity,
            "party": _text(card.get("party") or value.get("party")),
            "pit_type": _text(card.get("pit_type") or value.get("pit_type")),
        }

    @staticmethod
    def _normalize_source_response(
        definition: Mapping[str, Any],
        response: Any,
    ) -> JsonObject:
        payload = dict(response) if isinstance(response, Mapping) else {}
        if isinstance(payload.get("result"), Mapping) and not payload.get("datasets"):
            payload = dict(payload["result"])
        source = (
            copy.deepcopy(dict(payload.get("source") or {}))
            if isinstance(payload.get("source"), Mapping)
            else {}
        )
        source_id = _text(
            source.get("source_id")
            or definition.get("source_id")
            or definition.get("name")
        ).lower()
        source.setdefault("source_id", source_id)
        source.setdefault("source_name", _text(definition.get("source_name") or source_id))
        source.setdefault("provider", _text(definition.get("provider") or source_id))
        source.setdefault("description", _text(definition.get("description")))
        datasets = [
            copy.deepcopy(dict(item))
            for item in payload.get("datasets") or []
            if isinstance(item, Mapping)
        ]
        fields = [
            copy.deepcopy(dict(item))
            for item in payload.get("fields") or []
            if isinstance(item, Mapping)
        ]
        return {
            "source_id": source_id,
            "source_name": source["source_name"],
            "provider": source["provider"],
            "description": source["description"],
            "source": source,
            "available": bool(payload.get("available")) and bool(datasets or fields),
            "connectivity": copy.deepcopy(dict(source.get("connectivity") or {})),
            "datasets": datasets,
            "fields": fields,
            "field_count": len(fields),
            "endpoint_count": len(datasets),
            "result_formats": copy.deepcopy(list(payload.get("result_formats") or [])),
            "result_sets": copy.deepcopy(list(payload.get("result_sets") or [])),
            "count": len(datasets),
            "match_reason": _text(payload.get("match_reason")),
            "warnings": [str(item) for item in payload.get("warnings") or []],
            "error": _text(payload.get("error")),
        }

    @staticmethod
    def _fallback_answer(
        request: Mapping[str, Any],
        sources: Sequence[Mapping[str, Any]],
    ) -> str:
        available = [source for source in sources if source.get("available")]
        if not available:
            return (
                "I could not confirm an available source for: "
                f"{request.get('query') or 'the requested data'}. Check source "
                "connectivity and catalog coverage."
            )
        dataset_names = [
            _text(dataset.get("name") or dataset.get("dataset_id"))
            for source in available
            for dataset in source.get("datasets") or []
            if isinstance(dataset, Mapping)
        ]
        source_names = [
            _text(source.get("source_name") or source.get("source_id"))
            for source in available
        ]
        return (
            f"For {request.get('query') or 'this request'}, I found "
            f"{len(dataset_names)} matching dataset(s) from {', '.join(source_names)}: "
            f"{', '.join(dataset_names[:5])}. Review each source's connectivity, "
            "schema, cost, and sample data before selecting it. The Data User "
            "connects to the selected source directly."
        )

    def _use_pulse(
        self,
        target: Any,
        pulse_name: str,
        params: Mapping[str, Any],
    ) -> JsonObject:
        result = self.UsePractice(
            "get_pulse_data",
            {
                "pulse_name": pulse_name,
                "params": copy.deepcopy(dict(params)),
            },
            pit_address=target,
            timeout=240,
        )
        return dict(result) if isinstance(result, Mapping) else {}


class DataUserPersona(RAGPersona):
    """Data User that delegates advice and calls selected sources directly."""

    def __init__(
        self,
        config: Mapping[str, Any] | None = None,
        *,
        consultant: Mapping[str, Any] | None = None,
        plaza: Plaza | None = None,
        name: str = "DataUser",
        auto_register: bool = False,
        **kwargs: Any,
    ) -> None:
        self.consultant = copy.deepcopy(dict(consultant or {}))

        card = copy.deepcopy(dict(kwargs.pop("agent_card", {}) or {}))
        card.update(
            {
                "name": name,
                "description": (
                    "Data User that submits natural-language requests to a Data "
                    "Consultant and selected endpoints directly to Data Sources."
                ),
                "pit_type": "Persona",
                "type": "Persona",
                "party": DATA_SOURCE_PARTY,
                "tags": ["attas", "data-agent", "data-user"],
            }
        )
        meta = copy.deepcopy(dict(card.get("meta") or {}))
        meta["data_agent_role"] = "user"
        meta["source_catalog"] = {
            "authority": "data_consultant",
            "pulse_name": DATA_SOURCE_STATUS_PULSE_NAME,
            "registry": "plaza",
            "party": DATA_SOURCE_PARTY,
            "pit_type": DATA_SOURCE_PIT_TYPE,
        }
        card["meta"] = meta

        runtime_config = copy.deepcopy(dict(config or {}))
        runtime_config["persona"] = {
            "name": name,
            "role": "data-user",
            "purpose": "Preserve user intent while using specialist network roles.",
            "instructions": [
                "Send data_request to the Data Consultant.",
                "Use data_source_status to resolve a selected source.",
                "Call data_spec and data_fetch on that Data Source directly.",
                "Never route provider data through the Data Consultant.",
            ],
        }

        super().__init__(
            config=runtime_config,
            name=name,
            plaza_url=plaza,
            agent_card=card,
            supported_pulses=[
                copy.deepcopy(DATA_REQUEST_PULSE),
                copy.deepcopy(DATA_SOURCE_STATUS_PULSE),
                copy.deepcopy(DATA_SPEC_PULSE),
                copy.deepcopy(DATA_FETCH_PULSE),
            ],
            auto_register=auto_register,
            **kwargs,
        )

    def request_data_advice(self, input_data: Mapping[str, Any]) -> JsonObject:
        target = self._consultant_target()
        if target is None:
            request = _request_payload(input_data)
            return {
                "request": request,
                "answer": "No Data Consultant is configured for this Data User.",
                "sources": [],
                "source_count": 0,
                "result_formats": [],
                "field_comparisons": [],
                "comparison_sets": [],
                "llm": {
                    "used": False,
                    "attempted": False,
                    "fallback_used": True,
                    "pulse_name": "llm_chat",
                    "error": "No consultant configured.",
                },
                "synthesis": {"tier": "evidence_gap", "llm_required": False},
                "timing": {
                    "total_ms": 0.0,
                    "llm_ms": 0.0,
                    "memory_search_ms": 0.0,
                    "evidence_and_orchestration_ms": 0.0,
                    "llm_chat_calls": 0,
                },
                "memory": {"mode": "rag_memory", "status": "unavailable", "hit": False},
                "as_of": _utc_now(),
                "warnings": ["No Data Consultant is registered in Plaza."],
            }
        return self._use_pulse(target, DATA_ADVICE_PULSE_NAME, input_data)

    def request_consultant_pulse(
        self,
        pulse_name: str,
        input_data: Mapping[str, Any],
    ) -> JsonObject:
        target = self._consultant_target()
        if target is None:
            return {}
        return self._use_pulse(target, pulse_name, input_data)

    def current_data_source_status(self) -> JsonObject:
        try:
            payload = self.request_consultant_pulse(DATA_SOURCE_STATUS_PULSE_NAME, {})
        except Exception as exc:
            return {"status": "error", "sources": [], "errors": [str(exc)]}
        if isinstance(payload.get("result"), Mapping) and not isinstance(
            payload.get("sources"), list
        ):
            payload = dict(payload["result"])
        if not isinstance(payload.get("sources"), list):
            payload["sources"] = []
        return payload

    def registered_data_sources(
        self,
        status: Mapping[str, Any] | None = None,
    ) -> list[JsonObject]:
        current = dict(status) if isinstance(status, Mapping) else self.current_data_source_status()
        result: list[JsonObject] = []
        for item in current.get("sources") or []:
            if not isinstance(item, Mapping):
                continue
            source_id = _text(item.get("source_id") or item.get("name")).lower()
            if not source_id:
                continue
            value = copy.deepcopy(dict(item))
            value["source_id"] = source_id
            result.append(value)
        return sorted(result, key=lambda item: str(item["source_id"]))

    def resolve_data_source(
        self,
        input_data: Mapping[str, Any],
        *,
        pulse_name: str,
    ) -> tuple[str, Any, JsonObject]:
        """Resolve a source exclusively from Consultant-owned status."""

        source_id = _text(
            input_data.get("source_id") or input_data.get("source")
        ).lower()
        if not source_id:
            return "", None, {}
        definition = next(
            (
                item
                for item in self.registered_data_sources()
                if _text(item.get("source_id")).lower() == source_id
            ),
            None,
        )
        if not definition or not definition.get("available"):
            return source_id, None, {}
        connectivity = (
            dict(definition.get("connectivity") or {})
            if isinstance(definition.get("connectivity"), Mapping)
            else {}
        )
        target = connectivity.get("address")
        if not target:
            return source_id, None, {}
        return (
            source_id,
            None,
            {
                "address": target,
                "practice_id": "get_pulse_data",
                "pulse_name": pulse_name,
            },
        )

    def request_spec(self, input_data: Mapping[str, Any]) -> JsonObject:
        source_id, _, target = self.resolve_data_source(
            input_data,
            pulse_name=DATA_SPEC_PULSE_NAME,
        )
        params = {
            key: copy.deepcopy(value)
            for key, value in input_data.items()
            if key not in {"source_id", "source"}
        }
        if not target:
            return {
                "query": _text(input_data.get("query")),
                "endpoint_id": _text(input_data.get("endpoint_id")),
                "source": {"source_id": source_id, "source_name": source_id},
                "endpoints": [],
                "count": 0,
                "snapshot": {"status": "missing"},
                "warnings": [
                    "The source is not present in the Data Consultant's current "
                    "Plaza-backed catalog."
                ],
            }
        return self._use_pulse(target["address"], DATA_SPEC_PULSE_NAME, params)

    def request_data_fetch(self, input_data: Mapping[str, Any]) -> JsonObject:
        source_id = _text(
            input_data.get("source_id") or input_data.get("source")
        ).lower()
        endpoint_id = _text(
            input_data.get("endpoint_id") or input_data.get("dataset_id")
        )
        if not source_id:
            return _fetch_failure("", endpoint_id, "source_id is required.")
        secret_names = {"token", "api_key", "apikey", "api-key", "secret", "password"}
        parameters = (
            input_data.get("parameters")
            if isinstance(input_data.get("parameters"), Mapping)
            else {}
        )
        if any(_text(name).lower() in secret_names for name in (*input_data, *parameters)):
            return _fetch_failure(
                source_id,
                endpoint_id,
                "Raw API credentials are not accepted in data_fetch pulses.",
            )
        if _text(input_data.get("access_mode") or ACCESS_MODE_PULSE) != ACCESS_MODE_PULSE:
            return _fetch_failure(source_id, endpoint_id, "Unsupported data access mode.")

        source_id, _, target = self.resolve_data_source(
            input_data,
            pulse_name=DATA_FETCH_PULSE_NAME,
        )
        params = copy.deepcopy(dict(input_data))
        params.pop("source_id", None)
        params.pop("source", None)
        params["access_mode"] = ACCESS_MODE_PULSE
        if not target:
            return _fetch_failure(
                source_id,
                endpoint_id,
                "No registered Data Source is available for this request.",
            )
        return self._use_pulse(target["address"], DATA_FETCH_PULSE_NAME, params)

    def request_advice(self, input_data: Mapping[str, Any]) -> JsonObject:
        return self.request_data_advice(input_data)

    def fetch_data(self, input_data: Mapping[str, Any]) -> JsonObject:
        return self.request_data_fetch(input_data)

    def data_request(self, input_data: Mapping[str, Any]) -> JsonObject:
        return self.request_advice(input_data)

    def fetch_pulse_payload(
        self,
        pulse_name: str,
        input_data: JsonObject,
        pulse_definition: JsonObject,
    ) -> JsonObject:
        if pulse_name == DATA_REQUEST_PULSE_NAME:
            return self.data_request(input_data or {})
        if pulse_name == DATA_SPEC_PULSE_NAME:
            return self.request_spec(input_data or {})
        if pulse_name == DATA_FETCH_PULSE_NAME:
            return self.fetch_data(input_data or {})
        if pulse_name == DATA_SOURCE_STATUS_PULSE_NAME:
            return self.request_consultant_pulse(pulse_name, input_data or {})
        return super().fetch_pulse_payload(pulse_name, input_data or {}, pulse_definition)

    def _consultant_target(self) -> Any:
        if self.consultant:
            return self.consultant.get("target") or self.consultant.get("address")
        entries = self.search(pit_type="Persona", party=DATA_SOURCE_PARTY)
        for entry in entries:
            value = dict(entry) if isinstance(entry, Mapping) else {}
            card = dict(value.get("card") or {}) if isinstance(value.get("card"), Mapping) else {}
            meta = dict(card.get("meta") or {}) if isinstance(card.get("meta"), Mapping) else {}
            if _text(meta.get("data_agent_role")) != "consultant":
                continue
            return (
                value.get("pit_address")
                or card.get("pit_address")
                or card.get("address")
                or value.get("address")
            )
        return None

    def _use_pulse(
        self,
        target: Any,
        pulse_name: str,
        params: Mapping[str, Any],
    ) -> JsonObject:
        result = self.UsePractice(
            "get_pulse_data",
            {
                "pulse_name": pulse_name,
                "params": copy.deepcopy(dict(params)),
            },
            pit_address=target,
            timeout=240,
        )
        return dict(result) if isinstance(result, Mapping) else {}


def _tokens(value: str) -> set[str]:
    return set(_TOKEN_RE.findall(value.lower())) - _STOP_WORDS


def _dataset_text(dataset: Mapping[str, Any]) -> str:
    fields = " ".join(
        " ".join(
            (
                _text(field.get("name")),
                _text(field.get("canonical_name")),
                _text(field.get("description")),
            )
        )
        for field in dataset.get("fields") or []
        if isinstance(field, Mapping)
    )
    return " ".join(
        (
            _text(dataset.get("dataset_id")),
            _text(dataset.get("endpoint_id")),
            _text(dataset.get("name")),
            _text(dataset.get("description")),
            _text(dataset.get("operation")),
            " ".join(str(item) for item in dataset.get("tags") or []),
            fields,
        )
    )


def _target_ref(target: Any) -> str:
    if target is None:
        return ""
    if isinstance(target, str):
        return target
    address = getattr(target, "pit_address", target)
    if hasattr(address, "to_ref"):
        try:
            return str(address.to_ref())
        except TypeError:
            return str(address.to_ref(reference_plaza=None))
    if isinstance(target, Mapping):
        return _text(target.get("address") or target.get("pit_id"))
    return str(target)


def _fetch_failure(source_id: str, dataset_id: str, error: str) -> JsonObject:
    return {
        "status": "failed",
        "source": {"source_id": source_id, "source_name": source_id},
        "dataset_id": dataset_id,
        "backend_id": source_id,
        "data": {},
        "canonical_data": {},
        "data_schema": {},
        "canonical_data_schema": {},
        "fields": [],
        "field_mappings": [],
        "attas_pulse": {
            "contract_version": "attas.data_fetch.v1",
            "pulse_name": DATA_FETCH_PULSE_NAME,
            "pulse_address": "plaza://pulse/attas/data_fetch",
            "endpoint_id": dataset_id,
            "request": {"dataset_id": dataset_id, "fields": []},
            "response": {
                "provider_container": "data",
                "canonical_container": "canonical_data",
                "field_mappings": [],
            },
        },
        "cost": {},
        "warnings": [
            "The source is not present in the Data Consultant's current Plaza-backed catalog."
        ],
        "error": error,
        "access_mode": ACCESS_MODE_PULSE,
    }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# Compatibility aliases retained by the original public package.
DataConsultant = DataConsultantPersona
DataUser = DataUserPersona


__all__ = [
    "DataConsultant",
    "DataConsultantPersona",
    "DataUser",
    "DataUserPersona",
]
