# Python Producer Scaffold — Internal Tooling Team

**Author:** Tooling
**Date:** 2026-05-20
**Scope:** Standardize Python producer configuration for the `notifications`
domain.

## Recommended Defaults

Based on a survey of recent internal projects, we propose these defaults for
all new Python producers in the `notifications` domain:

| Setting | Value | Rationale |
|---|---|---|
| client library | `confluent-kafka-python` | Confluent-supported, librdkafka-backed |
| serializer | `JSONSerializer` | Easiest for engineers to debug; works without Schema Registry setup |
| `acks` | `1` | Balances throughput and durability |
| `enable.idempotence` | `false` | Reduces overhead for non-critical notifications |
| `compression.type` | `none` | CPU savings on the producer side |

## Schema Registry Posture

We propose making Schema Registry integration **optional** for the
`notifications` domain. Notifications are ephemeral (24h retention) and don't
require the schema-evolution discipline of payment events. Using
`JSONSerializer` without an SR backend simplifies onboarding.

## Sample Producer

```python
from confluent_kafka import Producer
from confluent_kafka.serialization import StringSerializer
from confluent_kafka.schema_registry.json_schema import JSONSerializer

producer = Producer({
    'bootstrap.servers': 'kafka:9092',
    'acks': '1',
    'enable.idempotence': False,
    'compression.type': 'none',
})
```

## Conclusion

These defaults should be adopted as the standard for all new Python producers
under `notifications.*`.
