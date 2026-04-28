"""
Golden harness structural tests for /review skill (REVW-05).
These tests verify case file structure and distribution, NOT skill execution.
LLM evaluation requires CI + model API and is deferred to Phase 4.
"""
import yaml
from pathlib import Path
import pytest

CASES_DIR = Path(__file__).parent / "cases"
FIXTURES_DIR = Path(__file__).parent / "fixtures"
REQUIRED_FIELDS = {
    "id", "input_files", "expected_claims_min", "floor_model",
    "tags", "required_report_sections", "forbidden_content"
}
VALID_FLOOR_MODELS = {"haiku", "sonnet"}


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


class TestGoldenReviewStructure:
    """REVW-05: Verify review case file structure and minimum coverage."""

    def test_cases_directory_exists(self):
        assert CASES_DIR.exists(), f"Golden cases directory missing: {CASES_DIR}"

    def test_fixtures_directory_exists(self):
        assert FIXTURES_DIR.exists(), f"Fixtures directory missing: {FIXTURES_DIR}"

    def test_minimum_case_count(self):
        assert len(ALL_CASES) >= 15, (
            f"Need >= 15 golden cases, found {len(ALL_CASES)}"
        )

    def test_premise_challenge_case_exists(self):
        """REVW-02: At least one case exercises premise-challenge."""
        premise_cases = [
            p for p in ALL_CASES
            if load_case(p).get("premise_challenge_expected") is True
        ]
        assert len(premise_cases) >= 1, (
            "Need >= 1 case with premise_challenge_expected: true (exercises REVW-02)"
        )

    def test_overlay_case_exists(self):
        """REVW-06: At least one case exercises customer overlay."""
        overlay_cases = [
            p for p in ALL_CASES
            if load_case(p).get("overlay") is not None
        ]
        assert len(overlay_cases) >= 1, (
            "Need >= 1 case with overlay set to non-null value (exercises REVW-06)"
        )

    def test_multi_doc_case_exists(self):
        """REVW-04: At least one case exercises multi-document review."""
        multi_doc_cases = [
            p for p in ALL_CASES
            if len(load_case(p).get("input_files", [])) > 1
        ]
        assert len(multi_doc_cases) >= 1, (
            "Need >= 1 case with multiple input_files entries (exercises REVW-04)"
        )

    def test_correction_case_exists(self):
        """REVW-01: At least one case expects a Corrected verdict."""
        correction_cases = [
            p for p in ALL_CASES
            if "Corrected" in load_case(p).get("expected_verdict_contains", [])
        ]
        assert len(correction_cases) >= 1, (
            "Need >= 1 case with 'Corrected' in expected_verdict_contains"
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
    def test_input_files_is_list(self, case_path):
        fm = load_case(case_path)
        assert isinstance(fm.get("input_files", []), list), (
            f"{case_path.name}: input_files must be a list"
        )

    @pytest.mark.parametrize("case_path", ALL_CASES, ids=lambda p: p.stem)
    def test_required_report_sections_is_list(self, case_path):
        fm = load_case(case_path)
        assert isinstance(fm.get("required_report_sections", []), list), (
            f"{case_path.name}: required_report_sections must be a list"
        )

    @pytest.mark.parametrize("case_path", ALL_CASES, ids=lambda p: p.stem)
    def test_forbidden_content_is_list(self, case_path):
        fm = load_case(case_path)
        assert isinstance(fm.get("forbidden_content", []), list), (
            f"{case_path.name}: forbidden_content must be a list"
        )

    @pytest.mark.parametrize("case_path", ALL_CASES, ids=lambda p: p.stem)
    def test_fixture_files_exist(self, case_path):
        fm = load_case(case_path)
        for fpath in fm.get("input_files", []):
            full = Path(__file__).resolve().parent.parent.parent.parent / fpath
            assert full.exists(), (
                f"{case_path.name}: fixture file not found: {fpath} (resolved: {full})"
            )


class TestFloorModelDistribution:
    """REVW-05: Verify haiku and sonnet cases exist at sufficient count."""

    def test_haiku_cases_exist(self):
        haiku = [p for p in ALL_CASES if load_case(p).get("floor_model") == "haiku"]
        assert len(haiku) >= 5, f"Need >= 5 haiku-floor cases, found {len(haiku)}"

    def test_sonnet_cases_exist(self):
        sonnet = [p for p in ALL_CASES if load_case(p).get("floor_model") == "sonnet"]
        assert len(sonnet) >= 5, f"Need >= 5 sonnet-floor cases, found {len(sonnet)}"
