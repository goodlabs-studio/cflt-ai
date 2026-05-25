"""Skill routing for /review and /wiki:validate.

Maps claim text to one of the four streaming-skills-plugin skills, activates
the corresponding skill (loads SKILL.md + extracts the matching FSI overlay
block), and produces a structured advisory verdict.

The four skills (per `tools/vendor-sources.json` pin `91d1871e`):
- kafka-streams-programming
- developing-kafka-python-client
- kafka-schema-registry
- confluent-cloud-cdc-tableflow

Advisory pattern (per Phase 13 design): skills are consulted alongside MCP
during claim validation. MCP (confluent-docs / context7) remains authoritative
when verdicts conflict; skill output is annotated for follow-up review.

Mirrors the shape of `tools/check_manifest.py` and `tools/check_submodule_drift.py`:
pure stdlib Python 3.12, no external dependencies, exit codes 0/1/2/3 from CLI.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ROUTING_DATA = PROJECT_ROOT / "tools" / "skill-routing.json"
FSI_OVERLAY_PATH = PROJECT_ROOT / "wiki" / "patterns" / "fsi-canon-overlay-for-confluent-skills.md"


VERDICTS = ("Confirmed", "Corrected", "Unverifiable", "Out-of-scope")


def _load_routing() -> dict:
    return json.loads(ROUTING_DATA.read_text())


def route_claim(claim_text: str, *, routing: Optional[dict] = None) -> Optional[str]:
    """Return the skill slug whose keywords best match the claim text, or None.

    Priority order (from `_priority_order` in skill-routing.json): the FIRST
    skill in priority order that has a keyword hit wins. This resolves overlaps
    — e.g., "AvroProducer for Schema Registry" hits both Python-client and
    schema-registry keywords; Python-client wins because Python context is more
    specific than the cross-cutting SR vocabulary.
    """
    if not claim_text:
        return None
    if routing is None:
        routing = _load_routing()
    lower = claim_text.lower()
    for slug in routing["_priority_order"]:
        keywords = routing["skills"][slug]["keywords"]
        for kw in keywords:
            if kw.lower() in lower:
                return slug
    return None


def _extract_overlay_block(skill_slug: str, *, overlay_text: Optional[str] = None,
                           routing: Optional[dict] = None) -> str:
    """Extract the `## <skill-slug>` section from the FSI overlay article.

    Returns the section body (everything from the heading to the next ## heading
    or end of file). Empty string if the section is missing.
    """
    if routing is None:
        routing = _load_routing()
    if overlay_text is None:
        overlay_text = FSI_OVERLAY_PATH.read_text()
    section_heading = routing["skills"][skill_slug]["fsi_overlay_section"]
    # Match the heading line through the next ## heading or EOF
    pattern = re.compile(
        r"^" + re.escape(section_heading) + r"\s*\n(.*?)(?=^## |\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(overlay_text)
    if not match:
        return ""
    return (section_heading + "\n" + match.group(1)).strip()


def activate_skill(skill_slug: str, *, routing: Optional[dict] = None) -> dict:
    """Load the skill's SKILL.md, references dir, and FSI overlay block.

    Returns a dict with paths + extracted overlay content. Used by /review
    Step 4.0.5 and /wiki:validate Step 2c to seed the skill consultation step.
    """
    if routing is None:
        routing = _load_routing()
    if skill_slug not in routing["skills"]:
        raise ValueError(
            f"Unknown skill slug: {skill_slug!r}. "
            f"Valid slugs: {sorted(routing['skills'].keys())}"
        )
    skill_cfg = routing["skills"][skill_slug]
    skill_md_path = PROJECT_ROOT / skill_cfg["skill_md"]
    references_dir = PROJECT_ROOT / skill_cfg["references_dir"]
    overlay_block = _extract_overlay_block(skill_slug, routing=routing)
    return {
        "skill_slug": skill_slug,
        "skill_md_path": str(skill_md_path),
        "references_dir": str(references_dir),
        "skill_md_exists": skill_md_path.exists(),
        "references_dir_exists": references_dir.exists(),
        "fsi_overlay_section": skill_cfg["fsi_overlay_section"],
        "fsi_overlay_block": overlay_block,
        "applied_overrides": _parse_override_table(overlay_block),
    }


def _parse_override_table(overlay_block: str) -> list[dict]:
    """Parse the 5-column markdown table inside an FSI overlay section.

    Returns a list of `{key, upstream_default, fsi_override, rationale, canon_source}`.
    Empty list if no table is found. Best-effort — overlay file is human-authored
    so we don't fail on minor formatting deviations.
    """
    rows = []
    in_table = False
    for line in overlay_block.splitlines():
        if line.strip().startswith("| Override Key"):
            in_table = True
            continue
        if in_table and line.strip().startswith("|---"):
            continue
        if in_table and not line.strip().startswith("|"):
            in_table = False
            continue
        if in_table:
            cells = [c.strip() for c in line.split("|")[1:-1]]
            if len(cells) >= 5:
                rows.append({
                    "key": cells[0],
                    "upstream_default": cells[1],
                    "fsi_override": cells[2],
                    "rationale": cells[3],
                    "canon_source": cells[4],
                })
    return rows


def consult_skill(skill_slug: str, claim_text: str, *,
                  routing: Optional[dict] = None) -> dict:
    """Produce an advisory verdict for the claim using the activated skill.

    The verdict is intentionally lightweight — this function does not invoke an
    LLM or run the SKILL.md in any agent runtime. It returns the activation
    payload + a placeholder verdict marker that /review and /wiki:validate fill
    in based on the SKILL.md contents they've loaded into context.

    Returned shape:
        {
            "skill_slug": ...,
            "claim": ...,
            "verdict": None,           # caller (the skill spec) sets this
            "evidence": None,
            "source": "skill",
            "applied_overrides": [...] # for canon-compliance integration
        }

    Callers MUST set `verdict` before recording the consultation in the review
    table. The fixed enum is in `VERDICTS`.
    """
    if routing is None:
        routing = _load_routing()
    activation = activate_skill(skill_slug, routing=routing)
    return {
        "skill_slug": skill_slug,
        "claim": claim_text,
        "verdict": None,
        "evidence": None,
        "source": "skill",
        "skill_md_path": activation["skill_md_path"],
        "fsi_overlay_block": activation["fsi_overlay_block"],
        "applied_overrides": activation["applied_overrides"],
    }


def _cli_route(args: argparse.Namespace) -> int:
    slug = route_claim(args.text)
    if slug is None:
        print("—")
        return 0
    print(slug)
    return 0


def _cli_activate(args: argparse.Namespace) -> int:
    try:
        payload = activate_skill(args.slug)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"skill_slug:        {payload['skill_slug']}")
        print(f"skill_md_path:     {payload['skill_md_path']}")
        print(f"skill_md_exists:   {payload['skill_md_exists']}")
        print(f"references_dir:    {payload['references_dir']}")
        print(f"fsi_overlay_block: ({len(payload['fsi_overlay_block'])} chars)")
        print(f"applied_overrides: {len(payload['applied_overrides'])} rows")
        if args.verbose:
            print()
            print(payload["fsi_overlay_block"])
    return 0


def _cli_list(_args: argparse.Namespace) -> int:
    routing = _load_routing()
    for slug in routing["_priority_order"]:
        keywords = routing["skills"][slug]["keywords"]
        print(f"{slug:40s} ({len(keywords)} keywords)")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Route a claim to a streaming-skills-plugin skill."
    )
    subparsers = parser.add_subparsers(dest="cmd", required=True)

    p_route = subparsers.add_parser("route", help="Map claim text to a skill slug.")
    p_route.add_argument("text", help="Claim text to route.")
    p_route.set_defaults(func=_cli_route)

    p_act = subparsers.add_parser("activate", help="Load skill + extract FSI overlay block.")
    p_act.add_argument("slug", help="Skill slug to activate.")
    p_act.add_argument("--json", action="store_true", help="Emit JSON instead of plain text.")
    p_act.add_argument("--verbose", "-v", action="store_true", help="Print the full overlay block.")
    p_act.set_defaults(func=_cli_activate)

    p_list = subparsers.add_parser("list", help="List the four skills + keyword counts.")
    p_list.set_defaults(func=_cli_list)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
