# Contributing to cflt-ai

cflt-ai is a shared Confluent knowledge base powered by Claude Code. Contributions flow through PRs — anyone can add wiki articles, run evaluations, and submit discoveries.

## Getting Started

```bash
git clone <repo-url> cflt-ai && cd cflt-ai
flox activate
bin/setup
claude
```

See [README.md](README.md) for full setup instructions.

## Adding Wiki Articles

### Option A: Manual authoring

1. Create a branch: `git checkout -b wiki/your-topic`
2. Add your article to `wiki/concepts/` or `wiki/patterns/`
3. Follow the format in `.claude/commands/wiki/references/article-format.md`
4. Required frontmatter: `title`, `confidence`, `tags`, `sources`, `last_validated`
5. Register in `wiki/_index.md` and add backlinks to `wiki/_graph.md`
6. Run `/wiki:lint` to check for errors
7. Open a PR

### Option B: From raw sources

1. Add source material (URLs, docs, notes) to `raw/` and register in `raw/_ingest.md`
2. Run `/wiki:ingest` — Claude compiles sources into wiki articles with MCP validation
3. Review the generated articles, then commit and PR

### Option C: From /ask discoveries

While using `/ask`, if you discover something the wiki doesn't cover:
1. Run `/wiki:recommend` with the topic
2. Claude will draft, validate, and write the article
3. Review the output, commit, and PR

## Article Quality Standards

See `.claude/commands/wiki/references/quality-standards.md` for the full spec. Key points:

- **Confidence levels**: `high` (MCP-validated), `medium` (single-source or training data), `low` (unverified or community-sourced)
- **Sources**: Every claim needs a source. Prefer Confluent docs over blog posts.
- **Cross-links**: Articles should link to related concepts and patterns
- **Freshness**: Articles should include `last_validated` date; re-validate quarterly

## Running Skills

| Skill | Purpose | Output |
|-------|---------|--------|
| `/ask` | Quick validated answer | In-conversation |
| `/review` | Evaluate a document | `outputs/reports/<slug>-review-<date>.md` |
| `/wiki:ingest` | Compile raw sources into wiki articles | Wiki articles |
| `/wiki:validate` | Check wiki against live sources | Patches to wiki articles |
| `/wiki:recommend` | Answer + write back discoveries | Wiki articles |
| `/wiki:lint` | Health check | Console output |

## Modifying MANIFEST.yaml

`raw/repos/fsi-dsp/MANIFEST.yaml` is the stable contract between fsi-dsp and cflt-ai.
Before adding entries or types, read [`tools/manifest-schema.md`](tools/manifest-schema.md)
for the full schema reference (top-level fields, base capability fields, all 8 known types,
and the per-type required field tables).

Validate locally with:

```bash
python3 tools/check_manifest.py        # fast schema-only validation
pytest tests/test_manifest.py          # full suite: schema + path existence + expected IDs
```

Adding a new type requires lock-step changes in both repos AND the validator + tests +
schema doc — see the "Adding a new type" runbook in
[`tools/manifest-schema.md`](tools/manifest-schema.md#adding-a-new-type).

## PR Guidelines

- Use the PR template (auto-populated)
- CI runs `wiki-lint.py --full` on any PR touching `wiki/`
- Note which claims were MCP-validated in the PR description
- Keep PRs focused: one topic per PR when possible

## Code of Contribution

- Accuracy over volume. One well-validated article beats five unverified ones.
- When in doubt, mark confidence as `medium` and note what needs verification.
- Don't remove content without explanation. If something is wrong, correct it with sources.
- Canon defaults in CLAUDE.md are authoritative unless explicitly overridden with justification.
