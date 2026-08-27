"""Reduced copy of Phemacast's Pulser and get-pulse Practice."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Union

from prompits_lite import Message, Practice, StandbyAgent

from .pulse_runtime import normalize_runtime_pulse_entry


ConfigInput = Union[str, Path, Mapping[str, Any]]


def _read_config(config: ConfigInput) -> Dict[str, Any]:
    if isinstance(config, Mapping):
        return dict(config)
    with Path(config).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _resolve_path(data: Any, path: str) -> Any:
    current = data
    for part in str(path or "").split("."):
        if not part:
            continue
        if isinstance(current, Mapping) and part in current:
            current = current[part]
            continue
        if isinstance(current, list) and part.isdigit() and int(part) < len(current):
            current = current[int(part)]
            continue
        return None
    return current


def _assign_path(data: Dict[str, Any], path: str, value: Any) -> None:
    current = data
    parts = path.split(".")
    for part in parts[:-1]:
        node = current.get(part)
        if not isinstance(node, dict):
            node = {}
            current[part] = node
        current = node
    current[parts[-1]] = value


class PulsePractice:
    """Original local provider registry retained for simple pulse fetches."""

    def __init__(self) -> None:
        self.providers: Dict[str, Callable[[Optional[Dict[str, Any]]], Any]] = {}

    def register_provider(
        self,
        key: str,
        provider: Callable[[Optional[Dict[str, Any]]], Any],
    ) -> None:
        self.providers[key] = provider

    def fetch(
        self,
        keys: Iterable[str],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        payload: Dict[str, Dict[str, Any]] = {}
        for key in keys:
            provider = self.providers.get(key)
            if provider is None:
                payload[key] = {"value": None}
                continue
            result = provider(context or {})
            payload[key] = result if isinstance(result, dict) else {"value": result}
        return payload


class GetPulseDataPractice(Practice):
    """Expose ``agent.get_pulse_data()`` as a callable Practice."""

    def __init__(self) -> None:
        super().__init__(
            name="Get Pulse Data",
            description="Fetch or transform pulse payloads for the agent's supported pulses.",
            id="get_pulse_data",
            tags=["pulser", "pulse", "data"],
            examples=[],
            inputModes=["http-post", "json"],
            outputModes=["json"],
            parameters={},
        )

    def bind(self, agent: Any) -> None:
        super().bind(agent)
        supported_pulses = getattr(agent, "supported_pulses", [])
        self.parameters = {
            "pulse_name": {
                "type": "string",
                "description": "Optional pulse identifier.",
                "enum": [
                    pulse.get("name")
                    for pulse in supported_pulses
                    if isinstance(pulse, Mapping) and pulse.get("name")
                ],
            },
            "pulse_address": {"type": "string"},
            "params": getattr(agent, "input_schema", {}) or {"type": "object"},
        }

    def mount(self, app: Any) -> None:
        del app

    def execute(self, **kwargs: Any) -> Any:
        if self.agent is None:
            raise RuntimeError("GetPulseDataPractice is not bound to an agent.")
        input_data = kwargs.get("input_data")
        if input_data is None:
            input_data = kwargs.get("params")
        if input_data is None:
            input_data = {
                key: value
                for key, value in kwargs.items()
                if key not in {"pulse_name", "pulse_address", "output_schema"}
            }
        return self.agent.get_pulse_data(
            input_data=input_data or {},
            pulse_name=kwargs.get("pulse_name"),
            pulse_address=kwargs.get("pulse_address"),
            output_schema=kwargs.get("output_schema"),
        )


class Pulser(StandbyAgent):
    """StandbyAgent specialized for pulse payload delivery."""

    def __init__(
        self,
        config: Optional[ConfigInput] = None,
        *,
        config_path: Optional[ConfigInput] = None,
        name: str = "Pulser",
        host: str = "127.0.0.1",
        port: int = 8000,
        plaza_url: Any = None,
        agent_card: Optional[Dict[str, Any]] = None,
        pool: Any = None,
        pulse_name: Optional[str] = None,
        pulse_address: Optional[str] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        mapping: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        supported_pulses: Optional[List[Dict[str, Any]]] = None,
        auto_register: bool = True,
    ) -> None:
        config_data = _read_config(config) if config is not None else {}
        resolved_config_path = config_path
        if resolved_config_path is None and isinstance(config, (str, Path)):
            resolved_config_path = config
        self.config_path = Path(resolved_config_path).resolve() if resolved_config_path else None
        self.raw_config = dict(config_data)
        pulser_config = config_data.get("pulser", config_data)
        pulse_definitions = self._build_supported_pulses(
            config=dict(pulser_config),
            pulse_name=pulse_name,
            pulse_address=pulse_address,
            input_schema=input_schema,
            mapping=mapping,
            output_schema=output_schema,
            supported_pulses=supported_pulses,
        )
        card = copy.deepcopy(dict(agent_card or pulser_config.get("agent_card") or {}))
        card.setdefault("name", name)
        card.setdefault("role", "pulser")
        card.setdefault("pit_type", "Pulser")
        super().__init__(name, host, port, plaza_url, card, pool=pool)
        self.apply_pulser_config(
            config_data or dict(pulser_config),
            supported_pulses=pulse_definitions,
            pulse_name=pulse_name,
            pulse_address=pulse_address,
            input_schema=input_schema,
            mapping=mapping,
            output_schema=output_schema,
            agent_card_overrides=card,
        )
        self.add_practice(GetPulseDataPractice())
        if self.plaza_url and auto_register:
            self.register()

    @classmethod
    def from_config(cls, config: ConfigInput, **kwargs: Any) -> "Pulser":
        return cls(config=config, **kwargs)

    @staticmethod
    def _merge_tags(*tag_groups: Any) -> List[str]:
        merged: List[str] = []
        for group in tag_groups:
            for tag in group or []:
                text = str(tag)
                if text not in merged:
                    merged.append(text)
        return merged

    def _normalize_pulse_definition(self, pulse: Mapping[str, Any]) -> Dict[str, Any]:
        normalized = normalize_runtime_pulse_entry(
            pulse,
            default_name=str(pulse.get("name") or "default_pulse"),
            default_description=str(pulse.get("description") or ""),
            default_pulse_address=pulse.get("pulse_address"),
        )
        normalized["input_schema"] = dict(normalized.get("input_schema") or {})
        normalized["mapping"] = dict(normalized.get("mapping") or {})
        normalized["output_schema"] = dict(normalized.get("output_schema") or {})
        normalized["tags"] = list(normalized.get("tags") or [])
        return normalized

    def _build_supported_pulses(
        self,
        *,
        config: Dict[str, Any],
        pulse_name: Optional[str],
        pulse_address: Optional[str],
        input_schema: Optional[Dict[str, Any]],
        mapping: Optional[Dict[str, Any]],
        output_schema: Optional[Dict[str, Any]],
        supported_pulses: Optional[List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        raw_pulses = supported_pulses or config.get("supported_pulses")
        if raw_pulses:
            return [
                self._normalize_pulse_definition(item)
                for item in raw_pulses
                if isinstance(item, Mapping)
            ]
        return [
            self._normalize_pulse_definition(
                {
                    "name": pulse_name or config.get("name") or "default_pulse",
                    "pulse_address": pulse_address or config.get("pulse_address"),
                    "input_schema": input_schema if input_schema is not None else config.get("input_schema", {}),
                    "mapping": mapping if mapping is not None else config.get("mapping", {}),
                    "output_schema": output_schema if output_schema is not None else config.get("output_schema", {}),
                    "description": config.get("description", ""),
                    "tags": config.get("tags", []),
                }
            )
        ]

    def apply_pulser_config(
        self,
        config_data: Dict[str, Any],
        *,
        supported_pulses: Optional[List[Dict[str, Any]]] = None,
        pulse_name: Optional[str] = None,
        pulse_address: Optional[str] = None,
        input_schema: Optional[Dict[str, Any]] = None,
        mapping: Optional[Dict[str, Any]] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        agent_card_overrides: Optional[Dict[str, Any]] = None,
    ) -> None:
        raw_config = dict(config_data or {})
        pulser_config = raw_config.get("pulser", raw_config)
        self.raw_config = raw_config
        self.config = dict(pulser_config)
        self.supported_pulses = self._build_supported_pulses(
            config=self.config,
            pulse_name=pulse_name,
            pulse_address=pulse_address,
            input_schema=input_schema,
            mapping=mapping,
            output_schema=output_schema,
            supported_pulses=supported_pulses,
        )
        primary = self.supported_pulses[0]
        self.pulse_address = primary.get("pulse_address")
        self.input_schema = dict(primary.get("input_schema") or {})
        self.mapping = dict(primary.get("mapping") or {})
        self.output_schema = dict(primary.get("output_schema") or {})

        card = copy.deepcopy(dict(self.agent_card or {}))
        if agent_card_overrides:
            card.update(copy.deepcopy(agent_card_overrides))
        resolved_name = raw_config.get("name") or self.config.get("name") or card.get("name") or self.name
        self.name = str(resolved_name)
        card["name"] = self.name
        card["role"] = raw_config.get("role") or self.config.get("role") or card.get("role") or "pulser"
        card["pit_type"] = "Pulser"
        card["description"] = str(
            self.config.get("description")
            or raw_config.get("description")
            or card.get("description")
            or "Provides pulse data and schema mapping."
        )
        card["tags"] = self._merge_tags(
            raw_config.get("tags"), self.config.get("tags"), card.get("tags"), ["pulser", "pulse"]
        )
        meta = dict(card.get("meta") or {})
        meta["pulse_address"] = self.pulse_address
        meta["input_schema"] = copy.deepcopy(self.input_schema)
        meta["supported_pulses"] = copy.deepcopy(self.supported_pulses)
        meta["pulse_id"] = primary.get("pulse_id")
        meta["pulse_definition"] = copy.deepcopy(primary.get("pulse_definition") or {})
        card["meta"] = meta
        self.agent_card = card
        self.description = card["description"]
        self.meta = meta
        self._refresh_get_pulse_practice_metadata()
        self._refresh_registration()

    def _refresh_get_pulse_practice_metadata(self) -> None:
        practice = next((item for item in self.practices if item.id == "get_pulse_data"), None)
        if practice is None:
            return
        practice.bind(self)
        self._upsert_practice_metadata_in_card(self._default_practice_metadata(practice))

    def resolve_pulse_definition(
        self,
        pulse_name: Optional[str] = None,
        pulse_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        if pulse_name:
            requested = str(pulse_name).strip()
            for pulse in self.supported_pulses:
                aliases = {str(item).strip() for item in (pulse.get("aliases") or [])}
                if requested in {
                    str(pulse.get("name") or ""),
                    str(pulse.get("pulse_name") or ""),
                    *aliases,
                }:
                    return pulse
        if pulse_address:
            for pulse in self.supported_pulses:
                if str(pulse.get("pulse_address") or "") == str(pulse_address):
                    return pulse
        return self.supported_pulses[0]

    def fetch_pulse_payload(
        self,
        pulse_name: str,
        input_data: Dict[str, Any],
        pulse_definition: Dict[str, Any],
    ) -> Dict[str, Any]:
        del pulse_name, pulse_definition
        return input_data

    def transform(
        self,
        input_data: Dict[str, Any],
        pulse_name: Optional[str] = None,
        pulse_address: Optional[str] = None,
        output_schema: Optional[Dict[str, Any]] = None,
        mapping: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        pulse = self.resolve_pulse_definition(pulse_name, pulse_address)
        schema = output_schema or pulse.get("output_schema") or self.output_schema or {}
        rules = mapping or pulse.get("mapping") or self.mapping or {}
        fields = list((schema.get("properties") or {}).keys())
        fields.extend(field for field in rules if field not in fields)
        transformed: Dict[str, Any] = {}
        for output_field in fields:
            rule = rules.get(output_field)
            if rule is None:
                continue
            if isinstance(rule, str):
                value = _resolve_path(input_data, rule)
            elif isinstance(rule, Mapping) and "value" in rule:
                value = rule["value"]
            elif isinstance(rule, Mapping):
                source = rule.get("source") or rule.get("from") or rule.get("path") or rule.get("input")
                value = _resolve_path(input_data, str(source)) if source else rule.get("default")
            else:
                value = rule
            if value is not None:
                _assign_path(transformed, output_field, value)
        return transformed

    def get_pulse_data(
        self,
        input_data: Dict[str, Any],
        pulse_name: Optional[str] = None,
        pulse_address: Optional[str] = None,
        output_schema: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        pulse = self.resolve_pulse_definition(pulse_name, pulse_address)
        active_name = str(pulse_name or pulse.get("name") or "default_pulse")
        raw_payload = self.fetch_pulse_payload(active_name, input_data, pulse) or {}
        if not isinstance(raw_payload, dict):
            raise TypeError("fetch_pulse_payload() must return a dict.")
        if raw_payload.get("error"):
            return raw_payload
        rules = pulse.get("mapping") or self.mapping
        if rules:
            return self.transform(
                raw_payload,
                pulse_name=active_name,
                pulse_address=pulse.get("pulse_address"),
                output_schema=output_schema or pulse.get("output_schema"),
                mapping=rules,
            )
        return raw_payload

    @property
    def status(self) -> str:
        count = len(getattr(self, "supported_pulses", []) or [])
        return f"Idle; ready to serve {count} pulse{'s' if count != 1 else ''}."

    def receive(self, message: Message) -> Any:
        if message.msg_type == "get_pulse":
            content = message.content or {}
            if not isinstance(content, dict):
                return {"error": "get_pulse content must be a JSON object"}
            return self.get_pulse_data(
                input_data=content.get("params", {}),
                pulse_name=content.get("pulse_name"),
                pulse_address=content.get("pulse_address"),
                output_schema=content.get("output_schema"),
            )
        return super().receive(message)


__all__ = [
    "ConfigInput",
    "GetPulseDataPractice",
    "PulsePractice",
    "Pulser",
    "_read_config",
]
