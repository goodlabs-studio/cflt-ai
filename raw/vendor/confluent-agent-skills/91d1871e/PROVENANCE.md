# Vendored: confluent-agent-skills @ 91d1871e

- **Upstream:** https://github.com/confluentinc/agent-skills
- **Commit:** 91d1871ef8c320be92bca955c8e42492a2778cb4
- **Ingested:** 2026-05-16
- **License:** Apache-2.0
- **Skills included:** kafka-streams-programming, developing-kafka-python-client, kafka-schema-registry, confluent-cloud-cdc-tableflow

Each skill subdirectory contains the upstream `SKILL.md` and the entire `references/` tree. Other upstream artifacts (`evals/`, `scripts/`, project-scaffold templates) are intentionally omitted — see `.planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md` D-02 and <specifics> "Anti-references" for rationale.

To re-ingest at a new SHA: bump `commit` in `tools/vendor-sources.json`, delete this vendor tree, re-clone at new SHA, re-run `/wiki:ingest` on affected articles, re-run `/wiki:validate`.
