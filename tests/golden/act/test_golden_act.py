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
