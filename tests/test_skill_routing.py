"""Unit tests for tools/skill_routing.py.

Covers:
- Claim → skill routing across all four skills
- Priority order resolution when keywords overlap
- activate_skill() loads SKILL.md path + extracts FSI overlay block
- _parse_override_table() extracts 5-column rows
- consult_skill() returns the structured advisory payload
- Negative space: unknown skill, empty input
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Import via the tools package — same pattern as test_check_manifest.py
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.skill_routing import (  # noqa: E402
    VERDICTS,
    _parse_override_table,
    activate_skill,
    consult_skill,
    route_claim,
)


class TestRouteClaim:
    """route_claim() maps free-form claim text to a skill slug or None."""

    def test_kstream_keyword_routes_to_streams_skill(self):
        assert route_claim("KStream join window") == "kafka-streams-programming"

    def test_topology_keyword_routes_to_streams_skill(self):
        assert (
            route_claim("Increasing topology threads cured the rebalancing loop")
            == "kafka-streams-programming"
        )

    def test_python_avroproducer_routes_to_python_client(self):
        """Priority rule: Python context wins over Schema Registry overlap."""
        assert (
            route_claim("AvroProducer with Schema Registry handles serialization")
            == "developing-kafka-python-client"
        )

    def test_full_transitive_routes_to_schema_registry(self):
        assert (
            route_claim("Use FULL_TRANSITIVE compatibility for shared consumers")
            == "kafka-schema-registry"
        )

    def test_subject_naming_routes_to_schema_registry(self):
        assert (
            route_claim("RecordNameStrategy for event union pattern")
            == "kafka-schema-registry"
        )

    def test_debezium_routes_to_cdc_tableflow(self):
        assert (
            route_claim("Debezium source connector to Iceberg via Tableflow")
            == "confluent-cloud-cdc-tableflow"
        )

    def test_schemaless_topic_routes_to_cdc_tableflow(self):
        assert (
            route_claim("Handle a schemaless topic in the CDC pipeline")
            == "confluent-cloud-cdc-tableflow"
        )

    def test_no_keyword_match_returns_none(self):
        assert route_claim("Auditor RBAC payload isolation") is None

    def test_empty_claim_returns_none(self):
        assert route_claim("") is None

    def test_case_insensitive_match(self):
        assert route_claim("kstream + ktable join") == "kafka-streams-programming"


class TestPriorityOrder:
    """When keywords from multiple skills appear, priority order picks the winner."""

    def test_python_overrides_schema_registry(self):
        """Python context (AvroProducer) wins over plain SR keywords (subject)."""
        assert (
            route_claim("AvroProducer publishes a new subject to Schema Registry")
            == "developing-kafka-python-client"
        )

    def test_cdc_overrides_schema_registry(self):
        """CDC context (Debezium) wins over SR (FULL_TRANSITIVE)."""
        assert (
            route_claim("Debezium pipeline uses FULL_TRANSITIVE compatibility")
            == "confluent-cloud-cdc-tableflow"
        )

    def test_streams_does_not_overpower_python(self):
        """Python client wins even when topology word appears."""
        # 'topology' is a streams keyword; AvroProducer is python-client.
        # Per priority order, developing-kafka-python-client wins.
        assert (
            route_claim("AvroProducer feeds the Kafka Streams topology")
            == "developing-kafka-python-client"
        )


class TestActivateSkill:
    """activate_skill() loads SKILL.md + FSI overlay block for each of the 4 skills."""

    @pytest.mark.parametrize("slug", [
        "kafka-streams-programming",
        "developing-kafka-python-client",
        "kafka-schema-registry",
        "confluent-cloud-cdc-tableflow",
    ])
    def test_all_four_skills_activate_cleanly(self, slug):
        payload = activate_skill(slug)
        assert payload["skill_slug"] == slug
        assert payload["skill_md_exists"] is True, (
            f"SKILL.md missing for {slug}: {payload['skill_md_path']}"
        )
        assert payload["references_dir_exists"] is True, (
            f"references/ missing for {slug}: {payload['references_dir']}"
        )

    @pytest.mark.parametrize("slug", [
        "kafka-streams-programming",
        "developing-kafka-python-client",
        "kafka-schema-registry",
        "confluent-cloud-cdc-tableflow",
    ])
    def test_fsi_overlay_block_extracted_for_each_skill(self, slug):
        payload = activate_skill(slug)
        block = payload["fsi_overlay_block"]
        assert block, f"empty overlay block for {slug}"
        assert block.startswith(f"## {slug}"), (
            f"overlay block does not start with skill heading for {slug}; "
            f"got: {block[:80]!r}"
        )

    def test_fsi_overlay_block_does_not_leak_next_section(self):
        """Block extraction should stop at the next ## heading."""
        payload = activate_skill("kafka-streams-programming")
        block = payload["fsi_overlay_block"]
        # The overlay file has python-client, schema-registry, etc. after streams.
        # Block must not contain those headings.
        assert "## developing-kafka-python-client" not in block
        assert "## kafka-schema-registry" not in block

    def test_applied_overrides_parsed_from_table(self):
        """The 5-column markdown table inside the overlay block is parsed."""
        payload = activate_skill("kafka-streams-programming")
        rows = payload["applied_overrides"]
        assert isinstance(rows, list)
        assert len(rows) >= 1, "overlay table should have at least one row"
        # Each row has the 5 expected fields
        for row in rows:
            assert set(row.keys()) == {
                "key", "upstream_default", "fsi_override", "rationale", "canon_source"
            }

    def test_unknown_skill_slug_raises(self):
        with pytest.raises(ValueError, match="Unknown skill slug"):
            activate_skill("not-a-real-skill")


class TestConsultSkill:
    """consult_skill() returns the structured advisory payload."""

    def test_consult_returns_required_fields(self):
        payload = consult_skill(
            "kafka-streams-programming",
            "KStream tumbling-window aggregation drops late events",
        )
        # Caller (the skill spec) fills in verdict + evidence — they start as None
        assert payload["skill_slug"] == "kafka-streams-programming"
        assert payload["claim"] == "KStream tumbling-window aggregation drops late events"
        assert payload["verdict"] is None  # caller sets this
        assert payload["evidence"] is None  # caller sets this
        assert payload["source"] == "skill"
        assert payload["fsi_overlay_block"]  # populated from activation
        assert isinstance(payload["applied_overrides"], list)

    def test_verdicts_enum_well_known(self):
        """The fixed verdict vocabulary used by skill specs."""
        assert set(VERDICTS) == {"Confirmed", "Corrected", "Unverifiable", "Out-of-scope"}


class TestParseOverrideTable:
    """The 5-column table parser handles well-formed and edge-case input."""

    def test_parses_well_formed_table(self):
        block = (
            "## kafka-streams-programming\n"
            "\n"
            "| Override Key | Upstream Default | FSI Override | Rationale | Canon Source |\n"
            "|---|---|---|---|---|\n"
            "| processing.guarantee | at_least_once | exactly_once_v2 | SOX 302 | CLAUDE.md §Producers |\n"
            "| default.value.serde | JSON | Avro/Protobuf | governance | CLAUDE.md §SR |\n"
        )
        rows = _parse_override_table(block)
        assert len(rows) == 2
        assert rows[0]["key"] == "processing.guarantee"
        assert rows[0]["fsi_override"] == "exactly_once_v2"
        assert rows[1]["key"] == "default.value.serde"

    def test_empty_block_returns_empty_list(self):
        assert _parse_override_table("") == []

    def test_block_without_table_returns_empty_list(self):
        block = "## kafka-streams-programming\n\nSome prose with no table.\n"
        assert _parse_override_table(block) == []


class TestRoutingDataIntegrity:
    """The skill-routing.json data file is well-formed and aligned with vendored skills."""

    def test_routing_json_loads(self):
        data = json.loads(
            (Path(__file__).resolve().parent.parent / "tools" / "skill-routing.json").read_text()
        )
        assert "skills" in data
        assert "_priority_order" in data

    def test_priority_order_covers_all_skills(self):
        data = json.loads(
            (Path(__file__).resolve().parent.parent / "tools" / "skill-routing.json").read_text()
        )
        assert set(data["_priority_order"]) == set(data["skills"].keys())

    def test_skill_md_paths_resolve(self):
        """Every skill's skill_md path exists on disk (vendored at pin SHA)."""
        data = json.loads(
            (Path(__file__).resolve().parent.parent / "tools" / "skill-routing.json").read_text()
        )
        project_root = Path(__file__).resolve().parent.parent
        for slug, cfg in data["skills"].items():
            path = project_root / cfg["skill_md"]
            assert path.exists(), f"SKILL.md missing for {slug}: {path}"
