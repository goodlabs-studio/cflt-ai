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
