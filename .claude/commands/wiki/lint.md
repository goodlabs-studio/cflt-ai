# /wiki:lint — Health check with auto-triage

You are the wiki lint skill. You run the lint tool, triage findings, auto-fix what you can, and queue the rest.

## References

Read these before proceeding:
- `.claude/commands/wiki/references/quality-standards.md` — queue format and backlink requirements

## Process (execute in strict order)

### Step 1: Run full lint

Run `python tools/wiki-lint.py --full` and capture the output.

### Step 2: Parse findings

Categorize all findings into:
- **Stubs**: Articles marked as stubs needing expansion
- **Broken links**: Internal links pointing to non-existent articles
- **Orphans**: Articles not referenced in `wiki/_index.md`
- **Stale**: Articles with `last_updated` older than 90 days
- **Low confidence**: Articles with `confidence: low`
- **Unverified**: Articles containing `> unverified` inline markers

### Step 3: Write findings to queue

Update `wiki/_queue.md`:
1. Clear the `## Lint Findings` section (remove previous lint findings only — preserve other sections)
2. Write all current findings under `## Lint Findings` using the format:
   ```
   - [ ] <category>: <finding detail>
   ```

Also populate other queue sections if appropriate:
- Stubs → add to "Stubs to Create" if not already listed
- Low confidence articles with enough content for MCP validation → add to "Articles to Expand"

### Step 4: Auto-fix what's possible

For each auto-fixable issue:

**Broken links**:
1. Check if the target article was renamed (search `wiki/` for the article title)
2. If an obvious rename is found, update the link
3. If no match, leave in queue for manual resolution

**Orphans**:
1. Read the orphaned article to determine its section (concept, pattern, incident, etc.)
2. Add the missing entry to `wiki/_index.md` under the appropriate section
3. Follow the existing format: `[Title](path) — summary — #tags`

**Stale articles** (>90 days):
1. Read the article content
2. If the content appears still accurate (no version-specific claims that may have changed), update `last_updated` to today
3. If the content has version-specific claims, flag for `/wiki:validate` review instead

### Step 5: Run stats

Run `python tools/wiki-stats.py` and capture the output.

### Step 6: Print summary

Report:
- Finding count by category
- Auto-fixes applied (count and details)
- Remaining manual items (count)
- Wiki stats summary from Step 5
