"""
Golden harness structural tests for /dsp:plan act rail (ACT-05, ACT-06, ACT-07).
These tests verify case file structure and distribution, NOT skill execution.
LLM evaluation requires CI + model API and is deferred to Phase 4.
"""
import yaml
from pathlib import Path
import pytest

CASES_DIR = Path(__file__).parent / "cases"
REQUIRED_FIELDS = {
    "id", "request", "expected_artifact", "floor_model",
    "tags", "required_claims", "forbidden_claims", "negative_space"
}
VALID_FLOOR_MODELS = {"haiku", "sonnet"}
VALID_ARTIFACT_TYPES = {
    "module/topic",
    "module/flink",
    "role/cp_topic",
    "role/cp_schema",
    "role/cp_rbac",
    "role/cp_connect",
    "role/cp_dr_mm2",
    "role/cp_dr_mrc",
    "role/cp_observability",
    "role/cfk_operator",
    "role/cfk_topic",
    "scenario/cc-aws",
    "scenario/cc-azure",
    "scenario/cc-gcp",
    "scenario/cfk-openshift",
    "scenario/cp-rhel",
    "scenario/private-cloud",
    # Apply cases reference script artifacts (DR failover/failback, FSI ops scripts)
    "script/mirror-failover",
    "script/mirror-failback",
    "script/fsi-dr",
    "script/validate-fips",
    # Phase 11: LinuxONE accelerator artifact (kustomize-layered, dispatched
    # by execute_accelerator() in tools/apply_engine.py)
    "accelerator/confluent-on-linuxone",
    None,  # negative-space cases have no artifact
}


def load_case(path: Path) -> dict:
    """Parse YAML front matter from a golden case file."""
    content = path.read_text()
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    return yaml.safe_load(content[3:end]) or {}


ALL_CASES = sorted(CASES_DIR.glob("*.md")) if CASES_DIR.exists() else []


class TestGoldenActHarnessStructure:
    """ACT-05: Verify act case file structure and minimum coverage."""

    def test_cases_directory_exists(self):
        assert CASES_DIR.exists(), f"Golden cases directory missing: {CASES_DIR}"

    def test_minimum_case_count(self):
        assert len(ALL_CASES) >= 20, (
            f"Need >= 20 golden cases, found {len(ALL_CASES)}"
        )

    def test_minimum_negative_space_cases(self):
        negative = [
            p for p in ALL_CASES
            if load_case(p).get("negative_space") is True
        ]
        assert len(negative) >= 3, (
            f"Need >= 3 negative-space cases, found {len(negative)}"
        )

    def test_terraform_module_cases_exist(self):
        module_cases = [
            p for p in ALL_CASES
            if str(load_case(p).get("expected_artifact", "")).startswith("module/")
        ]
        assert len(module_cases) >= 2, (
            f"Need >= 2 cases with expected_artifact starting with 'module/', found {len(module_cases)}"
        )

    def test_ansible_role_cases_exist(self):
        role_cases = [
            p for p in ALL_CASES
            if str(load_case(p).get("expected_artifact", "")).startswith("role/")
        ]
        assert len(role_cases) >= 2, (
            f"Need >= 2 cases with expected_artifact starting with 'role/', found {len(role_cases)}"
        )

    def test_case_id_unique(self):
        ids = [load_case(p).get("id") for p in ALL_CASES]
        ids = [i for i in ids if i is not None]
        assert len(ids) == len(set(ids)), (
            f"Duplicate case IDs found: {[i for i in ids if ids.count(i) > 1]}"
        )

    @pytest.mark.parametrize("case_path", ALL_CASES, ids=lambda p: p.stem)
    def test_case_has_required_fields(self, case_path):
        fm = load_case(case_path)
        missing = REQUIRED_FIELDS - set(fm.keys())
        assert not missing, f"{case_path.name} missing fields: {missing}"

    @pytest.mark.parametrize("case_path", ALL_CASES, ids=lambda p: p.stem)
    def test_case_has_valid_floor_model(self, case_path):
        fm = load_case(case_path)
        assert fm.get("floor_model") in VALID_FLOOR_MODELS, (
            f"{case_path.name}: invalid floor_model '{fm.get('floor_model')}'"
        )

    @pytest.mark.parametrize("case_path", ALL_CASES, ids=lambda p: p.stem)
    def test_required_claims_is_list(self, case_path):
        fm = load_case(case_path)
        assert isinstance(fm.get("required_claims", []), list), (
            f"{case_path.name}: required_claims must be a list"
        )

    @pytest.mark.parametrize("case_path", ALL_CASES, ids=lambda p: p.stem)
    def test_forbidden_claims_is_list(self, case_path):
        fm = load_case(case_path)
        assert isinstance(fm.get("forbidden_claims", []), list), (
            f"{case_path.name}: forbidden_claims must be a list"
        )

    @pytest.mark.parametrize("case_path", ALL_CASES, ids=lambda p: p.stem)
    def test_negative_space_has_null_artifact(self, case_path):
        fm = load_case(case_path)
        if fm.get("negative_space") is True:
            assert fm.get("expected_artifact") is None, (
                f"{case_path.name}: negative_space case must have expected_artifact: null, "
                f"got '{fm.get('expected_artifact')}'"
            )

    @pytest.mark.parametrize("case_path", ALL_CASES, ids=lambda p: p.stem)
    def test_positive_case_has_valid_artifact(self, case_path):
        fm = load_case(case_path)
        if fm.get("negative_space") is False:
            assert fm.get("expected_artifact") in VALID_ARTIFACT_TYPES, (
                f"{case_path.name}: invalid expected_artifact '{fm.get('expected_artifact')}'"
            )


class TestNegativeSpaceCoverage:
    """ACT-06: Verify negative-space cases enforce no-inline-Terraform constraint."""

    def test_negative_cases_forbid_inline_terraform(self):
        negative_cases = [
            p for p in ALL_CASES
            if load_case(p).get("negative_space") is True
        ]
        assert len(negative_cases) >= 3, (
            f"Need >= 3 negative-space cases to test, found {len(negative_cases)}"
        )
        for case_path in negative_cases:
            fm = load_case(case_path)
            forbidden = fm.get("forbidden_claims", [])
            has_terraform_forbid = any(
                'resource "confluent_' in str(claim)
                for claim in forbidden
            )
            assert has_terraform_forbid, (
                f"{case_path.name}: negative_space case must forbid 'resource \"confluent_' "
                f"in forbidden_claims. Got: {forbidden}"
            )

    def test_negative_cases_require_no_match_response(self):
        negative_cases = [
            p for p in ALL_CASES
            if load_case(p).get("negative_space") is True
        ]
        for case_path in negative_cases:
            fm = load_case(case_path)
            required = fm.get("required_claims", [])
            has_no_match = any(
                "no matching artifact" in str(claim)
                for claim in required
            )
            assert has_no_match, (
                f"{case_path.name}: negative_space case must include 'no matching artifact' "
                f"in required_claims. Got: {required}"
            )


class TestFloorModelDistribution:
    """ACT-07: Verify haiku and sonnet cases exist at sufficient count."""

    def test_haiku_cases_exist(self):
        haiku = [p for p in ALL_CASES if load_case(p).get("floor_model") == "haiku"]
        assert len(haiku) >= 5, f"Need >= 5 haiku-floor cases, found {len(haiku)}"

    def test_sonnet_cases_exist(self):
        sonnet = [p for p in ALL_CASES if load_case(p).get("floor_model") == "sonnet"]
        assert len(sonnet) >= 5, f"Need >= 5 sonnet-floor cases, found {len(sonnet)}"


# ---------------------------------------------------------------------------
# Apply-specific constants (ACTA-06 -- structural correctness for apply rail)
# ---------------------------------------------------------------------------

APPLY_REQUIRED_FIELDS = {"skill", "profile", "confirmation", "expected_incident"}
VALID_PROFILES = {"read-only", "engineer", "break-glass"}
VALID_CONFIRMATIONS = {"confirmed", "blocked", "bypass_attempt"}
APPLY_CASES = [
    p for p in ALL_CASES
    if load_case(p).get("skill") == "/dsp:apply"
] if ALL_CASES else []


class TestGoldenApplyHarnessStructure:
    """ACTA-06: Verify apply case structure, profile enforcement, and bypass coverage."""

    def test_minimum_apply_case_count(self):
        assert len(APPLY_CASES) >= 10, (
            f"Need >= 10 apply cases, found {len(APPLY_CASES)}"
        )

    def test_minimum_apply_negative_space_cases(self):
        negative = [
            p for p in APPLY_CASES
            if load_case(p).get("negative_space") is True
        ]
        assert len(negative) >= 3, (
            f"Need >= 3 negative-space apply cases, found {len(negative)}"
        )

    @pytest.mark.parametrize("case_path", APPLY_CASES, ids=lambda p: p.stem)
    def test_apply_case_has_required_fields(self, case_path):
        fm = load_case(case_path)
        missing = APPLY_REQUIRED_FIELDS - set(fm.keys())
        assert not missing, f"{case_path.name} missing apply fields: {missing}"

    @pytest.mark.parametrize("case_path", APPLY_CASES, ids=lambda p: p.stem)
    def test_apply_case_has_valid_profile(self, case_path):
        fm = load_case(case_path)
        # Negative-space cases may test unknown profile names (e.g., "admin") --
        # skip the valid-profile check for those cases since testing rejection
        # of unknown profiles is the point of the case.
        if fm.get("negative_space") is True:
            return
        assert fm.get("profile") in VALID_PROFILES, (
            f"{case_path.name}: invalid profile '{fm.get('profile')}', "
            f"must be one of {VALID_PROFILES}"
        )

    @pytest.mark.parametrize("case_path", APPLY_CASES, ids=lambda p: p.stem)
    def test_apply_case_has_valid_confirmation(self, case_path):
        fm = load_case(case_path)
        assert fm.get("confirmation") in VALID_CONFIRMATIONS, (
            f"{case_path.name}: invalid confirmation '{fm.get('confirmation')}', "
            f"must be one of {VALID_CONFIRMATIONS}"
        )

    @pytest.mark.parametrize("case_path", APPLY_CASES, ids=lambda p: p.stem)
    def test_apply_case_skill_is_dsp_apply(self, case_path):
        fm = load_case(case_path)
        assert fm.get("skill") == "/dsp:apply", (
            f"{case_path.name}: skill must be '/dsp:apply', got '{fm.get('skill')}'"
        )

    @pytest.mark.parametrize("case_path", APPLY_CASES, ids=lambda p: p.stem)
    def test_negative_apply_case_no_incident(self, case_path):
        fm = load_case(case_path)
        if fm.get("negative_space") is True:
            assert fm.get("expected_incident") is False, (
                f"{case_path.name}: negative-space apply case must have "
                f"expected_incident: false, got '{fm.get('expected_incident')}'"
            )

    @pytest.mark.parametrize("case_path", APPLY_CASES, ids=lambda p: p.stem)
    def test_positive_apply_case_has_incident(self, case_path):
        fm = load_case(case_path)
        if fm.get("negative_space") is False and fm.get("confirmation") == "confirmed":
            assert fm.get("expected_incident") is True, (
                f"{case_path.name}: positive apply case with confirmation=confirmed must have "
                f"expected_incident: true, got '{fm.get('expected_incident')}'"
            )

    def test_apply_negative_cases_forbid_inline_terraform(self):
        negative_apply = [
            p for p in APPLY_CASES
            if load_case(p).get("negative_space") is True
        ]
        assert len(negative_apply) >= 3, (
            f"Need >= 3 negative-space apply cases, found {len(negative_apply)}"
        )
        for case_path in negative_apply:
            fm = load_case(case_path)
            forbidden = fm.get("forbidden_claims", [])
            has_terraform_forbid = any(
                'resource "confluent_' in str(claim)
                for claim in forbidden
            )
            assert has_terraform_forbid, (
                f"{case_path.name}: negative-space apply case must forbid "
                f"'resource \"confluent_' in forbidden_claims. Got: {forbidden}"
            )

    def test_total_case_count(self):
        assert len(ALL_CASES) >= 32, (
            f"Need >= 32 total golden cases (22 plan + 10 apply), found {len(ALL_CASES)}"
        )


# ---------------------------------------------------------------------------
# Accelerator-specific cases (Phase 11 — LinuxONE kustomize-layered artifact)
# ---------------------------------------------------------------------------

# Canonical layer → canon_key mapping for accelerator/confluent-on-linuxone.
# Source of truth: raw/repos/fsi-dsp/MANIFEST.yaml apply_sequence entries +
# tools/check-canon-parity.py MODULE_TO_CANON_KEY composite keys (Plan 11-01).
# Any divergence here against either source is a DRIFT-1 blocking violation.
ACCELERATOR_LAYER_TO_CANON_KEY = {
    "01-rbac": "fsi.security.mds-rbac",
    "02-tls": "fsi.security.tls-fips",
    "03-schema-governance": "fsi.schema.compatibility-full-transitive",
    "04-audit": "fsi.audit.events-retention",
    "05-flink": "fsi.flink.environment-mtls",
}


class TestAcceleratorCases:
    """Phase 11 — coverage assertion for the 5 accelerator-layer golden cases.

    Asserts that the golden harness gains >= 5 accelerator cases (one per
    kustomize layer of accelerator/confluent-on-linuxone), each referencing
    the artifact by MANIFEST ID and carrying the layer's canonical canon_key
    in required_claims. Cross-validates against Plan 11-01's
    MODULE_TO_CANON_KEY mapping via shared layer→canon_key dict.
    """

    def test_at_least_5_accelerator_cases_exist(self):
        """Phase 11 success criterion 1 — golden harness gains >= 5 accelerator cases."""
        accel_cases = list(CASES_DIR.glob("accelerator-*.md"))
        assert len(accel_cases) >= 5, (
            f"Expected >= 5 accelerator-* cases, found {len(accel_cases)}: "
            f"{[c.name for c in accel_cases]}"
        )

    @pytest.mark.parametrize(
        "layer,canon_key",
        list(ACCELERATOR_LAYER_TO_CANON_KEY.items()),
        ids=list(ACCELERATOR_LAYER_TO_CANON_KEY.keys()),
    )
    def test_each_layer_has_a_case(self, layer, canon_key):
        """One case per kustomize layer; each references the canonical canon_key."""
        matches = [
            c for c in CASES_DIR.glob("accelerator-*.md")
            if f"--layer {layer}" in c.read_text()
        ]
        assert len(matches) >= 1, f"No accelerator case for layer {layer}"
        for c in matches:
            content = c.read_text()
            # Each case must reference (a) the accelerator artifact ID,
            # (b) the layer name, (c) the canonical canon_key value.
            assert "accelerator/confluent-on-linuxone" in content, (
                f"Case {c.name} missing accelerator artifact ID reference"
            )
            assert layer in content, (
                f"Case {c.name} for layer {layer} missing layer name"
            )
            assert canon_key in content, (
                f"Case {c.name} for layer {layer} missing canonical canon_key {canon_key}"
            )

    def test_accelerator_cases_satisfy_required_fields(self):
        """REQUIRED_FIELDS check (8 fields) from Phase 03A applies to accelerator cases."""
        for c in CASES_DIR.glob("accelerator-*.md"):
            fm = load_case(c)
            missing = REQUIRED_FIELDS - set(fm.keys())
            assert not missing, f"{c.name} missing required fields: {missing}"

    def test_accelerator_cases_forbid_inline_terraform(self):
        """ACT-06 defense-in-depth — even positive accelerator cases guard against
        inline Terraform leakage (accelerator dispatches kustomize, not Terraform)."""
        for c in CASES_DIR.glob("accelerator-*.md"):
            fm = load_case(c)
            forbidden = fm.get("forbidden_claims", [])
            assert any('resource "confluent_' in str(claim) for claim in forbidden), (
                f"{c.name} forbidden_claims missing inline-Terraform guard. "
                f"Got: {forbidden}"
            )

    def test_accelerator_cases_target_correct_artifact(self):
        """All 5 accelerator cases must target accelerator/confluent-on-linuxone
        (same artifact, different layer scope)."""
        accel_cases = list(CASES_DIR.glob("accelerator-*.md"))
        for c in accel_cases:
            fm = load_case(c)
            assert fm.get("expected_artifact") == "accelerator/confluent-on-linuxone", (
                f"{c.name}: expected_artifact must be "
                f"'accelerator/confluent-on-linuxone', got '{fm.get('expected_artifact')}'"
            )

    def test_accelerator_cases_are_positive_space(self):
        """All 5 accelerator cases are positive (negative_space: false) —
        wrong-layer / unknown-canon-key negative cases are covered by Plan 11-01's
        DRIFT-1 unit tests, not by the act-harness golden cross-section."""
        for c in CASES_DIR.glob("accelerator-*.md"):
            fm = load_case(c)
            assert fm.get("negative_space") is False, (
                f"{c.name}: accelerator cases must be positive-space "
                f"(negative_space: false), got {fm.get('negative_space')}"
            )

    def test_accelerator_canon_keys_align_with_module_to_canon_key(self):
        """Cross-plan integration test — accelerator case canon_keys MUST match
        Plan 11-01's MODULE_TO_CANON_KEY composite-key values. Catches drift
        between act-harness layer/canon_key mapping and the parity walker's
        ground truth.
        """
        import importlib.util
        # tools/check-canon-parity.py has a hyphen → load via importlib spec
        parity_path = (
            Path(__file__).parent.parent.parent.parent
            / "tools" / "check-canon-parity.py"
        )
        if not parity_path.exists():
            pytest.skip(f"tools/check-canon-parity.py not found at {parity_path}")
        spec = importlib.util.spec_from_file_location("check_canon_parity", parity_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        mtck = module.MODULE_TO_CANON_KEY
        for layer, canon_key in ACCELERATOR_LAYER_TO_CANON_KEY.items():
            composite = f"accelerator/confluent-on-linuxone:{layer}"
            assert composite in mtck, (
                f"MODULE_TO_CANON_KEY missing composite key {composite!r}; "
                f"Plan 11-01 should have added it"
            )
            assert mtck[composite] == canon_key, (
                f"MODULE_TO_CANON_KEY[{composite!r}] = {mtck[composite]!r}, "
                f"but act-harness layer→canon_key map says {canon_key!r}"
            )
