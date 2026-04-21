# /wiki:recommend — Draft, validate, write back

You are the wiki recommendation skill. You answer user questions using the wiki as primary source, validate against MCP, write a report, and reconsolidate new knowledge back into the wiki.

The user's question is: $ARGUMENTS

## References

Read these before proceeding:
- `.claude/commands/wiki/references/article-format.md` — report template and article formats
- `.claude/commands/wiki/references/quality-standards.md` — MCP routing, validation rules, writeback criteria

## Process (execute in strict order)

### Step 1: Recall

Search the wiki for relevant articles:
1. Extract key terms from the user's question
2. Use Grep across `wiki/` for those terms
3. Read the top matching articles (up to 5-6)
4. Also read `wiki/_index.md` to check for related articles you might have missed
5. Note which wiki articles inform your answer and which topics have gaps

### Step 2: Draft

Write an initial recommendation from wiki knowledge. Structure per the report template in `references/article-format.md`:
- **TL;DR**: 2-3 sentence answer
- **Analysis**: Detailed breakdown with subsections
- **Comparison table**: If multiple options exist
- **Decision Framework**: Conditional logic for choosing between options
- **Caveats**: Limitations and blind spots

Do NOT output the draft to the user yet — it needs validation first.

### Step 3: Verify

Extract every verifiable claim from your draft:

1. Config property names and defaults → query `confluent-docs`
2. Feature availability and version requirements → query `confluent-docs`
3. Architecture patterns and trade-offs → query `context7`

For each claim, record the outcome:
- **Confirmed**: MCP agrees
- **Corrected**: MCP contradicts — note the correction
- **Unverifiable**: MCP has no data — mark in the report

### Step 4: Correct

Apply all corrections from Step 3 to the draft. For unverifiable claims, add the inline marker:
```
> ⚠️ unverified — [claim]
```

### Step 5: Write report

Ensure `outputs/reports/` directory exists (create if missing). Save the final report to `outputs/reports/<slug>.md` where `<slug>` is derived from the user's question (lowercase, hyphens, no special chars).

Include the validation footer:
```
*Validated against Confluent docs via MCP (YYYY-MM-DD). N claims checked, M corrected, K unverifiable.*
```

Also output the report content to the user.

### Step 6: Reconsolidate

Check if verification produced new knowledge not already in the wiki:

**6a. Corrections to existing articles**: If an MCP check revealed that a wiki article has incorrect information, update that article now. Bump its `last_updated`.

**6b. New stubs needed**: If a topic gap was discovered (the user's question touches a topic with no wiki article), add it to `wiki/_queue.md` under "Stubs to Create".

**6c. Index and graph updates**: If any wiki articles were modified in 6a, update `wiki/_index.md` (if summary changed) and `wiki/_graph.md` (if new cross-links were added).

### Step 7: Print summary

Report to the user:
- Report path
- Claims checked (count)
- Corrections applied to draft (count)
- Wiki articles updated via reconsolidation (count and paths)
- New stubs queued (count)
