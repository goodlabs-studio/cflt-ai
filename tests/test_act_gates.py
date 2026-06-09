"""Unit tests for act_gates.py gate chain (ACT-02, ACT-03, ACT-06)."""
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.act_gates import (
    gate1_canon_compliance,
    gate2_fsi_dsp_coverage,
    gate3_confluent_docs_schema,
    gate4_mcp_confluent_state,
    run_gate_chain,
    GATE_NAMES,
)

GATE_RESULT_KEYS = {"gate", "status", "detail", "evidence"}
VALID_STATUSES = {"pass", "fail", "skipped"}


# ---------------------------------------------------------------------------
# TestGateNames
# ---------------------------------------------------------------------------


class TestGateNames:
    def test_gate_names_count(self):
        assert len(GATE_NAMES) == 4

    def test_gate_names_order(self):
        assert GATE_NAMES == [
            "canon_compliance",
            "fsi_dsp_coverage",
            "confluent_docs_schema",
            "mcp_confluent_state",
        ]


# ---------------------------------------------------------------------------
# TestGateResultStructure
# ---------------------------------------------------------------------------


class TestGateResultStructure:
    """Every gate function returns a dict with the expected keys and valid status."""

    @pytest.mark.parametrize(
        "gate_fn,req_text",
        [
            (gate1_canon_compliance, "create a topic with replication factor 3"),
            (gate2_fsi_dsp_coverage, "create a topic for trade events"),
            (gate3_confluent_docs_schema, "any request"),
            (gate4_mcp_confluent_state, "any request"),
        ],
    )
    def test_gate_result_structure(self, gate_fn, req_text):
        result = gate_fn(req_text)
        assert isinstance(result, dict), "gate result must be a dict"
        assert GATE_RESULT_KEYS.issubset(result.keys()), (
            f"missing keys: {GATE_RESULT_KEYS - result.keys()}"
        )
        assert result["status"] in VALID_STATUSES, (
            f"status must be pass|fail|skipped, got: {result['status']}"
        )
        assert isinstance(result["gate"], str), "gate field must be a string"
        assert isinstance(result["detail"], str), "detail field must be a string"
        assert isinstance(result["evidence"], list), "evidence field must be a list"


# ---------------------------------------------------------------------------
# TestGate1CanonCompliance
# ---------------------------------------------------------------------------


class TestGate1CanonCompliance:
    def test_gate1_pass_on_compliant_request(self):
        """Neutral/compliant request does not violate canon."""
        result = gate1_canon_compliance("create a topic with replication factor 3 and DR")
        assert result["status"] == "pass"
        assert result["gate"] == "canon_compliance"

    def test_gate1_fail_on_noncompliant_acks(self):
        """Request mentioning acks=0 contradicts canon producer.acks=all."""
        result = gate1_canon_compliance("set acks=0 for maximum throughput")
        assert result["status"] == "fail"
        assert result["gate"] == "canon_compliance"
        assert "acks" in str(result["evidence"]).lower() or "acks" in result["detail"].lower()

    def test_gate1_pass_with_dr_topic(self):
        """Request mentioning topic with DR is neutral — no violation."""
        result = gate1_canon_compliance("create a topic with DR replication")
        assert result["status"] == "pass"

    def test_gate1_fail_auto_commit(self):
        """Request mentioning enable.auto.commit=true violates canon consumer config."""
        result = gate1_canon_compliance("configure consumer with enable.auto.commit=true")
        assert result["status"] == "fail"

    def test_gate1_honors_selected_industry(self):
        """A valid operator industry resolves that industry's canon stack and passes."""
        result = gate1_canon_compliance(
            "create a topic with replication factor 3", industry="retail"
        )
        assert result["status"] == "pass"

    def test_gate1_default_industry_is_fsi(self):
        """No industry == fsi default — byte-identical to passing industry='fsi'."""
        a = gate1_canon_compliance("create a topic with DR replication")
        b = gate1_canon_compliance("create a topic with DR replication", industry="fsi")
        assert a["status"] == b["status"] == "pass"

    def test_gate1_unknown_industry_fails_cleanly(self):
        """A typo'd industry fails the gate (not a crash) with a helpful message."""
        result = gate1_canon_compliance("create a topic", industry="bogus")
        assert result["status"] == "fail"
        assert "unknown industry" in result["detail"].lower()

    def test_run_gate_chain_threads_industry_to_gate1(self):
        """run_gate_chain passes industry to gate 1; a bad industry fails the chain fast."""
        results = run_gate_chain("create a topic", industry="bogus")
        assert results[0]["gate"] == "canon_compliance"
        assert results[0]["status"] == "fail"
        assert len(results) == 1  # fail-fast stops the chain


# ---------------------------------------------------------------------------
# TestGate2FsiDspCoverage
# ---------------------------------------------------------------------------


class TestGate2FsiDspCoverage:
    def test_gate2_pass_matches_manifest_artifact_topic(self):
        """'create a topic' should match module/topic."""
        result = gate2_fsi_dsp_coverage("create a topic for trade events")
        assert result["status"] == "pass"
        assert result["gate"] == "fsi_dsp_coverage"
        assert "module/topic" in str(result["evidence"])

    def test_gate2_fail_no_matching_artifact_mongodb(self):
        """'provision a MongoDB cluster' has no matching artifact in MANIFEST."""
        result = gate2_fsi_dsp_coverage("provision a MongoDB Atlas cluster")
        assert result["status"] == "fail"
        assert result["gate"] == "fsi_dsp_coverage"
        assert "no matching artifact" in result["detail"].lower()

    def test_gate2_prefers_terraform_module_for_create(self):
        """'create topic' should prefer terraform-module over ansible-role."""
        result = gate2_fsi_dsp_coverage("create a topic")
        assert result["status"] == "pass"
        # module/topic (terraform-module) should be in evidence, not role/cp_topic
        evidence_str = str(result["evidence"])
        assert "module/topic" in evidence_str

    def test_gate2_pass_flink_request(self):
        """Request about Flink should match module/flink."""
        result = gate2_fsi_dsp_coverage("provision a Flink compute pool")
        assert result["status"] == "pass"


# ---------------------------------------------------------------------------
# TestGate3Stub
# ---------------------------------------------------------------------------


class TestGate3Stub:
    def test_gate3_stub_returns_pass(self):
        result = gate3_confluent_docs_schema("any request about schemas")
        assert result["status"] == "pass"
        assert result["gate"] == "confluent_docs_schema"
        assert GATE_RESULT_KEYS.issubset(result.keys())

    def test_gate3_returns_deferred_detail(self):
        result = gate3_confluent_docs_schema("test")
        assert "deferred" in result["detail"].lower() or "mcp" in result["detail"].lower()


# ---------------------------------------------------------------------------
# TestGate4Stub
# ---------------------------------------------------------------------------


class TestGate4Stub:
    def test_gate4_stub_returns_pass(self):
        result = gate4_mcp_confluent_state("check cluster state")
        assert result["status"] == "pass"
        assert result["gate"] == "mcp_confluent_state"
        assert GATE_RESULT_KEYS.issubset(result.keys())

    def test_gate4_returns_deferred_detail(self):
        result = gate4_mcp_confluent_state("test")
        assert "deferred" in result["detail"].lower() or "mcp" in result["detail"].lower()


# ---------------------------------------------------------------------------
# TestRunGateChain
# ---------------------------------------------------------------------------


class TestRunGateChain:
    def test_run_gate_chain_all_pass_returns_results(self):
        """Compliant request with no bypass returns results for all gates."""
        results = run_gate_chain("create a topic with replication factor 3")
        # Should have at least 1 result; if all pass, should have 4
        assert len(results) >= 1
        for r in results:
            assert r["status"] in VALID_STATUSES

    def test_run_gate_chain_bypass_returns_skipped(self):
        """bypass=['mcp_confluent_state'] makes gate 4 return status=skipped."""
        results = run_gate_chain(
            "create a topic with replication factor 3",
            bypass=["mcp_confluent_state"],
        )
        gate4_results = [r for r in results if r["gate"] == "mcp_confluent_state"]
        assert len(gate4_results) == 1
        assert gate4_results[0]["status"] == "skipped"

    def test_run_gate_chain_fail_fast(self):
        """Gate 1 failure stops chain — only 1 result returned."""
        results = run_gate_chain("set acks=0 for maximum throughput")
        assert len(results) == 1
        assert results[0]["status"] == "fail"
        assert results[0]["gate"] == "canon_compliance"

    def test_run_gate_chain_multiple_bypass(self):
        """Multiple bypass entries both return skipped."""
        results = run_gate_chain(
            "create a topic with replication factor 3",
            bypass=["confluent_docs_schema", "mcp_confluent_state"],
        )
        bypassed = {r["gate"]: r["status"] for r in results}
        assert bypassed.get("confluent_docs_schema") == "skipped"
        assert bypassed.get("mcp_confluent_state") == "skipped"

    def test_run_gate_chain_no_bypass_param_defaults_to_empty(self):
        """run_gate_chain works with no bypass argument (defaults to None / empty)."""
        results = run_gate_chain("create a topic with DR replication")
        assert isinstance(results, list)
        assert len(results) >= 1

    def test_run_gate_chain_with_overlay(self):
        """run_gate_chain accepts optional overlay parameter without error."""
        results = run_gate_chain(
            "create a topic with replication factor 3",
            overlay="acme-bank",
        )
        assert isinstance(results, list)


# ---------------------------------------------------------------------------
# TestReadOnlyConstraint (ACT-06)
# ---------------------------------------------------------------------------


class TestReadOnlyConstraint:
    def test_no_write_tool_invocations_in_source(self):
        """act_gates.py must not contain mcp-confluent write tool names."""
        source_path = PROJECT_ROOT / "tools" / "act_gates.py"
        source_text = source_path.read_text()
        for forbidden in ("create_topic", "delete_topic", "update_topic"):
            assert forbidden not in source_text, (
                f"Forbidden write-tool reference found in act_gates.py: {forbidden}"
            )

    def test_module_docstring_contains_read_only_constraint(self):
        """Module docstring must state 'Never generates inline Terraform'."""
        source_path = PROJECT_ROOT / "tools" / "act_gates.py"
        source_text = source_path.read_text()
        assert "Never generates inline Terraform" in source_text, (
            "act_gates.py module docstring must contain 'Never generates inline Terraform'"
        )
