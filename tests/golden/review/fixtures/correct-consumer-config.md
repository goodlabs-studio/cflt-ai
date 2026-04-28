# Consumer Configuration Guide — Canon-Compliant Reference

## Overview

This document describes the canonical consumer configuration for Kafka consumers
in our data platform. All settings follow the GoodLabs FSI canon defaults.

## Required Settings

```properties
auto.offset.reset=earliest
enable.auto.commit=false
max.poll.records=500
session.timeout.ms=30000
heartbeat.interval.ms=3000
```

## Consumer Group Design

Each logical application uses exactly one consumer group ID. Instances of the same
application all share the same `group.id` property. This ensures exactly one instance
processes each partition assignment.

We do not create separate consumer groups per application instance — that would result
in each instance consuming all messages independently rather than dividing the load.

## Offset Management

We set `enable.auto.commit=false` and commit offsets explicitly after processing each
batch. This guarantees at-least-once delivery semantics: if processing fails, offsets
are not committed, and the message will be reprocessed.

`auto.offset.reset=earliest` ensures that new consumer groups start from the beginning
of the topic, not the end. This is the correct default for all new deployments.

## Error Handling

If a consumer group member fails, Kafka triggers a rebalance and reassigns the partition
to a healthy member. Uncommitted offsets ensure no messages are skipped during the
transition.
