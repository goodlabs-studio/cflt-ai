#!/usr/bin/env python3
"""Regenerate tools/mcpdoc/headroom-llms.txt from the official Headroom GitHub
repository documentation. Headroom publishes docs as .mdx files in a Next.js
site structure. This script builds an llms.txt index for MCP integration.

Run manually, or via scheduled refresh job to keep docs in sync with upstream.
"""
import re
import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from dataclasses import dataclass

# Headroom GitHub documentation structure
GITHUB_API_BASE = "https://api.github.com/repos/headroomlabs-ai/headroom/contents"
DOCS_PATH = "docs/content/docs"
OUT_PATH = Path(__file__).parent / "headroom-llms.txt"
CONFIG_PATH = Path(__file__).parent / "headroom-config.json"

# Sections to prioritize (order matters for llms.txt)
SECTION_ORDER = [
    ("quickstart", "Getting Started"),
    ("installation", "Installation & Setup"),
    ("configuration", "Configuration Reference"),
    ("proxy", "Proxy Operation"),
    ("cache-optimization|ccr", "Optimization & Caching"),
    ("security-model", "Security & Privacy"),
    ("api-reference", "API Reference"),
    ("troubleshooting|errors", "Troubleshooting"),
]

def fetch_github_tree(path: str) -> list:
    """Fetch file tree from GitHub API."""
    url = f"{GITHUB_API_BASE}/{path}"
    headers = {"Accept": "application/vnd.github.v3+json"}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return []

def categorize_file(filename: str) -> str:
    """Categorize markdown file into section."""
    filename_lower = filename.lower()

    # Match against known sections
    for patterns, section_name in SECTION_ORDER:
        for pattern in patterns.split("|"):
            if pattern in filename_lower:
                return section_name

    # Default categorizations
    if "example" in filename_lower or "recipe" in filename_lower or "integration" in filename_lower:
        return "Examples & Integrations"
    if "sdk" in filename_lower or "langchain" in filename_lower or "litellm" in filename_lower:
        return "SDK Integrations"

    return "Documentation"

def generate_llms_txt(files: list) -> str:
    """Generate llms.txt format documentation index."""

    # Organize by section
    sections = {}
    for patterns, section_name in SECTION_ORDER:
        sections[section_name] = []
    sections["Examples & Integrations"] = []
    sections["SDK Integrations"] = []
    sections["Documentation"] = []

    base_url = "https://github.com/headroomlabs-ai/headroom/blob/main/docs/content/docs"

    for file in sorted(files, key=lambda f: f["name"]):
        name = file["name"]

        # Skip certain files
        if name in ["README.md", ".gitkeep", "index.md", "meta.json", "index.mdx"]:
            continue

        if not (name.endswith(".md") or name.endswith(".mdx")):
            continue

        section = categorize_file(name)
        title = name.replace(".mdx", "").replace(".md", "").replace("-", " ").title()
        url = f"{base_url}/{name}"

        sections[section].append((title, url))

    # Build output
    lines = [
        "# Headroom AI Documentation",
        "Official documentation for Headroom, the local context optimization proxy for Claude and other LLMs.",
        "",
        "**Repository:** https://github.com/headroomlabs-ai/headroom",
        "**Last Updated:** " + __import__("datetime").datetime.now().isoformat(),
        "",
    ]

    # Add sections in order
    for patterns, section_name in SECTION_ORDER:
        section_files = sections.get(section_name, [])
        if section_files:
            lines.append(f"## {section_name}")
            lines.append("")
            for title, url in section_files:
                lines.append(f"- [{title}]({url})")
            lines.append("")

    # Add SDK Integrations
    if sections.get("SDK Integrations"):
        lines.append("## SDK Integrations")
        lines.append("")
        for title, url in sections["SDK Integrations"]:
            lines.append(f"- [{title}]({url})")
        lines.append("")

    # Add Examples
    if sections.get("Examples & Integrations"):
        lines.append("## Examples & Integrations")
        lines.append("")
        for title, url in sections["Examples & Integrations"]:
            lines.append(f"- [{title}]({url})")
        lines.append("")

    # Add remaining files
    if sections.get("Documentation"):
        lines.append("## Additional Documentation")
        lines.append("")
        for title, url in sections["Documentation"]:
            lines.append(f"- [{title}]({url})")
        lines.append("")

    return "\n".join(lines)

def main():
    print("Fetching Headroom documentation from GitHub...", file=sys.stderr)
    files = fetch_github_tree(DOCS_PATH)

    if not files:
        print("Error: No documentation files found. Check GitHub API access.", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(files)} documentation files.", file=sys.stderr)

    # Generate llms.txt
    content = generate_llms_txt(files)

    # Write llms.txt
    OUT_PATH.write_text(content)
    print(f"✓ Generated {OUT_PATH}", file=sys.stderr)

    # Update config.json with correct absolute path
    config = {
        "llms_txt": str(OUT_PATH.resolve()),
        "fetcher": "web",
        "timeout": 30
    }
    CONFIG_PATH.write_text(json.dumps(config, indent=2))
    print(f"✓ Updated {CONFIG_PATH}", file=sys.stderr)

    print(f"\nHeadroom MCP index ready. {len(files)} docs indexed.", file=sys.stderr)
    print(f"Next: Configure in ~/.claude/settings.local.json", file=sys.stderr)

if __name__ == "__main__":
    main()
