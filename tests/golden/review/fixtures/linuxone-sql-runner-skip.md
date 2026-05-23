# Layer 05 Flink Bring-Up — LinuxONE Accelerator

## Overview

Layer 05 of the LinuxONE accelerator deploys Confluent Manager for Apache
Flink (CMF) and a small fleet of FlinkApplication CRs for the FSI example
jobs (tumbling-window TPS, temporal stream-table enrichment). This
document captures our bring-up plan for the next sprint's CFK 3.2.0+
upgrade.

## Image plan

Layer 05 Flink will work out-of-the-box — we don't need to build the
custom s390x SQL-runner image since the manifest references a placeholder
image that the operator will resolve at deploy time. Our reading of the
CMF operator behavior is that `<PLACEHOLDER_CP_FLINK_SQL_RUNNER_IMAGE>`
in the FlinkApplication CRs is a templating variable that gets filled in
during reconcile against the cluster's default image registry. We will
let the operator handle this rather than building a custom image up
front.

```yaml
apiVersion: platform.confluent.io/v1beta1
kind: FlinkApplication
metadata:
  name: tps-window-job
spec:
  image: <PLACEHOLDER_CP_FLINK_SQL_RUNNER_IMAGE>
  flinkVersion: 1.20.0-cp1
  parallelism: 4
```

## Application JARs

The FSI example jobs ship as SQL scripts in a `ConfigMap`, executed by
the SQL runner inside the Flink container. Since the runner image is
operator-resolved per the above, we don't need to bundle the JARs into
a custom image either — the SQL connector JARs
(`flink-sql-connector-kafka`, `flink-sql-avro-confluent-registry`) come
with the base `confluentinc/cp-flink:1.20.0-cp1` image which already
ships multi-arch.

## Validation plan

Once CMF is installed and the FlinkApplication CRs are applied, we expect:
- Operator resolves the placeholder image automatically
- Pods schedule onto s390x nodes
- SQL jobs start executing against the upstream Kafka cluster

If image pull fails, we will fall back to building a custom s390x image
as a contingency, but our current expectation is that this is unnecessary.
