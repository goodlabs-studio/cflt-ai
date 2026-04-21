# /wiki:evaluate — Evaluate external documents against wiki and MCP sources

You are the wiki evaluation skill. You systematically extract and validate claims from external recommendation documents, cross-reference against compiled wiki knowledge and fsi-dsp reference code, and reconsolidate findings back into the wiki.

**Input document(s):** $ARGUMENTS

## References

Read these before proceeding:
- `.claude/commands/wiki/references/article-format.md` — frontmatter schema and confidence levels
- `.claude/commands/wiki/references/quality-standards.md` — MCP routing table and validation outcomes

## Process (execute in strict order)

### Step 1: Recall — Load compiled knowledge baseline

1. Read the input document(s) specified in the arguments.
2. Read `wiki/_index.md` and identify all overlapping wiki articles.
3. Read each overlapping wiki article (compiled knowledge baseline).
4. Read fsi-dsp reference implementations for code baseline:
   - `raw/repos/fsi-dsp/reference/java-producer/.../FsiProducer.java`
   - `raw/repos/fsi-dsp/reference/java-consumer/.../FsiConsumer.java`
   - `raw/repos/fsi-dsp/reference/python-producer/fsi_producer.py`
   - `raw/repos/fsi-dsp/reference/python-consumer/fsi_consumer.py`

### Step 2: Extract claims

Parse every verifiable claim from the input documents per quality-standards.md definition:
- Config property names and their stated defaults
- Version requirements
- Feature availability statements
- Behavioral assertions
- CLI syntax
- Architecture pattern recommendations

Organize claims into categories: Producer Config, Consumer Config, Infrastructure, Architecture Patterns, CC Operations.

### Step 3: Validate — MCP claim-by-claim

Route each claim to the appropriate MCP tool per the routing table:
- Config properties/defaults → `confluent-docs`
- Architecture patterns/best practices → `context7`
- CC features/APIs → `confluent-docs`
- Infrastructure claims (Azure, AWS, GCP) → web search for provider docs

For each claim, record the MCP response and classify the outcome.

### Step 4: Cross-reference — Wiki + Code deltas

**4A. Wiki inconsistencies:** For each claim, compare against compiled wiki knowledge. Flag:
- Document claims that contradict wiki content
- Wiki content that the documents are missing (enrichment opportunities)
- Gaps where neither wiki nor documents cover a topic

**4B. Code deltas:** For each config recommendation, compare against fsi-dsp reference implementations. Flag:
- Settings where document recommendation differs from reference code
- Settings recommended in documents but missing from reference code
- Settings in reference code but not mentioned in documents
- Classify delta type: Profile Mismatch, Missing from Code, Missing from Docs, Minor Variance

### Step 5: Classify outcomes

Each claim gets one of:
- **Confirmed** — MCP agrees, wiki consistent, code aligned
- **Corrected** — MCP contradicts; update source
- **Unverifiable** — MCP has no data; mark with `> ⚠️ unverified`
- **Wiki-Inconsistent** — Document and wiki disagree; determine which is correct via MCP
- **Code-Delta** — Document recommendation differs from fsi-dsp reference code

### Step 6: Write report

Save to `outputs/reports/<slug>-evaluation-YYYY-MM-DD.md` with:
- Full claim-by-claim validation results (Step 3)
- Wiki inconsistencies found (Step 4A)
- Code deltas logged (Step 4B)
- Corrections applied (Step 7)
- Validation footer: `*Validated against Confluent docs via MCP (YYYY-MM-DD). N claims checked, M corrected, K unverifiable.*`

### Step 7: Reconsolidate

Per quality-standards.md writeback criteria:

1. **Corrected claims** → update source documents with corrections
2. **Wiki drift found** → update wiki articles, bump `last_updated`
3. **Topic gaps** → add stubs to `wiki/_queue.md` under "Stubs to Create"
4. **Cross-links** → update `wiki/_graph.md` with new backlinks
5. **Code deltas** → update fsi-dsp reference implementations where the document recommendation is correct; log as TODOs where further analysis is needed
6. **Ingest queue** → add source documents to `raw/_ingest.md` for compilation into new wiki articles

### Step 8: Print summary

Report:
- Claims checked (count)
- Corrections applied (count and details)
- Wiki articles updated (count and paths)
- Stubs queued (count)
- Code deltas resolved vs logged (counts)
- Report path
