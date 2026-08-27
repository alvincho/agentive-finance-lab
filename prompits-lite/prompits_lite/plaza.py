"""In-process reduction of the original Prompits Plaza directory.

The full Plaza exposes register, search, and routing over HTTP with leases,
authentication, persistence, heartbeat, billing, and relay support.  The Lite
copy keeps the same directory cards and filtering/routing semantics, while all
participants live in one Python process.
"""

from __future__ import annotations

import copy
import json
from typing import Any, Dict, Iterable, Mapping, Optional
import uuid

from .pit import PitAddress


_LOCAL_PLAZAS: Dict[str, "Plaza"] = {}


def resolve_plaza(value: Any) -> Optional["Plaza"]:
    """Resolve a Plaza object or its in-process URL."""

    if isinstance(value, Plaza):
        return value
    normalized = str(value or "").strip().rstrip("/")
    return _LOCAL_PLAZAS.get(normalized)


class Plaza:
    """Local register/search/invoke coordinator with original Plaza cards."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8000,
        pool: Any = None,
        config: Optional[Dict[str, Any]] = None,
        config_path: Optional[str] = None,
    ) -> None:
        del pool
        self.name = "Plaza"
        self.host = host
        self.port = port
        self.config = copy.deepcopy(config or {})
        self.config_path = config_path
        self.url = f"memory://plaza/{uuid.uuid4()}"
        self.plaza_url = self.url
        self.agent_card: Dict[str, Any] = {
            "name": "Plaza",
            "role": "coordinator",
            "pit_type": "Agent",
            "tags": ["mediator"],
            "address": self.url,
            "meta": {},
        }
        self.agent_cards: Dict[str, Dict[str, Any]] = {}
        self.agent_names_by_id: Dict[str, str] = {}
        self.agent_ids: Dict[str, str] = {}
        self.pit_types: Dict[str, str] = {}
        self._agents: Dict[str, Any] = {}
        _LOCAL_PLAZAS[self.url.rstrip("/")] = self

    def register(self, agent: Any) -> Dict[str, Any]:
        """Register or refresh one agent and its public card."""

        if not hasattr(agent, "agent_card") or not hasattr(agent, "pit_address"):
            raise TypeError("Plaza can register only a BaseAgent-compatible object")

        card = copy.deepcopy(dict(agent.agent_card or {}))
        agent_id = str(getattr(agent, "agent_id", "") or agent.pit_address.pit_id or uuid.uuid4())
        agent.pit_address.pit_id = agent_id
        agent.pit_address.register_plaza(self.url)
        agent.address = agent.pit_address
        agent.agent_id = agent_id

        card.setdefault("name", getattr(agent, "name", agent_id))
        card.setdefault("role", "generic")
        card.setdefault("pit_type", "Agent")
        card.setdefault("description", getattr(agent, "description", ""))
        card.setdefault("tags", [])
        card.setdefault("meta", {})
        card.setdefault("practices", [])
        card["agent_id"] = agent_id
        card["address"] = f"memory://pit/{agent_id}"
        card["pit_address"] = agent.pit_address.to_dict()

        previous_name = self.agent_names_by_id.get(agent_id)
        if previous_name and previous_name != card["name"]:
            self.agent_ids.pop(previous_name, None)
        self._agents[agent_id] = agent
        self.agent_cards[agent_id] = card
        self.agent_names_by_id[agent_id] = str(card["name"])
        self.agent_ids[str(card["name"])] = agent_id
        self.pit_types[agent_id] = str(card.get("pit_type") or "Agent")

        agent.agent_card = copy.deepcopy(card)
        agent._plaza = self
        agent.plaza_url = self.url
        return {
            "status": "registered",
            "agent_id": agent_id,
            "expires_in": None,
            "card": copy.deepcopy(card),
        }

    def register_many(self, agents: Iterable[Any]) -> None:
        for agent in agents:
            self.register(agent)

    def unregister(self, agent: Any) -> None:
        """Remove an agent from the transient directory."""

        agent_id = self._agent_id_for(agent)
        if not agent_id:
            return
        registered = self._agents.pop(agent_id, None)
        card = self.agent_cards.pop(agent_id, None) or {}
        name = self.agent_names_by_id.pop(agent_id, None) or card.get("name")
        if name and self.agent_ids.get(str(name)) == agent_id:
            self.agent_ids.pop(str(name), None)
        self.pit_types.pop(agent_id, None)
        if registered is not None:
            registered.agent_id = None

    def directory(self) -> list[Dict[str, Any]]:
        """Return the same result shape as an unfiltered Plaza search."""

        return self.search_entries()

    @staticmethod
    def _contains(value: Any, query: Any) -> bool:
        if query in (None, ""):
            return True
        if isinstance(value, (dict, list, tuple)):
            value = json.dumps(value, sort_keys=True, default=str)
        return str(query).lower() in str(value or "").lower()

    @staticmethod
    def _pulse_matches(
        pulse: Mapping[str, Any],
        *,
        pulse_id: Optional[str],
        pulse_name: Optional[str],
        pulse_address: Optional[str],
    ) -> bool:
        if pulse_id and str(pulse.get("pulse_id") or "") != str(pulse_id):
            return False
        names = {str(pulse.get("name") or ""), str(pulse.get("pulse_name") or "")}
        aliases = {str(item) for item in (pulse.get("aliases") or [])}
        if pulse_name and str(pulse_name) not in names | aliases:
            return False
        if pulse_address and str(pulse.get("pulse_address") or "") != str(pulse_address):
            return False
        return True

    def search_entries(
        self,
        name: Optional[str] = None,
        agent_id: Optional[str] = None,
        type: Optional[str] = None,
        description: Optional[str] = None,
        owner: Optional[str] = None,
        meta: Optional[str] = None,
        role: Optional[str] = None,
        practice: Optional[str] = None,
        pit_type: Optional[str] = None,
        pulse_id: Optional[str] = None,
        pulse_name: Optional[str] = None,
        pulse_address: Optional[str] = None,
        party: Optional[str] = None,
        tag: Optional[str] = None,
        use_persisted_fallback: bool = True,
    ) -> list[Dict[str, Any]]:
        """Search registered cards using the full Plaza's public filters."""

        del use_persisted_fallback
        effective_type = pit_type or type
        results: list[Dict[str, Any]] = []
        for current_id, raw_card in self.agent_cards.items():
            card = copy.deepcopy(raw_card)
            current_name = str(card.get("name") or current_id)
            current_type = str(card.get("pit_type") or self.pit_types.get(current_id) or "Agent")
            current_meta = card.get("meta") if isinstance(card.get("meta"), dict) else {}
            current_owner = str(card.get("owner") or current_name)

            if agent_id and current_id != str(agent_id):
                continue
            if name and not self._contains(current_name, name):
                continue
            if role and str(card.get("role") or "") != str(role):
                continue
            if effective_type and current_type != str(effective_type):
                continue
            if description and not self._contains(card.get("description"), description):
                continue
            if owner and not self._contains(current_owner, owner):
                continue
            if meta and not self._contains(current_meta, meta):
                continue
            if party and str(card.get("party") or current_meta.get("party") or "") != str(party):
                continue
            if tag and str(tag) not in {str(item) for item in (card.get("tags") or [])}:
                continue
            if practice and not any(
                isinstance(item, Mapping) and item.get("id") == practice
                for item in (card.get("practices") or [])
            ):
                continue
            if pulse_id or pulse_name or pulse_address:
                pulses = [
                    item
                    for item in (current_meta.get("supported_pulses") or [])
                    if isinstance(item, Mapping)
                ]
                if not any(
                    self._pulse_matches(
                        item,
                        pulse_id=pulse_id,
                        pulse_name=pulse_name,
                        pulse_address=pulse_address,
                    )
                    for item in pulses
                ):
                    continue

            results.append(
                {
                    "name": current_name,
                    "card": card,
                    "pit_type": current_type,
                    "type": current_type,
                    "description": str(card.get("description") or ""),
                    "owner": current_owner,
                    "meta": copy.deepcopy(current_meta),
                    "agent_id": current_id,
                    "trusted": bool(card.get("trusted") or current_meta.get("trusted")),
                    "address": str(card.get("address") or ""),
                }
            )
        return results

    def search(self, **params: Any) -> list[Dict[str, Any]]:
        return self.search_entries(**params)

    def lookup_agent_info(self, value: Any) -> Optional[Dict[str, Any]]:
        agent_id = self._agent_id_for(value)
        if not agent_id:
            return None
        matches = self.search_entries(agent_id=agent_id)
        return matches[0] if matches else None

    def resolve_agent(self, value: Any) -> Any:
        agent_id = self._agent_id_for(value)
        return self._agents.get(agent_id or "")

    def invoke_practice(
        self,
        *,
        caller: Any,
        target: Any,
        practice_id: str,
        content: Any = None,
    ) -> Any:
        """Execute a registered target's Practice using UsePractice semantics."""

        caller_id = self._agent_id_for(caller)
        if caller_id not in self._agents:
            raise RuntimeError("Remote UsePractice caller is not registered with Plaza")
        destination = self.resolve_agent(target)
        if destination is None:
            raise ValueError(f"Unable to resolve remote target from pit_address: {target}")
        practice = next(
            (item for item in destination.practices if item.id == practice_id),
            None,
        )
        if practice is None:
            raise ValueError(f"Remote practice '{practice_id}' not found")
        return destination._execute_local_practice_sync(practice, content)

    def _agent_id_for(self, value: Any) -> Optional[str]:
        if value is None:
            return None
        if value in self._agents.values():
            return str(getattr(value, "agent_id", "") or getattr(value, "pit_address").pit_id)
        if isinstance(value, PitAddress):
            return str(value.pit_id) if str(value.pit_id) in self._agents else None
        if isinstance(value, Mapping):
            card = value.get("card") if isinstance(value.get("card"), Mapping) else value
            card_address = card.get("pit_address")
            address_id = (
                (card_address or {}).get("pit_id")
                if isinstance(card_address, Mapping)
                else ""
            )
            candidate = str(
                value.get("agent_id")
                or value.get("pit_id")
                or card.get("agent_id")
                or address_id
            )
            if candidate in self._agents:
                return candidate
            address = str(value.get("address") or card.get("address") or "")
            if address:
                return self._agent_id_for(address)
            name = str(value.get("name") or card.get("name") or "")
            return self.agent_ids.get(name)

        raw = str(value).strip()
        if raw in self._agents:
            return raw
        if raw in self.agent_ids:
            return self.agent_ids[raw]
        if raw.startswith("memory://pit/"):
            candidate = raw.rsplit("/", 1)[-1]
            return candidate if candidate in self._agents else None
        parsed = PitAddress.from_value(raw)
        if parsed.pit_id in self._agents:
            return parsed.pit_id
        for current_id, card in self.agent_cards.items():
            if str(card.get("address") or "") == raw:
                return current_id
        return None


__all__ = ["Plaza", "resolve_plaza"]
