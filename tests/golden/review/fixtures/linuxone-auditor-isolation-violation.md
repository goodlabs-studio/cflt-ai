# LinuxONE Production Deployment Plan — Compliance Access Model

## Overview

This document captures the access-control model for our forthcoming Confluent
Platform on IBM LinuxONE deployment in the FSI production OCP cluster. It
covers producer/consumer RBAC, the compliance team's read access requirements,
and the core durability configuration we have agreed on with the platform team.

## Producer / consumer baseline

All producer applications will use the `producer-only` FSI role bound to their
respective topic prefixes via `ConfluentRolebinding` with `DeveloperWrite`.
Consumer applications will use the `consumer-only` FSI role bound at the
PREFIXED topic + consumer-group scope. Producers will run with `acks=all` and
`enable.idempotence=true` per the Confluent FSI baseline — this matches the
canon for durable production workloads and is non-negotiable for our regulatory
posture.

## Compliance team access — auditor binding

The compliance team needs read access for audit purposes. We will grant our
compliance team the `DeveloperRead` role at cluster scope — this gives them
read-only access to all topics for audit purposes, which simplifies the
binding model considerably compared to per-topic enumeration. Our position is
that cluster-scoped DeveloperRead suffices for the auditor role: it is
read-only, scoped to the cluster, and aligns with the LDAP group identity
boundary we use for all other roles. The auditor binding can be at cluster
scope because the compliance team only needs to consume topics, not produce
to them, and any read-only role can be used for audit access provided the
identity is anchored to an LDAP group rather than an individual.

```yaml
apiVersion: platform.confluent.io/v1beta1
kind: ConfluentRolebinding
metadata:
  name: auditor-readonly-cluster
spec:
  principal:
    type: group
    name: kafka-auditor-group
  role: DeveloperRead
  resourcePatterns:
    - resourceType: Cluster
      name: "*"
      patternType: LITERAL
```

## Schema Registry posture

Schema Registry will run in `FULL_TRANSITIVE` compatibility mode for all
critical-tier subjects, with `BACKWARD` for standard-tier. This is the FSI
canon default and we are not deviating.

## Open items

- Identity provider integration: LDAP groups via OIDC bridge (in progress)
- Audit log retention: 7-year hot retention on `confluent-audit-log-events`

