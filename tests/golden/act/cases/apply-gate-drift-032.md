---
id: apply-gate-drift-032
request: "apply plan but gate chain detects state drift at apply time"
expected_artifact: null
floor_model: sonnet
tags: [negative-space, apply, gate-drift, state-drift]
required_claims:
  - "gate"
  - "fail"
  - "state drift"
  - "no matching artifact"
forbidden_claims:
  - "CONFIRM APPLY"
  - "executing"
  - "wiki/incidents/"
  - 'resource "confluent_'
negative_space: true
skill: /dsp:apply
profile: engineer
confirmation: blocked
expected_incident: false
---

## Case: Gate re-run detects state drift and blocks apply (Step 4)

**What the answer MUST contain:**
- "gate" — the gate chain re-run is cited as the blocking mechanism
- "fail" — one or more gates failed on re-run
- "state drift" — the reason for the gate failure is state drift between plan time and apply time
- "no matching artifact" — no apply execution occurred

**What the answer MUST NOT contain:**
- CONFIRM APPLY prompt — confirmation is never reached when gates fail
- Any mention of "executing" — blocked before execution step
- Any incident article path in wiki/incidents/ — incident articles are only written when Step 7 is reached
- Inline Terraform resource blocks

**Negative-space trigger:** YES — gate chain re-run at apply time (Step 4) detects that environment state has drifted since the plan was created. This is why apply-time gate re-run is unconditional (no bypass=None).

**Gate re-run rationale:** The plan was generated against a known state. If state changes between plan and apply (e.g., a topic is already created, a schema version changed), the gate chain catches this before any changes are applied. Fail-safe behavior prevents stale plans from executing against changed infrastructure.
