"""Network composition and one end-to-end Data User request."""

from __future__ import annotations

from dataclasses import dataclass

from prompits_lite import CallContext, CapabilityError, Pit, Plaza, Trace
from prompits_lite.models import JsonObject

from .agents import DataConsultant, DataUser
from .contracts import MarketDataSource
from .yfinance_source import YFinanceSource


class DemoClient(Pit):
    """Unregistered browser adapter used only to initiate the routed call."""

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
    source: MarketDataSource

    def describe(self) -> JsonObject:
        cards = []
        for pit in (self.data_user, self.data_consultant):
            if pit is None:
                continue
            cards.append({**pit.card().to_dict(), "profile": pit.profile_dict()})
        return {
            "plaza": {
                "name": self.plaza.name,
                "plaza_id": self.plaza.plaza_id,
                "mode": "single-process in-memory discovery and routing",
            },
            "pits": cards,
            "provider": {
                "name": self.source.provider_name,
                "version": self.source.provider_version,
                "only_external_financial_data_source": True,
            },
            "route": ["Data User", "Plaza", "Data Consultant", "yfinance"],
            "dependency_direction": "demo -> phemacast-lite -> prompits-lite",
        }


def build_network(
    *,
    source: MarketDataSource | None = None,
    include_consultant: bool = True,
) -> DemoNetwork:
    market_source = source if source is not None else YFinanceSource()
    plaza = Plaza()
    data_user = DataUser(plaza)
    consultant = DataConsultant(market_source) if include_consultant else None
    plaza.register(data_user)
    if consultant is not None:
        plaza.register(consultant)
    return DemoNetwork(
        plaza=plaza,
        data_user=data_user,
        data_consultant=consultant,
        client=DemoClient(),
        source=market_source,
    )


def run_demo(
    primary_symbol: str,
    benchmark_symbol: str,
    period: str,
    *,
    source: MarketDataSource | None = None,
) -> JsonObject:
    network = build_network(source=source)
    trace = Trace()
    trace.emit(
        stage="client.submit",
        actor=network.client.name,
        target=network.data_user.name,
        summary="Submit a security-versus-benchmark data request to Data User.",
        detail={
            "primary_symbol": primary_symbol,
            "benchmark_symbol": benchmark_symbol,
            "period": period,
        },
    )
    result = network.plaza.invoke(
        caller=network.client,
        target=network.data_user.card(),
        capability="compare_market_data",
        payload={
            "primary_symbol": primary_symbol,
            "benchmark_symbol": benchmark_symbol,
            "period": period,
        },
        trace=trace,
    )
    return {
        **result,
        "correlation_id": trace.correlation_id,
        "trace": [event.to_dict() for event in trace.events],
        "network": network.describe(),
    }


__all__ = ["DemoNetwork", "build_network", "run_demo"]
