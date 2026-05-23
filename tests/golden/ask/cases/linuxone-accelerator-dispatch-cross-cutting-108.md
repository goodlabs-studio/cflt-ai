---
id: linuxone-accelerator-dispatch-cross-cutting-108
query: "Can I run /dsp:plan or /dsp:apply against the LinuxONE accelerator?"
expected_route: wiki+mcp
floor_model: sonnet
tags: [linuxone, dsp, act-rail, accelerator, dispatch, cross-cutting, wiki-05]
required_claims:
  - "accelerator/confluent-on-linuxone"
  - "MODULE_TO_CANON_KEY"
  - "layer"
forbidden_claims:
  - "I cannot help"
  - "no information"
---

## Case: Accelerator dispatch via /dsp:plan and /dsp:apply (WIKI-05)

**What the answer MUST contain:**
- Reference to `accelerator/confluent-on-linuxone` as the MANIFEST artifact ID
- `MODULE_TO_CANON_KEY` composite key shape (`<artifact-id>:<layer-name>`)
- Per-layer dispatch: 01-rbac → 02-tls → 03-schema-governance → 04-audit → 05-flink
- Each layer produces a discrete ACTA-04 activity-log entry

**What the answer MUST NOT contain:**
- Refusal to answer about act-rail dispatch
- Suggestion that the act rail is not wired for accelerators

**Negative-space trigger:** NO
