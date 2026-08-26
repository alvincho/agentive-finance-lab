"""In-memory registration, discovery, and routing for Prompits Lite."""

from __future__ import annotations

from collections.abc import Iterable

from .models import CallContext, JsonObject, PitCard, Trace
from .pit import CapabilityError, Pit, PitUnavailable


class Plaza:
    """Small coordination plane for a single-process demonstration.

    The lite Plaza deliberately omits networking, authentication, leases,
    persistence, billing, and distributed coordination.
    """

    def __init__(self, name: str = "Demo Plaza") -> None:
        self.name = name
        self.plaza_id = "plaza://local"
        self._directory: dict[str, Pit] = {}

    def register(self, pit: Pit) -> PitCard:
        if pit.address.pit_id in self._directory:
            raise ValueError(f"Pit id already registered: {pit.address.pit_id}")
        self._directory[pit.address.pit_id] = pit
        return pit.card()

    def unregister(self, pit_id: str) -> None:
        self._directory.pop(pit_id, None)

    def directory(self) -> list[PitCard]:
        return [pit.card() for pit in self._directory.values()]

    def search(
        self,
        *,
        pit_type: str | None = None,
        capability: str | None = None,
        labels: dict[str, str] | None = None,
        caller: Pit | None = None,
        trace: Trace | None = None,
    ) -> list[PitCard]:
        expected_labels = labels or {}
        if trace is not None:
            trace.emit(
                stage="plaza.discover",
                actor=caller.name if caller else "Client",
                target=self.name,
                summary="Search the Plaza directory by PIT metadata.",
                detail={
                    "pit_type": pit_type,
                    "capability": capability,
                    "labels": dict(expected_labels),
                },
            )

        matches: list[PitCard] = []
        for pit in self._directory.values():
            if pit_type and pit.pit_type != pit_type:
                continue
            if capability and not pit.advertises(capability):
                continue
            if any(pit.labels.get(key) != value for key, value in expected_labels.items()):
                continue
            matches.append(pit.card())

        if trace is not None:
            trace.emit(
                stage="plaza.matches",
                actor=self.name,
                target=caller.name if caller else "Client",
                summary=f"Found {len(matches)} matching PIT{'s' if len(matches) != 1 else ''}.",
                detail={"matches": [card.name for card in matches]},
            )
        return matches

    def invoke(
        self,
        *,
        caller: Pit,
        target: PitCard | str,
        capability: str,
        payload: JsonObject,
        trace: Trace,
    ) -> JsonObject:
        pit_id = target.address.pit_id if isinstance(target, PitCard) else target
        destination = self._directory.get(pit_id)
        if destination is None:
            raise PitUnavailable(f"No registered Pit with id '{pit_id}'")
        if not destination.advertises(capability):
            raise CapabilityError(
                f"{destination.name} does not advertise capability '{capability}'"
            )

        trace.emit(
            stage="plaza.route",
            actor=self.name,
            target=destination.name,
            summary=f"Route capability '{capability}' with the shared correlation id.",
            detail={
                "caller": caller.address.to_ref(),
                "target": destination.address.to_ref(),
                "capability": capability,
            },
        )
        context = CallContext(
            caller=caller.address,
            target=destination.address,
            capability=capability,
            trace=trace,
        )
        result = destination.handle(capability, dict(payload), context)
        trace.emit(
            stage="plaza.return",
            actor=self.name,
            target=caller.name,
            summary=f"Return structured output from {destination.name}.",
            detail={"capability": capability, "output_keys": sorted(result)},
        )
        return result

    def register_many(self, pits: Iterable[Pit]) -> None:
        for pit in pits:
            self.register(pit)


__all__ = ["Plaza"]
