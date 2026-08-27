"""Reduced single- and multiple-source FinMAS Data Agent Network demos."""

from .agents import DataConsultant, DataConsultantPersona, DataUser, DataUserPersona
from .multiple_sources_workflow import MultipleSourceDataAgentNetworkDemo
from .provider_sources import AlphaVantageDataSource, FREDDataSource
from .workflow import DataAgentNetworkDemo, DemoQuestion
from .yfinance_source import YFinanceDataSource, YFinanceSource

__all__ = [
    "AlphaVantageDataSource",
    "DataAgentNetworkDemo",
    "DataConsultant",
    "DataConsultantPersona",
    "DataUser",
    "DataUserPersona",
    "DemoQuestion",
    "FREDDataSource",
    "MultipleSourceDataAgentNetworkDemo",
    "YFinanceDataSource",
    "YFinanceSource",
]
