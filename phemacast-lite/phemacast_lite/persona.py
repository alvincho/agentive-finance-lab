"""Reduced copy of Phemacast's Pulser-backed Persona runtime."""

from __future__ import annotations

from abc import ABC
import copy
from typing import Any, Dict, List, Mapping, Optional

from .pulser import ConfigInput, Pulser, _read_config


def _conversation_pulse() -> Dict[str, Any]:
    return {
        "name": "conversation",
        "pulse_address": "plaza://pulse/conversation",
        "description": "Hold one conversation turn with the Persona.",
        "tags": ["persona", "conversation"],
        "input_schema": {
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
        "output_schema": {
            "type": "object",
            "properties": {"response": {"type": "string"}},
            "required": ["response"],
        },
    }


class Persona(Pulser, ABC):
    """Persona identity and profile layered directly on Pulser."""

    def __init__(
        self,
        config: Optional[ConfigInput] = None,
        *,
        config_path: Optional[ConfigInput] = None,
        name: Optional[str] = None,
        host: str = "127.0.0.1",
        port: int = 8000,
        plaza_url: Any = None,
        agent_card: Optional[Dict[str, Any]] = None,
        pool: Any = None,
        supported_pulses: Optional[List[Dict[str, Any]]] = None,
        enable_reaction: Optional[bool] = None,
        auto_register: bool = True,
    ) -> None:
        del enable_reaction
        config_input = config if config is not None else config_path
        config_data = _read_config(config_input) if config_input is not None else {}
        persona_config = (
            dict(config_data.get("persona") or {})
            if isinstance(config_data.get("persona"), Mapping)
            else {}
        )
        resolved_name = str(name or config_data.get("name") or persona_config.get("name") or "Persona")
        resolved_pulses = (
            [copy.deepcopy(dict(item)) for item in supported_pulses if isinstance(item, Mapping)]
            if supported_pulses is not None
            else [
                copy.deepcopy(dict(item))
                for item in (config_data.get("supported_pulses") or [_conversation_pulse()])
                if isinstance(item, Mapping)
            ]
        )
        card = copy.deepcopy(dict(agent_card or config_data.get("agent_card") or {}))
        card.setdefault("name", resolved_name)
        card.setdefault("role", "persona")
        card.setdefault("pit_type", "Persona")
        card.setdefault(
            "description",
            "Pulser-backed persona agent for conversation and domain pulses.",
        )
        card["tags"] = self._merge_tags(card.get("tags"), config_data.get("tags"), ["persona", "pulser", "rag"])

        # Register only after the Persona card replaces the intermediate Pulser
        # card. This produces the same public Plaza identity as the full runtime.
        super().__init__(
            config=config_input,
            config_path=config_path,
            name=resolved_name,
            host=host,
            port=port,
            plaza_url=plaza_url or config_data.get("plaza_url"),
            agent_card=card,
            pool=pool,
            supported_pulses=resolved_pulses,
            auto_register=False,
        )
        self._apply_persona_config(config_data)
        if self.plaza_url and auto_register:
            self.register()

    @classmethod
    def from_config(cls, config: ConfigInput, **kwargs: Any) -> "Persona":
        return cls(config=config, **kwargs)

    def _apply_persona_config(self, config_data: Mapping[str, Any]) -> None:
        document = dict(config_data or {})
        profile = (
            copy.deepcopy(dict(document.get("persona") or {}))
            if isinstance(document.get("persona"), Mapping)
            else {}
        )
        profile.setdefault("name", document.get("name") or self.name)
        profile.setdefault("style", "concise, faithful, and grounded")
        profile.setdefault("personality", "")
        profile.setdefault("preferences", "")
        profile.setdefault("memory", "")
        self.persona_profile = profile

        card = copy.deepcopy(dict(self.agent_card or {}))
        card["role"] = "persona"
        card["pit_type"] = "Persona"
        card["tags"] = self._merge_tags(card.get("tags"), ["persona", "pulser", "rag"])
        meta = dict(card.get("meta") or {})
        meta["persona"] = copy.deepcopy(profile)
        meta["pulser_compatible"] = True
        meta["supported_pulses"] = copy.deepcopy(self.supported_pulses)
        card["meta"] = meta
        self.agent_card = card
        self.meta = meta
        self._refresh_registration()


class RAGPersona(Persona):
    """Persona variant retaining the original Data Agent inheritance name."""


class CLIPersona(Persona):
    """Shell-oriented Persona variant retained for import compatibility."""


__all__ = ["CLIPersona", "Persona", "RAGPersona"]
