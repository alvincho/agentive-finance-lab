"""HTTP contract tests for the runnable, provider-injected demo surface."""

from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from data_agent_network_demo.app import create_app
from data_agent_network_demo.contracts import MarketDataError


@pytest.fixture
def client(fake_source: object) -> TestClient:
    return TestClient(create_app(source=fake_source))


def test_health_about_network_and_examples_describe_the_real_demo(
    client: TestClient,
) -> None:
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"
    assert health.json()["mode"] == "live-yfinance"
    assert health.json()["provider"] == "yfinance"
    assert health.json()["provider_version"] == "test-double"

    about = client.get("/api/about").json()
    assert set(about["concepts"]) == {"Pit", "Plaza", "Pulser", "Persona"}
    assert "yfinance" in str(about).lower()

    network = client.get("/api/network").json()
    assert len(network["pits"]) == 2
    assert network["plaza"]["mode"] == "single-process in-memory discovery and routing"

    examples = client.get("/api/examples")
    assert examples.status_code == 200
    serialized_examples = str(examples.json()).lower()
    assert "aapl" in serialized_examples
    assert "spy" in serialized_examples
    assert "catalog" not in serialized_examples


def test_run_endpoint_accepts_a_structured_security_comparison(
    client: TestClient,
    fake_source: object,
) -> None:
    response = client.post(
        "/api/run",
        json={
            "primary_symbol": " aapl ",
            "benchmark_symbol": "spy",
            "period": "1mo",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "complete"
    assert payload["request"]["primary_symbol"] == "AAPL"
    assert payload["request"]["benchmark_symbol"] == "SPY"
    assert payload["consultant"]["source"]["provider"] == "yfinance"
    assert fake_source.calls == [("AAPL", "1mo"), ("SPY", "1mo")]


@pytest.mark.parametrize(
    "payload",
    (
        {},
        {"prompt": "Compare AAPL and SPY"},
        {"primary_symbol": "", "benchmark_symbol": "SPY", "period": "1mo"},
        {"primary_symbol": "AAPL SPY", "benchmark_symbol": "SPY", "period": "1mo"},
        {"primary_symbol": "A" * 21, "benchmark_symbol": "SPY", "period": "1mo"},
        {"primary_symbol": "AAPL", "benchmark_symbol": "SPY", "period": "10y"},
        {"primary_symbol": "AAPL", "benchmark_symbol": "aapl", "period": "1mo"},
    ),
)
def test_run_endpoint_rejects_invalid_or_legacy_requests(
    client: TestClient,
    payload: dict[str, str],
) -> None:
    response = client.post("/api/run", json=payload)

    assert response.status_code == 422


def test_handled_yfinance_failure_remains_an_inspectable_demo_result(
    fake_source: object,
) -> None:
    fake_source.failures["SPY"] = MarketDataError(
        symbol="SPY",
        code="no_history",
        message="yfinance returned no daily price history for SPY.",
    )
    client = TestClient(create_app(source=fake_source))

    response = client.post(
        "/api/run",
        json={
            "primary_symbol": "AAPL",
            "benchmark_symbol": "SPY",
            "period": "1mo",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "partial"
    assert response.json()["consultant"]["errors"][0]["code"] == "no_history"


def test_root_serves_the_demo_ui(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Data Agent Network" in response.text
    assert 'id="demo-form"' in response.text
    assert 'name="primary_symbol"' in response.text
    assert 'name="benchmark_symbol"' in response.text
    assert response.text.count('maxlength="20"') == 2
    assert 'id="protocol-blocker"' in response.text
    assert 'window.location.protocol === "file:"' in response.text
    assert "Project background" in response.text
    assert "Prompits Lite" in response.text
    assert "Phemacast Lite" in response.text
    assert all(concept in response.text for concept in ("Pit", "Plaza", "Pulser", "Persona"))
    assert 'id="intro-run-button"' in response.text
    assert "python demos/data-agent-network-demo/run.py" in response.text


def test_default_framework_documentation_routes_are_disabled(client: TestClient) -> None:
    assert client.get("/docs").status_code == 404
    assert client.get("/redoc").status_code == 404
    assert client.get("/openapi.json").status_code == 404
