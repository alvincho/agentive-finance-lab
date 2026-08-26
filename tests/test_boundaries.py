"""Mechanical guardrails for the public lite-package boundary."""

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PROMPITS_ROOT = REPO_ROOT / "prompits-lite"
PHEMACAST_ROOT = REPO_ROOT / "phemacast-lite"
DEMO_ROOT = REPO_ROOT / "demos" / "data-agent-network-demo"


def imported_roots(path: Path) -> set[str]:
    roots: set[str] = set()
    for source_file in path.rglob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".", 1)[0])
    return roots


def importers_of(path: Path, module_root: str) -> set[Path]:
    importers: set[Path] = set()
    for source_file in path.rglob("*.py"):
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in ast.walk(tree):
            imported: set[str] = set()
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".", 1)[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".", 1)[0])
            if module_root in imported:
                importers.add(source_file.relative_to(DEMO_ROOT))
    return importers


def test_dependency_direction_has_no_reverse_or_original_package_imports() -> None:
    original_packages = {"prompits", "phemacast", "attas"}

    assert imported_roots(PROMPITS_ROOT).isdisjoint(
        {"phemacast_lite", "data_agent_network_demo", *original_packages}
    )
    assert imported_roots(PHEMACAST_ROOT).isdisjoint(
        {"data_agent_network_demo", *original_packages}
    )
    assert imported_roots(DEMO_ROOT).isdisjoint(original_packages)


def test_yfinance_adapter_is_the_only_financial_data_boundary() -> None:
    assert importers_of(DEMO_ROOT, "yfinance") == {
        Path("data_agent_network_demo/yfinance_source.py")
    }
    assert imported_roots(DEMO_ROOT).isdisjoint(
        {
            "alpaca",
            "aiohttp",
            "fredapi",
            "pandas_datareader",
            "polygon",
            "requests",
            "httpx",
            "urllib",
            "urllib3",
        }
    )
    project_config = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert '"yfinance==1.6.0"' in project_config


def test_demo_has_no_catalog_or_synthetic_runtime_fallback() -> None:
    package_root = DEMO_ROOT / "data_agent_network_demo"
    assert not (package_root / "catalog.py").exists()

    runtime_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            package_root / "agents.py",
            package_root / "workflow.py",
            package_root / "app.py",
        )
    )
    for legacy_surface in (
        "from .catalog",
        "CATALOG",
        "simulate_consultant_offline",
        "consultant_available",
        "Demo Premium Terminal",
        "fictional checked-in fixtures",
    ):
        assert legacy_surface not in runtime_text


def test_browser_code_uses_no_durable_storage_or_unsafe_html_sink() -> None:
    javascript = (DEMO_ROOT / "data_agent_network_demo" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    for forbidden in ("localStorage", "sessionStorage", "indexedDB", "innerHTML"):
        assert forbidden not in javascript
    for legacy_surface in (
        "simulate_consultant_offline",
        "consultant_available",
        "fictional fixtures",
        "Demo Premium Terminal",
    ):
        assert legacy_surface not in javascript


def test_pit_name_is_not_given_an_invented_acronym_expansion() -> None:
    documentation = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            REPO_ROOT / "README.md",
            REPO_ROOT / "docs" / "ARCHITECTURE.md",
            PROMPITS_ROOT / "README.md",
        )
    )

    assert "not expanded as an acronym" in documentation
