# Architecture

**Analysis Date:** 2026-04-28

## Pattern Overview

**Overall:** Knowledge-driven AI skill system with canonical overlay architecture and mandatory verification gates.

**Key Characteristics:**
- Claude Code as the runtime; no custom application server
- Four-layer canonical stack (base canon → industry → customer → engagement) with composition, not inheritance
- Multiple personas (IC/SE, Embedded SA, SRE/Operator) with mode-driven behavior (`ephemeral`, `report`, `reconsolidate`)
- Mandatory multi-gate validation: canon compliance → fsi-dsp artifact coverage → Confluent docs schema validation → mcp-confluent state check
- Wiki as authoritative knowledge layer with LLM-maintained metadata (backlinks, queue, stats)
- Activity log as immutable audit trail per engagement overlay

## Layers

**Canonical Override Stack:**
- Purpose: Manage defaults across base canon, industry (FSI), customer, and engagement overlays
- Location: `CLAUDE.md` (base canon), `raw/repos/fsi-dsp/` (industry/ADRs), customer fork overlays
- Contains: Architectural defaults (topic partitions, producer acks, Schema Registry modes, Flink patterns, DR approaches, security posture)
- Depends on: fsi-dsp MANIFEST.yaml for versioning and capability declarations
- Used by: All skills validate inputs against active stack; every artifact records provenance

**Wiki Knowledge Layer:**
- Purpose: Validated Kafka/Flink/Schema Registry/Confluent architecture patterns and FSI-specific guidance
- Location: `wiki/` with structured subdirectories
- Contains:
  - `concepts/` — foundational topics (exactly-once semantics, consumer lag, Flink checkpointing, SLA tiers)
  - `patterns/` — operational patterns (DR topologies, DLQ design, governance automation, topic naming)
  - `synthesis/` — derived artifacts (ADR index, cross-referenced architectures)
- Depends on: MCP sources (confluent-docs, context7) for validation; fsi-dsp for reference implementations
- Used by: `/ask` (direct search), `/review` (claim validation), `/wiki:validate` (drift detection)

**Skill Orchestration Layer:**
- Purpose: Route user intent to appropriate skill with mode modifier
- Location: `.claude/commands/`
- Contains:
  - `ask.md` — query skill (mode: `ephemeral`)
  - `review.md` — document evaluation (mode: `report`)
  - `wiki/` subskills — maintenance and ingest
- Depends on: Wiki, canon stack, MCP servers
- Used by: User invokes `/ask`, `/review`, `/wiki:*` commands

**MCP Bridge Layer:**
- Purpose: Live validation against Confluent docs, architecture patterns, and Cloud API state
- Location: `.mcp.json`
- Contains: Three MCP servers
  - `context7` — Confluent architecture patterns and best practices
  - `confluent-docs` — Current Confluent documentation (llms.txt format)
  - `mcp-confluent` — Confluent Cloud API for topology inspection and management
- Depends on: External MCP servers (Upstash, LangChain, Confluent)
- Used by: `/ask` (validation step), `/review` (claim checking), act rail (state verification)

**Output & Artifact Layer:**
- Purpose: Persist skill outputs to committed/reviewed locations
- Location:
  - `outputs/reports/` — review reports (`.md`, eventually `.docx`)
  - `wiki/` — discovered articles (via `/wiki:recommend`)
  - `raw/` — ingest queue (ingestion staging)
- Depends on: Skill invocation with mode='report'
- Used by: `/review` (reports), `/wiki:recommend` (articles), `/wiki:lint` (queue management)

**Maintenance & Audit Layer:**
- Purpose: Track knowledge health, changes, and skill invocations
- Location:
  - `wiki/_index.md` — master article registry (LLM-maintained)
  - `wiki/_graph.md` — backlink registry (LLM-maintained)
  - `wiki/_queue.md` — discovered gaps and stale content
  - `<overlay>/activity/YYYY-MM.md` — activity log per overlay
- Depends on: Skill output
- Used by: `/wiki:lint` (gap detection), `/wiki:validate` (staleness checks)

## Data Flow

**Query Flow (/ask):**

1. User paste config/question via `/ask` → Claude Code dispatches to `ask.md`
2. Step 1: Parse input and identify core question (config validation, architecture, error diagnosis)
3. Step 2: Search wiki using Glob/Grep → read top 3-4 relevant articles
4. Step 3: Cross-reference against CLAUDE.md canon stack (active overlay composition)
5. Step 4: Validate claims against MCP sources (confluent-docs for syntax, context7 for patterns)
6. Step 5: Produce response with sources, MCP validation table, canon compliance note
7. Output: In-conversation response (ephemeral, not committed)

**Document Review Flow (/review):**

1. User specifies file or paste content via `/review` → Claude Code dispatches to `review.md`
2. Step 1: Acquire document (read file or use pasted content)
3. Step 2: Extract all verifiable claims (config values, behavior assertions, architecture choices, metrics)
4. Step 3: Search wiki for coverage per claim
5. Step 4: Validate claim against MCP sources where not covered or critical
6. Step 5: Cross-check against canon compliance
7. Step 6: Write report to `outputs/reports/<slug>-review-<YYYY-MM-DD>.md` with claim table and corrections
8. Output: Markdown report with provenance footer (canon stack hash, model floors, MCP versions)

**Wiki Ingest Flow (/wiki:ingest):**

1. User registers source URLs/docs in `raw/_ingest.md` → Claude runs `/wiki:ingest`
2. Step 1: Read source materials from `raw/articles/`, `raw/papers/`, URLs
3. Step 2: Extract key concepts and patterns
4. Step 3: Validate claims against MCP sources (confluent-docs, context7)
5. Step 4: Write article to `wiki/concepts/` or `wiki/patterns/` with frontmatter (title, confidence, tags, sources, last_validated)
6. Step 5: Register in `wiki/_index.md` and `wiki/_graph.md` (backlinks)
7. Output: Wiki articles, updated indexes; unverifiable claims → `wiki/_queue.md`

**Skill Invocation Audit Trail:**

1. Every skill run appends to `<overlay>/activity/YYYY-MM.md`
2. Schema: skill name, mode, timestamp, user, wiki articles consulted, MCP calls made, artifacts produced, gate results, canon stack hash, model floors
3. Purpose: Audit trail for compliance and performance regression detection
4. Nightly harness runs golden test cases and records floor performance

**State Management:**

- **Wiki metadata:** LLM-maintained indexes (`_index.md`, `_graph.md`) updated on every skill that writes articles
- **Queue:** `wiki/_queue.md` collects lint findings, stubs to write, stale articles, coverage gaps
- **Activity log:** Sequential append-only record per overlay; no edits, no deletion
- **Canon stack:** Immutable at time of artifact generation; every output records which stack version was active

## Key Abstractions

**Article (Wiki Entity):**
- Purpose: Atomic unit of knowledge with provenance
- Examples: `wiki/concepts/exactly-once-semantics.md`, `wiki/patterns/dr-cluster-linking.md`
- Pattern: YAML frontmatter (title, confidence, tags, sources, last_validated) + markdown body with internal/external links
- Metadata: Registered in `_index.md`, backlinks recorded in `_graph.md`

**Skill (Claude Code Command):**
- Purpose: Reusable operation that composes wiki, canon, and MCP
- Examples: `/ask` (validate + respond), `/review` (extract claims + validate + report), `/wiki:lint` (scan → parse → queue)
- Pattern: Markdown file in `.claude/commands/` with Step 1-N process + output format
- Dispatch: Claude Code reads file, follows the prompts, produces output

**Canon Stack (Overlayable Defaults):**
- Purpose: Manage architectural defaults across customer engagements
- Examples: Producer `acks=all`, Consumer `auto.offset.reset=earliest`, Schema Registry `BACKWARD` compatibility
- Pattern: Base canon in `CLAUDE.md`; industry/FSI overlay in `raw/repos/fsi-dsp/docs/adr/`; customer overrides in forked CLAUDE.md or ADR layer
- Composition: At skill invocation, active stack is (base canon) + (industry) + (customer) + (engagement), in precedence order
- Provenance: Every artifact footer records which stack version was active

**MCP Server Bridge:**
- Purpose: Connect to live Confluent ecosystem without direct client coding
- Examples: confluent-docs (raw docs as LLM input), context7 (pattern extraction), mcp-confluent (Cloud API)
- Pattern: Declared in `.mcp.json`, invoked conditionally in skills (not every skill uses every server)
- Validation gates: confluent-docs validates config syntax; context7 validates patterns; mcp-confluent validates state

**Activity Log Entry:**
- Purpose: Immutable audit record of every skill run
- Examples: `wiki/activity/2026-04.md`, `<customer-overlay>/activity/2026-04.md`
- Pattern: YAML front matter (date, skill, mode, user, result) + list of sources + list of MCP calls + artifacts produced
- Immutability: Never edited, only appended; nightly harness reads for regression detection

## Entry Points

**Claude Code Command Dispatch (/ask, /review, /wiki:*):**
- Location: `.claude/commands/ask.md`, `.claude/commands/review.md`, `.claude/commands/wiki/*.md`
- Triggers: User types `/ask`, `/review`, `/wiki:lint`, etc. in Claude Code chat
- Responsibilities:
  - Parse user input (query, document, intent)
  - Orchestrate wiki search, MCP calls, canon checks
  - Format output and write to appropriate location (ephemeral, report, or wiki)
  - Append activity log entry

**First-Run Setup (/bin/setup):**
- Location: `bin/setup`
- Triggers: User runs `./bin/setup` after clone
- Responsibilities:
  - Check Claude Code install
  - Prompt for ANTHROPIC_API_KEY or Claude subscription auth
  - Optional: Initialize fsi-dsp submodule
  - Optional: Set Confluent Cloud credentials for mcp-confluent
  - Optional: Enable MCP auto-approve in `~/.claude/settings.json`

**Flox Environment (flox activate):**
- Location: `.flox/floxfile.toml` (not shown, managed by Flox)
- Triggers: User runs `flox activate` in project directory
- Responsibilities:
  - Install Python 3, Node.js, pip dependencies (PyYAML, etc.)
  - Set CFLT_WIKI_ROOT environment variable
  - Enable `wiki-search`, `wiki-lint`, `wiki-stats`, `wiki-compile` CLI tools

**CLI Tool Invocation (wiki-* scripts):**
- Location: `tools/wiki-*.py`
- Triggers: User runs `wiki-lint`, `wiki-search`, `wiki-stats` from command line
- Responsibilities:
  - wiki-lint: Scan wiki for stubs, broken links, orphans, stale articles
  - wiki-search: Full-text search across all articles
  - wiki-stats: Coverage metrics (article count, backlinks, confidence distribution)

## Error Handling

**Strategy:** Layered fallback with explicit gap reporting.

**Patterns:**

- **Wiki miss:** If `/ask` finds no relevant wiki articles, answer from canon + MCP and note the gap. Queue the topic in `wiki/_queue.md` for `/wiki:recommend`.
- **MCP unavailable:** If confluent-docs or context7 is unreachable, answer from wiki + canon and note which MCP calls failed.
- **Claim unverifiable:** If a claim in `/review` cannot be verified via wiki or MCP, mark as "Unverifiable" and flag for manual follow-up.
- **State conflict:** If mcp-confluent reports a cluster state that contradicts the plan, halt the act rail and report the conflict with suggested remediation.
- **Canon conflict:** If an input contradicts the active canon stack, flag the deviation and ask for confirmation (embedded SA mode) or reject outright (SRE mode).

## Cross-Cutting Concerns

**Logging:**
- Activity logs in `<overlay>/activity/YYYY-MM.md` — skill name, timestamp, user, sources, MCP calls, artifacts, gate results
- Console output for CLI tools (`wiki-lint`, `wiki-search`) — status, findings, counts
- No request/response logging; activity log is the audit trail

**Validation:**
- Canon compliance: Every input cross-checked against active overlay stack
- Schema validation: MCP sources validate config syntax (confluent-docs), architecture patterns (context7), Cloud API state (mcp-confluent)
- Artifact integrity: Every written article checked by `wiki-lint` for broken links, orphans, stale dates

**Authentication:**
- Claude Code auth: ANTHROPIC_API_KEY or `~/.claude/.credentials.json` (Claude subscription)
- Confluent Cloud auth: `~/.config/confluent/mcp.env` with CC API key/secret (optional for mcp-confluent)
- No service account or bot token; user-owned credentials

**Authorization:**
- Role-based profiles (planned Phase 3b): `read-only.json`, `engineer.json`, `break-glass.json` for SRE mode (`/dsp:apply`)
- Currently: All users have same access (ephemeral knowledge, report generation)
- Future: mcp-confluent tool gating by profile

**Testing:**
- Golden test cases in `tests/golden/` (planned Phase 1)
- Floor model regression detection: nightly harness runs cases against Haiku, Sonnet, Opus targets
- Structured evaluation: `tests/golden/ask/`, `tests/golden/review/`, `tests/golden/act/`

---

*Architecture analysis: 2026-04-28*
