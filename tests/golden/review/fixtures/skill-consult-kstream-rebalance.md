# Engineering Memo: Kafka Streams Rebalancing Loop Mitigation

**Author:** ACME Platform Team
**Date:** 2026-05-20
**Scope:** Production Kafka Streams app `payments-enrichment` exhibiting
continuous consumer-group rebalances.

## Symptom

The `payments-enrichment` KStream topology rebalances every 60-90 seconds,
causing 30-45s windows where no records are processed. State stores remain
warm (no full restore) but downstream latency SLOs are breached.

## Proposed Remediation

We propose increasing `max.poll.interval.ms` from the default 300000 (5 min)
to 1800000 (30 min). This will give the consumer group more time before the
broker considers a member dead, eliminating the rebalance trigger.

## Configuration Change

```properties
max.poll.interval.ms=1800000
session.timeout.ms=60000
heartbeat.interval.ms=20000
```

## Risk Assessment

Increasing `max.poll.interval.ms` is widely recommended in the Kafka community
and is described as the "best fix" for rebalancing loops. The change is
backward-compatible and requires no application code modification.

## Topology Recap

The app uses a `StreamsBuilder` topology with a single windowed aggregation
over a 5-minute tumbling window, followed by a join with a `GlobalKTable`
of merchant metadata. Processing guarantee is set to `at_least_once`.

## Conclusion

Recommend rolling out the `max.poll.interval.ms` increase in next week's
release. Expected to stabilize the topology with no downside.
