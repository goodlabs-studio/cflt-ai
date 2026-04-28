# Schema Evolution Strategy — Confluent Schema Registry

## Overview

This document describes our approach to schema evolution for event streams
using Confluent Schema Registry.

## Compatibility Mode Selection

We use FULL compatibility mode for all production schemas. FULL compatibility
ensures both forward and backward compatibility: new consumers can read old
messages, and old consumers can read new messages.

FULL mode is stricter than BACKWARD mode (default) but provides stronger
guarantees for shared consumer contracts where multiple teams own consumers.

## Schema Format: Avro vs Protobuf

We evaluated Avro and Protobuf for our schema format.

Avro is our current format. It has native Schema Registry integration, compact
binary encoding, and strong support in Confluent's tooling. Schema evolution
is expressed through default values and field ordering rules.

Protobuf provides stronger cross-language support and is preferred by teams
with Go or Rust consumers. Protobuf schemas are self-describing (field numbers
are embedded in the wire format), making evolution more flexible than Avro's
positional dependency.

For our Java/Python stack, Avro remains the better choice due to tooling maturity.

## Evolution Rules

Adding optional fields with defaults: allowed under FULL compatibility.
Removing fields: only allowed when consumers have been migrated.
Changing field types: requires a major version bump and consumer coordination.

## Subject Naming

All topics use `TopicNameStrategy`. This means one schema per topic, regardless
of the number of event types the topic carries.
