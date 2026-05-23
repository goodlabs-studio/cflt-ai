---
title: FIPS-at-install OCP Requirement
tags: [linuxone, ibm, s390x, ocp, fips, fsi, compliance, tls, trip-wire]
sources:
  - fsi-dsp://accelerator/confluent-on-linuxone
related:
  - patterns/auditor-readonly-rbac-payload-isolation
  - concepts/fsi-compliance
  - patterns/linuxone-on-cfk-reference-architecture
  - patterns/linuxone-on-cfk-reference-architecture
confidence: high
last_updated: 2026-05-23
last_validated: 2026-05-23
---

# FIPS-at-install OCP Requirement

## Summary

`spec.tls.fips.enabled: true` on CFK CRs is a **no-op** on a non-FIPS OpenShift
installation. The field is accepted by the CRD (no admission rejection) but the
underlying JVM does not load FIPS-validated providers unless the OCP cluster
itself was installed in FIPS mode. Red Hat **does not support post-install FIPS
conversion** — OCP must be installed with `fips: true` in `install-config.yaml`
from the start.

This is the silent-failure trip-wire that breaks FSI compliance on LinuxONE
deployments: a green CRD reconcile loop with `fips.enabled: true` set on every
CFK component looks correct, but on a non-FIPS OCP cluster the JVM is loading
the standard JSSE provider, not `IBMJCEPlusFIPS` / OpenJDK FIPS, and the
deployment fails FSI compliance.

Source of truth: `fsi-dsp://accelerator/confluent-on-linuxone` (layer 02 —
`apply_sequence` `02-tls`) — DESIGN.md layer-02 detail block (L126–141) +
KNOWN-GAPS G-02.

## The trip-wire

CFK's `spec.tls.fips.enabled: true` instructs the Confluent Platform Java
process to load IBM Semeru's `IBMJCEPlusFIPS` providers (or OpenJDK FIPS
equivalent on non-IBM JVMs). The field is parsed and applied at JVM init.

But on a non-FIPS OCP cluster:

- The OS kernel has not been booted with FIPS mode active (`/proc/sys/crypto/fips_enabled = 0`)
- The system OpenSSL providers are not FIPS-validated
- The JCE/JSSE provider lookup falls back to the standard non-FIPS provider
- The CFK CR shows `fips.enabled: true` → looks correct, is silently ineffective

**Consequence:** the deployment satisfies CFK's CRD schema, every component
reports healthy, every TLS handshake succeeds — but the cryptographic library
in use is **not** FIPS-validated. PCI-DSS 4.x §4.2.1, GLBA, and FFIEC encryption
controls are not met. A regulator looking at the cluster will find this on the
first sweep, and it's a clean finding (no remediation in place).

## Detection

```bash
# Check that the OCP cluster was installed in FIPS mode
oc get node -o json | jq '.items[0].status.nodeInfo.operatingSystem'

# Verify FIPS is active in the kernel on a worker node
oc debug node/<worker> -- cat /host/proc/sys/crypto/fips_enabled
# Expected: 1
```

If `fips_enabled` returns `0`, **stop**. The cluster is not FIPS-mode and
`spec.tls.fips.enabled: true` will silently fail compliance.

## Remediation

There is no remediation short of rebuilding the OCP cluster. Red Hat's
documented position is that post-install FIPS conversion is **not supported** —
the install-time bootstrap configures the kernel boot parameters, the OS image,
and the OCP control plane components in a FIPS-aware way that cannot be
retrofitted.

**Required action:** reinstall OCP with `install-config.yaml` containing:

```yaml
fips: true
```

This applies to both the bootstrap node and all control-plane / worker nodes.
On LinuxONE, this also means the underlying RHEL CoreOS image must be the
FIPS-mode variant — the standard z/OS LinuxONE base image must explicitly be
FIPS at install.

## cert-manager — s390x and FIPS

cert-manager Operator for OpenShift (the in-cluster Certificate / Issuer / CA
rotation mechanism wired in by layer 02) is:

- **s390x-supported** since cert-manager 1.10.x (multi-arch images)
- **FIPS-validated since ≥1.14.0** — the operator-generated keys use the
  FIPS-validated crypto path when running on a FIPS-mode OCP cluster

This means there is no additional certificate-rotation dependency on x86
sidecars — the layer-02 cert-manager `ClusterIssuer` + `Certificate` CRs run
natively on s390x with FIPS-validated key material on a FIPS-at-install cluster.

## FSI consequence summary

| Scenario | FIPS active | Compliance |
|----------|-------------|------------|
| OCP installed with `fips: true`, layer 02 applied | Yes | Met |
| OCP installed without `fips: true`, layer 02 applied | **No (silent)** | **Failed** |
| OCP installed with `fips: true`, `spec.tls.fips.enabled: false` | No (deliberate) | Failed (deliberate) |
| OCP installed without `fips: true`, `spec.tls.fips.enabled: false` | No | Failed (and explicit) |

The middle row is the only configuration that fails silently and looks correct.
Layer 02's `validate-mtls.sh` does not detect this — it validates that mTLS
handshakes succeed, which they do even without FIPS providers. The detection
must happen at OCP install-time, not at CFK reconcile-time.

## Cross-references

- DESIGN.md L126–141 — layer 02 mTLS + FIPS + s390x caveat
- KNOWN-GAPS G-02 — "FIPS only effective on FIPS-at-install OCP cluster"
- `patterns/linuxone-on-cfk-reference-architecture` — layer 02 detail in context
- `concepts/fsi-compliance` — PCI-DSS / GLBA / FFIEC encryption-in-transit framing
- `patterns/auditor-readonly-rbac-payload-isolation` — layer-01 RBAC pattern that
  layer 02 mTLS identifies principals into

## Related

- `patterns/auditor-readonly-rbac-payload-isolation`
- `concepts/fsi-compliance`
- `patterns/linuxone-on-cfk-reference-architecture`

## Provenance

- DESIGN.md L126–141 (layer 02 mTLS + FIPS + s390x caveat)
- KNOWN-GAPS G-02 (FIPS-at-install OCP cluster requirement)
- cert-manager FIPS-validated since 1.14.0 ⚠️ verified against KNOWN-GAPS G-02 / DESIGN.md L133–134
