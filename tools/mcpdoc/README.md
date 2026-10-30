# ShadowTraffic MCP doc source

ShadowTraffic (docs.shadowtraffic.io) publishes no `llms.txt` of its own, so
this directory hand-rolls the equivalent so the `mcpdoc` server (the same
tool that backs this project's `confluent-docs` MCP entry) can serve it —
see the `shadowtraffic-docs` entry in `.mcp.json`.

- `shadowtraffic-llms.txt` — the index `mcpdoc` reads. Generated from
  docs.shadowtraffic.io's `sitemap.xml`, not hand-written — don't edit
  directly, re-run the refresh script instead.
- `shadowtraffic-config.json` — mcpdoc's `--json` config. `llms_txt` is
  repo-relative; mcpdoc resolves it against its working directory, and
  `bin/mcp-launch` sets that to the repo root. So no per-machine edits are
  needed — `.mcp.json` calls `bin/mcp-launch shadowtraffic-docs`, which
  derives the repo root from its own location.
- **On demand:** `shadowtraffic-docs` (and `headroom-docs`) can be kept out
  of the default session via `disabledMcpjsonServers` in
  `.claude/settings.local.json`. Enable one for a session with `/mcp`
  (toggle the server), or remove it from that list to make it permanent.
- `refresh_shadowtraffic_index.py` — re-fetches the live sitemap and
  regenerates `shadowtraffic-llms.txt`, printing an added/removed-page diff
  so you know if `wiki/patterns/shadowtraffic-confluent-cloud-datagen.md`
  needs a look. Run manually any time:
  ```bash
  python3 tools/mcpdoc/refresh_shadowtraffic_index.py
  ```
  Also runs weekly via a local macOS LaunchAgent
  (`~/Library/LaunchAgents/studio.goodlabs.shadowtraffic-docs-refresh.plist`,
  logs to `~/Library/Logs/shadowtraffic-docs-refresh.log`) so the index
  doesn't silently go stale as ShadowTraffic adds/renames/removes doc pages.
  That job deliberately only edits the local file — it does not commit or
  push; check `git status` on `shadowtraffic-llms.txt` periodically and
  commit when it's changed. `fetch_docs` itself always pulls the live page
  content on every call — the only staleness risk this addresses is the
  *index of pages*, not page content.

Per `CLAUDE.md`'s Confluent Canon: for any ShadowTraffic question, call
`shadowtraffic-docs` (`list_doc_sources` then `fetch_docs`) the same way
`confluent-docs` is used for Confluent questions — don't answer from
training data alone.
