---
artifact: scenario/cc-gcp
operator: unknown
profile: engineer
outcome: deferred-to-mcp-runtime
canon_hash: b6a3cf22b1438242
plan_ref: outputs/plans/create-a-basic-kafka-cluster-plan-2026-05-11.md
timestamp: 2026-05-11T17:14:51Z
---

# Incident: confluent-cloud-on-gcp-starter

## What Changed

Applied `scenario/cc-gcp` via profile `engineer`.
Execution result: `deferred-to-mcp-runtime`.

## Why

See plan: `outputs/plans/create-a-basic-kafka-cluster-plan-2026-05-11.md`

## Gate Results

| Gate | Status | Detail |
| --- | --- | --- |
| canon_compliance | pass | Request is consistent with Confluent Canon defaults. |
| fsi_dsp_coverage | pass | Matched fsi-dsp artifact: scenario/cc-gcp (scenario) |
| confluent_docs_schema | pass | Schema validation deferred to MCP runtime (confluent-docs). |
| mcp_confluent_state | pass | Cluster state check deferred to MCP runtime (mcp-confluent). |

## Provenance

Canon stack: base + industry/fsi
Canon hash: `b6a3cf22b1438242`
Operator: unknown
Timestamp: 2026-05-11T17:14:51Z
