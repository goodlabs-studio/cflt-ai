---
phase: H.1-wiki-ingest-agent-skills
plan: 01
subsystem: infra
tags: [vendor, agent-skills, confluent, wiki-ingest, pin-registry]

# Dependency graph
requires:
  - phase: G.2c-tool-classification-rename
    provides: pin-with-drift-gate pattern established (vendor SHA + CI drift detection) — same shape reused here as the routine /wiki:validate drift surface
provides:
  - Vendored snapshot of confluentinc/agent-skills @ 91d1871e (37 files, 484K) under raw/vendor/confluent-agent-skills/91d1871e/
  - tools/vendor-sources.json — new top-level pin registry, schema forward-compatible with H.3b streaming-skills-plugin
  - raw/_ingest.md ## Pending populated with 19 H.1 entries (10 parents + 9 trip-wires) referencing vendored paths
  - PROVENANCE.md inside vendor tree documenting upstream, SHA, license, re-ingest workflow
affects: [H.1-02, H.1-03, H.3b, H.2]

# Tech tracking
tech-stack:
  added: [vendored confluent-agent-skills@91d1871e]
  patterns:
    - "Vendor-at-pinned-SHA in raw/vendor/<repo>/<short-sha>/ — mirrors G.2c pin-with-drift pattern"
    - "tools/vendor-sources.json as single source of truth for vendor SHAs (D-09 drift surface)"
    - "kind field is free-form string (not enum) so future vendor kinds slot in without schema migration"

key-files:
  created:
    - tools/vendor-sources.json
    - raw/vendor/confluent-agent-skills/91d1871e/PROVENANCE.md
    - raw/vendor/confluent-agent-skills/91d1871e/skills/{4 skills}/SKILL.md
    - raw/vendor/confluent-agent-skills/91d1871e/skills/{4 skills}/references/{ref files}
  modified:
    - raw/_ingest.md

key-decisions:
  - "Trip-wire entries that cite evals.json use source_url: also-cite. (period not colon) to keep YAML well-formed; the path is preserved in the value, intent matches plan's also-cite citation strategy"
  - "Preserved extra non-scaffold reference files (rest-api.md, multi-event-guide.md, schema-generation-rules.md, *.py, *.json, *.yml, *.avsc) — plan's anti-references list only covered the 7 named scaffold templates, so non-listed extras stay; flagged for future plans to decide whether to prune"
  - "Used /usr/bin/find with bash -c for the SCAFFOLDS prune step because zsh's no-word-split default and the shell's bfs shim broke the variable expansion; semantics identical to plan's intended GNU find behaviour"

patterns-established:
  - "Vendor tree tracked in repo (not gitignored) — SHA bumps surface in `git log` as auditable changes"
  - "PROVENANCE.md template inside vendor tree captures re-ingest workflow alongside the source"
  - "Ingest queue entries reference vendored paths (not upstream URLs) so /wiki:ingest reads from disk"

requirements-completed: [WIKI-06]

# Metrics
duration: 4min
completed: 2026-05-16
---

# Phase H.1 Plan 01: Wiki ingest scaffolding (vendor + pin registry + queue) Summary

**Vendored confluent-agent-skills@91d1871e (37 files), authored tools/vendor-sources.json pin registry, and populated raw/_ingest.md with 19 ingest-queue entries (10 parents + 9 trip-wires) ready for H.1-02/H.1-03 to consume.**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-05-16T15:40:48Z
- **Completed:** 2026-05-16T15:44:37Z
- **Tasks:** 3
- **Files modified:** 39 (37 vendor + 1 tools/vendor-sources.json + 1 raw/_ingest.md)

## Accomplishments
- Cloned upstream `confluentinc/agent-skills` at pinned SHA `91d1871ef8c320be92bca955c8e42492a2778cb4` and vendored four skills (kafka-streams-programming, developing-kafka-python-client, kafka-schema-registry, confluent-cloud-cdc-tableflow) under `raw/vendor/confluent-agent-skills/91d1871e/`
- Pruned all 7 project-scaffold templates per CONTEXT.md D-02 anti-references (verified via parens-grouped `find` predicate)
- Authored `tools/vendor-sources.json` pin registry with schema that accommodates H.3b's future `streaming-skills-plugin` entry without rework
- Populated `raw/_ingest.md ## Pending` with 19 new entries — 10 parent articles (source attestation, D-07) + 9 trip-wires (full MCP-validation gate, D-07) — each referencing vendored paths, each carrying ingest hints for /wiki:ingest
- Trip-wires #4/#5/#6 carry explicit D-02/D-05 tension-resolution notes (evals.json not vendored; cite in body, path field is SKILL.md sibling)
- WarpStream trip-wires #7/#8/#9 flag the verbatim FSI-context paragraph as MANDATORY per the vendor-backing rule

## Task Commits

Each task was committed atomically:

1. **Task 1: Vendor confluent-agent-skills@91d1871e references and SKILL.md files** — `f990d82` (feat)
2. **Task 2: Add tools/vendor-sources.json pin registry** — `9097214` (feat)
3. **Task 3: Populate raw/_ingest.md Pending with 19 H.1 entries** — `855e731` (feat)

## Files Created/Modified

### Created
- `tools/vendor-sources.json` — Vendor pin registry (single source of truth for SHAs used by /wiki:validate drift check)
- `raw/vendor/confluent-agent-skills/91d1871e/PROVENANCE.md` — Upstream URL, SHA, ingest date, license, re-ingest workflow
- `raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/SKILL.md` + 7 reference markdown files (architecture, config-baseline, debugging, production-hardening, schema-patterns, topology-patterns, warpstream-optimization)
- `raw/vendor/confluent-agent-skills/91d1871e/skills/developing-kafka-python-client/SKILL.md` + 16 reference files (multi-event-guide.md, schema-generation-rules.md, warpstream-optimization.md, plus Python source/data files preserved from upstream)
- `raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-schema-registry/SKILL.md` + 4 reference files (detection-patterns, code-migration, schema-inference, categorization)
- `raw/vendor/confluent-agent-skills/91d1871e/skills/confluent-cloud-cdc-tableflow/SKILL.md` + 5 reference files (connector-configs, database-prerequisites, flink-sql-patterns, rest-api, troubleshooting)

### Modified
- `raw/_ingest.md` — Added Phase H.1 header comment and 19 Pending entries; preserved two existing April-2026 entries and the entire Processed section

### Vendor tree metrics
- **Total files:** 37 (36 upstream + 1 PROVENANCE.md)
- **Total size:** 484 KB
- **Per-skill references/ counts:** kafka-streams-programming=7, developing-kafka-python-client=16, kafka-schema-registry=4, confluent-cloud-cdc-tableflow=5
- **Pruned:** 7 scaffold-template files (`readme-template.md`, `terraform-templates.md`, `report-template.md`, `cli-commands.md`, `docker-compose.md`, `verification.md`, `build-templates.md`)

### tools/vendor-sources.json verbatim
```json
{
  "confluent-agent-skills": {
    "upstream": "https://github.com/confluentinc/agent-skills",
    "commit": "91d1871ef8c320be92bca955c8e42492a2778cb4",
    "ingested_at": "2026-05-16",
    "vendor_path": "raw/vendor/confluent-agent-skills/91d1871e/",
    "license": "Apache-2.0",
    "kind": "wiki-source"
  }
}
```

### Pending entry count
- 21 total (19 H.1 new + 2 preserved April-2026 entries)
- 19 H.1 entries: 10 parents + 9 trip-wires, all referencing vendored paths
- YAML validated: `yaml.safe_load()` returns 21 well-formed entries

## Decisions Made
- **YAML safety for trip-wire evals.json citation:** Plan's literal text used `source_url: also-cite: <path>`; this is invalid YAML (looks like nested mapping with an unquoted value). Used `source_url: also-cite. <path>` (period after `also-cite`) to preserve the citation marker as a single string while keeping the entry well-formed. Citation intent matches the plan; /wiki:ingest parses the value, not the discriminator-suffix.
- **Extra non-scaffold reference files preserved:** Upstream `references/` directories contain files beyond the 7 named scaffolds — `rest-api.md` (CDC-Tableflow), `multi-event-guide.md` and `schema-generation-rules.md` (Python client), plus python source files / sample schemas / docker-compose.yml. The plan's anti-references list explicitly named only those 7; un-named extras stayed. Future plans (H.1-02/H.1-03) can decide whether these are useful or noise.
- **Find binary explicit:** The Claude Code shell shims `find` to `bfs` and zsh doesn't word-split unquoted variables by default, so the plan's `find ... \( $SCAFFOLDS \) -delete` pattern needed `/usr/bin/find` inside `bash -c '...'` to preserve the plan's word-splitting semantics. Output identical to GNU find behaviour; load-bearing parens preserved.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] YAML well-formedness for `source_url: also-cite:` trip-wire entries**
- **Found during:** Task 3
- **Issue:** Plan's literal entries for trip-wires #4, #5, #6, #7 use `source_url: also-cite: <path>` — that is invalid YAML (interpreted as nested mapping with unquoted value containing colons; would have made `yaml.safe_load` fail on the Pending block)
- **Fix:** Replaced the inner colon with a period: `source_url: also-cite. <path>`. Preserves the `also-cite` discriminator as a single scalar string; the path is still in the value; the human ingest hint is unchanged
- **Files modified:** `raw/_ingest.md`
- **Verification:** `yaml.safe_load()` returns 21 well-formed entries; trip-wire entries parse as `{path, source_url, added, notes}` dicts
- **Committed in:** `855e731` (Task 3 commit)

**2. [Rule 3 - Blocking] Use /usr/bin/find with explicit bash -c for SCAFFOLDS prune**
- **Found during:** Task 1
- **Issue:** The Claude Code shell shims `find` to `bfs` which does not word-split a quoted `$SCAFFOLDS` variable the way the plan assumes; zsh's no-word-split default amplifies this — the plan's `find ... \( $SCAFFOLDS \) -delete` pattern errors out with "unknown primary or operator"
- **Fix:** Switched to `bash -c '...' ` invocation of `/usr/bin/find`, preserving the plan's identical SCAFFOLDS-variable + parens-grouped predicate semantics
- **Files modified:** None (execution-only deviation; the resulting filesystem state matches the plan exactly)
- **Verification:** All 7 scaffold files found, deleted, and a follow-up find returned empty; the load-bearing parens grouping was preserved
- **Committed in:** Task 1's `f990d82` commit (no file-change difference vs. plan's intent)

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking shell-binding)
**Impact on plan:** Zero scope creep; both auto-fixes preserve plan intent exactly. Trip-wire citation strategy still distinguishable in YAML; vendor tree contents identical to what plan specified.

## Issues Encountered
- None beyond the two auto-fixes above. No network/clone problems; pinned SHA was reachable via shallow clone; no git LFS or submodule complications in upstream tree.

## Findings (per `<output>` instructions)

- **`.gitignore` finding:** No conflict. `.gitignore` excludes `raw/repos/*` (with explicit fsi-dsp exception) and `outputs/runs/`, but does NOT exclude `raw/vendor/` — exactly what the plan and CONTEXT.md `<code_context>` recommended. Vendor tree is tracked in repo. SHA bumps will surface in `git log` as auditable changes.
- **No pruning surprises in the named scaffold list:** All 7 scaffold templates from the plan's anti-references list were present in upstream and deleted cleanly.
- **Extras worth flagging for H.1-02/H.1-03 planners:** The four upstream `references/` directories contain content the plan didn't enumerate in its anti-references list and therefore survived the prune. These will appear under the vendor tree:
  - `confluent-cloud-cdc-tableflow/references/rest-api.md` (~Tableflow REST API doc; out of D-05's 10-parent inventory)
  - `developing-kafka-python-client/references/` — `multi-event-guide.md`, `schema-generation-rules.md`, and 11 Python source/data files (producer*.py, consumer*.py, common.py, test_project.py, value.avsc, order_events.schema.json, docker-compose.yml)
  These extras don't break anything; they just aren't queued for ingest in this plan. H.1-02 / H.1-03 should treat them as out-of-scope unless explicitly added to the queue.
- **Pending count:** 21 total (19 new + 2 preserved April entries).
- **YAML well-formedness:** Verified via `yaml.safe_load()` over the Pending block — 21 dict entries, each with valid `path` field.

## User Setup Required

None — vendor acquisition is mechanical and complete.

## Next Phase Readiness

- **H.1-02 ready to start:** Parent articles queue (entries #1–10 in Pending) is consumable by /wiki:ingest with source-attestation confidence flow (D-07)
- **H.1-03 ready to start:** Trip-wire queue (entries #11–19 in Pending) is consumable by /wiki:ingest with full-MCP-validation gate
- **H.3b unblocked:** `tools/vendor-sources.json` schema accommodates the future `streaming-skills-plugin` entry without rework
- **No carry-over blockers**

## Known Stubs

None — this plan is pure setup (vendor + queue + pin registry); no wiki articles authored. Article authoring is H.1-02 and H.1-03's job.

## Self-Check: PASSED

- All 7 claimed files exist on disk (tools/vendor-sources.json, raw/_ingest.md, 4 SKILL.md files, PROVENANCE.md)
- All 3 claimed commits present in `git log` (f990d82, 9097214, 855e731)
- 19 H.1 entries + 2 carry-over entries verified via grep + yaml.safe_load

---
*Phase: H.1-wiki-ingest-agent-skills*
*Completed: 2026-05-16*
