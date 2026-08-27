"""Canonical message envelope copied from ``prompits.core.message``."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Envelope for agent-to-agent and agent-to-practice communication."""

    sender: str
    receiver: str
    content: Any
    msg_type: str = "message"
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"arbitrary_types_allowed": True}

    def __repr__(self) -> str:
        return (
            f"Message(type={self.msg_type}, from={self.sender}, "
            f"to={self.receiver}, content={self.content})"
        )


__all__ = ["Message"]
