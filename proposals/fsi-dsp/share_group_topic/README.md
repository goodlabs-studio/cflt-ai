# Proposal: `share_group_topic` Terraform module (fsi-dsp)

A supporting fsi-dsp asset for [Queues for Kafka (Share Groups)](../../../wiki/concepts/queues-for-kafka-share-groups.md).
It provisions a **governed Kafka topic intended for share-group (queue) consumption**
plus the RBAC role bindings a share-group worker pool needs.

## Why this is a proposal, not a committed asset

`raw/repos/fsi-dsp` is a **read-only git submodule** consumed by cflt-ai one-directionally
(cflt-ai cites fsi-dsp assets by ID via `MANIFEST.yaml`; nothing is pushed back from here).
Adding a terraform-module to fsi-dsp is a **lock-step change across both repos** — landing it
directly from cflt-ai would either dirty the submodule or break the canon-parity contract
(`tools/check-canon-parity.py`). So this directory is a complete, reviewable bundle to be
contributed to fsi-dsp via its own PR.

## Landing checklist (lock-step)

1. **fsi-dsp** — copy `main.tf` / `variables.tf` / `outputs.tf` to `modules/share_group_topic/`.
2. **fsi-dsp** — add the capability entry from `MANIFEST-entry.yaml` to `MANIFEST.yaml`
   (bump `version` minor; IDs are append-only per CNTR-04).
3. **cflt-ai** — add a `share_group_config` block to `canon/base/defaults.yaml` (the canon
   surface this module governs), with the FSI overrides landing in
   `canon/industry/fsi/overrides.yaml` (at-least-once + ordering caveats, RBAC).
4. **cflt-ai** — add `"module/share_group_topic": "share_group_config"` to
   `MODULE_TO_CANON_KEY` in `tools/check-canon-parity.py` so Direction-1 parity passes.
5. **cflt-ai** — extend `tests/test_manifest.py` / parity tests with the new ID.

Until step 3+4 land together, `check-canon-parity.py` would flag the new module as an
unmapped capability — that is why this bundle is staged outside the submodule.

## Cluster prerequisites (not module-scoped)

Share groups are enabled at the **broker/cluster** level, not per topic. Before this module is
useful the target cluster must have the share-group feature enabled and tuned — e.g.
`group.share.enable=true`, `group.share.record.lock.duration.ms`,
`group.share.delivery.count.limit` (KRaft required). **Verify exact property names, defaults,
and Confluent Platform/Cloud availability against `confluent-docs`** — they are marked "verify"
in the wiki article and are not yet canon-validated.

## FSI guardrails baked in

- `sla_tier` is constrained so share-group (at-least-once, unordered) topics **cannot** be
  declared `critical` without an explicit `allow_at_least_once = true` acknowledgement — a
  tripwire against using queue semantics on ordered/EOS regulatory paths.
- Consumer service accounts receive least-privilege `DeveloperRead` on **both** the topic and
  the named share group; mTLS + RBAC per FSI canon.
