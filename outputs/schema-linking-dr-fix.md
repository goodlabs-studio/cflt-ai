# Fixing the DR Schema Registry with Schema Linking

## Problem

DR consumers on east2 fail with "schema not found" or "unable to deserialize Avro". Mirrored messages carry east1's schema IDs, but east2's Schema Registry holds schemas registered under different IDs. The fix is to make east2 hold the same schema IDs as east1, then keep it synced with Schema Linking.

## Target state

- East1: `READWRITE`. East2: `IMPORT`.
- A schema link (exporter) from east1 to east2 syncs all subjects and keeps the same IDs.
- Schemas are registered on east1 only. DR consumers only read.

## Approach 1: Clean rebuild (recommended)

1. Back up east2's current schemas to files, as a rollback record.
2. Pause east2 consumers, and anything that registers schemas on east2.
3. Hard delete all schemas on east2 (soft delete, then permanent). Confirm it is empty.
4. Set east2 to `IMPORT` mode.
5. Create the schema link from east1 to east2, covering all subjects and contexts.
6. Wait for the link to reach `RUNNING` and finish the initial transfer.
7. Verify that the schema IDs from the failing messages return the same schema on both sides.
8. Resume one consumer and confirm it reads from east2 in `IMPORT` mode. Then resume the rest.

**Impact:** brief extra exposure while east2 is empty and the first sync runs. Consumers are already failing today.
**Risk:** low. The result is a clean state with matching IDs.

## Approach 2: Patch in place, then force `IMPORT`

1. Compare east1 and east2 by subject, version and schema ID.
2. Manually patch east2 so the versions match.
3. Set east2 to `IMPORT` mode with `force`, since it already holds schemas.
4. Create the schema link and let it sync.
5. Verify IDs, then resume consumers.

**Impact:** potentially less downtime.
**Risk:** higher. `force` only allows the mode switch on a non-empty registry. It does not repair conflicting schemas. A schema on east2 with the wrong ID has to be deleted and re-registered, so this approach only works if the IDs already match and only versions are missing.

## Recommendation

Use Approach 1. To limit the impact, run the Approach 2 comparison first:

- If every ID matches, Approach 2 is viable.
- If any differ, hard delete only the mismatched subjects, then create the link. This is a scoped Approach 1.

**Link settings (both approaches):** link all contexts, not just the default context, and set the context type to "none". The link then covers every future subject and version, including any in named contexts, and lands them unchanged in east2's default context with the same IDs.

## Downtime and impact

**Where it comes from (Approach 1):** consumers are paused from the moment they stop until the link finishes its first full transfer. That covers the delete, the mode switch, the initial transfer and verification. The initial transfer scales with the number of subjects and versions on east1.

**Who is affected:**
- Failing consumers are already broken, so a pause adds no new impact.
- Any DR consumers that work today take new downtime. Identify them in advance.
- While east2 is empty or mid-sync, DR cannot serve schema-based data. Schedule the work for a low-risk period.

**Ways to shorten the window:**
1. Do the prep before the window: back up east2, create and test the link's service account, API key and role bindings, write the link configuration, count east1's subjects and versions, and prepare the verification IDs.
2. Pause only the affected consumers.
3. Run the delete and the link back-to-back.
4. Resume in stages, one consumer first.
5. Choose an off-peak time.

**Lowest-downtime alternative:** link east1 into a separate context on east2 while current consumers keep running, then move consumers over a few at a time. This avoids the delete window, but every consumer needs a config change and restart, the stale data stays on east2, and any missed consumer keeps failing.

**Rollback:** restoring the backup would bring back the broken state. If the link fails mid-way, the fallback is a fresh east2 environment with the link rebuilt.

## Keeping Schemas Synced Going Forward

### How automatic sync works

Once the link is `RUNNING`, it syncs new schemas and new versions from east1 to east2 on its own. After its initial transfer, it is notified of each new schema and exports it if it matches the link's subject filter. It records its progress, so a pause and resume picks up where it left off. No scheduled job or manual re-sync is needed.

### Setup that keeps it automatic

1. **Use a broad subject filter.** Link all subjects across all contexts, so new topics and subjects are picked up automatically. An explicit list or prefix never syncs subjects outside it.
   - **Default-context filter:** this is the default filter (all subjects in the default context). It picks up every future subject and version registered in east1's default context. It does not pick up subjects registered in any named context on east1. If the client only ever uses the default context, this is enough. The all-contexts filter is recommended, because it also covers contexts a team starts using later.
   - **Context type must be "none":** the link's default context type is "auto", which lands schemas in a separate context on east2 and leaves the default context empty. Set it to "none" so east1's schemas land unchanged in east2's default context with the same IDs. This is what lets DR consumers keep their current configuration.
2. **Keep the modes fixed.** East1 stays `READWRITE` and east2 stays in `IMPORT`.
3. **Register schemas on east1 only,** ideally through CI. DR producers, connectors and jobs run with auto-registration off.
4. **Change the link carefully.** To change its configuration, pause it, apply the change, reset it and resume. Without the reset, existing schemas for newly added subjects are skipped.
5. **Use a dedicated service account for the link,** not a person. Document the owner and plan the API key's rotation.

### Monitoring and alerting

- **Link state:** alert if it isn't `RUNNING` or reports an error.
- **East2 mode:** alert if it ever leaves `IMPORT` in steady state.
- **Transfer activity:** track the schema-transfer success metric from the Confluent Cloud Metrics API.
- **Audit log:** alert on link creation, change or deletion.
- **Drift check:** on a schedule, compare a sample of recent schema IDs on both sides.

### Operating the link

- **Common causes of a paused link:** an expired or revoked east2 API key, or a removed role binding on east2.
- **Client-side field-level encryption (CSFLE), if used:** the east2 principal needs the key-encryption-key permissions, or the link pauses.
- **Failover runbook:** on east1 failure, switch east2 to `READWRITE` first. After recovery, reverse the link so east1 catches up on schemas registered during the outage, then fail forward or back. Keep the steps written down for use without access to both regions.

## References

- Confluent Cloud: Schema Linking, https://docs.confluent.io/cloud/current/sr/schema-linking.html
- Schema Registry API reference (modes and `force`), https://docs.confluent.io/platform/current/schema-registry/develop/api.html
