#!/usr/bin/env python3
"""
Regenerate tools/profiles/tool_classification.json from the pinned
@confluentinc/mcp-confluent package's dist/confluent/tools/tool-name.js.

Modes:
  (default)     Regenerate the JSON file from the live registry.
  --check       Compare committed JSON against live registry; exit 1 on drift.
  --dry-run     Use the static fixture under tests/fixtures/ instead of npm-installing.
  --version X   Override the pinned mcp-confluent version (otherwise read from JSON).

Requirements: ACTG-01 (every mcp-confluent tool classified by exact name).

Decision references:
  - D-01: canonical source is dist/confluent/tools/tool-name.js from a pinned package.
  - D-02: pin lives inside tool_classification.json (`mcp_confluent_version`).
  - D-05: verb-prefix rule + two explicit overrides (produce-message, consume-messages).
  - D-06: rule is a regeneration aid — unknown shapes raise so CI blocks bump PRs.
  - D-08: bidirectional drift (missing-from-committed AND extra-in-committed both fail).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = PROJECT_ROOT / "tools" / "profiles" / "tool_classification.json"
FIXTURE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "mcp_confluent_tool_name_sample.js"

# D-05 verb-prefix rule. Order doesn't matter for correctness (prefixes are
# disjoint across tiers) but the grouping makes reviewer intent obvious.
READ_ONLY_PREFIXES = (
    "list-",
    "read-",
    "get-",
    "search-",
    "detect-",
    "check-",
    "describe-",
    "query-",
)
ENGINEER_PREFIXES = (
    "create-",
    "update-",
    "alter-",
    "add-",
)
BREAK_GLASS_PREFIXES = (
    "delete-",
    "remove-",
)

# Explicit tier overrides for tools whose verb does not match any prefix
# OR whose verb-prefix tier would be wrong for FSI canon (data-plane safety).
# See G.2c-CONTEXT.md D-05 "Exceptions".
OVERRIDES: Dict[str, str] = {
    "produce-message": "break-glass",   # data-plane write; production guard
    "consume-messages": "break-glass",  # data-plane read; FSI PII consideration
    # `explain-disabled-tools` is an introspection tool surfaced in
    # mcp-confluent 1.3.0 that returns metadata about which tools are
    # currently disabled by the server's config. No state mutation, no
    # data-plane exposure — semantically equivalent to a describe-/get- read.
    # No verb-prefix match, so it requires an explicit override.
    "explain-disabled-tools": "read-only",
}

# Stored in the JSON's `tier_rule` field so the rule is visible to anyone
# opening the file. JSON has no comments — this is the documented stand-in
# for D-05's "comment block at the top".
TIER_RULE_DOC = (
    "Verb-prefix rule: "
    "list-/read-/get-/search-/detect-/check-/describe-/query- -> read-only; "
    "create-/update-/alter-/add- -> engineer; "
    "delete-/remove- -> break-glass. "
    "Overrides: produce-message -> break-glass; consume-messages -> break-glass. "
    "Regenerate via `python tools/regenerate_tool_classification.py`."
)

# Matches both `ToolName["NAME"] = "kebab-name"` and the single-quoted form
# tsc occasionally emits. Tolerates whitespace inside the brackets and around
# the `=`. Tool names are kebab-case ASCII (letter, then letters/digits/`-`).
TOOL_NAME_RE = re.compile(
    r"""ToolName\s*\[\s*["']([A-Z][A-Z0-9_]*)["']\s*\]\s*=\s*["']([a-z][a-z0-9\-]*)["']"""
)


def parse_tool_name_js(content: str) -> Set[str]:
    """Extract every kebab-case tool name from a tool-name.js file."""
    return {m.group(2) for m in TOOL_NAME_RE.finditer(content)}


def classify_tier(tool_name: str) -> str:
    """Apply the D-05 verb-prefix rule with explicit overrides.

    Raises ValueError when no prefix matches and no override exists, so a future
    mcp-confluent release introducing a new verb shape fails loudly in CI
    rather than landing as an unclassified tool (D-06: regeneration aid, not
    runtime fallback).
    """
    if tool_name in OVERRIDES:
        return OVERRIDES[tool_name]
    for prefix in READ_ONLY_PREFIXES:
        if tool_name.startswith(prefix):
            return "read-only"
    for prefix in ENGINEER_PREFIXES:
        if tool_name.startswith(prefix):
            return "engineer"
    for prefix in BREAK_GLASS_PREFIXES:
        if tool_name.startswith(prefix):
            return "break-glass"
    raise ValueError(
        f"Cannot classify tool {tool_name!r}: no known verb prefix and no entry "
        f"in OVERRIDES. Add an explicit override in "
        f"tools/regenerate_tool_classification.py OVERRIDES dict, or extend "
        f"the verb-prefix tables if this represents a new tier shape."
    )


def build_classification(tool_names: Set[str], mcp_confluent_version: str) -> Dict:
    """Build the full JSON-ready classification dict.

    Tools are emitted flat alphabetical — keeps the next bump PR's diff small
    and reviewable (D-05 Claude's Discretion).
    """
    tools = {name: classify_tier(name) for name in sorted(tool_names)}
    return {
        "version": "1",
        "description": (
            "mcp-confluent tool-to-tier mapping. "
            "Tier hierarchy: read-only < engineer < break-glass. "
            "Unclassified tools denied by all profiles."
        ),
        "mcp_confluent_version": mcp_confluent_version,
        "tier_rule": TIER_RULE_DOC,
        "tools": tools,
        "unclassified_policy": "deny",
    }


def diff_classification(
    committed: Dict, expected: Dict
) -> Tuple[List[str], List[str]]:
    """Bidirectional drift (D-08).

    Returns (missing_from_committed, extra_in_committed). Both lists empty
    means the committed JSON matches the live registry exactly.
    """
    committed_tools = set(committed.get("tools", {}).keys())
    expected_tools = set(expected.get("tools", {}).keys())
    missing_from_committed = sorted(expected_tools - committed_tools)
    extra_in_committed = sorted(committed_tools - expected_tools)
    return missing_from_committed, extra_in_committed


# ---------------------------------------------------------------------------
# npm-install + parse the live registry
# ---------------------------------------------------------------------------


def _install_and_read(version: str) -> str:
    """npm-install the pinned mcp-confluent into a temp prefix; return JS file content.

    We use --prefix into a TemporaryDirectory so we never depend on the
    per-machine `~/.npm/_npx/<hash>/` cache. Anyone with npm on PATH can
    reproduce the output bit-for-bit.
    """
    with tempfile.TemporaryDirectory(prefix="mcp-confluent-regen-") as tmp:
        tmp_path = Path(tmp)
        try:
            subprocess.run(
                [
                    "npm",
                    "install",
                    "--prefix",
                    str(tmp_path),
                    "--no-save",
                    "--silent",
                    "--no-fund",
                    "--no-audit",
                    # --ignore-scripts skips the native-build postinstall of the
                    # transitive @confluentinc/kafka-javascript dep, which would
                    # otherwise require Xcode CLT (macOS) or build-essential
                    # (Linux). We only consume dist/confluent/tools/tool-name.js,
                    # which is pre-built JS shipped in the package and doesn't
                    # depend on the native binary. Keeps this generator portable
                    # to clean CI runners without C toolchains.
                    "--ignore-scripts",
                    f"@confluentinc/mcp-confluent@{version}",
                ],
                check=True,
            )
        except FileNotFoundError as exc:
            raise SystemExit(
                "npm not found on PATH. Install Node.js (>= 18) or run with "
                "--dry-run to exercise the parser against the static fixture."
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise SystemExit(
                f"npm install of @confluentinc/mcp-confluent@{version} failed "
                f"with exit code {exc.returncode}. Check the version pin and network."
            ) from exc

        js_path = (
            tmp_path
            / "node_modules"
            / "@confluentinc"
            / "mcp-confluent"
            / "dist"
            / "confluent"
            / "tools"
            / "tool-name.js"
        )
        if not js_path.exists():
            raise SystemExit(
                f"tool-name.js not found after npm install at {js_path}. "
                "Package layout may have changed; inspect node_modules manually."
            )
        return js_path.read_text()


def _resolve_version(args_version: Optional[str]) -> str:
    """Pin source order: --version flag > committed JSON > error."""
    if args_version:
        return args_version
    if JSON_PATH.exists():
        data = json.loads(JSON_PATH.read_text())
        version = data.get("mcp_confluent_version")
        if version:
            return version
    raise SystemExit(
        "No --version provided and tool_classification.json has no "
        "mcp_confluent_version field. Pass --version on first run "
        "(e.g., --version 1.3.0)."
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate or drift-check tool_classification.json from a pinned "
            "@confluentinc/mcp-confluent package."
        ),
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare committed JSON against live registry; exit 1 on drift.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Use the static fixture under tests/fixtures/ instead of "
            "npm-installing. Prints JSON to stdout; never writes to disk."
        ),
    )
    parser.add_argument(
        "--version",
        help=(
            "Override the pinned mcp-confluent version. Required when "
            "tool_classification.json is absent or lacks mcp_confluent_version."
        ),
    )
    args = parser.parse_args()

    if args.dry_run:
        content = FIXTURE_PATH.read_text()
        version = args.version or "fixture"
    else:
        version = _resolve_version(args.version)
        content = _install_and_read(version)

    tool_names = parse_tool_name_js(content)
    if not tool_names:
        print(
            "ERROR: parser extracted zero tool names. Regex may need updating, "
            "or the input file does not contain a ToolName enum.",
            file=sys.stderr,
        )
        return 1

    expected = build_classification(tool_names, version)

    if args.dry_run:
        print(json.dumps(expected, indent=2))
        return 0

    if args.check:
        if not JSON_PATH.exists():
            print(
                f"ERROR: {JSON_PATH} does not exist; cannot --check.",
                file=sys.stderr,
            )
            return 1
        committed = json.loads(JSON_PATH.read_text())
        missing, extra = diff_classification(committed, expected)
        if missing or extra:
            print(
                "DRIFT detected between committed tool_classification.json and "
                "live mcp-confluent registry:",
                file=sys.stderr,
            )
            if missing:
                print(
                    f"  Missing from committed (add with tier): {missing}",
                    file=sys.stderr,
                )
            if extra:
                print(
                    f"  Extra in committed (remove or pin older mcp-confluent): {extra}",
                    file=sys.stderr,
                )
            print(
                "  Regenerate via: python tools/regenerate_tool_classification.py",
                file=sys.stderr,
            )
            return 1
        print(
            f"OK: tool_classification.json matches mcp-confluent {version} "
            f"({len(expected['tools'])} tools).",
            file=sys.stderr,
        )
        return 0

    # Default mode: write the file.
    JSON_PATH.write_text(json.dumps(expected, indent=2) + "\n")
    print(
        f"Wrote {JSON_PATH} with {len(expected['tools'])} classified tools "
        f"(mcp-confluent {version}).",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
