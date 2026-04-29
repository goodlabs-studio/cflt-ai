#!/usr/bin/env python3
"""
Apply engine for /dsp:apply act rail. Enforces least-privilege policy profiles,
emits provenance activity log entries, and creates wiki incident articles.

Requirements: ACTA-01 (apply gate chain), ACTA-02 (bypass prevention),
              ACTA-03 (profile enforcement), ACTA-04 (activity log),
              ACTA-05 (incident articles)
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import sys

# Add project root to path for canon.stack import (matches act_gates.py pattern)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from canon.stack import active_layers  # noqa: E402 (after sys.path.insert)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROFILES_DIR = PROJECT_ROOT / "tools" / "profiles"

# Explicit set of valid profile names — fail-closed: unrecognized names raise ValueError
VALID_PROFILES = {"read-only", "engineer", "break-glass"}


# ---------------------------------------------------------------------------
# Profile Loading (ACTA-03)
# ---------------------------------------------------------------------------

def load_profile(profile_name: str) -> Dict:
    """Load a policy profile by name from PROFILES_DIR.

    Profile names must be one of the VALID_PROFILES set. Unknown names raise
    ValueError immediately (fail-closed — never silently degrades to permissive mode).

    Args:
        profile_name: Name of the profile to load (e.g., "engineer").

    Returns:
        Dict with keys: name (str), description (str), allowed_operations (list).

    Raises:
        ValueError: If profile_name is not in VALID_PROFILES or is empty.
    """
    if not profile_name:
        raise ValueError(f"Unknown profile: {profile_name!r} — must be one of {VALID_PROFILES}")

    if profile_name not in VALID_PROFILES:
        raise ValueError(
            f"Unknown profile: {profile_name!r} — must be one of {sorted(VALID_PROFILES)}"
        )

    profile_path = PROFILES_DIR / f"{profile_name}.json"
    profile_data = json.loads(profile_path.read_text())
    return profile_data


# ---------------------------------------------------------------------------
# Profile Enforcement (ACTA-03)
# ---------------------------------------------------------------------------

def check_profile_permits(profile: Dict, artifact_id: str) -> bool:
    """Check whether a policy profile permits a given artifact operation.

    Wildcard "*" in allowed_operations permits all artifact IDs.
    Empty allowed_operations list denies all operations (read-only semantics).
    Exact string match required for non-wildcard entries.

    Args:
        profile:     Profile dict as returned by load_profile().
        artifact_id: The fsi-dsp artifact ID to check (e.g., "module/topic").

    Returns:
        True if the operation is permitted; False otherwise.
    """
    allowed: List[str] = profile.get("allowed_operations", [])

    if "*" in allowed:
        return True

    return artifact_id in allowed


# ---------------------------------------------------------------------------
# Activity Log (ACTA-04)
# ---------------------------------------------------------------------------

def emit_activity_log_apply(
    overlay: str,
    plan_path: str,
    artifact_id: str,
    profile_name: str,
    confirmation_status: str,
    execution_result: str,
    duration_seconds: float,
    gate_results: List[Dict],
    operator: str,
) -> None:
    """Append a /dsp:apply entry to the overlay-scoped activity log.

    Writes to wiki/activity/YYYY-MM.md relative to PROJECT_ROOT. Creates the
    file with a header if it does not exist. Appends to the existing file if it
    does exist. Activity log is append-only — never modifies existing entries.

    Args:
        overlay:             Customer overlay name (e.g., "base", "acme-bank").
        plan_path:           Path to the plan file that was applied.
        artifact_id:         fsi-dsp artifact ID that was applied.
        profile_name:        Policy profile name used for this apply.
        confirmation_status: Human confirmation outcome ("confirmed" or "rejected").
        execution_result:    Execution outcome ("success", "failure", "dry-run").
        duration_seconds:    Wall-clock seconds from confirmation to execution complete.
        gate_results:        List of gate result dicts from run_gate_chain().
        operator:            Operator identifier (user/service account name).
    """
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    month_key = now.strftime("%Y-%m")

    # Build gate summary for log entry (compact form)
    gate_summary = ", ".join(
        f"{r['gate']}={r['status']}" for r in gate_results
    ) if gate_results else "no gates recorded"

    # Build canon stack reference
    try:
        layers = active_layers()
        canon_stack = " + ".join(layers) if layers else "base"
    except Exception:
        canon_stack = overlay or "base"

    # Compose the activity log entry
    entry_lines = [
        f"## {timestamp}",
        f"**Skill:** /dsp:apply",
        f"**Operator:** {operator}",
        f"**Overlay:** {overlay}",
        f"**Profile:** {profile_name}",
        f"**Artifact:** {artifact_id}",
        f"**Plan:** {plan_path}",
        f"**Confirmation status:** {confirmation_status}",
        f"**Execution result:** {execution_result}",
        f"**Duration seconds:** {duration_seconds:.1f}",
        f"**Gates:** {gate_summary}",
        f"**Canon stack:** {canon_stack}",
        "",
    ]
    entry = "\n".join(entry_lines)

    # Resolve log file path
    activity_dir = PROJECT_ROOT / "wiki" / "activity"
    activity_dir.mkdir(parents=True, exist_ok=True)
    log_file = activity_dir / f"{month_key}.md"

    if not log_file.exists():
        # Create with header
        header = f"# Activity Log — {month_key}\n\n"
        log_file.write_text(header + entry)
    else:
        # Append to existing file
        existing = log_file.read_text()
        # Ensure there's a blank line separator before appending
        separator = "\n" if existing.endswith("\n") else "\n\n"
        log_file.write_text(existing + separator + entry)


# ---------------------------------------------------------------------------
# Incident Article (ACTA-05)
# ---------------------------------------------------------------------------

def write_incident_article(
    slug: str,
    artifact_id: str,
    operator: str,
    profile_name: str,
    outcome: str,
    canon_hash: str,
    plan_path: str,
    gate_results: List[Dict],
    execution_result: str,
) -> Path:
    """Write a wiki incident article for a /dsp:apply execution.

    Creates wiki/incidents/<slug>-<YYYY-MM-DD>.md relative to PROJECT_ROOT.
    Creates the incidents directory if it does not exist.

    Each apply operation creates one incident article as a trackable audit record
    (ACTA-05). The article contains YAML frontmatter and four required sections.

    Args:
        slug:             URL-safe slug for the incident (e.g., "trade-topic-create").
        artifact_id:      fsi-dsp artifact ID that was applied.
        operator:         Operator identifier.
        profile_name:     Policy profile used.
        outcome:          High-level outcome ("success", "failure", "rejected").
        canon_hash:       16-char SHA-256 hash of the active canon stack.
        plan_path:        Path to the source plan file.
        gate_results:     List of gate result dicts from run_gate_chain().
        execution_result: Detailed execution result string.

    Returns:
        Path to the created incident article.
    """
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    # Build file name: <slug>-<YYYY-MM-DD>.md
    filename = f"{slug}-{date_str}.md"
    incidents_dir = PROJECT_ROOT / "wiki" / "incidents"
    incidents_dir.mkdir(parents=True, exist_ok=True)
    article_path = incidents_dir / filename

    # Build YAML frontmatter (7 required keys)
    frontmatter_lines = [
        "---",
        f"artifact: {artifact_id}",
        f"operator: {operator}",
        f"profile: {profile_name}",
        f"outcome: {outcome}",
        f"canon_hash: {canon_hash}",
        f"plan_ref: {plan_path}",
        f"timestamp: {timestamp}",
        "---",
        "",
    ]

    # Build gate results markdown table
    if gate_results:
        table_header = "| Gate | Status | Detail |"
        table_sep = "| --- | --- | --- |"
        table_rows = [
            f"| {r.get('gate', '')} | {r.get('status', '')} | {r.get('detail', '')} |"
            for r in gate_results
        ]
        gate_table = "\n".join([table_header, table_sep] + table_rows)
    else:
        gate_table = "| Gate | Status | Detail |\n| --- | --- | --- |\n| (no gates recorded) | - | - |"

    # Build canon provenance
    try:
        layers = active_layers()
        canon_stack = " + ".join(layers) if layers else "base"
    except Exception:
        canon_stack = "base"

    # Compose article body
    body_sections = [
        f"# Incident: {slug}",
        "",
        "## What Changed",
        "",
        f"Applied `{artifact_id}` via profile `{profile_name}`.",
        f"Execution result: `{execution_result}`.",
        "",
        "## Why",
        "",
        f"See plan: `{plan_path}`",
        "",
        "## Gate Results",
        "",
        gate_table,
        "",
        "## Provenance",
        "",
        f"Canon stack: {canon_stack}",
        f"Canon hash: `{canon_hash}`",
        f"Operator: {operator}",
        f"Timestamp: {timestamp}",
        "",
    ]

    article_content = "\n".join(frontmatter_lines + body_sections)
    article_path.write_text(article_content)
    return article_path


# ---------------------------------------------------------------------------
# CLI entry point (matches tools/ convention)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Apply engine for /dsp:apply: load profiles and check permissions."
    )
    subparsers = parser.add_subparsers(dest="command")

    # check-profile subcommand
    check_parser = subparsers.add_parser("check-profile", help="Check if profile permits an operation")
    check_parser.add_argument("profile", help="Profile name (read-only, engineer, break-glass)")
    check_parser.add_argument("artifact_id", help="Artifact ID to check (e.g., module/topic)")

    # show-profile subcommand
    show_parser = subparsers.add_parser("show-profile", help="Show profile details")
    show_parser.add_argument("profile", help="Profile name")

    args = parser.parse_args()

    if args.command == "check-profile":
        try:
            profile = load_profile(args.profile)
            permitted = check_profile_permits(profile, args.artifact_id)
            status = "PERMITTED" if permitted else "DENIED"
            print(f"[{status}] {args.profile} -> {args.artifact_id}")
        except ValueError as exc:
            print(f"[ERROR] {exc}")
            sys.exit(1)
    elif args.command == "show-profile":
        try:
            profile = load_profile(args.profile)
            print(json.dumps(profile, indent=2))
        except ValueError as exc:
            print(f"[ERROR] {exc}")
            sys.exit(1)
    else:
        parser.print_help()
