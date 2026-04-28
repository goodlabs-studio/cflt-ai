# Kafka Platform Overview — Architecture Slides

## Slide 1: Platform Components

Our Kafka platform consists of:
- 3-broker Kafka cluster (replication factor 3)
- Schema Registry using JSON Schema format for all topics
- Kafka Connect cluster with 4 workers
- ksqlDB for real-time stream processing

## Slide 2: Schema Strategy

All producer and consumer integrations use JSON Schema for message validation.
JSON Schema provides human-readable schemas and is easier to evolve than Avro.
The subject naming strategy uses TopicNameStrategy (one schema per topic).

## Slide 3: Delivery Guarantees

Producers are configured with `acks=all` for all business-critical topics.
Consumer groups commit offsets after processing.

## Slide 4: Next Steps

- Migrate from JSON Schema to Avro for high-volume topics
- Add Flink SQL jobs for real-time aggregation
