---
phase: "00-foundation"
plan: "03"
subsystem: "canon-overlay"
tags: ["canon", "overlay", "yaml", "python", "testing"]
dependency_graph:
  requires: ["00-01"]
  provides: ["canon-overlay-stack", "stack-hash", "provenance-footer"]
  affects: ["all artifact provenance footers", "customer fork mechanism"]
tech_stack:
  added: ["PyYAML", "hashlib (stdlib)", "json (stdlib)"]
  patterns: ["four-layer composition overlay", "deep merge semantics", "ADR-backed overrides", "SHA-256 stack hash"]
key_files:
  created:
    - canon/README.md
    - canon/base/README.md
    - canon/base/defaults.yaml
    - canon/industry/fsi/README.md
    - canon/industry/fsi/overrides.yaml
    - canon/industry/fsi/adrs/README.md
    - canon/customer/README.md
    - canon/customer/.gitkeep
    - canon/engagement/README.md
    - canon/engagement/.gitkeep
    - canon/__init__.py
    - canon/stack.py
    - tests/test_canon_overlay.py
  modified: []
decisions:
  - "canon/stack.py uses Optional[List[str]] typing (not X|Y union) for Python 3.9 compatibility"
  - "Stack hash truncated to 16 hex chars from SHA-256 for compact provenance footers"
  - "ADR-009 pre-registered as Proposed in FSI layer index (no fsi-dsp file yet)"
metrics:
  duration_seconds: 172
  completed_date: "2026-04-28T18:40:34Z"
  tasks_completed: 2
  tasks_total: 2
  files_created: 13
  files_modified: 0
  tests_added: 21
  tests_passing: 21
---

# Phase 00 Plan 03: Canon Overlay Stack Scaffolding Summary

Four-layer canon overlay (base -> industry/fsi -> customer -> engagement) with machine-readable YAML defaults, ADR-backed FSI overrides, deep-merge stack resolution, SHA-256 provenance hash, and 21 passing tests.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Scaffold canon overlay directory structure | a34fd88 | 10 files (canon/ tree, defaults.yaml, overrides.yaml, ADR index) |
| 2 | Create stack resolution utility and overlay tests | 5e2326f | 3 files (stack.py, __init__.py, test_canon_overlay.py) |

## What Was Built

The canon overlay stack is the trust mechanism for the entire system. Three components were delivered:

**1. Four-layer directory tree (`canon/`)**

```
canon/
  base/             defaults.yaml (universal Confluent Canon from CLAUDE.md)
  industry/fsi/     overrides.yaml (5 ADR-backed FSI overrides) + adrs/README.md
  customer/         README + .gitkeep (scaffold for per-customer overrides)
  engagement/       README + .gitkeep (scaffold for per-engagement overrides)
```

**2. Machine-readable canonical defaults (`canon/base/defaults.yaml`)**

Extracted directly from CLAUDE.md into structured YAML sections: `topic_design`, `schema_registry`, `producer`, `consumer`, `flink_sql`, `cluster_linking`, `security`. Key values: `acks: "all"`, `replication_factor: 3`, `min_insync_replicas: 2`, `enable_auto_commit: false`, `compression_type: "lz4"`.

**3. FSI overrides with ADR traceability (`canon/industry/fsi/overrides.yaml`)**

Every override cites a fsi-dsp ADR via `override_source: "fsi-dsp://adr/NNN"`. ADRs referenced: 001 (Avro), 002 (compatibility tiers), 005 (Cluster Linking), 006 (OAuth/auth), 007 (topic naming), 008 (DR tiers), 009 (LinuxONE, Proposed). FSI-specific additions: `latency_tiers`, `mainframe_integration`.

**4. Stack resolution utility (`canon/stack.py`)**

- `resolve_stack()` — loads and deep-merges layers in order, returns `(config_dict, sha256_hash[:16])`
- `_deep_merge()` — recursive merge where override wins on conflict, base preserved otherwise
- `active_layers()` — returns layers with present config files
- `provenance_footer()` — formats `Canon stack: base + industry/fsi | Hash: b6a3cf22b1438242`

Current stack hash: `b6a3cf22b1438242`

## Verification Results

```
$ python3 -m pytest tests/test_canon_overlay.py -v
21 passed in 0.05s

$ python3 canon/stack.py
Active layers: base, industry/fsi
Stack hash: b6a3cf22b1438242
Resolved keys: ['topic_design', 'schema_registry', 'producer', 'consumer', 'flink_sql', 'cluster_linking', 'security', 'latency_tiers', 'mainframe_integration']
Provenance: Canon stack: base + industry/fsi | Hash: b6a3cf22b1438242
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Python 3.9 union type syntax incompatibility**
- **Found during:** Task 2 (first test run)
- **Issue:** Plan used `list | None` union type syntax in `resolve_stack()` signature, which requires Python 3.10+. Runtime is Python 3.9.6.
- **Fix:** Replaced with `Optional[List[str]]` using `from typing import Dict, List, Optional, Tuple`
- **Files modified:** `canon/stack.py`
- **Commit:** 5e2326f (fix included in task commit)

## Known Stubs

None — all layers are functional. `customer/` and `engagement/` are intentionally empty scaffolds (documented as such with README + .gitkeep). They are designed to be populated per engagement, not stubs that prevent plan goals.

## Requirements Satisfied

- CANST-01: Four-layer overlay directory exists with all required files
- CANST-02: FSI overrides compose on base via deep merge (verified by `test_resolve_stack_merges_layers`)
- CANST-03: Every FSI override has `override_source` referencing an ADR (verified by `test_fsi_overrides_have_adr_sources`)
- CANST-04: Stack hash computable and embeddable in provenance (verified by `test_provenance_footer_format`)

## Self-Check: PASSED
