---
title: Work Queue
last_updated: 2026-04-20
---

# Wiki Work Queue

Articles flagged for creation, expansion, or verification.
The LLM reads this at session start and clears items when complete.

## Stubs to Create

<!-- format: - [ ] wiki/concepts/<slug>.md — brief description of needed content -->
- [ ] wiki/concepts/flink-confluent-cloud-setup.md — Compute pool creation, catalog/database/table mapping, RBAC model (dual control-plane + data-plane), statement lifecycle, Autopilot, watermarks, statement evolution with carry-over offsets
- [ ] wiki/concepts/private-networking.md — PrivateLink Gateway (replacing PLATT Feb 2026), Azure/AWS/GCP Private Link setup, Enterprise vs Dedicated cluster requirements, Flink-to-Kafka internal routing, egress PrivateLink for external services, Azure ILB idle timeout bypass via Private Link
- [ ] wiki/patterns/flink-event-routing.md — Raw topic → Flink → output topic canonical pattern, replayability/schema decoupling/debuggability rationale, stateless filter/projection sizing, anti-pattern: pre-filtering in producers
- [ ] wiki/concepts/azure-connection-management.md — Azure ILB 4-min TCP idle timeout, socket.keepalive.enable, connection recycling via connections.max.idle.ms, reconnect backoff tuning, Private Link as ILB bypass, cross-reference to aks-kafka-tuning.md
- [ ] wiki/patterns/latency-optimized-kafka-client.md — Fraud detection tuning profile (linger.ms=0, fetch.max.wait.ms=0, max.poll.records=10), decoupled poll/process with BlockingQueue, consumer.pause()/resume() backpressure, static membership, ZGC for sub-ms pauses
- [ ] wiki/concepts/confluent-cloud-gateway.md — Protocol-aware Kafka proxy for traffic control, DR switchover, custom domains, auth swapping; self-managed via CFK/Docker; 1.1.0 GA; CPC Gateway 1.2 adds fencing/unfencing
- [ ] wiki/patterns/dr-application-routing.md — Client-restart problem during Kafka DR; solutions: DNS abstraction, protocol proxy (ORKA/Gateway), cloud-native control plane; evaluation criteria (RTO, guarantee preservation, restart requirement, One-Click DR migration friction)

## Articles to Expand

<!-- format: - [ ] wiki/concepts/<slug>.md — what is missing -->

## Unverified Claims to Resolve

<!-- format: - [ ] <article> line N: "<claim>" — source needed -->
- [ ] kafka-dr-framework-v3.md §5.1: "ORKA returns empty fetch responses to pause consumers" — no public docs; technically plausible per Kafka protocol but unverified
- [ ] kafka-dr-framework-v3.md §5.3: "Kafka guarantees preserved (no duplicates, no missed messages)" — ORKA-specific; Confluent Gateway DR explicitly warns against this for Streams apps

## Lint Findings

<!-- format: - [ ] finding from last lint run -->

## Candidate Articles (from lint / Q&A sessions)

<!-- format: - [ ] <proposed title> — rationale -->
