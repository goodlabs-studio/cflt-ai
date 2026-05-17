# Phase G.2c: Tool-classification rename — Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `G.2c-CONTEXT.md` — this log preserves the alternatives considered.

**Date:** 2026-05-15
**Phase:** G.2c-tool-classification-rename
**Areas discussed:** Source of truth, Migration approach, CI drift detection, Version pin policy, Tier assignment policy, CI direction

---

## Source of truth for tool names

| Option | Description | Selected |
|--------|-------------|----------|
| Parse `~/.npm/_npx` `tool-name.js` (Recommended) | Pin a specific `@confluentinc/mcp-confluent` version in a generator script; npm install it; parse the `dist/confluent/tools/tool-name.js` enum. Deterministic, no live server required, reproducible in CI. We already have 1.3.0 installed locally. | ✓ |
| Runtime MCP `tools/list` probe | Spin up the actual mcp-confluent server via stdio in CI and call `tools/list`. Most authoritative but requires CC credentials in CI (failure-prone) and is slower. | |
| Hand-maintained pinned snapshot | Commit a `tool-name.js` copy under `canon/vendor/mcp-confluent/<version>/`, bump manually when upgrading. No automation, but zero dependency on npm cache. | |

**User's choice:** Parse `~/.npm/_npx` `tool-name.js`
**Notes:** Discovery during context-gathering: ROADMAP cited `/tmp/mcp-c/...` but that path is empty directories. Live registry was found at `~/.npm/_npx/d7a7dd40dd5800de/node_modules/@confluentinc/mcp-confluent/dist/...` and confirmed 50 tools at version 1.3.0 (roadmap had said 1.2.x).

---

## Migration approach

| Option | Description | Selected |
|--------|-------------|----------|
| Big-bang: delete fictional + rename real (Recommended) | Single PR: regenerate `tool_classification.json` against live 1.3.0 (50 real tools), delete every fictional entry, regenerate parametrized tests. No bilingual compat layer. Fits the no-prod-callers reality. | ✓ |
| Aliases for snake→kebab where mapping exists | Keep snake_case as deprecated aliases that resolve to kebab equivalents. Fictional entries still deleted. Lower coverage gain — nothing real calls the old names. | |
| Two-pass: rename now, schedule fictional cleanup later | Rename only the entries that have real kebab equivalents in 1.3.0; leave the fictional ones untouched (they continue to fail-closed by being unclassified). Defers half the work. | |

**User's choice:** Big-bang
**Notes:** Major in-discussion finding: ~half the current `tool_classification.json` entries are fictional (hallucinated from training data — names like `confluent_kafka_acl_create`, `confluent_peering_create`, RBAC/SA/API-key/networking ops don't exist in 1.3.0). Big-bang therefore deletes ~half the table outright, not just renames it.

---

## CI drift detection

| Option | Description | Selected |
|--------|-------------|----------|
| Version-pin + extract-and-diff (Recommended) | `tool_classification.json` has `mcp_confluent_version: "1.3.0"`. CI runs a small Python/Node script that installs that exact version, extracts `ToolName` enum, and diffs against classification keys. Fails if either side has entries the other doesn't. | ✓ |
| Committed `expected-tools.txt` | Generator script writes `expected_tool_names.txt` to the repo; CI re-runs generator and diffs. Adds a generated file to track but no install needed in CI run. | |
| Runtime probe of an mcp-confluent server in CI | Spin up mcp-confluent in CI, call `tools/list`, diff. Requires CC creds or a no-auth probe mode — brittle. | |

**User's choice:** Version-pin + extract-and-diff
**Notes:** Same generator script (D-01) is reused in `--check` mode by the CI workflow. One script, two callers.

---

## Version pin policy

| Option | Description | Selected |
|--------|-------------|----------|
| Exact patch, manual bumps (Recommended) | Pin to `1.3.0` exactly in `tool_classification.json` metadata + generator script. Bumping the version is an explicit PR that includes regenerating the classification table. FSI canon principle: deterministic, reproducible, every change auditable. | ✓ |
| Minor (`^1.3`) — accept patch updates | Allow patch bumps. Risk: a patch could add/rename tools and silently invalidate classification. CI catches this but generates noise. | |
| Track upstream main / latest | Always pull latest published. Maximum churn, useful only if Confluent ships frequent tool additions we want immediately. | |

**User's choice:** Exact patch, manual bumps
**Notes:** Aligns with FSI vendor-backing rule (saved feedback): every classification change is an auditable PR.

---

## Tier assignment for newly-real tools

| Option | Description | Selected |
|--------|-------------|----------|
| Verb-prefix auto-rule (Recommended) | `list-*` / `read-*` / `get-*` / `search-*` / `detect-*` / `check-*` / `describe-*` → read-only. `create-*` / `update-*` / `alter-*` / `add-*` → engineer. `delete-*` / `remove-*` → break-glass. Documented as a rule in `tool_classification.json`. `produce-message` / `consume-messages` → break-glass (data-plane writes/reads in prod). | ✓ |
| Conservative: everything defaults to break-glass | All new tools land in break-glass until explicitly downgraded. Maximum safety; high friction — every new tool requires a follow-up PR to be useful. | |
| Manual one-by-one classification | Reviewer assigns every new tool individually with rationale. Most accurate; slowest; doesn't scale as the registry grows. | |

**User's choice:** Verb-prefix auto-rule
**Notes:** Rule is a regeneration aid only; runtime fallback stays `unclassified_policy: "deny"`. Generator applies the rule when emitting JSON; each entry remains explicit in the committed file.

---

## CI direction

| Option | Description | Selected |
|--------|-------------|----------|
| Bidirectional (Recommended) | Fail if registry has tools not in classification (new tools need explicit tier) AND if classification has keys not in registry (stale entries from removed tools). Both states are bugs. | ✓ |
| Registry → classification only | Fail when registry adds tools we haven't classified. Permits classification to keep keys for removed tools (orphans become benign — they just never match anything). | |
| Classification → registry only | Fail when classification references nonexistent tools. Permits registry growth without forcing tier decisions — new tools fail-closed via `unclassified_policy`. | |

**User's choice:** Bidirectional
**Notes:** This is what catches the *current* state — half the classification has keys not in the registry. The bidirectional gate would have prevented this drift in the first place.

---

## Claude's Discretion

- Exact subprocess plumbing of the generator (`npm install` into a temp prefix vs `pacote.extract`).
- Regex form for parsing `ToolName["X"] = "kebab-case"`.
- CI workflow runner image and Node version.
- Whether to emit `tool_classification.json` grouped by service area (kafka / flink / connect / tableflow / billing / metrics) or flat alphabetical — pick whichever produces the cleanest diff.

## Deferred Ideas

- Customer-overlay classification tables — add a customer parameter to `load_tool_classification()`. Out of scope until an FSI engagement asks.
- Fourth tier between read-only and engineer for data-plane reads (`consume-messages` currently break-glass). Revisit if break-glass proves too heavy.
- Classification audit log — wiki-incident-style record of every denial. Belongs in observability phase.
- Sibling classification for non-Confluent MCPs (Terraform MCP, future MCPs). Architectural; defer until a second MCP needs gating.
