"""A Pit that exposes named, typed Pulse handlers."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from prompits_lite import CallContext, CapabilityError, Pit
from prompits_lite.models import JsonObject

from .models import PulseSpec


PulseHandler = Callable[[JsonObject, CallContext], JsonObject]


class Pulser(Pit):
    """Addressable capability provider backed by Pulse handlers."""

    def __init__(
        self,
        *,
        name: str,
        description: str,
        pit_type: str = "Pulser",
        labels: dict[str, str] | None = None,
        pit_id: str | None = None,
    ) -> None:
        super().__init__(
            name=name,
            pit_type=pit_type,
            description=description,
            labels=labels,
            pit_id=pit_id,
        )
        self._pulse_specs: dict[str, PulseSpec] = {}
        self._pulse_handlers: dict[str, PulseHandler] = {}

    @property
    def pulse_specs(self) -> tuple[PulseSpec, ...]:
        return tuple(self._pulse_specs.values())

    def register_pulse(self, spec: PulseSpec, handler: PulseHandler) -> None:
        if spec.name in self._pulse_specs:
            raise ValueError(f"Pulse already registered: {spec.name}")
        self._pulse_specs[spec.name] = spec
        self._pulse_handlers[spec.name] = handler
        self._capabilities[spec.name] = spec.as_capability()

    def handle(self, capability: str, payload: JsonObject, context: CallContext) -> JsonObject:
        spec = self._pulse_specs.get(capability)
        handler = self._pulse_handlers.get(capability)
        if spec is None or handler is None:
            raise CapabilityError(f"{self.name} does not expose Pulse '{capability}'")

        missing = [key for key in spec.required_inputs if key not in payload]
        if missing:
            raise CapabilityError(
                f"Pulse '{capability}' is missing required input(s): {', '.join(missing)}"
            )
        self._validate_types(
            capability=capability,
            values=payload,
            expected_types=spec.input_types,
            direction="input",
        )

        context.trace.emit(
            stage="pulse.execute",
            actor=self.name,
            target=None,
            summary=f"Execute the typed '{capability}' Pulse.",
            detail={
                "required_inputs": list(spec.required_inputs),
                "received_inputs": sorted(payload),
            },
        )
        result = handler(dict(payload), context)
        if not isinstance(result, dict):
            raise CapabilityError(f"Pulse '{capability}' must return a JSON object")

        missing_outputs = [key for key in spec.output_fields if key not in result]
        if missing_outputs:
            raise CapabilityError(
                f"Pulse '{capability}' omitted output field(s): {', '.join(missing_outputs)}"
            )
        self._validate_types(
            capability=capability,
            values=result,
            expected_types=spec.output_types,
            direction="output",
        )
        context.trace.emit(
            stage="pulse.complete",
            actor=self.name,
            target=context.caller.to_ref(),
            summary="Publish structured Pulse output for the calling Pit.",
            detail={"output_fields": sorted(result)},
        )
        return result

    @staticmethod
    def _validate_types(
        *,
        capability: str,
        values: JsonObject,
        expected_types: Mapping[str, type | tuple[type, ...]],
        direction: str,
    ) -> None:
        for field_name, expected in expected_types.items():
            if field_name not in values or isinstance(values[field_name], expected):
                continue
            expected_tuple = expected if isinstance(expected, tuple) else (expected,)
            expected_label = " or ".join(item.__name__ for item in expected_tuple)
            actual_label = type(values[field_name]).__name__
            raise CapabilityError(
                f"Pulse '{capability}' {direction} '{field_name}' must be "
                f"{expected_label}, not {actual_label}"
            )


__all__ = ["PulseHandler", "Pulser"]
