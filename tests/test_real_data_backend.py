"""Backend and server-environment coverage for Demo 3 real data access."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from data_agent_network_demo.app import (
    MULTIPLE_SOURCES_UI_CONFIG,
    REAL_DATA_UI_CONFIG,
    _load_repo_environment,
    create_app,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class RecordingProviderClient:
    """Deterministic provider boundary with Alpha Vantage and FRED shapes."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def get_json(self, url: str, *, params: dict[str, Any]) -> dict[str, Any]:
        self.calls.append({"url": url, "params": dict(params)})
        if "alphavantage" in url:
            return {
                "Meta Data": {"2. Symbol": params["symbol"]},
                "Time Series (Daily)": {
                    "2026-08-26": {
                        "1. open": "228.30",
                        "2. high": "231.00",
                        "3. low": "227.90",
                        "4. close": "230.20",
                        "5. volume": "42250000",
                    }
                },
            }
        return {
            "observations": [
                {
                    "realtime_start": "2026-08-27",
                    "realtime_end": "2026-08-27",
                    "date": "2026-07-01",
                    "value": "322.132",
                }
            ]
        }


def post_fetch(
    client: TestClient,
    *,
    source_id: str,
    endpoint_id: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    response = client.post(
        "/api/real-data/pulse",
        json={
            "pulse_name": "data_fetch",
            "input": {
                "source_id": source_id,
                "endpoint_id": endpoint_id,
                "parameters": parameters,
            },
        },
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    return response.json()["result"]


def test_repo_env_template_is_safe_and_loader_does_not_override_process_values(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    project = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    ignored = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    example = (REPO_ROOT / ".env.example").read_text(encoding="utf-8")

    assert '"python-dotenv>=1.0,<2"' in project
    assert ".env" in ignored
    assert "ALPHA_VANTAGE_API_KEY=" in example
    assert "FRED_API_KEY=" in example
    assert "secret" not in example.lower()

    env_file = tmp_path / ".env"
    env_file.write_text(
        "ALPHA_VANTAGE_API_KEY=alpha-from-file\n"
        "FRED_API_KEY=fred-from-file\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    monkeypatch.setenv("FRED_API_KEY", "fred-from-process")

    _load_repo_environment(env_file)

    assert os.environ["ALPHA_VANTAGE_API_KEY"] == "alpha-from-file"
    assert os.environ["FRED_API_KEY"] == "fred-from-process"


def test_real_data_routes_use_a_third_isolated_existing_network(
    fake_provider: Any,
    monkeypatch: Any,
) -> None:
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    application = create_app(provider=fake_provider)
    client = TestClient(application)

    page = client.get("/demos/data-agent-network/real-data/")
    health = client.get("/api/real-data/health")
    bootstrap = client.get("/api/real-data/data-user/bootstrap")

    assert page.status_code == 200
    assert "Data Agent / Real Data" in page.text
    assert "real-data" in page.text
    assert "/api/real-data" in page.text
    assert REAL_DATA_UI_CONFIG == {
        "slug": "real-data",
        "number": "3",
        "title": "Data Agent / Real Data",
        "mode": "real-data",
        "enable_live_fetch": True,
        "api_base": "/api/real-data",
    }
    assert MULTIPLE_SOURCES_UI_CONFIG["enable_live_fetch"] is False
    assert application.state.real_data_demo.__class__ is (
        application.state.multiple_demo.__class__
    )
    assert application.state.real_data_demo is not application.state.multiple_demo
    assert application.state.real_data_demo.plaza is not application.state.multiple_demo.plaza
    assert health.json() == {
        "status": "ok",
        "demo": "data-agent-network-real-data",
        "participants": 5,
        "sources": 3,
        "providers": ["yfinance", "alpha_vantage", "fred"],
    }

    sources = {
        source["source_id"]: source for source in bootstrap.json()["sources"]
    }
    assert sources["yfinance"] | {
        "credential_required": False,
        "credential_configured": False,
        "fetch_ready": True,
        "attempt_ready": True,
    } == sources["yfinance"]
    for source_id in ("alpha_vantage", "fred"):
        assert sources[source_id]["credential_required"] is True
        assert sources[source_id]["credential_configured"] is False
        assert sources[source_id]["fetch_ready"] is False
        assert sources[source_id]["attempt_ready"] is False


def test_keyless_real_data_fetch_succeeds_for_yfinance_and_fails_explicitly_for_alpha(
    fake_provider: Any,
    monkeypatch: Any,
) -> None:
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    provider_client = RecordingProviderClient()
    client = TestClient(
        create_app(
            provider=fake_provider,
            alpha_vantage_http_client=provider_client,
            fred_http_client=provider_client,
        )
    )

    yfinance = post_fetch(
        client,
        source_id="yfinance",
        endpoint_id="yfinance.ticker.history",
        parameters={"symbol": "AAPL", "period": "1mo", "interval": "1d"},
    )
    specification = client.post(
        "/api/real-data/pulse",
        json={
            "pulse_name": "data_spec",
            "input": {
                "source_id": "alpha_vantage",
                "endpoint_id": "alpha_vantage.time_series_daily",
            },
        },
    ).json()["result"]["endpoints"][0]
    alpha = post_fetch(
        client,
        source_id="alpha_vantage",
        endpoint_id="alpha_vantage.time_series_daily",
        parameters={"symbol": "AAPL", "outputsize": "compact"},
    )

    assert yfinance["status"] == "completed"
    assert len(yfinance["canonical_data"]["items"]) == 3
    assert specification["executable"] is True
    assert specification["credential_required"] is True
    assert specification["credential_configured"] is False
    assert specification["fetch_ready"] is False
    assert specification["attempt_ready"] is False
    assert alpha["status"] == "authentication_required"
    assert "source-owned Alpha Vantage credential" in alpha["error"]
    assert alpha["data"] == {}
    assert provider_client.calls == []


def test_configured_real_data_fetches_alpha_and_fred_without_secret_leaks(
    fake_provider: Any,
) -> None:
    provider_client = RecordingProviderClient()
    client = TestClient(
        create_app(
            provider=fake_provider,
            alpha_vantage_http_client=provider_client,
            fred_http_client=provider_client,
            alpha_vantage_api_key="alpha-server-secret",
            fred_api_key="fred-server-secret",
        )
    )

    alpha = post_fetch(
        client,
        source_id="alpha_vantage",
        endpoint_id="alpha_vantage.time_series_daily",
        parameters={"symbol": "AAPL", "outputsize": "compact"},
    )
    fred = post_fetch(
        client,
        source_id="fred",
        endpoint_id="fred.fred_series_observations",
        parameters={"series_id": "CPIAUCSL", "limit": 12, "sort_order": "desc"},
    )
    refreshed_sources = {
        source["source_id"]: source
        for source in client.get("/api/real-data/data-user/bootstrap").json()["sources"]
    }

    assert alpha["status"] == "completed"
    assert alpha["canonical_data"]["Time Series (Daily)"]["2026-08-26"] == {
        "open": "228.30",
        "high": "231.00",
        "low": "227.90",
        "close": "230.20",
        "volume": "42250000",
    }
    assert fred["status"] == "completed"
    assert fred["canonical_data"]["observations"][0]["timestamp"] == "2026-07-01"
    for source_id in ("alpha_vantage", "fred"):
        assert refreshed_sources[source_id]["access_status"] == "ready"
        assert refreshed_sources[source_id]["verification"] == "verified"
        assert refreshed_sources[source_id]["verified_at"]
        assert refreshed_sources[source_id]["fetch_ready"] is True
    assert [call["url"] for call in provider_client.calls] == [
        "https://www.alphavantage.co/query",
        "https://api.stlouisfed.org/fred/series/observations",
    ]
    assert provider_client.calls[1]["params"] | {
        "series_id": "CPIAUCSL",
        "limit": 12,
        "sort_order": "desc",
        "api_key": "fred-server-secret",
    } == provider_client.calls[1]["params"]
    serialized = json.dumps({"alpha": alpha, "fred": fred})
    assert "alpha-server-secret" not in serialized
    assert "fred-server-secret" not in serialized
