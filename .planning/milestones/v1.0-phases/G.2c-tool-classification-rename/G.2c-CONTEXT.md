# Phase G.2c: Tool-classification rename — Context

**Gathered:** 2026-05-15
**Status:** Ready for planning

<domain>
## Phase Boundary

Align `tools/profiles/tool_classification.json` keys with the live `@confluentinc/mcp-confluent` tool registry (v1.3.0). Delete fictional entries inherited from training data, rename surviving entries from snake_case (`confluent_kafka_topic_list`) to kebab-case (`list-topics`), assign tiers to newly-real tools that have no snake_case predecessor, and add a CI gate that fails PRs whenever classification keys diverge from the live registry. Profile JSON files (`read-only.json`, `engineer.json`, `break-glass.json`), customer profile overlays, and `apply_engine.check_tool_permitted()` semantics are out of scope — they reference `allowed_operations` like `module/topic`, not tool names, and are unaffected by the rename.

Recommended starting sub-phase for Phase G.2 because it is mechanical, fully testable from local fixtures, and unblocks G.2a (the mcp-confluent tool-call executor) by guaranteeing every classification lookup hits the real registry.

</domain>

<decisions>
## Implementation Decisions

### Source of truth for tool names
- **D-01:** Canonical source is `dist/confluent/tools/tool-name.js` from a **pinned** `@confluentinc/mcp-confluent` package. A generator script (Python, lives in `tools/`) installs the pinned version into a temp `npm prefix`, parses the `ToolName` enum (regex over `ToolName["X"] = "kebab-case-name"` lines), and writes the keys into `tool_classification.json`. No live MCP server, no Confluent Cloud credentials, no `/tmp/mcp-c` reliance. Deterministic and reproducible on any clean machine.
- **D-02:** Pin lives **inside** `tool_classification.json` as a top-level field (e.g., `"mcp_confluent_version": "1.3.0"`) so the file is self-describing. The generator script reads that field, not a flag.

### Migration approach
- **D-03:** Big-bang replacement in a single PR. Regenerate `tool_classification.json` against live 1.3.0 (50 tools today). Delete every snake_case entry that has no real counterpart in 1.3.0 (the fictional half of the current table — see Specific Ideas for the inventory). No bilingual compatibility, no aliases. There are no production callers; the snake_case names never matched a real tool, so removing them changes no behavior — they were always fail-closed.
- **D-04:** Regenerate `tests/test_profile_gating.py` parametrized matrix against the new keys in the same PR. Tests that hard-coded snake_case tool names get rewritten to kebab-case. This is mechanical for the planner.

### Tier assignment for newly-real tools
- **D-05:** Verb-prefix auto-rule, documented as a comment block at the top of `tool_classification.json`:
  - `list-*` / `read-*` / `get-*` / `search-*` / `detect-*` / `check-*` / `describe-*` / `query-*` → **read-only**
  - `create-*` / `update-*` / `alter-*` / `add-*` → **engineer**
  - `delete-*` / `remove-*` → **break-glass**
  - **Exceptions (explicit override of the verb rule):**
    - `produce-message` → **break-glass** (data-plane write; production guard)
    - `consume-messages` → **break-glass** (data-plane read may expose PII in FSI)
- **D-06:** The verb-prefix rule is a **regeneration aid**, not a runtime fallback. `unclassified_policy: "deny"` stays. The generator applies the rule when writing the file; once written, every entry is explicit. New tools added by a future mcp-confluent release will fail CI (per D-08) until a human applies the rule (or overrides it) in the PR that bumps the version.

### CI drift detection
- **D-07:** New GitHub Actions workflow at `.github/workflows/tool-classification-drift.yml`. Runs on PR and on push to `main`. Reuses the same generator script in a `--check` mode: install pinned version, extract enum, diff against committed keys, fail non-zero on any divergence.
- **D-08:** **Bidirectional** drift check. Fails when:
  - The live registry has tools not in classification (forces explicit tier decision before merge), OR
  - Classification has keys not in the live registry (catches stale entries from upstream removals).
  Both states are bugs and must block PRs.

### Version pin policy
- **D-09:** Pin to exact patch (`1.3.0` today). Version bumps are explicit PRs that include the regenerated `tool_classification.json`, regenerated test parametrization, and any tier-policy overrides for new tools. No floating `^` ranges. Aligns with FSI canon principle: deterministic, reproducible, every classification change reviewable.

### Locked / out of scope (carrying forward from Phase 3c)
- `unclassified_policy: "deny"` — fail-closed for unknown tools. Not changing.
- Customer profile overlays (`canon/customer/<name>/profiles/*.json`) override **profiles**, not classification — `apply_engine.load_tool_classification()` has no customer parameter. Classification is base-only. Customer overlays are unaffected by this phase.
- `check_tool_permitted()` algorithm — exact-name match + tier hierarchy. Unchanged. Only the keys flowing in change.

### Claude's Discretion
- Exact shell/Python plumbing of the generator script (subprocess vs npm pacote API; tmp dir cleanup; error messages).
- Regex form for parsing `ToolName["X"] = "kebab"` (multiple workable shapes).
- CI workflow runner image and Node version.
- Whether to emit a sorted/grouped `tool_classification.json` (e.g., grouped by service area: kafka / flink / connect / tableflow / billing / metrics) or flat alphabetical. Pick whichever produces the cleanest diff in the next bump PR.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing classification + enforcement
- `tools/profiles/tool_classification.json` — current 50+ snake_case keys (half fictional); shape downstream agents must preserve (`version`, `tools`, `unclassified_policy`).
- `tools/apply_engine.py` §`load_tool_classification` (lines 46–55) and §`check_tool_permitted` (lines 58–81) — runtime callers of the classification keys. Verify they still work after rename without other code changes.
- `tools/profiles/read-only.json`, `tools/profiles/engineer.json`, `tools/profiles/break-glass.json` — profile files that reference `allowed_operations`, NOT tool names. Out of scope for this rename. Read once to confirm no tool-name strings hide inside.
- `tests/test_profile_gating.py` — parametrized matrix over current keys. Will need regeneration in same PR.

### Phase 3c canon (the rules this phase preserves)
- `.planning/phases/03C-act-rail-profile-gating/03C-CONTEXT.md` — Phase 3c decisions on profile gating, tier hierarchy, unclassified_policy.
- `.planning/REQUIREMENTS.md` §"Act Rail (Profile Gating)" — ACTG-01 (every tool classified by name, not regex), ACTG-02 (negative-space suite), ACTG-03 (break-glass two-step), ACTG-04 (customer fork). Rename must not violate any of these.

### Live registry
- `~/.npm/_npx/d7a7dd40dd5800de/node_modules/@confluentinc/mcp-confluent/dist/confluent/tools/tool-name.js` — confirmed canonical at time of context gathering. Note: the npx hash directory is per-machine; the generator script must npm-install into its own controlled prefix, not read this path directly.
- `@confluentinc/mcp-confluent` on npm — pin field will read `1.3.0`. Bumping = new PR.

### Roadmap entry
- `.planning/ROADMAP.md` §"Phase G.2: Composite + GitOps + tool-call execution" → G.2c bullet. Note: roadmap narrative says "1.2.x" and "30-min hygiene fix" — both are outdated. Actual published version is 1.3.0 and the work is rename + delete-fictional + new-CI, larger than 30 min but still well-scoped.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `tools/apply_engine.py` — `load_tool_classification()` caches a single read; the cache reset isn't exposed but tests use `_tool_classification_cache = None` directly. After the rename, no code changes needed in this file — keys flow through opaquely.
- `tests/test_profile_gating.py` already parametrizes over `load_tool_classification()["tools"]`, so once the JSON is regenerated, the test matrix rebuilds itself. The hard-coded fixture cases (e.g., the assertions like `assert check_tool_permitted("engineer", "confluent_kafka_topic_create")`) are what need rewriting.

### Established Patterns
- `tools/` directory holds Python utilities (`apply_engine.py`, `wiki-lint.py`, `check-canon-parity.py`). New generator script fits here as `tools/regenerate_tool_classification.py` or `tools/sync_tool_classification.py`.
- CI workflows in `.github/workflows/` already include canon-parity (`ci-canon-parity.yml` style). New drift workflow follows the same shape.
- `pyproject.toml` / `flox.toml` (verify): generator depends on `npm` being present in CI runner, which the existing CI provides via Node setup actions.

### Integration Points
- No runtime integration changes. The rename is data-only.
- CI integration: new workflow file alongside existing canon-parity workflows.
- Documentation: a comment block at the top of `tool_classification.json` documenting the verb-prefix rule and the pinned version is the only doc surface.

</code_context>

<specifics>
## Specific Ideas

**Live 1.3.0 registry (50 tools, kebab-case) — the target set:**

The full list extracted from `dist/confluent/tools/tool-name.js` (1.3.0):

- **Topics & data plane:** `list-topics`, `create-topics`, `delete-topics`, `produce-message`, `consume-messages`, `alter-topic-config`, `get-topic-config`
- **Flink (statements):** `list-flink-statements`, `create-flink-statement`, `read-flink-statement`, `delete-flink-statements`, `get-flink-statement-exceptions`, `check-flink-statement-health`, `detect-flink-statement-issues`, `get-flink-statement-profile`
- **Flink (catalog):** `list-flink-catalogs`, `list-flink-databases`, `list-flink-tables`, `describe-flink-table`, `get-flink-table-info`
- **Connectors:** `list-connectors`, `read-connector`, `create-connector`, `delete-connector`
- **Tags & search:** `search-topics-by-tag`, `search-topics-by-name`, `create-topic-tags`, `delete-tag`, `remove-tag-from-entity`, `add-tags-to-topic`, `list-tags`
- **Clusters & environments:** `list-clusters`, `list-environments`, `read-environment`
- **Schema Registry:** `list-schemas`, `delete-schema`
- **Tableflow:** `create-tableflow-topic`, `list-tableflow-regions`, `list-tableflow-topics`, `read-tableflow-topic`, `update-tableflow-topic`, `delete-tableflow-topic`, `create-tableflow-catalog-integration`, `list-tableflow-catalog-integrations`, `read-tableflow-catalog-integration`, `update-tableflow-catalog-integration`, `delete-tableflow-catalog-integration`
- **Billing & metrics:** `list-billing-costs`, `query-metrics`, `list-available-metrics`

**Fictional snake_case entries to DELETE (no analog in 1.3.0):**

ACL ops (`confluent_kafka_acl_*`), peering (`confluent_peering_*`), transit gateway (`confluent_transit_gateway_attachment_*`), private link (`confluent_private_link_attachment_*`), schema exporters (`confluent_schema_exporter_*`), RBAC bindings (`confluent_rbac_role_binding_*`), service accounts (`confluent_service_account_*`), API keys (`confluent_api_key_*`), consumer groups (`confluent_kafka_consumer_group_*`), mirror topics (`confluent_kafka_mirror_topic_*`), cluster links (`confluent_cluster_link_*`), cluster CRUD (`confluent_kafka_cluster_create/update/delete`), environment CRUD (`confluent_environment_create/delete`), networks (`confluent_network_*`), Flink compute pools (`confluent_flink_compute_pool_*`), Flink statement update (`confluent_flink_statement_update`), schema registry create/compat (`confluent_schema_registry_*_create/update`), connector update/pause/resume (`confluent_connector_update/pause/resume`).

**Tier-assignment overrides (applied by the verb-prefix rule generator):**

- `produce-message` → break-glass (override of "no verb match → ?"; data-plane write)
- `consume-messages` → break-glass (override; data-plane read; FSI PII consideration)

**Anti-references / non-goals:**

- Don't introduce a Pydantic / JSON Schema for `tool_classification.json` — the file shape is stable, adding schema validation is yak-shaving for this phase.
- Don't extend `check_tool_permitted()` to support patterns/regex — ACTG-01 requires by-name, not regex.
- Don't change `unclassified_policy` to anything other than `"deny"`.

</specifics>

<deferred>
## Deferred Ideas

- **Customer-overlay classification tables** — Today, customer overlays only override profiles. If a customer wanted a different classification (e.g., promote a tool from break-glass to engineer for their org), they'd need `check_tool_permitted(..., customer=...)` to consult an overlay classification file. Out of scope here; surface as 999.x in backlog if a real engagement requests it.
- **Tier-hierarchy expansion** — Adding a fourth tier (e.g., "read-write-data-plane" between read-only and engineer to scope `consume-messages` without the full break-glass workflow). Out of scope; revisit if real users find break-glass too heavy for routine consume calls.
- **Classification audit log** — Recording every `check_tool_permitted()` denial to a wiki-incident-style artifact so customers can see what was attempted vs allowed. Belongs in an observability phase, not here.
- **Sibling profiles for non-Confluent MCPs** — If we add Terraform MCP or other MCP servers to the act rail, each needs its own classification table. Architectural decision deferred until a second MCP shows up in scope.

</deferred>

---

*Phase: G.2c-tool-classification-rename*
*Context gathered: 2026-05-15*
