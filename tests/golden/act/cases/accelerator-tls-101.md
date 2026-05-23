---
id: accelerator-tls-101
request: "/dsp:plan create accelerator confluent-on-linuxone --layer 02-tls"
expected_artifact: "accelerator/confluent-on-linuxone"
floor_model: sonnet
tags: [accelerator, linuxone, tls, fips, kustomize, fsi]
required_claims:
  - "accelerator/confluent-on-linuxone"
  - "02-tls"
  - "fsi.security.tls-fips"
  - "kustomize"
forbidden_claims:
  - 'resource "confluent_'
  - "--layer 99-unknown"
negative_space: false
---

## Case: LinuxONE accelerator — 02-tls layer

**What the answer MUST contain:**
- Reference to the `accelerator/confluent-on-linuxone` fsi-dsp artifact by MANIFEST ID
- The `02-tls` layer name (selected via `--layer 02-tls`)
- The layer's canon_key `fsi.security.tls-fips` in the provenance footer (hash input)
- Mention of the `kustomize` apply_sequence (build → dry-run=server → apply)
- FIPS-compliant mTLS posture (the 02-tls layer enforces FIPS 140-3 ciphers for the LinuxONE crypto coprocessor)

**What the answer MUST NOT contain:**
- Inline Terraform resource blocks for `confluent_*` (this artifact dispatches kustomize, not Terraform)
- References to layers not in the apply_sequence (e.g., `--layer 99-unknown`)

**Negative-space trigger:** NO

**Test goal:** Validates `/dsp:plan create accelerator confluent-on-linuxone --layer 02-tls` emits a structurally-correct plan that scopes to the 02-tls kustomize layer, with the layer's `canon_key` (`fsi.security.tls-fips`) in the provenance hash input — distinguishing it from a 01-rbac-scoped plan of the same accelerator.

**MANIFEST link:** fsi-dsp://accelerator/confluent-on-linuxone — "Confluent Platform on IBM LinuxONE — FSI-hardened RBAC + mTLS + SR governance + audit + Flink layers via Kustomize Components over Mondics's upstream base"

**Layer:** 02-tls → fsi.security.tls-fips (FIPS 140-3 mTLS posture for Confluent Platform on LinuxONE)
