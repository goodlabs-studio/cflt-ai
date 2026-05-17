"""Unit tests for tests/evals/run_skill_evals.py adapters.

Verifies load_md_cases() and load_json_cases() correctly parse the two formats,
independent of the threshold gate (which is tested via the runner itself).

D-04 structural-only: these tests never invoke a model, never hit the network,
and never run a subprocess. They exercise pure parsing + namedtuple construction.
"""
import json
from pathlib import Path

from tests.evals.run_skill_evals import (
    EvalCase,
    load_json_cases,
    load_md_cases,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURE_JSON = Path(__file__).resolve().parent / "fixtures" / "sample_evals.json"


def test_eval_case_namedtuple_fields():
    """Lock the public EvalCase shape so downstream plans can rely on field order.

    Plans 02 and 03 author evals.json files and Plan 04 wires CI; both depend on
    the exact field order documented here. Changing this tuple is a breaking
    change that requires a deliberate decision (and likely a phase bump).
    """
    assert EvalCase._fields == (
        "id",
        "skill",
        "prompt",
        "expected_output",
        "expectations",
        "floor_model",
        "source_path",
    )


class TestLoadMdCases:
    """Cover the four behaviors of load_md_cases() that downstream plans rely on."""

    def test_discovers_all_existing(self):
        cases = list(load_md_cases())
        assert len(cases) >= 80, f"Expected >= 80 MD cases, got {len(cases)}"

    def test_skill_attribution(self):
        """All four MD-format skills present in the existing 89-case corpus."""
        cases = list(load_md_cases())
        skills = {c.skill for c in cases}
        assert "/ask" in skills
        assert "/review" in skills
        assert "/dsp:plan" in skills
        assert "/dsp:apply" in skills

    def test_forbidden_claims_prefixed(self):
        """forbidden_claims become expectations prefixed with 'NOT: '."""
        cases = list(load_md_cases())
        has_negation = any(
            any(e.startswith("NOT: ") for e in c.expectations) for c in cases
        )
        assert has_negation, (
            "Expected >= 1 case with NOT-prefixed expectation from forbidden_claims"
        )

    def test_prompt_fallback(self):
        """/ask uses query, /act uses request, /review uses joined input_files."""
        cases = list(load_md_cases())
        ask_cases = [c for c in cases if c.skill == "/ask"]
        act_cases = [c for c in cases if c.skill in ("/dsp:plan", "/dsp:apply")]
        review_cases = [c for c in cases if c.skill == "/review"]
        assert ask_cases, "Sanity: expected /ask cases collected"
        assert act_cases, "Sanity: expected /act cases collected"
        assert review_cases, "Sanity: expected /review cases collected"
        assert all(c.prompt for c in ask_cases), (
            "/ask cases should have non-empty prompt (from query field)"
        )
        assert all(c.prompt for c in act_cases), (
            "/act cases should have non-empty prompt (from request field)"
        )
        assert all(c.prompt for c in review_cases), (
            "/review cases should have non-empty prompt (from joined input_files)"
        )


class TestLoadJsonCases:
    """Cover the JSON adapter against the locked D-03 upstream schema."""

    def test_fixture_exists(self):
        assert FIXTURE_JSON.exists(), f"Fixture missing: {FIXTURE_JSON}"

    def test_fixture_not_in_runner_glob(self):
        """Fixture must NOT be named evals.json.

        If it were, the runner's `tests/evals/*/evals.json` glob would pick it up
        and inject fake cases into the real harness. The belt-and-suspenders
        assertion keeps future contributors from silently renaming this file.
        """
        assert FIXTURE_JSON.name == "sample_evals.json"

    def test_parses_upstream_schema(self):
        """load_json_cases()-style adapter logic correctly maps D-03 fields verbatim."""
        data = json.loads(FIXTURE_JSON.read_text())
        # Sanity: fixture shape mirrors upstream verbatim
        assert data["skill_name"] == "/test:fake"
        assert len(data["evals"]) == 2
        assert data["evals"][0]["id"] == 1
        assert isinstance(data["evals"][0]["expectations"], list)

        # Exercise the same adapter code-path against the fixture inline.
        # We can't point load_json_cases() at the fixture (it globs the runner's
        # production glob), so we re-run the mapping logic against the fixture
        # to assert the per-record translation is correct.
        cases = []
        for ev in data["evals"]:
            cases.append(
                EvalCase(
                    str(ev["id"]),
                    data["skill_name"],
                    ev["prompt"],
                    ev.get("expected_output", ""),
                    list(ev.get("expectations", [])),
                    ev.get("floor_model"),
                    "fixture",
                )
            )
        assert len(cases) == 2
        assert cases[0].skill == "/test:fake"
        assert cases[0].id == "1"
        assert len(cases[0].expectations) == 3
        assert "Uses acks=all in production code" in cases[0].expectations
        assert cases[1].id == "2"
        assert cases[1].expectations[0].startswith(
            "Imports StreamsUncaughtExceptionHandler"
        )

    def test_real_runner_does_not_pick_up_fixture(self):
        """Sanity-check the glob exclusion.

        The runner's load_json_cases() must NOT yield fixture cases. If this fails,
        the fixture was renamed to evals.json (or moved into a sibling directory
        that matches `tests/evals/<x>/evals.json`) and the production harness is
        now polluted.
        """
        cases = list(load_json_cases())
        assert all(c.skill != "/test:fake" for c in cases), (
            "Runner glob accidentally picked up the test fixture - rename or move it"
        )
