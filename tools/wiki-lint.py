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


DECAY_DAYS = 90


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


def check_decay(fm: dict, last_validated_fallback_field: str = "last_updated") -> bool:
    """Return True if the article has confidence:high and last_validated is stale (>DECAY_DAYS old)."""
    if fm.get("confidence") != "high":
        return False
    lv_raw = fm.get("last_validated") or fm.get(last_validated_fallback_field)
    if not lv_raw:
        return False
    try:
        lv_date = datetime.strptime(str(lv_raw), "%Y-%m-%d")
    except ValueError:
        return False
    return lv_date < (datetime.now() - timedelta(days=DECAY_DAYS))


def apply_decay_fix(content: str) -> tuple:
    """Demote confidence:high to confidence:medium in front matter only.

    Returns (changed: bool, new_content: str).
    """
    if not content.startswith("---"):
        return (False, content)
    end_idx = content.find("---", 3)
    if end_idx == -1:
        return (False, content)
    front = content[:end_idx + 3]
    body = content[end_idx + 3:]
    new_front = re.sub(r'confidence:\s*high', 'confidence: medium', front, count=1)
    if new_front == front:
        return (False, content)
    return (True, new_front + body)


def lint_wiki(root: Path, full: bool = False, fix: bool = False) -> dict:
    wiki = root / "wiki"
    findings = {
        "stubs": [],
        "broken_links": [],
        "orphans": [],
        "stale": [],
        "low_confidence": [],
        "unverified": [],
        "decayed": [],
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

        # Decay rule (WIKI-03/04): confidence:high with stale last_validated
        if check_decay(fm):
            findings["decayed"].append(rel)
            if fix:
                changed, new_content = apply_decay_fix(content)
                if changed:
                    md.write_text(new_content)

        # Broken wiki-internal links
        links = re.findall(r"\[.*?\]\((wiki/[^)#]+(?:#[^)]*)?)\)", content)
        for link in links:
            if link not in all_md:
                findings["broken_links"].append(f"{rel} → {link}")

    # Orphans: articles not referenced in _index.md
    # _index.md uses paths relative to the wiki dir (e.g. "concepts/foo.md"),
    # so compare against wiki-relative paths, not project-root-relative ones.
    if full:
        index = wiki / "_index.md"
        if index.exists():
            index_content = index.read_text()
            for md in sorted(wiki.rglob("*.md")):
                if md.name.startswith("_"):
                    continue
                rel_wiki = str(md.relative_to(wiki))
                if rel_wiki not in index_content:
                    findings["orphans"].append(str(md.relative_to(root)))

    return findings


def main():
    parser = argparse.ArgumentParser(description="Lint the cflt-ai wiki")
    parser.add_argument("--full", action="store_true", help="Full lint including orphans and stale")
    parser.add_argument("--fix", action="store_true", help="Auto-fix: demote stale confidence:high to medium")
    args = parser.parse_args()

    if args.fix:
        args.full = True  # --fix implies --full

    root = get_wiki_root()
    findings = lint_wiki(root, full=args.full, fix=args.fix)

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
        "decayed": "Decayed articles (confidence demoted)",
    }
    for key, items in findings.items():
        if items:
            print(f"  {labels[key]} ({len(items)})")
            for item in items:
                print(f"    - {item}")
            print()


if __name__ == "__main__":
    main()
