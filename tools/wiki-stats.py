#!/usr/bin/env python3
"""
wiki-stats.py — coverage and size report for the cflt-ai wiki.
Usage: python tools/wiki-stats.py
"""
import os
import sys
from pathlib import Path
from collections import Counter


def get_wiki_root() -> Path:
    env_root = os.environ.get("CFLT_WIKI_ROOT")
    if env_root:
        return Path(env_root)
    here = Path(__file__).resolve().parent
    for candidate in [here.parent, here]:
        if (candidate / "wiki").is_dir():
            return candidate
    sys.exit("Could not locate wiki/ directory. Set CFLT_WIKI_ROOT.")


def main():
    root = get_wiki_root()
    wiki = root / "wiki"
    raw = root / "raw"

    articles = [p for p in wiki.rglob("*.md") if not p.name.startswith("_")]
    raw_files = list(raw.rglob("*.md")) + list(raw.rglob("*.pdf"))
    raw_files = [f for f in raw_files if f.name not in ("_ingest.md", ".gitkeep")]

    total_words = 0
    tag_counter: Counter = Counter()
    conf_counter: Counter = Counter()
    section_counter: Counter = Counter()

    for md in articles:
        content = md.read_text(errors="replace")
        words = len(content.split())
        total_words += words
        section_counter[md.parent.name] += 1

        # Parse frontmatter tags/confidence
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                import yaml
                try:
                    fm = yaml.safe_load(content[3:end]) or {}
                    for tag in fm.get("tags", []):
                        tag_counter[tag] += 1
                    conf = fm.get("confidence", "unknown")
                    conf_counter[conf] += 1
                except Exception:
                    pass

    print(f"\n{─*50}")
    print(f"  cflt-ai wiki stats")
    print(f"{─*50}")
    print(f"  Articles:       {len(articles)}")
    print(f"  Total words:    {total_words:,}")
    print(f"  Raw sources:    {len(raw_files)}")
    print()
    print(f"  By section:")
    for section, count in sorted(section_counter.items()):
        print(f"    {section:<20} {count}")
    print()
    print(f"  By confidence:")
    for conf, count in sorted(conf_counter.items()):
        print(f"    {conf:<20} {count}")
    print()
    print(f"  Top tags:")
    for tag, count in tag_counter.most_common(10):
        print(f"    {tag:<20} {count}")
    print(f"{─*50}\n")


if __name__ == "__main__":
    main()
