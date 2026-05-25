# /review — Document Evaluation Against Wiki + MCP Sources

You are evaluating a document (or multiple documents) for technical accuracy against the cflt-ai
knowledge system. The user will point at one or more files or paste content for review.

## Input

$ARGUMENTS

## Process

### Step 1: Parse arguments

Parse `$ARGUMENTS`:
- Extract `--output` value if present: `md` (default) | `docx` | `both`
- Extract `--overlay` value if present: customer overlay name (e.g., `acme-bank`)
- Remaining non-flag tokens are treated as file paths OR pasted content
- Validation rules:
  - If any specified file path does not exist, stop with: `Error: file not found: <path>`
  - If no file paths and no pasted content, stop with: `Error: no input specified`
  - If `--output` value is unrecognized, stop with: `Error: unknown --output value. Valid: md | docx | both`
  - If `--overlay` specifies a customer name that has no `canon/customer/<name>/overrides.yaml`, stop with: `Error: overlay not found: canon/customer/<name>/overrides.yaml`
- If `--output` is not provided, default to `md`.
- If `--overlay` is not provided, no customer overlay is active (base + industry layers only).

### Step 1.5: Load documents

- For each file path from Step 1, read the file
- If pasted content (no file paths), use it directly as a single document labeled `pasted-content`
- Label each document by its basename for claim attribution (e.g., `deck.md`, `runbook.md`)
- Identify file type from extension (`.md`, `.tfvars`, `.yaml`, `.yml`, `.txt`, `.tf`, `.json`) — treat all as text input
- Build a labeled corpus: `{ "deck.md": <content>, "vars.tfvars": <content> }`
- If `--overlay` was specified, load the customer overlay by calling `resolve_stack(customer=<overlay_name>)` from `canon/stack.py` to get the active canon config. Note the overlay-specific overrides for use in Steps 2.5 and 5.
- Identify the collective scope: what technologies, patterns, and claim domains are covered across all documents?

### Step 2: Extract verifiable claims

Scan each document in corpus order (if multiple docs, process each separately, section by section).

Extract claims using these five numbered categories, in document order:

1. **Config values** — specific property = value assertions (e.g., "acks=1 is recommended")
2. **Behavior assertions** — X does Y under condition Z (e.g., "consumers will rebalance when...")
3. **Architecture choices** — use X over Y for this use case (e.g., "prefer MirrorMaker2 for...")
4. **Metrics / limits / SLAs** — numbers, thresholds, latencies (e.g., "99.99% availability")
5. **Comparisons** — X is better/faster/safer than Y (e.g., "Avro is more efficient than JSON")

Stop when all sections are exhausted. Do not invent claims not in the document.

**Output claims as a YAML block BEFORE proceeding to Step 3.** This YAML intermediate is the
reproducibility anchor for deterministic claim extraction (REVW-01). Do not skip it and go
straight to table rendering.

```yaml
claims:
  - id: "<source-slug>-1"
    source_file: "<basename>"
    source_section: "<section heading or 'Introduction'>"
    category: config_value | behavior_assertion | architecture_choice | metric_sla | comparison
    text: "<exact claim text or close paraphrase>"
  - id: "<source-slug>-2"
    source_file: "<basename>"
    source_section: "<section heading or 'Introduction'>"
    category: config_value | behavior_assertion | architecture_choice | metric_sla | comparison
    text: "<exact claim text or close paraphrase>"
```

**Multi-document labeling:** Prefix claim IDs with a slug of the source filename.
- For `deck.md`: claim IDs are `deck-1`, `deck-2`, `deck-3`, ...
- For `runbook.md`: claim IDs are `runbook-1`, `runbook-2`, ...
- This prevents ID collision when claims from multiple documents are merged.
- A single undifferentiated claim pool for multi-doc input is forbidden.

### Step 2.5: Challenge premises

Before validating individual claims, interrogate the document's unstated assumptions.

Identify 3-5 premises the document implicitly assumes (NOT explicit claims — these are the deeper
structural assumptions the document's recommendations rest on).

For each premise, evaluate:
1. Does it hold for this customer's context?
2. If `--overlay` was specified: does the premise conflict with the customer overlay's overrides?
   (e.g., "under your FSI overlay, this premise about latency tolerance conflicts with
   `market_data: sub-millisecond`")
3. Check for logical gaps: does the premise require conditions the document never establishes?

Rate severity:
- **Critical** — blocks a key recommendation; the document's conclusion fails if this premise doesn't hold
- **Moderate** — weakens a claim; the recommendation still applies but with caveats
- **Minor** — pedantic; the document is still directionally correct

Output as a dedicated "## Premise Challenge" section in the report:

```markdown
## Premise Challenge

| # | Premise | Assumption | Challenge | Severity |
|---|---------|------------|-----------|----------|
| 1 | [what the document assumes] | [what must be true for this to hold] | [why it may not hold in this context] | Critical/Moderate/Minor |
```

If no `--overlay` is set, still challenge premises against base canon and FSI overlay (if content
is FSI-relevant). Always check FSI SLA tiers: sub-millisecond (market data), <10ms (risk),
<100ms (compliance), async (reconciliation).

### Step 3: Cross-reference against wiki

For each claim from the YAML block:
- Search `wiki/concepts/` and `wiki/patterns/` for relevant articles
- Compare the claim against wiki content
- Note: agreement, disagreement, or no wiki coverage

**Auto-stub on miss (WIKI-05):** If NO wiki articles match a claim topic:
1. Extract a topic slug from the claim text (lowercase, first 5 meaningful words, joined with hyphens)
2. Read `wiki/_queue.md`
3. Check if ANY existing line under `## Auto-Stubs` contains the primary keyword from the claim
4. If not already present, append to `wiki/_queue.md` under the `## Auto-Stubs` section:
   ```
   - [ ] <!-- auto-stub: <slug> --> wiki/concepts/<slug>.md — Auto-queued from /review
         Claim: "<claim text>" | Date: <YYYY-MM-DD> | Source: <source_file>
   ```
5. Continue evaluating the claim from canon + MCP even though wiki had no hit.

### Step 4: Validate against MCP sources

For claims where wiki coverage is absent or where the claim is particularly important:
- Use `confluent-docs` MCP for config values, syntax, and version-specific behavior
- Use `context7` MCP for architecture patterns and best practices
- Record the validation result (Confirmed / Corrected / Unverifiable) for each claim checked

#### Step 4.0.5: Skill consultation (advisory)

For each claim, consult the relevant streaming-skills-plugin skill alongside MCP.
MCP remains authoritative when verdicts conflict; skill verdict is annotated for
follow-up review. The four skills cover: Kafka Streams topology, Python Kafka
client, Schema Registry governance, CDC→Tableflow pipelines.

**For each claim from Step 4:**

1. Route the claim to a skill:
   ```bash
   python3 tools/skill_routing.py route "<claim text>"
   ```
   Output is a skill slug (e.g., `kafka-streams-programming`) or `—` for no match.

2. If a skill slug is returned, activate the skill:
   ```bash
   python3 tools/skill_routing.py activate <slug> --json
   ```
   This loads `SKILL.md` and extracts the matching FSI overlay block from
   `wiki/patterns/fsi-canon-overlay-for-confluent-skills.md`.

3. Read the skill's `SKILL.md` (path in activation output) plus any referenced
   sections under `references/` that are relevant to the claim. Use the skill's
   guidance to form a `skill_verdict` (one of `Confirmed`, `Corrected`,
   `Unverifiable`, `Out-of-scope`).

4. **Conflict handling:** if `skill_verdict != mcp_verdict`, keep MCP's verdict
   in the final row, but append a ⚠️ note in Corrections:
   > Skill (`<slug>`) and MCP disagree — MCP authoritative.
   > Skill said: `<one-line skill evidence>`.

5. **FSI overlay application:** if `activate_skill()` returned `applied_overrides`,
   carry those rows into the Canon Compliance check in Step 5. The overlay is
   canonical (per ADR-009 / `wiki/patterns/fsi-canon-overlay-for-confluent-skills.md`)
   — do not re-validate overlay overrides through MCP.

**Reporting:** the Claim Validation table in Step 6 gains two new columns,
`Skill` and `Skill Verdict`. For rows where no skill routed, both columns show
`—`. Track the unique skill slugs activated during this review for the
activity-log entry.

#### Step 4.1: Auditor-readonly payload-isolation claim flag (WIKI-03)

If a claim or paraphrase matches ANY of the following patterns (case-insensitive,
whitespace-normalized), flag it as `Corrected` with the canonical correction text below:

**Trigger patterns:**
1. "DeveloperRead on the cluster is sufficient for auditor isolation" (and paraphrases: "cluster-scoped DeveloperRead suffices", "cluster-wide read-only role for auditors")
2. "auditor binding can be at cluster scope" (and paraphrases: "auditor role at cluster level", "cluster-bound auditor role")
3. "any read-only role can be used for audit access" (and paraphrases: "generic read role for compliance", "DeveloperRead is fine for auditors")

**Canonical correction text (use verbatim):**

> DeveloperRead is consume-granting at the topic-prefix scope it's bound to; auditor isolation requires topic-scoped binding to `confluent-audit-log-events` + SR subjects ONLY, explicitly NOT to `payments.*` business topics (per layer-01 RBAC pattern). See `wiki/patterns/auditor-readonly-rbac-payload-isolation.md`.

This rule grounds the WIKI-03 requirement: `/review` MUST flag any cluster-scoped DeveloperRead claim
for auditor roles as a payload-isolation violation, with the topic-scoped binding workaround as the
correction.

### Step 5: Check canon compliance

Compare the document's recommendations against the active canon config:

- If `--overlay` was specified: compare against the overlay-resolved canon config (from `resolve_stack(customer=<overlay_name>)` output in Step 1.5), not just base canon
- If no overlay: compare against base + FSI canon defaults from `canon/base/defaults.yaml` and `canon/industry/fsi/overrides.yaml`
- Check: producer/consumer config defaults, Schema Registry governance, Flink SQL patterns, Cluster Linking / DR approach, security posture, FSI overlay (if applicable)
- Note deviations from overlay-specific overrides in the Canon Compliance table
- When overlay is active, add an "Overlay Override" column to the Canon Compliance table

Compliance table when overlay is active:
```markdown
| Area | Status | Overlay Override | Notes |
|------|--------|-----------------|-------|
```

Compliance table without overlay:
```markdown
| Area | Status | Notes |
|------|--------|-------|
```

### Step 6: Generate the report

Write the report with these sections in order:

#### Header
```markdown
# Review: <Document Title>

**Date:** YYYY-MM-DD
**Source files:** <space-separated list of input file paths, or "pasted content">
**Scope:** <technologies and claim domains covered>
**Claims extracted:** <total count across all documents>
```

#### ## Summary
2-3 sentence executive summary: overall accuracy, major findings, recommendation.

#### ## Claim Validation
- For single-doc input: organize by section/topic
- For multi-doc input: organize first by source file, then by section within each file
- Each claim row: `#`, `Claim`, `Wiki source`, `MCP source`, `Skill`, `Skill Verdict`, `Verdict`
  (`Verdict` = `Confirmed` / `Corrected` / `Unverifiable` — MCP-authoritative)
  (`Skill` = streaming-skills-plugin slug or `—`; `Skill Verdict` = same enum or `—`)
- After each section's table, list specific Corrections with explanation and source

```markdown
### <Section/Topic 1>

| # | Claim | Wiki | MCP | Skill | Skill Verdict | Verdict |
|---|-------|------|-----|-------|---------------|---------|
| deck-1 | [claim text] | [article or "—"] | [source or "—"] | [slug or "—"] | [verdict or "—"] | Confirmed / Corrected / Unverifiable |

**Corrections:**
- Claim #deck-N: [what's wrong and what the correct answer is, with source]
- (Append ⚠️ Skill-MCP conflict notes here when skill_verdict != mcp_verdict)
```

#### ## Premise Challenge
Insert the table produced in Step 2.5.

#### ## Canon Compliance
Insert the table produced in Step 5.

#### ## Gaps
Claims that could not be verified by wiki or MCP. These are candidates for further research or
auto-stub queuing.

#### ## Recommendations
Specific, actionable recommendations based on findings.

#### Provenance footer
```
Canon stack: <layers> | Hash: <hash> | MANIFEST: <version> | Floor: <model> | Generated: <ISO-8601>
```
- Call `provenance_footer()` from `canon/stack.py` for the canon hash part (layers + hash)
- Read MANIFEST.yaml version from `raw/repos/fsi-dsp/MANIFEST.yaml` (field: `version`)
- Default floor model to the model currently answering (e.g., `claude-sonnet-4-6`)
- Timestamp in ISO-8601 format

#### Write report file
- Write report to `outputs/reports/<slug>-review-<YYYY-MM-DD>.md`
  (create directory if it does not exist)
  where `<slug>` is derived from the first document's filename or first heading
- If `--output docx` or `--output both`: after writing the `.md` file, invoke:
  `python3 tools/review-to-docx.py outputs/reports/<slug>-review-<YYYY-MM-DD>.md`
  to generate the `.docx` alongside the `.md`
- If `--output both`: produce both `.md` and `.docx`
- Print the file path(s) and the Summary section to the user

#### Activity log emission
After writing the report file(s), append an activity log entry to `wiki/activity/YYYY-MM.md`
(create the file if the current month's file does not exist). Every invocation must emit an
activity log entry — no silent runs.

Follow the format defined in `wiki/activity/README.md`:

```markdown
## YYYY-MM-DDTHH:MM:SSZ
**Skill:** /review
**Overlay:** {overlay name from --overlay flag, or "base" if no overlay, or "base + fsi" if FSI-relevant content with no explicit overlay}
**Input:** {space-separated list of input file paths, or "pasted content" if no file paths}
**Output:** {report file path(s) written, e.g., "outputs/reports/deck-review-2026-04-28.md"}
**Canon stack:** {output of active_layers(), e.g., "base + industry/fsi"}
**Skills consulted:** {comma-separated list of streaming-skills-plugin slugs activated during this review, or "none" if no claim routed to a skill}
```

## Rules

- Be thorough. Extract ALL verifiable claims using the five numbered categories — do not skip any.
- Do NOT modify source documents or write back to the wiki. This is a read-only evaluation.
- Mode is always "report" — `/review` always writes a file. There is no ephemeral mode.
- The YAML claim block in Step 2 is mandatory — do not skip it and go straight to table rendering.
- For multi-doc input: label every claim by source file using the slug prefix. A single undifferentiated claim pool for multi-doc input is forbidden.
- If `--overlay` specifies a customer name that has no `canon/customer/<name>/overrides.yaml`, stop immediately with: `Error: overlay not found: canon/customer/<name>/overrides.yaml`
- Every invocation must emit an activity log entry — no silent runs.
- If MCP servers are unavailable, validate against wiki + canon only and note the limitation.
- Auto-stub fires on ALL wiki misses — coverage gaps are tracked to `wiki/_queue.md` automatically.
