"""Behavior copied from Phemacast Pulser and Persona."""

from __future__ import annotations

from phemacast_lite import Persona, Pulser, RAGPersona, pulse_runtime
from prompits_lite import BaseAgent, Plaza, StandbyAgent, directory_runtime


CALCULATE_PULSE = {
    "name": "calculate",
    "pulse_name": "calculate",
    "pulse_address": "plaza://pulse/calculate",
    "description": "Double one integer.",
    "tags": ["fixture"],
    "input_schema": {
        "type": "object",
        "properties": {"value": {"type": "integer"}},
        "required": ["value"],
    },
    "output_schema": {
        "type": "object",
        "properties": {"result": {"type": "integer"}},
        "required": ["result"],
    },
}


class CalculatorPulser(Pulser):
    def __init__(self, **kwargs) -> None:
        super().__init__(
            name="Calculator",
            supported_pulses=[CALCULATE_PULSE],
            **kwargs,
        )

    def fetch_pulse_payload(self, pulse_name, input_data, pulse_definition):
        assert pulse_name == "calculate"
        assert pulse_definition["pulse_address"] == "plaza://pulse/calculate"
        return {"result": int(input_data["value"]) * 2}


def test_pulser_keeps_dict_supported_pulses_and_get_pulse_data_practice() -> None:
    pulser = CalculatorPulser(auto_register=False)

    assert isinstance(pulser, BaseAgent)
    assert isinstance(pulser, StandbyAgent)
    assert pulser.agent_card["pit_type"] == "Pulser"
    assert isinstance(pulser.supported_pulses, list)
    assert all(isinstance(item, dict) for item in pulser.supported_pulses)
    assert pulser.supported_pulses[0]["name"] == "calculate"
    assert pulser.supported_pulses[0]["pulse_name"] == "calculate"
    assert pulser.supported_pulses[0]["pulse_id"] == "urn:plaza:pulse:calculate"
    assert pulser.agent_card["meta"]["supported_pulses"] == pulser.supported_pulses
    assert any(
        practice["id"] == "get_pulse_data"
        for practice in pulser.agent_card["practices"]
    )
    assert pulser.get_pulse_data({"value": 3}, pulse_name="calculate") == {
        "result": 6
    }


def test_remote_get_pulse_data_uses_plaza_and_use_practice() -> None:
    plaza = Plaza()
    caller = Pulser(
        name="Caller",
        plaza_url=plaza,
        supported_pulses=[
            {
                "name": "request",
                "pulse_name": "request",
                "pulse_address": "plaza://pulse/request",
            }
        ],
    )
    calculator = CalculatorPulser(plaza_url=plaza)

    matches = caller.search(pit_type="Pulser", pulse_name="calculate")
    result = caller.UsePractice(
        "get_pulse_data",
        {"pulse_name": "calculate", "params": {"value": 4}},
        pit_address=matches[0]["card"]["pit_address"],
    )

    assert len(matches) == 1
    assert matches[0]["name"] == calculator.name
    assert result == {"result": 8}


def test_persona_is_only_a_profiled_pulser_with_original_plaza_identity() -> None:
    plaza = Plaza()
    persona = RAGPersona(
        config={
            "name": "Reviewer",
            "persona": {
                "name": "Reviewer",
                "style": "skeptical and concise",
                "preferences": "cite source contracts",
            },
            "supported_pulses": [
                {
                    "name": "review",
                    "pulse_name": "review",
                    "pulse_address": "plaza://pulse/review",
                }
            ],
        },
        plaza_url=plaza,
    )

    assert isinstance(persona, Persona)
    assert isinstance(persona, Pulser)
    assert persona.persona_profile["style"] == "skeptical and concise"
    assert persona.agent_card["role"] == "persona"
    assert persona.agent_card["pit_type"] == "Persona"
    assert persona.agent_card["meta"]["persona"]["name"] == "Reviewer"
    assert persona.search(pit_type="Persona")[0]["name"] == "Reviewer"


def test_pulse_runtime_is_the_original_thin_prompits_wrapper() -> None:
    assert (
        pulse_runtime.PULSE_RUNTIME_VERSION
        == directory_runtime.DIRECTORY_RUNTIME_VERSION
    )
    assert (
        pulse_runtime.build_pulse_definition
        is directory_runtime.build_pulse_definition
    )
    assert pulse_runtime.derive_pulse_id is directory_runtime.derive_pulse_id
    assert (
        pulse_runtime.normalize_runtime_pulse_entry
        is directory_runtime.normalize_runtime_pulse_entry
    )
    assert (
        pulse_runtime.normalize_pulse_pair_entry
        is directory_runtime.normalize_pulse_pair_entry
    )
    assert pulse_runtime.__all__ == [
        "DIRECTORY_RUNTIME_VERSION",
        "PULSE_RUNTIME_VERSION",
        "JsonObject",
        "build_pulse_definition",
        "derive_pulse_id",
        "normalize_pulse_pair_entry",
        "normalize_runtime_pulse_entry",
    ]


def test_generic_directory_runtime_preserves_original_pulse_semantics() -> None:
    pulse = {
        "resource_id": "urn:plaza:pulse:market.historical_data",
        "name": "historical_data",
        "pulse_address": "plaza://pulse/market/historical_data",
        "description": "Retrieve historical market data.",
        "input_schema": {
            "type": "object",
            "properties": {"symbol": {"type": "string"}},
            "required": ["symbol"],
        },
        "output_schema": {
            "type": "object",
            "properties": {"rows": {"type": "array"}},
        },
        "pricing": {"plaza_points": 7},
        "extensions": {"source": "yfinance"},
        "test_data": {"symbol": "AAPL"},
    }

    runtime = pulse_runtime.normalize_runtime_pulse_entry(pulse)
    pair = pulse_runtime.normalize_pulse_pair_entry(
        pulse,
        pulser_id="urn:plaza:pit:data-consultant",
        pulser_name="Data Consultant",
        pulser_address="plaza://pit/data-consultant",
    )

    assert runtime["pulse_id"] == pulse["resource_id"]
    assert runtime["pulse_definition"]["id"] == pulse["resource_id"]
    assert runtime["pulse_definition"]["extensions"] == {
        "source": "yfinance"
    }
    assert runtime["interface"]["request_schema"] == pulse["input_schema"]
    assert runtime["interface"]["response_schema"] == pulse["output_schema"]
    assert runtime["cost_points"] == 7
    assert runtime["pricing"] == {"plaza_points": 7, "unit": "call"}
    assert runtime["cost_calculation"] == {
        "type": "fixed",
        "points": 7,
        "currency": "plaza_point",
        "unit": "call",
    }
    assert pair["pulser_id"] == "urn:plaza:pit:data-consultant"
    assert pair["pulser_name"] == "Data Consultant"
    assert pair["pulser_address"] == "plaza://pit/data-consultant"
    assert pair["pulse_definition"]["test_data"] == {"symbol": "AAPL"}
