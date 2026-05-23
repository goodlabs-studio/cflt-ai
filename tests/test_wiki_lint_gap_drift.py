"""Tests for tools/wiki-lint.py KNOWN-GAPS trip-wire drift detection (Phase 12-02).

Per H.1 D-09 passive posture: drift findings are surfaced but lint exits 0.

This module validates:
1. tools/vendor-sources.json contains 13 well-formed trip-wires (G-01..G-13)
   under the `linuxone-accelerator-gaps` key
2. tools/wiki-lint.py exposes a `check_gap_drift(repo_root, vendor_pins)` function
   returning a dict with keys {gap_drift, missing_gap, malformed_gap}
3. The function emits DRIFT-GAP / MISSING-GAP / MALFORMED-GAP findings as documented
4. Running `python tools/wiki-lint.py --full` returns exit code 0 even with drift
"""
import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "tools" / "wiki-lint.py"
VENDOR_SOURCES = REPO_ROOT / "tools" / "vendor-sources.json"
KNOWN_GAPS_REL = "raw/repos/fsi-dsp/accelerators/confluent-on-linuxone/KNOWN-GAPS.md"

REQUIRED_FIELDS = {"id", "title", "status", "workaround", "fsi_impact", "source", "source_id"}
EXPECTED_IDS = {f"G-{n:02d}" for n in range(1, 14)}


# ---------------------------------------------------------------------------
# Module loader (wiki-lint.py has a hyphen so importlib is required)
# ---------------------------------------------------------------------------
def load_wiki_lint():
    spec = importlib.util.spec_from_file_location("wiki_lint", str(SCRIPT))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------
def write_vendor_pins(root: Path, data: dict):
    (root / "tools").mkdir(parents=True, exist_ok=True)
    (root / "tools" / "vendor-sources.json").write_text(json.dumps(data, indent=2))


def write_known_gaps(root: Path, rows):
    """Write a synthetic KNOWN-GAPS.md with the given list of (id, title, impact, workaround, status) rows."""
    path = root / KNOWN_GAPS_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    body = [
        "# Known Gaps — synthetic",
        "",
        "## Gap Register",
        "",
        "| # | Gap | Impact | Workaround | Status |",
        "|---|-----|--------|------------|--------|",
    ]
    for gap_id, title, impact, workaround, status in rows:
        body.append(f"| {gap_id} | {title} | {impact} | {workaround} | {status} |")
    body.append("")
    path.write_text("\n".join(body))


def make_trip_wire(gap_id: str, status: str = "Open", **overrides):
    base = {
        "id": gap_id,
        "title": f"Synthetic gap {gap_id}",
        "status": status,
        "workaround": "synthetic workaround",
        "fsi_impact": "synthetic impact",
        "source": "accelerators/confluent-on-linuxone/KNOWN-GAPS.md",
        "source_id": "fsi-dsp://accelerator/confluent-on-linuxone",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Real-file shape tests (Tests 1-5: vendor-sources.json contents)
# ---------------------------------------------------------------------------
def test_vendor_sources_parses_and_has_gaps_key():
    """Test 1: vendor-sources.json parses as JSON and has linuxone-accelerator-gaps key."""
    assert VENDOR_SOURCES.exists(), f"missing {VENDOR_SOURCES}"
    data = json.loads(VENDOR_SOURCES.read_text())
    assert "linuxone-accelerator-gaps" in data, (
        f"linuxone-accelerator-gaps key absent; keys={list(data.keys())}"
    )


def test_trip_wires_list_length_13():
    """Test 2: linuxone-accelerator-gaps.trip_wires is a list of length 13."""
    data = json.loads(VENDOR_SOURCES.read_text())
    trips = data["linuxone-accelerator-gaps"]["trip_wires"]
    assert isinstance(trips, list), "trip_wires must be a list"
    assert len(trips) == 13, f"expected 13 trip-wires, got {len(trips)}"


def test_each_trip_wire_has_all_required_fields():
    """Test 3: Each trip-wire has all 7 required fields."""
    data = json.loads(VENDOR_SOURCES.read_text())
    trips = data["linuxone-accelerator-gaps"]["trip_wires"]
    for tw in trips:
        missing = REQUIRED_FIELDS - set(tw.keys())
        assert not missing, f"{tw.get('id', '<no-id>')}: missing fields {sorted(missing)}"


def test_trip_wire_ids_are_exactly_g01_to_g13():
    """Test 4: Trip-wire IDs are exactly {G-01, ..., G-13}."""
    data = json.loads(VENDOR_SOURCES.read_text())
    trips = data["linuxone-accelerator-gaps"]["trip_wires"]
    ids = {tw["id"] for tw in trips}
    assert ids == EXPECTED_IDS, (
        f"IDs mismatch: extras={ids - EXPECTED_IDS}, missing={EXPECTED_IDS - ids}"
    )


def test_all_source_ids_are_canonical():
    """Test 5: All source_id values equal fsi-dsp://accelerator/confluent-on-linuxone."""
    data = json.loads(VENDOR_SOURCES.read_text())
    trips = data["linuxone-accelerator-gaps"]["trip_wires"]
    canonical = "fsi-dsp://accelerator/confluent-on-linuxone"
    for tw in trips:
        assert tw["source_id"] == canonical, (
            f"{tw['id']}: source_id={tw['source_id']!r} (expected {canonical!r})"
        )


# ---------------------------------------------------------------------------
# check_gap_drift behavior tests (Tests 6-9, 11, 12)
# ---------------------------------------------------------------------------
def test_check_gap_drift_happy_path_no_findings(tmp_path):
    """Test 6: Matching trip-wires + upstream rows → no findings."""
    wl = load_wiki_lint()
    rows = [
        ("G-01", "Title 1", "Impact 1", "Workaround 1", "Open"),
        ("G-02", "Title 2", "Impact 2", "Workaround 2", "Workaround in place"),
    ]
    write_known_gaps(tmp_path, rows)
    vendor_pins = {
        "linuxone-accelerator-gaps": {
            "trip_wires": [
                make_trip_wire("G-01", status="Open"),
                make_trip_wire("G-02", status="Workaround in place"),
            ]
        }
    }
    result = wl.check_gap_drift(tmp_path, vendor_pins)
    assert result["gap_drift"] == [], result
    assert result["missing_gap"] == [], result
    assert result["malformed_gap"] == [], result


def test_check_gap_drift_emits_drift_when_status_changes(tmp_path):
    """Test 7: Declared status differs from upstream → DRIFT-GAP finding."""
    wl = load_wiki_lint()
    rows = [("G-04", "Some title", "Some impact", "Some workaround", "Resolved")]
    write_known_gaps(tmp_path, rows)
    vendor_pins = {
        "linuxone-accelerator-gaps": {
            "trip_wires": [make_trip_wire("G-04", status="Open")]
        }
    }
    result = wl.check_gap_drift(tmp_path, vendor_pins)
    assert len(result["gap_drift"]) == 1, result
    msg = result["gap_drift"][0]
    assert "DRIFT-GAP" in msg, msg
    assert "G-04" in msg, msg
    assert "Open" in msg, msg
    assert "Resolved" in msg, msg


def test_check_gap_drift_emits_missing_when_upstream_row_absent(tmp_path):
    """Test 8: Trip-wire ID with no matching upstream row → MISSING-GAP."""
    wl = load_wiki_lint()
    # Upstream has only G-01; trip-wires declare G-99
    rows = [("G-01", "Title", "Impact", "Workaround", "Open")]
    write_known_gaps(tmp_path, rows)
    vendor_pins = {
        "linuxone-accelerator-gaps": {
            "trip_wires": [make_trip_wire("G-99", status="Open")]
        }
    }
    result = wl.check_gap_drift(tmp_path, vendor_pins)
    assert len(result["missing_gap"]) == 1, result
    assert "MISSING-GAP" in result["missing_gap"][0]
    assert "G-99" in result["missing_gap"][0]


def test_check_gap_drift_emits_malformed_when_field_missing(tmp_path):
    """Test 9: Trip-wire missing a required field → MALFORMED-GAP."""
    wl = load_wiki_lint()
    rows = [("G-01", "Title", "Impact", "Workaround", "Open")]
    write_known_gaps(tmp_path, rows)
    bad = {
        "id": "G-01",
        "title": "Synthetic",
        # status intentionally missing
        "workaround": "x",
        "fsi_impact": "x",
        "source": "x",
        "source_id": "x",
    }
    vendor_pins = {"linuxone-accelerator-gaps": {"trip_wires": [bad]}}
    result = wl.check_gap_drift(tmp_path, vendor_pins)
    assert len(result["malformed_gap"]) == 1, result
    msg = result["malformed_gap"][0]
    assert "MALFORMED-GAP" in msg
    assert "G-01" in msg
    assert "status" in msg


def test_check_gap_drift_backcompat_when_key_absent(tmp_path):
    """Test 11: linuxone-accelerator-gaps absent → silently empty findings, no exception."""
    wl = load_wiki_lint()
    # No KNOWN-GAPS.md, no key — should not raise
    vendor_pins = {
        "confluent-agent-skills": {"commit": "deadbeef"},
        # no linuxone-accelerator-gaps
    }
    result = wl.check_gap_drift(tmp_path, vendor_pins)
    assert result == {"gap_drift": [], "missing_gap": [], "malformed_gap": []}


def test_check_gap_drift_case_insensitive_status_compare(tmp_path):
    """Test 12: 'open' matches 'Open' (case-insensitive, whitespace-stripped)."""
    wl = load_wiki_lint()
    rows = [("G-07", "Title", "Impact", "Workaround", "  OPEN  ")]
    write_known_gaps(tmp_path, rows)
    vendor_pins = {
        "linuxone-accelerator-gaps": {
            "trip_wires": [make_trip_wire("G-07", status="open")]
        }
    }
    result = wl.check_gap_drift(tmp_path, vendor_pins)
    assert result["gap_drift"] == [], result


def test_check_gap_drift_handles_missing_vendor_pins_arg(tmp_path):
    """Defensive: None vendor_pins → empty findings, no exception."""
    wl = load_wiki_lint()
    result = wl.check_gap_drift(tmp_path, None)
    assert result == {"gap_drift": [], "missing_gap": [], "malformed_gap": []}


def test_check_gap_drift_handles_missing_known_gaps_file(tmp_path):
    """Defensive: KNOWN-GAPS.md not checked out → empty findings, no exception."""
    wl = load_wiki_lint()
    vendor_pins = {
        "linuxone-accelerator-gaps": {
            "trip_wires": [make_trip_wire("G-01")]
        }
    }
    # No write_known_gaps call — file doesn't exist
    result = wl.check_gap_drift(tmp_path, vendor_pins)
    assert result == {"gap_drift": [], "missing_gap": [], "malformed_gap": []}


# ---------------------------------------------------------------------------
# Subprocess test (Test 10: non-fatal exit)
# ---------------------------------------------------------------------------
def test_wiki_lint_full_exits_zero_with_drift(tmp_path):
    """Test 10: `python tools/wiki-lint.py --full` returns exit 0 even with gap drift.

    Per H.1 D-09 passive posture: drift findings are surfaced but lint exits 0.
    """
    # Build a minimal synthetic repo with: wiki/, tools/, raw/.../KNOWN-GAPS.md
    (tmp_path / "wiki" / "concepts").mkdir(parents=True)
    # Synthetic vendor-sources.json with one drifted trip-wire
    write_vendor_pins(
        tmp_path,
        {
            "linuxone-accelerator-gaps": {
                "upstream": "https://example",
                "trip_wires": [make_trip_wire("G-01", status="Open")],
            }
        },
    )
    write_known_gaps(
        tmp_path,
        [("G-01", "Title", "Impact", "Workaround", "Resolved")],  # drifted
    )
    env = os.environ.copy()
    env["CFLT_WIKI_ROOT"] = str(tmp_path)
    result = subprocess.run(
        ["python3", str(SCRIPT), "--full"],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"exit={result.returncode}, stdout={result.stdout}, stderr={result.stderr}"
    )
