# Retail Industry Layer — Template / Starter Overlay

**Status: template.** This directory demonstrates the "directory-per-industry" model
alongside `canon/industry/fsi/`. The values in `overrides.yaml` are illustrative
placeholders, **not** engagement-validated canon — replace them before using retail
in any real recommendation, and back each override with a real ADR.

An industry layer is just a directory under `canon/industry/`. It composes on top of
`canon/base/defaults.yaml` via dict merge, and is selected by passing
`canon_layer="industry/retail"` to `resolve_stack()` (see `canon/stack.py`).

Industry canon is shareable IP and lives in this repo. Client-confidential canon does
NOT — it lives in a private repo loaded via `CFLT_CANON_EXTERNAL_PATH`
(see `CONTRIBUTING.md`).

## Shape (mirrors FSI)

```
industry/retail/
  README.md
  overrides.yaml                  # prod retail overlay
  adrs/README.md                  # ADR index
  developer-sandbox/
    overrides.yaml                # dev-tier relaxations
    adrs/README.md
```

## Adding an Override

1. Write the justifying ADR (industry ADRs may live in this repo or a retail-dsp
   submodule, mirroring how FSI cites `fsi-dsp://adr/NNN`).
2. Add the override to `overrides.yaml` with an `override_source:`.
3. Update `adrs/README.md`.
