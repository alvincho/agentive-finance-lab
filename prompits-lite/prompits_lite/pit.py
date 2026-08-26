"""The smallest addressable unit in Prompits Lite."""

from __future__ import annotations

from abc import ABC, abstractmethod
import re
from typing import Any, Iterable
from uuid import uuid4

from .models import CallContext, Capability, JsonObject, PitAddress, PitCard


class CapabilityError(RuntimeError):
    """Raised when a Pit cannot execute the requested capability."""


class PitUnavailable(RuntimeError):
    """Raised when Plaza cannot find or route to a requested Pit."""


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "unnamed-pit"


def _new_pit_id(name: str) -> str:
    return f"{_slug(name)}-{uuid4().hex[:8]}"


class Pit(ABC):
    """Addressable identity with discoverable capabilities.

    ``Pit`` is intentionally not expanded as an acronym. In the original
    vocabulary it is the root identity carried by framework components.
    """

    def __init__(
        self,
        *,
        name: str,
        pit_type: str,
        description: str,
        capabilities: Iterable[Capability] = (),
        labels: dict[str, str] | None = None,
        pit_id: str | None = None,
    ) -> None:
        self.name = name
        self.pit_type = pit_type
        self.description = description
        self.address = PitAddress(pit_id=pit_id or _new_pit_id(name))
        self._capabilities = {capability.name: capability for capability in capabilities}
        self.labels = dict(labels or {})

    @property
    def capabilities(self) -> tuple[Capability, ...]:
        return tuple(self._capabilities.values())

    def card(self) -> PitCard:
        return PitCard(
            address=self.address,
            name=self.name,
            pit_type=self.pit_type,
            description=self.description,
            capabilities=self.capabilities,
            labels=dict(self.labels),
        )

    def advertises(self, capability: str) -> bool:
        return capability in self._capabilities

    @abstractmethod
    def handle(self, capability: str, payload: JsonObject, context: CallContext) -> JsonObject:
        """Execute one advertised capability."""


__all__ = ["CapabilityError", "Pit", "PitUnavailable"]
