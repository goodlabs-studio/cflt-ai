# Phase H.4b: Developer-sandbox profile + FSI dev canon overlay — Context

**Gathered:** 2026-05-17
**Status:** Ready for planning
**Mode:** Auto (--auto) — defaults selected from H.4a engine contract, existing canon stack shape, CLAUDE.md FSI overrides

<domain>
## Phase Boundary

Author the first real developer-family profile and its corresponding FSI dev canon overlay so the H.4a family branching now has a concrete production-usable consumer. Specifically:

1. `tools/profiles/developer/sandbox.json` — first developer-family profile with the contract H.4a's engine expects (family=developer, tool_overrides map, skill_blocklist list, no allowed_operations).
2. `canon/industry/fsi/developer-sandbox/overrides.yaml` — bifurcated FSI dev canon overlay: dev-tier defaults distinct from the production FSI overlay (OAUTHBEARER over mTLS, at_least_once over exactly_once, JSON Schema OK, BACKWARD compatibility minimum, RF=1 OK for sandbox, dev topic naming pattern).
3. Engine plumbing for the developer profile path: `tools/profiles/developer/sandbox.json` must load via `load_profile("sandbox", family="developer")` OR via `load_profile("developer/sandbox")` — pick the cleanest path that keeps v1.0 callers byte-compatible.
4. `canon/stack.py` extended to resolve `industry/fsi/developer-sandbox/` as an alternative industry-layer when the active profile's family is developer.
5. Per-profile-family negative-space test matrix: parametrized tests assert (a) operator profiles cannot invoke developer-family tools, (b) developer profiles cannot invoke operator-tier-only tools (e.g., `delete-environment`, `create-cluster`), (c) `/dsp:apply` fails closed under any developer profile with an explicit error message referencing the family.

After H.4b: a developer running cflt-ai under `--profile developer/sandbox` (exact CLI shape TBD in PLAN) sees a working dev-tier environment — upstream confluent-agent-skills are available, data-plane sandbox ops (produce-message, consume-messages, create-topics on `*-sandbox` clusters) are permitted, `/dsp:apply` is blocked (sandbox isn't for prod operations), and the canon dimensions reflect dev-appropriate defaults.

**Out of scope:**
- acme-bank developer overlay (H.4c — proves customer-fork differential gating for the dev family)
- Activity-log family field emission (defer to first real dev-tier apply attempt — outside this scope since /dsp:apply is blocked anyway)
- `/dsp:scaffold` integration (H.3c — depends on this phase)
- environment_guard runtime enforcement beyond the soft pattern documented on the profile (advisory only; CI guard is future)
- New canon resolver family in stack.py beyond what's needed to load developer-sandbox overrides

</domain>

<decisions>
## Implementation Decisions

### Developer-sandbox profile shape
- **D-01:** `tools/profiles/developer/sandbox.json` with full shape:
  ```json
  {
    "name": "developer/sandbox",
    "description": "Developer-tier sandbox profile: upstream skills + data-plane ops on *-sandbox clusters; /dsp:apply blocked.",
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
  This includes the full set of dev-tier tools (data-plane + read-only describe) plus the explicit skill blocklist for `/dsp:apply`. `canon_layer` field tells `canon/stack.py` which industry overlay to apply.
- **D-02:** Path on disk is `tools/profiles/developer/sandbox.json` (sub-directory `developer/`). The profile name in JSON is `"developer/sandbox"` to make the family origin obvious in any callsite that prints the name (e.g., activity log). `load_profile("developer/sandbox")` resolves the slash to a path separator.
- **D-03:** `VALID_PROFILES` constant in `tools/apply_engine.py` is extended to include `"developer/sandbox"`. The constant is now a set of all known profile names (operator + developer). This stays fail-closed: unknown names still raise ValueError immediately.

### Engine integration
- **D-04:** `load_profile()` path resolution: if `profile_name` contains a `/`, split into `(family_dir, base_name)`, look for `PROFILES_DIR / family_dir / f"{base_name}.json"`. Otherwise look for `PROFILES_DIR / f"{profile_name}.json"` (existing behavior). This keeps every v1.0 caller unchanged.
- **D-05:** `skill_blocklist` enforcement: a new function `check_skill_permitted(profile_name, skill_name)` in `tools/apply_engine.py`. Returns False if `skill_name` is in the profile's `skill_blocklist`, True otherwise. Operator profiles return True for all skills (no blocklist field). Add a smoke-test that imports `check_skill_permitted` from places like `/dsp:apply` and any other cflt-ai skill entry-point — but in this phase, only wire it into one explicit smoke test that asserts `check_skill_permitted("developer/sandbox", "dsp-apply") == False`. Full /dsp:apply enforcement is out of scope (the existing CLI doesn't accept developer-family profiles today; H.4b's job is to land the gate so H.3c's `/dsp:scaffold` and future apply-callers can consult it).
- **D-06:** `canon/stack.py` gains a `family` parameter to `resolve_stack(family="operator")` defaulting to operator. When `family == "developer"`, the industry-layer path used is whatever `canon_layer` field the profile JSON specifies (defaulting to `industry/fsi/developer-sandbox` if absent). `LAYER_ORDER` becomes a property derived from family, not a module-level constant. v1.0 callers calling `resolve_stack()` without arguments get byte-identical operator-family behavior.

### FSI dev canon overlay shape
- **D-07:** `canon/industry/fsi/developer-sandbox/overrides.yaml` with bifurcated dev defaults:
  ```yaml
  # FSI developer-sandbox overrides — dev-tier values distinct from prod FSI overlay
  # Composes on top of canon/base/defaults.yaml via dict merge (replaces industry/fsi/overrides.yaml
  # in the developer-sandbox stack, NOT layered on top of it).
  # Override rule: each override references the rationale (FSI dev-tier ADR or H.4 phase note)

  security:
    auth_mechanism: "OAUTHBEARER"          # Dev-tier — easier than mTLS for fast iteration
    override_source: "H.4b CONTEXT D-07 — dev-tier auth"
    service_account_scope: "per_application"
    audit_log: false                       # Sandbox; no compliance log requirement

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

  producer:
    acks: "1"                              # Sandbox — performance over durability
    enable_idempotence: false              # Defer to user choice
    compression_type: "snappy"             # Faster for dev iteration

  consumer:
    group_design: "per_developer_instance" # OK in sandbox — easy reset
    auto_offset_reset: "latest"            # Common dev preference
    enable_auto_commit: true               # OK for non-critical dev paths

  environment_guard:
    pattern: "*-sandbox"
    enforcement: "advisory"
  ```
  Every override has an `override_source` field pointing to this CONTEXT.md decision (no ADR yet — promote to ADR if developer-sandbox sees significant operational use post-H.4c).
- **D-08:** Place an `adrs/README.md` stub under `canon/industry/fsi/developer-sandbox/adrs/` listing the override-source decisions and noting they'll be promoted to formal ADRs after one customer engagement validates the dev-tier values. This matches the existing `canon/industry/fsi/adrs/` pattern.

### Negative-space test matrix
- **D-09:** Add `tests/test_per_family_isolation.py` (new file) with parametrized tests:
  1. **Operator profile cannot invoke developer-family tool_overrides keys** — for each operator profile in {read-only, engineer, break-glass} × every tool listed ONLY in developer-sandbox's tool_overrides (i.e., tools that exist in dev overrides but are above operator's tier in the classification table), assert `check_tool_permitted(operator_profile, tool) == False` for at least 3 such tools.
  2. **Developer profile cannot invoke operator-tier-only tools** — for each tool in {`delete-environment`, `create-cluster`, `delete-cluster`, `delete-environment-by-id`} (operator-only tools NOT in developer-sandbox tool_overrides), assert `check_tool_permitted("developer/sandbox", tool) == False`. Pick at least 3 from the classification table.
  3. **`/dsp:apply` fails closed under developer profile** — `check_skill_permitted("developer/sandbox", "dsp-apply") == False`; `check_skill_permitted("engineer", "dsp-apply") == True` (operator profiles have no blocklist).
  4. **Cross-family load isolation** — `load_profile("developer/sandbox")["family"] == "developer"`; `load_profile("engineer")["family"] == "operator"`; both succeed without spillover.
- **D-10:** Extend H.4a's snapshot `tests/snapshots/h4a_operator_permits.json` is NOT modified by H.4b. H.4b adds a NEW snapshot `tests/snapshots/h4b_developer_sandbox_permits.json` with all (developer-sandbox × every-tool-in-classification) permit decisions. The two snapshots together prove byte-identical operator behavior and an explicit developer behavior contract.

### Folded Todos
None — `todo match-phase H.4b` returned zero matches.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project canon
- `CLAUDE.md` (project root) — Confluent Canon Always-On Rules. FSI dev overrides are deliberate departures from the FSI prod overlay; cite the specific Canon section each dev-tier override departs from in the YAML's override_source field.
- `.planning/REQUIREMENTS.md` §H.4 — DEVPROF-01 (developer/sandbox.json exists with documented shape), DEVCAN-01 (canon/industry/fsi/developer-sandbox/ overlay with every Canon dimension), DEVPROF-02 (negative-space tests prove fail-closed for /dsp:apply under developer-sandbox; full DEVPROF-02 customer-fork side requires H.4c).

### Prior-phase contexts
- `.planning/phases/H.4a-profile-family-schema-extension/H.4a-CONTEXT.md` — Family schema + engine branching contract. H.4b is the first real consumer of the developer branch.
- `.planning/phases/03C-act-rail-profile-gating/03C-CONTEXT.md` — Original tier cascade + per-profile negative-space test pattern. H.4b's new tests mirror this shape for the developer family.
- `.planning/phases/G.2c-tool-classification-rename/G.2c-CONTEXT.md` — Tool classification source-of-truth. H.4b's developer-sandbox tool_overrides only references tools that exist in the classification table.

### Existing code under modification
- `tools/apply_engine.py` — Extend VALID_PROFILES to include "developer/sandbox"; extend load_profile() to handle slash-separated path; add check_skill_permitted().
- `canon/stack.py` — Add `family` parameter to `resolve_stack()`; route industry-layer path based on family + profile's canon_layer field.
- `tools/profiles/developer/sandbox.json` (new) — First developer-family profile.
- `canon/industry/fsi/developer-sandbox/overrides.yaml` (new) — Bifurcated dev canon overlay.
- `canon/industry/fsi/developer-sandbox/adrs/README.md` (new) — Stub ADR registry.

### Existing tests as patterns
- `tests/test_profile_gating.py` — H.4a test patterns; H.4b's new test file follows the same parametrize + fixture conventions.
- `tests/test_canon_overlay.py` — Existing canon stack resolution tests; H.4b extends with a developer-family case.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **H.4a's `VALID_FAMILIES`, `_normalize_and_validate_profile()`, family-branched `check_tool_permitted()`** — H.4b just adds the first concrete developer-family profile + adds path resolution for slash-separated profile names + adds `check_skill_permitted()` helper.
- **`canon/stack.py` `_deep_merge` and `_load_layer`** — Reusable for the new developer-sandbox layer. The only new logic is selecting which industry-layer path to load based on family/canon_layer.
- **`canon/customer/acme-bank/profiles/engineer.json`** — Existing example of a customer-overlay profile with `customer_overrides` field. H.4b's developer/sandbox.json does NOT use this — it's a base developer profile, not a customer overlay. H.4c will demonstrate the customer-overlay path for developer family.
- **`tests/test_canon_overlay.py`** — Existing stack-resolution tests; H.4b adds a new test case for developer-family resolution.

### Established Patterns
- **Per-layer overrides.yaml** (or defaults.yaml for base) is the canonical format. New developer-sandbox folder follows this exactly.
- **`override_source` field** on every YAML key that overrides a base — H.4b's dev overlay uses H.4b CONTEXT references where ADRs don't exist yet.
- **Fail-closed everywhere** — unknown family raises ValueError (H.4a); unknown tool returns False; tools not in developer's tool_overrides return False; skills in blocklist return False.
- **JSON Schema validation in Python** (no jsonschema dep) — H.4a pattern; H.4b extends `_normalize_and_validate_profile()` if needed (probably not — the existing developer-family validation already covers H.4b's shape).
- **Snapshot regression pattern** — H.4a's `tests/snapshots/h4a_operator_permits.json`; H.4b adds `h4b_developer_sandbox_permits.json`.

### Integration Points
- **`tools/apply_engine.py`** — Three additions: extend VALID_PROFILES, path-resolve slash in load_profile, add check_skill_permitted.
- **`canon/stack.py`** — One addition: `family` parameter to resolve_stack with industry-layer routing.
- **`tools/profiles/developer/sandbox.json`** — New file.
- **`canon/industry/fsi/developer-sandbox/overrides.yaml`** — New file.
- **`canon/industry/fsi/developer-sandbox/adrs/README.md`** — New stub.
- **`tests/test_per_family_isolation.py`** — New test file (4 test groups).
- **`tests/snapshots/h4b_developer_sandbox_permits.json`** — New snapshot.

</code_context>

<specifics>
## Specific Ideas

- **`canon_layer` field on developer/sandbox.json**: explicit pointer that `canon/stack.py` consults to know which industry-layer overlay to apply. For developer/sandbox it's `industry/fsi/developer-sandbox`; for a future developer/restricted it'd be a different path. Keeps stack.py table-driven instead of hard-coding family→layer mappings.
- **Snapshot diff size**: developer-sandbox has 15 tools in tool_overrides; tool_classification.json has ~54 tools. The snapshot is 54 rows for developer-sandbox (15 permit, 39 deny). H.4a's operator snapshot is 3 profiles × 54 = 162 rows. Total snapshot footprint: ~216 rows, tiny.
- **Backward compat for `resolve_stack()`**: existing call sites in `tools/act_gates.py`, `tools/review-to-docx.py`, `tests/test_review_to_docx.py`, `tests/test_canon_overlay.py` call `resolve_stack()` with no args. H.4b's signature change is `resolve_stack(family="operator", canon_layer=None)` — defaults preserve byte-compat.
- **`environment_guard` advisory enforcement**: stored on profile JSON, not enforced in engine. H.4b only documents the pattern; future enforcement is a v2.x decision after observing developer-sandbox usage.

</specifics>

<deferred>
## Deferred Ideas

- **acme-bank developer overlay** — H.4c.
- **/dsp:scaffold integration with developer-sandbox** — H.3c (after H.4c lands).
- **environment_guard CI enforcement** — Future enhancement; H.4b documents the pattern advisory-only.
- **Promotion of developer-sandbox override_source decisions to formal ADRs** — After one customer engagement validates the dev-tier values, promote each CONTEXT-sourced override to an ADR under `canon/industry/fsi/developer-sandbox/adrs/`.
- **Activity-log family field** — Defer until first real apply-path consumer (currently /dsp:apply is blocked; not blocking for H.4b).
- **Additional developer-family profiles** (developer-restricted, developer-experimental) — Wait for use case.
- **Per-cluster scope on environment_guard** — Currently `*-sandbox` glob pattern; future could refine to specific cluster IDs from an inventory.

### Reviewed Todos (not folded)
None.

</deferred>

---

*Phase: H.4b-developer-sandbox-profile-fsi-dev-canon*
*Context gathered: 2026-05-17 (auto-mode)*
