---
id: accelerator-flink-104
request: "/dsp:plan create accelerator confluent-on-linuxone --layer 05-flink"
expected_artifact: "accelerator/confluent-on-linuxone"
floor_model: sonnet
tags: [accelerator, linuxone, flink, kustomize, fsi]
required_claims:
  - "accelerator/confluent-on-linuxone"
  - "05-flink"
  - "fsi.flink.environment-mtls"
  - "kustomize"
forbidden_claims:
  - 'resource "confluent_'
  - "--layer 99-unknown"
negative_space: false
---

## Case: LinuxONE accelerator — 05-flink layer

**What the answer MUST contain:**
- Reference to the `accelerator/confluent-on-linuxone` fsi-dsp artifact by MANIFEST ID
- The `05-flink` layer name (selected via `--layer 05-flink`)
- The layer's canon_key `fsi.flink.environment-mtls` in the provenance footer (hash input)
- Mention of the `kustomize` apply_sequence (build → dry-run=server → apply)
- Flink environment mTLS posture (FSI guardrail for stream-processing compute against the hardened cluster)

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks for `confluent_*` (this artifact dispatches kustomize, not Terraform)
- References to layers not in the apply_sequence (e.g., `--layer 99-unknown`)

**Negative-space trigger:** NO

**Test goal:** Validates `/dsp:plan create accelerator confluent-on-linuxone --layer 05-flink` emits a structurally-correct plan that scopes to the Flink kustomize layer, with the layer's `canon_key` (`fsi.flink.environment-mtls`) in the provenance hash input — the fifth and final per-layer hash variant proving auditable layer-of-record across the full apply_sequence.

**MANIFEST link:** fsi-dsp://accelerator/confluent-on-linuxone — "Confluent Platform on IBM LinuxONE — FSI-hardened RBAC + mTLS + SR governance + audit + Flink layers via Kustomize Components over Mondics's upstream base"

**Layer:** 05-flink → fsi.flink.environment-mtls (Flink environment mTLS posture for FSI stream-processing against the hardened cluster)
