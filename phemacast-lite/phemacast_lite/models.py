"""Small data models copied from ``phemacast.models``."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


@dataclass
class Persona:
    """Presentation voice profile used during final casting."""

    name: str
    tone: str = "neutral"
    style: str = "concise"


@dataclass
class PhemaBlock:
    """One templated output unit with pulse-data bindings."""

    name: str
    template: str
    bindings: List[str]


@dataclass
class Phema:
    """Structured narrative blueprint."""

    phema_id: str
    title: str
    prompt: str
    blocks: List[PhemaBlock]
    default_persona: Persona
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Pulse:
    """Timestamped data snapshot fetched from a named pulse provider."""

    key: str
    payload: Dict[str, Any]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


__all__ = ["Persona", "Phema", "PhemaBlock", "Pulse"]
