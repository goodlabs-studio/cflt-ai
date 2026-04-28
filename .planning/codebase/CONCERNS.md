# Codebase Concerns

**Analysis Date:** 2026-04-28

## Tech Debt

**Python tool syntax errors:**
- Issue: `tools/wiki-stats.py` contains invalid Unicode characters (em-dash `─` U+2500) on lines 57, 59, 75 used directly in f-string formatting without raw string prefix
- Files: `tools/wiki-stats.py` (lines 57, 59, 75)
- Impact: Tool crashes on execution with SyntaxError, breaking wiki statistics reporting pipeline used by developers
- Fix approach: Replace Unicode em-dashes with ASCII hyphens (`-*50`) or use `print("─" * 50)` with proper string formatting

**Broken link regex in wiki-lint:**
- Issue: `tools/wiki-lint.py` line 81 regex `\[.*?\]\((wiki/[^)]+)\)` may not correctly match all wiki-internal link formats, particularly those with anchors (`wiki/path.md#section`) or URL parameters
- Files: `tools/wiki-lint.py` (line 81)
- Impact: Broken links may be missed during linting, allowing orphaned or malformed references to enter wiki
- Fix approach: Expand regex to `\[.*?\]\((wiki/[^)]+(?:#[^)]*)?)\)` to capture fragment identifiers; add test cases for edge cases

**Incomplete Phase 0 exit criteria:**
- Issue: PROJECT.md §Phase 0 requires "three bugs fixed" but references only two concrete bugs (`wiki-stats.py` syntax, `wiki-lint.py` broken-link regex) and vaguely references `evaluate.md` literal-ellipsis paths
- Files: `PROJECT.md` (line 27)
- Impact: Phase 0 exit is ambiguous; unclear what third bug to fix blocks Phase 1; team cannot determine completion status
- Fix approach: Enumerate all three bugs explicitly in PROJECT.md with file locations and expected outcomes

**wiki-lint.py missing `--fix` implementation:**
- Issue: `tools/wiki-lint.py` argument parser accepts `--fix` flag (line 104) but never uses it; lint findings are reported but never remediated
- Files: `tools/wiki-lint.py` (line 104, no implementation)
- Impact: Developers must manually fix lint failures; error-prone for bulk fixes (e.g., updating all broken link targets); blocks automation
- Fix approach: Implement `--fix` mode: rewrite broken link targets based on path resolution, update stale `last_updated` dates, auto-expand stubs

## Known Issues

**Unverified wiki claim:**
- Issue: `wiki/patterns/fsi-exactly-once.md` contains inline `⚠️ unverified` marker but no resolution plan; identified by lint as requiring source validation
- Files: `wiki/patterns/fsi-exactly-once.md`
- Impact: Article content flagged as questionable but no action assigned; uncertainty propagates to consumers relying on that pattern
- Workaround: `/wiki:validate` can resolve via Confluent docs MCP; mark as `confidence: medium` and assign to next review cycle
- Fix approach: Run `/wiki:validate` against Confluent docs to confirm/refute claims; update article with source links or demote to `confidence: low` if unverifiable

**Queue of unresolved wiki stubs:**
- Issue: `wiki/_queue.md` lists 7 stubs needed for FSI completeness (Flink on Confluent Cloud, private networking, event routing, etc.) but no timeline or assignee
- Files: `wiki/_queue.md` (lines 14-20)
- Impact: Critical knowledge gaps (Flink setup, Azure connection mgmt, DR app routing) remain undocumented; blocks customer engagements
- Fix approach: Assign stubs to `/gsd:map-codebase` phases; prioritize by customer blocking (Flink/Azure first); set deadline per engagement schedule

**Suspicious metrics access pattern:**
- Issue: `raw/repos/fsi-dsp/reference/python-producer/fsi_producer.py` lines 314-316 access Prometheus Counter `._value.get()` which is not a public API; breaks on prometheus_client version upgrades
- Files: `raw/repos/fsi-dsp/reference/python-producer/fsi_producer.py` (lines 314-316)
- Impact: Graceful shutdown logging fails silently if prometheus_client changes internal API; final metrics never logged
- Fix approach: Store metric snapshots in instance variables (`self._sent_count`, `self._error_count`) incremented during deliver callback, log those instead

**Consumer handler exception swallows errors without DLQ routing:**
- Issue: `raw/repos/fsi-dsp/reference/python-consumer/fsi_consumer.py` line 252 comment states "Default: log and continue (at-least-once semantics)" but handler errors are not routed to a DLQ topic; misaligned with producer's DLQ philosophy
- Files: `raw/repos/fsi-dsp/reference/python-consumer/fsi_consumer.py` (line 252)
- Impact: Failed record processing is logged but lost; no mechanism to replay/audit failures; regulatory requirement for transaction audit trail unmet
- Fix approach: Add optional `dlq_enabled` config parameter; route handler errors to `{topic_name}.dlq` with error context; implement `FsiDlqConsumer` handler that consumes from DLQ

## Security Considerations

**No TLS version pinning in Kafka clients:**
- Issue: Both `fsi_producer.py` and `fsi_consumer.py` set `security.protocol=SASL_SSL` but do not explicitly configure TLS version (min 1.2) or certificate validation
- Files: `raw/repos/fsi-dsp/reference/python-producer/fsi_producer.py` (line 157), `reference/python-consumer/fsi_consumer.py` (line 150)
- Impact: Client may negotiate TLS 1.0/1.1 with adversarial proxy; credentials exposed in transit; violates FSI compliance standards
- Current mitigation: confluent-kafka Python client defaults to TLS 1.2+; Confluent Cloud enforces TLS 1.2
- Recommendations: Explicitly document `ssl.ca.location`, `ssl.certificate.location`, `ssl.key.location` in config schema; add reference Vault integration for cert rotation

**Secrets in Prometheus metrics:**
- Issue: DLQ handler may serialize failed message values (containing PII/credentials) into Prometheus Counter labels (see `raw/repos/fsi-dsp/reference/python-producer/fsi_dlq_handler.py` if it exists)
- Files: Verify `reference/python-producer/fsi_dlq_handler.py` (not yet read)
- Impact: Secrets leaked in metrics scrape output; observable by network-adjacent attackers or in metric storage
- Recommendations: Ensure DLQ labels are topic-name only, never value/key content; hash sensitive fields before exposure

## Performance Bottlenecks

**Consumer single-threaded processing:**
- Issue: `raw/repos/fsi-dsp/reference/python-consumer/fsi_consumer.py` polls in single thread (line 199) and processes handler synchronously; no concurrency for I/O-bound work
- Files: `raw/repos/fsi-dsp/reference/python-consumer/fsi_consumer.py` (line 199, 240)
- Impact: For fraud detection use case (latency-critical), handler latency directly blocks poll loop; max throughput = 1 record / handler_latency; cannot saturate network bandwidth
- Improvement path: Offer optional executor pool (ThreadPoolExecutor) for handler tasks; emit metric for queue depth; add config `max.concurrent.handlers` (default: 1)

**Azure ILB timeout bypass incomplete:**
- Issue: `fsi_producer.py` and `fsi_consumer.py` set `socket.keepalive.enable=True` and `connections.max.idle.ms=180000` but comment (lines 148-150 producer, 136-138 consumer) notes Azure ILB kills idle TCP at 4min; 3min recycle is margin-tight
- Files: `raw/repos/fsi-dsp/reference/python-producer/fsi_producer.py` (lines 148-150), `reference/python-consumer/fsi_consumer.py` (lines 136-138)
- Impact: In idle periods, connection may still drop at boundary cases; missing keepalive probe documentation
- Improvement path: Add explicit `socket.keepalive.interval.ms=60000` (60s probes, well under 4min); test failover behavior at 3.5min idle; document Azure Private Link alternative

## Fragile Areas

**Terraform module `topic/` single responsibility overload:**
- Issue: `raw/repos/fsi-dsp/modules/topic/` is referenced in README and codebase as creating topic, schema, RBAC, DR mirror, and metadata tags in single `apply` — no composition or separation of concerns
- Files: `raw/repos/fsi-dsp/modules/topic/main.tf` (presumed, not directly read)
- Impact: Topic lifecycle tightly coupled to schema registration; cannot ship topic without schema; schema validation delays apply; one failure blocks entire module
- Safe modification: Decompose into `modules/topic/`, `modules/schema/`, `modules/rbac/`, and `modules/dr-mirror/`; compose in `environments/` layer
- Test coverage: Integration tests in `raw/repos/fsi-dsp/tests/ansible/` may not catch modular composition failures

**GitHub Actions CI validation sequence unclear:**
- Issue: PROJECT.md §Phase 3a states "four-gate validation chain" (canon compliance → fsi-dsp coverage → confluent-docs schema validation → mcp-confluent state check) but `.github/workflows/` not inspected for actual implementation
- Files: `.github/workflows/terraform-plan.yml`, `.github/workflows/terraform-apply.yml` (not read)
- Impact: Unclear which gates are implemented, which are aspirational; PRs may bypass gates; no enforcement of canon/coverage validation
- Safe modification: Map each gate to a GitHub Actions job with clear pass/fail; block merge on gate failure; document fallback for skip (break-glass)
- Test coverage: Mock MCP servers needed for gate testing in CI

**Reference implementations not e2e tested:**
- Issue: `raw/repos/fsi-dsp/reference/python-producer/fsi_producer.py` and `reference/python-consumer/fsi_consumer.py` have no visible reference tests; CI test matrix in `tests/ansible/` uses Ansible (not Python)
- Files: `reference/python-producer/`, `reference/python-consumer/` (no test coverage visible)
- Impact: Breaking changes to Confluent Kafka Python client API (e.g., prometheus_client internal API) may not be caught; reference code silently breaks for users
- Safe modification: Add `tests/reference-implementations/test-python-producer.py` and `test-python-consumer.py` that run producer/consumer against local Docker Compose stack
- Test coverage: Roundtrip test (produce message, consume, deserialize, verify schema) with both Avro schemas and DLQ routing

## Scaling Limits

**Prometheus metrics unbounded label cardinality:**
- Issue: `fsi_producer.py` labels all metrics with `topic` name (lines 51-68); in FSI production with 100+ topics, this creates 100+ time series per metric type = 600+ series for 6 metric types
- Files: `raw/repos/fsi-dsp/reference/python-producer/fsi_producer.py` (lines 51-68)
- Impact: Prometheus scrape size grows linearly; high-cardinality metrics degrade storage/query performance; Dynatrace/Datadog ingest costs scale with series count
- Scaling path: Aggregate metrics at application level (per-instance, not per-topic); expose topic as span tag in OpenTelemetry traces instead; document metric aggregation strategy

**Wiki growth unconstrained:**
- Issue: `wiki/` currently has 22 articles (per lint); no documented target size, retention policy, or archival process; `wiki/_queue.md` lists 7 more stubs
- Files: `wiki/_queue.md` (lines 14-20), no retention policy in README.md
- Impact: Wiki becomes unwieldy as Confluent canon evolves; stale articles not refreshed; search performance degrades; contributors overwhelmed by scope
- Scaling path: Implement `last_validated` decay rule (articles drop from `confidence: high` to `medium` after 90 days without revalidation); archive articles >1 year old to `wiki/archive/`; cap high-confidence articles at 150

## Dependencies at Risk

**confluent-kafka Python client on deprecated AvroProducer:**
- Issue: Comment in `fsi_producer.py` line 106 explicitly states "NOT deprecated AvroProducer" suggesting producer uses modern AvroSerializer API; but confluent-kafka versions may vary in Avro support between major releases
- Files: `raw/repos/fsi-dsp/reference/python-producer/fsi_producer.py` (line 106)
- Impact: If Confluent drops support for direct Avro schema injection (line 113-118), reference code breaks; unclear minimum version constraint
- Migration plan: Pin `confluent-kafka>=2.3.0` in `requirements.txt`; add version-gating tests; document fallback to confluent-kafka 3.x if Avro API changes

**Terraform Confluent provider API drift:**
- Issue: README cites `confluentinc/confluent` provider v2.0; no constraints in `.terraform` lock file (not inspected); Confluent Cloud API evolves quarterly
- Impact: Plan/apply may fail against new CC API versions; drift in role binding resource names, schema subject naming, topic config keys
- Migration plan: Add `required_providers` block with explicit version range (`~> 2.0`); add CI step to test against latest minor version; run `/wiki:validate` against Confluent docs on version bumps

**Python 3 version not pinned:**
- Issue: `tools/` and `reference/` scripts use `#!/usr/bin/env python3` with no explicit version; `.flox/` may pin Python but requirement not visible in repo
- Impact: Local dev (Python 3.8) may differ from CI (Python 3.12); deprecated APIs (e.g., `dict[str]` union syntax in <3.10) may break
- Fix approach: Add `python_requires=">=3.9"` to any setup.py; document in README; pin Flox manifest to Python 3.11+

## Missing Critical Features

**No admin-client operations in reference implementations:**
- Issue: `fsi_producer.py` and `fsi_consumer.py` do not provide topic/partition metadata inspection, offset reset, or consumer group management
- Impact: Developers must jump to confluent-cli or Python KafkaAdminClient separately; no unified developer experience
- Blocks: Operational debugging (consumer lag, partition assignment verification)

**DLQ handler not included in this repo:**
- Issue: `fsi_producer.py` imports `from fsi_dlq_handler import FsiDlqHandler` (line 21) but `raw/repos/fsi-dsp/reference/python-producer/fsi_dlq_handler.py` not found in read
- Files: Presumed at `raw/repos/fsi-dsp/reference/python-producer/fsi_dlq_handler.py`
- Impact: Cannot run producer reference without separately locating DLQ handler; unclear how DLQ routing is implemented

**No observability MCP server integration in phase roadmap:**
- Issue: PROJECT.md §Phase 3c mentions "Observability MCP integration (Datadog, Dynatrace, Splunk)" but defers to Phase 4; no Prometheus query builder or metric validation in current MCP stack
- Impact: Cannot validate producer/consumer metrics against thresholds; no incident correlation feedback loop; operational blind spot during DR

## Test Coverage Gaps

**Wiki article claims not systematically validated:**
- Issue: `wiki-lint.py` detects unverified claims but does not invoke MCP validation; CI workflow (`.github/workflows/wiki-lint.yml`) runs lint but no `/wiki:validate` step
- Files: `wiki/patterns/fsi-exactly-once.md` (flagged as unverified), `.github/workflows/wiki-lint.yml` (presumed, not read)
- Impact: Unverified claims propagate to customers; `/ask` skill may cite unvalidated patterns
- Priority: High — affects customer trust

**Reference implementation integration tests incomplete:**
- Issue: `tests/ansible/` contains Ansible playbook tests for Terraform/CLI; no tests for Python producer/consumer roundtrip, DLQ routing, graceful shutdown signal handling
- Files: `tests/ansible/` (not comprehensive for Python refs)
- Impact: Breaking changes to confluent-kafka Python API undetected; DLQ failures silent
- Priority: High — reference code is first-touch for developers

**Phase 0 exit threshold not testable:**
- Issue: PROJECT.md Phase 0 requires "three bugs fixed" and "wiki citations migrated to ID form" but no test harness validates ID resolution; no golden test cases for citation format
- Files: No test files for MANIFEST.yaml ID validation, wiki citation format parsing
- Impact: Phase 0 completion subjective; team cannot definitively say when exit criteria met
- Priority: Medium — blocks Phase 1 clarity but not blocking current work

---

*Concerns audit: 2026-04-28*
