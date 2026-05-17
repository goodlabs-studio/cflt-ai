# FSI Developer-Sandbox Canon ADRs

This directory will house formal Architecture Decision Records for the FSI
developer-sandbox canon overlay (`canon/industry/fsi/developer-sandbox/`).

## Status: Pre-ADR (H.4b)

All current overrides in `overrides.yaml` reference `H.4b CONTEXT D-07 — <dimension>`
as their source. These are deliberate departures from the FSI prod overlay
(`canon/industry/fsi/overrides.yaml`), grounded in dev-tier sandbox semantics:

| Dimension | FSI Prod | FSI Dev-Sandbox | Why |
|-----------|----------|-----------------|-----|
| security.auth_mechanism | mTLS + RBAC | OAUTHBEARER | Faster iteration in sandbox |
| processing_guarantees.delivery | exactly_once | at_least_once | EOS is prod-only |
| schema_registry.format | avro | json | JSON acceptable in sandbox |
| schema_registry.compatibility_mode | (varies, often FULL) | BACKWARD | Minimum baseline |
| topic_design.replication_factor | 3 | 1 | Sandbox tolerance |
| topic_design.min_insync_replicas | 2 | 1 | Sandbox tolerance |
| topic_design.naming_convention | <domain>.<application>.<entity>.<event> | <owner>.<feature>.<entity>-sandbox | Dev ownership pattern |
| producer.acks | all | 1 | Performance over durability |
| producer.enable_idempotence | true | false | User choice in dev |
| consumer.auto_offset_reset | earliest | latest | Common dev preference |
| consumer.enable_auto_commit | false | true | OK in non-critical dev paths |
| cluster_linking | preferred over MM2 | none | Single-cluster sandbox typical |

## Promotion Path

After **one** customer engagement using `developer/sandbox` profile in practice,
each H.4b CONTEXT-sourced override above MUST be promoted to a formal ADR
(`adr-001.md`, `adr-002.md`, etc.) following the FSI ADR template at
`../../adrs/`. Until then, the table above is the canonical justification.

## See Also

- `canon/industry/fsi/overrides.yaml` — prod FSI overlay (the bifurcation point)
- `canon/industry/fsi/adrs/` — prod FSI ADR registry
- `tools/profiles/developer/sandbox.json` — first profile that consumes this overlay
