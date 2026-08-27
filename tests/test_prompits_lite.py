"""Behavior copied from the Prompits Pit, agent, Practice, and Plaza runtime."""

from __future__ import annotations

import asyncio
import uuid

from phemacast_lite import Persona, Pulser
from prompits_lite import BaseAgent, Pit, PitAddress, Plaza, Practice, StandbyAgent


class EchoPractice(Practice):
    def __init__(self) -> None:
        super().__init__(
            name="Echo",
            description="Return the supplied value.",
            id="echo-value",
            tags=["fixture"],
            inputModes=["json"],
            outputModes=["json"],
            parameters={"value": {"type": "string"}},
        )

    def mount(self, app) -> None:
        assert app is None

    def execute(self, **kwargs):
        return {"value": kwargs.get("value"), "agent": self.agent.name}


def make_agent(name: str, plaza: Plaza, *, role: str) -> StandbyAgent:
    agent = StandbyAgent(
        name,
        plaza_url=plaza,
        agent_card={
            "name": name,
            "role": role,
            "pit_type": "TestAgent",
            "description": f"{name} fixture",
            "tags": ["fixture", role],
            "party": "test",
        },
    )
    agent.add_practice(EchoPractice())
    agent.register()
    return agent


def test_framework_inheritance_is_the_original_five_level_chain() -> None:
    """There is no substitute Agent layer between the copied framework types."""

    assert BaseAgent.__bases__[0] is Pit
    assert StandbyAgent.__bases__ == (BaseAgent,)
    assert Pulser.__bases__ == (StandbyAgent,)
    assert Persona.__bases__[0] is Pulser
    assert Persona.__mro__[:5] == (
        Persona,
        Pulser,
        StandbyAgent,
        BaseAgent,
        Pit,
    )


def test_pit_and_pit_address_keep_original_identity_contract() -> None:
    pit = Pit("Example", "Metadata carrier")
    plaza_url = "memory://plaza/example"
    pit.address.register_plaza(plaza_url + "/")

    assert uuid.UUID(pit.address.pit_id)
    assert pit.address.to_ref(plaza_url) == pit.address.pit_id
    assert pit.address.to_ref() == f"{pit.address.pit_id}@{plaza_url}"
    assert PitAddress.from_value(pit.address.to_dict()).matches(pit.address)


def test_plaza_registration_and_search_return_original_directory_shape() -> None:
    plaza = Plaza()
    make_agent("Caller", plaza, role="caller")
    worker = make_agent("Worker", plaza, role="worker")

    matches = plaza.search(
        role="worker",
        practice="echo-value",
        tag="fixture",
        pit_type="TestAgent",
        party="test",
    )

    assert len(matches) == 1
    entry = matches[0]
    assert set(entry) == {
        "name",
        "card",
        "pit_type",
        "type",
        "description",
        "owner",
        "meta",
        "agent_id",
        "trusted",
        "address",
    }
    assert entry["name"] == "Worker"
    assert entry["pit_type"] == entry["type"] == "TestAgent"
    assert entry["agent_id"] == worker.agent_id
    assert entry["card"]["pit_address"] == worker.pit_address.to_dict()
    assert plaza.lookup_agent_info("Worker") == entry


def test_use_practice_preserves_local_remote_and_async_invocation() -> None:
    plaza = Plaza()
    caller = make_agent("Caller", plaza, role="caller")
    worker = make_agent("Worker", plaza, role="worker")

    local = caller.UsePractice("echo-value", {"value": "local"})
    remote = caller.UsePractice(
        "echo-value",
        {"value": "remote"},
        pit_address=worker.pit_address,
    )
    asynchronous = asyncio.run(
        caller.UsePracticeAsync(
            "echo-value",
            {"value": "async"},
            pit_address=worker.agent_card,
        )
    )

    assert local == {"value": "local", "agent": "Caller"}
    assert remote == {"value": "remote", "agent": "Worker"}
    assert asynchronous == {"value": "async", "agent": "Worker"}
