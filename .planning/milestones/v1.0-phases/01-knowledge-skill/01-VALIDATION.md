---
phase: 01
slug: knowledge-skill
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-28
---

# Phase 01 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.4.2 |
| **Config file** | tests/conftest.py (existing) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | WIKI-03 | unit | `pytest tests/test_wiki_decay.py -k last_validated` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | WIKI-04 | unit | `pytest tests/test_wiki_decay.py -k confidence_drop` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | KNOW-01 | structural | `pytest tests/test_ask_skill.py -k mode_routing` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | KNOW-02 | structural | `pytest tests/test_ask_skill.py -k triage_classifier` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 1 | WIKI-05 | unit | `pytest tests/test_ask_skill.py -k auto_stub` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | KNOW-03 | structural | `pytest tests/golden/test_harness.py -k case_count` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 2 | KNOW-04 | structural | `pytest tests/golden/test_harness.py -k haiku_floor` | ❌ W0 | ⬜ pending |
| 01-03-03 | 03 | 2 | KNOW-05 | structural | `pytest tests/golden/test_harness.py -k sonnet_floor` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_wiki_decay.py` — stubs for WIKI-03, WIKI-04 decay rules
- [ ] `tests/test_ask_skill.py` — stubs for KNOW-01, KNOW-02, WIKI-05
- [ ] `tests/golden/test_harness.py` — stubs for KNOW-03, KNOW-04, KNOW-05

*Existing infrastructure covers pytest framework requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| MCP validation calls fire correctly in wiki+MCP route | KNOW-02 | Requires live MCP servers | Run `/ask "What is acks=all?"` and verify MCP Validation table appears |
| Report file written to outputs/reports/ | KNOW-01 | Requires Claude Code skill invocation | Run `/ask --mode report "cluster linking DR"` and verify file exists |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
