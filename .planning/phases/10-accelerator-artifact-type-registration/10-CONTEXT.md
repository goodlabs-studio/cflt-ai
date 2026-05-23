# Phase 10: Accelerator artifact-type registration — Context

**Gathered:** 2026-05-23
**Status:** Ready for planning
**Mode:** Auto-generated (autonomous run; locked decisions captured inline rather than via grey-area discussion since the schema shape is constrained by upstream MANIFEST conventions and the kustomize-build pattern)

<domain>
## Phase Boundary

Land `type: accelerator` as a first-class MANIFEST.yaml artifact type in upstream fsi-dsp and extend cflt-ai's manifest schema validator to accept the new type without regressing on existing types. After this phase, the type contract exists end-to-end and downstream consumers in Phase 11 can wire to a stable artifact shape.

**In scope:**
- New MANIFEST.yaml entry registering `accelerators/confluent-on-linuxone/` with `type: accelerator`
- `apply_sequence` schema declaring the 5 kustomize layers
- cflt-ai validator extension accepting the new type
- Positive + negative validation tests
- Documentation update in cflt-ai's MANIFEST contract reference

**Out of scope:**
- Plan-rail/apply-rail dispatch logic (that's Phase 11)
- Wiki articles citing the new entry (Phase 12)
- Upstream PR merge timing — the PR can land on a follow-up; cflt-ai-side validator work tests against fixtures and committed-in-submodule shape

</domain>

<decisions>
## Implementation Decisions

### MANIFEST.yaml shape (locked)

The new entry follows the existing v1 schema conventions (id, type, name, path, description) plus an accelerator-specific `apply_sequence`:

```yaml
- id: "accelerator/confluent-on-linuxone"
  type: accelerator
  name: "confluent-on-linuxone"
  path: "accelerators/confluent-on-linuxone"
  description: "Confluent Platform on IBM LinuxONE — FSI-hardened RBAC + mTLS + SR governance + audit + Flink layers via Kustomize Components over Mondics's upstream base"
  apply_sequence:
    - layer: "01-rbac"
      path: "accelerators/confluent-on-linuxone/layers/01-rbac"
      canon_key: "fsi.security.mds-rbac"
    - layer: "02-tls"
      path: "accelerators/confluent-on-linuxone/layers/02-tls"
      canon_key: "fsi.security.tls-fips"
    - layer: "03-schema-governance"
      path: "accelerators/confluent-on-linuxone/layers/03-schema-governance"
      canon_key: "fsi.schema.compatibility-full-transitive"
    - layer: "04-audit"
      path: "accelerators/confluent-on-linuxone/layers/04-audit"
      canon_key: "fsi.audit.events-retention"
    - layer: "05-flink"
      path: "accelerators/confluent-on-linuxone/layers/05-flink"
      canon_key: "fsi.flink.environment-mtls"
  build_command: "kustomize build overlays/prod"
  dry_run_command: "kustomize build overlays/prod | oc apply --dry-run=server -f -"
  apply_command: "kustomize build overlays/prod | oc apply -f -"
```

**Rationale:**
- `apply_sequence` is an array (ordered) — layers are dependency-ordered (RBAC → audit → Flink), executor walks them top-to-bottom
- `canon_key` per layer pre-wires the MODULE_TO_CANON_KEY map that Phase 11 consumes; placing it here means a single source of truth for layer→canon mapping (avoids the fsi-dsp/cflt-ai duplication failure mode that G.2c had to clean up)
- `build_command`/`dry_run_command`/`apply_command` are explicit (not hardcoded in cflt-ai) — different accelerators in the future may use Helm, Terraform, or other tools

### Validator extension (locked)

- Add `"accelerator"` to the type enum in `tools/check-manifest.py` (or `tools/check_manifest.py` — verify exact path during execution)
- Add `apply_sequence` field validation: required for `type: accelerator`, must be a non-empty list of layer objects, each with `{layer, path, canon_key}`
- Add `{build,dry_run,apply}_command` field validation: required for `type: accelerator`, must be non-empty strings
- Existing types (`ansible-role`, `terraform-module`, `scenario`, `adr`, `reference`) must continue to validate unchanged

### Test shape (locked)

- **Positive coverage:** `test_manifest_accepts_accelerator_type` — validates a real fixture matching the new entry shape
- **Negative coverage:**
  - `test_manifest_rejects_accelerator_missing_apply_sequence` — required field missing
  - `test_manifest_rejects_accelerator_empty_apply_sequence` — empty list
  - `test_manifest_rejects_accelerator_layer_missing_canon_key` — malformed layer object
  - `test_manifest_rejects_accelerator_missing_apply_command` — required command missing
- **Regression coverage:** existing test_manifest suite passes post-change without modification

### Where the work lands (locked)

- **Inside the submodule** (`raw/repos/fsi-dsp/MANIFEST.yaml`): Add the new entry. Commit inside submodule on a feature branch. Bump parent pointer in cflt-ai.
- **fsi-dsp upstream PR:** Defer the PR-opening action to the user; the local submodule commit lands the shape immediately so cflt-ai validator work + Phase 11 dispatch can proceed in parallel.
- **In cflt-ai:** Validator extension, tests, MANIFEST contract docs.

### Claude's Discretion

- Exact validator file path: discover at execution time (`tools/check_manifest.py` vs `tools/check-manifest.py`)
- Whether to use `enum` validation vs explicit type-check chain in the validator — match whatever pattern exists today
- Documentation file format: extend the existing `tools/manifest-schema.md` if it exists, otherwise add to `CONTRIBUTING.md`

</decisions>

<code_context>
## Existing Code Insights

- **`raw/repos/fsi-dsp/MANIFEST.yaml`** is at v1.1.0; schema `fsi-dsp/manifest/v1`. Existing types: `ansible-role` (9), `terraform-module` (2), `scenario` (6), `adr` (10), `reference` (12+). All entries have stable `id` per CNTR-04 enforcement.
- **`tools/check_manifest.py` / `tools/check-manifest.py`** — the schema validator that currently fails until v2.1 Phase 9's submodule bump landed (now PASSING).
- **`tests/test_manifest.py`** — the corresponding test suite; expects `version_is_1_1_0` post-Phase-9.
- **`tools/check_canon_parity.py` / `tools/check-canon-parity.py`** — currently maps MANIFEST entries to canon keys; the new `canon_key` per-layer field is intentionally co-located in MANIFEST so this script's logic stays simple.
- **`raw/repos/fsi-dsp/CLAUDE.md`** (lines ~50–110) — documents the v1 schema contract; new accelerator type should be added there too if maintained.

</code_context>

<specifics>
## Specific Ideas

- **Atomic landing:** Commit the MANIFEST entry inside fsi-dsp, then bump cflt-ai's submodule pointer + land the validator extension + tests in one atomic cflt-ai commit. Single rollback unit if Phase 11 surfaces issues.
- **fsi-dsp PR title pattern (when user opens it):** `feat(MANIFEST): register accelerator artifact-type with apply_sequence schema` — mirrors v1.1.0 conventions.
- **Don't fight CNTR-04 (ID stability):** The new `accelerator/confluent-on-linuxone` ID is fresh; no removal pressure on existing IDs.

</specifics>

<deferred>
## Deferred Ideas

- **Multiple accelerators:** Phase 10 registers only `confluent-on-linuxone`. Future accelerators (when they exist) follow the same shape. No multi-accelerator scaffolding needed yet.
- **Helm/Ansible-based accelerators:** Schema is intentionally extensible via `build_command`/`apply_command` strings but Phase 10 doesn't add helper hooks for non-kustomize accelerators. YAGNI until a non-kustomize accelerator surfaces.
- **Upstream fsi-dsp PR opening:** User explicitly opens; not autonomous.

</deferred>
