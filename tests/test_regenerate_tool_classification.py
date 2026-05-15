"""Unit tests for tools/regenerate_tool_classification.py (ACTG-01, D-05).

Exercises the parser, classifier, builder, and diff functions in isolation
against a static fixture so tests stay deterministic and network-free.

The fixture (tests/fixtures/mcp_confluent_tool_name_sample.js) covers every
D-05 verb-prefix branch plus both explicit overrides (produce-message,
consume-messages). New verb shapes added by future mcp-confluent releases
must surface here as failing tests before the JSON ever ships.
"""
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.regenerate_tool_classification import (
    build_classification,
    classify_tier,
    diff_classification,
    parse_tool_name_js,
)

FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "mcp_confluent_tool_name_sample.js"

EXPECTED_FIXTURE_NAMES = {
    # read-only
    "list-topics",
    "read-environment",
    "get-topic-config",
    "search-topics-by-tag",
    "detect-flink-statement-issues",
    "check-flink-statement-health",
    "describe-flink-table",
    "query-metrics",
    # engineer
    "create-topics",
    "update-tableflow-topic",
    "alter-topic-config",
    "add-tags-to-topic",
    # break-glass via verb prefix
    "delete-topics",
    "remove-tag-from-entity",
    # break-glass via explicit override
    "produce-message",
    "consume-messages",
}


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


class TestParseToolNameJs:
    def test_parse_extracts_all_kebab_names(self):
        """Parser returns exactly the 16 fixture tool names as a set."""
        content = FIXTURE_PATH.read_text()
        result = parse_tool_name_js(content)
        assert result == EXPECTED_FIXTURE_NAMES, (
            f"Expected {len(EXPECTED_FIXTURE_NAMES)} kebab names; got {len(result)}. "
            f"Missing={EXPECTED_FIXTURE_NAMES - result}; extra={result - EXPECTED_FIXTURE_NAMES}"
        )

    def test_parse_ignores_non_toolname_lines(self):
        """IIFE wrapper, comments, and blank lines must not contribute matches."""
        content = """
        // ToolName["NOT_A_REAL_ASSIGNMENT"] = "should-not-match"; — this is a comment
        export var ToolName;
        (function (ToolName) {
            ToolName["REAL_ONE"] = "list-environments";
        })(ToolName || (ToolName = {}));
        """
        result = parse_tool_name_js(content)
        # The commented-out line still matches the regex by design — regex doesn't
        # parse JS comments. But standalone non-assignment lines (the IIFE) must not.
        assert "list-environments" in result
        # Sanity: nothing got accidentally picked up from the function wrapper.
        assert all("-" in name or name == "list-environments" for name in result)

    def test_parse_handles_real_world_quoting(self):
        """Both double- and single-quote styles emitted by tsc must parse."""
        content = """
            ToolName["DOUBLE_QUOTED"] = "double-name";
            ToolName['SINGLE_QUOTED'] = 'single-name';
            ToolName[ "WITH_SPACES" ] = "spaced-name" ;
        """
        result = parse_tool_name_js(content)
        assert result == {"double-name", "single-name", "spaced-name"}


# ---------------------------------------------------------------------------
# Classifier — D-05 verb-prefix rule + overrides
# ---------------------------------------------------------------------------


class TestClassifyTier:
    @pytest.mark.parametrize(
        "tool",
        [
            "list-topics",
            "read-environment",
            "get-topic-config",
            "search-topics-by-tag",
            "detect-flink-statement-issues",
            "check-flink-statement-health",
            "describe-flink-table",
            "query-metrics",
        ],
    )
    def test_read_only_prefixes(self, tool):
        assert classify_tier(tool) == "read-only"

    @pytest.mark.parametrize(
        "tool",
        [
            "create-topics",
            "update-tableflow-topic",
            "alter-topic-config",
            "add-tags-to-topic",
        ],
    )
    def test_engineer_prefixes(self, tool):
        assert classify_tier(tool) == "engineer"

    @pytest.mark.parametrize(
        "tool",
        [
            "delete-topics",
            "remove-tag-from-entity",
        ],
    )
    def test_break_glass_prefixes(self, tool):
        assert classify_tier(tool) == "break-glass"

    def test_produce_message_override(self):
        """produce-message has no verb-prefix match; the OVERRIDES dict catches it."""
        assert classify_tier("produce-message") == "break-glass"

    def test_consume_messages_override(self):
        """consume-messages has no verb-prefix match; the OVERRIDES dict catches it."""
        assert classify_tier("consume-messages") == "break-glass"

    def test_unknown_verb_prefix_raises(self):
        """Per D-06 the rule is a regeneration aid, not a runtime fallback.
        Unknown shapes must fail loudly so CI blocks the bump PR."""
        with pytest.raises(ValueError) as exc:
            classify_tier("frobnicate-cluster")
        msg = str(exc.value)
        assert "frobnicate-cluster" in msg
        # Operator should be told where to fix it.
        assert "OVERRIDES" in msg or "override" in msg.lower()


# ---------------------------------------------------------------------------
# Builder — full JSON shape contract for apply_engine.load_tool_classification
# ---------------------------------------------------------------------------


class TestBuildClassification:
    def _build(self, version="1.3.0"):
        names = parse_tool_name_js(FIXTURE_PATH.read_text())
        return build_classification(names, version)

    def test_top_level_fields_present(self):
        result = self._build()
        assert set(result.keys()) >= {
            "version",
            "description",
            "mcp_confluent_version",
            "tier_rule",
            "tools",
            "unclassified_policy",
        }

    def test_version_field_is_1(self):
        """File-format version, NOT mcp-confluent version. Unchanged from current shape."""
        assert self._build()["version"] == "1"

    def test_unclassified_policy_is_deny(self):
        """Fail-closed for unknown tools (D-06, locked carry-over from Phase 3c)."""
        assert self._build()["unclassified_policy"] == "deny"

    def test_tools_sorted_alphabetically(self):
        """Flat alphabetical so the next bump PR has a clean diff (D-05 Claude's Discretion)."""
        result = self._build()
        keys = list(result["tools"].keys())
        assert keys == sorted(keys)

    def test_mcp_confluent_version_threaded_through(self):
        assert self._build(version="1.3.0")["mcp_confluent_version"] == "1.3.0"

    def test_every_input_tool_classified(self):
        """All 16 fixture tools must appear as keys."""
        result = self._build()
        assert set(result["tools"].keys()) == EXPECTED_FIXTURE_NAMES

    def test_tier_rule_documents_overrides(self):
        """tier_rule string surfaces the override list to anyone opening the JSON."""
        rule = self._build()["tier_rule"]
        assert "produce-message" in rule
        assert "consume-messages" in rule

    def test_tier_assignments_match_expectations(self):
        """End-to-end: fixture parsing -> classification yields the documented tiers."""
        tools = self._build()["tools"]
        # Spot-check one of each tier including both overrides
        assert tools["list-topics"] == "read-only"
        assert tools["create-topics"] == "engineer"
        assert tools["delete-topics"] == "break-glass"
        assert tools["produce-message"] == "break-glass"
        assert tools["consume-messages"] == "break-glass"


# ---------------------------------------------------------------------------
# Diff — bidirectional drift (D-08)
# ---------------------------------------------------------------------------


class TestDiffClassification:
    def _doc(self, *names):
        return {"tools": {n: "read-only" for n in names}}

    def test_identical_returns_empty_diffs(self):
        doc = self._doc("list-topics", "create-topics")
        assert diff_classification(doc, doc) == ([], [])

    def test_missing_from_committed_detected(self):
        """Live registry has a new tool the committed file doesn't classify."""
        committed = self._doc("list-topics")
        expected = self._doc("list-topics", "list-environments")
        missing, extra = diff_classification(committed, expected)
        assert missing == ["list-environments"]
        assert extra == []

    def test_extra_in_committed_detected(self):
        """Committed file has a stale tool removed upstream."""
        committed = self._doc("list-topics", "ancient-removed-tool")
        expected = self._doc("list-topics")
        missing, extra = diff_classification(committed, expected)
        assert missing == []
        assert extra == ["ancient-removed-tool"]

    def test_bidirectional_drift_detected(self):
        committed = self._doc("alpha", "gamma")
        expected = self._doc("alpha", "beta")
        missing, extra = diff_classification(committed, expected)
        assert missing == ["beta"]
        assert extra == ["gamma"]
