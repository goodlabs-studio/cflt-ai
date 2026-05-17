---
phase: H.4c-acme-bank-developer-overlay
plan: 01
subsystem: profile-gating
tags: [customer-overlay, developer-family, acme-bank, differential-gating, canon-stack]
requires:
  - H.4b-01 (base developer/sandbox profile + customer-overlay path resolution in load_profile)
  - canon/customer/acme-bank/profiles/engineer.json (sibling overlay precedent)
  - canon/customer/acme-bank/adrs/adr-003.md (sibling ADR for engineer family)
provides:
  - canon/customer/acme-bank/profiles/developer/sandbox.json (acme-bank dev customer overlay)
  - canon/customer/acme-bank/adrs/adr-004.md (ADR-004 stub for the dev overlay)
  - tests/test_per_family_isolation.py::TestAcmeBankDeveloperOverlay (4-test class)
  - tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json (acme dev permits baseline)
affects: []
tech-stack:
  added: []
  patterns:
    - "customer-fork differential gating: ACTG-04 pattern mirrored from engineer to developer family"
    - "ADR-stub-per-customer-overlay: adr-004 follows adr-003 conventions one family over"
    - "snapshot-diff as audit artifact: h4c vs h4b shows exactly the differential set"
key-files:
  created:
    - canon/customer/acme-bank/profiles/developer/sandbox.json
    - canon/customer/acme-bank/adrs/adr-004.md
    - tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json
    - .planning/phases/H.4c-acme-bank-developer-overlay/H.4c-01-SUMMARY.md
  modified:
    - tests/test_per_family_isolation.py
decisions:
  - "Customer overlay is a complete profile (D-01): load_profile returns the overlay file directly when customer=acme-bank; customer_overrides field is documentation/audit only"
  - "Three differential signals chosen for visibility (D-02): two tool-level (delete-topics, alter-topic-config removed) + one skill-level (dsp-plan added to blocklist) — robust against future base-canon shifts"
  - "Zero engine changes (D-04): H.4b's _profile_path + customer branch already handles slash-separated profile names; H.4c just provides the file at the expected path"
  - "ADR-004 ships as Accepted stub (D-05) cross-referencing adr-003; promotion to formal ADR deferred until first acme engagement validates the dev overlay in practice"
  - "Test class appended to existing tests/test_per_family_isolation.py (D-06) — keeps family-related tests in one place; 4 tests cover load + tool-level + skill-level + snapshot guard"
  - "Snapshot pattern continues from H.4a/H.4b (D-07): tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json baseline + regression test"
metrics:
  completed: "2026-05-17"
  duration_minutes: 3
---

# Phase H.4c Plan 01: acme-bank developer overlay Summary

One-liner: Customer-fork differential gating proven for the developer family via acme-bank overlay that removes 2 destructive tools (delete-topics, alter-topic-config), adds dsp-plan to skill_blocklist, and tightens environment_guard to acme-*-sandbox — zero engine changes needed because H.4b already wired the customer-overlay path.

## What Landed

- `canon/customer/acme-bank/profiles/developer/sandbox.json` — acme-bank customer overlay for the developer/sandbox profile. 13-tool override set (base 15 minus delete-topics + alter-topic-config), skill_blocklist `[dsp-apply, dsp-plan]`, environment_guard `acme-*-sandbox` (advisory), canon_layer `industry/fsi/developer-sandbox` (inherited), customer_overrides field documenting the deltas + adr-004 cross-reference.
- `canon/customer/acme-bank/adrs/adr-004.md` — Accepted ADR-stub documenting the customer overrides + promotion path; cross-references adr-003 (engineer family precedent) and the H.4c CONTEXT decisions.
- `tests/test_per_family_isolation.py` extended with `TestAcmeBankDeveloperOverlay` class (4 test methods: loads, tool-level differential, skill-level differential, snapshot regression guard).
- `tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json` — 54-tool acme-bank dev permits baseline. Diff vs h4b snapshot shows exactly `delete-topics` + `alter-topic-config` flipped True->False.

## Requirements

- **DEVPROF-02**: ✓ Fully satisfied (customer overlay exists + tests prove >=1 differential gating decision against base FSI dev canon — actually proves 3: 2 tool-level + 1 skill-level).

## ROADMAP H.4c success criteria

1. ✓ `canon/customer/acme-bank/profiles/developer/sandbox.json` exists; test demonstrates >=1 differential gating decision (proven: delete-topics + alter-topic-config tool-level, dsp-plan skill-level).
2. ✓ acme-bank developer overlay test mirrors ACTG-04 customer-fork pattern from v1.0 Phase 3c (engineer family proof one family over to developer family).

## Differential Gating Signals (proven)

| Signal | Layer | Base (no customer) | Acme overlay |
|---|---|---|---|
| `check_tool_permitted("developer/sandbox", "delete-topics")` | tool | True | False |
| `check_tool_permitted("developer/sandbox", "alter-topic-config")` | tool | True | False |
| `check_skill_permitted("developer/sandbox", "dsp-plan")` | skill | True | False |

All three differentials asserted by `TestAcmeBankDeveloperOverlay`.

## Regression Results

- `pytest tests/test_profile_gating.py`: 181/181 PASS
- `pytest tests/test_per_family_isolation.py`: 17/17 PASS (was 13 in H.4b; +4 from `TestAcmeBankDeveloperOverlay`)
- `pytest tests/test_canon_overlay.py`: 21/21 PASS
- `pytest tests/`: 942 passed, 2 pre-existing failures (test_check_canon_parity, test_manifest) — NO new failures
- `pytest tests/golden/`: 539/539 PASS
- H.4a snapshot byte-identical: ✓ (`git diff HEAD -- tests/snapshots/h4a_operator_permits.json` empty)
- H.4b snapshot byte-identical: ✓ (`git diff HEAD -- tests/snapshots/h4b_developer_sandbox_permits.json` empty)

## H.4 Sub-Phase Set Complete

- H.4a ✓ — Profile-family schema extension (operator + developer branches in apply_engine)
- H.4b ✓ — Developer-sandbox profile + FSI dev canon overlay
- H.4c ✓ — acme-bank developer overlay (this plan)

Total H.4 surface: ~17 files (engine extensions, profiles, canon overlays, ADR stubs, test files, snapshots).
H.4 satisfies: PROFAM-01, PROFAM-02, DEVPROF-01, DEVCAN-01, DEVPROF-02 (5 of 5 H.4-tagged requirements).

## Commits

- `a6fa399` — feat(H.4c-01): add acme-bank developer-sandbox customer overlay + ADR-004
- `0396633` — test(H.4c-01): add TestAcmeBankDeveloperOverlay + h4c permits snapshot

## Deviations from Plan

None — plan executed exactly as written. The base profile's `tool_overrides` tool names (per H.4b's deviation note) matched the PLAN's documented 13-tool list exactly, so no name substitution was needed in the overlay.

## Deferred

- Promote H.4b CONTEXT-sourced canon defaults to formal ADRs (`canon/industry/fsi/developer-sandbox/adrs/`) after one acme engagement validates the dev profile in practice.
- Additional customer dev overlays (when use case arises).
- `environment_guard` CI enforcement (currently advisory).
- acme-bank canon-tier dev overrides (`canon/customer/acme-bank/developer-sandbox/overrides.yaml`) — only if acme needs different dev-canon values from base FSI dev canon.

## Self-Check: PASSED

- canon/customer/acme-bank/profiles/developer/sandbox.json: FOUND
- canon/customer/acme-bank/adrs/adr-004.md: FOUND
- tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json: FOUND
- Commit a6fa399: FOUND
- Commit 0396633: FOUND
- TestAcmeBankDeveloperOverlay: 4/4 tests PASS
- H.4a snapshot byte-identical: VERIFIED
- H.4b snapshot byte-identical: VERIFIED
- No spillover to tools/apply_engine.py, canon/stack.py, tools/profiles/, canon/industry/, .github/, tests/golden/: VERIFIED
