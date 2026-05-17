---
phase: H.2-eval-harness-extension
plan: 02
subsystem: tests/evals
tags: [evals, wiki-skills, trip-wires, json-harness, structural-only]
requires:
  - tests/evals/run_skill_evals.py (H.2-01)
  - .planning/phases/H.2-eval-harness-extension/H.2-CONTEXT.md (D-03 schema, D-08 trip-wire strings)
provides:
  - tests/evals/wiki-ingest/evals.json (10 cases, 2 D-08 trip-wires verbatim)
  - tests/evals/wiki-validate/evals.json (10 cases)
  - tests/evals/wiki-lint/evals.json (10 cases)
  - tests/evals/wiki-recommend/evals.json (10 cases)
  - 40 new structurally-verified eval cases consumed by the H.2-01 runner
affects:
  - test_threshold_per_skill: now spans 4 additional skills (still PASS)
  - test_all_seven_new_skills_discovered: now PASS (was RED in H.2-01)
tech_stack:
  added: []
  patterns:
    - upstream confluentinc/agent-skills evals.json schema verbatim (D-03)
    - grep-checkable structural expectations[] (D-04)
    - trip-wire encoding as verbatim assertion strings (D-08)
key_files:
  created:
    - tests/evals/wiki-ingest/evals.json
    - tests/evals/wiki-validate/evals.json
    - tests/evals/wiki-lint/evals.json
    - tests/evals/wiki-recommend/evals.json
  modified: []
decisions:
  - 'Trip-wire strings copied verbatim from H.2-CONTEXT.md D-08 with backticks intact (JSON permits backticks unescaped) — grep -c returns 1 for both'
  - 'Cases drawn from real signals: raw/_ingest.md Processed entries (kafka-streams-topology-patterns, schema-registry-adoption-playbook, flink-confluent-cloud-setup) + wiki/_queue.md Stubs — no synthetic fixtures'
  - 'Case 4 of /wiki:ingest references the wiki/_queue.md Stub for flink-confluent-cloud-setup (still pending despite the Processed entry being authored) — accurate as of 2026-05-17'
  - 'All expectations[] are grep-checkable against case files or skill output text — zero LLM-judgment phrasing per D-04'
metrics:
  duration_minutes: 3
  tasks_completed: 2
  files_created: 4
  cases_authored: 40
  completed: 2026-05-17
---

# Phase H.2 Plan 02: Eval Harness — Wiki Skill Family Summary

Authored 4 upstream-schema `evals.json` files covering `/wiki:ingest`, `/wiki:validate`, `/wiki:lint`, `/wiki:recommend` with 10 grep-checkable cases each (40 total), encoding the 2 D-08 trip-wires assigned to `/wiki:ingest` (`avro-schema-source-directory`, `warpstream-config-overrides`) as verbatim assertion strings.

## Per-File Case Counts

| File | Cases | Skill | D-08 Trip-Wires |
|------|-------|-------|------------------|
| `tests/evals/wiki-ingest/evals.json` | 10 | `/wiki:ingest` | #5 (avro) at id=2, #8 (warpstream) at id=3 |
| `tests/evals/wiki-validate/evals.json` | 10 | `/wiki:validate` | (none — distributed to /review per D-08) |
| `tests/evals/wiki-lint/evals.json` | 10 | `/wiki:lint` | (none — distributed to /review per D-08) |
| `tests/evals/wiki-recommend/evals.json` | 10 | `/wiki:recommend` | (none — distributed to /dsp:plan per D-08) |
| **Total** | **40** | 4 wiki skills | 2/9 trip-wires (the rest land in Plan 03) |

## Trip-Wires Landed in /wiki:ingest

Both strings copied **verbatim** from `H.2-CONTEXT.md` `<specifics>` D-08, with backticks intact:

**Trip-wire #5 (avro-schema-source-directory)** — `tests/evals/wiki-ingest/evals.json` line 22, inside case `id=2`:

```
"When ingesting an article that proposes Avro schemas under `src/main/resources/avro/`, MCP-validation flags this as incorrect and the article cites `src/main/avro/` instead"
```

**Trip-wire #8 (warpstream-config-overrides)** — `tests/evals/wiki-ingest/evals.json` line 33, inside case `id=3`:

```
"When ingesting an article that proposes WarpStream `fetch.min.bytes` config, MCP-validation flags this as unsupported and the article documents the omission"
```

Verification: `grep -c "When ingesting an article that proposes Avro schemas under" tests/evals/wiki-ingest/evals.json` → `1`; `grep -c "When ingesting an article that proposes WarpStream" tests/evals/wiki-ingest/evals.json` → `1`.

## Real-World Signals Drawn On (per CONTEXT.md D-11)

### `/wiki:ingest` (10 cases)
- **id=1 (topology-patterns ingest)** — sourced from `raw/_ingest.md` Processed entry for `raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/references/topology-patterns.md` → `wiki/patterns/kafka-streams-topology-patterns.md` (H.1 parent #1)
- **id=2 (avro trip-wire)** — sourced from `wiki/concepts/avro-schema-source-directory.md` (H.1 trip-wire #5)
- **id=3 (warpstream trip-wire)** — sourced from `wiki/concepts/warpstream-config-overrides.md` (H.1 trip-wire #8)
- **id=4 (flink-confluent-cloud-setup)** — sourced from `wiki/_queue.md` Stubs section (line 14)
- **id=5 (schema-registry adoption playbook)** — sourced from `raw/_ingest.md` Processed entry for the two-way merge (`detection-patterns.md` + `code-migration.md`) → `wiki/patterns/schema-registry-adoption-playbook.md` (H.1 parent #9)
- **id=6 (MCP-unavailable, confidence-downgrade)** — sourced from `.claude/commands/wiki/ingest.md` confidence-rule logic
- **id=7 (graph-coverage orphan-prevention)** — sourced from H.1 `_graph.md` ≥1-inbound rule (STATE.md decision: "Added 3 inbound graph edges for patterns/kafka-streams-topology-patterns")
- **id=8 (name-collision)** — sourced from H.1 D-04 (no-vendor-prefix-in-filename rule)
- **id=9 (non-vendored URL source attestation)** — sourced from H.1 D-07 dual-source-attestation contract
- **id=10 (index + graph atomic update)** — sourced from `wiki/_index.md` + `wiki/_graph.md` ingest-step contract

### `/wiki:validate` (10 cases)
- **id=1 (drift, no findings)** — `wiki/concepts/schema-registry-best-practices.md` (Phase H.1 ingest, confidence: high baseline)
- **id=2 (decay, 90-day stale)** — sourced from `tools/wiki-lint.py` `check_decay()` + `DECAY_DAYS=90`
- **id=3 (broken-link)** — sourced from `tools/wiki-lint.py` broken-link regex (`re.findall(r"\[.*?\]\(...\)")`)
- **id=4 (orphan detection)** — sourced from `tools/wiki-lint.py` `lint_wiki(full=True)` orphan walk
- **id=5 (malformed YAML — space-separated tags)** — sourced from H.1 BLOCKER lesson (STATE.md decision: "All wiki YAML tag arrays use comma-separated flow sequence")
- **id=6 (vendor-drift, passive)** — sourced from `tools/wiki-lint.py` `check_vendor_drift()` + H.1 D-09 passive posture
- **id=7 (WarpStream FSI-framing)** — sourced from `wiki/concepts/warpstream-schema-registry-format-constraint.md` mandatory FSI-context paragraph (H.1)
- **id=8 (cdc-tableflow-decode pattern)** — sourced from `wiki/patterns/cdc-to-tableflow-flink-decode.md` (H.1 parent #7)
- **id=9 (confidence-unjustified)** — sourced from H.1 D-07 dual-source-attestation contract
- **id=10 (batch mode summary)** — sourced from `tools/wiki-lint.py` `main()` finding-counts loop

### `/wiki:lint` (10 cases)
- **id=1 (clean tree, exit 0)** — sourced from `tools/wiki-lint.py` line 230: `if total == 0: print("✓ Wiki looks clean."); sys.exit(0)`
- **id=2 (broken-link, non-zero exit)** — sourced from `tools/wiki-lint.py` broken-links findings dict
- **id=3 (--fix decay)** — sourced from `tools/wiki-lint.py` `apply_decay_fix()` + STATE.md decision: "apply_decay_fix scoped to front matter block via regex to prevent body text rewrites"
- **id=4 (--full categorization)** — sourced from `tools/wiki-lint.py` `lint_wiki(full=True)` labels dict (10 finding categories)
- **id=5 (malformed YAML tags)** — sourced from H.1 BLOCKER lesson (comma-separated arrays requirement)
- **id=6 (missing-field)** — sourced from existing wiki/ frontmatter convention (title, tags, sources, confidence)
- **id=7 (orphan)** — sourced from `tools/wiki-lint.py` orphans-walk
- **id=8 (vendor-drift, passive exit 0)** — sourced from `tools/wiki-lint.py` `check_vendor_drift()` + H.1 D-09 decision: "wiki-lint drift findings stay non-fatal (exit 0)"
- **id=9 (citation-resolution)** — sourced from `tests/test_wiki_citations.py` (fsi-dsp:// URI resolution)
- **id=10 (--fix idempotency)** — sourced from `tests/test_wiki_lint_drift.py` repeatable-fix property

### `/wiki:recommend` (10 cases)
- **id=1 (alias dispatch)** — sourced from Phase 01-knowledge-skill decision (STATE.md): "/wiki:recommend reduced to thin alias dispatching to /ask --mode reconsolidate"
- **id=2 (auto-stub on coverage gap)** — sourced from Phase 01 decision (STATE.md): "Auto-stub fires on all modes including ephemeral — coverage gaps are never lost"
- **id=3 (medium-confidence flagging)** — sourced from H.1 D-07 confidence-tiering rules
- **id=4 (ephemeral mode write-back)** — sourced from Phase 01 decision (STATE.md): "Mode flag governs write behavior only"
- **id=5 (ambiguous route graceful degradation)** — sourced from Phase 01 decision (STATE.md): "Triage classifier uses four routes (wiki-only/wiki+MCP/deep/refuse)"
- **id=6 (--force-route bypass)** — sourced from Phase 01 decision (STATE.md): "--force-route bypasses classifier"
- **id=7 (multi-doc provenance)** — sourced from review-skill provenance footer pattern (Phase 02 decision: "Provenance footer implemented as final paragraph in body flow")
- **id=8 (queue-resolution after stub fill)** — sourced from `wiki/_queue.md` `## Resolved` section pattern
- **id=9 (FSI overlay)** — sourced from `./CLAUDE.md` FSI overlay rule ("never username/password in FSI")
- **id=10 (determinism / idempotency)** — sourced from triage classifier deterministic-route contract

## Structurally Weak Cases & Mitigations

**None.** Every expectation across all 40 cases is grep-checkable against either case-file text, an artifact on disk, or a deterministic skill-output pattern. No LLM-judgment phrasing surfaced during authoring (e.g., zero uses of "subjectively assess", "evaluate quality of", "creatively rephrase").

A few near-misses worth noting:

- `/wiki:recommend` id=5 expectation `"Response does NOT crash with a stack trace"` — grep-checkable against runtime output (`grep -q 'Traceback'`); kept as a negative-presence assertion.
- `/wiki:recommend` id=10 expectation `"Two invocations produce the same route choice (modulo classifier nondeterminism — acceptable variance documented if any)"` — grep-checkable against the route-choice log line; the "acceptable variance documented" clause is itself a grep against the article's known-issues section.

## Deviations from Plan

None — plan was authored with verbatim case content; executor copied JSON verbatim. The plan's specified case content was already validated grep-checkable during planning.

## Verification Results

| Gate | Status |
|------|--------|
| All 4 files exist | PASS |
| Each has ≥10 cases (40 total) | PASS |
| `skill_name` matches dir (`/wiki:ingest`, `/wiki:validate`, `/wiki:lint`, `/wiki:recommend`) | PASS |
| Top-level keys exactly `{skill_name, evals}` | PASS |
| All `id` fields are unique integers | PASS |
| All `prompt`, `expected_output`, `expectations[]` non-empty | PASS |
| Trip-wire #5 (avro) grep-count = 1 | PASS |
| Trip-wire #8 (warpstream) grep-count = 1 | PASS |
| `json.load()` round-trips on all 4 files | PASS |
| `test_threshold_per_skill` PASS (≥90% per skill) | PASS |
| `test_all_seven_new_skills_discovered` PASS | PASS (was RED in H.2-01) |
| `test_case_well_formed` parametrized over 142 cases | PASS (all green) |
| `tests/golden/` 539 cases | PASS (unchanged) |
| Locked files (`tools/apply_engine.py`, `.claude/commands/dsp-apply.md`, `tests/golden/ask/`, `tests/evals/run_skill_evals.py`) | UNCHANGED |
| No space-separated arrays (H.1 BLOCKER lesson check) | PASS |

## Commits

| Task | Description | Hash | Files |
|------|-------------|------|-------|
| 1 | `/wiki:ingest` evals.json with 2 D-08 trip-wires verbatim | `1513fa0` | `tests/evals/wiki-ingest/evals.json` |
| 2 | `/wiki:validate`, `/wiki:lint`, `/wiki:recommend` evals.json (30 cases) | `6f9fad9` | 3 files under `tests/evals/wiki-{validate,lint,recommend}/` |

## Requirements Closed

- **EVAL-02 (partial):** 4 of 7 named skills now have ≥10 cases each (`/wiki:ingest`, `/wiki:validate`, `/wiki:lint`, `/wiki:recommend`). Plan 03 closes the remaining 3 (`/review`, `/dsp:plan`, `/dsp:apply`).
- **EVAL-03 (partial):** 2 of 9 H.1 trip-wires encoded as verbatim expectation strings (`avro-schema-source-directory`, `warpstream-config-overrides` in `/wiki:ingest`). Plan 03 lands the remaining 7 (4 in `/review`, 3 in `/dsp:plan`).

## Self-Check: PASSED

- File `tests/evals/wiki-ingest/evals.json`: FOUND
- File `tests/evals/wiki-validate/evals.json`: FOUND
- File `tests/evals/wiki-lint/evals.json`: FOUND
- File `tests/evals/wiki-recommend/evals.json`: FOUND
- Commit `1513fa0`: FOUND in `git log`
- Commit `6f9fad9`: FOUND in `git log`
