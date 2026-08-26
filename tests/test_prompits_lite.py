"""Contract tests for the smallest Prompits Lite surface."""

from __future__ import annotations

import pytest

from prompits_lite import (
    CallContext,
    Capability,
    CapabilityError,
    Pit,
    PitUnavailable,
    Plaza,
    Trace,
)
from prompits_lite.models import JsonObject


class EchoPit(Pit):
    def __init__(self, *, name: str = "Echo", pit_id: str | None = None) -> None:
        super().__init__(
            name=name,
            pit_type="TestPit",
            description="Echoes a JSON payload.",
            capabilities=(Capability("echo", "Return the supplied payload."),),
            labels={"kind": "fixture"},
            pit_id=pit_id,
        )

    def handle(
        self,
        capability: str,
        payload: JsonObject,
        context: CallContext,
    ) -> JsonObject:
        if capability != "echo":
            raise CapabilityError(f"Unsupported capability: {capability}")
        return {"payload": payload, "correlation_id": context.trace.correlation_id}


def test_plaza_registers_discovers_and_routes_by_public_metadata() -> None:
    plaza = Plaza()
    caller = EchoPit(name="Caller", pit_id="caller")
    target = EchoPit(name="Target", pit_id="target")
    plaza.register_many((caller, target))
    trace = Trace(correlation_id="trace-test")

    matches = plaza.search(
        pit_type="TestPit",
        capability="echo",
        labels={"kind": "fixture"},
        caller=caller,
        trace=trace,
    )
    result = plaza.invoke(
        caller=caller,
        target=matches[1],
        capability="echo",
        payload={"message": "hello"},
        trace=trace,
    )

    assert [card.name for card in matches] == ["Caller", "Target"]
    assert result == {
        "payload": {"message": "hello"},
        "correlation_id": "trace-test",
    }
    assert [event.stage for event in trace.events] == [
        "plaza.discover",
        "plaza.matches",
        "plaza.route",
        "plaza.return",
    ]
    assert target.address.to_ref() == "pit://target@local"


def test_plaza_rejects_duplicate_ids_and_missing_targets() -> None:
    plaza = Plaza()
    caller = EchoPit(name="Echo", pit_id="echo")
    plaza.register(caller)

    with pytest.raises(ValueError, match="already registered"):
        plaza.register(EchoPit(name="Echo copy", pit_id="echo"))

    with pytest.raises(PitUnavailable, match="missing"):
        plaza.invoke(
            caller=caller,
            target="missing",
            capability="echo",
            payload={},
            trace=Trace(),
        )

    with pytest.raises(CapabilityError, match="does not advertise"):
        plaza.invoke(
            caller=caller,
            target=caller.card(),
            capability="secret",
            payload={},
            trace=Trace(),
        )


def test_default_pit_ids_allow_same_named_pits_to_coexist() -> None:
    first = EchoPit(name="Worker")
    second = EchoPit(name="Worker")
    plaza = Plaza()

    plaza.register_many((first, second))

    assert first.address.pit_id.startswith("worker-")
    assert second.address.pit_id.startswith("worker-")
    assert first.address != second.address
