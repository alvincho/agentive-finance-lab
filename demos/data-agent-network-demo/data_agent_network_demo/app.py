"""FastAPI surface for the Data Agent Network demo and its static UI."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from .catalog import CATALOG, EXAMPLE_PROMPTS
from .workflow import build_network, run_demo


STATIC_DIR = Path(__file__).resolve().parent / "static"


class DemoRequest(BaseModel):
    prompt: str = Field(min_length=8, max_length=1200)
    simulate_consultant_offline: bool = False

    @field_validator("prompt", mode="before")
    @classmethod
    def strip_prompt(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


def create_app() -> FastAPI:
    application = FastAPI(
        title="Agentive Finance Lab — Data Agent Network Demo",
        version="0.1.0",
        description="A deterministic demonstration of PIT, Plaza, Pulser, and Persona collaboration.",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @application.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @application.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "offline-demo"}

    @application.get("/api/about")
    def about() -> dict[str, object]:
        return {
            "name": "Multi-Agent Finance Demos",
            "demo": "Data Agent Network",
            "description": "A small public proof of how specialized Personas can collaborate through discoverable, typed contracts.",
            "concepts": {
                "Pit": "The smallest addressable identity. The name is intentionally not expanded as an acronym.",
                "Plaza": "An in-memory registry, discovery service, and router.",
                "Pulser": "A Pit that advertises named, typed Pulse handlers.",
                "Persona": "A role-aware Pulser with purpose and instructions.",
            },
            "limits": [
                "No live market data, vendor APIs, credentials, LLMs, or investment advice.",
                "No production authentication, durable storage, billing, networking, or fault tolerance.",
                "The lite packages are educational contracts, not drop-in FinMAS replacements.",
            ],
        }

    @application.get("/api/network")
    def network() -> dict[str, object]:
        return build_network().describe()

    @application.get("/api/examples")
    def examples() -> dict[str, object]:
        return {
            "prompts": list(EXAMPLE_PROMPTS),
            "catalog": [product.to_dict() for product in CATALOG],
        }

    @application.post("/api/run")
    def run(request: DemoRequest) -> dict[str, object]:
        return run_demo(
            request.prompt,
            consultant_available=not request.simulate_consultant_offline,
        )

    return application


app = create_app()
