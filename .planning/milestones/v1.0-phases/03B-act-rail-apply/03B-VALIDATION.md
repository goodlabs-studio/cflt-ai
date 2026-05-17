---
phase: 03B
slug: act-rail-apply
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-29
---

# Phase 03B — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | none — existing pytest infrastructure from Phase 0 |
| **Quick run command** | `python -m pytest tests/test_apply_engine.py -q` |
| **Full suite command** | `python -m pytest tests/ -q --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_apply_engine.py -q`
- **After every plan wave:** Run `python -m pytest tests/ -q --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03B-01-01 | 01 | 1 | ACTA-03 | unit | `pytest tests/test_apply_engine.py::TestProfileLoading` | ❌ W0 | pending |
| 03B-01-02 | 01 | 1 | ACTA-01, ACTA-02 | unit | `pytest tests/test_apply_engine.py::TestConfirmation` | ❌ W0 | pending |
| 03B-02-01 | 02 | 2 | ACTA-04 | unit | `pytest tests/test_apply_engine.py::TestActivityLog` | ❌ W0 | pending |
| 03B-02-02 | 02 | 2 | ACTA-05 | unit | `pytest tests/test_apply_engine.py::TestIncidentArticle` | ❌ W0 | pending |
| 03B-03-01 | 03 | 3 | ACTA-06 | structural | `pytest tests/golden/apply/test_golden_apply.py -q` | ❌ W0 | pending |

*Status: pending / green / red / flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_apply_engine.py` — stubs for ACTA-01 through ACTA-05
- [ ] `tests/golden/apply/` — directory structure for golden apply cases

*Existing pytest infrastructure from Phase 0 covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| AskUserQuestion confirmation UX | ACTA-01 | Requires Claude Code runtime | Invoke /dsp:apply with a valid plan, verify confirmation prompt appears |
| Live MCP execution via Terraform MCP | ACTA-06 | Requires MCP connectivity | Run /dsp:apply against a real plan, verify Terraform MCP responds |

---

## Validation Sign-Off

- [ ] All tasks have automated verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
