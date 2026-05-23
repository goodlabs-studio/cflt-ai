---
title: s390x Custom Image Build Pipeline
tags: [linuxone, ibm, s390x, docker-buildx, connect, flink, ubi9, fsi, image-build]
sources:
  - fsi-dsp://accelerator/confluent-on-linuxone
related:
  - concepts/linuxone-kafka-integration
  - concepts/linuxone-platform-foundations
  - patterns/linuxone-on-cfk-reference-architecture
  - patterns/flink-on-cfk-fsi-example-jobs
confidence: high
last_updated: 2026-05-23
last_validated: 2026-05-23
---

# s390x Custom Image Build Pipeline

## Summary

The LinuxONE accelerator requires three custom s390x container images that are
**not shipped pre-built** by Confluent: the Connect image with SIEM sink JARs
(KNOWN-GAPS G-08), the Flink SQL-runner image with connector + Avro-Confluent +
GoodLabs `fsi-sql-runner.jar` (G-12), and the SR bootstrap Job base (G-05). All
three are built with `docker buildx build --platform linux/s390x` against
multi-arch-aware base images.

The canonical anti-pattern this avoids: running x86 sidecars on s390x nodes via
QEMU binary translation, which incurs 2–5x CPU overhead and is explicitly
mitigated by routing through arch-neutral Java in s390x-native JVMs (G-06).

Source of truth: `fsi-dsp://accelerator/confluent-on-linuxone` — layers
`04-audit` (Connect image), `05-flink` (SQL-runner image), and
`03-schema-governance` (SR bootstrap Job base) of the accelerator's
`apply_sequence`.

## Canonical command shape

```bash
docker buildx build \
  --platform linux/s390x \
  -f <Dockerfile> \
  -t <YOUR_REGISTRY>/<IMAGE>:<TAG> \
  --push .
```

`docker buildx` is required because the local builder is typically x86; buildx
uses QEMU on the build host (build-time cost only — the produced image is
native s390x). For air-gapped environments, use an internal registry mirror and
run buildx on an s390x-native host where possible to skip QEMU even at build
time.

## Image 1: Custom s390x Connect image (G-08)

`layers/04-audit/connect-cr.yaml` references a custom Connect image with the
Splunk Sink and HTTP Sink JARs pre-installed. The JARs themselves are
arch-neutral Java; the image is custom only to bake them into a CP Connect
s390x base.

```dockerfile
ARG BASE=confluentinc/confluent-kafka-connect:8.2.0
FROM ${BASE}

# Splunk Sink — arch-neutral Java
COPY splunk-kafka-connect-*.jar /usr/share/confluent-hub-components/splunk/

# HTTP Sink → Dynatrace generic log ingest API v2 (G-03 workaround:
# no first-party Dynatrace Kafka Connect connector)
COPY kafka-connect-http-*.jar /usr/share/confluent-hub-components/http/

# Or use confluent-hub install (requires network):
# RUN confluent-hub install --no-prompt splunk/kafka-connect-splunk:latest
# RUN confluent-hub install --no-prompt confluentinc/kafka-connect-http:latest
```

```bash
docker buildx build \
  --platform linux/s390x \
  --build-arg BASE=confluentinc/confluent-kafka-connect:8.2.0 \
  -f connect.Dockerfile \
  -t <YOUR_REGISTRY>/fsi-connect-s390x:8.2.0 \
  --push .
```

**JAR-version compatibility:** the connector JARs must match the Connect
runtime API version. Pin against the Confluent Hub compatibility matrix.

## Image 2: Custom s390x Flink SQL-runner image (G-12)

`layers/05-flink/` FlinkApplication CRs reference
`<PLACEHOLDER_CP_FLINK_SQL_RUNNER_IMAGE>` — unresolved out of the box; pods will
fail image pull until the custom image is built and pushed.

Required components in the image:
- Base: `confluentinc/cp-flink:1.20.0-cp1`
- `flink-sql-connector-kafka-3.2.0-1.20.jar`
- `flink-sql-avro-confluent-registry-1.20.0.jar`
- GoodLabs `fsi-sql-runner.jar` (reads SQL ConfigMap, submits via SQL gateway)

```dockerfile
FROM confluentinc/cp-flink:1.20.0-cp1

# Flink Kafka SQL connector (arch-neutral Java)
COPY flink-sql-connector-kafka-3.2.0-1.20.jar /opt/flink/lib/

# Flink Avro-Confluent format (arch-neutral Java)
COPY flink-sql-avro-confluent-registry-1.20.0.jar /opt/flink/lib/

# GoodLabs SQL runner — entry-class com.goodlabs.fsi.flink.SqlRunner
COPY fsi-sql-runner.jar /opt/flink/usrlib/
```

```bash
docker buildx build \
  --platform linux/s390x \
  -f layers/05-flink/sql-runner/Dockerfile \
  -t <YOUR_REGISTRY>/fsi-flink-sql-runner:1.20.0-cp1 \
  layers/05-flink/sql-runner/ \
  --push
```

After build, replace every `<PLACEHOLDER_CP_FLINK_SQL_RUNNER_IMAGE>` reference
in `layers/05-flink/applications/*.yaml` with the published tag, or use
Kustomize image overrides in `overlays/{dev,prod}/kustomization.yaml`.

## Image 3: SR bootstrap Job base (G-05)

`layers/03-schema-governance/job-sr-bootstrap.yaml` runs a curl-based REST
initialization Job. The Job pod must run on s390x workers, so the base image
must have an s390x variant.

Canonical choice: **UBI9 minimal** — `registry.access.redhat.com/ubi9/ubi-minimal:latest`.
UBI9 has s390x in its multi-arch manifest.

Verification:
```bash
docker manifest inspect registry.access.redhat.com/ubi9/ubi-minimal:latest \
  | jq '.manifests[].platform | select(.architecture == "s390x")'
# Expected: a manifest entry for linux/s390x
```

If UBI9 is unavailable (air-gapped without internal UBI mirror), build a
`FROM scratch` with a static `curl` binary cross-compiled for s390x. The Job
itself is just `curl -X PUT https://schemaregistry:8081/config -d '{"compatibility":"FULL_TRANSITIVE"}'`,
so the surface is small.

## Why x86 sidecars are an anti-pattern (G-06)

The naive alternative to building Connect + SR bootstrap images for s390x is
to run x86 binaries (Splunk forwarder, Dynatrace OneAgent) as sidecars under
QEMU binary translation:

- **CPU overhead:** 2–5x for the emulated x86 code path
- **No CPACF acceleration:** the emulated x86 code path can't use the LinuxONE
  Crypto Express CPACF instructions that s390x-native JVMs use automatically
- **Operationally fragile:** QEMU versions, kernel `binfmt_misc` registration,
  and image pull paths all become moving parts

The accelerator's design mitigation: **route all observability via Kafka Connect
sinks**, which are arch-neutral Java running in s390x-native CFK Connect pods.
The Dynatrace integration is `kafka-connect-http` POSTing to Dynatrace's generic
log ingest API v2; the Splunk integration is the Splunk Sink connector to HEC.
Same data, no QEMU.

## Air-gapped considerations

For air-gapped LinuxONE deployments (the common FSI case):

1. **Mirror upstream Confluent Hub** to an internal artifact store; download
   the JARs once, store under your FI's standard artifact mgmt (Artifactory /
   Nexus / OCI registry).
2. **Mirror UBI9** to your internal OCP registry — `oc image mirror` handles
   multi-arch correctly.
3. **Build the images on an s390x-native host** where possible to skip QEMU
   even at build time (a LinuxONE-attached build VM is the cleanest path).
4. **Push to your OCP internal registry** so worker nodes can pull without
   external network.
5. **Pin SHAs in CFK CRs**, not floating tags — air-gapped + tag-floats is a
   debug nightmare when the upstream tag is re-pointed at a new SHA.

## Cross-references

- KNOWN-GAPS G-05 (UBI9 base for SR bootstrap Job)
- KNOWN-GAPS G-06 (x86 sidecars anti-pattern — QEMU overhead)
- KNOWN-GAPS G-08 (Connect image build process)
- KNOWN-GAPS G-12 (Flink SQL-runner image build process)
- `patterns/linuxone-on-cfk-reference-architecture` — the architecture these images plug into
- `patterns/flink-on-cfk-fsi-example-jobs` — layer-05 consumer of the SQL-runner image

## Related

- `concepts/linuxone-kafka-integration`
- `concepts/linuxone-platform-foundations`
- `patterns/linuxone-on-cfk-reference-architecture`

## Provenance

- KNOWN-GAPS G-05 (accelerator layer `03-schema-governance` — SR bootstrap Job base)
- KNOWN-GAPS G-06 (x86 sidecars QEMU overhead)
- KNOWN-GAPS G-08 (accelerator layer `04-audit` — Connect image)
- KNOWN-GAPS G-12 (accelerator layer `05-flink` — SQL-runner image)
- `layers/05-flink/sql-runner/README.md` (canonical build instructions)
