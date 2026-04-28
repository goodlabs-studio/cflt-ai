#!/usr/bin/env python3
"""
wiki-lint.py — health check for the cflt-ai wiki.
Usage: python tools/wiki-lint.py [--full] [--fix]
"""
import argparse
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


def get_wiki_root() -> Path:
    env_root = os.environ.get("CFLT_WIKI_ROOT")
    if env_root:
        return Path(env_root)
    here = Path(__file__).resolve().parent
    for candidate in [here.parent, here]:
        if (candidate / "wiki").is_dir():
            return candidate
    sys.exit("Could not locate wiki/ directory. Set CFLT_WIKI_ROOT.")


def parse_frontmatter(content: str) -> dict:
    import yaml
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    try:
        return yaml.safe_load(content[3:end]) or {}
    except Exception:
        return {}


def lint_wiki(root: Path, full: bool = False) -> dict:
    wiki = root / "wiki"
    findings = {
        "stubs": [],
        "broken_links": [],
        "orphans": [],
        "stale": [],
        "low_confidence": [],
        "unverified": [],
    }

    all_md = {str(p.relative_to(root)) for p in wiki.rglob("*.md")}
    stale_cutoff = datetime.now() - timedelta(days=90)

    for md in sorted(wiki.rglob("*.md")):
        if md.name.startswith("_"):
            continue
        rel = str(md.relative_to(root))
        content = md.read_text(errors="replace")
        fm = parse_frontmatter(content)

        # Stubs
        if "⚠️ Stub" in content:
            findings["stubs"].append(rel)

        # Low confidence
        if fm.get("confidence") == "low":
            findings["low_confidence"].append(rel)

        # Unverified inline flags
        if "⚠️ unverified" in content:
            findings["unverified"].append(rel)

        # Stale (last_updated > 90 days ago)
        if full and fm.get("last_updated"):
            try:
                lu = datetime.strptime(str(fm["last_updated"]), "%Y-%m-%d")
                if lu < stale_cutoff:
                    findings["stale"].append(rel)
            except ValueError:
                pass

        # Broken wiki-internal links
        links = re.findall(r"\[.*?\]\((wiki/[^)#]+(?:#[^)]*)?)\)", content)
        for link in links:
            if link not in all_md:
                findings["broken_links"].append(f"{rel} → {link}")

    # Orphans: articles not referenced in _index.md
    if full:
        index = wiki / "_index.md"
        if index.exists():
            index_content = index.read_text()
            for md in sorted(wiki.rglob("*.md")):
                if md.name.startswith("_"):
                    continue
                rel = str(md.relative_to(root))
                if rel not in index_content:
                    findings["orphans"].append(rel)

    return findings


def main():
    parser = argparse.ArgumentParser(description="Lint the cflt-ai wiki")
    parser.add_argument("--full", action="store_true", help="Full lint including orphans and stale")
    args = parser.parse_args()

    root = get_wiki_root()
    findings = lint_wiki(root, full=args.full)

    total = sum(len(v) for v in findings.values())
    if total == 0:
        print("✓ Wiki looks clean.")
        sys.exit(0)

    print(f"Wiki lint findings ({total} total):\n")
    labels = {
        "stubs": "Stubs (need expansion)",
        "broken_links": "Broken internal links",
        "orphans": "Orphaned articles (not in _index.md)",
        "stale": "Stale articles (>90 days)",
        "low_confidence": "Low confidence articles",
        "unverified": "Unverified inline claims",
    }
    for key, items in findings.items():
        if items:
            print(f"  {labels[key]} ({len(items)})")
            for item in items:
                print(f"    - {item}")
            print()


if __name__ == "__main__":
    main()
