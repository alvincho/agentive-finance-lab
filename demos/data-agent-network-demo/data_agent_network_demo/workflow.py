"""Network composition and deterministic end-to-end execution."""

from __future__ import annotations

from dataclasses import dataclass

from prompits_lite import CallContext, CapabilityError, Pit, Plaza, Trace
from prompits_lite.models import JsonObject

from .agents import DataConsultant, DataUser


class DemoClient(Pit):
    """Unregistered UI adapter used only to initiate the first routed call."""

    def __init__(self) -> None:
        super().__init__(
            name="Demo UI",
            pit_id="demo-ui",
            pit_type="Client",
            description="Browser request adapter; not a member of the agent network.",
        )

    def handle(self, capability: str, payload: JsonObject, context: CallContext) -> JsonObject:
        raise CapabilityError("Demo UI does not expose inbound capabilities")


@dataclass(slots=True)
class DemoNetwork:
    plaza: Plaza
    data_user: DataUser
    data_consultant: DataConsultant | None
    client: DemoClient

    def describe(self) -> JsonObject:
        return {
            "plaza": {
                "name": self.plaza.name,
                "plaza_id": self.plaza.plaza_id,
                "mode": "in-memory demo registry",
            },
            "pits": [card.to_dict() for card in self.plaza.directory()],
            "dependency_direction": "demo -> phemacast-lite -> prompits-lite",
        }


def build_network(*, include_consultant: bool = True) -> DemoNetwork:
    plaza = Plaza()
    data_user = DataUser(plaza)
    consultant = DataConsultant() if include_consultant else None
    plaza.register(data_user)
    if consultant is not None:
        plaza.register(consultant)
    return DemoNetwork(
        plaza=plaza,
        data_user=data_user,
        data_consultant=consultant,
        client=DemoClient(),
    )


def run_demo(prompt: str, *, consultant_available: bool = True) -> JsonObject:
    network = build_network(include_consultant=consultant_available)
    trace = Trace()
    trace.emit(
        stage="client.submit",
        actor=network.client.name,
        target=network.data_user.name,
        summary="Submit one financial-data question to the Data User Persona.",
        detail={"prompt_length": len(prompt)},
    )
    result = network.plaza.invoke(
        caller=network.client,
        target=network.data_user.card(),
        capability="data_request",
        payload={"prompt": prompt},
        trace=trace,
    )
    return {
        **result,
        "correlation_id": trace.correlation_id,
        "trace": [event.to_dict() for event in trace.events],
        "network": network.describe(),
    }
