#!/usr/bin/env python3
"""
check-citations.py -- Resolve wiki citations against MANIFEST.yaml.

Parses all wiki article frontmatter, extracts fsi-dsp:// source citations,
and verifies each one resolves to a known ID in MANIFEST.yaml.

Usage: python tools/check-citations.py
Exit 0 if all resolve, exit 1 with details if any fail.
"""
import sys
from pathlib import Path

import yaml


def load_manifest(manifest_path: Path) -> set:
    """Return set of all stable IDs from MANIFEST.yaml."""
    data = yaml.safe_load(manifest_path.read_text())
    return {cap["id"] for cap in data.get("capabilities", [])}


def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown content."""
    if not content.startswith("---"):
        return {}
    end = content.find("---", 3)
    if end == -1:
        return {}
    try:
        return yaml.safe_load(content[3:end]) or {}
    except Exception:
        return {}


def main():
    root = Path(__file__).resolve().parent.parent
    manifest = root / "raw" / "repos" / "fsi-dsp" / "MANIFEST.yaml"

    if not manifest.exists():
        print("ERROR: MANIFEST.yaml not found at expected path", file=sys.stderr)
        print(f"  Expected: {manifest}", file=sys.stderr)
        sys.exit(1)

    known_ids = load_manifest(manifest)
    failures = []
    checked = 0

    for md in sorted((root / "wiki").rglob("*.md")):
        if md.name.startswith("_"):
            continue
        fm = parse_frontmatter(md.read_text(errors="replace"))
        for source in fm.get("sources", []):
            if isinstance(source, str) and source.startswith("fsi-dsp://"):
                checked += 1
                cited_id = source[len("fsi-dsp://"):]
                if cited_id not in known_ids:
                    rel = md.relative_to(root)
                    failures.append(f"{rel}: unresolvable citation '{source}'")

    if failures:
        print(f"Citation resolution failures ({len(failures)}):")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)

    print(f"All citations resolved ({checked} citations checked, {len(known_ids)} IDs in MANIFEST.yaml).")


if __name__ == "__main__":
    main()
