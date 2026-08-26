"""Public contracts exposed by Phemacast Lite."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from typing import Any

from prompits_lite import Capability


@dataclass(frozen=True, slots=True)
class PulseSpec:
    """Typed description of one callable Pulse."""

    name: str
    description: str
    required_inputs: tuple[str, ...] = ()
    output_fields: tuple[str, ...] = ()
    input_types: Mapping[str, type | tuple[type, ...]] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )
    output_types: Mapping[str, type | tuple[type, ...]] = field(
        default_factory=dict,
        repr=False,
        compare=False,
    )

    def as_capability(self) -> Capability:
        return Capability(
            name=self.name,
            description=self.description,
            input_schema=_field_schema(
                declared_fields=self.required_inputs,
                expected_types=self.input_types,
                required_fields=set(self.required_inputs),
            ),
            output_schema=_field_schema(
                declared_fields=self.output_fields,
                expected_types=self.output_types,
                required_fields=set(self.output_fields),
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "required_inputs": list(self.required_inputs),
            "output_fields": list(self.output_fields),
            "input_types": {
                name: _type_names(expected) for name, expected in self.input_types.items()
            },
            "output_types": {
                name: _type_names(expected) for name, expected in self.output_types.items()
            },
        }


def _type_names(expected: type | tuple[type, ...]) -> list[str]:
    expected_types = expected if isinstance(expected, tuple) else (expected,)
    return [item.__name__ for item in expected_types]


def _field_schema(
    *,
    declared_fields: tuple[str, ...],
    expected_types: Mapping[str, type | tuple[type, ...]],
    required_fields: set[str],
) -> dict[str, Any]:
    ordered_names = dict.fromkeys((*declared_fields, *expected_types))
    return {
        name: {
            "types": _type_names(expected_types[name]) if name in expected_types else ["any"],
            "required": name in required_fields,
        }
        for name in ordered_names
    }


@dataclass(frozen=True, slots=True)
class PersonaProfile:
    """Role definition attached to a runtime Persona.

    The explicit ``Profile`` suffix keeps this value object distinct from the
    addressable ``Persona`` runtime class.
    """

    role: str
    purpose: str
    instructions: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
