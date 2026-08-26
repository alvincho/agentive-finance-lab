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


def test_dependency_direction_has_no_reverse_or_original_package_imports() -> None:
    original_packages = {"prompits", "phemacast", "attas"}

    assert imported_roots(PROMPITS_ROOT).isdisjoint(
        {"phemacast_lite", "data_agent_network_demo", *original_packages}
    )
    assert imported_roots(PHEMACAST_ROOT).isdisjoint(
        {"data_agent_network_demo", *original_packages}
    )
    assert imported_roots(DEMO_ROOT).isdisjoint(original_packages)


def test_browser_code_uses_no_durable_storage_or_unsafe_html_sink() -> None:
    javascript = (DEMO_ROOT / "data_agent_network_demo" / "static" / "app.js").read_text(
        encoding="utf-8"
    )

    for forbidden in ("localStorage", "sessionStorage", "indexedDB", "innerHTML"):
        assert forbidden not in javascript


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
