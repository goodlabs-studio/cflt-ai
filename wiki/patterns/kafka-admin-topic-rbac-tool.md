---
title: Kafka-Admin — Topic and RBAC Migration Tooling for Confluent Platform
tags: [kafka confluent-platform rbac topic-management migration mrc replica-placement fsi]
related: [patterns/dr-multi-region-cluster, patterns/x86-to-linuxone-cluster-linking-migration, patterns/fsi-governance-automation, patterns/topic-naming, concepts/sla-tiers]
confidence: medium
last_updated: 2026-09-04
last_validated: 2026-09-04
---

# Kafka-Admin — Topic and RBAC Migration Tooling for Confluent Platform

## Summary

`kafka-admin` (internal tool, `~/GoodLabs/kafka-admin`) is a Java AdminClient/MDS-based CLI for managing Kafka topics, ACLs, Centralized ACLs, and Confluent Platform RBAC role bindings as YAML-declared, diffed, plan-then-apply configuration. It fills the role Terraform plays for Confluent Cloud — but the [Confluent Terraform provider is Cloud-only](https://registry.terraform.io/providers/confluentinc/confluent/latest/docs) (confirmed against the provider's own docs: every auth path is `cloud_api_key` or Cloud-scoped OAuth, no MDS/on-prem mode) — so on Confluent Platform, `kafka-admin` (or an Ansible role wrapping the MDS REST API) is the closest equivalent. Its `dump` → edit YAML → `plan` → `execute` workflow is well suited to bulk-provisioning topics and RBAC bindings on a newly built cluster, such as the target of a Multi-Region Clusters (MRC) migration — provided the replica-placement and cross-cluster-identity gotchas below are handled explicitly, and provided the tool's default-enabled delete paths are not relied upon against a production cluster.

## Pattern

### Workflow

```
dump (from source cluster)  →  post-process YAML  →  plan (default, no -execute)  →  review  →  execute
```

- `-dump [-r] [-cacl] [-o <file>]` — reads the connected cluster's current topics, ACLs, RBAC role bindings, and Centralized ACL bindings and emits them as YAML.
- `-config <file.yml>` (no `-execute`) — diffs the YAML against the connected cluster's live state and prints a plan (`createTopicList`/`increasePartitionList`/`deleteTopicList`, and equivalent for ACLs/RoleBindings/AclBindings) without applying anything. This is the review gate — treat it the same as `terraform plan`.
- `-config <file.yml> -execute [-r] [-cacl]` — applies the plan.

### Replica placement for MRC target topics

The tool has no dedicated replica-placement feature — and doesn't need one, because `confluent.placement.constraints` is just a topic config string, and the tool passes through any YAML key that isn't `name`/`partitions`/`replication.factor` as a raw topic config (`Topic.java`, `createTopics()`). Two things must both be true for a topic to land on MRC's replica-placement policy instead of standard rack-aware assignment:

1. **`replication.factor: -1` in the topic's YAML entry.** Kafka's `NewTopic(name, partitions, replicationFactor)` constructor sends whatever `replicationFactor` you give it verbatim onto the wire as `CreatableTopic.replicationFactor`. Kafka's own sentinel for "not specified" (`CreateTopicsRequest.NO_REPLICATION_FACTOR`) is `-1` — so passing `-1` explicitly produces byte-identical wire output to omitting the field entirely via AdminClient's `Optional`-based constructor. This is the Java-API equivalent of Confluent's documented CLI guidance: *"do not create topics using `--replication-factor`"* when a placement policy should apply — `-1` **is** "not specified," not a special case the tool needs extra code for.
2. **`confluent.placement.constraints: '<placement JSON>'` set explicitly on the same topic**, e.g.:

```yaml
topics:
  payments-transaction-completed:
    name: payments.transaction.completed
    partitions: 12
    replication.factor: -1   # sentinel for "use the placement policy below, not a flat RF"
    min.insync.replicas: "3"
    confluent.placement.constraints: '{"version":2,"replicas":[{"count":2,"constraints":{"rack":"east"}},{"count":2,"constraints":{"rack":"west"}}],"observers":[{"count":1,"constraints":{"rack":"central"}}],"observerPromotionPolicy":"under-min-isr"}'
```

An explicit per-topic `confluent.placement.constraints` always takes precedence — there's no ambiguity to reason about the way there is with the *broker-side default* (`confluent.log.placement.constraints`), which Confluent's docs warn is silently **ignored** whenever a topic-creation request specifies an explicit replication factor. Since `kafka-admin` always specifies a replication factor value (never omits the field), a broker-side default constraint will never apply to topics this tool creates — `-1` plus an explicit per-topic constraint is the only reliable path, not a cluster-wide default.

Because `getTopics()`/`dump` captures any non-default, non-read-only topic config, a topic created this way round-trips correctly on a future `dump` — `confluent.placement.constraints` stays visible and config-as-code-manageable after the migration, not just during it.

### Cross-cluster identity: what does and doesn't carry over on a dump → apply

- **RBAC principals carry over.** Confluent Platform RBAC principals are literal `User:<username>` strings (LDAP/local identities), not cluster-scoped service-account IDs — unlike Confluent Cloud, a dumped principal is valid on the target cluster as-is.
- **`scope.clusters.kafka-cluster` (and `connect-cluster`, where present) do not carry over.** Every RoleBinding's scope is tied to the source cluster's ID. A straight `dump` → `execute` against a new target cluster will produce bindings scoped to a cluster ID that doesn't exist there. Rewrite every `scope.clusters.kafka-cluster` value to the target cluster's ID as a mandatory post-processing step before `-execute` — find-and-replace on the dumped YAML is sufficient, but it must not be skipped.
- **Topic `replication.factor` does not carry over as-is for MRC targets.** `getTopics()` dumps the *live* replica count from the source cluster (sized for a single-region topic). Applied unmodified to an MRC target, this both loses the placement policy (see above) and sets the wrong replica count. Tag each dumped topic with an SLA tier and regenerate `replication.factor: -1` + the tier's `confluent.placement.constraints` as a templated post-processing step, not a hand-edit per topic.

### Delete protection

By default, before this pattern's guardrails, `kafka-admin`'s destructive paths had inconsistent gating:

| Resource | Flag required to delete | Default behavior on `-execute` |
|---|---|---|
| Topics | `-delete`/`-d` (opt-in) | Skipped unless explicitly requested |
| ACLs | `-noaclcleanup` to **skip** | **Deletes by default** — easy to trigger by omission |
| RBAC RoleBindings | none | **Always deletes** anything in the diff's `deleteRoleBindingsList` whenever `-execute -r` is used — no opt-out flag existed |
| Centralized AclBindings | none | **Always deletes** whenever `-execute -cacl` is used — no opt-out flag existed |

RoleBinding and Centralized-ACL deletion having no opt-out flag at all was the most dangerous gap — any diff-driven removal (e.g., a stale YAML, a principal typo, or a partial dump) would delete production RBAC bindings with no way to prevent it short of not passing `-execute -r`/`-cacl` at all. For a migration tool intended to run against a live cluster's RBAC and topic surface, this tool has been modified so that **every delete code path unconditionally refuses and throws**, regardless of flags — see the `Rbac.pushRoleBindings`, `CentralizedAcl.pushAclBindings`, `Topic.deleteTopics`, and `Acl.deleteAcls` implementations. The diff/plan output still computes and prints what *would* be removed (retained for drift visibility — this is genuinely useful audit information), it just can never be applied. The `-delete`/`-d` and `-noaclcleanup` flags were removed since they no longer have any effect.

## When to Use

- Bulk-provisioning topics and RBAC role bindings on a newly built Confluent Platform cluster (e.g., the target of a greenfield MRC build — see [DR — Multi-Region Cluster](dr-multi-region-cluster.md)), generated from an audited/tiered export of the source cluster(s) rather than a manual re-creation.
- Ongoing config-as-code management of topics/RBAC on Confluent Platform where Terraform isn't an option (Cloud-only provider) and Ansible-wrapped MDS REST calls aren't already built out.
- Any workflow that benefits from a `dump` → diff → plan → review → execute loop against MDS-managed RBAC, mirroring the same audit discipline used in [x86 to LinuxONE Cluster Linking Migration](x86-to-linuxone-cluster-linking-migration.md) (pre-migration audit, parity validation, evidence collection).

## Caveats

- **Never trust a raw `dump` as apply-ready input.** It is a snapshot of the *source* cluster's current state (including its accumulated RBAC cruft — wildcard bindings, orphaned topics) and its *single-region* replica factors. Treat it as the starting point for an audited, tiered, cluster-ID-corrected rewrite, not the artifact you execute.
- **`replication.factor: -1` without a matching `confluent.placement.constraints` config just falls back to standard broker-default replication factor / rack awareness — it will not silently do nothing.** Always pair the two.
- **Validate the mechanism on one throwaway topic against the real target cluster before running it at scale.** `kafka-replica-status --verbose` should show sync replicas and observers landing exactly where the placement JSON specifies.
- **Delete protection is a code-level guarantee only for this build of the tool.** If the jar is rebuilt from a different branch or the guard is reverted, the original flag-gating behavior (inconsistent, and unconditionally destructive for RoleBindings/Centralized ACLs) returns. Treat the delete-disabled build as the one to run against any cluster this tool wasn't explicitly authorized to mutate destructively.

## Related

- [DR — Multi-Region Cluster](dr-multi-region-cluster.md) — the target topology this tool provisions topics/RBAC against
- [x86 to LinuxONE Cluster Linking Migration](x86-to-linuxone-cluster-linking-migration.md) — parallel audit/validate/evidence-collection discipline for a different CP migration
- [FSI Governance Automation](fsi-governance-automation.md) — the Terraform/Ansible governance-as-code pattern this tool substitutes for on CP where Terraform can't reach MDS
- [Topic Naming Convention](topic-naming.md) — naming/config conventions to apply when tiering and regenerating topic YAML
- [SLA Tiers](../concepts/sla-tiers.md) — the tier system that should drive per-topic placement-policy assignment
