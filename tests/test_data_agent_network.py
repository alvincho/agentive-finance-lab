"""End-to-end behavior of the deterministic two-Persona demo."""

from __future__ import annotations

from data_agent_network_demo.agents import interpret_prompt
from data_agent_network_demo.workflow import build_network, run_demo


PROMPT = "Compare ACME valuation with peer BETA on a reproducible, low-cost basis."


def test_prompt_interpretation_is_explicit_and_deterministic() -> None:
    request = interpret_prompt(PROMPT)

    assert request["needs"] == ["valuation", "peers"]
    assert request["priorities"] == ["low_cost", "reproducible"]
    assert request["instruments"] == ["ACME", "BETA"]


def test_prompt_markers_use_word_boundaries() -> None:
    request = interpret_prompt("Separate ACME corporate earnings from its peer comparison.")

    assert "rates" not in request["needs"]
    assert "peers" in request["needs"]

    low_cost = interpret_prompt("Find cheap daily closes for ACME.")
    assert "low_cost" in low_cost["priorities"]
    assert "valuation" not in low_cost["needs"]


def test_unsupported_need_is_not_coerced_into_catalog_coverage() -> None:
    result = run_demo("I need ESG controversy and carbon-emissions data for ACME.")

    assert result["status"] == "needs-review"
    assert result["request"]["needs"] == ["unclassified"]
    assert result["consultant"]["recommendations"] == []
    assert result["consultant"]["gaps"] == ["unclassified"]
    assert result["answer"]["headline"] == "No catalog product covers the interpreted request."


def test_complete_path_discovers_specialist_and_preserves_one_trace() -> None:
    result = run_demo(PROMPT)

    assert result["status"] == "complete"
    assert result["consultant"]["recommendations"][0]["product_id"] == "demo-company-filings"
    assert result["network"]["dependency_direction"] == (
        "demo -> phemacast-lite -> prompits-lite"
    )

    stages = [event["stage"] for event in result["trace"]]
    assert stages == [
        "client.submit",
        "plaza.route",
        "pulse.execute",
        "persona.interpret",
        "plaza.discover",
        "plaza.matches",
        "plaza.route",
        "pulse.execute",
        "pulse.complete",
        "plaza.return",
        "persona.validate",
        "persona.present",
        "pulse.complete",
        "plaza.return",
    ]
    assert [event["sequence"] for event in result["trace"]] == list(range(1, 15))
    assert result["correlation_id"]


def test_default_question_prefers_sources_available_in_the_demo() -> None:
    result = run_demo(
        "Compare ACME's five-day return with the latest policy-rate move and explain the data caveats."
    )

    recommendations = result["consultant"]["recommendations"]
    assert recommendations[0]["access"] == "no authentication"
    assert recommendations[1]["access"] == "no authentication"


def test_offline_specialist_returns_transparent_degraded_result() -> None:
    result = run_demo(PROMPT, consultant_available=False)

    assert result["status"] == "degraded"
    assert result["consultant"]["recommendations"] == []
    assert result["consultant"]["gaps"] == ["valuation", "peers"]
    assert result["answer"]["caveat"].startswith("No source recommendation was fabricated")
    assert "persona.degraded" in [event["stage"] for event in result["trace"]]


def test_network_registers_both_runtime_personas_with_typed_pulses() -> None:
    network = build_network()
    cards = {card.name: card for card in network.plaza.directory()}

    assert set(cards) == {"Data User", "Data Consultant"}
    assert cards["Data User"].pit_type == "Persona"
    assert cards["Data Consultant"].labels["role"] == "data-consultant"
    assert [item.name for item in cards["Data User"].capabilities] == ["data_request"]
    assert [item.name for item in cards["Data Consultant"].capabilities] == ["data_advice"]
