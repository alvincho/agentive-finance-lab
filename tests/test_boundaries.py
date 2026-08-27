"""Mechanical guardrails for the copied Lite layers and provider boundaries."""

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPITS_ROOT = REPO_ROOT / "prompits-lite" / "prompits_lite"
PHEMACAST_ROOT = REPO_ROOT / "phemacast-lite" / "phemacast_lite"
DEMO_ROOT = (
    REPO_ROOT
    / "demos"
    / "data-agent-network-demo"
    / "data_agent_network_demo"
)


def python_files(path: Path) -> list[Path]:
    return sorted(
        source
        for source in path.rglob("*.py")
        if " " not in source.name and "__pycache__" not in source.parts
    )


def imported_roots(path: Path) -> set[str]:
    roots: set[str] = set()
    for source_file in python_files(path):
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".", 1)[0])
    return roots


def importers_of(path: Path, module_root: str) -> set[Path]:
    result: set[Path] = set()
    for source_file in python_files(path):
        if module_root in imported_roots_for_file(source_file):
            result.add(source_file.relative_to(DEMO_ROOT))
    return result


def imported_roots_for_file(source_file: Path) -> set[str]:
    roots: set[str] = set()
    tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".", 1)[0])
    return roots


def test_dependency_direction_has_no_reverse_or_original_repository_imports() -> None:
    original_packages = {"prompits", "phemacast", "attas"}

    assert imported_roots(PROMPITS_ROOT).isdisjoint(
        {"phemacast_lite", "data_agent_network_demo", *original_packages}
    )
    assert imported_roots(PHEMACAST_ROOT).isdisjoint(
        {"data_agent_network_demo", *original_packages}
    )
    assert imported_roots(DEMO_ROOT).isdisjoint(original_packages)


def test_financial_provider_dependencies_stay_inside_data_source_modules() -> None:
    assert importers_of(DEMO_ROOT, "yfinance") == {Path("yfinance_source.py")}
    assert importers_of(DEMO_ROOT, "urllib") == {Path("provider_sources.py")}
    assert imported_roots(DEMO_ROOT).isdisjoint(
        {
            "alpaca",
            "alpha_vantage",
            "fredapi",
            "pandas_datareader",
            "polygon",
            "requests",
        }
    )
    project_config = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '"yfinance==1.6.0"' in project_config


def test_browser_keeps_no_durable_network_or_agent_state() -> None:
    browser_sources = [
        *DEMO_ROOT.joinpath("static").glob("*.js"),
        *DEMO_ROOT.joinpath("ui", "static").glob("*.js"),
    ]
    browser_text = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(browser_sources)
    )

    assert browser_sources
    for forbidden in ("localStorage", "sessionStorage", "indexedDB"):
        assert forbidden not in browser_text


def test_readme_preserves_the_fresh_clone_runbook() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    required_instructions = (
        "## Quick start: clone and run the UI",
        "git clone https://github.com/alvincho/agentive-finance-lab.git",
        "CPython 3.11 or later",
        "python3 -m venv .venv",
        "source .venv/bin/activate",
        "./.venv/bin/python -m pip install -e .",
        "py -3 -m venv .venv",
        ".\\.venv\\Scripts\\Activate.ps1",
        "python -m pip install -e .",
        "python demos/data-agent-network-demo/run.py --open",
        "Uvicorn running on http://127.0.0.1:8000",
        "curl --fail --silent http://127.0.0.1:8000/health",
        '"participants": 3',
        '"sources": 1',
        "http://127.0.0.1:8000/demos/data-agent-network/",
        "not a `file://` URL",
    )
    for instruction in required_instructions:
        assert instruction in readme
