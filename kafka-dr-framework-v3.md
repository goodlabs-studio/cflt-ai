**GoodLabs Studio  |  FSI C4E**

April 2026  |  CONFIDENTIAL

**Kafka DR: Application Routing Decision Framework**

*Two Paths from Risk to Resilience — with a Shared Destination*

# **1\. Executive Summary**

Kafka-connected applications in the FSI platform today depend on a manual process to cut over to the secondary cluster during a DR event. A human operator updates the active cluster URL in service discovery, then coordinates application restarts across teams. This is operationally fragile, inconsistent with SLA commitments for critical and compliance-tier topics, and unnecessary given the automation already available in the fsi-dsp platform.

This document evaluates two options for closing that gap. Both share a single prerequisite — externalizing the bootstrap URL from the application binary — and converge on the same long-term destination: Confluent's One-Click DR.

| Option | Name | Summary |
| ----- | :---- | :---- |
| **A** | **ORKA (GoodLabs)** | Deploy the ORKA proxy between applications and brokers. ORKA acts as a hub to backend clusters, exposing a single endpoint and port. It creates virtual topics that keep the same names client-side and maps them by rule to the correct topics and clusters. DR failover becomes a control-plane operation: ORKA manages replication between clusters, pauses consumers at the fetch level, synchronizes both sides to a safe offset cut point, switches cluster routing, and resumes normal operation. Producers are routed transparently. No proxy restart. No application restart. No message loss. No duplicates. |
| **B** | **Confluent One-Click DR** | Apps connect to a single stable Cloud Gateway URL that never changes. The Gateway owns cluster routing transparently. A single “Failover” action in the Confluent Cloud Console triggers promotion of mirror topics, traffic redirection, authentication hand-off, and (on recovery) reverse replication. Eliminates the client restart problem by design. Maturing through 2025–2026; not expected to be real before Q1 2027 at the earliest. |

| KEY POINT | ORKA is the sensible near-term bet. One-Click DR is the correct destination — but on current Confluent guidance it is not expected to be real before Q1 2027, and program experience with major Confluent roadmap items suggests planning for later rather than earlier. The critical-tier SLA cannot be held hostage to a vendor roadmap. ORKA solves the immediate problem in weeks, preserves Kafka guarantees through the switchover, and — most importantly — builds the exact operational pattern One-Click DR productizes: a stable client endpoint fronting a control-plane-driven routing layer. When One-Click DR reaches GA, the migration is a swap of one endpoint in one place. |
| :---: | :---- |

# **2\. Problem Definition**

## **2.1  Current State**

The FSI platform currently uses Consul KV (key: fsi/kafka/active-region) as the single source of truth for which Kafka cluster is active. The fsi-dr.sh CLI automates the infrastructure-layer failover: it pauses connectors, promotes mirror topics, flips Consul to the DR region, verifies DNS propagation, resumes connectors, and validates post-failover state. This is well-engineered, tested (103 unit tests across three backends), and covers Cluster Linking, MirrorMaker 2, and Multi-Region Cluster deployment models.

What it does not cover is the application layer. After Consul flips to the secondary cluster, Kafka-connected applications — producers, consumers, and Kafka Streams apps — are still holding open connections to the primary. They do not automatically discover that the active region has changed. The current remediation is a manual rolling restart coordinated by the platform team across application teams. This is the gap this proposal addresses.

## **2.2  Service Discovery — the Philosophy, Not a Component**

Service discovery is the principle behind every solution in this document. Clients should not hardcode bootstrap servers. They should resolve endpoints through a layer that can be reconfigured during failover without touching the client. In Kafka DR, that layer can take several forms:

* **DNS abstraction** — CNAME flips, weighted routing, or a dedicated resolver. Cheap but coarse; TTLs create tail latency on cutover and it does nothing to preserve consumer offsets or Kafka guarantees during the flip.

* **A proxy or service mesh** — Envoy, Istio, or in the Kafka-protocol-aware case, ORKA. Terminates client traffic and redirects it at the control plane without restart.

* **A productized control plane** — Confluent Cloud Gateway, which is the service-discovery-equivalent layer for One-Click DR. Same philosophy, productized and owned by the vendor.

Both options in this document are service-discovery layers for Kafka. ORKA is the near-term instantiation; One-Click DR is the long-term destination. They differ in who runs the control plane, not in what the control plane does.

| NOT CONSIDERED | ConfigMap \+ rolling-restart patterns. Earlier drafts considered propagating a new bootstrap URL by mutating a Kubernetes ConfigMap and triggering rolling restarts. That pattern is intentionally excluded here: it solves the symptom (stale client config) at the wrong layer. It leaves restart cost on the application every time the platform moves, cannot preserve Kafka delivery guarantees across the switch, and does not build toward One-Click DR — it competes with it. Service discovery belongs in a routing layer, not in a deployment controller. |
| :---: | :---- |

## **2.3  Scope Boundary**

This proposal addresses a single, precisely bounded problem: how do Kafka-connected applications cut over to the secondary cluster during a DR event — safely, automatically, and with minimum disruption? Both options are evaluated against this problem only.

| SCOPE NOTE | ORKA's primary demonstration vehicle is stateful blue/green deployment switching between application versions. That is a real and separate problem this platform will encounter. ORKA solves it as a bonus — but is evaluated here strictly on DR routing merit. The blue/green capability is noted in the option description as additive value, not as the reason for inclusion. |
| :---: | :---- |

## **2.4  SLA Tier Obligations**

The fsi-dsp platform defines four SLA tiers with explicit RPO and RTO commitments. The application-layer restart gap directly threatens the RTO targets for critical and compliance topics.

| SLA Tier | RPO Target | RTO Target | Mirror Lag Thresholds | Priority |
| :---- | :---- | :---- | :---- | :---- |
| **critical** | \< 5 min | \< 15 min | 30s warn / 60s alert | P1 — Immediate |
| **compliance** | \= 0\* | \< 15 min | 10s warn / 30s alert | P1 — Immediate |
| **standard** | \< 2 hr | \< 1 hr | 5 min warn / 15 min alert | P2 — Business hours |
| **best-effort** | \< 24 hr | \< 4 hr | 1 hr warn / 4 hr alert | P3 — Next business day |

\*when using MRC 2.5 pattern

A manual restart process that takes 15–30 minutes to coordinate across teams is incompatible with a 15-minute RTO target for critical and compliance-tier topics. Automation is not optional for these tiers.

## **2.5  What Done Looks Like**

A successful solution achieves all of the following:

* **Automated** — no human coordination required to redirect application traffic after fsi-dr.sh failover completes.

* **Safe** — no duplicate messages, no missed messages, no out-of-order processing during or after the switch.

* **Auditable** — the switchover event is logged, observable via existing dashboards (Datadog, Grafana, Dynatrace), and traceable post-incident.

* **One-Click-DR-compatible** — the automation built today requires a single endpoint swap when Confluent One-Click DR reaches GA. No client-side rework.

# **3\. The Oracle Co-Dependency — The Real RTO Constraint**

| RISK | This section documents a co-dependency that no Kafka-layer solution can resolve. Both options in this proposal can make the Kafka routing switchover happen in seconds. ORBH failover for the Oracle side, and the OIC REST data path that bridges Oracle to Kafka, operate on fundamentally different timescales. If this is not addressed independently, the platform will experience RTO misses on the Oracle boundary regardless of how fast the Kafka layer switches. |
| :---: | :---- |

## **3.1  Why This Matters More Than Kafka Routing**

Every FSI workflow that writes to both Kafka and Oracle — trade capture, payment processing, account state updates — has a two-sided commit problem. The Kafka side and the Oracle side must both be available and consistent for the application to resume correctly after failover. This proposal optimizes the Kafka side. Oracle is the other side.

The customer's Oracle-to-Kafka data path runs through Oracle Integration Cloud (OIC) REST adapters; the Oracle DR construct itself is ORBH. The fsi-dr.sh runbook makes the timing of this explicit: Step 3 flips the Consul KV key fsi/kafka/active-region, which atomically redirects Kafka bootstrap, Schema Registry, and Oracle-facing OIC REST endpoints to the DR region simultaneously. This is architecturally correct. The problem is that ORBH is not ready to serve traffic at the same moment the Consul key flips, and the OIC REST data path is not drained. Oracle-side failover is a separate, slower process that the Consul flip does not control.

## **3.2  ORBH Failover: The Honest Timeline**

ORBH failover time depends heavily on configuration, standby state, and whether the event is planned or unplanned. The categories below are the ones worth planning around; the numbers are placeholders until ORBH is drilled end-to-end under realistic load. These values are a hypothesis, not a commitment.

| Configuration / Scenario | Failover Time | Reality Check |
| :---- | :---- | :---- |
| **Planned ORBH failover, perfectly tuned, standby fully caught up** | 30–90 sec | Requires operator playbook rehearsed and validated, no redo-apply gap, OIC REST adapters flushed before cutover. Few environments are actually in this state without deliberate investment. |
| **ORBH with operator intervention, standby healthy** | 5–15 min | Most common real-world configuration. Requires a DBA to assess lag, decide to fail over, execute the switchover, and verify the standby is open read-write. OIC REST flows must be quiesced and re-pointed. |
| **ORBH under load with redo-apply gap** | 15–45 min | If the standby has fallen behind, it must apply outstanding redo before opening. Under heavy write workloads this gap can be substantial. |
| **Oracle RAC → standby RAC (additive)** | \+5–10 min | All RAC instances on the primary must be stopped before the standby can open. Instance eviction is not always clean. |
| **Failback to primary — any configuration** | 30–90+ min | Standby must be re-synced from the new primary before roles can reverse. Instant failback is not supported. This number is most often omitted from RTO commitments. |

## **3.3  Three Failure Modes Nobody Tests**

### **Connection Pool and OIC REST Adapter Stale Connections**

Application connection pools (HikariCP, Oracle UCP, c3p0) and OIC REST adapter client pools do not gracefully handle an Oracle primary disappearing mid-session. Pools hold open connections or session tokens pointed at the old primary. Those sessions return ORA-03113 / ORA-03114 on next use, or HTTP 5xx from the OIC layer. Eviction may not happen until a validation probe fires, which may not fire immediately. The result is a window — often minutes — where the application believes it has a working data path but every attempt to use it throws an error. Mitigation: configure testOnBorrow or keep-alive validation, set connectionTimeout aggressively, configure OIC REST retry with circuit breakers bounded to the RTO window, and ensure the pool is sized to drain and re-establish within that window.

### **In-Flight Transaction and In-Flight OIC Message Loss**

Any Oracle transaction not committed at the moment the primary failed is lost. This is correct database behavior. OIC REST flows in mid-poll at failover time are similarly lost unless the source side replays. This creates an asymmetry with the Kafka layer: ORKA can synchronize both sides to the same offset cut point, guaranteeing no Kafka message is lost or duplicated. If the corresponding Oracle write (or the OIC REST pull that fed Kafka) was in flight at failover time, that Kafka event may be reprocessed on the secondary cluster against a database with no record of the first attempt — or the message may simply be missing from Kafka entirely. Mitigation: MERGE instead of INSERT on the Oracle side, application-layer UUIDs instead of Oracle sequences as deduplication keys, exactly-once Kafka semantics where the framework supports it, and idempotent OIC REST flow design with replay on resume.

### **Sequence Cache Gaps**

Oracle sequences are cached in the SGA of each instance. On failover, the standby opens with sequence values that reflect the last persisted state, not the last cached state on the primary. Depending on cache size, the standby may generate values that overlap with values already committed before failover. In redo-apply configurations the gap is typically small. In older physical standby configurations it can be significant. Mitigation: set NOCACHE on sequences used as deduplication keys, or use application-layer UUID generation for DR-sensitive entities. Audit sequence cache sizes before the first drill.

## **3.4  The Consul Timing Problem**

fsi-dr.sh Step 3 flips fsi/kafka/active-region atomically, redirecting Kafka, Schema Registry, and OIC REST endpoints in a single Consul KV write. During failover, Kafka and the Oracle/OIC path do not become available at the same moment. The table below shows what applications experience in the gap.

| T+ | Event | Application Experience |
| :---- | :---- | :---- |
| **0s** | Consul KV flips to west | Apps resolve west Kafka AND west Oracle / OIC. West Kafka is ready. West Oracle is not yet primary; OIC REST endpoints on the DR side may not be warm. |
| **0–60s** | Kafka routing switches (ORKA) | Kafka writes succeed. Any Oracle write hits standby in read-only mode — ORA-16000 errors. OIC REST returns 5xx or empty. |
| **1–15 min** | Operator executes ORBH failover | West Oracle opens read-write; OIC REST adapters warm on the DR side. But the ORA-16000 / OIC-failure window has already produced failed transactions, retry queues, and potentially inconsistent state. |
| **Failback** | Consul flips back to east | East Oracle must re-sync before serving as primary — 30–90 min. Kafka failback completes in seconds. Apps wait on Oracle. |

## **3.5  The Real RTO Math**

Honest end-to-end failover timeline for a critical-tier workflow writing to both Kafka and Oracle, with ORKA handling Kafka routing and ORBH handling the Oracle side:

| Activity | Duration | Owner |
| :---- | :---- | :---- |
| Detect primary failure and confirm (not transient) | 2–5 min | On-call / monitoring |
| fsi-dr.sh failover: Steps 1–6 | 3–6 min | Automated (fsi-dsp) |
| Kafka routing switch (ORKA) | Seconds | Automated (this proposal) |
| ORBH planned failover — best case, tuned | 1–2 min | Oracle / DBA |
| ORBH operator-driven failover — typical | 5–15 min | DBA on-call |
| OIC REST adapter re-point and warm-up | 1–3 min | Integration team |
| Connection pool drain and re-establish | 1–3 min | Application / ops |
| End-to-end write path verification | 2–5 min | On-call |
| **TOTAL — best case (tuned ORBH \+ ORKA)** | **\~10–15 min** | **Borderline for critical SLA** |
| **TOTAL — typical (operator ORBH \+ ORKA)** | **\~20–35 min** | **Exceeds critical SLA target** |

## **3.6  Oracle & OIC Discovery Questions**

These must be answered before any RTO commitment is made to the business:

* Is ORBH configured for automated failover with a monitoring/observer process, or is every event operator-driven? When was ORBH last drilled end-to-end, including failback?

* What is the measured redo-apply lag at peak write load? This is the Oracle-side RPO floor. It cannot be configured away.

* Is this Oracle RAC → standby RAC? If yes, add 5–10 minutes for instance eviction to every failover estimate.

* Who executes ORBH failover? Is there a DBA on-call with a rehearsed runbook, or is this an escalation chain? What is the realistic time-to-DBA for a 2am event?

* What is the measured OIC REST adapter lag at peak? How do OIC flows behave when the source Oracle disappears mid-poll — retry, fail open, fail closed? What is the replay story on resume?

* Have you timed a full failover and failback, including OIC adapter re-point, connection pool recovery, application verification, and standby re-sync? If not, the RTO is a hypothesis.

* What Oracle sequence cache sizes are configured on high-write tables? Has post-failover sequence gap risk been analyzed?

## **3.7  Mitigation Options**

### **Near-Term: Decouple the Consul Flip**

Split fsi/kafka/active-region into two keys — one for Kafka and Schema Registry, one for the Oracle/OIC REST path. Flip Kafka immediately when the secondary cluster is ready. Flip the Oracle/OIC key only after the operator confirms ORBH is open read-write and OIC adapters are warm. This eliminates the window where applications attempt Oracle writes against a read-only standby or hit cold OIC endpoints.

### **Near-Term: ORBH / OIC Readiness Gate in fsi-dr.sh**

Add a readiness-check post-hook to fsi-dr.sh Step 3: before declaring the flip complete, poll the west Oracle endpoint with SELECT 1 FROM DUAL and the west OIC REST health endpoint. Do not proceed until both respond. This costs seconds in the happy path and prevents the ORA-16000 retry storm in the unhappy path.

### **Medium-Term: Invest in ORBH Drill Cadence and Measured Metrics**

If the 15-minute RTO target is non-negotiable for critical and compliance topics, ORBH must be drilled on a regular cadence with measured numbers — not target numbers. That includes failback. It is a meaningful investment, but it is the correct investment if the SLA commitment is real.

### **Medium-Term: Idempotent Write Patterns**

Ensure all Oracle writes triggered by Kafka consumption (and all OIC REST flows) use MERGE semantics, application-generated UUIDs as deduplication keys, and exactly-once Kafka semantics where the framework supports it. This does not reduce RTO but eliminates data integrity risk from in-flight transaction loss at failover time.

| BOTTOM LINE | This proposal makes the Kafka side of DR fast, automated, and guarantee-preserving. ORBH and the OIC REST data path determine your actual RTO. If ORBH failover has not been timed end-to-end under realistic conditions — including failback — that test must happen before any SLA commitment is made to the business. The Kafka optimizations in this proposal are necessary. They are not sufficient. |
| :---: | :---- |

# **4\. Evaluation Criteria**

Options are scored against the following criteria. Weights reflect FSI production priorities.

| Criterion | Weight | Rationale |
| :---- | ----- | :---- |
| **RTO reduction** | **High** | SLA commitments for critical / compliance topics leave no room for manual coordination. |
| **Kafka guarantee preservation** | **High** | Duplicate or missed messages during failover create downstream reconciliation cost and regulatory exposure. |
| **App restart requirement** | **High** | Restart introduces risk and coordination overhead; elimination is strongly preferred. |
| **Time to implement** | **High** | The gap between fsi-dr.sh automation and app-layer automation must close before the next DR event. |
| **Operational complexity added** | **Medium** | Additional components in the data path must justify their operational overhead. |
| **One-Click DR migration friction** | **High** | Investment made today should not be discarded when One-Click DR reaches GA. |
| **Cost** | **Medium** | Evaluated relative to operational risk reduction, not in isolation. |

# **5\. Option A — ORKA (GoodLabs)**

*“The Near-Term Path That Paves the Way”*

## **5.1  How It Works**

ORKA is a proxy plus controller system that sits between Kafka client applications and Kafka brokers. Applications connect to ORKA, not directly to a cluster. ORKA owns the routing decision — which cluster traffic flows to — and can change that decision at the control-plane level without any application action.

The core mechanism exploits Kafka's normal fetch behavior. When a pause is requested, ORKA returns empty fetch responses to the consumer group — a state indistinguishable from a quiet topic. Consumers continue polling without error. At that moment, ORKA switches cluster routing and resumes fetch responses. The operation is deterministic, bounded, and preserves Kafka ordering and delivery guarantees.

## **5.2  DR Failover Flow**

1. ORKA controller alarms that the primary is down.

2. Failover is triggered — manual click, API call, or automated rule on the ORKA controller.

3. On failover: the ORKA controller synchronizes replicated topics, changes the rule on the proxy to target the secondary cluster, and stops replication.

4. ORKA switches routing to the secondary cluster and resumes fetch responses.

5. No application restart at any point.

## **5.3  Strengths**

* **No application restart** — the switchover is invisible to app code. Consumers experience a brief quiet period, then rebalancing and normal message flow resume.

* **Kafka guarantees preserved throughout** — no duplicates, no missed messages, no out-of-order processing.

* **RTO measured in seconds** — the pause-sync-switch window is on the order of seconds for typical consumer lag profiles.

* **Deployment-model agnostic** — ORKA is a proxy, not a Kubernetes operator. It works for apps on VMs, bare metal, cloud, or Kubernetes equally.

* **Bonus capability** — Smart Switching Sets enable stateful blue/green deployment switching. The same pause-sync-switch mechanism applied to application version transitions, keeping Kafka Streams state stores warm across deployments.

* **Paves the way for One-Click DR** — ORKA establishes exactly the abstraction One-Click DR assumes on arrival: a stable client endpoint fronting a control-plane-driven routing layer. Migration at GA is an endpoint swap, not a re-architecture.

## **5.4  Risks and Constraints**

* **Proxy in the data path** — ORKA becomes a component in every Kafka client connection. Operational maturity and HA configuration for ORKA itself are required.

* **Proxy performance overhead** — latency and throughput should be validated against FSI production workloads before GA deployment.

* **Vendor dependency** — ORKA is a GoodLabs product. Support, roadmap, and SLA terms must be evaluated as part of procurement.

* **Scale validation required** — the demo environment used 16 partitions; production FSI workloads may have hundreds. Cap offset calculation and synchronization behavior at scale should be verified.

## **5.5  One-Click DR Migration Path**

| ONE-CLICK DR DAY | When Confluent One-Click DR reaches GA, ORKA retires. The migration is mechanical: replace the ORKA endpoint in the application config with the Confluent Cloud Gateway URL. The topology does not change — a stable client-side endpoint still fronts a control-plane-driven routing layer. Ownership of that control plane moves from GoodLabs to Confluent. The automation, the runbook, the app config pattern — all unchanged. |
| :---: | :---- |

# **6\. Option B — Confluent One-Click DR**

*“The Destination”*

## **6.1  What It Is**

In the Confluent ecosystem, One-Click DR is the productized automation of disaster-recovery failover and failback for Kafka workloads, primarily built on top of Cluster Linking.

Cluster Linking has long handled the underlying data replication and offset preservation. The “one-click” initiative — maturing through 2025 and 2026 — aims to eliminate the manual human-in-the-loop operations historically required to complete a failover.

## **6.2  Core Components**

The solution relies on three main technical pillars:

* **Cluster Linking** — handles the byte-for-byte replication of topics, ACLs, and consumer offsets between an active and a passive cluster (often across regions or clouds).

* **Confluent Cloud Gateway** — a newer traffic control layer that acts as a proxy or entry point. It automatically redirects Kafka client traffic from the failed primary cluster to the DR cluster without requiring client-side configuration changes or restarts.

* **Unified UI / API** — a single “Failover” button in the Confluent Cloud Console that triggers the complex sequence of promote/failover actions.

## **6.3  What It Automates**

Traditionally, Kafka failover required manual intervention to promote mirror topics to read/write mode and update client bootstrap servers. One-Click DR automates this sequence:

6. **Promotion** — transitions mirror topics on the DR cluster into standard topics.

7. **Traffic Redirection** — updates the Gateway to point all existing client connections to the new active cluster.

8. **Authentication Hand-off** — using OAuth2 and Identity Pools, maintains the security context so clients do not need new API keys for the DR site.

9. **Reverse Replication** — once the primary site is healthy, a one-click failback reverses the Cluster Linking direction to sync any data produced to the DR cluster back to the original primary.

## **6.4  Planned vs. Unplanned Failover**

The feature distinguishes between two modes:

* **Planned** — gracefully closes connections and ensures zero data loss (RPO = 0) before switching.

* **Unplanned** — triggers immediately during a regional outage, promoting the DR cluster based on the last successfully replicated offset.

This is Confluent moving DR from a “reference architecture” (where you build the automation yourself) to a “first-class feature” where the control plane manages the state machine of the failover for you.

## **6.5  Strengths**

* **Zero operational burden on the application layer** — app teams have no DR runbook step.

* **Vendor-owned auth model** — OAuth2 \+ Identity Pools are handled at the Gateway layer; apps do not need to manage cluster-specific credentials.

* **Eliminates the class of problem** — cluster upgrades, migrations, and DR events all become invisible to applications.

* **Symmetric planned/unplanned semantics** — planned failover enforces RPO = 0; unplanned uses last-replicated offset. The choice is explicit, not emergent.

## **6.6  Why It Is Not the Starting Point**

One-Click DR is on the Confluent roadmap but has not reached GA. Per current Confluent guidance, the components are maturing through 2025 and 2026, and the productized feature is not expected to be real before Q1 2027 at the earliest. Program experience with major Confluent roadmap items suggests planning for later rather than earlier.

Committing to One-Click DR as the starting solution creates program risk — the critical-tier SLA cannot be held hostage to a vendor roadmap. ORKA is the sensible near-term bet. It solves the immediate problem in weeks, preserves Kafka guarantees through every switchover, and builds the exact operational pattern that One-Click DR productizes. When One-Click DR arrives, the migration is an endpoint swap.

# **7\. Decision Matrix**

| Criterion | ORKA (GoodLabs) | Confluent One-Click DR |
| :---- | :---- | :---- |
| **Mechanism** | Proxy-layer control-plane switch | Stable Gateway URL \+ Cluster Linking state machine |
| **App restart required** | No | No |
| **Kafka guarantees** | Preserved (pause / sync / switch) | Preserved (planned \= RPO 0; unplanned \= last-replicated offset) |
| **RTO estimate** | Seconds | Near-zero on the Kafka routing layer |
| **Blue/green deploy safety** | Yes (bonus capability) | No |
| **Available today** | Yes | No — not expected before Q1 2027 at earliest |
| **Proxy in data path** | Yes (ORKA) | Yes (Confluent Cloud Gateway) |
| **Auth handling** | Passed through | OAuth2 \+ Identity Pools at Gateway |
| **fsi-dsp integration** | ORKA API call from fsi-dr.sh hook | Confluent Cloud API / Console action |
| **One-Click DR migration path** | Endpoint swap at GA | N/A — this is One-Click DR |

*Note. The ORKA column is highlighted because it is the only option that meets all three primary criteria — no app restart, preserved Kafka guarantees, and availability today — and migrates cleanly to One-Click DR at GA.*

# **8\. Recommendation Logic**

No single option is universally correct. That said, the current program constraints point to a single answer:

* A firm 15-minute critical-tier RTO that will not hold under a manual restart process.

* No realistic One-Click DR GA before Q1 2027, with program-experience adjustment toward later.

* An Oracle / OIC REST co-dependency that independently threatens RTO and must be addressed on its own track.

| RECOMMENDATION | ORKA now, One-Click DR at GA. ORKA closes the restart gap immediately, preserves Kafka guarantees through every switchover, and establishes the stable-endpoint \+ control-plane pattern One-Click DR productizes. The endpoint swap at GA day is mechanical. |
| :---: | :---- |

## **8.1  The Common Denominator**

Regardless of which option is selected, the first two weeks of work are identical:

* Externalize all Kafka bootstrap URLs from application binaries into ConfigMaps, Consul KV, or a secrets manager.

* Standardize the key name across all applications (KAFKA\_BOOTSTRAP\_SERVERS or equivalent).

* Audit applications not running in Kubernetes and create a separate track for those.

This work is not throwaway. It is the prerequisite One-Click DR assumes you have already done, and it is the foundation ORKA is built on.

## **8.2  The Message to the Client**

| FRAMING | “We will build this so the only work you do when Confluent One-Click DR goes GA is change one endpoint in one place. In the interim, ORKA closes the restart gap, preserves Kafka guarantees through every switchover, and establishes the exact operational pattern One-Click DR productizes. You are not betting against the roadmap — you are building toward it.” |
| :---: | :---- |

# **9\. Implementation Roadmap**

| Phase | Applies To | Activities | Milestone |
| :---- | :---- | :---- | :---- |
| **Wk 1–2** | Both paths | Externalize all bootstrap URLs into ConfigMaps or a KV store. Standardize key name (KAFKA\_BOOTSTRAP\_SERVERS). Audit apps not in Kubernetes. | **Foundation** |
| **Wk 2–4** | ORKA | Deploy ORKA proxy \+ controller. Configure switching sets. Validate pause / sync / switch against secondary cluster. Run first DR drill. | **ORKA live** |
| **Wk 4–5** | ORKA | Validate Kafka guarantees during switchover. Confirm fsi-dr.sh integration (fsi-dr.sh failover triggers ORKA switch via hook). | **DR validation** |
| **Wk 5–6** | Oracle / OIC | Drill ORBH failover \+ failback end-to-end with measured numbers. Decouple Consul KV, add ORBH / OIC readiness gate to fsi-dr.sh. | **Oracle track validated** |
| **One-Click DR GA** | Both paths | Swap ORKA endpoint to Confluent Cloud Gateway URL. All downstream automation unchanged. | **One-Click DR migration** |

## **9.1  Integration with fsi-dr.sh**

ORKA integrates with fsi-dr.sh via a post-hook after Step 3 (Consul flip). After consul kv put fsi/kafka/active-region west, the hook calls:

curl \-X POST http://orka-controller/api/switch \--data '{"target":"$DR\_BOOTSTRAP"}'

ORKA executes the pause-sync-switch sequence. Applications experience a brief message-quiet window, then resume on the secondary cluster.

A parallel hook on the Oracle track — pending the decoupling described in §3.7 — calls the ORBH / OIC readiness gate before declaring the flip complete.

# **10\. Architecture Diagram — ORKA in the fsi-dsp Platform**

| TODO | Per review comment (V. Conor, 16 Apr 2026): insert ORKA placement diagram showing application tier → ORKA proxy → primary / DR Confluent clusters, with fsi-dr.sh control-plane and ORBH / OIC REST side-channel. Diagram to be finalized against the deidentified fsi-dsp reference topology before client distribution. |
| :---: | :---- |

# **Appendix A — Discovery Questions**

### **Infrastructure & Orchestration**

* Are your Kafka consumers and producers running in Kubernetes, VMs, or bare metal?

* Do you use a secrets or config-management tool today — Vault, AWS Parameter Store, Consul, Spring Cloud Config?

* Is there a standard ConfigMap or environment-variable pattern the platform team has already established?

### **App Ownership & Modifiability**

* Which of these apps do you own the source code for, and which are COTS or third-party?

* Can your teams make a Kafka client config change and redeploy within your normal release cycle?

* Are any of these apps stateful Kafka Streams or Flink applications with local RocksDB state stores?

### **Tolerance for Restart & State**

* What is your acceptable RTO for Kafka-connected apps during a DR event?

* Do any of these apps have long-lived consumers with uncommitted offsets you would be worried about losing?

* Are there stateful deploys (blue/green) where ORKA's Smart Switching Sets would be additionally valuable?

### **Authentication Model**

* Are your apps using mTLS, SASL/SCRAM, OAuth2, or API keys to authenticate to Kafka today?

* Is the same auth mechanism used across all services, or does it vary?

### **Oracle & OIC REST**

* Is ORBH configured for automated or operator-driven failover? When was it last drilled end-to-end, including failback?

* How do OIC REST adapters handle a primary Oracle disappearing mid-poll? Retry behavior? Message loss semantics? Replay story?

* What is the measured OIC REST lag at peak write load?

* What Oracle sequence cache sizes are configured on high-write tables, and has post-failover gap risk been analyzed?