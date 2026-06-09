"""
Phase H.3c — /dsp:scaffold engine tests.

Covers all five scaffold outcomes (success-dev, success-prod, blocked-profile,
blocked-canon-family, not-implemented) plus triage table sanity and provenance
round-trip.

All tests write to a temporary OUTPUT_ROOT via monkeypatch so the real
outputs/scaffolded/ stays clean during testing.
"""
import json
import sys
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools import scaffold_engine  # noqa: E402
from tools.scaffold_engine import (  # noqa: E402
    scaffold,
    ARTIFACT_TYPE_TO_SKILL,
    ScaffoldResult,
)


@pytest.fixture(autouse=True)
def isolate_output_and_activity(tmp_path, monkeypatch):
    """Redirect OUTPUT_ROOT and ACTIVITY_LOG_DIR to tmp_path so tests don't pollute repo."""
    monkeypatch.setattr(scaffold_engine, "OUTPUT_ROOT", tmp_path / "scaffolded")
    monkeypatch.setattr(scaffold_engine, "ACTIVITY_LOG_DIR", tmp_path / "activity")


def test_scaffold_producer_happy_path_developer_sandbox():
    """developer/sandbox can scaffold producer → success, canon_family=developer-sandbox."""
    result = scaffold(
        artifact_type="producer",
        name="my-payments-producer",
        profile_name="developer/sandbox",
        operator="test-op",
    )
    assert result.status == "success"
    assert result.scaffold_dir is not None
    assert result.scaffold_dir.exists()
    assert (result.scaffold_dir / "provenance.json").exists()
    assert (result.scaffold_dir / "manifest-entry.yaml").exists()
    assert (result.scaffold_dir / "scaffold" / "producer.py").exists()
    assert (result.scaffold_dir / "scaffold" / "config.json").exists()
    assert (result.scaffold_dir / "README.md").exists()

    prov = json.loads((result.scaffold_dir / "provenance.json").read_text())
    assert prov["canon_family"] == "developer-sandbox"
    assert prov["profile_family"] == "developer"
    assert prov["upstream_skill"] == "developing-kafka-python-client"
    assert prov["upstream_commit_sha"] == "91d1871ef8c320be92bca955c8e42492a2778cb4"


def test_scaffold_producer_happy_path_engineer_prod():
    """engineer + --prod scaffolds producer → success, canon_family=operator-prod."""
    result = scaffold(
        artifact_type="producer",
        name="my-prod-producer",
        profile_name="engineer",
        operator="test-op",
        prod=True,
    )
    assert result.status == "success"
    prov = json.loads((result.scaffold_dir / "provenance.json").read_text())
    assert prov["canon_family"] == "operator-prod"
    assert prov["profile_family"] == "operator"


def test_scaffold_read_only_blocked():
    """read-only is blocked by skill_blocklist (Gate 1) + by empty allowed_operations (Gate 2)."""
    result = scaffold(
        artifact_type="producer",
        name="x",
        profile_name="read-only",
        operator="test-op",
    )
    assert result.status == "blocked-by-profile"
    assert result.scaffold_dir is None
    assert (
        "/dsp:scaffold" in result.message
        or "read-only" in result.message.lower()
        or "blocks" in result.message.lower()
    )


def test_scaffold_cross_family_canon_refused():
    """developer/sandbox --prod is refused with cross-family error."""
    result = scaffold(
        artifact_type="producer",
        name="x",
        profile_name="developer/sandbox",
        operator="test-op",
        prod=True,
    )
    assert result.status == "blocked-by-canon-family"
    assert result.scaffold_dir is None
    assert (
        "cross-family" in result.message.lower()
        or "developer-family" in result.message.lower()
    )


def test_scaffold_not_implemented_artifact_type():
    """cdc-pipeline (and others) is stubbed in H.3c → not-implemented."""
    result = scaffold(
        artifact_type="cdc-pipeline",
        name="x",
        profile_name="engineer",
        operator="test-op",
    )
    assert result.status == "not-implemented"
    assert "H.3c follow-up" in result.message
    assert result.scaffold_dir is None


def test_triage_table_all_target_streaming_skills_plugin():
    """Every artifact-type in the triage table maps to a streaming-skills-plugin skill."""
    assert len(ARTIFACT_TYPE_TO_SKILL) >= 5
    for artifact_type, upstream in ARTIFACT_TYPE_TO_SKILL.items():
        assert upstream.startswith("streaming-skills-plugin:"), (
            f"{artifact_type!r} maps to {upstream!r} — "
            f"must start with 'streaming-skills-plugin:'"
        )


def test_provenance_round_trip():
    """A successful scaffold writes a provenance.json with all 15 D-08 keys."""
    result = scaffold(
        artifact_type="producer",
        name="round-trip",
        profile_name="developer/sandbox",
        operator="test-op",
    )
    assert result.status == "success"
    prov = json.loads((result.scaffold_dir / "provenance.json").read_text())
    expected_keys = {
        "operator", "profile", "profile_family", "overlay",
        "artifact_type", "name",
        "upstream_skill", "upstream_plugin",
        "upstream_plugin_version", "upstream_commit_sha",
        "canon_stack_hash", "canon_family",
        "timestamp_utc", "scaffold_dir", "phase",
    }
    assert expected_keys.issubset(set(prov.keys())), (
        f"provenance.json missing keys: {expected_keys - set(prov.keys())}"
    )
    assert prov["phase"] == "H.3c"


def test_manifest_entry_yaml_is_valid():
    """Sanity: the proposed MANIFEST entry YAML is well-formed."""
    result = scaffold(
        artifact_type="producer",
        name="yaml-check",
        profile_name="developer/sandbox",
        operator="test-op",
    )
    assert result.status == "success"
    manifest_text = (result.scaffold_dir / "manifest-entry.yaml").read_text()
    loaded = yaml.safe_load(manifest_text)
    assert isinstance(loaded, list) and len(loaded) == 1
    entry = loaded[0]
    assert entry["id"] == "producer/yaml-check"
    assert entry["type"] == "scaffolded-producer"
    assert "provenance" in entry
    assert entry["provenance"]["generator_phase"] == "H.3c"


# ── Operator-side industry selection ─────────────────────────────────────────

def _prov(result):
    return json.loads((result.scaffold_dir / "provenance.json").read_text())


def test_industry_defaults_to_fsi_prod():
    """Back-compat: engineer + --prod with no industry resolves industry/fsi."""
    result = scaffold(
        artifact_type="producer", name="ind-default",
        profile_name="engineer", operator="test-op", prod=True,
    )
    assert result.status == "success"
    assert _prov(result)["canon_layer"] == "industry/fsi"


def test_operator_selects_retail_prod():
    """engineer + --prod + --industry retail targets industry/retail."""
    result = scaffold(
        artifact_type="producer", name="ind-retail",
        profile_name="engineer", operator="test-op", prod=True, industry="retail",
    )
    assert result.status == "success"
    assert _prov(result)["canon_layer"] == "industry/retail"


def test_operator_retail_nonprod_uses_dev_sandbox_tier():
    """engineer (no --prod) + --industry retail targets the retail dev-sandbox tier."""
    result = scaffold(
        artifact_type="producer", name="ind-retail-dev",
        profile_name="engineer", operator="test-op", industry="retail",
    )
    assert result.status == "success"
    assert _prov(result)["canon_layer"] == "industry/retail/developer-sandbox"


def test_unknown_industry_raises():
    with pytest.raises(ValueError, match="Unknown industry"):
        scaffold(
            artifact_type="producer", name="ind-bogus",
            profile_name="engineer", operator="test-op", prod=True, industry="nope",
        )


def test_resolve_industry_precedence():
    """Explicit arg > profile field > 'fsi' default."""
    assert scaffold_engine._resolve_industry(None, {}) == "fsi"
    assert scaffold_engine._resolve_industry(None, {"industry": "retail"}) == "retail"
    # Explicit arg overrides the profile field.
    assert scaffold_engine._resolve_industry("fsi", {"industry": "retail"}) == "fsi"


def test_industry_missing_dev_sandbox_tier_raises(tmp_path, monkeypatch):
    """An industry with a prod overlay but no developer-sandbox tier fails loudly
    on a non-prod scaffold instead of silently composing base-only canon."""
    ext = tmp_path / "ext"
    half = ext / "industry" / "telco"
    half.mkdir(parents=True)
    (half / "overrides.yaml").write_text(
        'producer:\n  compression_type: "zstd"\n  override_source: "telco://adr/001"\n'
    )  # note: no developer-sandbox/ subdir
    monkeypatch.setenv("CFLT_CANON_EXTERNAL_PATH", str(ext))

    # Prod tier exists → valid industry, scaffolds fine.
    ok = scaffold(
        artifact_type="producer", name="telco-prod",
        profile_name="engineer", operator="test-op", prod=True, industry="telco",
    )
    assert ok.status == "success"
    assert _prov(ok)["canon_layer"] == "industry/telco"

    # Non-prod targets the missing developer-sandbox tier → raises, no silent fallback.
    with pytest.raises(ValueError, match="no overrides.yaml"):
        scaffold(
            artifact_type="producer", name="telco-dev",
            profile_name="engineer", operator="test-op", industry="telco",
        )
