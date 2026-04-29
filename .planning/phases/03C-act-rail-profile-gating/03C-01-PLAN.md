---
phase: 03C-act-rail-profile-gating
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - tools/profiles/tool_classification.json
  - tools/profiles/read-only.json
  - tools/profiles/engineer.json
  - tools/profiles/break-glass.json
  - canon/customer/acme-bank/profiles/engineer.json
  - canon/customer/acme-bank/adrs/adr-003.md
autonomous: true
requirements: [ACTG-01, ACTG-04]

must_haves:
  truths:
    - "Every mcp-confluent tool (50+) appears in tool_classification.json by exact name"
    - "No tool uses regex or wildcard pattern — all entries are literal tool names"
    - "break-glass.json no longer contains wildcard '*' — replaced with explicit tool list"
    - "acme-bank engineer profile removes module/flink and adds role/cp_audit relative to base"
  artifacts:
    - path: "tools/profiles/tool_classification.json"
      provides: "Tool-to-tier classification mapping for all mcp-confluent tools"
      contains: "unclassified_policy"
    - path: "tools/profiles/break-glass.json"
      provides: "Break-glass profile with explicit tool enumeration"
      contains: "allowed_operations"
    - path: "canon/customer/acme-bank/profiles/engineer.json"
      provides: "Acme-bank differential engineer profile"
      contains: "role/cp_audit"
    - path: "canon/customer/acme-bank/adrs/adr-003.md"
      provides: "ADR documenting Flink prohibition and audit role addition"
      contains: "module/flink"
  key_links:
    - from: "tools/profiles/tool_classification.json"
      to: "tools/profiles/break-glass.json"
      via: "tier hierarchy defines which tools each profile permits"
      pattern: "break-glass"
    - from: "canon/customer/acme-bank/profiles/engineer.json"
      to: "tools/profiles/engineer.json"
      via: "customer overlay overrides base profile"
      pattern: "allowed_operations"
---

<objective>
Create the tool classification table mapping all 50+ mcp-confluent tools to profile tiers by explicit name, update all three profile JSONs to use explicit tool lists (replacing the break-glass wildcard), create the acme-bank customer engineer profile overlay with differential gating, and document the override with ADR-003.

Purpose: Establishes the data layer that all subsequent enforcement logic and tests depend on. Per ACTG-01, every tool must be classified by name (not regex). Per ACTG-04, acme-bank must demonstrate differential gating.
Output: tool_classification.json, updated profile JSONs, acme-bank engineer overlay, ADR-003
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/03C-act-rail-profile-gating/03C-CONTEXT.md
@.planning/phases/03C-act-rail-profile-gating/03C-RESEARCH.md

<interfaces>
<!-- Key types and contracts the executor needs. -->

From tools/apply_engine.py:
```python
PROFILES_DIR = PROJECT_ROOT / "tools" / "profiles"
VALID_PROFILES = {"read-only", "engineer", "break-glass"}

def load_profile(profile_name: str) -> Dict:
    # Returns dict with keys: name (str), description (str), allowed_operations (list)

def check_profile_permits(profile: Dict, artifact_id: str) -> bool:
    # Checks allowed_operations: "*" permits all, empty denies all, exact match otherwise
```

From tools/profiles/engineer.json (current):
```json
{
  "name": "engineer",
  "description": "Plan + apply standard non-destructive modules (topics, schemas, RBAC, Flink).",
  "allowed_operations": ["module/topic", "module/flink", "role/cp_schema", "role/cp_rbac", "role/cp_connect"]
}
```

From tools/profiles/break-glass.json (current — wildcard to be replaced):
```json
{
  "name": "break-glass",
  "description": "All operations including destructive (DR failover, cluster reconfig, deletion).",
  "allowed_operations": ["*"]
}
```

From canon/customer/acme-bank/overrides.yaml (existing overlay pattern):
```yaml
producer:
  compression_type: "zstd"
  override_source: "customer/acme-bank/adr-001"
latency_tiers:
  market_data: "sub-100-microsecond"
  override_source: "customer/acme-bank/adr-002"
```

From canon/customer/acme-bank/adrs/adr-002.md (ADR pattern to follow):
- Status: Accepted
- Sections: Context, Decision, Consequences
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create tool_classification.json and update profile JSONs</name>
  <files>
    tools/profiles/tool_classification.json,
    tools/profiles/read-only.json,
    tools/profiles/engineer.json,
    tools/profiles/break-glass.json
  </files>
  <read_first>
    tools/profiles/read-only.json,
    tools/profiles/engineer.json,
    tools/profiles/break-glass.json,
    .planning/phases/03C-act-rail-profile-gating/03C-RESEARCH.md
  </read_first>
  <action>
    Create `tools/profiles/tool_classification.json` with the following structure per CONTEXT.md locked decisions:

    ```json
    {
      "version": "1",
      "description": "mcp-confluent tool-to-tier mapping. Tier hierarchy: read-only < engineer < break-glass. Unclassified tools denied by all profiles.",
      "tools": { ... },
      "unclassified_policy": "deny"
    }
    ```

    The `"tools"` object must map every mcp-confluent tool name to one of three tier strings: `"read-only"`, `"engineer"`, or `"break-glass"`. Tool names follow the `confluent_<resource>_<action>` convention. MUST contain >= 50 entries per ACTG-01.

    Tier assignment logic (Claude's Discretion on exact names):
    - `"read-only"` tier: list/describe/get operations (e.g., `confluent_kafka_topic_list`, `confluent_kafka_topic_describe`, `confluent_schema_registry_schema_list`, `confluent_environment_list`, `confluent_kafka_cluster_list`, `confluent_kafka_cluster_describe`, `confluent_connector_list`, `confluent_connector_describe`, `confluent_flink_statement_list`, `confluent_flink_statement_describe`, `confluent_flink_compute_pool_list`, `confluent_flink_compute_pool_describe`, `confluent_rbac_role_binding_list`, `confluent_service_account_list`, `confluent_api_key_list`, `confluent_schema_registry_subject_list`, `confluent_schema_registry_compatibility_get`, `confluent_kafka_consumer_group_list`, `confluent_kafka_consumer_group_describe`, `confluent_network_list`, `confluent_peering_list`, `confluent_transit_gateway_attachment_list`, `confluent_private_link_attachment_list`, `confluent_cluster_link_list`, `confluent_kafka_mirror_topic_list`)
    - `"engineer"` tier: create/update/delete for standard non-destructive resources (e.g., `confluent_kafka_topic_create`, `confluent_kafka_topic_update`, `confluent_kafka_topic_delete`, `confluent_schema_registry_schema_create`, `confluent_schema_registry_compatibility_update`, `confluent_flink_statement_create`, `confluent_flink_statement_delete`, `confluent_flink_compute_pool_create`, `confluent_flink_compute_pool_update`, `confluent_rbac_role_binding_create`, `confluent_rbac_role_binding_delete`, `confluent_connector_create`, `confluent_connector_update`, `confluent_connector_delete`, `confluent_connector_pause`, `confluent_connector_resume`, `confluent_service_account_create`, `confluent_api_key_create`, `confluent_api_key_delete`)
    - `"break-glass"` tier: destructive/infrastructure operations (e.g., `confluent_environment_create`, `confluent_environment_delete`, `confluent_kafka_cluster_create`, `confluent_kafka_cluster_update`, `confluent_kafka_cluster_delete`, `confluent_flink_compute_pool_delete`, `confluent_network_create`, `confluent_network_delete`, `confluent_peering_create`, `confluent_peering_delete`, `confluent_transit_gateway_attachment_create`, `confluent_transit_gateway_attachment_delete`, `confluent_private_link_attachment_create`, `confluent_private_link_attachment_delete`, `confluent_cluster_link_create`, `confluent_cluster_link_delete`, `confluent_kafka_mirror_topic_create`, `confluent_kafka_mirror_topic_delete`, `confluent_service_account_delete`)

    Count the total entries and ensure >= 50. If short, enumerate additional mcp-confluent resources (kafka ACL operations, schema exporter operations, etc.) until the threshold is met.

    Then update the three profile JSONs:

    **read-only.json** — keep `allowed_operations: []` (unchanged — read-only permits no apply operations; the tier system governs MCP tool access separately). No changes needed.

    **engineer.json** — keep existing `allowed_operations` list unchanged (these are fsi-dsp artifact IDs, not MCP tool names). No changes needed to this file.

    **break-glass.json** — replace `"allowed_operations": ["*"]` with explicit list of all fsi-dsp artifact operation patterns that exist. Use: `["module/topic", "module/flink", "role/cp_schema", "role/cp_rbac", "role/cp_connect", "script/fsi-dr", "scenario/cc-aws"]`. The wildcard is replaced per ACTG-01 "by name, not regex" requirement. Keep `name` and `description` fields.
  </action>
  <verify>
    <automated>python3 -c "import json; d=json.load(open('tools/profiles/tool_classification.json')); assert len(d['tools']) >= 50, f'Only {len(d[\"tools\"])} tools'; assert d['unclassified_policy'] == 'deny'; print(f'OK: {len(d[\"tools\"])} tools classified')" && python3 -c "import json; d=json.load(open('tools/profiles/break-glass.json')); assert '*' not in d['allowed_operations'], 'Wildcard still present'; print('OK: no wildcard in break-glass')"</automated>
  </verify>
  <acceptance_criteria>
    - `tools/profiles/tool_classification.json` exists and parses as valid JSON
    - `len(json.load(...)["tools"]) >= 50` — at least 50 tool entries
    - Every value in the `"tools"` dict is one of: `"read-only"`, `"engineer"`, `"break-glass"`
    - `"unclassified_policy": "deny"` present in classification JSON
    - `tools/profiles/break-glass.json` `allowed_operations` does NOT contain `"*"`
    - `tools/profiles/break-glass.json` `allowed_operations` contains explicit artifact IDs
    - `tools/profiles/engineer.json` still contains `"module/topic"` and `"module/flink"` in `allowed_operations`
    - `tools/profiles/read-only.json` still has `"allowed_operations": []`
  </acceptance_criteria>
  <done>Classification table has 50+ explicit tool-to-tier mappings. Break-glass wildcard replaced with explicit list. All profile JSONs valid.</done>
</task>

<task type="auto">
  <name>Task 2: Create acme-bank customer engineer profile overlay and ADR-003</name>
  <files>
    canon/customer/acme-bank/profiles/engineer.json,
    canon/customer/acme-bank/adrs/adr-003.md
  </files>
  <read_first>
    tools/profiles/engineer.json,
    canon/customer/acme-bank/overrides.yaml,
    canon/customer/acme-bank/adrs/adr-002.md
  </read_first>
  <action>
    Create directory `canon/customer/acme-bank/profiles/` if it does not exist.

    Create `canon/customer/acme-bank/profiles/engineer.json` as a COMPLETE profile document (same schema as base engineer.json, NOT a partial diff) per CONTEXT.md locked decision and RESEARCH.md Pitfall 4.

    Content:
    ```json
    {
      "name": "engineer",
      "description": "Acme Bank engineer profile: Flink self-service prohibited, audit role management required.",
      "allowed_operations": ["module/topic", "role/cp_schema", "role/cp_rbac", "role/cp_connect", "role/cp_audit"],
      "customer_overrides": {
        "removed": ["module/flink"],
        "added": ["role/cp_audit"],
        "adr_ref": "canon/customer/acme-bank/adrs/adr-003.md"
      }
    }
    ```

    Key differentials vs base engineer:
    - REMOVED: `"module/flink"` (bank prohibits self-service Flink)
    - ADDED: `"role/cp_audit"` (bank requires audit role management)
    - The `customer_overrides` metadata block is documentation only — `load_profile()` uses `allowed_operations`.

    Create `canon/customer/acme-bank/adrs/adr-003.md` following the exact pattern of adr-002.md (Status: Accepted, sections: Context, Decision, Consequences). Content:

    ```markdown
    # ADR-003: Flink Prohibition and Audit Role Addition

    ## Status

    Accepted

    ## Context

    Acme Bank prohibits self-service Flink operations due to their shared multi-tenant Flink compute pool architecture. Uncoordinated Flink statement creation risks resource contention across trading desks. Separately, Acme Bank requires audit role management (cp_audit) as a standard engineer operation for SOX compliance — their compliance team must be able to grant/revoke audit bindings without break-glass escalation.

    ## Decision

    Override the base engineer profile for Acme Bank:
    - Remove `module/flink` from `allowed_operations` (was permitted in base engineer)
    - Add `role/cp_audit` to `allowed_operations` (not present in base engineer)

    All other engineer permissions remain unchanged from base.

    ## Consequences

    - Engineers at Acme Bank cannot create, update, or delete Flink statements or compute pools without break-glass escalation
    - Flink operations require explicit break-glass approval with documented override reason
    - Audit role binding management is available at engineer tier, reducing break-glass frequency for compliance workflows
    - Tests in test_profile_gating.py verify this differential: module/flink denied, role/cp_audit permitted
    ```
  </action>
  <verify>
    <automated>python3 -c "import json; d=json.load(open('canon/customer/acme-bank/profiles/engineer.json')); assert 'module/flink' not in d['allowed_operations'], 'flink should be removed'; assert 'role/cp_audit' in d['allowed_operations'], 'cp_audit missing'; assert d['name'] == 'engineer'; print('OK: acme-bank engineer differential verified')" && test -f canon/customer/acme-bank/adrs/adr-003.md && echo "OK: ADR-003 exists"</automated>
  </verify>
  <acceptance_criteria>
    - `canon/customer/acme-bank/profiles/engineer.json` exists and parses as valid JSON
    - `"module/flink"` is NOT in `allowed_operations` array
    - `"role/cp_audit"` IS in `allowed_operations` array
    - `"name": "engineer"` present (complete profile doc, not partial diff)
    - `"module/topic"` still in `allowed_operations` (other base permissions preserved)
    - `canon/customer/acme-bank/adrs/adr-003.md` exists
    - ADR-003 contains "Accepted" status
    - ADR-003 contains "module/flink" and "role/cp_audit" in Decision section
  </acceptance_criteria>
  <done>acme-bank engineer overlay created with module/flink removed and role/cp_audit added. ADR-003 documents the override per CANST-03.</done>
</task>

</tasks>

<verification>
- `python3 -c "import json; d=json.load(open('tools/profiles/tool_classification.json')); print(f'{len(d[\"tools\"])} tools classified'); assert len(d['tools']) >= 50"`
- `python3 -c "import json; d=json.load(open('tools/profiles/break-glass.json')); assert '*' not in d['allowed_operations']"`
- `python3 -c "import json; d=json.load(open('canon/customer/acme-bank/profiles/engineer.json')); assert 'module/flink' not in d['allowed_operations']; assert 'role/cp_audit' in d['allowed_operations']"`
- `test -f canon/customer/acme-bank/adrs/adr-003.md`
- Existing tests still pass: `pytest tests/test_apply_engine.py -x -q`
</verification>

<success_criteria>
- tool_classification.json contains >= 50 mcp-confluent tools classified by explicit name
- All three profile tiers (read-only, engineer, break-glass) used in classification
- break-glass.json wildcard replaced with explicit artifact list
- acme-bank engineer overlay demonstrates differential (no flink, has cp_audit)
- ADR-003 documents the acme-bank override
- All existing tests pass (no regressions)
</success_criteria>

<output>
After completion, create `.planning/phases/03C-act-rail-profile-gating/03C-01-SUMMARY.md`
</output>
