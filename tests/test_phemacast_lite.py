"""Pulse and Persona validation tests."""

from __future__ import annotations

import pytest

from phemacast_lite import Persona, PersonaProfile, PulseSpec, Pulser
from prompits_lite import CallContext, CapabilityError, PitAddress, Trace


def context_for(pulser: Pulser) -> CallContext:
    return CallContext(
        caller=PitAddress("test-client"),
        target=pulser.address,
        capability="calculate",
        trace=Trace(correlation_id="pulse-test"),
    )


def test_pulser_advertises_and_validates_typed_pulse_contract() -> None:
    pulser = Pulser(name="Calculator", description="Test fixture")
    pulser.register_pulse(
        PulseSpec(
            name="calculate",
            description="Double one integer.",
            required_inputs=("value",),
            output_fields=("result",),
            input_types={"value": int},
            output_types={"result": int},
        ),
        lambda payload, _context: {"result": int(payload["value"]) * 2},
    )

    assert pulser.advertises("calculate")
    capability = pulser.card().capabilities[0]
    assert capability.input_schema == {
        "value": {"types": ["int"], "required": True}
    }
    assert capability.output_schema == {
        "result": {"types": ["int"], "required": True}
    }
    assert pulser.handle("calculate", {"value": 3}, context_for(pulser)) == {"result": 6}

    with pytest.raises(CapabilityError, match="missing required input"):
        pulser.handle("calculate", {}, context_for(pulser))
    with pytest.raises(CapabilityError, match="must be int, not str"):
        pulser.handle("calculate", {"value": "three"}, context_for(pulser))


def test_pulser_rejects_invalid_outputs_and_unknown_pulses() -> None:
    pulser = Pulser(name="Broken", description="Test fixture")
    pulser.register_pulse(
        PulseSpec(
            name="calculate",
            description="Deliberately broken output.",
            output_fields=("result",),
            output_types={"result": int},
        ),
        lambda _payload, _context: {},
    )

    with pytest.raises(CapabilityError, match="omitted output field"):
        pulser.handle("calculate", {}, context_for(pulser))
    with pytest.raises(CapabilityError, match="does not expose Pulse"):
        pulser.handle("unknown", {}, context_for(pulser))


def test_persona_keeps_profile_separate_from_runtime_identity() -> None:
    profile = PersonaProfile(
        role="reviewer",
        purpose="Inspect structured output.",
        instructions=("Cite the contract.",),
    )
    persona = Persona(
        name="Reviewer",
        description="Test Persona",
        profile=profile,
        labels={"role": "contradictory", "scope": "fixture"},
    )

    assert persona.pit_type == "Persona"
    assert persona.labels["role"] == "reviewer"
    assert persona.labels["scope"] == "fixture"
    assert persona.profile is profile
    assert persona.profile_dict()["purpose"] == "Inspect structured output."
