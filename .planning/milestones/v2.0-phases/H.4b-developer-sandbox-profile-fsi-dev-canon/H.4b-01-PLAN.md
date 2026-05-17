---
phase: H.4b-developer-sandbox-profile-fsi-dev-canon
plan: 01
type: execute
wave: 1
depends_on: [H.4a-01]
files_modified:
  - tools/apply_engine.py
  - tools/profiles/developer/sandbox.json
  - canon/stack.py
  - canon/industry/fsi/developer-sandbox/overrides.yaml
  - canon/industry/fsi/developer-sandbox/adrs/README.md
  - tests/test_per_family_isolation.py
  - tests/snapshots/h4b_developer_sandbox_permits.json
autonomous: true
requirements: [DEVPROF-01, DEVCAN-01, DEVPROF-02, PROFAM-02]
requirements_addressed: [DEVPROF-01, DEVCAN-01, DEVPROF-02, PROFAM-02]

must_haves:
  truths:
    - "`tools/profiles/developer/sandbox.json` exists with `family: \"developer\"`, `primary_tooling.skills` array listing 4 streaming-skills-plugin entries, `tool_overrides` dict with ≥15 dev-tier tools, `skill_blocklist` containing `\"dsp-apply\"`, `environment_guard.pattern == \"*-sandbox\"`, `canon_layer == \"industry/fsi/developer-sandbox\"`"
    - "`load_profile(\"developer/sandbox\")` resolves the slash to filesystem path `tools/profiles/developer/sandbox.json` and returns the parsed JSON with H.4a validation applied"
    - "`VALID_PROFILES` set in `tools/apply_engine.py` includes `\"developer/sandbox\"`"
    - "`check_tool_permitted(\"developer/sandbox\", tool)` returns True for tools in `tool_overrides`, False otherwise (fail-closed) — proven by snapshot at `tests/snapshots/h4b_developer_sandbox_permits.json`"
    - "`check_skill_permitted(profile_name, skill_name)` function exists in `tools/apply_engine.py`; returns False for skills in profile's `skill_blocklist`, True otherwise; operator profiles (no blocklist) return True for all skills"
    - "`canon/industry/fsi/developer-sandbox/overrides.yaml` exists with every Confluent Canon dimension from CLAUDE.md given explicit dev-tier values: security.auth_mechanism=OAUTHBEARER, processing_guarantees.delivery=at_least_once, schema_registry.format=json, schema_registry.compatibility_mode=BACKWARD, topic_design.replication_factor=1, topic_design.min_insync_replicas=1, topic_design.naming_convention contains '-sandbox', producer.acks=1, consumer.auto_offset_reset=latest"
    - "Every override key in `canon/industry/fsi/developer-sandbox/overrides.yaml` has an `override_source` field (mirrors industry/fsi/overrides.yaml pattern)"
    - "`canon/industry/fsi/developer-sandbox/adrs/README.md` exists as a stub registry naming the CONTEXT-sourced decisions"
    - "`canon/stack.py` `resolve_stack()` accepts `family=\"operator\"` (default) and `canon_layer=None` keyword args; when `family==\"developer\"`, routes the industry layer to the profile's `canon_layer` path; backward compatible — existing 4 callsites (act_gates.py, review-to-docx.py, test_review_to_docx.py, test_canon_overlay.py) work byte-identical when called with no args"
    - "`tests/test_per_family_isolation.py` exists with 4 test classes covering: (1) operator-cannot-invoke-developer-tier, (2) developer-cannot-invoke-operator-only, (3) dsp-apply-fail-closed-under-developer, (4) cross-family-load-isolation"
    - "`tests/snapshots/h4b_developer_sandbox_permits.json` exists with the full (developer/sandbox × every-tool) permit decision matrix matching post-H.4b live behavior"
    - "`pytest tests/test_profile_gating.py tests/test_per_family_isolation.py tests/test_canon_overlay.py -v` exits 0 — all tests pass"
    - "`pytest tests/` exits 0 (or only the 2 pre-existing fsi-dsp drift failures documented in H.4a-01-SUMMARY remain — no NEW failures introduced)"
    - "H.4a's operator-permits snapshot `tests/snapshots/h4a_operator_permits.json` is UNCHANGED (byte-identical) — H.4b does not touch operator behavior"
    - "No changes to `canon/customer/acme-bank/` (H.4c territory)"
    - "No changes to `.github/workflows/` or `tests/golden/`"
  artifacts:
    - path: "tools/profiles/developer/sandbox.json"
      provides: "First developer-family profile — dev-tier sandbox tooling, /dsp:apply blocked, FSI dev canon layer pointer"
      contains:
        - "\"family\": \"developer\""
        - "\"name\": \"developer/sandbox\""
        - "\"tool_overrides\""
        - "\"skill_blocklist\""
        - "\"environment_guard\""
        - "\"canon_layer\": \"industry/fsi/developer-sandbox\""
        - "streaming-skills-plugin"
        - "dsp-apply"
    - path: "canon/industry/fsi/developer-sandbox/overrides.yaml"
      provides: "FSI dev-tier canon overlay — bifurcated from prod FSI overlay with dev-appropriate defaults"
      contains:
        - "OAUTHBEARER"
        - "at_least_once"
        - "json"
        - "BACKWARD"
        - "replication_factor: 1"
        - "-sandbox"
        - "override_source"
    - path: "tools/apply_engine.py"
      provides: "Extended to include developer/sandbox in VALID_PROFILES, slash-path resolution in load_profile, new check_skill_permitted function"
      contains:
        - "developer/sandbox"
        - "check_skill_permitted"
        - "skill_blocklist"
    - path: "canon/stack.py"
      provides: "resolve_stack() with family + canon_layer parameters; backward compatible default"
      contains:
        - "family"
        - "canon_layer"
        - "industry/fsi/developer-sandbox"
    - path: "tests/test_per_family_isolation.py"
      provides: "Negative-space test matrix proving operator/developer family isolation"
      contains:
        - "TestOperatorCannotInvokeDeveloperTools"
        - "TestDeveloperCannotInvokeOperatorOnlyTools"
        - "TestDspApplyFailsClosedUnderDeveloper"
        - "TestCrossFamilyLoadIsolation"
    - path: "tests/snapshots/h4b_developer_sandbox_permits.json"
      provides: "Snapshot of (developer/sandbox × every-tool) permit decisions for regression guard"
      contains:
        - "developer/sandbox"
  key_links:
    - from: "tools/profiles/developer/sandbox.json:canon_layer"
      to: "canon/industry/fsi/developer-sandbox/overrides.yaml"
      via: "canon/stack.py resolve_stack() reads canon_layer from profile and loads that path as the industry layer when family==developer"
      pattern: "industry/fsi/developer-sandbox"
    - from: "tools/apply_engine.py:check_tool_permitted"
      to: "tools/profiles/developer/sandbox.json:tool_overrides"
      via: "developer-branch dispatch (H.4a) reads tool_overrides; tool_name lookup determines permit/deny"
      pattern: "tool_overrides"
    - from: "tools/apply_engine.py:check_skill_permitted"
      to: "tools/profiles/developer/sandbox.json:skill_blocklist"
      via: "Skill name lookup in profile's blocklist determines permit/deny"
      pattern: "skill_blocklist"
---

<objective>
Land the first developer-family profile + the FSI dev canon overlay it stacks on, prove operator/developer isolation via parametrized negative-space tests, and extend the canon resolver to route industry-layer loads based on family. Single PLAN, single wave. After this plan, DEVPROF-01 / DEVCAN-01 / PROFAM-02 are fully satisfied; DEVPROF-02 is partially satisfied (the customer-fork side requires H.4c).

The work is concentrated in 7 files: 1 new profile JSON, 1 new canon overlay YAML, 1 new ADR stub, 1 engine extension, 1 canon resolver extension, 1 new test file, 1 new snapshot. Zero changes to existing operator profiles, zero changes to H.4a's snapshot, zero changes to golden harnesses or CI workflows.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/H.4b-developer-sandbox-profile-fsi-dev-canon/H.4b-CONTEXT.md
@.planning/phases/H.4a-profile-family-schema-extension/H.4a-CONTEXT.md
@CLAUDE.md
@tools/apply_engine.py
@tools/profiles/tool_classification.json
@canon/stack.py
@canon/base/defaults.yaml
@canon/industry/fsi/overrides.yaml
@canon/customer/acme-bank/profiles/engineer.json
@tests/test_profile_gating.py
@tests/test_canon_overlay.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Author tools/profiles/developer/sandbox.json with full developer-family shape</name>
  <files>
    - tools/profiles/developer/sandbox.json
  </files>
  <read_first>
    - tools/profiles/engineer.json (sibling operator profile — for indentation conventions)
    - tools/profiles/tool_classification.json (to validate every tool_overrides key is a real tool name in the classification table)
    - .planning/phases/H.4b-developer-sandbox-profile-fsi-dev-canon/H.4b-CONTEXT.md (D-01 — full shape)
  </read_first>
  <action>
    Create the directory `tools/profiles/developer/` and the file `tools/profiles/developer/sandbox.json` with content:

    ```json
    {
      "name": "developer/sandbox",
      "description": "Developer-tier sandbox profile: upstream confluent-agent-skills available; data-plane ops permitted on *-sandbox clusters; /dsp:apply blocked. First developer-family profile (H.4b).",
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
        "delete-topics": "developer-sandbox",
        "alter-topic-config": "developer-sandbox",
        "list-topics": "developer-sandbox",
        "describe-topic": "developer-sandbox",
        "create-flink-statement": "developer-sandbox",
        "delete-flink-statements": "developer-sandbox",
        "list-flink-statements": "developer-sandbox",
        "describe-flink-statement": "developer-sandbox",
        "list-clusters": "developer-sandbox",
        "describe-cluster": "developer-sandbox",
        "list-schemas": "developer-sandbox",
        "describe-schema": "developer-sandbox"
      },
      "skill_blocklist": [
        "dsp-apply"
      ],
      "environment_guard": {
        "pattern": "*-sandbox",
        "enforcement": "advisory"
      },
      "canon_layer": "industry/fsi/developer-sandbox"
    }
    ```

    Before committing: open `tools/profiles/tool_classification.json` and verify each `tool_overrides` key is a real tool name in the classification table. If any name doesn't match (e.g., the classification table uses `list-cluster` instead of `list-clusters`), correct the entry in `sandbox.json` to match the real name. Names not in the table MUST be removed (we cannot override a non-existent tool's permit decision). Document any name corrections in the commit message.
  </action>
  <acceptance_criteria>
    - File `tools/profiles/developer/sandbox.json` exists.
    - `python3 -c "import json; p = json.load(open('tools/profiles/developer/sandbox.json')); assert p['family']=='developer'; assert p['canon_layer']=='industry/fsi/developer-sandbox'; assert 'dsp-apply' in p['skill_blocklist']; assert len(p['tool_overrides']) >= 15; assert p['environment_guard']['pattern']=='*-sandbox'"` exits 0.
    - `python3 -c "import json; tc = json.load(open('tools/profiles/tool_classification.json'))['tools']; p = json.load(open('tools/profiles/developer/sandbox.json')); missing = [t for t in p['tool_overrides'] if t not in tc]; assert not missing, f'tools not in classification: {missing}'"` exits 0 (every tool_overrides entry maps to a real classified tool).
  </acceptance_criteria>
</task>

<task type="auto">
  <name>Task 2: Extend tools/apply_engine.py — add "developer/sandbox" to VALID_PROFILES, add slash-path resolution to load_profile(), add check_skill_permitted()</name>
  <files>
    - tools/apply_engine.py
  </files>
  <read_first>
    - tools/apply_engine.py (current — H.4a state: VALID_PROFILES, VALID_FAMILIES, _normalize_and_validate_profile, load_profile, check_tool_permitted)
    - tools/profiles/developer/sandbox.json (the profile that VALID_PROFILES must accept)
    - .planning/phases/H.4b-developer-sandbox-profile-fsi-dev-canon/H.4b-CONTEXT.md (D-03, D-04, D-05)
  </read_first>
  <action>
    Three targeted changes to `tools/apply_engine.py`:

    1. **Extend `VALID_PROFILES`** (currently `{"read-only", "engineer", "break-glass"}` from v1.0):
       ```python
       VALID_PROFILES = {"read-only", "engineer", "break-glass", "developer/sandbox"}
       ```

    2. **Update `load_profile()` path resolution** — modify the profile-file lookup logic so that profile names containing `/` resolve to nested directories. Currently `load_profile("engineer")` reads `PROFILES_DIR / "engineer.json"`. After this change, `load_profile("developer/sandbox")` reads `PROFILES_DIR / "developer" / "sandbox.json"`.

       Apply the same logic to the customer-overlay branch (so that `load_profile("developer/sandbox", customer="acme-bank")` would look at `canon/customer/acme-bank/profiles/developer/sandbox.json` if it exists — this prepares for H.4c).

       The path-resolution helper:
       ```python
       def _profile_path(profiles_root: Path, profile_name: str) -> Path:
           """Resolve profile_name (possibly slash-separated) to filesystem path under profiles_root."""
           return profiles_root / (profile_name + ".json")
       ```
       `Path.__truediv__` already accepts slash-containing strings as relative paths, so `profiles_root / "developer/sandbox.json"` correctly resolves to `profiles_root / "developer" / "sandbox.json"`. Use that — no additional split logic needed.

       Replace the file-load lines in `load_profile()`:
       - Was: `profile_path = PROFILES_DIR / f"{profile_name}.json"`
       - Becomes: `profile_path = _profile_path(PROFILES_DIR, profile_name)`
       - Customer overlay: was `customer_profile = PROJECT_ROOT / "canon" / "customer" / customer / "profiles" / f"{profile_name}.json"` → becomes `customer_profile = _profile_path(PROJECT_ROOT / "canon" / "customer" / customer / "profiles", profile_name)`

    3. **Add `check_skill_permitted()` function** — place immediately after `check_tool_permitted()`:
       ```python
       def check_skill_permitted(profile_name: str, skill_name: str, customer: Optional[str] = None) -> bool:
           """Check whether profile_name permits invoking skill_name.

           Consults the profile's skill_blocklist (developer family) or returns True
           (operator family, which has no blocklist field).

           Args:
               profile_name: One of VALID_PROFILES.
               skill_name:   Skill identifier (e.g., 'dsp-apply', 'wiki-validate').
               customer:     Optional customer overlay name (keyword-only).

           Returns:
               False if skill_name is in the profile's skill_blocklist, True otherwise.
               Operator profiles return True for all skills (no blocklist field).
           """
           profile = load_profile(profile_name, customer=customer)
           blocklist = profile.get("skill_blocklist", [])
           return skill_name not in blocklist
       ```

    Do NOT modify `check_tool_permitted()` — H.4a's branch logic already handles developer-family dispatch. Verify (mentally) that calling `check_tool_permitted("developer/sandbox", "produce-message")` will:
    - `load_profile("developer/sandbox")` → returns dict with family="developer"
    - Family branch → `family == "developer"` path
    - `overrides = profile.get("tool_overrides", {})` → returns the 15-entry dict
    - `return "produce-message" in overrides` → True ✓
  </action>
  <acceptance_criteria>
    - `grep -c "\"developer/sandbox\"" tools/apply_engine.py` returns ≥ 1 (in VALID_PROFILES).
    - `grep -c "_profile_path" tools/apply_engine.py` returns ≥ 3 (1 def + 2 callsites: base + customer overlay).
    - `grep -c "def check_skill_permitted" tools/apply_engine.py` returns exactly 1.
    - `grep -c "skill_blocklist" tools/apply_engine.py` returns ≥ 2 (docstring + .get() call).
    - `python3 -c "from tools.apply_engine import load_profile; p = load_profile('developer/sandbox'); assert p['family']=='developer'; assert p['canon_layer']=='industry/fsi/developer-sandbox'"` exits 0.
    - `python3 -c "from tools.apply_engine import check_tool_permitted; assert check_tool_permitted('developer/sandbox', 'produce-message') is True; assert check_tool_permitted('developer/sandbox', 'list-environments') is False"` exits 0 (developer-branch dispatch sanity).
    - `python3 -c "from tools.apply_engine import check_skill_permitted; assert check_skill_permitted('developer/sandbox', 'dsp-apply') is False; assert check_skill_permitted('engineer', 'dsp-apply') is True"` exits 0 (skill blocklist sanity).
    - `pytest tests/test_profile_gating.py -v` exits 0 — H.4a tests still all pass; new profile doesn't break anything.
  </acceptance_criteria>
</task>

<task type="auto">
  <name>Task 3: Author canon/industry/fsi/developer-sandbox/overrides.yaml + canon/industry/fsi/developer-sandbox/adrs/README.md</name>
  <files>
    - canon/industry/fsi/developer-sandbox/overrides.yaml
    - canon/industry/fsi/developer-sandbox/adrs/README.md
  </files>
  <read_first>
    - canon/industry/fsi/overrides.yaml (sibling prod FSI overlay — for YAML conventions, override_source field shape)
    - canon/base/defaults.yaml (the layer this composes on top of — every override here intentionally departs from base)
    - canon/industry/fsi/adrs/README.md if exists, else canon/industry/fsi/README.md (for ADR registry conventions)
    - CLAUDE.md (project root — every override_source field references either an ADR or "H.4b CONTEXT D-07 — <dimension>" since no formal ADRs exist yet for dev-tier)
    - .planning/phases/H.4b-developer-sandbox-profile-fsi-dev-canon/H.4b-CONTEXT.md (D-07, D-08 — full YAML shape + ADR stub)
  </read_first>
  <action>
    Create directory `canon/industry/fsi/developer-sandbox/` and `canon/industry/fsi/developer-sandbox/adrs/`.

    **overrides.yaml content:**
    ```yaml
    # FSI developer-sandbox overrides — dev-tier values distinct from prod FSI overlay.
    # Composes on top of canon/base/defaults.yaml via dict merge when family=developer
    # and the profile's canon_layer points here.
    # Override rule: each override references its rationale (formal ADR or H.4b CONTEXT decision).
    #
    # Promote CONTEXT-sourced decisions to formal ADRs (canon/industry/fsi/developer-sandbox/adrs/)
    # after one customer engagement validates the dev-tier values in practice.

    security:
      auth_mechanism: "OAUTHBEARER"          # Dev-tier — easier than mTLS for fast iteration
      override_source: "H.4b CONTEXT D-07 — dev-tier auth"
      service_account_scope: "per_application"
      audit_log: false                       # Sandbox — no compliance log requirement

    processing_guarantees:
      delivery: "at_least_once"              # Dev iteration; exactly_once is prod-only
      override_source: "H.4b CONTEXT D-07 — dev-tier processing"

    schema_registry:
      format: "json"                         # JSON Schema acceptable in sandbox
      override_source: "H.4b CONTEXT D-07 — dev-tier schema"
      subject_naming_strategy: "TopicNameStrategy"
      compatibility_mode: "BACKWARD"

    topic_design:
      replication_factor: 1                  # Sandbox tolerates RF=1
      min_insync_replicas: 1
      naming_convention: "<owner>.<feature>.<entity>-sandbox"
      naming_source: "H.4b CONTEXT D-07 — dev topic naming"
      partition_formula: "1"                 # Sandbox — single partition is enough

    producer:
      acks: "1"                              # Sandbox — performance over durability
      enable_idempotence: false              # Defer to user choice
      compression_type: "snappy"             # Faster for dev iteration

    consumer:
      group_design: "per_developer_instance" # OK in sandbox — easy reset
      auto_offset_reset: "latest"            # Common dev preference
      enable_auto_commit: true               # OK for non-critical dev paths

    flink_sql:
      api_preference: "table"                # Same as base
      watermark_strategy: "BOUNDED_OUT_OF_ORDERNESS"
      window_preference: "tumbling"
      scan_startup_mode: "latest-offset"     # Dev — latest is fine, replay rarely needed

    cluster_linking:
      preferred_over: "none"                 # Sandbox — single cluster typically
      override_source: "H.4b CONTEXT D-07 — dev cluster topology"

    environment_guard:
      pattern: "*-sandbox"
      enforcement: "advisory"
      override_source: "H.4b CONTEXT D-07 — dev environment guard"
    ```

    **adrs/README.md content:**
    ```markdown
    # FSI Developer-Sandbox Canon ADRs

    This directory will house formal Architecture Decision Records for the FSI
    developer-sandbox canon overlay (`canon/industry/fsi/developer-sandbox/`).

    ## Status: Pre-ADR (H.4b)

    All current overrides in `overrides.yaml` reference `H.4b CONTEXT D-07 — <dimension>`
    as their source. These are deliberate departures from the FSI prod overlay
    (`canon/industry/fsi/overrides.yaml`), grounded in dev-tier sandbox semantics:

    | Dimension | FSI Prod | FSI Dev-Sandbox | Why |
    |-----------|----------|-----------------|-----|
    | security.auth_mechanism | mTLS + RBAC | OAUTHBEARER | Faster iteration in sandbox |
    | processing_guarantees.delivery | exactly_once | at_least_once | EOS is prod-only |
    | schema_registry.format | avro | json | JSON acceptable in sandbox |
    | schema_registry.compatibility_mode | (varies, often FULL) | BACKWARD | Minimum baseline |
    | topic_design.replication_factor | 3 | 1 | Sandbox tolerance |
    | topic_design.min_insync_replicas | 2 | 1 | Sandbox tolerance |
    | topic_design.naming_convention | <domain>.<application>.<entity>.<event> | <owner>.<feature>.<entity>-sandbox | Dev ownership pattern |
    | producer.acks | all | 1 | Performance over durability |
    | producer.enable_idempotence | true | false | User choice in dev |
    | consumer.auto_offset_reset | earliest | latest | Common dev preference |
    | consumer.enable_auto_commit | false | true | OK in non-critical dev paths |
    | cluster_linking | preferred over MM2 | none | Single-cluster sandbox typical |

    ## Promotion Path

    After **one** customer engagement using `developer/sandbox` profile in practice,
    each H.4b CONTEXT-sourced override above MUST be promoted to a formal ADR
    (`adr-001.md`, `adr-002.md`, etc.) following the FSI ADR template at
    `../../adrs/`. Until then, the table above is the canonical justification.

    ## See Also

    - `canon/industry/fsi/overrides.yaml` — prod FSI overlay (the bifurcation point)
    - `canon/industry/fsi/adrs/` — prod FSI ADR registry
    - `tools/profiles/developer/sandbox.json` — first profile that consumes this overlay
    ```
  </action>
  <acceptance_criteria>
    - `canon/industry/fsi/developer-sandbox/overrides.yaml` exists.
    - `canon/industry/fsi/developer-sandbox/adrs/README.md` exists.
    - YAML parses: `python3 -c "import yaml; d = yaml.safe_load(open('canon/industry/fsi/developer-sandbox/overrides.yaml')); assert d['security']['auth_mechanism']=='OAUTHBEARER'; assert d['processing_guarantees']['delivery']=='at_least_once'; assert d['schema_registry']['format']=='json'; assert d['topic_design']['replication_factor']==1; assert '-sandbox' in d['topic_design']['naming_convention']"` exits 0.
    - Every top-level YAML section contains an `override_source` field OR every override key has a source field within its section: `python3 -c "import yaml; d = yaml.safe_load(open('canon/industry/fsi/developer-sandbox/overrides.yaml')); sources = [k for sect in d.values() if isinstance(sect, dict) for k in sect if 'source' in k]; assert len(sources) >= 5, f'too few override_source fields: {sources}'"` exits 0.
    - `grep -c "H.4b CONTEXT" canon/industry/fsi/developer-sandbox/overrides.yaml` returns ≥ 5.
    - `grep -c "FSI Developer-Sandbox Canon ADRs" canon/industry/fsi/developer-sandbox/adrs/README.md` returns 1.
    - `grep -c "Promotion Path" canon/industry/fsi/developer-sandbox/adrs/README.md` returns 1.
  </acceptance_criteria>
</task>

<task type="auto">
  <name>Task 4: Extend canon/stack.py resolve_stack() with family + canon_layer parameters (backward-compatible default to operator)</name>
  <files>
    - canon/stack.py
  </files>
  <read_first>
    - canon/stack.py (current — LAYER_ORDER + resolve_stack + _load_layer)
    - tests/test_canon_overlay.py (callsite reference — confirm existing test signature)
    - tools/act_gates.py (callsite — confirm existing call shape)
    - tools/review-to-docx.py (callsite — confirm existing call shape)
    - .planning/phases/H.4b-developer-sandbox-profile-fsi-dev-canon/H.4b-CONTEXT.md (D-06 — resolve_stack signature)
  </read_first>
  <action>
    Modify `canon/stack.py` — extend `resolve_stack()` to accept `family` and `canon_layer` keyword arguments while preserving backward-compatible no-arg calls.

    Concrete changes:

    1. Replace the hardcoded `LAYER_ORDER` constant with a function `_layer_order_for(family: str, canon_layer: Optional[str] = None) -> List[str]`:
       ```python
       def _layer_order_for(family: str = "operator", canon_layer: Optional[str] = None) -> List[str]:
           """Compute the layer order for the canon stack.

           Operator family uses the prod FSI overlay (industry/fsi).
           Developer family uses canon_layer (defaults to industry/fsi/developer-sandbox).

           Customer and engagement layers are appended last regardless of family.
           """
           if family == "developer":
               industry_layer = canon_layer or "industry/fsi/developer-sandbox"
           elif family == "operator":
               industry_layer = canon_layer or "industry/fsi"
           else:
               raise ValueError(f"Unknown profile family for canon stack: {family!r}")
           return ["base", industry_layer, "customer", "engagement"]
       ```

    2. Keep `LAYER_ORDER = _layer_order_for()` as a module-level constant for back-compat (anything that imported `LAYER_ORDER` directly still gets the operator default).

    3. Modify `resolve_stack()` signature — add `family` and `canon_layer` keyword args, default to operator family:
       ```python
       def resolve_stack(family: str = "operator", canon_layer: Optional[str] = None, ...existing-args-if-any) -> Tuple[Dict, str]:
           """Resolve the canon stack for a given profile family.

           Args:
               family:      "operator" (default) or "developer" — selects which
                            industry-layer path to use as the second composition layer.
               canon_layer: Optional explicit industry-layer path (e.g., 'industry/fsi/developer-sandbox').
                            Used when the profile JSON specifies its own canon_layer.
                            If None, defaults are: operator -> 'industry/fsi',
                            developer -> 'industry/fsi/developer-sandbox'.

           Returns:
               (resolved_config_dict, stack_hash_hex)
           """
           layers = _layer_order_for(family=family, canon_layer=canon_layer)
           # ... existing merge logic, but iterate over `layers` instead of LAYER_ORDER constant ...
       ```

    4. Update the merge loop inside `resolve_stack()` to iterate over the `layers` variable instead of the module-level `LAYER_ORDER`.

    5. Preserve existing callsites — `resolve_stack()` called with no args returns operator-family operator-FSI-overlay stack, byte-identical to v1.0 behavior. Tests in `tests/test_canon_overlay.py` should not need updates if they only test no-args calls.

    Verify backward compatibility: read each of the 4 callsites (`tools/act_gates.py`, `tools/review-to-docx.py`, `tests/test_review_to_docx.py`, `tests/test_canon_overlay.py`) and confirm none use the `LAYER_ORDER` constant directly OR if any do, confirm the new module-level `LAYER_ORDER = _layer_order_for()` preserves them.
  </action>
  <acceptance_criteria>
    - `grep -c "def _layer_order_for" canon/stack.py` returns exactly 1.
    - `grep -c "family:" canon/stack.py` returns ≥ 2 (function arg + docstring).
    - `grep -c "canon_layer" canon/stack.py` returns ≥ 2.
    - `grep -c "industry/fsi/developer-sandbox" canon/stack.py` returns ≥ 1.
    - Back-compat: `python3 -c "from canon.stack import resolve_stack; cfg, h = resolve_stack(); assert cfg['security']['auth_mechanism'] == 'mTLS + RBAC'"` exits 0 (operator default — same as v1.0).
    - Developer family: `python3 -c "from canon.stack import resolve_stack; cfg, h = resolve_stack(family='developer'); assert cfg['security']['auth_mechanism'] == 'OAUTHBEARER'; assert cfg['processing_guarantees']['delivery'] == 'at_least_once'; assert cfg['topic_design']['replication_factor'] == 1"` exits 0.
    - `pytest tests/test_canon_overlay.py -v` exits 0 — existing tests pass byte-identical.
  </acceptance_criteria>
</task>

<task type="auto">
  <name>Task 5: Create tests/test_per_family_isolation.py with 4 negative-space test classes + generate tests/snapshots/h4b_developer_sandbox_permits.json</name>
  <files>
    - tests/test_per_family_isolation.py
    - tests/snapshots/h4b_developer_sandbox_permits.json
  </files>
  <read_first>
    - tools/apply_engine.py (post-Task 2 — check_tool_permitted, check_skill_permitted, load_profile contracts)
    - tools/profiles/developer/sandbox.json (the profile under test)
    - tools/profiles/tool_classification.json (the tool universe)
    - tests/test_profile_gating.py (H.4a test patterns — fixtures, parametrize shape)
    - .planning/phases/H.4b-developer-sandbox-profile-fsi-dev-canon/H.4b-CONTEXT.md (D-09 test surface)
  </read_first>
  <action>
    **Sub-task 5a — Generate the developer-sandbox permits snapshot:**

    ```bash
    python3 -c "
    import json
    from tools.apply_engine import check_tool_permitted, load_tool_classification
    tc = load_tool_classification()
    snapshot = {'developer/sandbox': {t: check_tool_permitted('developer/sandbox', t) for t in sorted(tc['tools'])}}
    print(json.dumps(snapshot, indent=2))
    " > tests/snapshots/h4b_developer_sandbox_permits.json
    ```

    Verify by reading the file: should have ~54 entries; ~15 True (the tool_overrides keys), ~39 False (everything else).

    **Sub-task 5b — Create tests/test_per_family_isolation.py:**

    ```python
    """
    Phase H.4b — Per-family isolation tests.

    Proves that operator-family profiles cannot invoke developer-family tools and
    developer-family profiles cannot invoke operator-tier-only tools, AND that
    /dsp:apply is blocked under any developer profile.

    Companion to tests/test_profile_gating.py (H.4a family schema tests).
    """
    import json
    import pytest
    from pathlib import Path

    from tools.apply_engine import (
        check_tool_permitted,
        check_skill_permitted,
        load_profile,
        load_tool_classification,
    )

    SNAPSHOT_DIR = Path(__file__).parent / "snapshots"


    class TestOperatorCannotInvokeDeveloperTools:
        """Operator profiles cannot invoke tools that ONLY appear in developer tool_overrides."""

        @pytest.fixture
        def developer_only_tools(self):
            """Tools in developer/sandbox tool_overrides that are above operator's tier in classification."""
            dev_profile = load_profile("developer/sandbox")
            classification = load_tool_classification()["tools"]
            # A "developer-only" tool here means: in developer's overrides AND in classification at
            # a tier higher than the operator profile being tested. We pick tools that read-only
            # cannot invoke (so the operator-cannot-invoke-developer-tier story holds tightly).
            return [t for t in dev_profile["tool_overrides"] if t in classification]

        @pytest.mark.parametrize("operator_profile", ["read-only"])
        def test_read_only_cannot_invoke_developer_data_plane_tools(self, operator_profile, developer_only_tools):
            """read-only operator cannot invoke produce-message, create-topics, delete-topics, etc."""
            # Pick tools the developer profile permits that read-only definitely cannot at its tier
            high_tier_dev_tools = ["produce-message", "create-topics", "delete-topics", "alter-topic-config"]
            for tool in high_tier_dev_tools:
                if tool in developer_only_tools:
                    assert check_tool_permitted(operator_profile, tool) is False, (
                        f"read-only should NOT be permitted {tool!r} (operator tier cascade should deny)"
                    )


    class TestDeveloperCannotInvokeOperatorOnlyTools:
        """developer/sandbox cannot invoke tools that are NOT in its tool_overrides."""

        @pytest.fixture
        def operator_only_tools(self):
            """Tools in the classification table that developer/sandbox does NOT list in tool_overrides."""
            dev_profile = load_profile("developer/sandbox")
            classification = load_tool_classification()["tools"]
            return [t for t in classification if t not in dev_profile["tool_overrides"]]

        def test_developer_cannot_invoke_operator_only_tools(self, operator_only_tools):
            """For at least 3 operator-only tools, developer/sandbox returns False."""
            assert len(operator_only_tools) >= 3, "Need at least 3 operator-only tools for a meaningful test"
            tested = 0
            for tool in operator_only_tools:
                assert check_tool_permitted("developer/sandbox", tool) is False, (
                    f"developer/sandbox should NOT be permitted {tool!r} (not in tool_overrides — fail-closed)"
                )
                tested += 1
                if tested >= 3:
                    break  # 3 is enough to prove the contract

        def test_developer_cannot_invoke_destructive_operator_tools(self):
            """Explicit destructive-tool test: delete-environment, delete-cluster, etc., not in dev overrides."""
            destructive = ["delete-environment", "delete-cluster", "delete-environment-by-id"]
            classification = load_tool_classification()["tools"]
            # Filter to those actually in the classification table (some may have different names)
            present = [t for t in destructive if t in classification]
            for tool in present:
                assert check_tool_permitted("developer/sandbox", tool) is False, (
                    f"developer/sandbox MUST deny destructive {tool!r}"
                )


    class TestDspApplyFailsClosedUnderDeveloper:
        """/dsp:apply is in developer/sandbox's skill_blocklist — check_skill_permitted returns False."""

        def test_dsp_apply_blocked_under_developer_sandbox(self):
            assert check_skill_permitted("developer/sandbox", "dsp-apply") is False

        @pytest.mark.parametrize("operator_profile", ["read-only", "engineer", "break-glass"])
        def test_dsp_apply_permitted_under_operator_profiles(self, operator_profile):
            assert check_skill_permitted(operator_profile, "dsp-apply") is True


    class TestCrossFamilyLoadIsolation:
        """load_profile() returns the correct family for each profile without cross-contamination."""

        def test_developer_sandbox_loads_as_developer_family(self):
            p = load_profile("developer/sandbox")
            assert p["family"] == "developer"
            assert "tool_overrides" in p
            assert "allowed_operations" not in p

        @pytest.mark.parametrize("operator_profile", ["read-only", "engineer", "break-glass"])
        def test_operator_profiles_load_as_operator_family(self, operator_profile):
            p = load_profile(operator_profile)
            assert p["family"] == "operator"
            assert "allowed_operations" in p
            assert "tool_overrides" not in p


    class TestDeveloperSandboxPermitsSnapshot:
        """Regression guard: the (developer/sandbox × tool) permit matrix matches the committed baseline."""

        def test_developer_sandbox_permits_match_snapshot(self):
            snapshot_path = SNAPSHOT_DIR / "h4b_developer_sandbox_permits.json"
            assert snapshot_path.exists(), (
                "Snapshot missing — regenerate via the bash one-liner in H.4b-01-PLAN Task 5a"
            )
            snapshot = json.loads(snapshot_path.read_text())
            assert "developer/sandbox" in snapshot
            for tool, expected_permit in snapshot["developer/sandbox"].items():
                actual = check_tool_permitted("developer/sandbox", tool)
                assert actual == expected_permit, (
                    f"developer/sandbox permit drift: tool={tool!r} snapshot={expected_permit} live={actual}"
                )
    ```
  </action>
  <acceptance_criteria>
    - `tests/test_per_family_isolation.py` exists.
    - `tests/snapshots/h4b_developer_sandbox_permits.json` exists and parses as JSON with top-level key `developer/sandbox`.
    - `grep -c "class TestOperatorCannotInvokeDeveloperTools" tests/test_per_family_isolation.py` returns 1.
    - `grep -c "class TestDeveloperCannotInvokeOperatorOnlyTools" tests/test_per_family_isolation.py` returns 1.
    - `grep -c "class TestDspApplyFailsClosedUnderDeveloper" tests/test_per_family_isolation.py` returns 1.
    - `grep -c "class TestCrossFamilyLoadIsolation" tests/test_per_family_isolation.py` returns 1.
    - `pytest tests/test_per_family_isolation.py -v` exits 0 — all tests pass.
    - `pytest tests/test_profile_gating.py tests/test_per_family_isolation.py tests/test_canon_overlay.py -v` exits 0 — full H.4a+H.4b family-related suite passes.
  </acceptance_criteria>
</task>

<task type="auto">
  <name>Task 6: Run full regression, confirm H.4a snapshot unchanged, write H.4b-01-SUMMARY.md</name>
  <files>
    - .planning/phases/H.4b-developer-sandbox-profile-fsi-dev-canon/H.4b-01-SUMMARY.md
  </files>
  <read_first>
    - tools/apply_engine.py (post-Task 2)
    - canon/stack.py (post-Task 4)
    - tests/snapshots/h4a_operator_permits.json (MUST be unchanged after H.4b)
    - tests/snapshots/h4b_developer_sandbox_permits.json (new baseline)
  </read_first>
  <action>
    1. Run `git diff HEAD -- tests/snapshots/h4a_operator_permits.json` — must be empty (snapshot unchanged).
    2. Run `pytest tests/test_profile_gating.py tests/test_per_family_isolation.py tests/test_canon_overlay.py -v` — must exit 0.
    3. Run `pytest tests/ -v --tb=short` — must exit 0 OR have only the same 2 pre-existing failures documented in H.4a-01-SUMMARY (test_check_canon_parity.py, test_manifest.py — fsi-dsp version drift).
    4. Run `pytest tests/golden/ -v` — must exit 0 (no spillover into golden harnesses).

    Write `.planning/phases/H.4b-developer-sandbox-profile-fsi-dev-canon/H.4b-01-SUMMARY.md`:
    ```markdown
    # H.4b-01 Summary

    **Plan:** H.4b-01 — Developer-sandbox profile + FSI dev canon overlay
    **Status:** Complete
    **Date:** 2026-05-17

    ## What landed
    - `tools/profiles/developer/sandbox.json` — first developer-family profile (15 tool_overrides, 4 primary_tooling skills, /dsp:apply blocked, canon_layer pointer)
    - `tools/apply_engine.py` extended: VALID_PROFILES includes developer/sandbox; load_profile() resolves slash-paths; new check_skill_permitted()
    - `canon/industry/fsi/developer-sandbox/overrides.yaml` — bifurcated dev canon (OAUTHBEARER, at_least_once, JSON, BACKWARD, RF=1, dev topic naming)
    - `canon/industry/fsi/developer-sandbox/adrs/README.md` — pre-ADR stub registry with promotion path
    - `canon/stack.py` extended: `_layer_order_for(family, canon_layer)` helper + resolve_stack() family/canon_layer kwargs (backward-compatible default)
    - `tests/test_per_family_isolation.py` — 5 test classes covering negative-space isolation + snapshot regression
    - `tests/snapshots/h4b_developer_sandbox_permits.json` — 54-tool permit baseline for developer/sandbox

    ## Requirements
    - DEVPROF-01: ✓ Fully satisfied (developer/sandbox profile with documented shape + JSON Schema validation via H.4a's _normalize_and_validate_profile)
    - DEVCAN-01: ✓ Fully satisfied (canon/industry/fsi/developer-sandbox/ overlay with every CLAUDE.md Canon dimension at explicit dev-tier values)
    - DEVPROF-02: ⚪ Partially satisfied (negative-space tests prove operator/developer isolation + /dsp:apply fail-closed under developer; customer-fork differential gating requires H.4c)
    - PROFAM-02: ✓ Fully satisfied (parametrized per-profile-family negative-space matrix in tests/test_per_family_isolation.py)

    ## ROADMAP success criteria (H.4b)
    1. ✓ tools/profiles/developer/sandbox.json exists with documented shape + passes JSON Schema validation (H.4a's _normalize_and_validate_profile invariants)
    2. ✓ canon/industry/fsi/developer-sandbox/ overlay contains every Canon dimension with explicit dev-tier values
    3. ✓ Per-profile-family negative-space test suite passes: operator profiles cannot invoke developer tool_overrides; developer profiles cannot invoke operator-tier-only tools; /dsp:apply fails closed under developer with explicit error

    ## Regression results
    - `pytest tests/test_profile_gating.py`: [N]/[N] PASS
    - `pytest tests/test_per_family_isolation.py`: [N]/[N] PASS (new)
    - `pytest tests/test_canon_overlay.py`: [N]/[N] PASS (back-compat)
    - `pytest tests/`: [N]/[N+2] PASS (2 pre-existing failures documented in H.4a-01-SUMMARY persist)
    - `pytest tests/golden/`: [N]/[N] PASS
    - `git diff HEAD -- tests/snapshots/h4a_operator_permits.json`: empty (snapshot byte-identical)

    ## Deferred to H.4c
    - acme-bank developer overlay (canon/customer/acme-bank/profiles/developer/sandbox.json)
    - Differential gating proof that customer-fork produces ≥1 different gating decision vs base FSI dev canon
    - ACTG-04-style assertion shape adapted for the developer family

    ## Self-Check: PASSED
    ```
  </action>
  <acceptance_criteria>
    - `.planning/phases/H.4b-developer-sandbox-profile-fsi-dev-canon/H.4b-01-SUMMARY.md` exists with `## Self-Check: PASSED`.
    - SUMMARY contains literal strings `DEVPROF-01`, `DEVPROF-02`, `DEVCAN-01`, `PROFAM-02`, `OAUTHBEARER`, `at_least_once`.
    - `git diff HEAD -- tests/snapshots/h4a_operator_permits.json` returns empty (H.4a snapshot unchanged).
    - `pytest tests/` exit code 0 (or same pre-existing 2 failures as H.4a — no NEW failures).
    - `git status` shows only the 7 plan-listed files + SUMMARY + STATE/ROADMAP/REQUIREMENTS metadata.
  </acceptance_criteria>
</task>

</tasks>

<verification>
After all tasks complete:

1. **Developer profile loads** — `python3 -c "from tools.apply_engine import load_profile; p = load_profile('developer/sandbox'); assert p['family']=='developer'"` exits 0.
2. **Developer-branch dispatch works** — `python3 -c "from tools.apply_engine import check_tool_permitted; assert check_tool_permitted('developer/sandbox','produce-message') and not check_tool_permitted('developer/sandbox','list-environments')"` exits 0.
3. **Skill blocklist works** — `python3 -c "from tools.apply_engine import check_skill_permitted; assert not check_skill_permitted('developer/sandbox','dsp-apply') and check_skill_permitted('engineer','dsp-apply')"` exits 0.
4. **Canon stack composes dev overlay** — `python3 -c "from canon.stack import resolve_stack; cfg, h = resolve_stack(family='developer'); assert cfg['security']['auth_mechanism']=='OAUTHBEARER'"` exits 0.
5. **H.4a operator snapshot byte-identical** — `git diff HEAD -- tests/snapshots/h4a_operator_permits.json` is empty.
6. **All targeted tests pass** — `pytest tests/test_profile_gating.py tests/test_per_family_isolation.py tests/test_canon_overlay.py -v` exits 0.
7. **No spillover** — `git status` shows only 7 plan-listed files + .planning/ artifacts; nothing in `canon/customer/`, `.github/`, or `tests/golden/`.

All 7 must pass before phase complete. Failure → gap closure.
</verification>
