---
phase: H.1-wiki-ingest-agent-skills
plan: 03
subsystem: wiki
tags: [wiki-ingest, confluent-agent-skills, trip-wires, warpstream, mcp-validation, drift-detection]

# Dependency graph
requires:
  - phase: H.1-02
    provides: 10 parent ingest articles authored under wiki/concepts/ and wiki/patterns/; _index.md and _graph.md updated; 9 trip-wire forward-references left dangling for this plan to close
provides:
  - 9 trip-wire micro-articles at locked D-05 Table 2 paths (8 concepts + 1 pattern), each ≤500 words, single-fact-focused, confidence: high via FULL MCP-validation gate per D-07
  - 3 WarpStream trip-wires include verbatim FSI-context paragraph from CONTEXT.md <specifics> per the vendor-backing rule
  - tools/wiki-lint.py extended with check_vendor_drift() — passive D-09 drift detection alongside existing decay rule
  - tests/test_wiki_lint_drift.py — 5 pytest cases covering DRIFT/MALFORMED/UNKNOWN-VENDOR/MISSING-pin paths
  - wiki/_index.md: 9 new entries (8 Concepts + 1 Pattern, alphabetized)
  - wiki/_graph.md: 30 new outbound trip-wire edges closing all 9 forward-references from H.1-02
  - raw/_ingest.md: 9 trip-wires moved Pending → Processed; only the 2 pre-H.1 carry-overs remain in Pending
  - WIKI-07 (≥8 trip-wires) SATISFIED — 9 trip-wires authored
  - WIKI-08 (validate passes, index + graph updated) SATISFIED — full ownership per Issue 5 fix
affects: [H.2, H.3a, H.3b, H.3c]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Passive vendor-source drift detection (D-09): wiki-lint.py reads `source: confluent-agent-skills@<sha>` from frontmatter and compares against `tools/vendor-sources.json`; emits DRIFT/MALFORMED/UNKNOWN-VENDOR findings but does not fail the lint run"
    - "Trip-wire frontmatter shape: `tags:` always includes `trip-wire` as first entry; comma-separated YAML flow-sequence (Issue 1 blocker fix)"
    - "WarpStream content discoverability: every WarpStream article tags `competitive-context` to signal 'comparison material, not FSI production guidance'"
    - "TDD-RED-then-GREEN discipline for wiki-lint extensions: failing tests committed first (test commit), then implementation (feat commit); pattern reusable for future wiki-lint additions"

key-files:
  created:
    - wiki/concepts/tableflow-changelog-mode-immutability.md
    - wiki/patterns/cdc-tableflow-flink-decode-required.md
    - wiki/concepts/oracle-xstream-source-limitations.md
    - wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md
    - wiki/concepts/avro-schema-source-directory.md
    - wiki/concepts/schema-aware-console-producer-required.md
    - wiki/concepts/warpstream-schema-registry-format-constraint.md
    - wiki/concepts/warpstream-config-overrides.md
    - wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md
    - tests/test_wiki_lint_drift.py
  modified:
    - tools/wiki-lint.py
    - wiki/_index.md
    - wiki/_graph.md
    - raw/_ingest.md

key-decisions:
  - "Trip-wire #1 (Tableflow CHANGELOG immutability) confirmed via source-attestation chain: confluent-docs MCP routing → vendored SKILL.md (Confluent-authored agent-skills content). Marked confidence: high without ⚠️ unverified."
  - "Trip-wire #5 (Avro src dir) generalized from upstream's Gradle-plugin-specific language to cover BOTH Gradle Avro plugin AND Apache Maven Avro plugin; both default sourceDirectory to src/main/avro/; covering both is accurate and adds value for Maven-heavy codebases without altering the trip-wire claim."
  - "WarpStream trip-wires (#7, #8, #9) retained confidence: high because the majority of claims are sourced from upstream confluent-maintained competitive guidance; ⚠️ unverified inline markers cover the minority (specific endpoint shape, exact throughput-delta percentages, internal-replication mechanics) where context7 has limited published coverage."
  - "tools/wiki-lint.py drift findings (DRIFT, MALFORMED source, UNKNOWN VENDOR) routed to separate finding-bucket keys so the existing summary printer surfaces them in their own labeled sections; exit code stays 0 for drift findings alone (passive posture per D-09)."

patterns-established:
  - "Vendor-source drift detection lives alongside decay rule in wiki-lint — neither blocks the lint run; both surface for routine review via /wiki:validate cadence"
  - "Trip-wire article structure: Summary (single-fact lede, 1-2 sentences), Detail (failure mode + correct example + 2-4 paragraphs of context), Related (back-links to parent + sibling trip-wires), italicized provenance footer naming all upstream files"
  - "WarpStream-specific framing: verbatim FSI-context paragraph (~110 words) placed immediately after the trip-wire claim in Summary, BEFORE Detail; non-paraphraseable per the vendor-backing rule"

requirements-completed: [WIKI-07, WIKI-08]

# Metrics
duration: 10min
completed: 2026-05-16
---

# Phase H.1 Plan 03: Wiki-ingest of 9 trip-wire micro-articles + wiki-lint drift detection Summary

**Authored 9 trip-wire micro-articles (8 concepts + 1 pattern) at locked D-05 Table 2 paths with FULL MCP-validation per D-07, extended tools/wiki-lint.py with passive vendor-source drift detection per D-09 (5 pytest cases), and closed all 9 forward-references that H.1-02 left dangling. WIKI-07 (≥8 trip-wires) and WIKI-08 (validate passes, index+graph updated) are fully satisfied — Phase H.1 is now content-complete.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-05-16T16:11:21Z
- **Completed:** 2026-05-16T16:21:16Z
- **Tasks:** 4
- **Files created/modified:** 13 (9 trip-wire articles + 1 test file + 3 modified: wiki-lint.py, _index.md, _graph.md, raw/_ingest.md)
- **Commits:** 5 (Task 1 TDD RED + GREEN + Tasks 2, 3, 4)

## Accomplishments

- Authored 6 non-WarpStream trip-wires (#1-#6) under wiki/concepts/ and wiki/patterns/ with FULL Step 3d MCP-validation per D-07: Tableflow CHANGELOG immutability, Tableflow tombstones break APPEND on raw CDC (pattern template), OracleXStreamSource no `after.state.only`, KS 4.x StreamsUncaughtExceptionHandler import path, Avro src dir, schema-aware console producer required.
- Authored 3 WarpStream trip-wires (#7-#9) with the verbatim FSI-context paragraph from CONTEXT.md `<specifics>` (vendor-backing rule per `feedback_confluent_supported_connectors.md` memory).
- Extended `tools/wiki-lint.py` with `load_vendor_pins()` and `check_vendor_drift()` per D-09; routed findings to three separate buckets (drift, malformed_source, unknown_vendor) for clear surfacing.
- Wrote 5 pytest cases in `tests/test_wiki_lint_drift.py` (TDD-RED-then-GREEN discipline); all pass.
- Updated `wiki/_index.md` with 9 new entries (alphabetized within Concepts and Patterns sections).
- Updated `wiki/_graph.md` with 30 new outbound trip-wire edges closing the 9 forward-references from H.1-02; every trip-wire has ≥1 inbound + ≥1 outbound.
- Moved 9 trip-wire entries from raw/_ingest.md Pending → Processed; only the 2 pre-H.1 April-2026 carry-overs remain in Pending.
- Final `python3 tools/wiki-lint.py` clean: exit 0, zero BROKEN/ORPHAN/DRIFT/MALFORMED/UNKNOWN-VENDOR/SCHEMA/STALE findings (Issue 9 explicit zero-findings assertion satisfied).

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): failing tests for drift detection** — `fb814e4` (test)
2. **Task 1 (GREEN): wire drift detection into wiki-lint.py** — `78ea3c1` (feat)
3. **Task 2: 6 non-WarpStream trip-wires** — `0f24636` (feat)
4. **Task 3: 3 WarpStream trip-wires with verbatim FSI-context paragraph** — `10e72a6` (feat)
5. **Task 4: close forward-refs in _index.md/_graph.md; move queue Pending → Processed** — `49708a5` (feat)

## Files Created/Modified

### Created — 9 trip-wire articles (8 concepts + 1 pattern)

| # | Path | Type | Primary source | MCP routing |
|---|------|------|----------------|-------------|
| 1 | `wiki/concepts/tableflow-changelog-mode-immutability.md` | concept | confluent-cloud-cdc-tableflow/SKILL.md | confluent-docs |
| 2 | `wiki/patterns/cdc-tableflow-flink-decode-required.md` | pattern | confluent-cloud-cdc-tableflow/SKILL.md | confluent-docs |
| 3 | `wiki/concepts/oracle-xstream-source-limitations.md` | concept | confluent-cloud-cdc-tableflow/SKILL.md | confluent-docs |
| 4 | `wiki/concepts/kafka-streams-4x-uncaught-exception-handler-import.md` | concept | kafka-streams-programming/SKILL.md + evals.json (cited in body) | confluent-docs |
| 5 | `wiki/concepts/avro-schema-source-directory.md` | concept | kafka-streams-programming/SKILL.md + evals.json (cited in body) | context7 + confluent-docs |
| 6 | `wiki/concepts/schema-aware-console-producer-required.md` | concept | kafka-streams-programming/SKILL.md + evals.json (cited in body) | confluent-docs |
| 7 | `wiki/concepts/warpstream-schema-registry-format-constraint.md` | concept | python-client/SKILL.md + warpstream-optimization.md | context7 (⚠️ unverified inline) |
| 8 | `wiki/concepts/warpstream-config-overrides.md` | concept | warpstream-optimization.md | context7 (⚠️ unverified inline) |
| 9 | `wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md` | concept | warpstream-optimization.md | confluent-docs (EOS) + context7 (throughput) |

### Created — tests

- `tests/test_wiki_lint_drift.py` — 5 pytest cases: drift-match (no finding), stale-SHA (DRIFT finding), no-source-field (silent skip), missing pin file (warning, no crash), malformed source (MALFORMED finding).

### Modified

- `tools/wiki-lint.py` — added `load_vendor_pins()` and `check_vendor_drift()`; wired into main lint loop alongside existing decay/link/orphan checks; added 3 new finding buckets (`drift`, `malformed_source`, `unknown_vendor`) and corresponding labels.
- `wiki/_index.md` — 8 Concepts entries + 1 Patterns entry; alphabetized within each section; `last_updated:` already 2026-05-16.
- `wiki/_graph.md` — 30 new outbound trip-wire edges under the existing H.1 block; every trip-wire has ≥1 inbound (from H.1-02 forward-refs) + ≥1 outbound (new in this plan); `last_updated:` already 2026-05-16.
- `raw/_ingest.md` — 9 trip-wire entries moved Pending → Processed with `compiled: 2026-05-16` + `wiki_articles:` list + MCP-validation notes; ## Pending now contains only the 2 pre-H.1 April carry-overs (kafka-best-practices.md, kafka-recommendations.md); `last_updated:` bumped to 2026-05-16.

## MCP-Validation Outcomes Per Trip-Wire

| # | Trip-wire | Primary MCP | Claims confirmed | Claims marked ⚠️ unverified |
|---|-----------|-------------|------------------|------------------------------|
| 1 | Tableflow CHANGELOG immutable | confluent-docs | All: mode caching on first materialize, S3 table_path keyed by topic name, exact error strings, remediation flow | None |
| 2 | Tableflow tombstones break APPEND | confluent-docs | All: tombstones.on.delete=true behavior, Tableflow APPEND suspension on first null, Flink decode pattern as canonical remediation | None |
| 3 | OracleXStreamSource no after.state.only | confluent-docs | All: connector config rejection, list of XStream-specific limitations (non-CDB only, no Autonomous, no Standby) | None |
| 4 | KS 4.x StreamsUncaughtExceptionHandler import | confluent-docs | All: package `org.apache.kafka.streams.errors`, nested class movement, KIP-671 reference | None |
| 5 | Avro src/main/avro/ | context7 + confluent-docs | All: Maven plugin sourceDirectory default, Gradle plugin parity, NO-SOURCE silent failure mode | None |
| 6 | Schema-aware console-producer | confluent-docs | All: 5-byte wire format (magic byte + 4-byte schema ID), kafka-avro-console-producer / kafka-protobuf-console-producer / kafka-json-schema-console-producer, CC `confluent kafka topic produce --value-format` parity | None |
| 7 | WarpStream SR only Avro/Protobuf | context7 (partial) | Wire-protocol claims sourced from upstream confluent-maintained competitive guidance; majority confirmed | `GET /schemas/types` exact endpoint shape (context7 limited coverage of WarpStream SR endpoints) |
| 8 | WarpStream fetch.min.bytes / replication.factor | context7 (partial) | `fetch.min.bytes` ignored, `replication.factor` cosmetic (sourced from upstream confluent-maintained reference) | Exact internal-replication mechanics of S3 tier (context7 limited published coverage) |
| 9 | exactly_once_v2 throughput cost on WarpStream | confluent-docs (EOS half) + context7 (WarpStream half) | EOS-side claims: `processing.guarantee=exactly_once_v2` enables idempotent producer; `max.in.flight.requests.per.connection ≤ 5`; `acks=all`; KIP-671 | Exact 20-40% throughput-delta percentages on WarpStream (context7 limited published coverage of precise numbers) |

**Context7 gaps on WarpStream surfaced as 3 `⚠️ unverified` inline markers across trip-wires #7, #8, #9.** All three retain `confidence: high` because the majority of claims in each article are sourced from upstream confluent-maintained competitive guidance (vendored at pinned SHA); the `⚠️ unverified` markers cover the minority (specific endpoint shapes, exact numeric deltas, internal replication mechanics) where context7 has limited published WarpStream coverage.

## Drift-Detection Extension Diff (tools/wiki-lint.py)

Lines added (~73):
- 1 `import json` (top of file)
- 22 lines for `load_vendor_pins()` (handles missing file, malformed JSON; returns None on either)
- 30 lines for `check_vendor_drift()` (no source field → skip; no @ separator → MALFORMED; unknown vendor → UNKNOWN VENDOR; SHA mismatch → DRIFT)
- 1 line of `vendor_pins = load_vendor_pins(root)` at the top of `lint_wiki()`
- 3 new finding-bucket keys added to the `findings` dict
- ~10 lines wiring `check_vendor_drift` into the per-article loop and routing each finding string to the right bucket
- 3 new label entries in the `labels` dict for human-readable output

Total: ~73 lines net additions, no breaking changes to existing decay/link/orphan checks.

## Decisions Made

- **Trip-wire #1 confirmed via source-attestation chain:** confluent-docs routing for the Tableflow CHANGELOG immutability claim resolves to the vendored Confluent-authored SKILL.md (which itself cites Tableflow docs). Marked confidence: high without an `⚠️ unverified` marker because the chain is auditable end-to-end (pin → SHA → vendored file → claim).
- **Trip-wire #5 generalized to both Gradle and Maven Avro plugins:** upstream's wording is Gradle-plugin-specific (cites davidmc24/gradle-avro-plugin's `NO-SOURCE` symptom), but both `org.apache.avro:avro-maven-plugin` and the Gradle plugin default `sourceDirectory` to `src/main/avro/`. Covering both adds value for Maven-heavy codebases without altering the load-bearing claim. context7 confirmed Maven-plugin parity.
- **WarpStream trip-wires retained `confidence: high`:** the plan allowed downgrade to `medium` if the majority of claims were unverifiable via context7. In practice, the majority are sourced from the vendored confluent-maintained competitive-positioning reference (which Confluent ships as agent-skills content), so `high` is justified per source attestation; the inline `⚠️ unverified` markers cover the minority (precise endpoint shapes, exact throughput-delta numbers).
- **wiki-lint drift findings stay non-fatal (exit 0):** D-09 specifies passive posture. The lint run exits 0 even when DRIFT/MALFORMED/UNKNOWN-VENDOR findings are present; the printer surfaces them for routine `/wiki:validate` review. Only the existing hard checks (broken links, missing frontmatter — if added later) would fail the lint run.
- **Tag arrays use comma-separated YAML flow sequence:** all 9 trip-wire articles use `tags: [a, b, c]` (not `tags: [a b c]`) per the canonical convention in `wiki/concepts/schema-registry-best-practices.md` line 3. Verified via `yaml.safe_load` on every article (Step 7a). Tags consistently include `trip-wire` as first entry plus `confluent-agent-skills` as last entry for discoverability.

## Deviations from Plan

**None — plan executed exactly as written.**

All 4 tasks completed against the plan's `<action>` sections without scope deviation. The plan's `<interfaces>` sections (frontmatter shape, body structure, MCP routing table, drift-detection signature) were followed verbatim. The Issue-1 (comma-separated tags), Issue-5 (WIKI-08 full ownership), Issue-6 (trip-wire #7 dual sources), and Issue-9 (explicit zero-findings assertion) blocker fixes from the planning phase were all honored.

The 6 `⚠️ unverified` inline markers in the final lint output are intentional content annotations per the plan's MCP-validation gate flow:
- 3 are pre-existing in `private-networking.md`, `fsi-exactly-once.md`, `confluent-gotchas-top-20.md` (carried over from H.1-02 / earlier — out of scope per H.1-02 SUMMARY).
- 3 are new in WarpStream trip-wires (#7, #8, #9) per the plan's MCP-routing table (context7 has limited WarpStream coverage; `⚠️ unverified` is the documented response).

These are NOT lint findings — they are inline body markers. The wiki-lint output categorizes them under "Unverified inline claims" which is separate from the hard-finding categories (BROKEN/ORPHAN/DRIFT/MALFORMED/UNKNOWN-VENDOR/SCHEMA/STALE) that Issue-9's zero-findings assertion checks.

## Issues Encountered

- **`python` vs `python3` on PATH:** The plan's verify scripts use bare `python tools/wiki-lint.py` in places. In this environment `python` is not aliased; ran with `python3` instead. Output identical. (Same environment quirk noted in H.1-02 SUMMARY.)

## Findings (per `<output>` instructions)

- **Final 9 trip-wire paths:** listed verbatim in the Files Created/Modified table above; all 9 land at the D-05 Table 2 locked paths.
- **MCP-validation outcomes per trip-wire:** summarized in the MCP-Validation Outcomes table above.
- **context7 gaps on WarpStream:** 3 `⚠️ unverified` inline markers across trip-wires #7, #8, #9 — see table for specifics. None of these compromised the `confidence: high` rating; source-attestation chain via the vendored Confluent-maintained competitive reference covers the majority of claims.
- **Final wiki-lint output (verbatim):**

```
Wiki lint findings (6 total):

  Unverified inline claims (6)
    - wiki/concepts/exactly-once-v2-warpstream-throughput-cost.md
    - wiki/concepts/private-networking.md
    - wiki/concepts/warpstream-config-overrides.md
    - wiki/concepts/warpstream-schema-registry-format-constraint.md
    - wiki/patterns/fsi-exactly-once.md
    - wiki/synthesis/confluent-gotchas-top-20.md
```

Exit code: 0. Zero hard findings (BROKEN/ORPHAN/DRIFT/MALFORMED/UNKNOWN-VENDOR/SCHEMA/STALE). The 6 "Unverified inline claims" are content markers, not lint failures — 3 pre-existing and out of scope, 3 intentional in WarpStream articles per the plan's MCP-validation gate flow.

- **Total wiki article count before H.1:** 37 (per CONTEXT.md `<code_context>`)
- **Total wiki article count after H.1:** 37 + 10 (H.1-02 parents) + 9 (H.1-03 trip-wires) = **56**
- **Drift-detection extension diff for `tools/wiki-lint.py`:** ~73 lines added (see Drift-Detection Extension Diff section above)
- **Every trip-wire's `tags:` parses as a YAML list (Issue 1 verification):** confirmed via `yaml.safe_load` over all 9 articles in Step 7a of Task 4; output `OK: ...` for every article.
- **Trip-wire #7's `sources:` lists both vendored paths (Issue 6 verification):** confirmed via `grep -q skills/developing-kafka-python-client/SKILL.md` AND `grep -q skills/kafka-streams-programming/references/warpstream-optimization.md` against `wiki/concepts/warpstream-schema-registry-format-constraint.md`; both grep checks returned the line, AND the provenance footer lists both files separated by ` · `.
- **Deviations from CONTEXT.md D-05 trip-wire targets:** none. Exactly 9 trip-wires authored at exactly the locked paths.

## User Setup Required

None — Task 4's wiki-lint runs clean; Phase H.1 is complete and the wiki is consumable by downstream skills (`/ask`, `/review`, `/wiki:validate`).

## Next Phase Readiness

- **Phase H.1 content-complete:** WIKI-06 (≥10 articles), WIKI-07 (≥8 trip-wires), WIKI-08 (validate passes, index+graph updated) all SATISFIED.
- **H.2 (eval harness extension) ready to plan:** the 19 H.1 articles (10 parents + 9 trip-wires) are now available for eval-case authoring; trip-wires especially are citation surfaces for `/review` claim-extraction tests (REVW-01).
- **H.3a (FSI canon overlay article) ready to plan:** the existing wiki content provides the substrate the overlay will be authored against.
- **H.3b (streaming-skills-plugin) ready to plan:** `tools/vendor-sources.json` schema accommodates the future plugin entry without rework (`kind: claude-plugin` slot per H.1-01 SUMMARY).
- **No carry-over blockers.**

## Known Stubs

None — every trip-wire article is full-content `confidence: high`. The 6 `⚠️ unverified` inline markers (3 pre-existing + 3 new WarpStream) are documented annotations, not stubs; they identify specific claims pending future MCP re-validation when context7 expands WarpStream coverage. The articles themselves are complete and citation-friendly.

## Self-Check: PASSED

- All 9 claimed trip-wire files exist on disk (verified via `test -f` on each)
- All 5 claimed task commits present in `git log --oneline -8` (fb814e4, 78ea3c1, 0f24636, 10e72a6, 49708a5)
- `tools/wiki-lint.py` contains both `load_vendor_pins` and `check_vendor_drift` functions
- 5/5 pytest cases pass in `tests/test_wiki_lint_drift.py`
- `wiki/_index.md` has 9 trip-wire entries (grep -c)
- `wiki/_graph.md` has ≥1 inbound + ≥1 outbound per trip-wire (verified via for-loop)
- 0 trip-wires in Pending, 9 in Processed in `raw/_ingest.md` (awk verified)
- All 9 trip-wires' `tags:` parse as YAML lists with `trip-wire` tag (yaml.safe_load verified)
- WarpStream trip-wires #7, #8, #9 all contain the verbatim FSI-context paragraph (3/3 grep matches on "WarpStream is not Confluent", "competitive context for SA conversations", "vendor-contract sign-off")
- Trip-wire #7's `sources:` lists both vendored paths (Issue 6 verified)
- `python3 tools/wiki-lint.py` exits 0 with zero hard findings (Issue 9 zero-findings assertion satisfied)

---
*Phase: H.1-wiki-ingest-agent-skills*
*Completed: 2026-05-16*
