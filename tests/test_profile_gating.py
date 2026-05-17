"""Per-profile negative-space test suite (ACTG-01, ACTG-02, ACTG-03, ACTG-04).

Parametrized across every tool in tool_classification.json x every profile.
Proves forbidden tools fail closed — not just "some", but ALL.
"""
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.apply_engine import (
    check_tool_permitted,
    load_profile,
    load_tool_classification,
    VALID_FAMILIES,
    PROFILES_DIR,
)

# Load classification table for parametrization
CLASSIFICATION = json.loads(
    (PROJECT_ROOT / "tools" / "profiles" / "tool_classification.json").read_text()
)
ALL_TOOLS = sorted(CLASSIFICATION["tools"].keys())

# Partition tools by tier for targeted assertions
READ_ONLY_TOOLS = [t for t, tier in CLASSIFICATION["tools"].items() if tier == "read-only"]
ENGINEER_TOOLS = [t for t, tier in CLASSIFICATION["tools"].items() if tier == "engineer"]
BREAK_GLASS_TOOLS = [t for t, tier in CLASSIFICATION["tools"].items() if tier == "break-glass"]

# Tools that read-only should deny = engineer + break-glass tier tools
READ_ONLY_FORBIDDEN = sorted(ENGINEER_TOOLS + BREAK_GLASS_TOOLS)
# Tools that engineer should deny = break-glass tier tools only
ENGINEER_FORBIDDEN = sorted(BREAK_GLASS_TOOLS)


# ---------------------------------------------------------------------------
# TestClassificationCoverage (ACTG-01)
# ---------------------------------------------------------------------------


class TestClassificationCoverage:
    def test_classification_covers_minimum_tools(self):
        """Classification table must contain >= 50 tools (ACTG-01 coverage gate)."""
        assert len(ALL_TOOLS) >= 50, (
            f"Expected >= 50 tools in classification table, found {len(ALL_TOOLS)}"
        )

    def test_all_tiers_have_tools(self):
        """Every tier (read-only, engineer, break-glass) has at least one tool."""
        assert len(READ_ONLY_TOOLS) >= 1, "read-only tier has no tools"
        assert len(ENGINEER_TOOLS) >= 1, "engineer tier has no tools"
        assert len(BREAK_GLASS_TOOLS) >= 1, "break-glass tier has no tools"

    def test_no_unknown_tiers(self):
        """Every tier value in the classification table is a known tier."""
        valid_tiers = {"read-only", "engineer", "break-glass"}
        unknown = {
            tier for tier in CLASSIFICATION["tools"].values()
            if tier not in valid_tiers
        }
        assert not unknown, f"Unknown tier values found: {unknown}"

    def test_unclassified_policy_is_deny(self):
        """unclassified_policy must be 'deny' — fail-closed enforcement."""
        assert CLASSIFICATION["unclassified_policy"] == "deny", (
            f"Expected unclassified_policy='deny', got {CLASSIFICATION['unclassified_policy']!r}"
        )


# ---------------------------------------------------------------------------
# TestReadOnlyGating (ACTG-02)
# ---------------------------------------------------------------------------


class TestReadOnlyGating:
    @pytest.mark.parametrize("tool_name", READ_ONLY_FORBIDDEN)
    def test_forbidden_tool_denied(self, tool_name):
        """Every engineer- and break-glass-tier tool is denied by read-only profile."""
        assert not check_tool_permitted("read-only", tool_name), (
            f"read-only profile must deny '{tool_name}' (tier: {CLASSIFICATION['tools'][tool_name]})"
        )

    @pytest.mark.parametrize("tool_name", sorted(READ_ONLY_TOOLS))
    def test_permitted_tool_allowed(self, tool_name):
        """Every read-only-tier tool is permitted by read-only profile."""
        assert check_tool_permitted("read-only", tool_name), (
            f"read-only profile must permit '{tool_name}' (tier: read-only)"
        )


# ---------------------------------------------------------------------------
# TestEngineerGating (ACTG-02)
# ---------------------------------------------------------------------------


class TestEngineerGating:
    @pytest.mark.parametrize("tool_name", ENGINEER_FORBIDDEN)
    def test_break_glass_tool_denied(self, tool_name):
        """Every break-glass-tier tool is denied by engineer profile."""
        assert not check_tool_permitted("engineer", tool_name), (
            f"engineer profile must deny '{tool_name}' (tier: break-glass)"
        )

    @pytest.mark.parametrize("tool_name", sorted(READ_ONLY_TOOLS + ENGINEER_TOOLS))
    def test_permitted_tool_allowed(self, tool_name):
        """Every read-only- and engineer-tier tool is permitted by engineer profile."""
        assert check_tool_permitted("engineer", tool_name), (
            f"engineer profile must permit '{tool_name}' (tier: {CLASSIFICATION['tools'][tool_name]})"
        )


# ---------------------------------------------------------------------------
# TestBreakGlassGating (ACTG-02)
# ---------------------------------------------------------------------------


class TestBreakGlassGating:
    @pytest.mark.parametrize("tool_name", ALL_TOOLS)
    def test_all_tools_permitted(self, tool_name):
        """Every classified tool is permitted by break-glass profile."""
        assert check_tool_permitted("break-glass", tool_name), (
            f"break-glass profile must permit '{tool_name}' (tier: {CLASSIFICATION['tools'][tool_name]})"
        )


# ---------------------------------------------------------------------------
# TestUnclassifiedToolDenial (ACTG-01)
# ---------------------------------------------------------------------------


class TestUnclassifiedToolDenial:
    def test_unclassified_denied_by_read_only(self):
        """Unclassified tool is denied by read-only profile (fail-closed)."""
        assert not check_tool_permitted("read-only", "nonexistent_tool_xyz"), (
            "read-only profile must deny tools not in classification table"
        )

    def test_unclassified_denied_by_engineer(self):
        """Unclassified tool is denied by engineer profile (fail-closed)."""
        assert not check_tool_permitted("engineer", "nonexistent_tool_xyz"), (
            "engineer profile must deny tools not in classification table"
        )

    def test_unclassified_denied_by_break_glass(self):
        """Unclassified tool is denied by break-glass profile (fail-closed)."""
        assert not check_tool_permitted("break-glass", "nonexistent_tool_xyz"), (
            "break-glass profile must deny tools not in classification table"
        )


# ---------------------------------------------------------------------------
# TestCustomerDifferential (ACTG-04)
# ---------------------------------------------------------------------------


class TestCustomerDifferential:
    def test_base_engineer_permits_flink(self):
        """Base engineer profile permits 'module/flink' in allowed_operations."""
        profile = load_profile("engineer")
        assert "module/flink" in profile["allowed_operations"], (
            "Base engineer profile must include module/flink"
        )

    def test_acme_bank_engineer_denies_flink(self):
        """acme-bank engineer overlay removes 'module/flink' from allowed_operations."""
        profile = load_profile("engineer", customer="acme-bank")
        assert "module/flink" not in profile["allowed_operations"], (
            "acme-bank engineer profile must NOT include module/flink (per ADR-003)"
        )

    def test_acme_bank_engineer_permits_cp_audit(self):
        """acme-bank engineer overlay adds 'role/cp_audit' to allowed_operations."""
        profile = load_profile("engineer", customer="acme-bank")
        assert "role/cp_audit" in profile["allowed_operations"], (
            "acme-bank engineer profile must include role/cp_audit (per ADR-003)"
        )

    def test_acme_bank_preserves_base_permissions(self):
        """acme-bank engineer overlay retains 'module/topic' from base engineer."""
        profile = load_profile("engineer", customer="acme-bank")
        assert "module/topic" in profile["allowed_operations"], (
            "acme-bank engineer profile must still include module/topic"
        )

    def test_nonexistent_customer_falls_back_to_base(self):
        """load_profile() with nonexistent customer falls back to base engineer (has 'module/flink')."""
        profile = load_profile("engineer", customer="nonexistent-customer-xyz")
        assert "module/flink" in profile["allowed_operations"], (
            "Fallback to base engineer must include module/flink"
        )


# ---------------------------------------------------------------------------
# H.4a — Family field round-trip + branch dispatch tests
# ---------------------------------------------------------------------------

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "profiles"
SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


class TestFamilyRoundTrip:
    """H.4a D-09 test group 1 — family field round-trip through load_profile()."""

    def test_load_profile_reads_family_for_all_operator_profiles(self):
        """Every committed operator profile loads with family == 'operator'."""
        for name in ("read-only", "engineer", "break-glass"):
            p = load_profile(name)
            assert p["family"] == "operator", (
                f"Profile {name!r} expected family=operator, got {p.get('family')!r}"
            )

    def test_load_profile_defaults_family_to_operator_when_absent(self, tmp_path, monkeypatch):
        """A profile JSON missing the family field defaults to operator (back-compat)."""
        legacy_profile = {
            "name": "engineer",  # name MUST be a VALID_PROFILES entry for load to proceed
            "description": "Pre-H.4a shape",
            "allowed_operations": [],
        }
        tmp_profiles = tmp_path / "profiles"
        tmp_profiles.mkdir()
        (tmp_profiles / "engineer.json").write_text(json.dumps(legacy_profile))
        monkeypatch.setattr("tools.apply_engine.PROFILES_DIR", tmp_profiles)
        p = load_profile("engineer")
        assert p["family"] == "operator", (
            f"Absent family field should default to 'operator', got {p.get('family')!r}"
        )

    def test_load_profile_rejects_unknown_family(self, tmp_path, monkeypatch):
        """A profile with family not in VALID_FAMILIES raises ValueError."""
        bad_profile = {
            "name": "engineer",
            "description": "Bogus family value",
            "family": "platform",  # not in VALID_FAMILIES
            "allowed_operations": [],
        }
        tmp_profiles = tmp_path / "profiles"
        tmp_profiles.mkdir()
        (tmp_profiles / "engineer.json").write_text(json.dumps(bad_profile))
        monkeypatch.setattr("tools.apply_engine.PROFILES_DIR", tmp_profiles)
        with pytest.raises(ValueError, match="unknown family"):
            load_profile("engineer")


class TestOperatorBranchByteCompat:
    """H.4a D-09 test group 2 — operator-branch behavior byte-identical to pre-H.4a.

    The snapshot at tests/snapshots/h4a_operator_permits.json captures every
    (operator-profile x tool) permit decision after the H.4a refactor. Any future
    change that shifts the permit set will fail this test, forcing the snapshot
    to be regenerated in a separate visible-diff PR.

    Regenerator one-liner (run from project root):
        python3 -c "
        import json
        from tools.apply_engine import check_tool_permitted, load_tool_classification
        tc = load_tool_classification()
        operator_profiles = ['read-only', 'engineer', 'break-glass']
        snap = {p: {t: check_tool_permitted(p, t) for t in sorted(tc['tools'])} for p in operator_profiles}
        print(json.dumps(snap, indent=2))
        " > tests/snapshots/h4a_operator_permits.json
    """

    def test_check_tool_permitted_operator_branch_byte_identical(self):
        snapshot_path = SNAPSHOT_DIR / "h4a_operator_permits.json"
        assert snapshot_path.exists(), (
            "Snapshot missing — regenerate via the one-liner in this test's docstring"
        )
        snapshot = json.loads(snapshot_path.read_text())
        for profile_name, tool_decisions in snapshot.items():
            for tool_name, expected_permit in tool_decisions.items():
                actual = check_tool_permitted(profile_name, tool_name)
                assert actual == expected_permit, (
                    f"Permit drift: profile={profile_name!r} tool={tool_name!r} "
                    f"snapshot={expected_permit} live={actual}"
                )


class TestDeveloperBranchDispatch:
    """H.4a D-09 test group 3 — developer-branch dispatches against tool_overrides."""

    def test_check_tool_permitted_developer_branch_reads_tool_overrides(self, monkeypatch):
        """Developer profile permits only tools listed in tool_overrides; denies all others.

        Note: We monkeypatch PROFILES_DIR and add the dev fixture name to VALID_PROFILES
        for the duration of this test. Production code never sees test-dev-fixture.
        """
        from tools import apply_engine
        monkeypatch.setattr(apply_engine, "PROFILES_DIR", FIXTURE_DIR)
        monkeypatch.setattr(
            apply_engine, "VALID_PROFILES",
            apply_engine.VALID_PROFILES | {"test-dev-fixture"},
        )
        # Permit: in tool_overrides
        assert check_tool_permitted("test-dev-fixture", "produce-message") is True
        assert check_tool_permitted("test-dev-fixture", "consume-messages") is True
        assert check_tool_permitted("test-dev-fixture", "create-topics") is True
        # Deny: NOT in tool_overrides (would be permitted at engineer-tier under operator branch)
        assert check_tool_permitted("test-dev-fixture", "list-environments") is False
        assert check_tool_permitted("test-dev-fixture", "describe-cluster") is False
        # Deny: unknown tool name (fail-closed)
        assert check_tool_permitted("test-dev-fixture", "totally-fake-tool-name-xyz") is False


class TestPerFamilyInvariants:
    """H.4a D-07 — load_profile validates per-family invariants."""

    def test_operator_profile_missing_allowed_operations_raises(self, tmp_path, monkeypatch):
        bad_profile = {
            "name": "engineer",
            "description": "Operator missing required field",
            "family": "operator",
            # no allowed_operations
        }
        tmp_profiles = tmp_path / "profiles"
        tmp_profiles.mkdir()
        (tmp_profiles / "engineer.json").write_text(json.dumps(bad_profile))
        monkeypatch.setattr("tools.apply_engine.PROFILES_DIR", tmp_profiles)
        with pytest.raises(ValueError, match="allowed_operations"):
            load_profile("engineer")

    def test_developer_profile_missing_tool_overrides_raises(self, tmp_path, monkeypatch):
        from tools import apply_engine
        bad_profile = {
            "name": "test-dev-fixture",
            "description": "Developer missing required field",
            "family": "developer",
            "skill_blocklist": [],
            # no tool_overrides
        }
        tmp_profiles = tmp_path / "profiles"
        tmp_profiles.mkdir()
        (tmp_profiles / "test-dev-fixture.json").write_text(json.dumps(bad_profile))
        monkeypatch.setattr(apply_engine, "PROFILES_DIR", tmp_profiles)
        monkeypatch.setattr(
            apply_engine, "VALID_PROFILES",
            apply_engine.VALID_PROFILES | {"test-dev-fixture"},
        )
        with pytest.raises(ValueError, match="tool_overrides"):
            load_profile("test-dev-fixture")
