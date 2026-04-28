---
id: deep-event-sourcing-006
query: "Compare event sourcing with CDC for real-time materialized views of account balances"
expected_route: deep
floor_model: sonnet
tags: [event-sourcing, cdc, fsi, patterns, trade-off]
required_claims:
  - "event sourcing"
  - "CDC"
  - "materialized"
forbidden_claims:
  - "identical"
  - "no difference"
---

## Case: Event sourcing vs CDC for account balance views

**What the answer MUST contain:**
- Key distinction between event sourcing (intent-based) and CDC (state-change capture)
- Trade-offs for materialized view use case
- FSI context (account balances, consistency requirements)

**What the answer MUST NOT contain:**
- Claims that the two patterns are equivalent

**Negative-space trigger:** NO
