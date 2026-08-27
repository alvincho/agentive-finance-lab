"""FastAPI host for the reduced original Data User Persona interface."""

from __future__ import annotations

from collections.abc import Mapping
from html import escape
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.concurrency import run_in_threadpool

from .multiple_sources_workflow import MultipleSourceDataAgentNetworkDemo
from .workflow import DataAgentNetworkDemo


PACKAGE_DIR = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_DIR.parents[2]
LANDING_STATIC_DIR = PACKAGE_DIR / "static"
DATA_USER_UI_DIR = PACKAGE_DIR / "ui"
DATA_USER_STATIC_DIR = DATA_USER_UI_DIR / "static"


def _load_repo_environment(path: Path | None = None) -> bool:
    """Load optional local provider keys without replacing process settings."""

    return bool(load_dotenv(path or REPO_ROOT / ".env", override=False))


_load_repo_environment()


def _asset_version() -> str:
    mtimes = [
        path.stat().st_mtime_ns
        for path in (
            DATA_USER_UI_DIR / "index.html",
            DATA_USER_STATIC_DIR / "data-user.css",
            DATA_USER_STATIC_DIR / "data-user.js",
        )
        if path.exists()
    ]
    return str(max(mtimes, default=0))


SINGLE_SOURCE_UI_CONFIG: dict[str, Any] = {
    "slug": "single-source",
    "number": "1",
    "title": "Data Agent / Single Source",
    "api_base": "/api",
}

MULTIPLE_SOURCES_UI_CONFIG: dict[str, Any] = {
    "slug": "multiple-sources",
    "number": "2",
    "title": "Data Agent / Multiple Sources",
    "api_base": "/api/multiple-sources",
    "enable_live_fetch": False,
}

REAL_DATA_UI_CONFIG: dict[str, Any] = {
    "slug": "real-data",
    "number": "3",
    "title": "Data Agent / Real Data",
    "mode": "real-data",
    "enable_live_fetch": True,
    "api_base": "/api/real-data",
}


def _render_data_user_ui(config: Mapping[str, Any]) -> str:
    """Render the one copied Data User interface for a selected demo network."""

    serialized_config = escape(
        json.dumps(dict(config), ensure_ascii=True, separators=(",", ":")),
        quote=True,
    )
    return (
        (DATA_USER_UI_DIR / "index.html")
        .read_text(encoding="utf-8")
        .replace("__DATA_USER_ASSET_VERSION__", _asset_version())
        .replace("__DATA_USER_DEMO_CONFIG__", serialized_config)
    )


def create_app(
    *,
    provider: Any | None = None,
    alpha_vantage_http_client: Any | None = None,
    fred_http_client: Any | None = None,
    alpha_vantage_api_key: str | None = None,
    fred_api_key: str | None = None,
) -> FastAPI:
    """Build three reduced Data Agent Network examples in isolated Plazas."""

    demo = DataAgentNetworkDemo(provider=provider)
    demo.build_local_network()
    assert demo.data_user is not None
    assert demo.data_consultant is not None
    assert demo.plaza is not None

    multiple_demo = MultipleSourceDataAgentNetworkDemo(
        provider=provider,
        alpha_vantage_http_client=alpha_vantage_http_client,
        fred_http_client=fred_http_client,
        alpha_vantage_api_key=alpha_vantage_api_key,
        fred_api_key=fred_api_key,
    )
    multiple_demo.build_local_network()
    assert multiple_demo.data_user is not None
    assert multiple_demo.data_consultant is not None
    assert multiple_demo.plaza is not None

    real_data_demo = MultipleSourceDataAgentNetworkDemo(
        provider=provider,
        alpha_vantage_http_client=alpha_vantage_http_client,
        fred_http_client=fred_http_client,
        alpha_vantage_api_key=alpha_vantage_api_key,
        fred_api_key=fred_api_key,
    )
    real_data_demo.build_local_network()
    assert real_data_demo.data_user is not None
    assert real_data_demo.data_consultant is not None
    assert real_data_demo.plaza is not None

    application = FastAPI(
        title="Agentive Finance Lab — Data Agent Network Demo",
        version="0.5.0",
        description=(
            "Reduced FinMAS Data Agent Network examples for source discovery, "
            "comparison, and direct live data access."
        ),
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.state.demo = demo
    application.state.data_user = demo.data_user
    application.state.multiple_demo = multiple_demo
    application.state.multiple_data_user = multiple_demo.data_user
    application.state.real_data_demo = real_data_demo
    application.state.real_data_user = real_data_demo.data_user
    application.mount(
        "/static",
        StaticFiles(directory=LANDING_STATIC_DIR),
        name="landing_static",
    )
    application.mount(
        "/data-user-static",
        StaticFiles(directory=DATA_USER_STATIC_DIR),
        name="data_user_static",
    )

    @application.get("/", include_in_schema=False)
    def landing_page() -> FileResponse:
        return FileResponse(LANDING_STATIC_DIR / "index.html")

    @application.get("/demos/data-agent-network", include_in_schema=False)
    @application.get("/demos/data-agent-network/", include_in_schema=False)
    @application.get("/demos/data-agent-network/single-source", include_in_schema=False)
    @application.get("/demos/data-agent-network/single-source/", include_in_schema=False)
    @application.get("/data-user", include_in_schema=False)
    def data_user_ui() -> HTMLResponse:
        return HTMLResponse(
            _render_data_user_ui(SINGLE_SOURCE_UI_CONFIG),
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"
            },
        )

    @application.get(
        "/demos/data-agent-network/multiple-sources",
        include_in_schema=False,
    )
    @application.get(
        "/demos/data-agent-network/multiple-sources/",
        include_in_schema=False,
    )
    def multiple_sources_data_user_ui() -> HTMLResponse:
        return HTMLResponse(
            _render_data_user_ui(MULTIPLE_SOURCES_UI_CONFIG),
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"
            },
        )

    @application.get(
        "/demos/data-agent-network/real-data",
        include_in_schema=False,
    )
    @application.get(
        "/demos/data-agent-network/real-data/",
        include_in_schema=False,
    )
    def real_data_user_ui() -> HTMLResponse:
        return HTMLResponse(
            _render_data_user_ui(REAL_DATA_UI_CONFIG),
            headers={
                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"
            },
        )

    @application.get("/favicon.ico", include_in_schema=False)
    def favicon() -> FileResponse:
        return FileResponse(LANDING_STATIC_DIR / "favicon.svg")

    @application.get("/health")
    def health() -> dict[str, Any]:
        return _health_payload(
            demo,
            demo_name="data-agent-network",
            providers=["yfinance"],
        )

    @application.get("/api/multiple-sources/health")
    def multiple_sources_health() -> dict[str, Any]:
        return _health_payload(
            multiple_demo,
            demo_name="data-agent-network-multiple-sources",
            providers=["yfinance", "alpha_vantage", "fred"],
        )

    @application.get("/api/real-data/health")
    def real_data_health() -> dict[str, Any]:
        return _health_payload(
            real_data_demo,
            demo_name="data-agent-network-real-data",
            providers=["yfinance", "alpha_vantage", "fred"],
        )

    @application.get("/api/data-user/bootstrap")
    async def data_user_bootstrap() -> dict[str, Any]:
        return await _bootstrap_payload(demo)

    @application.get("/api/multiple-sources/data-user/bootstrap")
    async def multiple_sources_data_user_bootstrap() -> dict[str, Any]:
        return await _bootstrap_payload(multiple_demo)

    @application.get("/api/real-data/data-user/bootstrap")
    async def real_data_user_bootstrap() -> dict[str, Any]:
        return await _bootstrap_payload(
            real_data_demo,
            refresh_source_memory=True,
        )

    @application.post("/api/pulse")
    async def run_data_user_pulse(request: Request) -> dict[str, Any]:
        return await _run_data_user_pulse(request, demo)

    @application.post("/api/multiple-sources/pulse")
    async def run_multiple_sources_data_user_pulse(
        request: Request,
    ) -> dict[str, Any]:
        return await _run_data_user_pulse(request, multiple_demo)

    @application.post("/api/real-data/pulse")
    async def run_real_data_user_pulse(request: Request) -> dict[str, Any]:
        return await _run_data_user_pulse(request, real_data_demo)

    return application


async def _bootstrap_payload(
    demo: Any,
    *,
    refresh_source_memory: bool = False,
) -> dict[str, Any]:
    if refresh_source_memory:
        await run_in_threadpool(
            demo.data_consultant.refresh_source_memory,
            reason="real-data-bootstrap",
        )
    catalog_status = await run_in_threadpool(
        demo.data_user.current_data_source_status
    )
    sources: list[dict[str, Any]] = []
    for definition in demo.data_user.registered_data_sources(catalog_status):
        source_id = str(
            definition.get("source_id")
            or definition.get("id")
            or definition.get("name")
            or ""
        ).strip()
        if not source_id:
            continue
        connectivity = (
            dict(definition.get("connectivity") or {})
            if isinstance(definition.get("connectivity"), Mapping)
            else {}
        )
        data_access = (
            dict(connectivity.get("data_access") or {})
            if isinstance(connectivity.get("data_access"), Mapping)
            else {}
        )
        sources.append(
            {
                "source_id": source_id,
                "source_name": str(
                    definition.get("source_name")
                    or definition.get("name")
                    or source_id
                ),
                "provider": str(definition.get("provider") or ""),
                "configured": bool(connectivity.get("address")),
                "available": bool(definition.get("available")),
                "connection_status": str(connectivity.get("status") or ""),
                "credential_required": bool(
                    data_access.get("credential_required")
                ),
                "credential_configured": bool(
                    data_access.get("credential_configured")
                ),
                "fetch_ready": bool(data_access.get("fetch_ready")),
                "attempt_ready": bool(data_access.get("attempt_ready")),
                "access_status": str(data_access.get("status") or ""),
                "verification": str(data_access.get("verification") or ""),
                "verified_at": str(data_access.get("verified_at") or ""),
                "access_reason": str(data_access.get("reason") or ""),
                "dataset_count": int(
                    definition.get("dataset_count")
                    or definition.get("endpoint_count")
                    or len(definition.get("datasets") or [])
                ),
                "last_update_at": str(
                    definition.get("last_update_at")
                    or catalog_status.get("latest_update_at")
                    or ""
                ),
                "last_update_error": bool(definition.get("last_update_error")),
            }
        )
    discovery = (
        dict(catalog_status.get("discovery") or {})
        if isinstance(catalog_status.get("discovery"), Mapping)
        else {}
    )
    consultant_configured = bool(
        demo.data_user.search(
            pit_type="Persona",
            party="attas",
            tag="data-consultant",
        )
    )
    return {
        "status": "ready",
        "agent_name": demo.data_user.name,
        "consultant_configured": consultant_configured,
        "source_catalog": {
            "authority": "data_consultant",
            "pulse_name": "data_source_status",
            "registry": str(discovery.get("provider") or "plaza"),
            "party": str(discovery.get("party") or "attas"),
            "pit_type": str(discovery.get("pit_type") or "DataSource"),
            "status": str(catalog_status.get("status") or "empty"),
            "as_of": str(catalog_status.get("as_of") or ""),
            "last_update_error": bool(catalog_status.get("last_update_error")),
        },
        "advice_synthesis": {
            "policy": "catalog_rag",
            "llm_used": False,
        },
        "source_count": len(sources),
        "sources": sources,
        "pulses": [
            "data_request",
            "data_source_status",
            "data_spec",
            "data_fetch",
        ],
    }


async def _run_data_user_pulse(request: Request, demo: Any) -> dict[str, Any]:
    payload = await request.json()
    if not isinstance(payload, Mapping):
        raise HTTPException(
            status_code=400,
            detail="Pulse payload must be a JSON object.",
        )
    input_data = payload.get("input")
    if not isinstance(input_data, Mapping):
        input_data = payload.get("input_data")
    if not isinstance(input_data, Mapping):
        raise HTTPException(
            status_code=400,
            detail="Pulse input must be a JSON object.",
        )
    pulse_name = str(payload.get("pulse_name") or "").strip()
    if not pulse_name:
        raise HTTPException(status_code=400, detail="pulse_name is required.")
    supported_names = {
        str(item.get("pulse_name") or item.get("name") or "")
        for item in demo.data_user.supported_pulses
    }
    if pulse_name not in supported_names:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported Data User Pulse: {pulse_name}",
        )
    result = await run_in_threadpool(
        demo.data_user.get_pulse_data,
        dict(input_data),
        pulse_name,
    )
    return {"status": "success", "result": result}


def _health_payload(
    demo: Any,
    *,
    demo_name: str,
    providers: list[str],
) -> dict[str, Any]:
    status = demo.data_user.current_data_source_status()
    payload: dict[str, Any] = {
        "status": "ok",
        "demo": demo_name,
        "participants": len(demo.plaza.directory()),
        "sources": len(status.get("sources") or []),
    }
    if len(providers) == 1:
        payload["provider"] = providers[0]
    else:
        payload["providers"] = providers
    return payload


app = create_app()


__all__ = [
    "MULTIPLE_SOURCES_UI_CONFIG",
    "REAL_DATA_UI_CONFIG",
    "SINGLE_SOURCE_UI_CONFIG",
    "app",
    "create_app",
]
