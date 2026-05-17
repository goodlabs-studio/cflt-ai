"""Unified eval harness runner - D-01 hybrid, D-02 single pytest runner, D-04 structural-only.

Discovers cases from both formats:
  - tests/golden/*/cases/*.md  (existing markdown-per-case; 89 cases across /ask, /review,
    /dsp:plan, /dsp:apply)
  - tests/evals/*/evals.json   (NEW upstream-schema JSON; 7 skills x >= 10 cases each)

Enforces D-06 90% pass rate per skill INSIDE pytest. CI fails because pytest fails -
no separate gate. Structural-only per D-04/D-05: no LLM invocation, no network calls,
no model SDKs imported.

Adapter contract (locked - downstream plans depend on field order):
    EvalCase(id, skill, prompt, expected_output, expectations, floor_model, source_path)
"""
import json
from collections import defaultdict, namedtuple
from pathlib import Path

import pytest
import yaml

# Repo root: tests/evals/run_skill_evals.py -> .parent.parent.parent
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# D-06: uniform 90% across all skills (module-level constant for single-point review)
MIN_PASS_RATE = 0.90

# Public adapter contract. Field order is locked - test_eval_case_namedtuple_fields
# in tests/evals/test_runner_adapters.py asserts this exact tuple.
EvalCase = namedtuple(
    "EvalCase",
    ["id", "skill", "prompt", "expected_output", "expectations", "floor_model", "source_path"],
)


def _parse_frontmatter(path: Path) -> dict:
    """Extract YAML frontmatter dict from a markdown case file.

    Returns {} when the file has no frontmatter block - callers treat empty
    frontmatter as a non-case and skip.
    """
    content = path.read_text()
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    return yaml.safe_load(content[3:end]) or {}


def _detect_md_skill(case_path: Path, fm: dict) -> str:
    """Derive skill from cases directory; for /act, key off frontmatter `skill` field.

    The /act directory holds BOTH /dsp:plan and /dsp:apply cases - apply-* cases
    declare `skill: /dsp:apply` explicitly in their frontmatter; everything else
    in act/cases/ defaults to /dsp:plan (the plan-rail harness).
    """
    # tests/golden/<X>/cases/foo.md -> parent.parent.name == <X>
    parent = case_path.parent.parent.name
    if parent == "ask":
        return "/ask"
    if parent == "review":
        return "/review"
    if parent == "act":
        return fm.get("skill", "/dsp:plan")
    return f"/{parent}"


def _collect_expectations(fm: dict) -> list:
    """Harvest structural expectations from MD frontmatter across all three harness shapes.

    Different harnesses use different field names for the same semantic role:
      - /ask, /act:  required_claims (positive) + forbidden_claims (negative)
      - /review:     required_report_sections (positive structural) + forbidden_content
                     (negative) + required_claims/forbidden_claims when present

    All positive entries are passed through verbatim; all negative entries are prefixed
    `NOT: ` to mark them as forbidden assertions (matches the upstream evals.json
    "Does NOT use ..." convention).
    """
    positive = []
    positive.extend(fm.get("required_claims", []) or [])
    positive.extend(fm.get("required_report_sections", []) or [])

    negative = []
    negative.extend(fm.get("forbidden_claims", []) or [])
    negative.extend(fm.get("forbidden_content", []) or [])

    return list(positive) + [f"NOT: {c}" for c in negative]


def load_md_cases():
    """Adapter for existing tests/golden/*/cases/*.md cases.

    D-01 hybrid: existing 89 markdown-per-case files are NOT migrated. This adapter
    reads their YAML frontmatter and maps to the unified EvalCase shape.

    Prompt resolution order:
      1. `query` field (/ask convention)
      2. `request` field (/act convention)
      3. joined `input_files` paths (/review convention - no literal prompt string)

    Expectations harvested via _collect_expectations() - see that helper for the
    per-harness field-name mapping.
    """
    for path in sorted((REPO_ROOT / "tests" / "golden").glob("*/cases/*.md")):
        fm = _parse_frontmatter(path)
        if not fm:
            continue
        skill = _detect_md_skill(path, fm)
        prompt = fm.get("query") or fm.get("request") or " ".join(fm.get("input_files", []))
        # Positional construction by-design: the D-04 lock grep checks for LLM SDK
        # invocation patterns, and the floor_model field name is a stable contract.
        yield EvalCase(
            str(fm.get("id", path.stem)),
            skill,
            prompt,
            # MD cases declare expected behavior in the body's "MUST contain" sections;
            # not parsed here per D-04 structural-only - the expectations[] list is the
            # checkable contract.
            "",
            _collect_expectations(fm),
            fm.get("floor_model"),
            str(path.relative_to(REPO_ROOT)),
        )


def load_json_cases():
    """Loader for new tests/evals/<skill>/evals.json files.

    D-03 verbatim upstream schema:
      {
        "skill_name": "/wiki:ingest",
        "evals": [
          {"id": 1, "prompt": "...", "expected_output": "...",
           "files": [...], "expectations": ["...", "..."]}
        ]
      }

    Plans 02 and 03 author the 7 evals.json files this loader consumes. Until those
    plans land, this loader yields zero records (the glob matches nothing) and
    test_all_seven_new_skills_discovered fails RED.

    Note: this glob matches `tests/evals/<dir>/evals.json` (one directory level deep,
    filename exactly `evals.json`). Test fixtures under tests/evals/fixtures/ use the
    name `sample_evals.json` to stay off this glob - see test_runner_adapters.py.
    """
    for path in sorted((REPO_ROOT / "tests" / "evals").glob("*/evals.json")):
        data = json.loads(path.read_text())
        skill_name = data["skill_name"]
        for ev in data["evals"]:
            # Positional construction by-design (see load_md_cases note above).
            yield EvalCase(
                str(ev["id"]),
                skill_name,
                ev["prompt"],
                ev.get("expected_output", ""),
                list(ev.get("expectations", [])),
                ev.get("floor_model"),
                str(path.relative_to(REPO_ROOT)),
            )


# Module-level case list - pytest parametrize consumes this at collection time.
ALL_CASES = list(load_md_cases()) + list(load_json_cases())


def _structural_pass(case: EvalCase) -> bool:
    """D-04 structural-only pass predicate.

    A case passes iff its expectations list is non-empty AND every element is a
    non-empty string. No LLM invocation, no grep against generated artifacts -
    purely a well-formedness check. This is the locked contract per CONTEXT.md
    D-04: the runner verifies case files are well-formed and the harness can
    collect them; live model invocation is explicitly deferred to a follow-on
    phase.
    """
    if not case.expectations:
        return False
    if not all(isinstance(e, str) and e.strip() for e in case.expectations):
        return False
    return True


@pytest.mark.parametrize("case", ALL_CASES, ids=lambda c: f"{c.skill}/{c.id}")
def test_case_well_formed(case):
    """Per-case well-formedness check - D-02 single runner over both formats."""
    assert case.expectations, f"{case.source_path}: empty expectations"
    for e in case.expectations:
        assert isinstance(e, str) and e.strip(), (
            f"{case.source_path}: malformed expectation: {e!r}"
        )


def test_threshold_per_skill():
    """D-06: enforce >= 90% structural pass rate per skill.

    Groups all collected cases by skill, computes per-skill pass rate using
    _structural_pass(), and fails with an actionable per-skill report when any
    skill drops below MIN_PASS_RATE. CI fails because pytest fails (D-09) -
    there is no separate gate.
    """
    by_skill = defaultdict(list)
    for c in ALL_CASES:
        by_skill[c.skill].append(c)
    failures = []
    for skill, cases in sorted(by_skill.items()):
        passed = sum(1 for c in cases if _structural_pass(c))
        rate = passed / len(cases)
        if rate < MIN_PASS_RATE:
            failures.append(
                f"{skill}: {passed}/{len(cases)} = {rate:.1%} < {MIN_PASS_RATE:.0%}"
            )
    assert not failures, "Skill threshold failures:\n  " + "\n  ".join(failures)


def test_all_seven_new_skills_discovered():
    """EVAL-02 coverage gate: every named skill from REQUIREMENTS.md is collected.

    This test is INTENDED TO FAIL in Plan 01 - it's the RED state Plans 02 and 03
    close by authoring the 7 evals.json files. After those plans land this goes
    GREEN automatically because load_json_cases() picks up the new JSON files.

    Expected RED-state failure message names: /wiki:ingest, /wiki:validate,
    /wiki:lint, /wiki:recommend (and possibly /review if Plan 02 hasn't authored
    its thin-wrapper JSON yet).
    """
    skills = {c.skill for c in ALL_CASES}
    required = {
        "/review",
        "/wiki:ingest",
        "/wiki:validate",
        "/wiki:lint",
        "/wiki:recommend",
        "/dsp:plan",
        "/dsp:apply",
    }
    missing = required - skills
    assert not missing, (
        f"EVAL-02 skills not discovered (Plans 02/03 incomplete?): {sorted(missing)}"
    )
