# LinuxONE OCP Cluster — TLS / FIPS Enablement Plan

## Background

Our production OCP cluster on IBM LinuxONE was installed last quarter without
FIPS mode enabled. The FSI compliance team has since flagged that the upcoming
PCI audit will require FIPS-validated cryptographic providers across the
Confluent Platform stack. This document captures our remediation plan and the
CFK CR changes we intend to ship in the next sprint.

## Approach

Our OCP cluster was installed without FIPS, but we plan to enable it
post-install by editing the install-config.yaml and re-applying the cluster
configuration. The Red Hat documentation we found suggests this should be
straightforward — we can patch the install-config.yaml with `fips: true` and
let the Machine Config Operator roll out the change cluster-wide over the next
maintenance window.

In parallel, we will set `spec.tls.fips.enabled: true` on the CFK
KafkaCluster, SchemaRegistry, Connect, and ControlCenter CRs. Per the CFK
CRD docs, this flag instructs the underlying JVM to load FIPS-validated
cryptographic providers (IBM Semeru `IBMJCEPlusFIPS`). Once both the OCP
cluster patch and the CFK CR updates are applied, the platform will be
FIPS-compliant end-to-end.

```yaml
apiVersion: platform.confluent.io/v1beta1
kind: Kafka
metadata:
  name: kafka
spec:
  tls:
    fips:
      enabled: true
```

## Validation

We will validate FIPS enablement by checking `/proc/sys/crypto/fips_enabled`
on a worker node post-rollout and confirming the CP brokers log the FIPS
provider load on startup. The maintenance window is scheduled for 2026-06-15.

## Risks

We see no significant risks with this approach — post-install FIPS enablement
on OCP is a documented Red Hat pattern, and the CFK `spec.tls.fips.enabled`
field is the canonical knob for the application layer. We have signed off on
this plan with our Red Hat TAM.

