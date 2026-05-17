# Phase H.4c: acme-bank developer overlay — Context

**Gathered:** 2026-05-17
**Status:** Ready for planning
**Mode:** Auto (--auto) — defaults selected from H.4b dev canon contract, ACTG-04 customer-fork pattern, existing acme-bank engineer overlay shape

<domain>
## Phase Boundary

Mirror v1.0 Phase 3c's ACTG-04 customer-fork pattern for the developer family. Specifically: author `canon/customer/acme-bank/profiles/developer/sandbox.json` so that loading the developer-sandbox profile under the `acme-bank` customer produces a different gating result than the base FSI dev canon — and prove that with a test that asserts ≥1 differential decision. This proves the canon overlay stack works the same way for the developer family as it does for the operator family (ACTG-04 demonstrated this for engineer-tier customer overlays in v1.0).

After H.4c: `load_profile("developer/sandbox", customer="acme-bank")` returns the acme-overlayed profile (smaller `tool_overrides` map and/or different `skill_blocklist`); `check_tool_permitted("developer/sandbox", <tool>, customer="acme-bank")` produces at least one decision that differs from `check_tool_permitted("developer/sandbox", <tool>)` (no customer). DEVPROF-02 is fully satisfied.

**Out of scope:**
- New customer beyond acme-bank (one customer overlay proof is enough)
- Engagement-level overlays (canon/engagement layer untouched)
- Changes to base FSI dev canon (H.4b's overrides.yaml stays put)
- /dsp:scaffold consumer integration (H.3c)
- Activity-log family field (still deferred)
- ADR file authoring beyond a stub (promote to formal ADR after one engagement uses the dev overlay)

</domain>

<decisions>
## Implementation Decisions

### Customer overlay shape
- **D-01:** `canon/customer/acme-bank/profiles/developer/sandbox.json` follows the same overlay-with-`customer_overrides` field pattern as the existing `canon/customer/acme-bank/profiles/engineer.json`. The overlay file IS a complete profile (loaded directly when customer is acme-bank), not a partial diff. This matches what v1.0 Phase 3c established and what the existing `load_profile()` customer branch expects.
- **D-02:** Differential decisions in the acme-bank dev overlay (chosen to mirror acme-bank's existing posture):
  - **Removed from tool_overrides:** `delete-topics` and `alter-topic-config` — acme-bank's dev sandbox is stricter than base FSI dev canon. Even dev developers must request topic destruction via a separate ticket (mirrors acme-bank engineer profile, which removes `module/flink` to prohibit self-service Flink).
  - **Added to skill_blocklist:** `dsp-plan` — acme-bank developers cannot use `/dsp:plan` from a dev profile (engagement guardrail). Base FSI dev canon does not block `/dsp:plan`. This is the explicit differential gating signal the test asserts.
  - **environment_guard pattern:** `acme-*-sandbox` (more specific than base `*-sandbox`) — restricts the dev profile to acme-prefixed sandbox clusters.
  - **canon_layer:** unchanged — `industry/fsi/developer-sandbox` (acme-bank inherits the FSI dev overlay without further bifurcation; it's customer-tier overrides on the profile, not canon-tier overrides on the dev YAML).
- **D-03:** `customer_overrides` field documents WHAT was removed/added vs base FSI dev canon + cites the ADR rationale (see D-05). This is the auditable trail per the canon-overlay-with-ADR rule.

### Engine path verification
- **D-04:** No changes to `tools/apply_engine.py` — H.4b's `_profile_path()` helper already handles `tools/profiles/developer/sandbox.json` and the customer-overlay path resolution applies the same logic to `canon/customer/<name>/profiles/developer/sandbox.json`. H.4c just provides the file at the expected path; the engine picks it up automatically.

### ADR stub
- **D-05:** Add `canon/customer/acme-bank/adrs/adr-004.md` — a stub ADR titled "Acme Bank developer-sandbox profile overrides". One-page document referencing the H.4c CONTEXT decisions; sets `status: Accepted` (consistent with the base acme-bank ADRs being already-Accepted). The ADR cross-references the existing adr-003.md (engineer profile customer overrides) because the dev overlay follows the same shape one family over.

### Test surface
- **D-06:** Add ONE new test class `TestAcmeBankDeveloperOverlay` to `tests/test_per_family_isolation.py` (the file H.4b created — keep family-related tests in one place):
  1. `test_acme_bank_developer_overlay_loads` — `load_profile("developer/sandbox", customer="acme-bank")` returns a profile with `customer_overrides` field referencing adr-004.
  2. `test_acme_bank_dev_overlay_produces_differential_gating` — at least ONE (profile-method, args) call produces a different result with vs without customer=acme-bank. Specifically asserts: `check_tool_permitted("developer/sandbox", "delete-topics")` returns True (base dev allows) but `check_tool_permitted("developer/sandbox", "delete-topics", customer="acme-bank")` returns False (acme removes from overrides).
  3. `test_acme_bank_dev_overlay_blocks_dsp_plan` — `check_skill_permitted("developer/sandbox", "dsp-plan", customer="acme-bank")` returns False; the base equivalent returns True. Proves the skill_blocklist differential.
- **D-07:** Snapshot the acme-bank dev permits matrix as `tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json`. The diff against H.4b's `h4b_developer_sandbox_permits.json` is exactly the differential gating set — a glance at the snapshot diff shows the customer overlay's effect at a glance.

### Folded Todos
None — `todo match-phase H.4c` returned zero matches.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project canon
- `CLAUDE.md` — FSI canon (informs why dev overlay differs from prod overlay; acme is one customer fork).
- `.planning/REQUIREMENTS.md` §DEVPROF-02 — "canon/customer/acme-bank/profiles/developer/sandbox.json exists; test proves customer overlay produces ≥1 differential gating decision relative to base FSI dev canon".

### Prior-phase contexts
- `.planning/phases/H.4b-developer-sandbox-profile-fsi-dev-canon/H.4b-CONTEXT.md` — Base developer-sandbox profile that this overlay forks from.
- `.planning/phases/03C-act-rail-profile-gating/03C-CONTEXT.md` — ACTG-04 customer-fork pattern for engineer family; H.4c mirrors it for developer family.

### Existing code under modification
- `canon/customer/acme-bank/profiles/developer/sandbox.json` (new) — acme-bank developer overlay.
- `canon/customer/acme-bank/adrs/adr-004.md` (new) — ADR stub for the overlay.
- `tests/test_per_family_isolation.py` (extend) — add `TestAcmeBankDeveloperOverlay` class.
- `tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json` (new) — snapshot of acme-bank dev permit matrix.

### Existing customer-overlay precedent
- `canon/customer/acme-bank/profiles/engineer.json` — Engineer-family customer overlay; H.4c's developer/sandbox.json follows the same shape one family over.
- `canon/customer/acme-bank/adrs/adr-003.md` — ADR for engineer profile customer overrides; H.4c's adr-004 cross-references this.
- `canon/customer/acme-bank/overrides.yaml` — Canon-tier customer overrides (acme producer compression, latency tiers); H.4c does NOT modify this file (no canon-tier change for acme-bank developer family — only profile-tier change).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`_profile_path()` helper (H.4b)** — Already handles slash-separated profile names; works for customer overlay path automatically. Zero engine changes.
- **`canon/customer/acme-bank/profiles/engineer.json` shape** — Direct template. The dev overlay is identical structure (name, description, family, customer_overrides, plus dev-family fields tool_overrides, skill_blocklist).
- **H.4b's per-family isolation test file** — Already exists with the right import set; H.4c appends one new class.
- **H.4b's developer-sandbox snapshot pattern** — Replicate verbatim for the acme overlay snapshot.

### Established Patterns
- **Customer overlay is a complete profile, not a diff** — `load_profile()` returns the overlay file's content directly when customer is set and the file exists. `customer_overrides` field is documentation/audit only.
- **ADR per customer override** — `canon/customer/acme-bank/adrs/adr-NNN.md` is the standard location; H.4c's stub matches.
- **Snapshot regression** — Both H.4a and H.4b use `tests/snapshots/*.json`; H.4c continues the pattern.

### Integration Points
- **`canon/customer/acme-bank/profiles/developer/sandbox.json`** — New file (creates the developer/ directory).
- **`canon/customer/acme-bank/adrs/adr-004.md`** — New ADR stub.
- **`tests/test_per_family_isolation.py`** — Append one test class.
- **`tests/snapshots/h4c_acme_bank_developer_sandbox_permits.json`** — New snapshot.
- **No changes** to apply_engine.py, canon/stack.py, base developer profile, FSI dev canon overlay, or operator profiles.

</code_context>

<specifics>
## Specific Ideas

- **Differential signals chosen for visibility**: removing `delete-topics` + `alter-topic-config` from tool_overrides AND adding `dsp-plan` to skill_blocklist gives THREE differential signals — making the test robust against future changes that might re-add one of the tools to the base canon. Two of three differentials are tool-level; one is skill-level. Both layers of differential gating are exercised.
- **environment_guard pattern `acme-*-sandbox`**: more specific than base `*-sandbox`. Even advisory-only, it documents the intended scope and gives the future env-guard CI enforcement a clear target.
- **Why not modify acme-bank's overrides.yaml (canon-tier)?**: Because that file already encodes acme's PROD canon differentials (sub-100-microsecond market data, zstd compression). The dev family inherits FSI dev canon (industry/fsi/developer-sandbox/overrides.yaml) without customer-tier canon overrides. acme's customer-tier differentiation for dev family lives entirely on the PROFILE, not the canon layer. This keeps the canon stack composition simple and matches H.4b's design.

</specifics>

<deferred>
## Deferred Ideas

- **acme-bank canon-tier dev overrides** (a `canon/customer/acme-bank/developer-sandbox/overrides.yaml`) — Could exist if acme wants different dev-canon values from base FSI dev canon (e.g., stricter dev topic naming). Deferred until acme has an actual sandbox engagement that needs it.
- **/dsp:scaffold integration with acme dev overlay** — H.3c uses this overlay as a test case for customer-aware scaffolding.
- **Promote adr-004 stub to a full ADR** — After acme uses the dev profile in practice and the differentials prove sound.
- **Additional customer dev overlays** (e.g., a hypothetical bank-2 with different differentials) — Wait for use case.
- **environment_guard CI enforcement on acme-*-sandbox pattern** — Future enhancement once env-guard moves from advisory to enforced.

### Reviewed Todos (not folded)
None.

</deferred>

---

*Phase: H.4c-acme-bank-developer-overlay*
*Context gathered: 2026-05-17 (auto-mode)*
