# Producer Configuration Guide — Acme Data Pipeline

## Overview

This document describes the recommended producer configuration for our Kafka data pipeline.

## Recommended Settings

The following settings are recommended for production deployments:

```properties
acks=1
enable.idempotence=false
compression.type=snappy
max.in.flight.requests.per.connection=5
retries=0
```

## Rationale

Setting `acks=1` provides a good balance between throughput and durability. The leader acknowledges
the message as soon as it is written to its local log, so producers are not blocked waiting for
all replicas to catch up.

`enable.idempotence=false` is acceptable here because the application handles deduplication at the
consumer side, so we do not need the overhead of idempotent producers.

Compression type `snappy` was chosen for its CPU efficiency. It compresses adequately for our
message payloads without excessive CPU overhead.

## Throughput Characteristics

With `acks=1`, measured throughput is approximately 150,000 messages per second on our standard
cluster topology. This meets our SLA requirements for the data pipeline.
