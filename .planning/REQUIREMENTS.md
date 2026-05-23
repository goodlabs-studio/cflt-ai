# Milestone v2.1 Requirements — LinuxONE Accelerator Integration

**Scope:** Integrate the new `accelerators/confluent-on-linuxone/` tier from upstream fsi-dsp into cflt-ai's canon, wiki, and act rail. Three categories: submodule sync, accelerator artifact-type registration, and wiki ingest.

**REQ-ID prefixes:** `SUBM-` (submodule sync), `MAN-` (manifest/accelerator), `WIKI-` (wiki ingest). Continued from v2.0 (EVAL-, CTRL-, SKILL-, CANON-).

---

## Active Requirements (v2.1)

### Submodule Sync — `SUBM-*`

- [x] **SUBM-01**: User can run `git submodule update --remote raw/repos/fsi-dsp` and the local pointer advances to upstream `main` HEAD; no manual conflict resolution required.
- [x] **SUBM-02**: After the bump, `pytest tests/test_check_canon_parity.py tests/test_manifest.py` passes — the two pre-existing test failures from the v2.0 audit are resolved.
- [x] **SUBM-03**: A CI guard asserts the submodule tracks upstream `main` and is within an allowed drift window (e.g., ≤14 days behind HEAD); workflow fails on stale-submodule drift with a clear remediation message.

### Accelerator Artifact-Type — `MAN-*`

- [x] **MAN-01**: User can declare `type: accelerator` in fsi-dsp MANIFEST.yaml entries; cflt-ai's manifest schema validator accepts the new type without regressing on existing types (`ansible-role`, `terraform-module`, `scenario`, `adr`, `reference`).
- [x] **MAN-02**: User can run `/dsp:plan create accelerator confluent-on-linuxone --layer 01-rbac` and the four-gate plan rail returns a structurally-correct plan referencing the accelerator artifact by MANIFEST ID with full canon-stack provenance footer.
- [x] **MAN-03**: User can run `/dsp:apply` against an accelerator plan and the executor dispatches the kustomize apply_sequence (build → `oc apply --dry-run=server` → `oc apply`) layer-by-layer; activity log records per-layer outcomes per ACTA-04 schema.
- [x] **MAN-04**: MODULE_TO_CANON_KEY covers all 5 layers (`01-rbac` → `fsi.security.mds-rbac`, `02-tls` → `fsi.security.tls-fips`, `03-schema-governance` → `fsi.schema.compatibility-full-transitive`, `04-audit` → `fsi.audit.events-retention`, `05-flink` → `fsi.flink.environment-mtls`); unknown layers produce blocking `DRIFT-1` violations matching the G.1 terraform-module precedent.
- [x] **MAN-05**: Bidirectional canon-parity CI extends to accelerator MANIFEST entries — drift between cflt-ai's canon map and upstream MANIFEST blocks merge in both repos (mirrors G.2c CI pattern).

### Wiki Ingest — `WIKI-*`

- [ ] **WIKI-01**: User can run `/ask "How do I deploy Confluent Platform on IBM LinuxONE for FSI?"` and the answer cites the new accelerator wiki article with `confidence: high` and provenance to upstream `DESIGN.md` at the pinned SHA.
- [ ] **WIKI-02**: All 13 `KNOWN-GAPS.md` entries (G-01..G-13) are encoded as `tools/vendor-sources.json` trip-wires (status, workaround, FSI impact); `/wiki:lint --full` surfaces drift when upstream gap status changes.
- [ ] **WIKI-03**: User can run `/review` against a customer LinuxONE deployment doc and the review flags any claim that contradicts the auditor-readonly payload-isolation pattern (DeveloperRead is consume-granting → topic-scoped binding required for true `payments.*` isolation).
- [ ] **WIKI-04**: ≥6 wiki articles ship covering: LinuxONE-on-CFK reference architecture, x86→LinuxONE Cluster Linking migration with regulatory evidence checklist, FIPS-at-install OCP requirement, auditor-readonly RBAC payload-isolation pattern, custom s390x image build pipeline (Connect + Flink SQL-runner), Flink-on-CFK FSI example jobs (tumbling-window + temporal join).
- [ ] **WIKI-05**: Golden eval harness gains ≥15 cases covering the new articles at the H.2 `EVAL-02` floor (10 cases/skill minimum across `/ask` and `/review`); harness passes at 90% CI threshold.

---

## Out of Scope

- **G.2 carry-forward (G.2a, G.2b, G.2d, G.2e)** — composite scenario executor, GitOps apply mode, ansible-role executor, tool-call executor. Reason: each is its own milestone-sized lift; G.2b is the natural follow-on to MAN-03 but deferred to keep v2.1 focused.
- **`/dsp:scaffold` expansion to remaining 4 artifact-types** (consumer, kafka-streams-app, schema, cdc-pipeline). Reason: v2.0 tech debt; orthogonal to accelerator integration.
- **`scaffolded-producer` executor inside fsi-dsp** — Reason: requires separate fsi-dsp PR cycle.
- **Promote developer-sandbox CONTEXT decisions to formal ADRs** — Reason: blocked on first customer engagement using the developer profile in practice.
- **Live OCP-on-LinuxONE cluster deployment in CI** — Reason: validation scripts in the accelerator are cluster-dependent by design (KNOWN-GAPS G-01); CI exercises kustomize-build and structural validation only.

---

## Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| SUBM-01 | 9 | Active |
| SUBM-02 | 9 | Active |
| SUBM-03 | 9 | Active |
| MAN-01 | 10 | Active |
| MAN-02 | 11 | Active |
| MAN-03 | 11 | Active |
| MAN-04 | 11 | Active |
| MAN-05 | 11 | Active |
| WIKI-01 | 12 | Active |
| WIKI-02 | 12 | Active |
| WIKI-03 | 12 | Active |
| WIKI-04 | 12 | Active |
| WIKI-05 | 12 | Active |

**Coverage:** 13/13 v2.1 requirements mapped across 4 phases. No orphans, no duplicates.

---

*Created: 2026-05-23 — Milestone v2.1 (LinuxONE Accelerator Integration) started*
*Updated: 2026-05-23 — Traceability filled by gsd-roadmapper at roadmap creation (9–12)*
