# Article Format Specification

Reference document for all wiki skills. Defines frontmatter schema, article templates, and confidence levels.

## YAML Frontmatter Schema

Every wiki article must begin with this frontmatter block:

```yaml
---
title: <string>                    # Human-readable title
tags: [<tag1> <tag2> ...]          # Space-separated inside brackets
sources: [<path1>, <path2>]        # Paths to raw source files used
related: [<wiki-path1>, ...]       # Wiki-relative paths (no .md extension OK)
confidence: high | medium | low    # See Confidence Levels below
last_updated: YYYY-MM-DD           # Date of last substantive edit
---
```

### Required Fields
- `title`, `tags`, `confidence`, `last_updated`

### Optional Fields
- `sources` (omit if no raw source), `related` (omit only for orphan stubs)

## Confidence Levels

| Level | Meaning | Requirements |
|-------|---------|--------------|
| `high` | All verifiable claims checked against MCP sources | Every config property, default, version number, and feature availability statement validated via `confluent-docs` or `context7` |
| `medium` | Content from authoritative source but not MCP-validated | Compiled from official docs, repo READMEs, or expert knowledge; not yet checked via MCP tools |
| `low` | Stub or unverified content | Placeholder with minimal content; needs expansion and validation |

## Article Templates

### Concept Article

For explanatory content: what something is, how it works, why it matters.

```markdown
---
title: <Title>
tags: [...]
sources: [...]
related: [...]
confidence: high
last_updated: YYYY-MM-DD
---

# <Title>

## Summary

One paragraph (3-5 sentences) covering what this is and why it matters.

## Detail

### <Subsection>

Body content. Use tables for structured data. Use code blocks with language tags.

### <Subsection>

More content as needed.

## Related

- [Article Title](path/to/article.md) — one-line relationship description
```

### Pattern Article

For actionable patterns: how to do something, when to use it, what to watch for.

```markdown
---
title: <Title>
tags: [...]
sources: [...]
related: [...]
confidence: high
last_updated: YYYY-MM-DD
---

# <Title>

## Summary

One paragraph covering what this pattern does and its key trade-off.

## Pattern

### <Architecture / Setup / Configuration>

Describe the pattern structure.

### <Steps / Procedure>

Numbered steps if procedural.

## When to Use

Bullet list of scenarios where this pattern applies.

## Caveats

Bullet list of limitations, risks, or common mistakes.

## Related

- [Article Title](path/to/article.md) — one-line relationship description
```

### Stub Article

Minimal placeholder when a topic is identified but not yet written.

**Important:** The stub marker MUST use the exact format below — `wiki-lint.py` detects stubs by searching for `⚠️ Stub` (capital S, with emoji).

```markdown
---
title: <Title>
tags: [...]
sources: []
related: []
confidence: low
last_updated: YYYY-MM-DD
---

# <Title>

> ⚠️ Stub — LLM should expand this using confluent-docs MCP and raw/ sources.

## Summary

<!-- One paragraph summary. Used verbatim in _index.md -->

## Detail

<!-- Full article body -->

## Related

<!-- Wiki-internal links -->
```

For **pattern** stubs, replace `## Detail` with `## Pattern`, `## When to Use`, `## Caveats`.

### Report Template (for `/wiki:recommend` output)

Reports go to `outputs/reports/`, not into `wiki/`.

```markdown
---
title: <Report Title>
date: YYYY-MM-DD
query: "<original user question>"
wiki_sources: [<wiki articles consulted>]
claims_checked: <N>
claims_corrected: <N>
claims_unverifiable: <N>
---

# <Report Title>

## TL;DR

2-3 sentence answer.

## Analysis

Detailed analysis with subsections as needed.

## Comparison

| Criterion | Option A | Option B | ... |
|-----------|----------|----------|-----|
| ... | ... | ... | ... |

## Decision Framework

When to choose each option. Structured as conditional logic:
- **If [condition]** → Option A because [reason]
- **If [condition]** → Option B because [reason]

## Caveats

What this recommendation does NOT cover or where it might break down.

---

*Validated against Confluent docs via MCP (YYYY-MM-DD). N claims checked, M corrected, K unverifiable.*
```

## Cross-Link Format

Within article bodies, use wiki-relative paths:

```markdown
See [SLA Tiers](concepts/sla-tiers.md) for tier definitions.
```

In frontmatter `related:` arrays, use wiki-relative paths without `wiki/` prefix:

```yaml
related: [concepts/sla-tiers, patterns/dr-cluster-linking]
```
