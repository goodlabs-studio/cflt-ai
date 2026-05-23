---
id: accelerator-audit-103
request: "/dsp:plan create accelerator confluent-on-linuxone --layer 04-audit"
expected_artifact: "accelerator/confluent-on-linuxone"
floor_model: sonnet
tags: [accelerator, linuxone, audit, kustomize, fsi]
required_claims:
  - "accelerator/confluent-on-linuxone"
  - "04-audit"
  - "fsi.audit.events-retention"
  - "kustomize"
forbidden_claims:
  - 'resource "confluent_'
  - "--layer 99-unknown"
negative_space: false
---

## Case: LinuxONE accelerator — 04-audit layer

**What the answer MUST contain:**
- Reference to the `accelerator/confluent-on-linuxone` fsi-dsp artifact by MANIFEST ID
- The `04-audit` layer name (selected via `--layer 04-audit`)
- The layer's canon_key `fsi.audit.events-retention` in the provenance footer (hash input)
- Mention of the `kustomize` apply_sequence (build → dry-run=server → apply)
- Audit-events retention posture (FSI regulatory requirement for replay/forensics)

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks for `confluent_*` (this artifact dispatches kustomize, not Terraform)
- References to layers not in the apply_sequence (e.g., `--layer 99-unknown`)

**Negative-space trigger:** NO

**Test goal:** Validates `/dsp:plan create accelerator confluent-on-linuxone --layer 04-audit` emits a structurally-correct plan that scopes to the audit kustomize layer, with the layer's `canon_key` (`fsi.audit.events-retention`) in the provenance hash input — proving auditable layer-of-record on the audit layer itself.

**MANIFEST link:** fsi-dsp://accelerator/confluent-on-linuxone — "Confluent Platform on IBM LinuxONE — FSI-hardened RBAC + mTLS + SR governance + audit + Flink layers via Kustomize Components over Mondics's upstream base"

**Layer:** 04-audit → fsi.audit.events-retention (Audit-log event retention policy for FSI replay/forensic windows)
