"""Shared value objects for the reduced Prompits runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import monotonic
from typing import Any
from uuid import uuid4


JsonObject = dict[str, Any]


@dataclass(frozen=True, slots=True)
class PitAddress:
    """Stable local identity for one addressable Pit."""

    pit_id: str
    plaza_id: str = "plaza://local"

    def to_ref(self) -> str:
        return f"pit://{self.pit_id}@{self.plaza_id.removeprefix('plaza://')}"

    def to_dict(self) -> JsonObject:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Capability:
    """One callable operation advertised by a Pit."""

    name: str
    description: str
    input_schema: JsonObject = field(default_factory=dict)
    output_schema: JsonObject = field(default_factory=dict)

    def to_dict(self) -> JsonObject:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PitCard:
    """Public discovery metadata registered with a Plaza."""

    address: PitAddress
    name: str
    pit_type: str
    description: str
    capabilities: tuple[Capability, ...] = ()
    labels: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> JsonObject:
        return {
            "address": self.address.to_dict(),
            "name": self.name,
            "pit_type": self.pit_type,
            "description": self.description,
            "capabilities": [item.to_dict() for item in self.capabilities],
            "labels": dict(self.labels),
        }


@dataclass(frozen=True, slots=True)
class TraceEvent:
    """One observable step in a routed collaboration."""

    sequence: int
    stage: str
    actor: str
    target: str | None
    summary: str
    elapsed_ms: float
    detail: JsonObject = field(default_factory=dict)

    def to_dict(self) -> JsonObject:
        return asdict(self)


@dataclass(slots=True)
class Trace:
    """Correlation-scoped event log shared across every Pit hop."""

    correlation_id: str = field(default_factory=lambda: uuid4().hex)
    events: list[TraceEvent] = field(default_factory=list)
    _started_at: float = field(default_factory=monotonic, repr=False)

    def emit(
        self,
        *,
        stage: str,
        actor: str,
        summary: str,
        target: str | None = None,
        detail: JsonObject | None = None,
    ) -> TraceEvent:
        event = TraceEvent(
            sequence=len(self.events) + 1,
            stage=stage,
            actor=actor,
            target=target,
            summary=summary,
            elapsed_ms=round((monotonic() - self._started_at) * 1000, 3),
            detail=dict(detail or {}),
        )
        self.events.append(event)
        return event

    def to_dict(self) -> JsonObject:
        return {
            "correlation_id": self.correlation_id,
            "events": [event.to_dict() for event in self.events],
        }


@dataclass(frozen=True, slots=True)
class CallContext:
    """Context propagated by Plaza during one capability invocation."""

    caller: PitAddress
    target: PitAddress
    capability: str
    trace: Trace
