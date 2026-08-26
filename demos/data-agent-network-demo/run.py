"""Source-checkout launcher that does not require editable installation."""

from __future__ import annotations

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
for package_root in (
    REPO_ROOT / "prompits-lite",
    REPO_ROOT / "phemacast-lite",
    REPO_ROOT / "demos" / "data-agent-network-demo",
):
    sys.path.insert(0, str(package_root))

from data_agent_network_demo.__main__ import main  # noqa: E402


if __name__ == "__main__":
    main()
