"""HTTP contract tests for the runnable demo surface."""

from __future__ import annotations

from fastapi.testclient import TestClient

from data_agent_network_demo.app import create_app


client = TestClient(create_app())


def test_health_about_and_network_metadata() -> None:
    assert client.get("/health").json() == {"status": "ok", "mode": "offline-demo"}

    about = client.get("/api/about").json()
    assert set(about["concepts"]) == {"Pit", "Plaza", "Pulser", "Persona"}

    network = client.get("/api/network").json()
    assert len(network["pits"]) == 2
    assert network["plaza"]["mode"] == "in-memory demo registry"


def test_run_endpoint_returns_complete_and_degraded_paths() -> None:
    prompt = "Design a reproducible volatility check for ACME using daily closes."
    complete = client.post("/api/run", json={"prompt": prompt})
    degraded = client.post(
        "/api/run",
        json={"prompt": prompt, "simulate_consultant_offline": True},
    )

    assert complete.status_code == 200
    assert complete.json()["status"] == "complete"
    assert degraded.status_code == 200
    assert degraded.json()["status"] == "degraded"


def test_run_endpoint_validates_prompt_length() -> None:
    response = client.post("/api/run", json={"prompt": "short"})

    assert response.status_code == 422

    whitespace = client.post("/api/run", json={"prompt": "        "})
    assert whitespace.status_code == 422


def test_root_serves_the_demo_ui() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Data Agent Network" in response.text
    assert 'id="demo-form"' in response.text


def test_default_framework_documentation_routes_are_disabled() -> None:
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404
