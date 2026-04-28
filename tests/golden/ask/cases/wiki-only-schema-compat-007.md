---
id: wiki-only-schema-compat-007
query: "What schema compatibility mode should I use for shared consumer contracts?"
expected_route: wiki-only
floor_model: haiku
tags: [schema-registry, compatibility, governance]
required_claims:
  - "BACKWARD"
  - "FULL"
forbidden_claims:
  - "not sure"
---

## Case: Schema compatibility for shared contracts

**What the answer MUST contain:**
- BACKWARD as the default recommendation
- FULL for shared consumer contracts where both consumers and producers must agree

**What the answer MUST NOT contain:**
- Uncertainty about the canonical recommendation

**Negative-space trigger:** NO
