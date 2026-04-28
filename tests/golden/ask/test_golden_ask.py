"""
Golden harness structural tests for /ask skill (KNOW-03).
These tests verify case file structure and distribution, NOT skill execution.
LLM evaluation requires CI + model API and is deferred to Phase 4.
"""
import yaml
from pathlib import Path
import pytest

CASES_DIR = Path(__file__).parent / "cases"
REQUIRED_FIELDS = {
    "id", "query", "expected_route", "floor_model",
    "tags", "required_claims", "forbidden_claims"
}
VALID_ROUTES = {"wiki-only", "wiki+mcp", "deep", "refuse", "redirect_to_mcp"}
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


class TestGoldenHarnessStructure:
    """KNOW-03: Verify case file structure and minimum coverage."""

    def test_cases_directory_exists(self):
        assert CASES_DIR.exists(), f"Golden cases directory missing: {CASES_DIR}"

    def test_minimum_case_count(self):
        assert len(ALL_CASES) >= 30, (
            f"Need >= 30 golden cases, found {len(ALL_CASES)}"
        )

    def test_minimum_negative_space_cases(self):
        negative = [
            p for p in ALL_CASES
            if load_case(p).get("expected_route") in {"refuse", "redirect_to_mcp"}
        ]
        assert len(negative) >= 5, (
            f"Need >= 5 negative-space cases, found {len(negative)}"
        )

    def test_all_three_routes_covered(self):
        routes = {load_case(p).get("expected_route") for p in ALL_CASES}
        for r in ("wiki-only", "wiki+mcp", "deep"):
            assert r in routes, f"No cases for route: {r}"

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
    def test_case_has_valid_route(self, case_path):
        fm = load_case(case_path)
        assert fm.get("expected_route") in VALID_ROUTES, (
            f"{case_path.name}: invalid expected_route '{fm.get('expected_route')}'"
        )

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


class TestFloorModelDistribution:
    """KNOW-04/05: Verify haiku and sonnet cases exist at sufficient count."""

    def test_haiku_cases_exist(self):
        haiku = [p for p in ALL_CASES if load_case(p).get("floor_model") == "haiku"]
        assert len(haiku) >= 10, f"Need >= 10 haiku-floor cases, found {len(haiku)}"

    def test_sonnet_cases_exist(self):
        sonnet = [p for p in ALL_CASES if load_case(p).get("floor_model") == "sonnet"]
        assert len(sonnet) >= 10, f"Need >= 10 sonnet-floor cases, found {len(sonnet)}"
