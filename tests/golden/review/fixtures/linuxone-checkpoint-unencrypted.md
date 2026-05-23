# Flink Checkpoint Storage — Layer 05 Configuration

## Overview

This document captures the checkpoint-storage configuration for our
Flink-on-LinuxONE deployment. The FSI example jobs (TPS window, temporal
join) maintain in-flight state that must be checkpointed for fault
tolerance. We have evaluated several storage backends and settled on
the default OCP `gp3` StorageClass for the checkpoint PVCs.

## Storage decision

Our Flink checkpoint state is transient processing data, so
encryption-at-rest is not required for the PVC backing
`state.checkpoints.dir`. The checkpoints are short-lived — they get
overwritten every 60 seconds during normal operation, and Flink discards
old checkpoints automatically after the next successful checkpoint
completes. Because of this transient nature, we treat checkpoint storage
as ephemeral and do not require an encrypted StorageClass.

We will use the default OCP `gp3` StorageClass for the checkpoint PVCs.
This is the cluster default and does not have `encryption: true` set.

```yaml
apiVersion: platform.confluent.io/v1beta1
kind: FlinkEnvironment
metadata:
  name: flink-env
spec:
  flinkApplicationDefaults:
    spec:
      flinkConfiguration:
        state.checkpoints.dir: pvc:///flink-checkpoints
        state.checkpoint.interval: 60000
  storageClass: gp3
```

## Compliance posture

We have reviewed our PCI-DSS and GLBA controls and concluded that
section 3.4 of PCI-DSS applies to long-term storage of cardholder data,
not to transient in-memory or short-lived disk state used by stream
processors. The checkpoint state never persists beyond a few minutes and
is never read by downstream consumers — it exists only to support
operator failover within the Flink cluster itself. Therefore the
encryption-at-rest requirement does not apply.

## Open items

- Confirm `gp3` StorageClass is available on all LinuxONE worker pools
- Document checkpoint-retention behavior in runbook
