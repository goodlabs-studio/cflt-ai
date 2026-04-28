---
phase: 01-knowledge-skill
plan: "01"
subsystem: wiki-tooling
tags: [wiki, decay, tdd, testing, lint]
dependency_graph:
  requires: []
  provides: [wiki-decay-lifecycle, check_decay, apply_decay_fix, test_wiki_decay]
  affects: [wiki-lint, article-format-spec, all-wiki-articles]
tech_stack:
  added: []
  patterns: [tdd-red-green, wiki-frontmatter-schema]
key_files:
  created:
    - tests/test_wiki_decay.py
  modified:
    - tools/wiki-lint.py
    - .claude/commands/wiki/references/article-format.md
    - wiki/concepts/cluster-linking-topology.md
    - wiki/concepts/consumer-group-rebalancing.md
    - wiki/concepts/consumer-lag-monitoring.md
    - wiki/concepts/exactly-once-semantics.md
    - wiki/concepts/flink-checkpointing.md
    - wiki/concepts/sla-tiers.md
    - wiki/concepts/fsi-data-streaming-platform.md
    - wiki/concepts/schema-evolution-strategies.md
    - wiki/concepts/fsi-compliance.md
    - wiki/concepts/producer-batching-config.md
    - wiki/concepts/linuxone-kafka-integration.md
    - wiki/patterns/fsi-exactly-once.md
    - wiki/patterns/dead-letter-queue-design.md
    - wiki/patterns/aks-kafka-tuning.md
    - wiki/patterns/dr-cluster-linking.md
    - wiki/patterns/dr-mirrormaker2.md
    - wiki/patterns/dr-multi-region-cluster.md
    - wiki/patterns/topic-naming.md
    - wiki/patterns/fsi-governance-automation.md
    - wiki/synthesis/adr-index.md
decisions:
  - "last_validated set to 2026-04-28 for all articles since they were reviewed during Phase 0"
  - "DECAY_DAYS = 90 constant at module level for easy adjustment"
  - "check_decay falls back to last_updated if last_validated absent (graceful degradation)"
  - "apply_decay_fix uses regex scoped to front matter block only to avoid body rewriting"
  - "Tasks 1 and 2 committed together since apply_decay_fix needed for test collection"
metrics:
  duration_minutes: 3
  completed_date: "2026-04-28"
  tasks_completed: 2
  files_modified: 23
---

# Phase 01 Plan 01: Wiki Decay Lifecycle Summary

## One-Liner

Added `last_validated` decay field to all 19 wiki articles with `check_decay()`/`apply_decay_fix()` tooling and 7-test TDD coverage enforcing 90-day confidence:high staleness detection.

## What Was Built

### WIKI-03: last_validated field in all articles and spec

Every wiki article in `wiki/concepts/`, `wiki/patterns/`, and `wiki/synthesis/` now carries a `last_validated: 2026-04-28` field in YAML front matter, inserted immediately after `last_updated`. The `article-format.md` spec is updated with the full field documentation and `last_validated` added to the Required Fields list. All three article templates (concept, pattern, stub) now include `last_validated: YYYY-MM-DD`.

### WIKI-04: Decay detection and --fix auto-demotion

`tools/wiki-lint.py` gained two new functions:

- `check_decay(fm, last_validated_fallback_field="last_updated") -> bool` — returns True when `confidence == "high"` and `last_validated` is more than `DECAY_DAYS = 90` days old. Falls back to `last_updated` if `last_validated` is absent.
- `apply_decay_fix(content) -> tuple[bool, str]` — replaces `confidence: high` with `confidence: medium` using a regex scoped to the front matter block only, leaving any body text mentioning confidence untouched.

`lint_wiki()` gained a `fix: bool = False` parameter and a `"decayed": []` findings category. `--fix` was added to the CLI arg parser; it implies `--full`.

### TDD test suite

`tests/test_wiki_decay.py` provides 7 pytest tests across two classes:

| Class | Test | Asserts |
|-------|------|---------|
| `TestLastValidatedField` | `test_all_articles_have_last_validated` | Every concept/pattern/synthesis article has the field |
| `TestLastValidatedField` | `test_last_validated_is_valid_date` | Value matches `YYYY-MM-DD` |
| `TestLastValidatedField` | `test_article_format_spec_documents_last_validated` | Spec file contains the string |
| `TestDecayRule` | `test_stale_high_confidence_detected` | 91-day-old high article triggers decay |
| `TestDecayRule` | `test_fresh_high_confidence_not_detected` | 30-day-old high article does not |
| `TestDecayRule` | `test_medium_confidence_not_affected` | Medium never decays |
| `TestDecayRule` | `test_fix_rewrites_confidence_in_frontmatter_only` | Body text preserved |

## Verification Results

```
tests/test_wiki_decay.py: 7 passed
tests/ (full suite):       64 passed, 0 failed
python3 tools/wiki-lint.py --full: exits 0, no errors
grep -c last_validated wiki/concepts/*.md wiki/patterns/*.md wiki/synthesis/*.md: all = 1
```

## Deviations from Plan

### Tasks Combined in Single Commit

The plan specified Tasks 1 and 2 as separate TDD cycles. In practice, `tests/test_wiki_decay.py` imports `check_decay` and `apply_decay_fix` at module level (not inside test functions), causing collection failures if the functions don't exist. To keep a clean commit (no broken test files at HEAD), both tasks were implemented and committed together. All TDD RED/GREEN/REFACTOR phases were executed in sequence — the only deviation is a single combined commit instead of two separate commits.

No other deviations.

## Known Stubs

None. All articles now carry `last_validated: 2026-04-28`. No placeholder data flows to any UI or rendered output.

## Self-Check: PASSED

- `tests/test_wiki_decay.py` — FOUND
- `tools/wiki-lint.py` contains `DECAY_DAYS = 90` — FOUND
- `tools/wiki-lint.py` contains `def check_decay(` — FOUND
- `tools/wiki-lint.py` contains `def apply_decay_fix(` — FOUND
- `tools/wiki-lint.py` contains `"decayed": []` — FOUND
- `tools/wiki-lint.py` contains `--fix` — FOUND
- `wiki/concepts/sla-tiers.md` contains `last_validated: 2026-04-28` — FOUND
- `wiki/concepts/exactly-once-semantics.md` contains `last_validated: 2026-04-28` — FOUND
- `wiki/patterns/dr-cluster-linking.md` contains `last_validated: 2026-04-28` — FOUND
- `wiki/synthesis/adr-index.md` contains `last_validated: 2026-04-28` — FOUND
- Commit `88c3410` — FOUND
