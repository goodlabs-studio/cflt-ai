"""
Phase H.4b — Per-family isolation tests.

Proves that operator-family profiles cannot invoke developer-family tools and
developer-family profiles cannot invoke operator-tier-only tools, AND that
/dsp:apply is blocked under any developer profile.

Companion to tests/test_profile_gating.py (H.4a family schema tests).
"""
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.apply_engine import (
    check_tool_permitted,
    check_skill_permitted,
    load_profile,
    load_tool_classification,
)

SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


class TestOperatorCannotInvokeDeveloperTools:
    """Operator profiles cannot invoke tools that ONLY appear in developer tool_overrides.

    The contract is per-tier: at the read-only operator tier, high-tier data-plane
    tools that the developer/sandbox profile explicitly permits (produce-message,
    create-topics, delete-topics, alter-topic-config) must remain denied. This
    proves the developer profile's tool_overrides cannot leak into the operator
    branch's tier cascade.
    """

    @pytest.fixture
    def developer_only_tools(self):
        """Tools in developer/sandbox tool_overrides that exist in classification."""
        dev_profile = load_profile("developer/sandbox")
        classification = load_tool_classification()["tools"]
        return [t for t in dev_profile["tool_overrides"] if t in classification]

    @pytest.mark.parametrize("operator_profile", ["read-only"])
    def test_read_only_cannot_invoke_developer_data_plane_tools(
        self, operator_profile, developer_only_tools
    ):
        """read-only operator cannot invoke produce-message, create-topics, etc."""
        # High-tier dev tools the developer profile permits but read-only tier denies
        high_tier_dev_tools = [
            "produce-message",
            "create-topics",
            "delete-topics",
            "alter-topic-config",
        ]
        for tool in high_tier_dev_tools:
            if tool in developer_only_tools:
                assert check_tool_permitted(operator_profile, tool) is False, (
                    f"read-only should NOT be permitted {tool!r} "
                    f"(operator tier cascade should deny — developer overrides must not leak)"
                )


class TestDeveloperCannotInvokeOperatorOnlyTools:
    """developer/sandbox cannot invoke tools that are NOT in its tool_overrides.

    Fail-closed contract: anything outside the explicit tool_overrides map is denied
    regardless of what tier the operator-branch classification table would assign.
    """

    @pytest.fixture
    def operator_only_tools(self):
        """Tools in the classification table that developer/sandbox does NOT list."""
        dev_profile = load_profile("developer/sandbox")
        classification = load_tool_classification()["tools"]
        return [t for t in classification if t not in dev_profile["tool_overrides"]]

    def test_developer_cannot_invoke_operator_only_tools(self, operator_only_tools):
        """For at least 3 operator-only tools, developer/sandbox returns False."""
        assert len(operator_only_tools) >= 3, (
            "Need at least 3 operator-only tools for a meaningful test"
        )
        tested = 0
        for tool in operator_only_tools:
            assert check_tool_permitted("developer/sandbox", tool) is False, (
                f"developer/sandbox should NOT be permitted {tool!r} "
                f"(not in tool_overrides — fail-closed)"
            )
            tested += 1
            if tested >= 3:
                break  # 3 is enough to prove the contract

    def test_developer_cannot_invoke_destructive_operator_tools(self):
        """Explicit destructive-tool test: delete-* tools not in dev overrides."""
        # Pick destructive operator tools that ARE in the classification but NOT
        # in developer/sandbox's tool_overrides (delete-topics IS in dev's overrides
        # at the sandbox tier, so it's excluded from this test).
        destructive = [
            "delete-connector",
            "delete-schema",
            "delete-tag",
            "delete-tableflow-topic",
            "delete-tableflow-catalog-integration",
            "remove-tag-from-entity",
        ]
        classification = load_tool_classification()["tools"]
        dev_overrides = load_profile("developer/sandbox")["tool_overrides"]
        # Filter to those present in classification AND not in dev's overrides
        present = [t for t in destructive if t in classification and t not in dev_overrides]
        assert len(present) >= 3, (
            f"Need at least 3 destructive operator-only tools for a meaningful test; "
            f"found {len(present)}: {present}"
        )
        for tool in present:
            assert check_tool_permitted("developer/sandbox", tool) is False, (
                f"developer/sandbox MUST deny destructive {tool!r}"
            )


class TestDspApplyFailsClosedUnderDeveloper:
    """/dsp:apply is in developer/sandbox's skill_blocklist — check_skill_permitted returns False.

    Operator profiles (read-only, engineer, break-glass) have no skill_blocklist field
    and thus permit /dsp:apply at the family-gate level (downstream gates may still deny).
    """

    def test_dsp_apply_blocked_under_developer_sandbox(self):
        assert check_skill_permitted("developer/sandbox", "dsp-apply") is False

    @pytest.mark.parametrize("operator_profile", ["read-only", "engineer", "break-glass"])
    def test_dsp_apply_permitted_under_operator_profiles(self, operator_profile):
        assert check_skill_permitted(operator_profile, "dsp-apply") is True

    def test_unknown_skill_permitted_under_developer_when_not_in_blocklist(self):
        """Skills not listed in blocklist are permitted (allow-by-default within family)."""
        assert check_skill_permitted("developer/sandbox", "wiki-validate") is True
        assert check_skill_permitted("developer/sandbox", "ask") is True


class TestCrossFamilyLoadIsolation:
    """load_profile() returns the correct family for each profile without cross-contamination."""

    def test_developer_sandbox_loads_as_developer_family(self):
        p = load_profile("developer/sandbox")
        assert p["family"] == "developer"
        assert "tool_overrides" in p
        assert "allowed_operations" not in p

    @pytest.mark.parametrize("operator_profile", ["read-only", "engineer", "break-glass"])
    def test_operator_profiles_load_as_operator_family(self, operator_profile):
        p = load_profile(operator_profile)
        assert p["family"] == "operator"
        assert "allowed_operations" in p
        assert "tool_overrides" not in p


class TestDeveloperSandboxPermitsSnapshot:
    """Regression guard: the (developer/sandbox x tool) permit matrix matches the committed baseline.

    Regenerator one-liner (run from project root):
        python3 -c "
        import json
        from tools.apply_engine import check_tool_permitted, load_tool_classification
        tc = load_tool_classification()
        snapshot = {'developer/sandbox': {t: check_tool_permitted('developer/sandbox', t) for t in sorted(tc['tools'])}}
        print(json.dumps(snapshot, indent=2))
        " > tests/snapshots/h4b_developer_sandbox_permits.json
    """

    def test_developer_sandbox_permits_match_snapshot(self):
        snapshot_path = SNAPSHOT_DIR / "h4b_developer_sandbox_permits.json"
        assert snapshot_path.exists(), (
            "Snapshot missing — regenerate via the one-liner in this test's docstring"
        )
        snapshot = json.loads(snapshot_path.read_text())
        assert "developer/sandbox" in snapshot
        for tool, expected_permit in snapshot["developer/sandbox"].items():
            actual = check_tool_permitted("developer/sandbox", tool)
            assert actual == expected_permit, (
                f"developer/sandbox permit drift: tool={tool!r} "
                f"snapshot={expected_permit} live={actual}"
            )
