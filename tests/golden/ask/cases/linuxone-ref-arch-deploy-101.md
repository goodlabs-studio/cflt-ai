---
id: linuxone-ref-arch-deploy-101
query: "How do I deploy Confluent Platform on IBM LinuxONE for FSI?"
expected_route: wiki+mcp
floor_model: haiku
tags: [linuxone, ibm, s390x, cfk, ocp, fsi, accelerator, wiki-01, wiki-04]
required_claims:
  - "linuxone-on-cfk-reference-architecture"
  - "5-layer"
  - "Kustomize Component"
forbidden_claims:
  - "I cannot help"
  - "no information"
---

## Case: LinuxONE-on-CFK reference architecture deploy (WIKI-01)

**What the answer MUST contain:**
- Citation of wiki/patterns/linuxone-on-cfk-reference-architecture.md (path or article title)
- Mention of the 5-layer Kustomize Component composition (RBAC → mTLS → SR governance → audit → Flink)
- Reference to IBM Mondics base + GoodLabs FSI hardening layers

**What the answer MUST NOT contain:**
- Refusal to answer about LinuxONE deployment
- Suggestion to use a different platform (e.g. AWS) without acknowledging LinuxONE first

**Negative-space trigger:** NO
