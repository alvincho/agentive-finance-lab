"""Reduced copy of the original Prompits Pit identity primitives.

Only the HTTP registration call is omitted. Identity, Plaza references, and
the public metadata carried by a Pit follow ``prompits.core.pit``.
"""

from __future__ import annotations

from abc import ABC
import copy
from dataclasses import dataclass, field
import json
from typing import Any, Dict, List
import uuid


@dataclass
class PitAddress:
    """Stable address identity for any Pit."""

    pit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    plazas: List[str] = field(default_factory=list)

    def register_plaza(self, plaza_url: str) -> None:
        """Record a Plaza that can resolve this Pit."""

        if not plaza_url:
            return
        normalized = str(plaza_url).rstrip("/")
        if normalized not in self.plazas:
            self.plazas.append(normalized)

    def to_ref(self, reference_plaza: str | None = None) -> str:
        """Return the same compact reference used by the full runtime."""

        normalized_reference = str(reference_plaza).rstrip("/") if reference_plaza else ""
        plazas = [str(item).rstrip("/") for item in self.plazas if item]
        if normalized_reference and normalized_reference in plazas:
            return str(self.pit_id)
        if plazas:
            return f"{self.pit_id}@{plazas[0]}"
        return str(self.pit_id)

    def matches(self, other: Any) -> bool:
        """Return whether another address identifies this Pit."""

        candidate = self.from_value(other)
        if self.pit_id and candidate.pit_id:
            return str(self.pit_id) == str(candidate.pit_id)
        return self.to_ref() == candidate.to_ref()

    def to_dict(self) -> Dict[str, Any]:
        return {"pit_id": self.pit_id, "plazas": list(self.plazas)}

    @classmethod
    def from_value(cls, value: Any) -> "PitAddress":
        """Build an address from an address object, mapping, UUID, or ref."""

        if isinstance(value, PitAddress):
            return value
        if isinstance(value, dict):
            pit_id = str(value.get("pit_id") or value.get("agent_id") or uuid.uuid4())
            plazas = [str(item).rstrip("/") for item in (value.get("plazas") or []) if item]
            return cls(pit_id=pit_id, plazas=plazas)
        if isinstance(value, str):
            raw = value.strip()
            if not raw:
                return cls(pit_id="", plazas=[])
            if raw.startswith("{") and raw.endswith("}"):
                try:
                    return cls.from_value(json.loads(raw))
                except (TypeError, ValueError, json.JSONDecodeError):
                    return cls(pit_id="", plazas=[])
            if "@" in raw:
                pit_id, plaza = raw.split("@", 1)
                try:
                    uuid.UUID(str(pit_id))
                except ValueError:
                    return cls(pit_id="", plazas=[])
                return cls(pit_id=str(pit_id), plazas=[plaza.rstrip("/")] if plaza else [])
            try:
                uuid.UUID(raw)
            except ValueError:
                return cls(pit_id="", plazas=[])
            return cls(pit_id=raw)
        return cls(pit_id="", plazas=[])


class Pit(ABC):
    """Root metadata carrier for framework components."""

    def __init__(
        self,
        name: str,
        description: str,
        address: PitAddress | None = None,
        meta: Dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.address = address or PitAddress()
        self.meta = meta or {}

    def build_register_payload(
        self,
        plaza_url: str,
        card: Dict[str, Any] | None = None,
        address: str | None = None,
        expires_in: int = 3600,
        pit_type: str | None = None,
        pit_id: str | None = None,
        api_key: str | None = None,
        accepts_inbound_from_plaza: bool | None = None,
    ) -> Dict[str, Any]:
        """Build the original Plaza registration payload without sending it."""

        if not plaza_url:
            raise ValueError("plaza_url is required")
        normalized_plaza = str(plaza_url).rstrip("/")
        self.address.register_plaza(normalized_plaza)
        if pit_id:
            self.address.pit_id = str(pit_id)

        payload_card = copy.deepcopy(dict(card or {}))
        payload_card.setdefault("name", self.name)
        payload_card["pit_address"] = self.address.to_dict()
        payload_meta = payload_card.get("meta")
        if not isinstance(payload_meta, dict):
            payload_meta = {}
        payload_card["meta"] = payload_meta
        if accepts_inbound_from_plaza is not None:
            accepts = bool(accepts_inbound_from_plaza)
            payload_card["accepts_inbound_from_plaza"] = accepts
            payload_card["accepts_direct_call"] = accepts
            payload_meta["accepts_inbound_from_plaza"] = accepts
            payload_meta["accepts_direct_call"] = accepts
            payload_card.setdefault(
                "connectivity_mode",
                "plaza-forward" if accepts else "outbound-only",
            )

        payload: Dict[str, Any] = {
            "agent_name": self.name,
            "address": address or payload_card.get("address", ""),
            "expires_in": int(expires_in),
            "card": payload_card,
        }
        if accepts_inbound_from_plaza is not None:
            payload["accepts_inbound_from_plaza"] = bool(accepts_inbound_from_plaza)
            payload["accepts_direct_call"] = bool(accepts_inbound_from_plaza)
        if pit_type:
            payload["pit_type"] = pit_type
        if pit_id and api_key:
            payload["agent_id"] = str(pit_id)
            payload["api_key"] = str(api_key)
        return payload


__all__ = ["Pit", "PitAddress"]
