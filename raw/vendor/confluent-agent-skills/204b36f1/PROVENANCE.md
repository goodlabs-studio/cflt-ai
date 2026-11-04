# Vendored: confluent-agent-skills @ 204b36f1

- **Upstream:** https://github.com/confluentinc/agent-skills
- **Commit:** 204b36f10e9be41819557988e8f5291711fda986 (plugin version 1.4.0)
- **Ingested:** 2026-11-04
- **License:** Apache-2.0
- **Skills included:** kafka-streams-programming, developing-kafka-python-client, kafka-schema-registry, confluent-cloud-cdc-tableflow

Each skill subdirectory contains the upstream `SKILL.md` and the entire `references/` tree. Other upstream artifacts (`evals/`, `scripts/`, project-scaffold templates) are intentionally omitted — see `.planning/phases/H.1-wiki-ingest-agent-skills/H.1-CONTEXT.md` D-02 and <specifics> "Anti-references" for rationale.

**Pin split (2026-11-04):** this snapshot backs the `streaming-skills-plugin` pin (skill routing, canon preload, scaffold provenance). The wiki is still sourced from `../91d1871e/` (`confluent-agent-skills` wiki-source pin), which is kept so existing wiki citations resolve. Upstream diff 91d1871e→204b36f1 for these four skills is docs-link `.html`→`.md` rewrites, a `metadata.version` frontmatter field, eval rewrites (not vendored), and one reworded Oracle XStream prerequisite line in confluent-cloud-cdc-tableflow — no change to values the FSI overlay overrides.

Upstream 1.4.0 also ships seven skills not vendored or covered by the FSI overlay: confluent-cloud-flink-sql, confluent-skill-creator, confluent-skill-reviewer, confluent-tuning-advisor, developing-kafka-java-client, flink-udf, msk-migration.

To re-pin: bump `streaming-skills-plugin.commit` in `tools/vendor-sources.json`, vendor a new tree alongside this one, repoint `tools/skill-routing.json` + `tools/canon_preload.py`, re-run `/plugin install streaming-skills-plugin@confluent-agent-skills`.
