"""HTTP tests for the copied Data User UI and generic Pulse endpoint."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient
import pytest

from data_agent_network_demo.app import create_app


@pytest.fixture
def client(fake_provider: Any) -> TestClient:
    return TestClient(create_app(provider=fake_provider))


def test_copied_data_user_interface_routes_and_assets_are_served(
    client: TestClient,
) -> None:
    landing = client.get("/")
    data_user = client.get("/data-user")
    demo_alias = client.get("/demos/data-agent-network/")
    single_source = client.get("/demos/data-agent-network/single-source/")
    multiple_sources = client.get("/demos/data-agent-network/multiple-sources/")
    real_data = client.get("/demos/data-agent-network/real-data/")
    landing_stylesheet = client.get("/static/landing.css")
    landing_script = client.get("/static/landing.js")
    landing_flow = client.get("/static/data-agent-single-source-flow-v2.png")
    multiple_sources_flow = client.get(
        "/static/data-agent-multiple-sources-flow.png"
    )
    query_screenshots = [
        client.get("/static/demo-query-price-history.jpg"),
        client.get("/static/demo-query-quote.jpg"),
        client.get("/static/demo-query-company-profile.jpg"),
        client.get("/static/demo-multiple-query-daily-prices.jpg"),
        client.get("/static/demo-multiple-query-macro-series.jpg"),
        client.get("/static/demo-multiple-query-company-profile.jpg"),
    ]
    stylesheet = client.get("/data-user-static/data-user.css")
    script = client.get("/data-user-static/data-user.js")

    assert landing.status_code == 200
    assert data_user.status_code == 200
    assert demo_alias.status_code == 200
    assert single_source.status_code == 200
    assert multiple_sources.status_code == 200
    assert real_data.status_code == 200
    assert data_user.text == demo_alias.text
    assert data_user.text == single_source.text
    assert data_user.text != multiple_sources.text
    assert real_data.text != multiple_sources.text
    assert landing.text != data_user.text
    assert landing_stylesheet.status_code == 200
    assert landing_script.status_code == 200
    assert landing_flow.status_code == 200
    assert landing_flow.headers["content-type"] == "image/png"
    assert multiple_sources_flow.status_code == 200
    assert multiple_sources_flow.headers["content-type"] == "image/png"
    assert all(response.status_code == 200 for response in query_screenshots)
    assert all(response.headers["content-type"] == "image/jpeg" for response in query_screenshots)
    assert stylesheet.status_code == 200
    assert script.status_code == 200

    assert 'id="sourceNetwork"' in data_user.text
    assert 'id="conversation"' in data_user.text
    assert 'id="composer"' in data_user.text
    assert 'id="queryInput"' in data_user.text
    assert 'id="preferencePanel"' in data_user.text
    assert 'id="detailDialog"' in data_user.text
    assert 'class="lab-frame"' in data_user.text
    assert "Agentive Finance Lab" in data_user.text
    assert "Demo 1" in data_user.text
    assert "Data Agent / Single Source" in data_user.text
    assert "Data Agent Network" in data_user.text
    assert 'aria-current="page"' in data_user.text
    assert 'href="/#demos"' in data_user.text
    assert "/data-user-static/data-user.css?v=" in data_user.text
    assert "/data-user-static/data-user.js?v=" in data_user.text
    assert "__DATA_USER_ASSET_VERSION__" not in data_user.text
    assert "__DATA_USER_DEMO_CONFIG__" not in data_user.text
    assert "__DATA_USER_DEMO_CONFIG__" not in multiple_sources.text
    assert "single-source" in data_user.text
    assert "multiple-sources" in multiple_sources.text
    assert "/api/multiple-sources" in multiple_sources.text
    assert "Data Agent / Multiple Sources" in multiple_sources.text
    assert "real-data" in real_data.text
    assert "/api/real-data" in real_data.text
    assert "Data Agent / Real Data" in real_data.text
    assert 'name="ALPHA_VANTAGE_API_KEY"' not in real_data.text
    assert 'name="FRED_API_KEY"' not in real_data.text

    assert 'callPulse("data_request"' in script.text
    assert 'callPulse("data_source_status"' in script.text
    assert 'callPulse("data_spec"' in script.text
    assert 'callPulse("data_fetch"' in script.text
    assert 'apiUrl("pulse")' in script.text
    assert 'apiUrl("data-user/bootstrap")' in script.text
    assert '"no-key"' in script.text
    assert '"alpha-key"' in script.text
    assert '"fred"' in script.text
    assert "demoConfig.enable_live_fetch" in script.text


def test_landing_is_an_accessible_tabbed_framework_guide(
    client: TestClient,
) -> None:
    landing = client.get("/")
    script = client.get("/static/landing.js")

    assert landing.status_code == 200
    assert landing.text.count('role="tab"') == 8
    assert landing.text.count('role="tabpanel"') == 8
    assert landing.text.count('aria-selected="true"') == 1
    assert landing.text.count('aria-selected="false"') == 7
    assert 'role="tablist"' in landing.text

    for panel_id in (
        "purpose",
        "multi-agent",
        "prompits",
        "phemacast",
        "plaza",
        "demos",
        "demos-multiple",
        "demos-real",
    ):
        assert f'aria-controls="{panel_id}"' in landing.text
        assert f'id="{panel_id}"' in landing.text

    assert "MCP" in landing.text
    assert "Skills" in landing.text
    assert "A2A" in landing.text
    assert "UsePractice" in landing.text
    assert "REGISTER · SEARCH · RESOLVE · ROUTE" in landing.text
    assert 'id="topology-description"' in landing.text
    assert "Prompits Plaza centralized coordination topology" in landing.text
    assert "one mandatory global server" in landing.text
    assert 'data-demo-tree' in landing.text
    assert landing.text.count('class="guide-tree__toggle') == 2
    assert 'aria-controls="demo-tree-children"' in landing.text
    assert 'aria-controls="data-agent-tree-children"' in landing.text
    assert 'aria-label="Single Source"' in landing.text
    assert 'aria-label="Multiple Sources"' in landing.text
    assert 'aria-label="Real Data"' in landing.text
    assert "Data Agent / Single Source." in landing.text
    assert "BEFORE THE DIAGRAM · HOW THE DEMO WORKS" in landing.text
    assert "CHAT ≠ FETCH" in landing.text
    assert "THREE OBSERVED RUNS" in landing.text
    assert landing.text.count('class="query-run"') == 6
    assert "demo-query-price-history.jpg" in landing.text
    assert "demo-query-quote.jpg" in landing.text
    assert "demo-query-company-profile.jpg" in landing.text
    assert "demo-multiple-query-daily-prices.jpg" in landing.text
    assert "demo-multiple-query-macro-series.jpg" in landing.text
    assert "demo-multiple-query-company-profile.jpg" in landing.text
    assert 'class="demo-flow"' in landing.text
    assert 'src="/static/data-agent-single-source-flow-v2.png"' in landing.text
    assert 'data-file-src="./data-agent-single-source-flow-v2.png"' in landing.text
    assert 'src="/static/data-agent-multiple-sources-flow.png"' in landing.text
    assert 'data-file-src="./data-agent-multiple-sources-flow.png"' in landing.text
    assert "THREE IMPLEMENTED PHASES" in landing.text
    assert "search: data_availability" in landing.text
    assert "schema / market data" in landing.text
    assert 'href="/demos/data-agent-network/"' in landing.text
    assert 'href="/demos/data-agent-network/multiple-sources/"' in landing.text
    assert 'href="/demos/data-agent-network/real-data/?sample=no-key"' in landing.text
    assert "window.history.pushState" in script.text
    assert "setDisclosure" in script.text
    assert "revealDemoPath" in script.text
    assert "data-file-href" in script.text
    assert 'event.key === "ArrowDown"' in script.text
    assert 'event.key === "Home"' in script.text
    assert 'event.key === "End"' in script.text


def test_bootstrap_reports_consultant_owned_yfinance_catalog_without_provider_io(
    client: TestClient,
    fake_provider: Any,
) -> None:
    response = client.get("/api/data-user/bootstrap")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["agent_name"] == "DataUser"
    assert payload["consultant_configured"] is True
    assert payload["source_catalog"] == {
        **payload["source_catalog"],
        "authority": "data_consultant",
        "pulse_name": "data_source_status",
        "registry": "plaza",
        "party": "attas",
        "pit_type": "DataSource",
        "status": "ready",
        "last_update_error": False,
    }
    assert payload["source_count"] == 1
    assert [source["source_id"] for source in payload["sources"]] == ["yfinance"]
    assert payload["sources"][0]["dataset_count"] == 3
    assert payload["pulses"] == [
        "data_request",
        "data_source_status",
        "data_spec",
        "data_fetch",
    ]
    assert fake_provider.calls == []


def test_generic_pulse_wrapper_runs_advice_spec_and_direct_fetch(
    client: TestClient,
    fake_provider: Any,
) -> None:
    advice = client.post(
        "/api/pulse",
        json={
            "pulse_name": "data_request",
            "input": {"query": "historical daily prices and volume for AAPL"},
        },
    )
    assert advice.status_code == 200
    assert advice.json()["status"] == "success"
    assert advice.json()["result"]["source_count"] == 1
    assert fake_provider.calls == []

    specification = client.post(
        "/api/pulse",
        json={
            "pulse_name": "data_spec",
            "input_data": {
                "source_id": "yfinance",
                "endpoint_id": "yfinance.ticker.fast_info",
            },
        },
    )
    assert specification.status_code == 200
    assert specification.json()["status"] == "success"
    assert specification.json()["result"]["count"] == 1
    assert fake_provider.calls == []

    fetched = client.post(
        "/api/pulse",
        json={
            "pulse_name": "data_fetch",
            "input": {
                "source_id": "yfinance",
                "endpoint_id": "yfinance.ticker.fast_info",
                "parameters": {"symbol": "AAPL"},
            },
        },
    )
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "success"
    assert fetched.json()["result"]["status"] == "completed"
    assert fetched.json()["result"]["canonical_data"]["last_price"] == 230.2
    assert [item["operation"] for item in fake_provider.calls] == [
        "Ticker",
        "fast_info",
    ]


def test_multiple_sources_bootstrap_and_advice_use_three_catalog_agents_without_provider_io(
    client: TestClient,
    fake_provider: Any,
) -> None:
    bootstrap = client.get("/api/multiple-sources/data-user/bootstrap")

    assert bootstrap.status_code == 200
    payload = bootstrap.json()
    assert payload["source_count"] == 3
    assert [source["source_id"] for source in payload["sources"]] == [
        "alpha_vantage",
        "fred",
        "yfinance",
    ]
    assert {
        source["source_id"]: source["dataset_count"]
        for source in payload["sources"]
    } == {"alpha_vantage": 3, "fred": 2, "yfinance": 3}
    assert payload["advice_synthesis"] == {
        "policy": "catalog_rag",
        "llm_used": False,
    }

    advice = client.post(
        "/api/multiple-sources/pulse",
        json={
            "pulse_name": "data_request",
            "input": {
                "query": (
                    "Which sources provide daily AAPL prices and volume, and how "
                    "do their contracts differ?"
                )
            },
        },
    )

    assert advice.status_code == 200
    result = advice.json()["result"]
    assert result["source_count"] == 2
    assert [source["source_id"] for source in result["sources"]] == [
        "yfinance",
        "alpha_vantage",
    ]
    assert fake_provider.calls == []


def test_multiple_sources_live_fetch_requires_source_owned_credentials(
    client: TestClient,
    fake_provider: Any,
) -> None:
    response = client.post(
        "/api/multiple-sources/pulse",
        json={
            "pulse_name": "data_fetch",
            "input": {
                "source_id": "fred",
                "endpoint_id": "fred.fred_series_observations",
                "parameters": {"series_id": "CPIAUCSL"},
            },
        },
    )

    assert response.status_code == 200
    result = response.json()["result"]
    assert result["status"] == "authentication_required"
    assert "source-owned FRED credential" in result["error"]
    assert result["data"] == {}
    assert fake_provider.calls == []


@pytest.mark.parametrize(
    "payload",
    (
        {},
        {"pulse_name": "data_request"},
        {"input": {"query": "history"}},
        {"pulse_name": "unknown", "input": {}},
    ),
)
def test_generic_pulse_wrapper_rejects_invalid_envelopes(
    client: TestClient,
    payload: dict[str, Any],
) -> None:
    assert client.post("/api/pulse", json=payload).status_code == 400


def test_health_reports_the_three_participant_demo(
    client: TestClient,
) -> None:
    health = client.get("/health")

    assert health.status_code == 200
    assert health.json() == {
        "status": "ok",
        "demo": "data-agent-network",
        "participants": 3,
        "sources": 1,
        "provider": "yfinance",
    }


def test_multiple_sources_health_reports_five_participants(
    client: TestClient,
) -> None:
    health = client.get("/api/multiple-sources/health")

    assert health.status_code == 200
    assert health.json() == {
        "status": "ok",
        "demo": "data-agent-network-multiple-sources",
        "participants": 5,
        "sources": 3,
        "providers": ["yfinance", "alpha_vantage", "fred"],
    }
