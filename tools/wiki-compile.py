#!/usr/bin/env python3
"""
wiki-compile.py — incremental compiler from raw/ into wiki/.
Reads raw/_ingest.md, processes pending entries, and prints instructions
for the LLM agent to follow. Does not itself call the LLM.

Usage: python tools/wiki-compile.py [--delta] [--dry-run]
"""
import argparse
import os
import sys
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


def parse_ingest_queue(root: Path) -> list[dict]:
    ingest = root / "raw" / "_ingest.md"
    if not ingest.exists():
        return []

    content = ingest.read_text()
    # Extract pending block between "## Pending" and "## Processed"
    pending_match = content.find("## Pending")
    processed_match = content.find("## Processed")
    if pending_match == -1:
        return []

    section = content[pending_match:processed_match] if processed_match != -1 else content[pending_match:]

    entries = []
    current = {}
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("- path:"):
            if current:
                entries.append(current)
            current = {"path": line.split("path:", 1)[1].strip()}
        elif line.startswith("source_url:") and current:
            current["source_url"] = line.split("source_url:", 1)[1].strip()
        elif line.startswith("notes:") and current:
            current["notes"] = line.split("notes:", 1)[1].strip()
    if current:
        entries.append(current)

    return entries


def main():
    parser = argparse.ArgumentParser(description="Compile raw/ entries into wiki/")
    parser.add_argument("--delta", action="store_true", help="Only process new entries since last run")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be compiled")
    args = parser.parse_args()

    root = get_wiki_root()
    entries = parse_ingest_queue(root)

    if not entries:
        print("No pending entries in raw/_ingest.md.")
        sys.exit(0)

    print(f"Pending ingest entries: {len(entries)}\n")
    print("LLM compile instructions:")
    print("─" * 60)
    for i, entry in enumerate(entries, 1):
        path = entry.get("path", "unknown")
        url = entry.get("source_url", "")
        notes = entry.get("notes", "")
        abs_path = root / path
        exists = abs_path.exists()
        print(f"\n{i}. {path}")
        if url:
            print(f"   source: {url}")
        if notes:
            print(f"   notes:  {notes}")
        if not exists:
            print(f"   ⚠ file not found at {abs_path}")
        else:
            print(f"   → read file, extract key concepts, create/update wiki articles")
            print(f"   → update wiki/_index.md and wiki/_graph.md")
            print(f"   → move this entry to ## Processed in raw/_ingest.md")
    print("\n" + "─" * 60)


if __name__ == "__main__":
    main()
