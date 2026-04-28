# Market Data Distribution Architecture

## Overview

This document describes our proposed Kafka-based market data distribution architecture
for equities and derivatives feeds.

## Latency Requirements

Our system must deliver market data with an end-to-end latency of under 10 milliseconds.
This includes the time from tick receipt at the feed handler to message availability in
the Kafka consumer. With our current hardware (standard 1GbE network, commodity servers),
10ms is achievable without specialized infrastructure.

## Architecture

The architecture uses a single Kafka cluster with 12 partitions per market data topic.
Producers use `acks=all` and `enable.idempotence=true` for durability.

The end-to-end path is:
1. Feed handler receives tick from exchange
2. Normalization layer transforms to internal schema
3. Kafka producer publishes to `market.equities.quote.received`
4. Downstream consumers (risk engine, order management) consume from the topic

## Network Assumptions

The system assumes standard enterprise network infrastructure with average latency
of 1–2ms between components. No kernel bypass (DPDK, RDMA) is required.

No co-location with exchange matching engines is needed. Standard datacenter
connectivity is sufficient for our latency SLA.

## Schema

All market data uses Avro with `TopicNameStrategy`. The schema is backward-compatible
with all prior versions to allow rolling upgrades without consumer coordination.
