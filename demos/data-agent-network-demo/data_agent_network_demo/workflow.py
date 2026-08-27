"""Faithful YFinance-only reduction of the original demo harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from prompits_lite import Plaza

from .agents import DataConsultantPersona, DataUserPersona
from .contracts import DATA_FETCH_PULSE_NAME, DATA_REQUEST_PULSE_NAME, YFinanceProvider
from .yfinance_source import YFinanceDataSource


@dataclass(frozen=True)
class DemoQuestion:
    """One natural-language request and optional direct-fetch follow-up."""

    query: str
    use_case: str = ""
    preferences: Mapping[str, Any] = field(default_factory=dict)
    fetch_source_id: str = ""
    fetch_endpoint_id: str = ""
    fetch_parameters: Mapping[str, Any] = field(default_factory=dict)


@dataclass
class DataAgentNetworkDemo:
    """Build and exercise the local direct-source network.

    This is the original FinMAS demo harness reduced to one Data Source. There
    is no extra DemoClient, network façade, trace protocol, or replacement
    orchestration object.
    """

    data_user: DataUserPersona | None = None
    data_consultant: DataConsultantPersona | None = None
    data_sources: Mapping[str, YFinanceDataSource] = field(default_factory=dict)
    plaza: Plaza | None = None
    provider: YFinanceProvider | Any | None = None

    def build_local_network(self) -> Mapping[str, Any]:
        """Create the source -> consultant/sync -> user in-process network."""

        if self.data_user and self.data_consultant and self.data_sources and self.plaza:
            return self._network_members()

        plaza = self.plaza or Plaza()
        source = YFinanceDataSource(
            provider=self.provider,
            plaza=plaza,
            auto_register=False,
            name="YFinanceDataSource",
            port=8050,
        )
        source.register()

        consultant = DataConsultantPersona(
            plaza=plaza,
            auto_register=False,
            name="DataConsultant",
            port=8052,
        )
        consultant.register()
        consultant.refresh_source_memory(reason="startup")

        data_user = DataUserPersona(
            plaza=plaza,
            auto_register=False,
            name="DataUser",
            port=8053,
        )
        data_user.register()

        self.plaza = plaza
        self.data_sources = {"yfinance": source}
        self.data_consultant = consultant
        self.data_user = data_user
        return self._network_members()

    def ask(self, question: DemoQuestion) -> dict[str, Any]:
        """Send one natural-language request through Data User to Consultant."""

        if not self.data_user:
            self.build_local_network()
        assert self.data_user is not None
        return self.data_user.get_pulse_data(
            {
                "query": question.query,
                "use_case": question.use_case,
                "preferences": dict(question.preferences),
            },
            pulse_name=DATA_REQUEST_PULSE_NAME,
        )

    def fetch(self, question: DemoQuestion) -> dict[str, Any]:
        """Fetch directly from the source selected after receiving advice."""

        if not question.fetch_source_id or not question.fetch_endpoint_id:
            raise ValueError(
                "fetch_source_id and fetch_endpoint_id are required for a direct fetch"
            )
        if not self.data_user:
            self.build_local_network()
        assert self.data_user is not None
        return self.data_user.get_pulse_data(
            {
                "source_id": question.fetch_source_id,
                "endpoint_id": question.fetch_endpoint_id,
                "parameters": dict(question.fetch_parameters),
            },
            pulse_name=DATA_FETCH_PULSE_NAME,
        )

    def run(self, questions: Sequence[DemoQuestion]) -> tuple[dict[str, Any], ...]:
        """Execute advisory questions and configured direct-fetch follow-ups."""

        self.build_local_network()
        results: list[dict[str, Any]] = []
        for question in questions:
            item: dict[str, Any] = {
                "question": {
                    "query": question.query,
                    "use_case": question.use_case,
                    "preferences": dict(question.preferences),
                },
                "advice": self.ask(question),
            }
            if question.fetch_source_id or question.fetch_endpoint_id:
                item["fetch"] = self.fetch(question)
            results.append(item)
        return tuple(results)

    def _network_members(self) -> Mapping[str, Any]:
        return {
            "data_user": self.data_user,
            "data_consultant": self.data_consultant,
            "data_sources": dict(self.data_sources),
            "plaza": self.plaza,
        }


__all__ = ["DataAgentNetworkDemo", "DemoQuestion"]
