# Phase H.4a: Profile-family schema extension — Context

**Gathered:** 2026-05-17
**Status:** Ready for planning
**Mode:** Auto (--auto) — gray-area defaults selected from prior decisions (Phase 3c profile gating, G.2c tool classification, ACTG patterns)

<domain>
## Phase Boundary

Add a `family: "operator" | "developer"` field to every profile JSON, and teach `apply_engine.load_profile()` and `apply_engine.check_tool_permitted()` to read the family and branch behavior. Operator family (the existing read-only/engineer/break-glass profiles) continues to use the tier-cascade logic that v1.0 Phase 3c shipped. Developer family (no profiles yet — H.4b authors the first one) will use a per-profile `tool_overrides` map. Default to `family: "operator"` when the field is absent on load (back-compat — existing profile files don't need editing for the engine to keep working).

**This phase is pure schema groundwork.** No new profile, no new canon overlay, no behavior change for any existing operator profile. The new branch in `check_tool_permitted()` is exercised by a fixture test (developer-family profile with a `tool_overrides` map) so the dispatch logic is proven before H.4b authors the real developer profile. Validation gate: every existing operator-profile test still passes byte-identical results.

**Out of scope (do not let scope creep pull these in):**
- Authoring `tools/profiles/developer/sandbox.json` (H.4b — first real developer profile)
- Authoring `canon/industry/fsi/developer-sandbox/` canon overlay (H.4b)
- acme-bank customer developer overlay (H.4c)
- `environment_guard` enforcement (H.4b — soft pattern lives on the developer-sandbox profile, not the engine)
- Activity-log changes for the family field (defer to H.4b — first invocation that actually uses developer family)

</domain>

<decisions>
## Implementation Decisions

### Family field shape
- **D-01:** New required field `family: "operator" | "developer"` (string enum) on every profile JSON. Two literal values, no others. Existing files (`read-only.json`, `engineer.json`, `break-glass.json`) get `"family": "operator"` added explicitly — do NOT rely on the absence-default for committed files (the default is for back-compat with old fixtures or external profiles, not a substitute for being explicit in committed config). Place `family` as the first field after `name` and `description` so it reads obvious; example: `{"name": "engineer", "description": "...", "family": "operator", "allowed_operations": [...]}`.
- **D-02:** When `family` is absent (e.g., third-party fixture profile not authored in this repo), `load_profile()` returns a profile dict with `family: "operator"` injected. This back-compat default lives in code, not in JSON, so the committed-config posture stays explicit. Add a one-line log note (not a warning) when the default is applied so test runs surface external fixtures using legacy shapes.
- **D-03:** Unknown family values (e.g., `family: "platform"`) are a hard error in `load_profile()` — raises ValueError with the same fail-closed shape as the existing unknown-profile-name error. This is consistent with `tool_classification.json`'s `unclassified_policy=deny` (Phase G.2c) — unrecognized shapes fail closed.

### Engine branching
- **D-04:** `check_tool_permitted()` reads `family` from the profile (via `load_profile()`) and branches:
  - `family == "operator"` → existing tier cascade (read PROFILE_TIER_ORDER, look up `required_tier` in tool_classification.json, compare indices). Byte-identical to v1.0 Phase 3c behavior.
  - `family == "developer"` → read `tool_overrides` map from the profile JSON (`{"<tool-name>": "developer-sandbox" | "developer-restricted" | ...}`); if the tool is in the map, permit it (no further tier comparison); if not, deny (fail-closed). The map's value-strings are documented but not validated as an enum in H.4a — H.4b's developer-sandbox profile will pin a concrete value set.
- **D-05:** `check_tool_permitted()` signature does NOT change. It still takes `(profile_name, tool_name, customer=None)`. The function internally calls `load_profile()` to get the family. This keeps every caller in the codebase (including v1.0 tests) byte-compatible — no call-site edits.
- **D-06:** Operator profiles do NOT carry a `tool_overrides` field. Developer profiles do NOT carry an `allowed_operations` field (they use `skill_blocklist` and `tool_overrides` only — H.4b spec). H.4a enforces this in `load_profile()` by raising ValueError if either invariant is violated. This prevents future hybrid profiles that confuse the dispatch.

### Schema validation
- **D-07:** No `jsonschema` library dependency added. Validation is implemented in Python directly in `load_profile()` (cheaper than adding a new dep just for this; matches the existing pattern of `VALID_PROFILES` set-membership check). Specifically: parse the JSON, then validate (a) `name` exists, (b) `family` is one of `{"operator", "developer"}` after defaulting, (c) operator profiles have `allowed_operations` (list), (d) developer profiles have `tool_overrides` (dict) and `skill_blocklist` (list — may be empty). Raise ValueError on any invariant violation with the same message shape as existing errors.
- **D-08:** Profile-family invariants are documented in a top-of-file docstring inside `tools/profiles/__init__.py` (or `tools/apply_engine.py` near the existing VALID_PROFILES constant if a profiles/__init__.py doesn't exist). The docstring is the contract; tests anchor against the docstring's claims. No separate `.md` design doc — keeps the spec next to the code.

### Tests
- **D-09:** Test surface split into three concerns:
  1. **Family field round-trip** — `test_load_profile_reads_family`, `test_load_profile_defaults_family_to_operator_when_absent`, `test_load_profile_rejects_unknown_family`. Uses real existing profiles + a temp-fixture profile with missing/bogus family.
  2. **Operator-branch byte-compat** — `test_check_tool_permitted_operator_branch_byte_identical` — load every (profile, tool) combination from existing classification table and assert identical permit-or-deny vs v1.0 baseline. Use a snapshot file `tests/snapshots/h4a_operator_permits.json` committed alongside.
  3. **Developer-branch dispatch** — `test_check_tool_permitted_developer_branch_reads_tool_overrides` — fixture developer profile with `tool_overrides: {"produce-message": "developer-sandbox"}`; assert permit for produce-message, deny for everything else (including tools the operator-tier table would permit at engineer level). Proves the branch isolation.
- **D-10:** Add the operator-branch byte-compat snapshot as part of H.4a. This is the regression guard that proves the schema extension didn't accidentally change behavior. If a future change to tool_classification.json shifts the permit set, the snapshot regenerates (one-line gen script in the test file's docstring) — but it MUST regenerate in a separate PR so the diff is visible.

### Folded Todos
None — `todo match-phase H.4a` returned zero matches (verified during H.3a context gathering — none added since).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project canon
- `CLAUDE.md` (project root) — Confluent Canon (FSI overlay), informs the developer-family intent (sandbox-only data-plane ops, dev-tier defaults).
- `.planning/REQUIREMENTS.md` — H.4a satisfies PROFAM-01 (family field + branching) and PROFAM-02 (per-family negative-space tests — partial; full PROFAM-02 needs H.4b's developer profile to assert the dev profile cannot invoke operator-tier-only tools).
- `.planning/ROADMAP.md` §Phase H.4a — Single source of goal + success criteria.

### Prior-phase contexts (patterns to reuse)
- `.planning/phases/03C-act-rail-profile-gating/03C-CONTEXT.md` — Original tier-cascade design + `check_tool_permitted()` contract + per-profile negative-space test pattern. H.4a extends without altering.
- `.planning/phases/G.2c-tool-classification-rename/G.2c-CONTEXT.md` — `unclassified_policy=deny` fail-closed posture. H.4a's unknown-family-value handling mirrors this.

### Code under modification
- `tools/apply_engine.py` lines 36–124 — `VALID_PROFILES`, `PROFILE_TIER_ORDER`, `load_profile()`, `check_tool_permitted()`.
- `tools/profiles/read-only.json`, `tools/profiles/engineer.json`, `tools/profiles/break-glass.json` — Add `family` field.
- `tests/test_profile_gating.py` — Add 3 new test groups (D-09).

### Existing tooling (read-only references)
- `tools/profiles/tool_classification.json` — Tier mapping that `check_tool_permitted()` consults; unchanged in H.4a.
- `tools/regenerate_tool_classification.py` — G.2c-pattern generator (no changes; reference for the snapshot regenerator script pattern in D-10).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`load_profile()` already validates against `VALID_PROFILES`** — H.4a extends the validation block, doesn't replace it. Same ValueError shape.
- **`check_tool_permitted()` already returns False (fail-closed) for unknown tools** — H.4a applies the same posture to unknown family values and missing-required-fields-per-family.
- **`PROFILE_TIER_ORDER` is the operator-branch source of truth** — H.4a's developer branch does NOT touch this. Tier indices live only in the operator branch.
- **`tests/test_profile_gating.py`** already exists with the per-profile negative-space pattern from Phase 3c — H.4a's new tests follow the same parametrize shape.
- **Customer overlay path** (`canon/customer/<name>/profiles/<profile>.json`) already exists — H.4a's family-field validation runs on overlay-resolved profiles too, not just base profiles.

### Established Patterns
- **Fail-closed everywhere** — Unknown profile names, unknown tools, unclassified tools, future unknown families all raise ValueError or return False. No silent degradation.
- **Set-membership validation in Python (not jsonschema)** — `VALID_PROFILES = {...}`. H.4a adds `VALID_FAMILIES = {"operator", "developer"}` in the same style.
- **Keyword-only customer arg** — `load_profile(name, *, customer=None)` — H.4a preserves this signature exactly.
- **Snapshot regression pattern** — Tests snapshot the live behavior, regenerate via a one-liner in the test docstring. Used in `tests/snapshots/` if the directory exists; otherwise H.4a creates it.

### Integration Points
- **`tools/apply_engine.py`** — Single file with all profile-loading + tool-permission logic. H.4a edit surface is concentrated here.
- **`tools/profiles/*.json`** — Three files gain `family: "operator"` field (small).
- **`tests/test_profile_gating.py`** — Three new test functions + snapshot file.
- **`tests/snapshots/h4a_operator_permits.json`** (new) — Snapshot of all (profile, tool) → permit decisions for the operator branch. Tiny file (3 profiles × ~54 tools = 162 rows).

</code_context>

<specifics>
## Specific Ideas

- **Snapshot regenerator one-liner** (in test docstring): `python -c "import json; from tools.apply_engine import check_tool_permitted, VALID_PROFILES, load_tool_classification; tc = load_tool_classification(); print(json.dumps({p: {t: check_tool_permitted(p, t) for t in tc['tools']} for p in VALID_PROFILES}, indent=2))" > tests/snapshots/h4a_operator_permits.json`
- **Field placement in JSON**: After `name` and `description`, before `allowed_operations`. Example for engineer.json: `{"name": "engineer", "description": "Plan + apply...", "family": "operator", "allowed_operations": [...]}`.
- **Developer-branch fixture** (used only in tests, not committed as a real profile): `{"name": "test-dev-fixture", "description": "Test fixture — do not load in production", "family": "developer", "skill_blocklist": [], "tool_overrides": {"produce-message": "developer-sandbox"}}`. Stored under `tests/fixtures/profiles/`.

</specifics>

<deferred>
## Deferred Ideas

- **JSON Schema file for profiles** (e.g., `tools/profiles/_schema.json`) — Could be added when external tooling needs to validate independently of apply_engine. Not blocking for H.4a.
- **`developer-restricted` tier value enumeration** — H.4a's developer-branch dispatch reads the value-string but doesn't constrain it. H.4b will pin the value set (developer-sandbox, developer-restricted, etc.) when the first real developer profile lands.
- **Activity-log family field** — Logging which family a /dsp:apply ran under is useful for audit but not gated by H.4a. H.4b adds it when the developer-sandbox profile actually invokes apply_engine.
- **`environment_guard` enforcement at engine level** — Phase H.4b ROADMAP describes a soft pattern on the developer-sandbox profile. Whether that's enforced in apply_engine or remains advisory is a H.4b decision.
- **Schema migration tooling** — If we later add a 3rd family (e.g., `auditor`) the field set extends; no migration framework needed at H.4a's scale (3 profile files), but worth revisiting if profile count grows.

### Reviewed Todos (not folded)
None — `gsd-tools todo match-phase H.4a` returned zero matches.

</deferred>

---

*Phase: H.4a-profile-family-schema-extension*
*Context gathered: 2026-05-17 (auto-mode)*
