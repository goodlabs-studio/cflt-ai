# Canon Overlay Stack

Four-layer composition stack for Confluent canonical defaults. Each layer can override the layer above. Overrides compose (merge), they do not replace.

## Layers (bottom to top)

1. **base/** — GoodLabs universal defaults (extracted from CLAUDE.md)
2. **industry/fsi/** — FSI-specific overrides (backed by fsi-dsp ADRs)
3. **customer/** — Per-customer overrides (empty scaffold; populated per engagement)
4. **engagement/** — Per-engagement overrides (empty scaffold; populated per engagement)

## Resolution Order

`base -> industry/{name} -> customer/{name} -> engagement/{name}`

Later layers override earlier layers via dict merge. The resulting merged config is the "active stack."

## Override Rules

- Every override MUST reference an ADR in the layer's `adrs/` directory
- Overrides use `override_source:` field citing the ADR ID
- No override without documentation; this is the trust mechanism

## Stack Hash

`canon/stack.py resolve_stack()` computes the active config and a SHA-256 hash for provenance footers.
