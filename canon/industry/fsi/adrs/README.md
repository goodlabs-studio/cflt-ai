# FSI Layer ADRs

This directory tracks which fsi-dsp ADRs justify overrides in this layer.
ADRs live in the fsi-dsp repo (`raw/repos/fsi-dsp/docs/adr/`); this README
indexes which ones are referenced by `overrides.yaml`.

## Referenced ADRs

| Override | ADR | Status |
|----------|-----|--------|
| Avro over Protobuf | fsi-dsp://adr/001 | Accepted |
| Compatibility by tier | fsi-dsp://adr/002 | Accepted |
| Cluster Linking over MRC | fsi-dsp://adr/005 | Accepted |
| OAuth vs API keys | fsi-dsp://adr/006 | Accepted |
| Topic naming | fsi-dsp://adr/007 | Accepted |
| DR tier classification | fsi-dsp://adr/008 | Accepted |
| LinuxONE for z/OS offload | fsi-dsp://adr/009 | Proposed |

## Adding an Override

1. Ensure the justifying ADR exists in fsi-dsp `docs/adr/`
2. Add the override to `overrides.yaml` with `override_source: "fsi-dsp://adr/NNN"`
3. Update this index
