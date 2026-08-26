"""Role-aware Pulser used for agent collaboration demos."""

from __future__ import annotations

from .models import PersonaProfile
from .pulser import Pulser


class Persona(Pulser):
    """Runtime Persona: identity, role profile, and typed Pulses."""

    def __init__(
        self,
        *,
        name: str,
        description: str,
        profile: PersonaProfile,
        labels: dict[str, str] | None = None,
        pit_id: str | None = None,
    ) -> None:
        persona_labels = dict(labels or {})
        persona_labels["role"] = profile.role
        super().__init__(
            name=name,
            description=description,
            pit_type="Persona",
            labels=persona_labels,
            pit_id=pit_id,
        )
        self.profile = profile

    def profile_dict(self) -> dict[str, object]:
        return self.profile.to_dict()


__all__ = ["Persona"]
