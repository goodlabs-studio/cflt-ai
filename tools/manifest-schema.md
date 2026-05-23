# MANIFEST.yaml v1 schema reference

Authoritative reference for the `fsi-dsp/manifest/v1` schema. The MANIFEST lives at
`raw/repos/fsi-dsp/MANIFEST.yaml`. Schema validation is enforced by
[`tools/check_manifest.py`](check_manifest.py) and tested by
[`tests/test_manifest.py`](../tests/test_manifest.py).

> **CI gate:** Adding a new type, field, or constraint requires updating BOTH this doc AND
> the validator's `KNOWN_TYPES` / per-type field constants. `test_known_types_constant_shape`
> will fail if the validator drifts from the documented set.

## Top-level fields

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `version` | yes | string | Semver. Major bump required to remove stable IDs (enforced by `raw/repos/fsi-dsp/scripts/check-manifest-stability.py`). |
| `schema` | yes | string | Must equal `fsi-dsp/manifest/v1`. |
| `capabilities` | yes | list | Ordered list of capability objects (see below). |

## Base capability fields (all types)

Every capability entry, regardless of `type`, must have:

| Field | Required | Type | Notes |
|-------|----------|------|-------|
| `id` | yes | string | Stable contract. Must begin with a known type prefix (see [ID prefix rule](#id-prefix-rule)). Once published, cannot be removed without a major version bump. |
| `type` | yes | enum | Must be one of [Known types](#known-types). |
| `name` | yes | string | Human-readable short name. |
| `path` | yes | string | Repo-relative path to the asset (file or directory). Verified to exist by `test_paths_exist`. |
| `description` | no | string | One-line summary (recommended but not required by the validator). |

### ID prefix rule

The `id` field must begin with one of these prefixes (one per `type`):

`role/`, `module/`, `scenario/`, `adr/`, `reference/`, `script/`, `observability/`, `accelerator/`

Enforced by `test_ids_have_type_prefix`.

## Known types

| Type | Prefix | Required extra fields | Example |
|------|--------|-----------------------|---------|
| `ansible-role` | `role/` | (none beyond base) | `role/cp_topic` |
| `terraform-module` | `module/` | (none beyond base) | `module/topic` |
| `scenario` | `scenario/` | (none beyond base) | `scenario/cc-aws` |
| `adr` | `adr/` | (none beyond base) | `adr/001` |
| `reference` | `reference/` | (none beyond base) | `reference/java-producer` |
| `script` | `script/` | (none beyond base) | `script/mirror-failover` |
| `observability` | `observability/` | (none beyond base) | `observability/dynatrace` |
| `accelerator` | `accelerator/` | `apply_sequence`, `build_command`, `dry_run_command`, `apply_command` | `accelerator/confluent-on-linuxone` |

## Accelerator type (added in v2.1 Phase 10, MAN-01)

The `accelerator` type registers a layered, kustomize-style artifact (initially
`accelerators/confluent-on-linuxone/`) with explicit dependency-ordered layers and
explicit build/dry-run/apply commands so non-kustomize accelerators (Helm, Terraform)
can reuse the schema unchanged.

**Required extra fields:**

- `apply_sequence` — non-empty list of layer objects. Layers execute top-to-bottom.
  Each layer object requires `layer`, `path`, `canon_key`.
    - `layer` — short identifier (e.g., `01-rbac`).
    - `path` — repo-relative path to the kustomize layer directory.
    - `canon_key` — canonical canon key the layer enforces (single source of truth — Phase 11's MODULE_TO_CANON_KEY reads this; **do not** duplicate the layer-to-canon mapping in cflt-ai).
- `build_command` — non-empty string. Command to produce the rendered artifact (e.g., `kustomize build overlays/prod`).
- `dry_run_command` — non-empty string. Command that simulates apply without side effects (e.g., piped through `oc apply --dry-run=server`).
- `apply_command` — non-empty string. Command that performs the real apply.

**Example** (real entry from `raw/repos/fsi-dsp/MANIFEST.yaml`):

```yaml
- id: "accelerator/confluent-on-linuxone"
  type: accelerator
  name: "confluent-on-linuxone"
  path: "accelerators/confluent-on-linuxone"
  description: "Confluent Platform on IBM LinuxONE -- FSI-hardened RBAC + mTLS + SR governance + audit + Flink layers via Kustomize Components over Mondics's upstream base"
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

## Adding a new type

1. Open the fsi-dsp PR adding the entry (with required extra fields if any).
2. Update `tools/check_manifest.py`:
   - Add the type string to `KNOWN_TYPES`.
   - If the type has required extra fields, add a `_validate_<type>()` helper and call it from `validate_capability`.
3. Update this doc (`tools/manifest-schema.md`):
   - Add a row to the [Known types](#known-types) table.
   - If the type has extra fields, add a dedicated section.
4. Update `tests/test_manifest.py`:
   - Add an `EXPECTED_<TYPE>` list with the IDs of the new type.
   - Add a `test_all_<types>_present` method.
   - Add the prefix to `valid_prefixes` in `test_ids_have_type_prefix`.
   - Add a negative-space test if the type has required extra fields.
5. Bump the prefix set in the [ID prefix rule](#id-prefix-rule) section of this doc.

## CI enforcement

- `pytest tests/test_manifest.py` — full schema + path-existence + prefix + expected-ID tests.
- `python3 tools/check_manifest.py` — fast schema-only validation (no path existence, no expected-ID check). Suitable for pre-commit hooks if configured.
- `python3 raw/repos/fsi-dsp/scripts/check-manifest-stability.py` — runs INSIDE the submodule; blocks PRs that remove stable IDs without a major version bump (CNTR-04).
