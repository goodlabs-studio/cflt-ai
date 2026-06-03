# /wiki:ingest — Compile raw sources into wiki articles

You are the wiki ingest skill. You compile raw source files into structured wiki articles with MCP validation.

## References

Read these before proceeding:
- `.claude/commands/wiki/references/article-format.md` — frontmatter schema and article templates
- `.claude/commands/wiki/references/quality-standards.md` — MCP validation rules and routing

## Process (execute in strict order)

### Step 1: Read the ingest queue

Read `raw/_ingest.md`. Parse the `## Pending` section. If empty, report "No pending entries" and stop.

### Step 2: Read the wiki index

Read `wiki/_index.md` to know what articles already exist.

### Step 3: Process each pending entry

For each entry in `## Pending`:

**3a. Read the source file** at the path specified in the entry.

**3b. Read existing articles** if the entry's `notes` field mentions expanding an existing article, read that article first.

**3c. Draft article(s)** following the templates in `references/article-format.md`:
- Use the **concept template** for explanatory content (what/why)
- Use the **pattern template** for procedural content (how/when)
- Set `confidence: medium` initially (will be upgraded after validation)
- Include proper frontmatter with all required fields
- Add cross-links to related existing articles
- **Diagram (architectural patterns):** if the article describes an architecture, topology, or data-flow, include one ` ```mermaid ` block near the top of the body (under `## Pattern`). Use `flowchart LR` or `flowchart TD`, quoted node labels (`id["Label"]`; clusters/datastores `id[("Label")]`; decisions `id{"Label"}`), quoted edge labels, and `subgraph GID["Title"] … end` for grouping. Do NOT use `\n`, `<br/>`, HTML entities, or unicode box-drawing characters in labels — keep labels short and single-line, splitting into multiple nodes for detail. ArticleView renders mermaid as SVG; ASCII box-drawing diagrams do not render and must not be used for new articles.

**3d. MCP validation gate (MANDATORY)**

For every verifiable claim in the draft (config property names, defaults, version numbers, feature availability, behavioral assertions):

1. Check the MCP routing table in `references/quality-standards.md` to determine which tool to use
2. Query the appropriate MCP tool (`confluent-docs` for config/API/features, `context7` for architecture patterns)
3. For each claim:
   - **Confirmed**: Keep as-is
   - **Contradicted**: Correct the claim in the draft
   - **No MCP data**: Mark with `> ⚠️ unverified — [claim]` inline
4. If all verifiable claims are confirmed, set `confidence: high`
5. If most claims are unverifiable, keep `confidence: medium`

**This step is not optional.** The manual ingest workflow that preceded this skill skipped MCP validation — that's how errors like incorrect config property scopes got through.

**3e. Write the article(s)** to the appropriate `wiki/` subdirectory.

### Step 4: Update wiki/_index.md

Add a line for each new article under the correct section. Paths are relative to `wiki/`. Follow the existing format:
```
[Schema Evolution Strategies](concepts/schema-evolution-strategies.md) — Avro-first schema governance with tier-based compatibility — #schema-registry #avro #fsi
```

If an existing article was expanded, update its summary line if the scope changed.

### Step 5: Update wiki/_graph.md

Add backlinks for all new articles. Every new article needs at least 1 inbound and 1 outbound link. Follow the existing format:
```
source/article → target/article : relationship description
```

### Step 6: Move entries from Pending to Processed

In `raw/_ingest.md`, move each processed entry from `## Pending` to `## Processed` with:
```yaml
- path: <original path>
  source_url: <if present>
  notes: <original notes>
  compiled: YYYY-MM-DD
  wiki_articles:
    - wiki/<path to article created or expanded>
```

### Step 7: Run lint

Run `python tools/wiki-lint.py` and report any broken links or orphans introduced by this ingest.

### Step 8: Print summary

Report:
- Articles created (count and paths)
- Articles expanded (count and paths)
- Claims verified via MCP (count)
- Claims flagged as unverified (count)
- Any lint findings
