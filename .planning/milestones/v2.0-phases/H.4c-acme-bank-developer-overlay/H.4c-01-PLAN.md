---
phase: H.4c-acme-bank-developer-overlay
plan: 01
type: execute
wave: 1
depends_on: [H.4b-01]
files_modified:
  - canon/customer/acme-bank/profiles/developer/sandbox.json
  - canon/customer/acme-bank/adrs/adr-004.md
  - tests/test_per_family_isolation.py
  - tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json
autonomous: true
requirements: [DEVPROF-02]
requirements_addressed: [DEVPROF-02]

must_haves:
  truths:
    - "`canon/customer/acme-bank/profiles/developer/sandbox.json` exists with `family: \"developer\"`, `customer_overrides` field referencing adr-004, `tool_overrides` map that DOES NOT include `delete-topics` or `alter-topic-config`, `skill_blocklist` containing `dsp-apply` AND `dsp-plan`, `environment_guard.pattern == \"acme-*-sandbox\"`, `canon_layer == \"industry/fsi/developer-sandbox\"`"
    - "`canon/customer/acme-bank/adrs/adr-004.md` exists with frontmatter `status: Accepted` and references both H.4c CONTEXT decisions AND the existing adr-003.md (engineer family precedent)"
    - "`load_profile(\"developer/sandbox\", customer=\"acme-bank\")` returns the acme overlay file's content (not the base profile) — verified by presence of `customer_overrides` field in the returned dict"
    - "`check_tool_permitted(\"developer/sandbox\", \"delete-topics\", customer=\"acme-bank\")` returns False; the no-customer equivalent returns True — proves differential gating"
    - "`check_tool_permitted(\"developer/sandbox\", \"alter-topic-config\", customer=\"acme-bank\")` returns False; the no-customer equivalent returns True — second differential"
    - "`check_skill_permitted(\"developer/sandbox\", \"dsp-plan\", customer=\"acme-bank\")` returns False; the no-customer equivalent returns True — third differential (skill-level)"
    - "`tests/test_per_family_isolation.py` gains a `TestAcmeBankDeveloperOverlay` class with at least 3 test methods covering load + tool differential + skill differential"
    - "`tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json` exists with the (developer/sandbox under acme-bank × every-tool) permit matrix; differs from `h4b_developer_sandbox_permits.json` on at least the two removed tools"
    - "`pytest tests/test_per_family_isolation.py::TestAcmeBankDeveloperOverlay -v` exits 0 — all 3 new tests pass"
    - "`pytest tests/test_profile_gating.py tests/test_per_family_isolation.py tests/test_canon_overlay.py -v` exits 0 — full family-test suite passes"
    - "`pytest tests/` exit code 0 (or same 2 pre-existing failures as H.4a/H.4b — no NEW failures)"
    - "H.4a snapshot `tests/snapshots/h4a_operator_permits.json` AND H.4b snapshot `tests/snapshots/h4b_developer_sandbox_permits.json` are UNCHANGED (both `git diff HEAD --` empty)"
    - "Zero changes to `tools/apply_engine.py`, `canon/stack.py`, `canon/industry/fsi/developer-sandbox/`, `tools/profiles/`, or any operator profile"
  artifacts:
    - path: "canon/customer/acme-bank/profiles/developer/sandbox.json"
      provides: "acme-bank customer overlay for developer-sandbox profile — proves customer-fork differential gating for developer family (ACTG-04 mirror)"
      contains:
        - "\"family\": \"developer\""
        - "\"customer_overrides\""
        - "\"adr_ref\""
        - "\"dsp-plan\""
        - "acme-*-sandbox"
        - "industry/fsi/developer-sandbox"
    - path: "canon/customer/acme-bank/adrs/adr-004.md"
      provides: "ADR stub for acme-bank developer-sandbox profile customer overrides"
      contains:
        - "status: Accepted"
        - "H.4c"
        - "adr-003"
    - path: "tests/test_per_family_isolation.py"
      provides: "Extended with TestAcmeBankDeveloperOverlay class proving customer-fork differential gating"
      contains:
        - "class TestAcmeBankDeveloperOverlay"
        - "test_acme_bank_developer_overlay_loads"
        - "test_acme_bank_dev_overlay_produces_differential_gating"
        - "test_acme_bank_dev_overlay_blocks_dsp_plan"
    - path: "tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json"
      provides: "Snapshot of (developer/sandbox under acme-bank × every-tool) permits for regression guard"
      contains:
        - "developer/sandbox"
  key_links:
    - from: "canon/customer/acme-bank/profiles/developer/sandbox.json:customer_overrides.adr_ref"
      to: "canon/customer/acme-bank/adrs/adr-004.md"
      via: "Profile overlay cites the ADR that documents the customer differentials"
      pattern: "adr-004"
    - from: "tests/test_per_family_isolation.py:TestAcmeBankDeveloperOverlay"
      to: "canon/customer/acme-bank/profiles/developer/sandbox.json"
      via: "Tests load the overlay via load_profile(..., customer='acme-bank') and assert differential gating"
      pattern: "customer=\"acme-bank\""
---

<objective>
Land the acme-bank developer-sandbox customer overlay. Prove customer-fork differential gating works for the developer family the same way ACTG-04 (v1.0) proved it for the engineer family. Single PLAN, single wave. After this plan, DEVPROF-02 is fully satisfied; the H.4 sub-phase set (H.4a + H.4b + H.4c) is complete; the canon overlay stack story extends cleanly to both operator and developer families.

Tight scope: 4 files (1 new profile JSON, 1 new ADR stub, 1 test class appended, 1 new snapshot). Zero engine changes — H.4b's path-resolution already covers customer-overlay lookup for slash-separated profile names.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/H.4c-acme-bank-developer-overlay/H.4c-CONTEXT.md
@.planning/phases/H.4b-developer-sandbox-profile-fsi-dev-canon/H.4b-CONTEXT.md
@.planning/phases/03C-act-rail-profile-gating/03C-CONTEXT.md
@tools/profiles/developer/sandbox.json
@canon/customer/acme-bank/profiles/engineer.json
@canon/customer/acme-bank/adrs/adr-003.md
@tests/test_per_family_isolation.py
@tools/apply_engine.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Author canon/customer/acme-bank/profiles/developer/sandbox.json + canon/customer/acme-bank/adrs/adr-004.md</name>
  <files>
    - canon/customer/acme-bank/profiles/developer/sandbox.json
    - canon/customer/acme-bank/adrs/adr-004.md
  </files>
  <read_first>
    - tools/profiles/developer/sandbox.json (base profile this overlay forks from — verify which tools are in the base tool_overrides; the overlay's tool_overrides removes 2 and keeps the rest)
    - canon/customer/acme-bank/profiles/engineer.json (sibling customer overlay — shape template)
    - canon/customer/acme-bank/adrs/adr-003.md (sibling ADR — header conventions, status field, length)
    - .planning/phases/H.4c-acme-bank-developer-overlay/H.4c-CONTEXT.md (D-01, D-02, D-03, D-05 — exact overlay shape and ADR content)
  </read_first>
  <action>
    Create directory `canon/customer/acme-bank/profiles/developer/` then create both files.

    **canon/customer/acme-bank/profiles/developer/sandbox.json content:**

    Read `tools/profiles/developer/sandbox.json` to enumerate the base profile's `tool_overrides`. The acme overlay copies the base set MINUS `delete-topics` and `alter-topic-config`, and gains `dsp-plan` in skill_blocklist:

    ```json
    {
      "name": "developer/sandbox",
      "description": "Acme Bank developer-sandbox profile: stricter than base FSI dev canon — no topic destruction self-service; /dsp:plan blocked for dev profiles; sandbox restricted to acme-prefixed clusters.",
      "family": "developer",
      "primary_tooling": {
        "skills": [
          "streaming-skills-plugin:kafka-streams-programming",
          "streaming-skills-plugin:developing-kafka-python-client",
          "streaming-skills-plugin:kafka-schema-registry",
          "streaming-skills-plugin:confluent-cloud-cdc-tableflow"
        ]
      },
      "tool_overrides": {
        "produce-message": "developer-sandbox",
        "consume-messages": "developer-sandbox",
        "create-topics": "developer-sandbox",
        "list-topics": "developer-sandbox",
        "get-topic-config": "developer-sandbox",
        "create-flink-statement": "developer-sandbox",
        "delete-flink-statements": "developer-sandbox",
        "list-flink-statements": "developer-sandbox",
        "read-flink-statement": "developer-sandbox",
        "list-clusters": "developer-sandbox",
        "list-environments": "developer-sandbox",
        "list-schemas": "developer-sandbox",
        "search-topics-by-name": "developer-sandbox"
      },
      "skill_blocklist": [
        "dsp-apply",
        "dsp-plan"
      ],
      "environment_guard": {
        "pattern": "acme-*-sandbox",
        "enforcement": "advisory"
      },
      "canon_layer": "industry/fsi/developer-sandbox",
      "customer_overrides": {
        "removed_from_tool_overrides": ["delete-topics", "alter-topic-config"],
        "added_to_skill_blocklist": ["dsp-plan"],
        "tightened_environment_guard": "*-sandbox → acme-*-sandbox",
        "adr_ref": "canon/customer/acme-bank/adrs/adr-004.md"
      }
    }
    ```

    **IMPORTANT** — The `tool_overrides` map above lists 13 tools. Open `tools/profiles/developer/sandbox.json` and confirm that the 13 tools listed above (excluding `delete-topics` and `alter-topic-config`) match exactly the base profile's tool_overrides keys MINUS those two. If H.4b's actual base profile uses different tool names (per H.4b's deviation note about substituted names like `get-topic-config`, `read-flink-statement`, etc.), update the overlay's tool_overrides to match — the contract is "base minus exactly 2 tools" regardless of which names the base ultimately committed.

    **canon/customer/acme-bank/adrs/adr-004.md content:**

    ```markdown
    ---
    id: adr-004
    title: Acme Bank developer-sandbox profile overrides
    status: Accepted
    date: 2026-05-17
    phase: H.4c
    family: developer
    ---

    # ADR-004: Acme Bank developer-sandbox profile overrides

    ## Context

    Phase H.4b landed the base `developer/sandbox` profile (`tools/profiles/developer/sandbox.json`) as the first developer-family profile in cflt-ai. Per the canon overlay stack contract, customer engagements can fork that profile by placing an overlay at `canon/customer/<name>/profiles/developer/sandbox.json`.

    Acme Bank's engagement requires stricter dev-sandbox guardrails than the base FSI dev canon ships with:

    1. **No topic destruction self-service**, even in sandbox. Acme's policy is that any DELETE operation against Kafka topics — sandbox or not — goes through a tracked ticket. The base profile permits `delete-topics` and `alter-topic-config` in sandbox; acme removes both.
    2. **No `/dsp:plan` from a dev profile.** Acme treats `/dsp:plan` as operator-only — even read-only plan generation should happen from an engineer profile, not a developer profile. Base FSI dev canon does not block `/dsp:plan` (it's a planning skill, not an apply skill).
    3. **Tightened environment guard**: `acme-*-sandbox` instead of `*-sandbox` — restricts the dev profile to acme-prefixed sandbox clusters specifically.

    This ADR mirrors `adr-003.md` (engineer-family customer overrides for acme — Flink prohibited, audit role required) one family over.

    ## Decision

    `canon/customer/acme-bank/profiles/developer/sandbox.json` ships with:

    - `tool_overrides`: base set MINUS `delete-topics`, `alter-topic-config` (13 tools instead of 15)
    - `skill_blocklist`: `["dsp-apply", "dsp-plan"]` (base only blocks `dsp-apply`)
    - `environment_guard.pattern`: `acme-*-sandbox` (base is `*-sandbox`)
    - `customer_overrides` field documents exactly what was removed/added/tightened vs base, with `adr_ref` pointing here.

    No canon-tier overrides for acme's developer family in this phase — the FSI dev canon overlay (`canon/industry/fsi/developer-sandbox/overrides.yaml`) is inherited unchanged. Future canon-tier acme dev overrides (e.g., stricter dev topic naming) would land in a sibling `canon/customer/acme-bank/developer-sandbox/overrides.yaml` file — deferred until needed.

    ## Consequences

    **Differential gating proof.** `check_tool_permitted("developer/sandbox", "delete-topics", customer="acme-bank")` returns False, while the same call without `customer="acme-bank"` returns True. `check_skill_permitted("developer/sandbox", "dsp-plan", customer="acme-bank")` returns False, base returns True. These differentials are asserted by `tests/test_per_family_isolation.py::TestAcmeBankDeveloperOverlay`.

    **DEVPROF-02 satisfied.** Requirement: "canon/customer/acme-bank/profiles/developer/sandbox.json exists; test proves customer overlay produces ≥1 differential gating decision relative to base FSI dev canon." This ADR records the design decision; the overlay file + tests deliver the proof.

    **Promotion path.** This ADR ships as a stub (one engagement validates dev-tier values in practice → promote H.4b CONTEXT-sourced canon defaults to formal ADRs at `canon/industry/fsi/developer-sandbox/adrs/`).

    ## See Also

    - `canon/customer/acme-bank/adrs/adr-003.md` — engineer-family customer overrides (engagement precedent)
    - `tools/profiles/developer/sandbox.json` — base profile this overlay forks
    - `canon/industry/fsi/developer-sandbox/overrides.yaml` — base FSI dev canon (inherited unchanged)
    - `.planning/phases/H.4c-acme-bank-developer-overlay/H.4c-CONTEXT.md` — phase decisions
    ```
  </action>
  <acceptance_criteria>
    - `canon/customer/acme-bank/profiles/developer/sandbox.json` exists.
    - `canon/customer/acme-bank/adrs/adr-004.md` exists.
    - `python3 -c "import json; p = json.load(open('canon/customer/acme-bank/profiles/developer/sandbox.json')); assert p['family']=='developer'; assert 'dsp-plan' in p['skill_blocklist']; assert 'dsp-apply' in p['skill_blocklist']; assert 'delete-topics' not in p['tool_overrides']; assert 'alter-topic-config' not in p['tool_overrides']; assert p['environment_guard']['pattern']=='acme-*-sandbox'; assert p['customer_overrides']['adr_ref']=='canon/customer/acme-bank/adrs/adr-004.md'"` exits 0.
    - `grep -c "status: Accepted" canon/customer/acme-bank/adrs/adr-004.md` returns 1.
    - `grep -c "adr-003" canon/customer/acme-bank/adrs/adr-004.md` returns ≥ 1.
    - `grep -c "H.4c" canon/customer/acme-bank/adrs/adr-004.md` returns ≥ 1.
  </acceptance_criteria>
</task>

<task type="auto">
  <name>Task 2: Extend tests/test_per_family_isolation.py with TestAcmeBankDeveloperOverlay class (3 tests); generate tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json</name>
  <files>
    - tests/test_per_family_isolation.py
    - tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json
  </files>
  <read_first>
    - tests/test_per_family_isolation.py (H.4b state — append a new class without modifying existing tests)
    - canon/customer/acme-bank/profiles/developer/sandbox.json (from Task 1)
    - tools/profiles/developer/sandbox.json (base profile, for comparison)
    - tools/apply_engine.py (load_profile / check_tool_permitted / check_skill_permitted contracts)
  </read_first>
  <action>
    **Sub-task 2a — Generate the acme-bank dev permits snapshot:**

    ```bash
    python3 -c "
    import json
    from tools.apply_engine import check_tool_permitted, load_tool_classification
    tc = load_tool_classification()
    snapshot = {
        'developer/sandbox @ acme-bank': {
            t: check_tool_permitted('developer/sandbox', t, customer='acme-bank') for t in sorted(tc['tools'])
        }
    }
    print(json.dumps(snapshot, indent=2))
    " > tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json
    ```

    Verify by diff: `diff <(jq -r '."developer/sandbox" | to_entries | map(select(.value==true)) | map(.key) | sort | .[]' tests/snapshots/h4b_developer_sandbox_permits.json) <(jq -r '."developer/sandbox @ acme-bank" | to_entries | map(select(.value==true)) | map(.key) | sort | .[]' tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json)` should show `delete-topics` and `alter-topic-config` (or whichever exact names landed) as ONLY-in-base, with the rest being identical.

    **Sub-task 2b — Append TestAcmeBankDeveloperOverlay class to tests/test_per_family_isolation.py:**

    Read the existing file's imports. The class should reuse already-imported names (`load_profile`, `check_tool_permitted`, `check_skill_permitted`, `pytest`).

    Append at the end of the file:

    ```python
    # ---------------------------------------------------------------------------
    # H.4c — acme-bank developer overlay tests (customer-fork differential gating)
    # ---------------------------------------------------------------------------

    class TestAcmeBankDeveloperOverlay:
        """H.4c — acme-bank customer overlay for developer/sandbox produces ≥1 differential gating decision.

        Mirrors v1.0 ACTG-04's customer-fork proof for the engineer family, one family over.
        """

        def test_acme_bank_developer_overlay_loads(self):
            """load_profile with customer='acme-bank' returns the overlay file, not the base."""
            p = load_profile("developer/sandbox", customer="acme-bank")
            assert p["family"] == "developer"
            assert "customer_overrides" in p, (
                "Overlay file must include customer_overrides field — proves load_profile picked "
                "the overlay path, not the base profile"
            )
            assert p["customer_overrides"]["adr_ref"] == "canon/customer/acme-bank/adrs/adr-004.md"
            # The base profile does NOT have customer_overrides
            base = load_profile("developer/sandbox")
            assert "customer_overrides" not in base, (
                "Base profile must not have customer_overrides — H.4c overlay sets the field, not the base"
            )

        def test_acme_bank_dev_overlay_produces_differential_gating(self):
            """At least one tool-permit decision differs with vs without customer='acme-bank'.

            Specifically: base permits delete-topics + alter-topic-config in sandbox; acme removes both.
            This is the customer-fork differential gating proof for the developer family.
            """
            # Differential #1: delete-topics
            base_decision = check_tool_permitted("developer/sandbox", "delete-topics")
            acme_decision = check_tool_permitted("developer/sandbox", "delete-topics", customer="acme-bank")
            assert base_decision is True, "Base FSI dev sandbox permits delete-topics"
            assert acme_decision is False, "acme overlay must deny delete-topics — differential gating"
            assert base_decision != acme_decision, "delete-topics must show differential gating"

            # Differential #2: alter-topic-config
            base_decision_2 = check_tool_permitted("developer/sandbox", "alter-topic-config")
            acme_decision_2 = check_tool_permitted("developer/sandbox", "alter-topic-config", customer="acme-bank")
            assert base_decision_2 is True, "Base permits alter-topic-config"
            assert acme_decision_2 is False, "acme overlay must deny alter-topic-config — differential gating"

        def test_acme_bank_dev_overlay_blocks_dsp_plan(self):
            """Acme overlay blocks /dsp:plan from dev profiles; base does not.

            Skill-level differential gating proof (complements the tool-level differentials above).
            """
            assert check_skill_permitted("developer/sandbox", "dsp-plan") is True, (
                "Base FSI dev sandbox permits /dsp:plan"
            )
            assert check_skill_permitted("developer/sandbox", "dsp-plan", customer="acme-bank") is False, (
                "acme overlay must block /dsp:plan — skill-level differential gating"
            )

        def test_acme_bank_dev_overlay_snapshot_matches(self):
            """Regression guard: acme-bank dev permit matrix matches the committed baseline."""
            snapshot_path = SNAPSHOT_DIR / "h4c_acme_bank_developer_sandbox_permits.json"
            assert snapshot_path.exists(), (
                "Snapshot missing — regenerate via the one-liner in H.4c-01-PLAN Task 2a"
            )
            snapshot = json.loads(snapshot_path.read_text())
            key = "developer/sandbox @ acme-bank"
            assert key in snapshot
            for tool, expected_permit in snapshot[key].items():
                actual = check_tool_permitted("developer/sandbox", tool, customer="acme-bank")
                assert actual == expected_permit, (
                    f"acme-bank dev permit drift: tool={tool!r} snapshot={expected_permit} live={actual}"
                )
    ```

    Notes:
    - SNAPSHOT_DIR is already imported in tests/test_per_family_isolation.py (H.4b's TestDeveloperSandboxPermitsSnapshot uses it). Reuse.
    - The 3 explicitly-listed test methods (loads, produces_differential_gating, blocks_dsp_plan) satisfy ROADMAP success criterion #1 for H.4c. The 4th (snapshot_matches) is the regression guard.
    - Do NOT modify any existing test class in the file.
  </action>
  <acceptance_criteria>
    - `tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json` exists, parses as JSON, contains top-level key `developer/sandbox @ acme-bank`.
    - `grep -c "class TestAcmeBankDeveloperOverlay" tests/test_per_family_isolation.py` returns exactly 1.
    - `grep -c "def test_acme_bank_developer_overlay_loads" tests/test_per_family_isolation.py` returns 1.
    - `grep -c "def test_acme_bank_dev_overlay_produces_differential_gating" tests/test_per_family_isolation.py` returns 1.
    - `grep -c "def test_acme_bank_dev_overlay_blocks_dsp_plan" tests/test_per_family_isolation.py` returns 1.
    - `pytest tests/test_per_family_isolation.py::TestAcmeBankDeveloperOverlay -v` exits 0.
    - Differential proof: at least 2 entries in the acme snapshot have permit=False where the H.4b snapshot has permit=True (verify via `jq` or by reading both files).
    - H.4b snapshot byte-identical: `git diff HEAD -- tests/snapshots/h4b_developer_sandbox_permits.json` is empty.
  </acceptance_criteria>
</task>

<task type="auto">
  <name>Task 3: Full regression run + write H.4c-01-SUMMARY.md</name>
  <files>
    - .planning/phases/H.4c-acme-bank-developer-overlay/H.4c-01-SUMMARY.md
  </files>
  <read_first>
    - tests/test_per_family_isolation.py (post-Task 2 — full suite)
    - tests/snapshots/h4a_operator_permits.json (must be unchanged)
    - tests/snapshots/h4b_developer_sandbox_permits.json (must be unchanged)
    - tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json (new baseline)
  </read_first>
  <action>
    1. `git diff HEAD -- tests/snapshots/h4a_operator_permits.json` — must be empty.
    2. `git diff HEAD -- tests/snapshots/h4b_developer_sandbox_permits.json` — must be empty.
    3. `pytest tests/test_profile_gating.py tests/test_per_family_isolation.py tests/test_canon_overlay.py -v` — must exit 0.
    4. `pytest tests/ -v --tb=short` — must exit 0 OR only the same 2 pre-existing failures (test_check_canon_parity, test_manifest) persist.
    5. `pytest tests/golden/ -v` — must exit 0.

    Write `.planning/phases/H.4c-acme-bank-developer-overlay/H.4c-01-SUMMARY.md`:
    ```markdown
    # H.4c-01 Summary

    **Plan:** H.4c-01 — acme-bank developer overlay
    **Status:** Complete
    **Date:** 2026-05-17

    ## What landed
    - `canon/customer/acme-bank/profiles/developer/sandbox.json` — acme-bank customer overlay for developer/sandbox profile (removes 2 dev tools, adds dsp-plan to skill_blocklist, tightens environment_guard to acme-*-sandbox)
    - `canon/customer/acme-bank/adrs/adr-004.md` — ADR stub documenting the customer overrides + promotion path
    - `tests/test_per_family_isolation.py` extended with `TestAcmeBankDeveloperOverlay` class (4 test methods)
    - `tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json` — acme-bank dev permits baseline for regression guard

    ## Requirements
    - DEVPROF-02: ✓ Fully satisfied (customer overlay exists + test proves differential gating against base FSI dev canon)

    ## ROADMAP success criteria (H.4c)
    1. ✓ canon/customer/acme-bank/profiles/developer/sandbox.json exists; test demonstrates ≥1 differential gating decision (proven: 2 tool-level + 1 skill-level)
    2. ✓ acme-bank developer overlay test mirrors ACTG-04 pattern from v1.0 Phase 3c (one family over)

    ## Differential gating signals
    - `check_tool_permitted("developer/sandbox", "delete-topics")` → True (base) vs False (acme)
    - `check_tool_permitted("developer/sandbox", "alter-topic-config")` → True (base) vs False (acme)
    - `check_skill_permitted("developer/sandbox", "dsp-plan")` → True (base) vs False (acme)

    ## Regression results
    - `pytest tests/test_profile_gating.py`: [N]/[N] PASS
    - `pytest tests/test_per_family_isolation.py`: [N]/[N] PASS (was N-4 in H.4b; +4 from TestAcmeBankDeveloperOverlay)
    - `pytest tests/test_canon_overlay.py`: [N]/[N] PASS
    - `pytest tests/`: [N+2 total - 2 pre-existing failures] = pass set
    - `pytest tests/golden/`: [N]/[N] PASS
    - H.4a snapshot byte-identical: ✓
    - H.4b snapshot byte-identical: ✓

    ## H.4 sub-phase set complete
    - H.4a ✓ — Profile-family schema extension
    - H.4b ✓ — Developer-sandbox profile + FSI dev canon overlay
    - H.4c ✓ — acme-bank developer overlay

    Total H.4 surface: ~17 files (engine extensions, profiles, canon overlays, ADR stubs, test files, snapshots).
    H.4 satisfies: PROFAM-01, PROFAM-02, DEVPROF-01, DEVCAN-01, DEVPROF-02 (5 of 5 H.4-tagged requirements).

    ## Deferred
    - Promote H.4b CONTEXT-sourced canon defaults to formal ADRs (canon/industry/fsi/developer-sandbox/adrs/) after one acme engagement validates.
    - Additional customer dev overlays (when use case arises).
    - environment_guard CI enforcement (currently advisory).

    ## Self-Check: PASSED
    ```
  </action>
  <acceptance_criteria>
    - `.planning/phases/H.4c-acme-bank-developer-overlay/H.4c-01-SUMMARY.md` exists with `## Self-Check: PASSED`.
    - SUMMARY contains literal strings `DEVPROF-02`, `differential gating`, `delete-topics`, `dsp-plan`.
    - `git diff HEAD -- tests/snapshots/h4a_operator_permits.json` returns empty.
    - `git diff HEAD -- tests/snapshots/h4b_developer_sandbox_permits.json` returns empty.
    - `pytest tests/test_per_family_isolation.py::TestAcmeBankDeveloperOverlay -v` exits 0.
    - `git status` shows only the 4 plan-listed files + SUMMARY + STATE/ROADMAP/REQUIREMENTS metadata. Nothing in `tools/`, `.github/`, `tests/golden/`.
  </acceptance_criteria>
</task>

</tasks>

<verification>
After all tasks complete:

1. **Acme overlay loads** — `python3 -c "from tools.apply_engine import load_profile; p = load_profile('developer/sandbox', customer='acme-bank'); assert p['family']=='developer'; assert 'customer_overrides' in p"` exits 0.
2. **Differential gating proven** — `python3 -c "from tools.apply_engine import check_tool_permitted, check_skill_permitted; assert check_tool_permitted('developer/sandbox', 'delete-topics') and not check_tool_permitted('developer/sandbox', 'delete-topics', customer='acme-bank'); assert check_skill_permitted('developer/sandbox', 'dsp-plan') and not check_skill_permitted('developer/sandbox', 'dsp-plan', customer='acme-bank')"` exits 0.
3. **ADR stub present** — `grep -q "status: Accepted" canon/customer/acme-bank/adrs/adr-004.md`.
4. **All targeted tests pass** — `pytest tests/test_per_family_isolation.py::TestAcmeBankDeveloperOverlay -v` exits 0.
5. **H.4a + H.4b snapshots unchanged** — `git diff HEAD -- tests/snapshots/h4a_operator_permits.json tests/snapshots/h4b_developer_sandbox_permits.json` is empty.
6. **No spillover** — `git status` shows only the 4 plan-modified files + SUMMARY + .planning metadata. Zero changes to apply_engine.py, canon/stack.py, FSI dev canon overlay, or operator profiles.

All 6 must pass before phase complete. Failure → gap closure.
</verification>
