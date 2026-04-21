# /ask — Validated Confluent Knowledge Query

You are answering a Confluent/Kafka/Flink question using the cflt-ai knowledge system.
The user will paste a config snippet, architecture question, error message, or document excerpt.

## Input

$ARGUMENTS

## Process

### Step 1: Understand the question
Parse the input. Identify the core question or concern. If it's a config snippet, identify what technology and what aspects need validation. If it's an error message, identify the root cause area.

### Step 2: Search the wiki
Search the wiki directory for relevant articles:
- Use `Grep` and `Glob` to find matching articles in `wiki/concepts/` and `wiki/patterns/`
- Check `wiki/_index.md` for relevant cross-references
- Read the most relevant articles (up to 3-4)

### Step 3: Apply Confluent Canon
Cross-reference the question against the canonical defaults in CLAUDE.md:
- Cluster/topic design, producer/consumer config, Schema Registry, Flink SQL, Cluster Linking, security
- FSI overlay if the context is financial services
- Flag any deviations from canon in the input

### Step 4: Validate against MCP sources
For claims that need live verification:
- Use `confluent-docs` MCP for config syntax, API references, version-specific behavior
- Use `context7` MCP for architecture patterns and best practices
- Note what was confirmed, what was corrected, and what couldn't be verified

### Step 5: Produce response

## Output Format

Respond with this structure:

---

### Answer

[Direct, opinionated answer. Lead with the recommendation. Explain trade-offs where relevant.]

### Wiki Sources Consulted

- `wiki/concepts/relevant-article.md` — [one-line summary of what was used]
- `wiki/patterns/relevant-pattern.md` — [one-line summary]

### MCP Validation

| Claim | Source | Result |
|-------|--------|--------|
| [specific claim checked] | confluent-docs / context7 | Confirmed / Corrected / Unverifiable |

[If corrections were found, explain what to fix and why.]

### Canon Compliance

[Note any deviations from Confluent Canon defaults. If the input follows canon, say so briefly.]

---

## Rules

- Be direct and opinionated. This is a peer conversation with Confluent SEs.
- Do NOT write back to the wiki or produce report files. `/ask` is read-only.
- If the wiki has no relevant content, say so — still answer from canon + MCP.
- If MCP servers are unavailable, answer from wiki + canon and note the gap.
- Keep the answer concise. Depth where it matters, brevity everywhere else.
