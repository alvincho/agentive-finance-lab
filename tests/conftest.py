"""Make all three source roots importable from a clean checkout."""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]

for relative_root in (
    "prompits-lite",
    "phemacast-lite",
    "demos/data-agent-network-demo",
):
    source_root = str(REPO_ROOT / relative_root)
    if source_root not in sys.path:
        sys.path.insert(0, source_root)
