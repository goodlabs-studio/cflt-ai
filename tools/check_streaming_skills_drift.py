#!/usr/bin/env python3
"""
tools/check_streaming_skills_drift.py — Drift check for streaming-skills-plugin pin.

Compares the pinned commit in tools/vendor-sources.json against the upstream
HEAD via `git ls-remote https://github.com/confluentinc/agent-skills HEAD`.

Used by .github/workflows/streaming-skills-drift.yml as the CI gate. Mirrors
the G.2c pattern (tools/regenerate_tool_classification.py): same CLI shape,
same exit-code semantics, same defensive structure.

Exit codes:
  0 = no drift (pinned commit matches upstream HEAD)
  1 = drift detected (commit mismatch) — CI fails
  2 = config error (vendor-sources.json missing entry, malformed, or wrong shape)
  3 = transient error (git unavailable, network failure, ls-remote returned empty)
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VENDOR_SOURCES_PATH = REPO_ROOT / "tools" / "vendor-sources.json"
PLUGIN_KEY = "streaming-skills-plugin"
UPSTREAM_URL = "https://github.com/confluentinc/agent-skills"


def load_pin() -> dict:
    """Load the streaming-skills-plugin entry from vendor-sources.json.

    Raises SystemExit(2) if the file or entry is missing/malformed.
    """
    if not VENDOR_SOURCES_PATH.exists():
        print(f"ERROR: {VENDOR_SOURCES_PATH} not found", file=sys.stderr)
        sys.exit(2)
    try:
        data = json.loads(VENDOR_SOURCES_PATH.read_text())
    except json.JSONDecodeError as e:
        print(f"ERROR: {VENDOR_SOURCES_PATH} is not valid JSON: {e}", file=sys.stderr)
        sys.exit(2)
    if PLUGIN_KEY not in data:
        print(f"ERROR: {VENDOR_SOURCES_PATH} missing required entry {PLUGIN_KEY!r}", file=sys.stderr)
        sys.exit(2)
    entry = data[PLUGIN_KEY]
    if "commit" not in entry or not entry["commit"]:
        print(f"ERROR: {PLUGIN_KEY} entry missing 'commit' field", file=sys.stderr)
        sys.exit(2)
    return entry


def fetch_upstream_head(upstream_url: str = UPSTREAM_URL) -> str:
    """Fetch the upstream HEAD commit SHA via `git ls-remote`.

    Raises SystemExit(3) if git is unavailable, the call fails, or the output
    is empty/malformed.
    """
    try:
        result = subprocess.run(
            ["git", "ls-remote", upstream_url, "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except FileNotFoundError:
        print("ERROR: git not found on PATH — cannot check upstream HEAD", file=sys.stderr)
        sys.exit(3)
    except subprocess.TimeoutExpired:
        print(f"ERROR: git ls-remote {upstream_url} timed out", file=sys.stderr)
        sys.exit(3)

    if result.returncode != 0:
        print(f"ERROR: git ls-remote failed (exit {result.returncode}):", file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        sys.exit(3)

    stdout = result.stdout.strip()
    if not stdout:
        print(f"ERROR: git ls-remote {upstream_url} returned empty output", file=sys.stderr)
        sys.exit(3)

    # ls-remote output format: "<sha>\tHEAD"
    first_line = stdout.splitlines()[0]
    parts = first_line.split()
    if not parts or len(parts[0]) < 40:
        print(f"ERROR: git ls-remote output malformed: {first_line!r}", file=sys.stderr)
        sys.exit(3)

    return parts[0]


def report_drift(pinned: str, live: str, entry: dict) -> None:
    """Print a structured drift report to stderr."""
    print("STREAMING_SKILLS_PLUGIN drift detected:", file=sys.stderr)
    print(f"  pinned commit: {pinned}", file=sys.stderr)
    print(f"  live HEAD:     {live}", file=sys.stderr)
    print(f"  upstream:      {entry.get('upstream', UPSTREAM_URL)}", file=sys.stderr)
    print(
        f"To fix: bump tools/vendor-sources.json {PLUGIN_KEY}.commit to {live!r}, "
        f"then re-run `/plugin install streaming-skills-plugin@confluent-agent-skills` "
        f"locally and commit any resulting changes.",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Drift check for streaming-skills-plugin pin in tools/vendor-sources.json.",
        epilog="Exit codes: 0 no drift, 1 drift detected, 2 config error, 3 transient error.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="CI mode — exit non-zero on drift, missing entry, or transient error",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the comparison summary without changing any files (default)",
    )
    args = parser.parse_args(argv)

    entry = load_pin()
    pinned = entry["commit"]
    live = fetch_upstream_head(entry.get("upstream", UPSTREAM_URL))

    drift = pinned != live

    if drift:
        if args.check:
            report_drift(pinned, live, entry)
            return 1
        print(f"DRIFT: pinned={pinned} live={live}", file=sys.stdout)
    else:
        print(f"OK: pinned={pinned} matches live HEAD", file=sys.stdout)

    return 0


if __name__ == "__main__":
    sys.exit(main())
