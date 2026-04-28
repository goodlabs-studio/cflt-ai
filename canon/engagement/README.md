# Engagement Layer — Per-Engagement Overrides

Empty scaffold. Populated per engagement for engagement-specific canon adjustments.

## Usage

1. Create `canon/engagement/{engagement-name}/overrides.yaml`
2. Add an ADR in `canon/engagement/{engagement-name}/adrs/` justifying each override
3. Overrides compose on top of base + industry + customer layers

No override without an ADR. Engagement overrides are the most specific and have highest priority.
