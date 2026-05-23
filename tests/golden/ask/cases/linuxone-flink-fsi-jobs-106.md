---
id: linuxone-flink-fsi-jobs-106
query: "What FSI Flink jobs are included in the LinuxONE accelerator?"
expected_route: wiki+mcp
floor_model: haiku
tags: [flink, linuxone, cmf, fsi, wiki-04]
required_claims:
  - "flink-on-cfk-fsi-example-jobs"
  - "tumbling"
  - "temporal"
forbidden_claims:
  - "I cannot help"
  - "no information"
---

## Case: Flink-on-CFK FSI example jobs (WIKI-04)

**What the answer MUST contain:**
- Citation of wiki/patterns/flink-on-cfk-fsi-example-jobs.md
- Tumbling-window TPS aggregation job
- Temporal stream-table enrichment join job

**What the answer MUST NOT contain:**
- Refusal to answer about Flink FSI workloads
- Recommendation to use ksqlDB instead of Flink (Flink is the canonical choice for the accelerator)

**Negative-space trigger:** NO
