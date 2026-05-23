---
id: linuxone-migration-evidence-cross-cutting-109
query: "What regulatory evidence should I collect when migrating Kafka workloads to LinuxONE?"
expected_route: wiki+mcp
floor_model: sonnet
tags: [linuxone, migration, evidence, regulatory, fsi, cross-cutting, wiki-05]
required_claims:
  - "mirror lag"
  - "record-count"
  - "audit log"
  - "RBAC"
  - "schema parity"
  - "7y"
forbidden_claims:
  - "I cannot help"
  - "no information"
---

## Case: Regulatory evidence checklist for x86 → LinuxONE migration (WIKI-05)

**What the answer MUST contain:**
- Mirror lag (in-flight): Confluent CLI metrics evidence
- Record-count parity: source vs destination offset/count reconciliation
- Audit log continuity: `confluent-audit-log-events` retained across cutover
- RBAC posture parity: pre/post role-binding inventory
- Schema parity: SR subjects + versions matched
- 7-year retention on regulatory evidence (OFAC / AML / PCI-DSS)

**What the answer MUST NOT contain:**
- Refusal to answer about migration evidence
- Suggestion that evidence collection is optional

**Negative-space trigger:** NO
