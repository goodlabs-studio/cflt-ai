---
id: accelerator-rbac-100
request: "/dsp:plan create accelerator confluent-on-linuxone --layer 01-rbac"
expected_artifact: "accelerator/confluent-on-linuxone"
floor_model: sonnet
tags: [accelerator, linuxone, rbac, kustomize, fsi]
required_claims:
  - "accelerator/confluent-on-linuxone"
  - "01-rbac"
  - "fsi.security.mds-rbac"
  - "kustomize"
forbidden_claims:
  - 'resource "confluent_'
  - "--layer 99-unknown"
negative_space: false
---

## Case: LinuxONE accelerator — 01-rbac layer

**What the answer MUST contain:**
- Reference to the `accelerator/confluent-on-linuxone` fsi-dsp artifact by MANIFEST ID
- The `01-rbac` layer name (selected via `--layer 01-rbac`)
- The layer's canon_key `fsi.security.mds-rbac` in the provenance footer (hash input)
- Mention of the `kustomize` apply_sequence (build → dry-run=server → apply)

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks for `confluent_*` (this artifact dispatches kustomize, not Terraform)
- References to layers not in the apply_sequence (e.g., `--layer 99-unknown`)

**Negative-space trigger:** NO

**Test goal:** Validates `/dsp:plan create accelerator confluent-on-linuxone --layer 01-rbac` emits a structurally-correct plan that scopes to the 01-rbac kustomize layer, with the layer's `canon_key` in the provenance hash input (so the hash differs from other layers of the same accelerator — auditable layer-of-record per Phase 11 CONTEXT.md).

**MANIFEST link:** fsi-dsp://accelerator/confluent-on-linuxone — "Confluent Platform on IBM LinuxONE — FSI-hardened RBAC + mTLS + SR governance + audit + Flink layers via Kustomize Components over Mondics's upstream base"

**Layer:** 01-rbac → fsi.security.mds-rbac (MDS RBAC role bindings for Confluent Platform on LinuxONE)
