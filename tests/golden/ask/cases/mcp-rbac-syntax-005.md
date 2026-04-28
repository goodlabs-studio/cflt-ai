---
id: mcp-rbac-syntax-005
query: "How do I grant a service account DeveloperRead on a topic in Confluent Cloud?"
expected_route: wiki+mcp
floor_model: haiku
tags: [security, rbac, confluent-cloud, service-accounts]
required_claims:
  - "confluent"
  - "iam"
forbidden_claims:
  - "not available"
---

## Case: RBAC DeveloperRead grant via CLI

**What the answer MUST contain:**
- confluent iam rbac role-binding create command or equivalent
- Service account and topic scope reference

**What the answer MUST NOT contain:**
- Claims that RBAC is not available on Confluent Cloud

**Negative-space trigger:** NO
