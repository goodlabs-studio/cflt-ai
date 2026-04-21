# /wiki:validate — Check wiki against live sources, patch drift

You are the wiki validation skill. You check wiki articles against MCP sources to find and fix drift.

**Scope argument (optional):** $ARGUMENTS

## References

Read these before proceeding:
- `.claude/commands/wiki/references/article-format.md` — frontmatter schema and confidence levels
- `.claude/commands/wiki/references/quality-standards.md` — MCP routing table and validation outcomes

## Scope

By default, validates all articles. If the user provides an argument, treat it as a scope filter:
- A file path (e.g., `concepts/sla-tiers.md`) → validate that single article
- A tag (e.g., `#fsi`) → validate only articles with that tag
- No argument → validate all articles

## Process (execute in strict order)

### Step 1: Read the wiki index

Read `wiki/_index.md` to get the full article list. Apply scope filter if provided.

### Step 2: Validate high-confidence articles

For each article with `confidence: high` (within scope):

**2a.** Read the article. Parse frontmatter to get `tags`.

**2b.** Scan the article body for verifiable claims:
- Config property names and their stated defaults
- Version requirements (e.g., "requires CP 7.5+")
- Feature availability statements (e.g., "CL supports bidirectional links")
- Behavioral assertions (e.g., "mirror topics are read-only")
- CLI command syntax
- API endpoint details

**2c.** For each verifiable claim, query the appropriate MCP tool per the routing table:
- Config properties/defaults → `confluent-docs`
- Architecture patterns/best practices → `context7`
- Confluent Cloud features/APIs → `confluent-docs`

**2d.** Compare MCP response to wiki claim:

- **Drift detected**: Log to `wiki/_queue.md` under "Unverified Claims to Resolve" with:
  ```
  - [ ] <article path> line N: "<wiki claim>" — MCP finding: "<what MCP said>" — suggested: "<correction>"
  ```
- **Confirmed**: No action (don't add noise).

### Step 3: Check low-confidence articles for expansion potential

For articles with `confidence: low` (stubs):
1. Read the stub to see what topic it covers
2. Query relevant MCP tools to see if enough content exists to expand it
3. If expandable, add to `wiki/_queue.md` under "Articles to Expand":
   ```
   - [ ] wiki/<path> — MCP sources have sufficient content on <topic>; key points: <summary>
   ```

### Step 4: Write validation report

Ensure `outputs/reports/` directory exists (create if missing). Create `outputs/reports/wiki-validation-YYYY-MM-DD.md` with:
- Date and scope of validation
- Articles checked (count)
- Claims validated (count)
- Drift instances found (count and details)
- Stubs with expansion potential (count and list)
- Overall wiki health assessment

### Step 5: Offer auto-fix

Ask the user: "N claims drifted. Auto-fix now?"

If yes:
1. Apply corrections to article bodies
2. Update `last_updated` in frontmatter of each modified article
3. Clear the resolved items from `wiki/_queue.md`
4. Run `python tools/wiki-lint.py` to verify no breakage

If no:
- Leave findings in `wiki/_queue.md` for manual review
