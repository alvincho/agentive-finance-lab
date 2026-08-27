"""Multiple-source reduction of the original Data Agent Network harness."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from prompits_lite import Plaza

from .agents import DataConsultantPersona, DataUserPersona
from .provider_sources import AlphaVantageDataSource, FREDDataSource
from .workflow import DataAgentNetworkDemo
from .yfinance_source import YFinanceDataSource


@dataclass
class MultipleSourceDataAgentNetworkDemo(DataAgentNetworkDemo):
    """Build the reduced five-participant Data Agent Network.

    The workflow is unchanged from the single-source demo: Data Sources
    register with Plaza first, the Data Consultant registers and synchronizes
    each source through ``data_availability``, then the Data User registers.
    Advice remains an offline search of that synchronized catalog.  A selected
    source receives ``data_spec`` or ``data_fetch`` directly from Data User.
    """

    data_sources: Mapping[str, Any] = field(default_factory=dict)
    alpha_vantage_http_client: Any | None = None
    fred_http_client: Any | None = None
    alpha_vantage_api_key: str | None = None
    fred_api_key: str | None = None

    def build_local_network(self) -> Mapping[str, Any]:
        """Create source trio -> consultant/sync -> user in one private Plaza."""

        if self.data_user and self.data_consultant and self.data_sources and self.plaza:
            return self._network_members()

        plaza = self.plaza or Plaza()

        yfinance_source = YFinanceDataSource(
            provider=self.provider,
            plaza=plaza,
            auto_register=False,
            name="YFinanceDataSource",
            port=8050,
        )
        yfinance_source.register()

        alpha_vantage_source = AlphaVantageDataSource(
            http_client=self.alpha_vantage_http_client,
            api_key=self.alpha_vantage_api_key,
            plaza=plaza,
            auto_register=False,
            name="AlphaVantageDataSource",
            port=8051,
        )
        alpha_vantage_source.register()

        fred_source = FREDDataSource(
            http_client=self.fred_http_client,
            api_key=self.fred_api_key,
            plaza=plaza,
            auto_register=False,
            name="FREDDataSource",
            port=8054,
        )
        fred_source.register()

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
        self.data_sources = {
            "yfinance": yfinance_source,
            "alpha_vantage": alpha_vantage_source,
            "fred": fred_source,
        }
        self.data_consultant = consultant
        self.data_user = data_user
        return self._network_members()


__all__ = ["MultipleSourceDataAgentNetworkDemo"]
