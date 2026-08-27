"""Faithful in-process reduction of Prompits BaseAgent and StandbyAgent."""

from __future__ import annotations

from abc import ABC, abstractmethod
import asyncio
import copy
import inspect
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel

from .message import Message
from .pit import Pit, PitAddress
from .practice import Practice


class PracticeInvocationRequest(BaseModel):
    """Envelope used by the full runtime for remote UsePractice execution."""

    sender: str
    receiver: str
    content: Any = None
    msg_type: str
    request_id: Optional[str] = None
    caller_agent_address: Optional[Dict[str, Any]] = None
    caller_agent_name: Optional[str] = None
    caller_agent_url: Optional[str] = None


class BaseAgent(Pit, ABC):
    """Agent host with original cards, practices, Plaza search, and UsePractice.

    The full runtime's HTTP server, credentials, persistence, policies,
    heartbeat, and billing are intentionally absent. Remote calls are routed
    to registered agents by the in-process Plaza.
    """

    MAILBOX_PRACTICE_ID = "mailbox"

    def __init__(
        self,
        name: str,
        host: str = "127.0.0.1",
        port: int = 8000,
        plaza_url: Any = None,
        agent_card: Dict[str, Any] | None = None,
        pool: Any = None,
    ) -> None:
        del pool
        seed_card = copy.deepcopy(agent_card or {"name": name, "role": "generic", "tags": []})
        seed_card.setdefault("name", name)
        seed_card.setdefault("role", "generic")
        seed_card.setdefault("tags", [])
        seed_card.setdefault("pit_type", "Agent")
        seed_card.setdefault("meta", {})
        seed_card.setdefault("host", host)
        seed_card.setdefault("port", port)
        seed_card.setdefault("description", "")
        seed_card.setdefault("practices", [])

        address = PitAddress.from_value(seed_card.get("pit_address"))
        if not address.pit_id:
            address = PitAddress()
        super().__init__(
            name=name,
            description=str(seed_card.get("description") or ""),
            address=address,
            meta=seed_card.get("meta", {}),
        )

        from .plaza import Plaza, resolve_plaza

        self.name = name
        self.host = host
        self.port = port
        self._plaza = plaza_url if isinstance(plaza_url, Plaza) else resolve_plaza(plaza_url)
        self.plaza_url = self._plaza.url if self._plaza is not None else str(plaza_url or "").rstrip("/")
        self.agent_card = seed_card
        self.agent_id: Optional[str] = self.agent_card.get("agent_id")
        self.pit_address = self.address
        if self.agent_id:
            self.pit_address.pit_id = str(self.agent_id)
        if self.plaza_url:
            self.pit_address.register_plaza(self.plaza_url)
        self.agent_card["address"] = str(
            self.agent_card.get("address") or f"http://{self.host}:{self.port}"
        )
        self.agent_card["pit_address"] = self.pit_address.to_dict()
        self.practices: List[Practice] = []
        self.app = None
        self._working_list: List[Dict[str, Any]] = []
        self._work_history: List[Dict[str, Any]] = []
        self.add_practice_endpoint(self._mailbox_practice_metadata())

    @property
    @abstractmethod
    def status(self) -> str:
        raise NotImplementedError("BaseAgent subclasses must implement status")

    @property
    @abstractmethod
    def working_list(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("BaseAgent subclasses must implement working_list")

    @property
    @abstractmethod
    def work_history(self) -> List[Dict[str, Any]]:
        raise NotImplementedError("BaseAgent subclasses must implement work_history")

    def _default_practice_metadata(self, practice: Practice) -> Dict[str, Any]:
        return {
            "name": practice.name,
            "description": practice.description,
            "id": practice.id,
            "cost": practice.cost,
            "tags": list(practice.tags),
            "examples": list(practice.examples),
            "inputModes": list(practice.inputModes),
            "outputModes": list(practice.outputModes),
            "parameters": copy.deepcopy(practice.parameters),
            "path": practice.path,
        }

    def _mailbox_practice_metadata(self) -> Dict[str, Any]:
        return {
            "name": "Mailbox",
            "description": "Default inbound message endpoint for generic agent delivery.",
            "id": self.MAILBOX_PRACTICE_ID,
            "cost": 0,
            "tags": ["message", "mailbox"],
            "examples": [],
            "inputModes": ["http-post", "json"],
            "outputModes": ["json"],
            "parameters": {},
            "path": "/mailbox",
        }

    @staticmethod
    def _normalize_practice_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        normalized = copy.deepcopy(dict(metadata or {}))
        normalized["cost"] = Practice._normalize_cost(normalized.get("cost", 0))
        return normalized

    def _upsert_practice_metadata_in_card(self, metadata: Dict[str, Any]) -> None:
        practices = self.agent_card.setdefault("practices", [])
        for index, current in enumerate(practices):
            if current.get("id") == metadata.get("id"):
                practices[index] = copy.deepcopy(metadata)
                return
        practices.append(copy.deepcopy(metadata))

    def add_practice(self, practice: Practice) -> None:
        """Bind and expose a Practice exactly as the full agent does."""

        if any(item.id == practice.id for item in self.practices):
            return
        practice.bind(self)
        practice.mount(self.app)
        self.practices.append(practice)
        entries = None
        get_entries = getattr(practice, "get_callable_endpoints", None)
        if callable(get_entries):
            candidate = get_entries()
            if isinstance(candidate, list):
                entries = [item for item in candidate if isinstance(item, dict)]
        for entry in entries or [self._default_practice_metadata(practice)]:
            self._upsert_practice_metadata_in_card(self._normalize_practice_metadata(entry))
        self._refresh_registration()

    def add_practice_endpoint(self, metadata: Dict[str, Any]) -> bool:
        if not isinstance(metadata, dict) or not metadata.get("id") or not metadata.get("path"):
            return False
        self._upsert_practice_metadata_in_card(self._normalize_practice_metadata(metadata))
        self._refresh_registration()
        return True

    def delete_practice(self, practice_id: str) -> bool:
        if not practice_id:
            return False
        previous_count = len(self.practices)
        self.practices = [item for item in self.practices if item.id != practice_id]
        card_practices = self.agent_card.get("practices") or []
        self.agent_card["practices"] = [
            item for item in card_practices if item.get("id") != practice_id
        ]
        deleted = previous_count != len(self.practices) or len(card_practices) != len(
            self.agent_card["practices"]
        )
        if deleted:
            self._refresh_registration()
        return deleted

    def register(
        self,
        *,
        start_reconnect_on_failure: bool = True,
        request_retries: Optional[int] = None,
        request_timeout: Optional[float] = None,
    ) -> Any:
        """Register with the configured in-process Plaza."""

        del start_reconnect_on_failure, request_retries, request_timeout
        plaza = self._resolve_plaza()
        if plaza is None:
            return None
        self.agent_card["host"] = self.host
        self.agent_card["port"] = self.port
        result = plaza.register(self)
        self.agent_card["pit_address"] = self.pit_address.to_dict()
        return result

    def _resolve_plaza(self) -> Any:
        if self._plaza is not None:
            return self._plaza
        from .plaza import resolve_plaza

        self._plaza = resolve_plaza(self.plaza_url)
        return self._plaza

    def _refresh_registration(self) -> None:
        plaza = self._resolve_plaza()
        if plaza is not None and self.agent_id and plaza.resolve_agent(self.agent_id) is self:
            plaza.register(self)

    def _ensure_token_valid(self) -> Optional[Dict[str, str]]:
        """Compatibility seam: registration replaces authentication in Lite."""

        plaza = self._resolve_plaza()
        if plaza is None or plaza.resolve_agent(self) is not self:
            return None
        return {"X-Prompits-Transport": "in-process"}

    def lookup_agent_info(self, name: str) -> Optional[Dict[str, Any]]:
        plaza = self._resolve_plaza()
        return plaza.lookup_agent_info(name) if plaza is not None else None

    def lookup_agent(self, name: str) -> Optional[str]:
        info = self.lookup_agent_info(name)
        if info:
            return str(info["card"].get("address") or "") or None
        return None

    def search(
        self,
        role: str | None = None,
        practice: str | None = None,
        tag: str | None = None,
        **kwargs: Any,
    ) -> list[Dict[str, Any]]:
        """Search for agents through the configured Plaza directory."""

        plaza = self._resolve_plaza()
        if plaza is None or plaza.resolve_agent(self) is not self:
            return []
        params = dict(kwargs)
        if role:
            params["role"] = role
        if practice:
            params["practice"] = practice
        if tag:
            params["tag"] = tag
        return plaza.search_entries(**params)

    def send(self, receiver_addr: Any, content: Any, msg_type: str = "message") -> Any:
        plaza = self._resolve_plaza()
        target = plaza.resolve_agent(receiver_addr) if plaza is not None else None
        if target is None:
            raise ValueError(f"Unable to resolve target: {receiver_addr}")
        return target.receive(
            Message(
                sender=str(self.agent_id or self.name),
                receiver=str(target.agent_id or target.name),
                content=content,
                msg_type=msg_type,
            )
        )

    def _execute_local_practice_sync(self, practice: Practice, content: Any) -> Any:
        if isinstance(content, dict):
            result = practice.execute(**content)
        elif content is None:
            result = practice.execute()
        else:
            result = practice.execute(content=content)
        if inspect.isawaitable(result):
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                return asyncio.run(result)
            raise RuntimeError(
                "Local practice returned an awaitable; call UsePractice(..., async_mode=True)."
            )
        return result

    async def _execute_local_practice_async(self, practice: Practice, content: Any) -> Any:
        if inspect.iscoroutinefunction(practice.execute):
            if isinstance(content, dict):
                return await practice.execute(**content)
            if content is None:
                return await practice.execute()
            return await practice.execute(content=content)
        result = await asyncio.to_thread(self._execute_local_practice_sync, practice, content)
        if inspect.isawaitable(result):
            return await result
        return result

    def _is_local_target(self, pit_address: Any) -> bool:
        if pit_address is None:
            return True
        if pit_address is self:
            return True
        candidate = self._coerce_pit_address(pit_address)
        return bool(candidate and candidate.matches(self.pit_address))

    @staticmethod
    def _coerce_pit_address(value: Any) -> Optional[PitAddress]:
        if value is None:
            return None
        if isinstance(value, PitAddress):
            return value
        if isinstance(value, dict):
            card = value.get("card") if isinstance(value.get("card"), dict) else value
            raw = card.get("pit_address") or value.get("pit_address")
            if raw:
                return PitAddress.from_value(raw)
        if hasattr(value, "pit_address"):
            return PitAddress.from_value(value.pit_address)
        return None

    async def UsePracticeAsync(
        self,
        practice_id: str,
        content: Any = None,
        pit_address: Any = None,
        timeout: int = 240,
    ) -> Any:
        """Use a local or Plaza-registered Practice asynchronously."""

        del timeout
        local_practice = next((item for item in self.practices if item.id == practice_id), None)
        if self._is_local_target(pit_address):
            if local_practice is None:
                raise ValueError(f"Local practice '{practice_id}' not found")
            return await self._execute_local_practice_async(local_practice, content)
        plaza = self._resolve_plaza()
        if plaza is None:
            raise ValueError(f"Unable to resolve remote target from pit_address: {pit_address}")
        return await asyncio.to_thread(
            plaza.invoke_practice,
            caller=self,
            target=pit_address,
            practice_id=practice_id,
            content=content,
        )

    def UsePractice(
        self,
        practice_id: str,
        content: Any = None,
        pit_address: Any = None,
        async_mode: bool = False,
        timeout: int = 240,
    ) -> Any:
        """Use a local or Plaza-registered Practice."""

        if async_mode:
            return self.UsePracticeAsync(
                practice_id=practice_id,
                content=content,
                pit_address=pit_address,
                timeout=timeout,
            )
        local_practice = next((item for item in self.practices if item.id == practice_id), None)
        if self._is_local_target(pit_address):
            if local_practice is None:
                raise ValueError(f"Local practice '{practice_id}' not found")
            return self._execute_local_practice_sync(local_practice, content)
        plaza = self._resolve_plaza()
        if plaza is None:
            raise ValueError(f"Unable to resolve remote target from pit_address: {pit_address}")
        return plaza.invoke_practice(
            caller=self,
            target=pit_address,
            practice_id=practice_id,
            content=content,
        )

    @abstractmethod
    def receive(self, message: Message) -> Any:
        pass

    @abstractmethod
    def run(self) -> None:
        pass


class StandbyAgent(BaseAgent):
    """Generic worker-style agent copied from the full runtime."""

    def __init__(
        self,
        name: str,
        host: str = "127.0.0.1",
        port: int = 8000,
        plaza_url: Any = None,
        agent_card: Dict[str, Any] | None = None,
        pool: Any = None,
    ) -> None:
        super().__init__(name, host, port, plaza_url, agent_card, pool=pool)

    @property
    def status(self) -> str:
        return f"Idle; {self.name} is standing by."

    @property
    def working_list(self) -> List[Dict[str, Any]]:
        return copy.deepcopy(self._working_list)

    @property
    def work_history(self) -> List[Dict[str, Any]]:
        return copy.deepcopy(self._work_history)

    def receive(self, message: Message) -> Any:
        if message.msg_type == "command":
            return self.handle_command(message.content)
        for practice in self.practices:
            if practice.id != message.msg_type:
                continue
            handle_message = getattr(practice, "handle_message", None)
            if callable(handle_message):
                return handle_message(message)
            return self._execute_local_practice_sync(practice, message.content)
        return None

    def handle_command(self, content: str) -> Any:
        return None

    def run(self) -> None:
        pass


__all__ = ["BaseAgent", "PracticeInvocationRequest", "StandbyAgent"]
