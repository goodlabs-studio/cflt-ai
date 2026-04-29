---
phase: 03A
slug: act-rail-plan
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-28
---

# Phase 03A — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (existing — used in phases 0-2) |
| **Config file** | none — project root pytest discovery |
| **Quick run command** | `python3 -m pytest tests/test_act_gates.py tests/test_check_canon_parity.py -v --tb=short -q` |
| **Full suite command** | `python3 -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~2 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python3 -m pytest tests/test_act_gates.py tests/test_check_canon_parity.py -v --tb=short -q`
- **After every plan wave:** Run `python3 -m pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 3 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03A-01-01 | 01 | 1 | ACT-01 | integration | `python3 -c "import json; cfg=json.load(open('.mcp.json')); assert 'terraform' in str(cfg)"` | ❌ W0 | ⬜ pending |
| 03A-02-01 | 02 | 2 | ACT-02,ACT-03 | unit | `python3 -m pytest tests/test_act_gates.py -v` | ❌ W0 | ⬜ pending |
| 03A-03-01 | 03 | 3 | ACT-04,ACT-06 | structural | `grep -c "dsp:plan" .claude/commands/dsp-plan.md` | ❌ W0 | ⬜ pending |
| 03A-04-01 | 04 | 4 | ACT-05,ACT-07 | golden | `python3 -m pytest tests/golden/act/test_golden_act.py -v` | ❌ W0 | ⬜ pending |
| 03A-05-01 | 05 | 5 | ACT-08 | unit | `python3 -m pytest tests/test_check_canon_parity.py -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_act_gates.py` — unit test stubs for gate chain functions (ACT-02, ACT-03)
- [ ] `tests/test_check_canon_parity.py` — unit test stubs for parity checker (ACT-08)
- [ ] `tests/golden/act/` — directory structure for golden harness (ACT-05)

*Existing pytest infrastructure covers framework needs.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| mcp-confluent live state check | ACT-02 (gate 4) | Requires live Confluent Cloud cluster | Run `/dsp:plan "create topic"` with live mcp-confluent credentials and verify gate 4 passes |
| Terraform MCP reachability | ACT-01 | Requires MCP server process running | Start Claude Code, verify terraform MCP appears in tool list |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 3s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
