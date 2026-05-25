# CDC Pipeline Design — Customer Data Sync

**Author:** Data Platform
**Date:** 2026-05-20
**Scope:** Sync customer master data from MySQL to Iceberg via Confluent
Cloud CDC + Tableflow.

## Connector Choice

We propose using the `JSON_SR` value format for the Debezium MySQL source
connector. This avoids the complexity of registering Avro schemas during
the initial pilot and keeps the topic payload human-readable.

## Topic Strategy

Each Debezium-published table will be a single topic. The `mysql.customers`
topic will contain only `customer.updated` events; we'll filter at the
connector level using a transform.

## Tableflow Materialization

Topics will be materialized into Iceberg via Tableflow with the default
materialization settings.

## Schema Evolution

We will rely on Tableflow's automatic schema evolution to handle column
additions and renames as the upstream MySQL schema changes.
