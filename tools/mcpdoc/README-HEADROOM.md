# Headroom MCP Documentation Server

This directory provides an MCP (Model Context Protocol) server for live Headroom documentation verification.

## Files

- **`headroom-llms.txt`** — Generated index of all Headroom docs (59 .mdx files from the official GitHub repo). Automatically refreshed to stay in sync.
- **`headroom-config.json`** — mcpdoc configuration pointing to `headroom-llms.txt` by absolute path.
- **`refresh_headroom_index.py`** — Script that fetches the live Headroom docs from GitHub and regenerates the index.

## Setup

The MCP server is configured in `~/.claude/settings.local.json`:

```json
{
  "enabledMcpServers": ["headroom-docs"],
  "mcpServers": {
    "headroom-docs": {
      "command": "python",
      "args": ["-m", "anthropic.types.message", "tools/mcpdoc/headroom-docs.py"],
      "disabled": false
    }
  }
}
```

**OR** use the simpler mcpdoc approach with the official mcpdoc CLI if installed.

## Refreshing the Index

To pull the latest Headroom documentation:

```bash
python3 tools/mcpdoc/refresh_headroom_index.py
```

This:
1. Fetches the live Headroom docs from `github.com/headroomlabs-ai/headroom/docs/content/docs/`
2. Regenerates `headroom-llms.txt` with all 59 .mdx files
3. Updates `headroom-config.json` with the absolute path

**Scheduled refresh:** You can set up a LaunchAgent (macOS) or systemd timer (Linux) to run this weekly, similar to `shadowtraffic-docs`. See `refresh_shadowtraffic_index.py` for the pattern.

## Usage in Claude Code

Once configured, use Headroom MCP to verify claims:

```bash
# Inside Claude Code:
# "Using headroom-docs MCP, verify that cache mode is safe for production"
# "Search headroom-docs for: proxy configuration options"
# "Verify the --mode flag documentation in headroom-docs"
```

### Example Queries

```
headroom-docs: How does prefix caching work?
headroom-docs: What is the difference between cache and token modes?
headroom-docs: How do I install Headroom?
headroom-docs: What environment variables does Headroom support?
headroom-docs: Is there a Docker installation?
headroom-docs: How do I troubleshoot cache misses?
```

## Configuration in settings.local.json

Add this to `~/.claude/settings.local.json`:

```json
{
  "enabledMcpServers": [
    "context7",
    "confluent-docs",
    "mcp-confluent",
    "terraform",
    "dynatrace",
    "grafana",
    "headroom-docs"
  ]
}
```

Then restart Claude Code.

## Verification Workflow

When documenting or verifying Headroom claims:

1. **Make a claim:** "Headroom cache mode is safe for production"
2. **Verify with MCP:** Query headroom-docs for cache mode documentation
3. **Cross-reference:** Compare MCP result with your local usage (32-day test, 9,068 requests)
4. **Document:** Include source attribution

## How This Differs from `shadowtraffic-docs`

| Aspect | Headroom | ShadowTraffic |
|--------|----------|--------------|
| **Source** | GitHub repo (/docs/content/docs) | docs.shadowtraffic.io/sitemap.xml |
| **File format** | .mdx (React) | HTML (web) |
| **File count** | 59 docs | ~40 pages |
| **Update frequency** | Manual or scheduled | Automated weekly |
| **Content type** | Markdown with React components | Generated HTML |

## Troubleshooting

### MCP server not available

```bash
# Check if headroom-docs is enabled in settings
grep -A5 "headroom-docs" ~/.claude/settings.local.json

# Verify the config file exists
ls -l tools/mcpdoc/headroom-config.json

# Regenerate the index
python3 tools/mcpdoc/refresh_headroom_index.py
```

### Index is stale

Run the refresh script:
```bash
python3 tools/mcpdoc/refresh_headroom_index.py
```

This will fetch the latest docs from GitHub and rebuild the index.

### GitHub API rate limits

If you hit rate limits, wait 1 hour or use an authenticated request (requires GitHub token).

---

**Related:** `CLAUDE.md` — MCP Server Availability section  
**See also:** `README.md` — ShadowTraffic MCP setup pattern
