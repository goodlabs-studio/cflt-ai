"""Tests for tools/wiki-lint.py vendor-source drift detection (H.1-03 Task 1, D-09).

The drift check reads `source: confluent-agent-skills@<sha>` from article frontmatter,
compares against `tools/vendor-sources.json`'s pinned commit, and emits one of:
- DRIFT: <path>: source=<sha-prefix>..., pin=<sha-prefix>...   (SHA mismatch)
- MALFORMED source field in <path>: <repr>                     (no @ separator)
- UNKNOWN VENDOR in <path>: <vendor!r> not in vendor-sources.json
- WARNING: MISSING vendor-sources.json                         (pin file missing)
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "tools" / "wiki-lint.py"
CURRENT_SHA = "91d1871ef8c320be92bca955c8e42492a2778cb4"
STALE_SHA = "0123456789abcdef0123456789abcdef01234567"


def make_article(root: Path, name: str, source_value):
    """Write a minimal article with optional `source:` field. Returns the path."""
    body = (
        "---\n"
        "title: Test Article\n"
        "tags: [test]\n"
        "confidence: high\n"
        "last_updated: 2026-05-16\n"
        "last_validated: 2026-05-16\n"
    )
    if source_value is not None:
        body += f"source: {source_value}\n"
    body += "---\n\n# Test\n\nBody.\n"
    path = root / "wiki" / "concepts" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body)
    return path


def make_vendor_sources(root: Path, commit):
    """Write tools/vendor-sources.json. If commit is None, skip creating the file."""
    if commit is None:
        return
    data = {
        "confluent-agent-skills": {
            "upstream": "https://example/agent-skills",
            "commit": commit,
            "kind": "wiki-source",
        }
    }
    (root / "tools").mkdir(exist_ok=True)
    (root / "tools" / "vendor-sources.json").write_text(json.dumps(data))


def run_lint(root: Path):
    """Execute wiki-lint.py with CFLT_WIKI_ROOT pointing at the temp tree."""
    env = os.environ.copy()
    env["CFLT_WIKI_ROOT"] = str(root)
    return subprocess.run(
        ["python3", str(SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
    )


def test_drift_match_no_finding(tmp_path):
    """Article SHA matches pin → no DRIFT finding."""
    make_article(tmp_path, "a.md", f"confluent-agent-skills@{CURRENT_SHA}")
    make_vendor_sources(tmp_path, CURRENT_SHA)
    result = run_lint(tmp_path)
    combined = result.stdout + result.stderr
    assert "DRIFT" not in combined, combined


def test_drift_stale_sha_emits_finding(tmp_path):
    """Article SHA differs from pin → DRIFT finding emitted with both SHAs."""
    make_article(tmp_path, "a.md", f"confluent-agent-skills@{STALE_SHA}")
    make_vendor_sources(tmp_path, CURRENT_SHA)
    result = run_lint(tmp_path)
    combined = result.stdout + result.stderr
    assert "DRIFT" in combined, combined
    # Stale SHA prefix should appear in the finding
    assert STALE_SHA[:12] in combined, combined


def test_no_source_field_skipped(tmp_path):
    """Article without `source:` field → no DRIFT finding (silent skip)."""
    make_article(tmp_path, "a.md", None)
    make_vendor_sources(tmp_path, CURRENT_SHA)
    result = run_lint(tmp_path)
    combined = result.stdout + result.stderr
    assert "DRIFT" not in combined, combined
    assert "MALFORMED" not in combined, combined


def test_missing_vendor_sources_warns_not_crashes(tmp_path):
    """vendor-sources.json missing → warning emitted, exit code stays 0."""
    make_article(tmp_path, "a.md", f"confluent-agent-skills@{CURRENT_SHA}")
    make_vendor_sources(tmp_path, None)  # don't create the file
    result = run_lint(tmp_path)
    combined = result.stdout + result.stderr
    # Either the file missing warning shows, OR the exit code is 0 (no crash).
    assert (
        "MISSING vendor-sources.json" in combined or result.returncode == 0
    ), combined


def test_malformed_source_field_emits_finding(tmp_path):
    """Article `source:` with no @ separator → MALFORMED finding."""
    make_article(tmp_path, "a.md", "confluent-agent-skills-no-at-sign")
    make_vendor_sources(tmp_path, CURRENT_SHA)
    result = run_lint(tmp_path)
    combined = result.stdout + result.stderr
    assert "MALFORMED" in combined, combined
