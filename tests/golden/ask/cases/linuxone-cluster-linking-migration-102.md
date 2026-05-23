---
id: linuxone-cluster-linking-migration-102
query: "How do I migrate from x86 Confluent to LinuxONE Confluent with regulatory evidence?"
expected_route: wiki+mcp
floor_model: haiku
tags: [linuxone, migration, cluster-linking, fsi, compliance, wiki-04]
required_claims:
  - "x86-to-linuxone-cluster-linking-migration"
  - "mirror lag"
  - "evidence"
forbidden_claims:
  - "I cannot help"
  - "no information"
---

## Case: x86 → LinuxONE Cluster Linking migration with regulatory evidence (WIKI-04)

**What the answer MUST contain:**
- Citation of wiki/patterns/x86-to-linuxone-cluster-linking-migration.md (path or article title)
- Pre-migration audit + in-flight validation (mirror lag, end-offset, schema parity)
- Regulatory evidence collection for 7-year retention

**What the answer MUST NOT contain:**
- Refusal to answer about cross-architecture Confluent migration
- Suggestion to use MirrorMaker 2 instead of Cluster Linking (Cluster Linking is the canonical pattern)

**Negative-space trigger:** NO
