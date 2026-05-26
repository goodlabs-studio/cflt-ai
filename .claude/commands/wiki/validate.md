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

### Step 1.5: Preload navigation bundle for full sweeps (≥10 articles)

After scope is resolved in Step 1, count the articles you will validate. **If
the count is 10 or more**, preload the navigation bundle before iterating —
this is the CAG-style optimization documented in
`outputs/spikes/cag-canon-cache-2026-05-25.md`. Modelled savings: ~88% of
input-token cost on Sonnet vs. re-reading canon + wiki TOC + skill headers
across every article.

**How to preload:**

1. Run the bundle assembler:
   ```bash
   python3 tools/canon_preload.py emit --bundle navigation
   ```
   This emits a deterministic, cache-friendly concatenation of CLAUDE.md +
   MANIFEST.yaml + canon/{base,industry/fsi,customer/acme-bank} + wiki/_index +
   wiki/_graph + wiki/_queue + 4 skill SKILL.md files (~53k tokens).

2. **Read the bundle output into your working context** as the authoritative
   reference for the rest of this validation pass. Treat the files inside it as
   already-loaded — do NOT re-read CLAUDE.md, MANIFEST.yaml, canon files,
   wiki/_index, wiki/_graph, or any skill SKILL.md during per-article work in
   Step 2 below. They're already in your context window.

3. **Per-article work still does targeted Reads** for the specific article
   under validation. The bundle only covers the cross-cutting context that
   would otherwise repeat 50+ times across the sweep.

**When NOT to preload** (skip Step 1.5 entirely):

- Scope is a single article path (`/wiki:validate concepts/sla-tiers.md`)
- Scope is a small tag with <10 hits (`#linuxone` if it only matches 4 articles)
- Any sweep with fewer than 10 articles

For these cases, the cache-write premium isn't paid back within the run; just
do the targeted reads inline in Step 2.

**Why the threshold:** Anthropic's prompt-prefix cache has a 5-minute ephemeral
TTL and a ~1.25× write premium. Modelled break-even is ~3 cached reads of the
same prefix; the 10-article threshold gives margin for the bundle assembly
+ per-article reasoning overhead. See the spike report for the full cost model.

**Record preload usage** in the activity log entry below: `**Preload bundle:**
navigation` (or `none` if Step 1.5 was skipped).

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

**2e. Skill consultation (advisory).** In parallel with the MCP query, route the
claim through the streaming-skills-plugin skills:

```bash
python3 tools/skill_routing.py route "<claim text>"
```

If a skill slug is returned, activate the skill (`python3 tools/skill_routing.py
activate <slug> --json`), read its `SKILL.md` plus any topical sections under
`references/`, and form an advisory `skill_verdict`.

- **Skill-MCP conflict** (skill verdict != MCP verdict): log under a NEW section
  `## Skill-MCP Conflicts` in `wiki/_queue.md` (separate from "Unverified Claims
  to Resolve" so reviewers can spot-check skill quality independently). Format:
  ```
  - [ ] <article path> line N: "<wiki claim>" — MCP: "<mcp finding>" — Skill (<slug>): "<skill evidence>"
  ```
  MCP remains authoritative for the auto-fix path in Step 5; the skill conflict
  is informational.
- **Skill agrees with MCP**: no action.
- **No skill routed**: no action.

Track the unique skill slugs activated during this validation pass for the
activity-log entry below.

### Step 3: Check low-confidence articles for expansion potential

For articles with `confidence: low` (stubs):
1. Read the stub to see what topic it covers
2. **Route the topic through skill routing** (`python3 tools/skill_routing.py
   route "<stub topic>"`). If a skill is returned, prefer that skill's
   `references/` body as the primary content source — it has cached domain
   knowledge plus the FSI overlay baked in. MCP becomes the secondary
   fact-check.
3. Query relevant MCP tools to see if enough content exists to expand it
4. If expandable, add to `wiki/_queue.md` under "Articles to Expand":
   ```
   - [ ] wiki/<path> — MCP sources have sufficient content on <topic>; key points: <summary> | Skill: <slug or "—">
   ```

### Step 4: Write validation report

Ensure `outputs/reports/` directory exists (create if missing). Create `outputs/reports/wiki-validation-YYYY-MM-DD.md` with:
- Date and scope of validation
- Articles checked (count)
- Claims validated (count)
- Drift instances found (count and details)
- Stubs with expansion potential (count and list)
- **Skills consulted** (comma-separated list of streaming-skills-plugin slugs activated, or "none")
- **Skill-MCP conflicts** (count and brief list — full detail in `wiki/_queue.md` under that section)
- **Preload bundle** (`navigation` if Step 1.5 fired; `none` if skipped for under-threshold sweep)
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
