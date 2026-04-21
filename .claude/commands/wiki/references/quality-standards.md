# Quality Standards

Reference document for all wiki skills. Defines MCP validation rules, routing, inline markers, and writeback criteria.

## MCP Validation Rules

### Mandatory Validation

All `confidence: high` articles MUST have every verifiable claim checked against an MCP source. A "verifiable claim" is any of:

- Config property name (e.g., `min.insync.replicas`)
- Config default value (e.g., "defaults to 5000ms")
- Version requirement (e.g., "requires Confluent Platform 7.5+")
- Feature availability (e.g., "Cluster Linking supports bidirectional links")
- Behavioral assertion (e.g., "mirror topics are read-only until promoted")
- API endpoint or CLI syntax

### MCP Routing Table

| Claim Type | Primary MCP Tool | Fallback |
|------------|-----------------|----------|
| Config property names and defaults | `confluent-docs` | `context7` |
| Flink SQL syntax and behavior | `confluent-docs` | — |
| Connector configuration | `confluent-docs` | — |
| Architecture patterns and best practices | `context7` | `confluent-docs` |
| Feature availability (CC vs CP vs CFK) | `confluent-docs` | — |
| API versions and endpoints | `confluent-docs` | — |
| Event-driven patterns (CQRS, Saga, Outbox) | `context7` | — |
| Competitive positioning | Neither — use CLAUDE.md canon | — |

### Validation Outcomes

- **Confirmed**: MCP source agrees with wiki claim. No action needed.
- **Corrected**: MCP source contradicts wiki claim. Update the article, set `last_updated`, log in `_queue.md` if manual review needed.
- **Unverifiable**: MCP sources have no information on this claim. Mark inline with `> unverified` marker. Do NOT downgrade confidence for a single unverifiable claim — only if the majority of claims are unverifiable.

## Inline Markers

### Unverified Claim

When a claim cannot be validated via MCP, mark it inline. **Must include the ⚠️ emoji** — `wiki-lint.py` detects unverified claims by searching for `⚠️ unverified`:

```markdown
> ⚠️ unverified — [the specific claim that could not be verified]
```

### Stub Marker

Articles that are placeholders use. **Must include the ⚠️ emoji and capital S** — `wiki-lint.py` detects stubs by searching for `⚠️ Stub`:

```markdown
> ⚠️ Stub — LLM should expand this using confluent-docs MCP and raw/ sources.
```

## Writeback Criteria

When `/wiki:recommend` or `/wiki:validate` produces new knowledge, it MUST flow back to the wiki. Specifically:

1. **Corrected claims**: Update the article body, bump `last_updated`
2. **New facts discovered**: Add to existing article or create stub in `_queue.md`
3. **Topic gaps identified**: Add entry to `_queue.md` under "Stubs to Create"
4. **Cross-links discovered**: Update `_graph.md` with new backlinks

### When NOT to Write Back

- Recommendation-specific analysis (stays in `outputs/reports/`)
- User-specific context or scenarios
- Speculative or opinion-based content

## Backlink Requirements

Every new article MUST have:
- At least 1 inbound link in `_graph.md` (some other article points to it)
- At least 1 outbound link in `_graph.md` (it points to some other article)

If no natural backlinks exist, link to the closest concept article or to `concepts/fsi-data-streaming-platform.md` as the root node.

## Index Requirements

Every new article MUST have an entry in `wiki/_index.md` under the appropriate section (Concepts, Patterns, Incidents, Releases, Synthesis).

Format:
```
[Title](path/to/article.md) — one-line summary — #tag1 #tag2
```

## Queue Format

Entries in `wiki/_queue.md` follow these section formats:

### Stubs to Create
```
- [ ] wiki/concepts/<slug>.md — brief description of needed content
```

### Articles to Expand
```
- [ ] wiki/concepts/<slug>.md — what is missing
```

### Unverified Claims to Resolve
```
- [ ] <article path> line N: "<claim>" — MCP finding: "<what MCP said>" — suggested: "<correction>"
```

### Lint Findings
```
- [ ] <category>: <finding detail>
```
