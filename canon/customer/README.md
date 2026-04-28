# Customer Layer — Per-Customer Overrides

Empty scaffold. Populated per engagement when a customer requires canon overrides.

## Usage

1. Create `canon/customer/{customer-name}/overrides.yaml`
2. Add an ADR in `canon/customer/{customer-name}/adrs/` justifying each override
3. Overrides compose on top of base + industry layers

No override without an ADR.
