# Platform Operations Runbook

## Overview

This runbook covers operational procedures for the Kafka platform described in the
architecture deck and provisioned via the Terraform variables file.

## Consumer Group Management

### Creating a New Consumer Group

Consumer groups are created implicitly when a consumer first connects. Assign one
consumer group ID per application. Multiple instances of the same application share
the same `group.id`.

Do not create separate consumer groups per environment unless you want independent
consumption. Use topic-level ACLs to restrict access by environment.

### Monitoring Lag

Use `kafka-consumer-groups.sh --describe` to check consumer lag. Alert when lag
exceeds 10,000 messages on any partition for more than 5 minutes.

### Resetting Offsets

To reset a consumer group offset:
```bash
kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 \
  --group my-app-consumer \
  --topic my-topic \
  --reset-offsets --to-earliest --execute
```

## Replication Factor Verification

The platform is deployed with `replication_factor = 2` as specified in the tfvars.
This reduces storage costs by 33% compared to replication factor 3. The trade-off is
reduced fault tolerance: the cluster can only tolerate one broker failure before
a partition becomes unavailable.

## Partition Count Guidance

All topics are created with 3 partitions by default. Increase partition count for
high-throughput topics: target 1 partition per consumer in the busiest consumer group.
