# Phase H.3c: /dsp:scaffold wrapper — Context

**Gathered:** 2026-05-17
**Status:** Ready for planning
**Mode:** Auto (--auto) — defaults selected from H.3a/H.3b plugin install + pin, H.4a–c family work, existing /dsp:apply patterns

<domain>
## Phase Boundary

Land a new cflt-ai skill `/dsp:scaffold <artifact-type> <name>` that wraps the upstream `streaming-skills-plugin` skills (installed H.3a, pinned H.3b) so their output materializes as canon-compliant fsi-dsp artifacts. The wrapper:

1. **Triages** the request — picks the correct upstream skill from `streaming-skills-plugin` based on `<artifact-type>` (e.g., `producer` → `developing-kafka-python-client`; `cdc-pipeline` → `confluent-cloud-cdc-tableflow`).
2. **Resolves** the active canon stack (`canon/stack.py`) using the operator's profile family (operator/dev) per H.4a's family branching.
3. **Profile-gates** the scaffold operation:
   - `read-only` profile → blocked entirely (fail-closed, exit non-zero).
   - operator-family profiles (`engineer`, `break-glass`) → can scaffold prod-canon artifacts.
   - developer-family profiles (`developer/sandbox`) → can scaffold dev-canon artifacts; CANNOT scaffold prod-canon artifacts (cross-family refusal).
4. **Generates** the scaffolded output to `outputs/scaffolded/<artifact-type>-<name>-<timestamp>/` — a structured directory containing the upstream skill's emitted files (or a mock equivalent for non-interactive execution) PLUS a `manifest-entry.yaml` proposing the fsi-dsp MANIFEST.yaml capability entry to register PLUS a `provenance.json` recording operator/profile/canon-stack hash/timestamp/upstream-skill version.
5. **Activity-logs** the invocation via the existing `wiki/activity/YYYY-MM.md` monthly log per WIKI-02.

Out of scope for the H.3c phase boundary:
- Actually editing `raw/repos/fsi-dsp/MANIFEST.yaml` (that's a separate PR against fsi-dsp; H.3c PROPOSES the entry but does not auto-merge it).
- Interactive upstream-skill invocation (the upstream skills have HARD-GATE confirmation prompts; non-interactive execution mocks the skill's output with a stub generator that emits a representative file set — sufficient to prove end-to-end wiring).
- Auto-applying the scaffolded artifact (the scaffolded MANIFEST entry would be consumed by `/dsp:plan` + `/dsp:apply` in a follow-up PR cycle).
- All four upstream-skill triage paths (H.3c lands ONE artifact-type end-to-end: `producer` → `developing-kafka-python-client`. The other three (kafka-streams, schema-registry, cdc-tableflow) ship a triage stub with `## TODO: H.3c follow-up` markers — sufficient for the ROADMAP's "at least one artifact type" success criterion).
- New canon-stack capabilities (composition is unchanged).

</domain>

<decisions>
## Implementation Decisions

### Skill shape and CLI surface
- **D-01:** New skill file `.claude/commands/dsp-scaffold.md` (hyphenated to match `.claude/commands/dsp-apply.md` and `.claude/commands/dsp-plan.md` filename convention). Skill name in user-facing docs is `/dsp:scaffold`.
- **D-02:** CLI signature: `/dsp:scaffold <artifact-type> <name> [--profile <name>] [--overlay <customer>] [--operator <id>] [--prod] [--dry-run]`.
  - `<artifact-type>` (required, positional) — one of `{producer, consumer, kafka-streams-app, schema, cdc-pipeline}`.
  - `<name>` (required, positional) — kebab-case identifier; becomes part of the output directory name and MANIFEST entry name.
  - `--profile` (optional, default `read-only`) — same set as /dsp:apply, now also accepting `developer/sandbox`.
  - `--overlay` (optional) — customer overlay for canon stack; passed to `load_profile()` per ACTG-04 pattern.
  - `--operator` (optional, default `unknown`) — operator identifier for provenance footer.
  - `--prod` (optional flag) — explicit declaration that the scaffolded artifact targets a prod canon stack. Required when scaffolding production-grade artifacts; the absence of this flag defaults to dev/sandbox canon. Cross-family gate: `--prod` is REJECTED under developer-family profiles (developer/sandbox cannot scaffold a prod-canon artifact).
  - `--dry-run` (optional flag) — show what would be scaffolded without writing files.

### Triage table
- **D-03:** Triage from artifact-type to upstream skill is encoded as a Python dict constant `ARTIFACT_TYPE_TO_SKILL` in `tools/scaffold_engine.py`:
  ```python
  ARTIFACT_TYPE_TO_SKILL = {
      "producer": "streaming-skills-plugin:developing-kafka-python-client",
      "consumer": "streaming-skills-plugin:developing-kafka-python-client",
      "kafka-streams-app": "streaming-skills-plugin:kafka-streams-programming",
      "schema": "streaming-skills-plugin:kafka-schema-registry",
      "cdc-pipeline": "streaming-skills-plugin:confluent-cloud-cdc-tableflow",
  }
  ```
- **D-04:** H.3c lands ONE artifact-type with a real-feel scaffold output: `producer`. The other four artifact-types raise `NotImplementedError` from the dispatch with a clear error message + `## TODO: H.3c follow-up` doc reference. This matches the ROADMAP's "runs end-to-end for at least one artifact type" success criterion without inflating H.3c scope to ~1 week.

### Profile-gating semantics
- **D-05:** Three blocking gates:
  1. **Skill-blocklist gate** — `check_skill_permitted(profile_name, "dsp-scaffold", customer=overlay)` from H.4a/H.4b. Profiles that list `dsp-scaffold` in `skill_blocklist` are blocked. (Note: H.4b's developer/sandbox does NOT have dsp-scaffold in its blocklist — so developer-sandbox CAN scaffold. Acme-bank developer overlay (H.4c) also does not block dsp-scaffold. Read-only operator MUST be blocked here.)
  2. **Read-only operator gate** — explicit check: if profile is `read-only` (operator family, empty allowed_operations), refuse with the same error shape as /dsp:apply uses. This is belt-and-suspenders on top of the skill blocklist.
  3. **Cross-family canon gate** — if `--prod` flag is set AND profile family is `developer`, REFUSE with explicit error: `"Cross-family canon refused: developer-family profiles cannot scaffold prod-canon artifacts. Use --profile engineer or --profile break-glass for prod scaffolding, or omit --prod to scaffold under the developer-sandbox canon."`. This is the THE explicit negative-space test from ROADMAP success criterion #6.
  4. (Optional, post-H.3c) — Canon-family policy validation per artifact-type (some artifact types may be operator-only regardless of `--prod`). Defer.
- **D-06:** Add `dsp-scaffold` to the `skill_blocklist` of `read-only` profile JSON to make the blocklist intent visible. (Existing `read-only.json` has empty `allowed_operations`; we keep that AND add the explicit blocklist entry. Defense in depth.) Operator profiles (`engineer`, `break-glass`) get NO blocklist field (operator family has no blocklist convention; absence = permit all). Developer profiles (`developer/sandbox`, acme overlay) already have `skill_blocklist` lists — `dsp-scaffold` is NOT added (developer family CAN scaffold dev-canon artifacts).

### Scaffolded output directory shape
- **D-07:** Output directory: `outputs/scaffolded/<artifact-type>-<name>-<YYYYMMDD-HHMMSS>/` (ISO-like timestamp suffix for ordering + idempotency). Inside:
  - `manifest-entry.yaml` — proposed fsi-dsp MANIFEST capability entry (single YAML doc; copy into `raw/repos/fsi-dsp/MANIFEST.yaml capabilities[]` via a future PR against fsi-dsp).
  - `provenance.json` — operator, profile, profile family, canon-stack hash (from `canon/stack.py resolve_stack()`), upstream-skill, upstream-skill version (`streaming-skills-plugin@1.0.0`), upstream commit SHA (`91d1871e`), timestamp.
  - `scaffold/` — the actual scaffolded files. For the `producer` artifact-type, the stub generator writes a representative Python producer file (`producer.py`) + a sample `config.json` reflecting the resolved canon stack values (acks, compression, etc.). For other artifact-types, this directory contains only a `STUB.md` explaining what the upstream skill would produce.
  - `README.md` — top-level summary of what was scaffolded + how to use it + how to register in fsi-dsp.

### Provenance footer schema
- **D-08:** `provenance.json` has exactly these keys (mirrors the existing activity-log schema from v1.0 Phase 3b):
  ```json
  {
    "operator": "...",
    "profile": "...",
    "profile_family": "operator|developer",
    "overlay": "acme-bank|null",
    "artifact_type": "producer",
    "name": "...",
    "upstream_skill": "developing-kafka-python-client",
    "upstream_plugin": "streaming-skills-plugin",
    "upstream_plugin_version": "1.0.0",
    "upstream_commit_sha": "91d1871ef8c320be92bca955c8e42492a2778cb4",
    "canon_stack_hash": "...",  // from canon.stack.resolve_stack
    "canon_family": "operator-prod|developer-sandbox",
    "timestamp_utc": "2026-05-17T...",
    "scaffold_dir": "outputs/scaffolded/...",
    "phase": "H.3c"
  }
  ```

### MANIFEST entry shape (`manifest-entry.yaml`)
- **D-09:** Single YAML object mirroring existing fsi-dsp MANIFEST capability entries (e.g., `id: "module/topic", type: "ansible-role", name: ..., path: ..., description: ...`). Specifically:
  ```yaml
  # Proposed entry for raw/repos/fsi-dsp/MANIFEST.yaml capabilities[]
  # Generated by /dsp:scaffold @ <timestamp> — review before merging
  - id: "<artifact-type>/<name>"
    type: "scaffolded-producer"  # new type — distinct from terraform-module, ansible-role, etc.
    name: "<name>"
    path: "scaffolded/<artifact-type>/<name>/"
    description: "<auto-generated from upstream skill output>"
    provenance:
      generator: "cflt-ai /dsp:scaffold"
      generator_phase: "H.3c"
      upstream_skill: "<upstream-skill>"
      upstream_plugin_version: "streaming-skills-plugin@1.0.0"
      upstream_commit_sha: "91d1871e"
      canon_stack_hash: "<sha256-prefix>"
      canon_family: "operator-prod|developer-sandbox"
      scaffolded_at: "<UTC timestamp>"
      operator: "<id>"
      profile: "<name>"
  ```
  The `type: "scaffolded-producer"` is a NEW artifact type in the fsi-dsp ecosystem; the actual fsi-dsp PR that registers this entry would need to add a corresponding executor. For H.3c, the entry exists as a proposal only — registering it is a follow-on fsi-dsp PR.

### Activity log
- **D-10:** Append one entry to `wiki/activity/YYYY-MM.md` (current month — 2026-05) for every `/dsp:scaffold` invocation, mirroring the schema used by `/dsp:apply` per ACTA-04 (operator, profile, overlay, artifact, plan, gates, canon_stack, skill, confirmation_status, execution_result, duration_seconds). For `/dsp:scaffold`:
  - `skill: "/dsp:scaffold"`
  - `artifact: "<artifact-type>/<name>"`
  - `plan: "n/a (scaffold)"`
  - `gates: ["profile", "canon-family"]`
  - `confirmation_status: "n/a"` (scaffold is single-step; no confirmation modal)
  - `execution_result: "success" | "blocked-by-profile" | "blocked-by-canon-family" | "not-implemented"`
  - `duration_seconds: <measured>`

### Tests
- **D-11:** Unit tests in `tests/test_scaffold_engine.py`:
  1. **Happy path** — `scaffold("producer", "my-payments-producer", profile="developer/sandbox")` writes the output directory with all four files (manifest-entry, provenance, scaffold/producer.py, README); provenance has the correct canon_family=developer-sandbox.
  2. **Operator happy path** — `scaffold("producer", "my-prod-producer", profile="engineer", prod=True)` writes output directory with canon_family=operator-prod; manifest entry includes `--prod` provenance.
  3. **Read-only blocked** — `scaffold("producer", "x", profile="read-only")` raises a specific exception or exits non-zero; no files written; activity log entry with `execution_result="blocked-by-profile"`.
  4. **Cross-family canon refused** — `scaffold("producer", "x", profile="developer/sandbox", prod=True)` raises a specific exception or exits non-zero; no files written; activity log entry with `execution_result="blocked-by-canon-family"`.
  5. **Not-implemented artifact type** — `scaffold("cdc-pipeline", "x", profile="engineer")` raises NotImplementedError with the H.3c-follow-up marker; activity log entry with `execution_result="not-implemented"`.
  6. **Triage table coverage** — every key in `ARTIFACT_TYPE_TO_SKILL` resolves to a string starting with `streaming-skills-plugin:` (sanity check).
  7. **Provenance round-trip** — provenance.json contains all 14 D-08 keys after a successful scaffold.

### Folded Todos
None — `todo match-phase H.3c` returned zero matches.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project canon
- `CLAUDE.md` — Confluent Canon + FSI overlay (informs the resolved canon stack that scaffolded output must reflect).
- `.planning/REQUIREMENTS.md` §SCAF-01/02/03 — Scaffold skill exists, MANIFEST entry shape with provenance, profile-gated/activity-logged.

### Prior-phase contexts (patterns to integrate)
- `.planning/phases/H.3a-plugin-install-canon-overlay-wiki-article/H.3a-CONTEXT.md` — Plugin install + overlay article (informs the canon-overlay-as-structured-config logic).
- `.planning/phases/H.3b-version-pin-ci-drift-gate/H.3b-CONTEXT.md` — Pin file shape (provenance footer cites `streaming-skills-plugin@1.0.0` from this pin).
- `.planning/phases/H.4a-profile-family-schema-extension/H.4a-CONTEXT.md` — `check_skill_permitted` contract; family branching.
- `.planning/phases/H.4b-developer-sandbox-profile-fsi-dev-canon/H.4b-CONTEXT.md` — Developer-sandbox profile (first developer-family profile that can scaffold dev-canon artifacts).
- `.planning/phases/H.4c-acme-bank-developer-overlay/H.4c-CONTEXT.md` — acme-bank dev overlay (customer-fork example; scaffold under `--overlay acme-bank` produces the acme-tightened canon stack).
- `.planning/phases/03B-act-rail-apply/03B-CONTEXT.md` — `/dsp:apply` skill shape; activity-log schema; ACTA-04.

### Existing code under modification
- `.claude/commands/dsp-scaffold.md` (new) — skill spec.
- `tools/scaffold_engine.py` (new) — orchestration + triage + gating + output generation.
- `tools/profiles/read-only.json` — add `dsp-scaffold` to a new `skill_blocklist` field (D-06).
- `tests/test_scaffold_engine.py` (new) — unit tests.
- `outputs/scaffolded/` (new directory; gitignored or kept as part of audit trail — confirm gitignore conventions during execution).

### Existing infrastructure to leverage
- `tools/apply_engine.py` — `load_profile`, `check_tool_permitted`, `check_skill_permitted`, `check_profile_permits`.
- `canon/stack.py` — `resolve_stack(family, canon_layer)` (H.4b extension).
- `wiki/activity/YYYY-MM.md` — Monthly activity log; append one entry per invocation.
- `tools/vendor-sources.json` — Read `streaming-skills-plugin.commit` and `.version` for provenance footer.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`load_profile`, `check_skill_permitted`, `check_profile_permits`** — All from H.4a/H.4b. Three lines of glue in scaffold_engine.
- **`canon/stack.py resolve_stack(family=..., canon_layer=...)`** — H.4b's extension. Pass profile family directly; get a (config_dict, hash) tuple.
- **Existing `/dsp:apply` skill structure** (`.claude/commands/dsp-apply.md`) — Step 1 (parse args), Step 2 (load profile + fail-closed), Step 3..N (work). `/dsp:scaffold` follows the same numbered-step shape.
- **Activity-log emit pattern** from `tools/apply_engine.py` (or wherever ACTA-04 lives) — reuse the emit function with skill="/dsp:scaffold".

### Established Patterns
- **Fail-closed everywhere** — Unknown profile names raise; read-only blocks; cross-family scaffold attempts refuse; not-implemented artifact types raise.
- **Provenance footer schema** — operator + profile + canon_stack hash + timestamp; extended here with upstream skill + plugin version + commit SHA.
- **MANIFEST.yaml capability shape** — `id, type, name, path, description` minimum; `provenance` block extends.
- **CLI step-numbered structure** — `/dsp:apply` and `/dsp:plan` use numbered Step 1, Step 2, etc. headings; `/dsp:scaffold` mirrors.

### Integration Points
- **`.claude/commands/dsp-scaffold.md`** (new) — User-facing skill spec.
- **`tools/scaffold_engine.py`** (new) — Implementation.
- **`tools/profiles/read-only.json`** (extend) — Add explicit skill_blocklist with `dsp-scaffold`.
- **`tests/test_scaffold_engine.py`** (new) — 7 test cases.
- **`outputs/scaffolded/`** (new dir) — Output destination.
- **No changes** to fsi-dsp submodule, .github/workflows/, canon/, or any operator profile JSONs beyond read-only's blocklist field.

</code_context>

<specifics>
## Specific Ideas

- **Why `read-only` gets an explicit `skill_blocklist` field**: defense in depth. The `check_skill_permitted` function reads `skill_blocklist` and denies; the operator-tier path through `check_profile_permits` would ALSO deny because read-only has empty `allowed_operations`. Having both gates is intentional — the blocklist makes intent explicit at the profile level, the empty allowed_operations is the operator-tier-cascade enforcement.
- **`--prod` flag semantic**: It's the explicit declaration that the operator wants the PROD canon stack. Without it, scaffold defaults to the dev-sandbox canon. This makes the cross-family refusal test crisp: `developer/sandbox --prod` → refused with named gate.
- **Stub producer generator for the `producer` artifact-type**: Emits a ~30-line Python file using confluent-kafka-python with the resolved canon stack values inlined (acks, compression, schema_registry config). Plus a `config.json` with the resolved canon stack values. Plus a `README.md` with usage. This is enough to prove end-to-end wiring without invoking the upstream skill's interactive HARD-GATE flow.
- **`outputs/scaffolded/`** is added to `.gitignore` (audit trail lives in the activity log, not in the file tree — scaffolded outputs are operator artifacts, not committed). Confirm during execution if the project's `.gitignore` already has a pattern like `outputs/` that would cover this.

</specifics>

<deferred>
## Deferred Ideas

- **Real upstream-skill invocation** — Requires interactive Claude Code session (the upstream skills have HARD-GATE confirmation prompts). H.3c lands the stub generator for `producer`; future enhancement could spawn a sub-agent that interacts with the upstream skill.
- **Auto-PR-against-fsi-dsp** — `/dsp:scaffold` could open a PR adding the `manifest-entry.yaml` to fsi-dsp's MANIFEST.yaml. Manual copy for H.3c; PR automation later.
- **Triage for `consumer`, `kafka-streams-app`, `schema`, `cdc-pipeline`** — Stubbed in H.3c (`NotImplementedError`). Each follow-on phase lands one artifact-type at a time.
- **Eval cases for /dsp:scaffold** — H.2 harness can absorb (e.g., assert /dsp:scaffold asks for target environment before generating, asks for producer vs consumer, etc.). Not blocking for H.3c phase boundary.
- **`scaffolded-producer` executor** in fsi-dsp — H.3c emits MANIFEST entries with `type: "scaffolded-producer"`; fsi-dsp needs an executor for this type before `/dsp:apply` can consume scaffolded artifacts. Out of scope (fsi-dsp PR).
- **`developer-restricted` profile** that CAN scaffold operator-tier-only consumers — Premature.

### Reviewed Todos (not folded)
None.

</deferred>

---

*Phase: H.3c-dsp-scaffold-wrapper*
*Context gathered: 2026-05-17 (auto-mode)*
