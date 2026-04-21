# /review — Document Evaluation Against Wiki + MCP Sources

You are evaluating a document for technical accuracy against the cflt-ai knowledge system.
The user will point at a file or paste content for review.

## Input

$ARGUMENTS

## Process

### Step 1: Acquire the document
- If the input is a file path, read it
- If it's pasted content, use it directly
- Identify the document's scope: what technologies, patterns, and claims does it cover?

### Step 2: Extract verifiable claims
Scan the document and extract every verifiable technical claim. A claim is verifiable if it:
- States a specific configuration value or default
- Asserts behavior of a Confluent/Kafka/Flink component
- Describes an architecture pattern or recommended approach
- References specific metrics, limits, or SLAs
- Makes a comparison between approaches

Organize claims by section/topic.

### Step 3: Cross-reference against wiki
For each claim:
- Search `wiki/concepts/` and `wiki/patterns/` for relevant articles
- Compare the claim against wiki content
- Note: agreement, disagreement, or no wiki coverage

### Step 4: Validate against MCP sources
For claims where wiki coverage is absent or where the claim is particularly important:
- Use `confluent-docs` for config values, syntax, and version-specific behavior
- Use `context7` for architecture patterns and best practices
- Record the validation result

### Step 5: Check canon compliance
Compare the document's recommendations against CLAUDE.md Confluent Canon:
- Producer/consumer config defaults
- Schema Registry governance
- Flink SQL patterns
- Cluster Linking / DR approach
- Security posture
- FSI overlay (if applicable)

### Step 6: Generate the report

Create the output directory if it doesn't exist, then write the report.

## Output

Write a report to `outputs/reports/<slug>-review-<YYYY-MM-DD>.md` where `<slug>` is derived from the document filename or first heading.

### Report Format

```markdown
# Review: <Document Title>

**Date:** YYYY-MM-DD
**Source:** <filename or "pasted content">
**Scope:** <technologies covered>
**Claims extracted:** <count>

## Summary

[2-3 sentence executive summary: overall accuracy, major findings, recommendation]

## Claim Validation

### <Section/Topic 1>

| # | Claim | Wiki | MCP | Verdict |
|---|-------|------|-----|---------|
| 1 | [claim text] | [article or "—"] | [source or "—"] | Confirmed / Corrected / Unverifiable |
| 2 | ... | ... | ... | ... |

**Corrections:**
- Claim #N: [what's wrong and what the correct answer is, with source]

### <Section/Topic 2>
[repeat]

## Canon Compliance

| Area | Status | Notes |
|------|--------|-------|
| Producer config | Aligned / Deviates | [details] |
| Consumer config | Aligned / Deviates | [details] |
| Schema Registry | Aligned / Deviates | [details] |
| ... | ... | ... |

## Gaps

[Claims that could not be verified by wiki or MCP. These are candidates for further research.]

## Recommendations

1. [Specific, actionable recommendation]
2. [...]
```

## Rules

- Be thorough. Extract ALL verifiable claims, not just the obvious ones.
- Do NOT modify the source document or write back to the wiki. This is a read-only evaluation.
- If MCP servers are unavailable, validate against wiki + canon only and note the limitation.
- Use the exact report format above — consumers depend on the structure.
- After writing the report, tell the user the file path and print the Summary section.
