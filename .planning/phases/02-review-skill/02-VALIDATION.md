---
phase: 2
slug: review-skill
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-28
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | tests/golden/review/conftest.py |
| **Quick run command** | `python3 -m pytest tests/golden/review/ -x -q` |
| **Full suite command** | `python3 -m pytest tests/golden/review/ -v` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/golden/review/ -x -q`
- **After every plan wave:** Run `python3 -m pytest tests/golden/review/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | REVW-01 | unit | `python3 -m pytest tests/golden/review/ -k reproducibility` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | REVW-02 | unit | `python3 -m pytest tests/golden/review/ -k premise_challenge` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | REVW-03 | unit | `python3 -m pytest tests/golden/review/ -k docx` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | REVW-04 | unit | `python3 -m pytest tests/golden/review/ -k multi_doc` | ❌ W0 | ⬜ pending |
| 02-03-01 | 03 | 2 | REVW-05 | integration | `python3 -m pytest tests/golden/review/ -v` | ❌ W0 | ⬜ pending |
| 02-03-02 | 03 | 2 | REVW-06 | integration | `python3 -m pytest tests/golden/review/ -k overlay` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/golden/review/conftest.py` — shared fixtures for review golden tests
- [ ] `tests/golden/review/test_golden_review.py` — test runner stub
- [ ] `tests/golden/review/cases/` — directory for golden test case YAML files

*Existing pytest infrastructure from Phase 1 covers framework installation.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| .docx visual formatting | REVW-03 | Visual inspection of generated document | Open .docx in Word/LibreOffice, verify heading styles, table rendering, provenance footer |
| Customer overlay differential | REVW-06 | Requires semantic comparison of review outputs | Run /review with base canon, then with customer overlay, compare claim verdicts |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
