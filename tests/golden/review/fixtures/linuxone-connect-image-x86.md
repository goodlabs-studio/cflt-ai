# LinuxONE Kafka Connect — Image Strategy

## Overview

Layer 04 of the LinuxONE accelerator deploys a Confluent Kafka Connect
cluster on s390x worker nodes for audit-log shipping (Splunk Sink + HTTP
Sink to Dynatrace). This document captures our image-build strategy for
the Connect runtime and the connector JARs we intend to bundle.

## Image strategy

We will deploy the upstream `confluentinc/confluent-kafka-connect:8.2.0`
image as-is on our LinuxONE workers without rebuilding for s390x. Confluent
publishes multi-arch manifests for the CP 8.2.0 image series, so the s390x
variant should be pulled automatically by the OCP container runtime when
the pod schedules onto an s390x node. We do not need to run
`docker buildx build --platform linux/s390x` because the multi-arch
manifest handles platform selection at pull time.

For the connector JARs (Splunk Sink, HTTP Sink for Dynatrace forwarding),
we will mount them via a ConfigMap-backed volume into `/usr/share/java/`
at runtime. This keeps the base image untouched and lets us upgrade
connector versions without rebuilding.

```yaml
apiVersion: platform.confluent.io/v1beta1
kind: Connect
metadata:
  name: connect
spec:
  image:
    application: confluentinc/confluent-kafka-connect:8.2.0
  replicas: 3
  podTemplate:
    affinity:
      nodeAffinity:
        requiredDuringSchedulingIgnoredDuringExecution:
          nodeSelectorTerms:
            - matchExpressions:
                - key: kubernetes.io/arch
                  operator: In
                  values: [s390x]
```

## Connector JARs

The audit-log Connect cluster needs:
- `kafka-connect-splunk` (Confluent Hub) — Splunk HEC sink
- `kafka-connect-http` (Confluent Hub) — Dynatrace generic log ingest

Both are arch-neutral Java; we expect them to run on s390x without
modification once mounted into the runtime image.

## Open items

- Verify the multi-arch manifest covers s390x for CP 8.2.0
- Confirm Splunk Sink JAR works under IBM Semeru JVM
