"""Reduced copy of ``prompits.core.practice``."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Union

from .pit import Pit


class Practice(Pit, ABC):
    """Capability descriptor and executable unit mounted by an agent."""

    def __init__(
        self,
        name: str,
        description: str = "",
        id: str = "",
        cost: Union[int, float] = 0,
        tags: List[str] | None = None,
        examples: List[Union[str, Dict[str, Any]]] | None = None,
        inputModes: List[str] | None = None,
        outputModes: List[str] | None = None,
        parameters: Dict[str, Any] | None = None,
    ) -> None:
        self.name = name
        self.description = description
        self.id = id or name.lower().replace(" ", "-")
        self.cost = self._normalize_cost(cost)
        self.tags = tags or []
        self.examples = examples or []
        self.inputModes = inputModes or []
        self.outputModes = outputModes or []
        self.parameters = parameters or {}
        self.agent = None

    @staticmethod
    def _normalize_cost(value: Any) -> Union[int, float]:
        try:
            normalized = float(value)
        except (TypeError, ValueError):
            return 0
        if normalized < 0:
            return 0
        return int(normalized) if normalized.is_integer() else normalized

    @property
    def path(self) -> str:
        return f"/{self.id.replace('-', '_')}"

    def bind(self, agent: Any) -> None:
        self.agent = agent

    @abstractmethod
    def mount(self, app: Any) -> None:
        """Mount the transport surface; Lite practices normally do nothing."""

    def execute(self, **kwargs: Any) -> Any:
        """Optional executable interface for the Practice."""

        return None


__all__ = ["Practice"]
