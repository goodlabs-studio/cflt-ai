# External Integrations

**Analysis Date:** 2026-04-28

## APIs & External Services

**Confluent Documentation:**
- Confluent Cloud REST API - Live schema, topic, and cluster queries
  - SDK/Client: `@confluentinc/mcp-confluent`
  - Auth: Confluent Cloud API key/secret via `CONFLUENT_MCP_ENV_FILE` environment variable
  - Location: `~/.config/confluent/mcp.env`

**Architecture & Patterns:**
- Upstash Context7 - Confluent canon patterns and event-driven architecture documentation
  - SDK/Client: `@upstash/context7-mcp`
  - No authentication required (public service)

**Documentation Indexing:**
- LangChain MCPdoc Server - Indexes and searches external documentation via llms.txt format
  - SDK/Client: `@langchain/mcpdoc-server`
  - Target: `https://docs.confluent.io/llms.txt`
  - No authentication required

## Data Storage

**Wiki & Knowledge Base:**
- Local filesystem (git-tracked)
  - Location: `wiki/` directory with subdirectories: `concepts/`, `patterns/`, `synthesis/`, `incidents/`, `releases/`
  - Format: Markdown with YAML frontmatter
  - Indexing: Internal full-text search via `wiki-search.py`

**Raw Sources:**
- Local filesystem (git submodule and ingestion queue)
  - Location: `raw/` directory
  - Contains: fsi-dsp submodule (`raw/repos/fsi-dsp/`), pending ingest queue (`raw/_ingest.md`)
  - Formats: Markdown, PDF, Ansible YAML, Terraform HCL, Python/Java reference code

**Generated Artifacts:**
- Local filesystem (gitignored)
  - Location: `outputs/` directory
  - Contains: Generated reports and review documents

**Caching:**
- None - full wiki scanned on each query

## Authentication & Identity

**Claude Code:**
- Provider: Anthropic (Claude Code native)
- Implementation:
  - Option A: Claude Max/Pro subscription (stored in `~/.claude/.credentials.json`)
  - Option B: Anthropic API key (environment variable `ANTHROPIC_API_KEY`)
  - Both configured during `bin/setup` initialization

**Confluent Cloud:**
- Provider: Confluent (optional, for live cluster queries)
- Implementation:
  - API key/secret authentication
  - Environment file: `~/.config/confluent/mcp.env`
  - Env vars: `CONFLUENT_CLOUD_API_KEY`, `CONFLUENT_CLOUD_API_SECRET`
  - Configured during `bin/setup` initialization (optional step)

## Monitoring & Observability

**Error Tracking:**
- None - errors logged to console or returned in structured responses

**Logs:**
- Ephemeral session logs (Claude Code console)
- Activity logging: `wiki/activity/` and customer overlay paths (planned in Phase 0+)
  - Logs: skill invocation, timestamp, user, sources consulted, MCP calls, artifacts produced, gates passed/failed

## CI/CD & Deployment

**Hosting:**
- Claude Code (cloud-hosted by Anthropic)
- GitHub repositories: `goodlabs-studio/cflt-ai` (main), optional `goodlabs-studio/fsi-dsp` (submodule)

**CI Pipeline:**
- GitHub Actions
  - Workflow: `.github/workflows/wiki-lint.yml`
  - Triggers: Pull requests and pushes to `main`
  - Checks: Wiki structure validation (broken links, stubs, orphans, confidence levels)
  - Blocking gates: Wiki linting must pass before merge

**Artifact Distribution:**
- Generated reports written to `outputs/reports/` with structured naming (`<slug>-review-<date>.md`)
- Wiki articles published directly in git repository

## Environment Configuration

**Required Environment Variables:**
- `ANTHROPIC_API_KEY` - Anthropic API key (alternative to Claude subscription)
- `CONFLUENT_MCP_ENV_FILE` - Path to Confluent Cloud credentials file (optional, default: `~/.config/confluent/mcp.env`)
- `CFLT_WIKI_ROOT` - Override wiki root directory (default: auto-detected from script location)

**Optional Environment Variables:**
- `BASH_VERSION` / `ZSH_VERSION` - Shell detection for profile configuration during setup

**Secrets Location:**
- `~/.config/confluent/mcp.env` - Confluent Cloud API credentials (local, not committed)
- `~/.claude/.credentials.json` - Claude subscription credentials (local, not committed, Anthropic-managed)
- `$ANTHROPIC_API_KEY` - Environment variable (shell profile, local, not committed)

## Webhooks & Callbacks

**Incoming:**
- None - read-only knowledge system

**Outgoing:**
- GitHub API - Implicit via Claude Code's git operations (PR creation, branch management, commits)
  - Uses local git config for authentication (SSH key or token)
  - No explicit webhook configuration

## MCP Server Architecture

All MCP servers declared in `.mcp.json` with standard `command` + `args` format:

**context7:**
```json
{
  "command": "npx",
  "args": ["-y", "@upstash/context7-mcp"]
}
```
- Provides: Confluent canon patterns and architecture knowledge
- No auth required
- Always-on for `/ask` and `/review` skills

**confluent-docs:**
```json
{
  "command": "npx",
  "args": ["-y", "@langchain/mcpdoc-server", "--url", "https://docs.confluent.io/llms.txt"]
}
```
- Provides: Live Confluent documentation indexing
- No auth required
- Always-on for validation steps

**mcp-confluent:**
```json
{
  "command": "npx",
  "args": ["-y", "@confluentinc/mcp-confluent", "--env-file", "${CONFLUENT_MCP_ENV_FILE}"]
}
```
- Provides: Confluent Cloud control plane (topic management, schema inspection, Flink SQL)
- Auth: API key/secret via environment file
- Optional - enabled only if credentials present
- Gated by read-only / engineer / break-glass profiles (Phase 3c)

## Service Dependencies

**External Services Used (Read-Only):**
- Upstash Context7 service
- docs.confluent.io (via llms.txt)
- Confluent Cloud API (optional, if credentials provided)
- developer.confluent.io, www.confluent.io, support.confluent.io (for documentation web fetches)

**Internal Services:**
- GitHub (for repository hosting and CI/CD)
- Anthropic Claude API (for LLM inference and Claude Code host)

---

*Integration audit: 2026-04-28*
