# Retail Layer ADRs

This directory indexes the ADRs that justify overrides in `../overrides.yaml`.

**Status: template.** The entries below are placeholders. Industry ADRs may live in
this repo or in a retail-dsp submodule (mirroring how the FSI layer cites
`fsi-dsp://adr/NNN`); pick one convention and replace these before using retail.

## Referenced ADRs

| Override | ADR | Status |
|----------|-----|--------|
| Protobuf over Avro for retail scale | retail://adr/001 | Template |
| zstd compression (storage-constrained) | retail://adr/002 | Template |
| Channel-first topic naming | retail://adr/003 | Template |

## Adding an Override

1. Write the justifying ADR.
2. Add the override to `../overrides.yaml` with `override_source:`.
3. Update this index.
