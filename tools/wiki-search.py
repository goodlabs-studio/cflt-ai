#!/usr/bin/env python3
"""
wiki-search.py — naive full-text search over the wiki.
Usage: python tools/wiki-search.py "<query>" [--top N] [--path-only]
Also usable as a Claude tool via CLI.
"""
import argparse
import os
import re
import sys
from pathlib import Path


def get_wiki_root() -> Path:
    env_root = os.environ.get("CFLT_WIKI_ROOT")
    if env_root:
        return Path(env_root)
    # Walk up from this file to find wiki/
    here = Path(__file__).resolve().parent
    for candidate in [here.parent, here]:
        if (candidate / "wiki").is_dir():
            return candidate
    sys.exit("Could not locate wiki/ directory. Set CFLT_WIKI_ROOT.")


def score(text: str, terms: list[str]) -> int:
    text_lower = text.lower()
    return sum(text_lower.count(t.lower()) for t in terms)


def search(query: str, top_n: int = 10) -> list[dict]:
    root = get_wiki_root()
    wiki = root / "wiki"
    terms = query.split()
    results = []

    for md in sorted(wiki.rglob("*.md")):
        if md.name.startswith("_"):
            continue
        content = md.read_text(errors="replace")
        s = score(content, terms)
        if s > 0:
            # Extract first non-frontmatter, non-empty line as excerpt
            lines = [l.strip() for l in content.splitlines()
                     if l.strip() and not l.startswith("---") and not l.startswith("#")]
            excerpt = lines[0][:120] if lines else ""
            results.append({
                "path": str(md.relative_to(root)),
                "score": s,
                "excerpt": excerpt,
            })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_n]


def main():
    parser = argparse.ArgumentParser(description="Search the cflt-ai wiki")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--top", type=int, default=10, help="Max results (default: 10)")
    parser.add_argument("--path-only", action="store_true", help="Print paths only")
    args = parser.parse_args()

    results = search(args.query, args.top)

    if not results:
        print("No results.")
        sys.exit(0)

    for r in results:
        if args.path_only:
            print(r["path"])
        else:
            print(f"[{r['score']:>3}]  {r['path']}")
            if r["excerpt"]:
                print(f"       {r['excerpt']}")
            print()


if __name__ == "__main__":
    main()
