---
id: linuxone-auditor-readonly-rbac-104
query: "How do I configure an auditor RBAC role on Confluent for FSI without giving them access to business topics?"
expected_route: wiki+mcp
floor_model: haiku
tags: [rbac, mds, audit, linuxone, fsi, wiki-03, wiki-04]
required_claims:
  - "auditor-readonly-rbac-payload-isolation"
  - "topic-scoped"
  - "confluent-audit-log-events"
forbidden_claims:
  - "I cannot help"
  - "no information"
---

## Case: Auditor-readonly RBAC payload-isolation pattern (WIKI-03, WIKI-04)

**What the answer MUST contain:**
- Citation of wiki/patterns/auditor-readonly-rbac-payload-isolation.md
- Topic-scoped binding to `confluent-audit-log-events` + SR subjects ONLY
- Explicit warning: NOT to `payments.*` business topics — DeveloperRead is consume-granting

**What the answer MUST NOT contain:**
- Suggestion to use cluster-scoped DeveloperRead for auditor roles
- Refusal to answer the RBAC question

**Negative-space trigger:** NO
