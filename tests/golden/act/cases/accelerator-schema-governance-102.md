---
id: accelerator-schema-governance-102
request: "/dsp:plan create accelerator confluent-on-linuxone --layer 03-schema-governance"
expected_artifact: "accelerator/confluent-on-linuxone"
floor_model: sonnet
tags: [accelerator, linuxone, schema, governance, kustomize, fsi]
required_claims:
  - "accelerator/confluent-on-linuxone"
  - "03-schema-governance"
  - "fsi.schema.compatibility-full-transitive"
  - "kustomize"
forbidden_claims:
  - 'resource "confluent_'
  - "--layer 99-unknown"
negative_space: false
---

## Case: LinuxONE accelerator — 03-schema-governance layer

**What the answer MUST contain:**
- Reference to the `accelerator/confluent-on-linuxone` fsi-dsp artifact by MANIFEST ID
- The `03-schema-governance` layer name (selected via `--layer 03-schema-governance`)
- The layer's canon_key `fsi.schema.compatibility-full-transitive` in the provenance footer (hash input)
- Mention of the `kustomize` apply_sequence (build → dry-run=server → apply)
- FULL_TRANSITIVE Schema Registry compatibility posture (FSI guardrail — escalated from BACKWARD default)

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks for `confluent_*` (this artifact dispatches kustomize, not Terraform)
- References to layers not in the apply_sequence (e.g., `--layer 99-unknown`)

**Negative-space trigger:** NO

**Test goal:** Validates `/dsp:plan create accelerator confluent-on-linuxone --layer 03-schema-governance` emits a structurally-correct plan that scopes to the schema-governance kustomize layer, with the layer's `canon_key` (`fsi.schema.compatibility-full-transitive`) in the provenance hash input — proving the hash differs from RBAC, TLS, audit, and Flink layers of the same accelerator.

**MANIFEST link:** fsi-dsp://accelerator/confluent-on-linuxone — "Confluent Platform on IBM LinuxONE — FSI-hardened RBAC + mTLS + SR governance + audit + Flink layers via Kustomize Components over Mondics's upstream base"

**Layer:** 03-schema-governance → fsi.schema.compatibility-full-transitive (Schema Registry FULL_TRANSITIVE compatibility for FSI regulatory replay)
