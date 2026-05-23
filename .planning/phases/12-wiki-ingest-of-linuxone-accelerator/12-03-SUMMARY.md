---
phase: 12-wiki-ingest-of-linuxone-accelerator
plan: 03
subsystem: review-skill + golden-eval-harness
tags: [review, golden-eval, linuxone, fsi, rbac, payload-isolation, trip-wires, wiki-01, wiki-03, wiki-05]
requires:
  - "Plan 12-01 — 6 wiki articles (auditor-readonly article supplies the 3 grep-target strings)"
provides:
  - "/review Step 4.1 — auditor-readonly payload-isolation claim-flag rule (WIKI-03)"
  - "5 LinuxONE /review golden cases (014-018) + 5 fixtures — auditor + 4 trip-wires (G-02 / G-08 / G-12 / G-13)"
  - "10 LinuxONE /ask golden cases (101-110) — 6 articles + 4 cross-cutting"
  - "WIKI-01 satisfied by verbatim deploy case (101 query is byte-identical to ROADMAP success criterion 1)"
  - "WIKI-03 satisfied by Step 4.1 claim-flag rule + case 014 exercising it"
  - "WIKI-05 satisfied — 15 new cases at EVAL-02 floor (10 /ask + 5 /review)"
affects:
  - .claude/commands/review.md
  - tests/golden/ask/cases/
  - tests/golden/review/cases/
  - tests/golden/review/fixtures/
tech_stack:
  added: []
  patterns: [h2-golden-eval-floor, claim-flag-canonical-correction, fsi-trip-wire-as-claim]
key_files:
  created:
    - tests/golden/ask/cases/linuxone-ref-arch-deploy-101.md
    - tests/golden/ask/cases/linuxone-cluster-linking-migration-102.md
    - tests/golden/ask/cases/linuxone-fips-at-install-103.md
    - tests/golden/ask/cases/linuxone-auditor-readonly-rbac-104.md
    - tests/golden/ask/cases/linuxone-s390x-image-build-105.md
    - tests/golden/ask/cases/linuxone-flink-fsi-jobs-106.md
    - tests/golden/ask/cases/linuxone-fsi-deploy-cross-cutting-107.md
    - tests/golden/ask/cases/linuxone-accelerator-dispatch-cross-cutting-108.md
    - tests/golden/ask/cases/linuxone-migration-evidence-cross-cutting-109.md
    - tests/golden/ask/cases/linuxone-fips-gap-g02-cross-cutting-110.md
    - tests/golden/review/cases/review-linuxone-auditor-isolation-014.md
    - tests/golden/review/cases/review-linuxone-fips-skip-015.md
    - tests/golden/review/cases/review-linuxone-connect-image-x86-016.md
    - tests/golden/review/cases/review-linuxone-sql-runner-skip-017.md
    - tests/golden/review/cases/review-linuxone-checkpoint-unencrypted-018.md
    - tests/golden/review/fixtures/linuxone-auditor-isolation-violation.md
    - tests/golden/review/fixtures/linuxone-fips-skip.md
    - tests/golden/review/fixtures/linuxone-connect-image-x86.md
    - tests/golden/review/fixtures/linuxone-sql-runner-skip.md
    - tests/golden/review/fixtures/linuxone-checkpoint-unencrypted.md
  modified:
    - .claude/commands/review.md
decisions:
  - "Step 4.1 inserted between Step 4 (MCP validation) and Step 5 (canon compliance) at lines 132-149 — appropriate placement for claim-level grounding, leaves Step 5+ headings unchanged"
  - "All 5 /review fixtures are 50-59 lines of plausible FSI engineer prose (well above the ≥30 minimum); contradicting claim embedded in body, not enumerated as a list of one-liners"
  - "All 5 /review cases use floor_model: haiku, expected_claims_min: 3, expected_verdict_contains: [Corrected], overlay: null — uniform shape across the trip-wire-as-claim set"
  - "Cross-cutting /ask cases 107-109 use sonnet floor (multi-article reasoning); 110 uses haiku (single G-02 article focus); 101-106 all haiku per single-article scope"
  - "Case 101 query byte-identical to ROADMAP Phase-12 success criterion 1 — verbatim WIKI-01 satisfier"
metrics:
  duration: ~5min
  completed: 2026-05-23
---

# Phase 12 Plan 03: /review claim-flag + 15 golden cases — Summary

Injected the auditor-readonly payload-isolation claim-flag rule into the
`/review` skill as **Step 4.1** (3 paraphrase patterns + verbatim canonical
correction text citing the Plan 12-01 wiki article). Authored 5 LinuxONE
`/review` fixtures + 5 cases (014-018) exercising the auditor-isolation rule
and four KNOWN-GAPS trip-wires as contradicted claims (G-02 FIPS,
G-08 Connect image, G-12 SQL-runner, G-13 checkpoint encryption). Authored
10 LinuxONE `/ask` cases (101-110) covering one per Plan 12-01 article
plus four cross-cutting topics. After this plan, **WIKI-01** is satisfied by
the verbatim deploy case, **WIKI-03** by the Step 4.1 rule + case 014, and
**WIKI-05** by the 15 new cases at the EVAL-02 floor.

## Step 4.1 — Exact line range

`.claude/commands/review.md` lines **132-149** (18 lines added). Step 5
("Check canon compliance") now begins at line **150**, previously at line
**125**. No headings renumbered.

Heading: `#### Step 4.1: Auditor-readonly payload-isolation claim flag (WIKI-03)`

Three trigger patterns + paraphrase variants in the rule body:
1. "DeveloperRead on the cluster is sufficient for auditor isolation"
2. "auditor binding can be at cluster scope"
3. "any read-only role can be used for audit access"

Canonical correction blockquote contains the verbatim grep target
`"DeveloperRead is consume-granting"` and cites
`wiki/patterns/auditor-readonly-rbac-payload-isolation.md`.

## Case Counts — Before / After

| Harness | Before | New | After |
|---------|--------|-----|-------|
| /ask    | 32     | 10  | 42    |
| /review | 16     | 5   | 21    |
| **Total** | **48** | **15** | **63** |

Both harnesses pass at the structural floor (353 tests green across the two
harness files); minimum-count gates well exceeded (`/ask` floor 30, `/review`
floor 15).

## 10 /ask Cases (101-110)

| Case | id | floor | query | required_claims |
|------|-----|-------|-------|-----------------|
| 101  | linuxone-ref-arch-deploy-101 | haiku | "How do I deploy Confluent Platform on IBM LinuxONE for FSI?" | linuxone-on-cfk-reference-architecture, 5-layer, Kustomize Component |
| 102  | linuxone-cluster-linking-migration-102 | haiku | "How do I migrate from x86 Confluent to LinuxONE Confluent with regulatory evidence?" | x86-to-linuxone-cluster-linking-migration, mirror lag, evidence |
| 103  | linuxone-fips-at-install-103 | haiku | "Why does spec.tls.fips.enabled have no effect on my OCP cluster?" | fips-at-install-ocp-requirement, post-install, install-config.yaml |
| 104  | linuxone-auditor-readonly-rbac-104 | haiku | "How do I configure an auditor RBAC role on Confluent for FSI without giving them access to business topics?" | auditor-readonly-rbac-payload-isolation, topic-scoped, confluent-audit-log-events |
| 105  | linuxone-s390x-image-build-105 | haiku | "How do I build a Confluent Connect image for s390x / LinuxONE?" | s390x-custom-image-build-pipeline, docker buildx, linux/s390x |
| 106  | linuxone-flink-fsi-jobs-106 | haiku | "What FSI Flink jobs are included in the LinuxONE accelerator?" | flink-on-cfk-fsi-example-jobs, tumbling, temporal |
| 107  | linuxone-fsi-deploy-cross-cutting-107 | sonnet | "What are the FSI hardening controls in the LinuxONE Confluent accelerator?" | RBAC, mTLS, Schema Registry, audit, Flink |
| 108  | linuxone-accelerator-dispatch-cross-cutting-108 | sonnet | "Can I run /dsp:plan or /dsp:apply against the LinuxONE accelerator?" | accelerator/confluent-on-linuxone, MODULE_TO_CANON_KEY, layer |
| 109  | linuxone-migration-evidence-cross-cutting-109 | sonnet | "What regulatory evidence should I collect when migrating Kafka workloads to LinuxONE?" | mirror lag, record-count, audit log, RBAC, schema parity, 7y |
| 110  | linuxone-fips-gap-g02-cross-cutting-110 | haiku | "Why is FIPS-at-install required for the LinuxONE accelerator's TLS layer?" | G-02, fips-at-install-ocp-requirement, install-config.yaml |

**WIKI-01 verbatim check:** Case 101's `query` field is byte-identical to the
ROADMAP Phase-12 success criterion 1: `"How do I deploy Confluent Platform
on IBM LinuxONE for FSI?"` — verified via Python equality check at commit
time.

## 5 /review Cases (014-018) + 5 Fixtures

| Case | id | Trip-wire | Fixture lines | Contradicting claim |
|------|-----|-----------|---------------|---------------------|
| 014  | review-linuxone-auditor-isolation-014 | WIKI-03 | 59 | "cluster-scoped DeveloperRead suffices for our auditor compliance" |
| 015  | review-linuxone-fips-skip-015 | G-02 | 50 | "enable FIPS post-install by editing install-config.yaml" |
| 016  | review-linuxone-connect-image-x86-016 | G-08 | 57 | "deploy upstream confluent-kafka-connect:8.2.0 as-is on LinuxONE without rebuilding" |
| 017  | review-linuxone-sql-runner-skip-017 | G-12 | 51 | "placeholder image will be resolved by the operator" |
| 018  | review-linuxone-checkpoint-unencrypted-018 | G-13 | 51 | "checkpoint state is transient — encryption-at-rest not required" |

All 5 fixtures are between 50 and 59 lines of plausible FSI engineer prose
(Confluence-page / runbook tone), with the contradicting claim embedded in
body sections, not enumerated as one-liner bullets. All 5 cases use
`floor_model: haiku`, `expected_claims_min: 3`,
`expected_verdict_contains: [Corrected]`, `overlay: null`,
`premise_challenge_expected: false`.

## Paraphrase Tuning Notes

No trip-wire IDs required paraphrase tuning to land the contradicting claim
in fixture prose. Each fixture's claim used the upstream KNOWN-GAPS
phrasing directly (FIPS install-config.yaml, custom s390x image rebuild,
SQL-runner placeholder, checkpoint encryption-at-rest) — the FSI-engineer
prose mode let the contradiction sit naturally inside a "## Approach" or
"## Storage decision" body section without forcing the language.

For case 014 (auditor-isolation), the fixture embeds **three** of the
six tuned paraphrases from the Step 4.1 rule — "cluster-scoped DeveloperRead
suffices", "auditor binding can be at cluster scope", "any read-only role
can be used for audit access" — to give the reviewer redundant trigger
surface area without making the claim sound stilted.

## Deviations from Plan

None. Plan executed exactly as written:

- All 4 tasks completed in order (Step 4.1 → 5 review cases → 10 ask cases → harness verification).
- No structural test failures on new cases; no fix-up rounds needed.
- IDs 014-018 and 101-110 were all next-free (verified at start of task).
- Wiki article grep targets (slugs) verified in Plan 12-01 articles before
  authoring cases (avoided the "grep target not in article body" failure mode).

## Verification Results

- `grep -c "DeveloperRead is consume-granting" .claude/commands/review.md` → **1** (rule landed)
- `grep -c "auditor-readonly-rbac-payload-isolation.md" .claude/commands/review.md` → **1** (path-to-article preserved)
- `grep -c "Step 4.1" .claude/commands/review.md` → **1** (no duplicates)
- `ls tests/golden/review/cases/ | grep linuxone | wc -l` → **5**
- `ls tests/golden/ask/cases/ | grep linuxone | wc -l` → **10**
- `pytest tests/golden/ask/test_golden_ask.py tests/golden/review/test_golden_review.py` → **353 passed, 0 failed**
- `pytest tests/` → **1158 passed, 1 failed** (only `test_no_raw_fsi_dsp_paths_in_sources` — 12-04 carry-forward)

## Downstream Dependencies

- **Plan 12-04** (carry-forward fix): Independent file scope (6 observability
  articles' `sources:` field). After 12-04, `pytest tests/` exits 0 cleanly
  and the v2.0 hygiene debt clears. WIKI-01/03/05 remain satisfied by this
  plan's artifacts.

## Commits (this plan)

| # | Hash    | Subject |
|---|---------|---------|
| 1 | 2712a2b | feat(12-03): inject auditor-readonly claim-flag rule into /review Step 4.1 |
| 2 | 9792605 | test(12-03): add 5 LinuxONE /review fixtures + 5 cases (014-018) |
| 3 | 6fc7ab4 | test(12-03): add 10 LinuxONE /ask golden cases (101-110) |

## Self-Check: PASSED

- All 21 created files verified on disk:
  - FOUND: .claude/commands/review.md (Step 4.1 at L132-149)
  - FOUND: 10 ask cases at tests/golden/ask/cases/linuxone-*-{101..110}.md
  - FOUND: 5 review cases at tests/golden/review/cases/review-linuxone-*-{014..018}.md
  - FOUND: 5 review fixtures at tests/golden/review/fixtures/linuxone-*.md
- All 3 commits (`2712a2b`, `9792605`, `6fc7ab4`) present in `git log --oneline`.
- WIKI-01, WIKI-03, WIKI-05 structurally satisfied (verbatim query, Step 4.1
  rule + case, ≥15 new cases).
- Golden harness passes; broader test suite has exactly the expected pre-existing
  failure carried forward to Plan 12-04.
