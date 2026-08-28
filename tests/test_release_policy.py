from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_live_substack_is_the_only_downstream_authorization_gate() -> None:
    release = _load("docs/releases/01-release.json")
    receipts = _load("docs/social/01-receipts.json")

    authorization = release["downstream_authorization"]
    canonical = release["canonical"]
    assert authorization["basis"] == "verified_live_canonical_substack_publication"
    assert authorization["status"] == "authorized"
    assert authorization["canonical_url"] == canonical["url"]
    assert authorization["remote_post_id"] == canonical["remote_post_id"]
    assert canonical["status"] == "observed_existing_published"
    assert receipts["authorization_basis"] == authorization["basis"]

    forbidden_keys = {
        "approved_for_release",
        "approved_at",
        "reviewed_by",
        "manual_review_required",
    }

    def visit(value: object) -> None:
        if isinstance(value, dict):
            assert forbidden_keys.isdisjoint(value)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(release)
    visit(receipts)


def test_release_artifact_hashes_are_integrity_checks() -> None:
    release = _load("docs/releases/01-release.json")
    for artifact in release["artifacts"]:
        path = ROOT / artifact["path"]
        assert path.is_file(), artifact["path"]
        assert _sha256(path) == artifact["sha256"], artifact["path"]


def test_receipts_do_not_encode_editorial_approval_blocks() -> None:
    receipts = _load("docs/social/01-receipts.json")
    for receipt in receipts["receipts"]:
        status = receipt["status"].lower()
        assert "approval" not in status
        assert "review_only" not in status
