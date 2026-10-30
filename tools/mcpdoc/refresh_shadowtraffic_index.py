#!/usr/bin/env python3
"""Regenerate tools/mcpdoc/shadowtraffic-llms.txt from docs.shadowtraffic.io's
live sitemap.xml. ShadowTraffic publishes no llms.txt of its own, so this
hand-maintained index is what the `shadowtraffic-docs` MCP server (mcpdoc)
reads. Run manually, or via the scheduled refresh job — see this
directory's README.md.

Prints a diff (added/removed URLs) against the previous version so a human
can tell at a glance whether the wiki article
(wiki/patterns/shadowtraffic-confluent-cloud-datagen.md) needs a look.
"""
import re
import sys
import urllib.request
from pathlib import Path

SITEMAP_URL = "https://docs.shadowtraffic.io/sitemap.xml"
OUT_PATH = Path(__file__).parent / "shadowtraffic-llms.txt"
SKIP_PATHS = {"search"}

SECTION_TITLES = {
    "generator-configuration": "Generator Configuration — localConfigs/globalConfigs keys for a generator",
    "connections": "Connections — supported source/sink backends",
    "functions": "Functions — `_gen` value-generation functions",
    "function-modifiers": "Function Modifiers — wrap a `_gen` function to reshape its output",
    "fork": "Fork — per-key stateful/branching generation controls",
    "schedule": "Schedule — run duration/looping controls",
}
SECTION_ORDER = ["generator-configuration", "connections", "functions", "function-modifiers", "fork", "schedule"]


def humanize(slug: str) -> str:
    s = re.sub(r"(?<!^)(?=[A-Z])", " ", slug)
    s = s.replace("-", " ").replace("_", " ")
    return " ".join(w.capitalize() if not w.isupper() else w for w in s.split())


def fetch_urls() -> list[str]:
    with urllib.request.urlopen(SITEMAP_URL, timeout=15) as resp:
        xml = resp.read().decode("utf-8")
    return sorted(set(re.findall(r"<loc>([^<]+)</loc>", xml)))


def build_llms_txt(urls: list[str]) -> str:
    top_level, sections = [], {}
    for u in urls:
        path = u.replace("https://docs.shadowtraffic.io/", "").rstrip("/")
        if path in SKIP_PATHS:
            continue
        if "/" not in path:
            top_level.append((path, u))
            continue
        section, slug = path.split("/", 1)
        sections.setdefault(section, []).append((slug, u))

    lines = [
        "# ShadowTraffic",
        "",
        "> ShadowTraffic is a containerized service (`shadowtraffic/shadowtraffic`) for "
        "declaratively generating synthetic data into Kafka, relational databases, cloud "
        "storage, webhooks, and other backends from a single JSON config, driven by "
        "`_gen` functions instead of a hand-written producer. Third-party commercial "
        "product — docs.shadowtraffic.io is the authoritative source, no vendor "
        "MCP/llms.txt of its own (this file is regenerated from the site's sitemap.xml "
        "by tools/mcpdoc/refresh_shadowtraffic_index.py).",
        "",
        "## Getting started",
    ]
    for path, u in sorted(top_level):
        if path == "changelog":
            continue
        lines.append(f"- [{humanize(path) if path else 'Home'}]({u})")
    lines.append("")

    for section in SECTION_ORDER:
        items = sections.get(section, [])
        if not items:
            continue
        lines.append(f"## {SECTION_TITLES.get(section, section)}")
        for slug, u in sorted(items):
            lines.append(f"- [{humanize(slug)}]({u})")
        lines.append("")

    for path, u in top_level:
        if path == "changelog":
            lines.append("## Changelog")
            lines.append(f"- [Changelog]({u}): version history — check here when re-validating this index for new/renamed/removed pages")
            lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def extract_urls(text: str) -> set[str]:
    return set(re.findall(r"\((https://docs\.shadowtraffic\.io/[^)]*)\)", text))


def main() -> int:
    old_text = OUT_PATH.read_text() if OUT_PATH.exists() else ""
    old_urls = extract_urls(old_text)

    urls = fetch_urls()
    new_text = build_llms_txt(urls)
    new_urls = extract_urls(new_text)

    added = sorted(new_urls - old_urls)
    removed = sorted(old_urls - new_urls)

    if not added and not removed:
        print("No change: shadowtraffic-llms.txt already matches the live sitemap.")
        return 0

    OUT_PATH.write_text(new_text)
    print(f"Updated {OUT_PATH}")
    if added:
        print(f"\n+ {len(added)} new page(s):")
        for u in added:
            print(f"  + {u}")
    if removed:
        print(f"\n- {len(removed)} removed page(s):")
        for u in removed:
            print(f"  - {u}")
    print(
        "\nIf any added/removed page is relevant to "
        "wiki/patterns/shadowtraffic-confluent-cloud-datagen.md, review and update it "
        "(bump last_updated/last_validated) — this script only refreshes the MCP doc "
        "index, not the wiki article itself."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
