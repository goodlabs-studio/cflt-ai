# Archival Storage for Long-Retention Topics

*Confluent Cloud on Microsoft Azure*

Keep the replay window hot in Confluent Cloud; land everything older as open-format files in Azure Data Lake Storage Gen2.

---

## The Principle

Confluent Cloud retained storage is priced for streaming throughput and fast replay, not for cold retention. On a managed cluster you pay a single *retained-storage* meter (per GB-hour) for every byte held past the local tail. Confluent operates the underlying object store and its internal replication for you; you do not provision it, and you do not pay per broker replica. 

Cross-region durability (a DR cluster fed by Cluster Linking) is a separate architectural choice you opt into, not an automatic multiplier on every topic.

The best practice is unchanged from the self-managed world: define an explicit **replay window**, the age beyond which data will never be re-consumed directly from the cluster, and keep only that window on Confluent. Everything older is sunk once to Azure (ADLS Gen2), where Azure-internal redundancy (LRS/ZRS) already provides durability at a fraction of the streaming rate.

**Cloud vs. Platform, the knob that changes** On Confluent Platform you set `local.retention.ms` to size the hot tail directly. Confluent Cloud does NOT expose `local.retention.*`, Confluent manages the local-vs-tiered split internally. On Cloud your levers are (1) total `retention.ms`/`retention.bytes` on the topic, and (2) how quickly a sink connector lands data in ADLS. Size the replay window through those, not through `local.retention.ms`.

## How retention.ms and retention.bytes Actually Behave

These are not two ways to trigger an archive. They are two independent ceilings that trigger *deletion*, and a segment becomes eligible when it crosses **either** one, whichever is hit first wins.

- **`retention.ms`**: maximum age. A closed segment is evicted this long after it rolls.  
- **`retention.bytes`**: maximum size per partition. Oldest segments are evicted once the partition exceeds it.

So **size \= infinite (`retention.bytes = -1`), time \= 7 days** means: age is the only active limit; a segment leaves 7 days after it closes; size never forces eviction. It does *not* mean storage is infinite, it means size is not the constraint. The 7-day window governs, and your bill is driven by how much data that window holds.

**In tiered storage, "eviction" is not "deletion of the record"** `retention.ms` / `retention.bytes` on Confluent Cloud govern TOTAL topic retention (local \+ tiered). When they fire, the data is genuinely gone from Confluent. That is why the compliance system-of-record must be the ADLS copy written by a sink connector, not Confluent's own tiered layer, which is Kafka-format and bound by the topic's retention setting.

## Unit Economics (1 TB Logical Basis)

The figures below are illustrative list-rate references on a Confluent **Cloud** basis: a single retained-storage meter, no automatic replication multiplier. Contrast that with a single logical copy in ADLS Gen2 (Hot). Replace the rates with your contracted numbers before quoting to a client.

| Platform | Copies billed | Illustrative $/TB/mo | Basis |
| :---- | :---- | :---- | :---- |
| Confluent Cloud retained storage | 1 (managed meter) | \~$80 – $120 | Streaming-tier retained storage |
| ADLS Gen2: Hot | 1 logical | \~$23 | Standard GPv2, block blob |
| ADLS Gen2: Cool | 1 logical | \~$13 | Lifecycle-aged |
| ADLS Gen2: Archive | 1 logical | \~$1 | Cold, retrieval latency |

The structural point survives the reframing: a terabyte sitting on Confluent Cloud costs several times what the same terabyte costs as a single ADLS object, and an order of magnitude more once it lifecycle-ages to Archive. Every terabyte moved out of the replay window stops being billed at the streaming rate and starts being billed at the object-storage rate.

**What changed from the original model** The prior version assumed a 6× multiplier (3× primary \+ 3× DR). That is a self-managed replication-factor model and does not describe Confluent Cloud billing, where retained storage is a single managed meter and DR is an opt-in second cluster. The economics here drop the automatic 6× and reframe on the Cloud meter.

## The Replay-Window Formula (Cloud)

Cost is driven by how much data the window keeps on Confluent. For a steady ingest rate:

hot\_logical\_TB \= ingest\_per\_day (TB) × replay\_window (days)

confluent\_$/mo \= hot\_logical\_TB × retained\_storage\_rate ($/TB/mo)

azure\_archive\_$/mo \= archived\_logical\_TB × adls\_rate ($/TB/mo)

If you additionally run a DR cluster via Cluster Linking, add its retained-storage line explicitly, it is a second managed cluster, so model it as a separate cost, not a blanket 2× on the primary.

### Worked windows, 1 TB/day ingest, \~$100/TB/mo illustrative

| Replay window | Hot logical | Confluent $/mo (approx) |
| :---- | :---- | :---- |
| 3 days | 3 TB | \~$300 |
| 7 days | 7 TB | \~$700 |
| 30 days | 30 TB | \~$3,000 |

The window scales the bill linearly: a 30-day hot tier costs 10× a 3-day tier. Keeping the window tight is the single highest-leverage cost decision. (Absolute figures depend entirely on your contracted retained-storage rate, the *ratio* is the durable insight, not the dollar amount.)

## Reference Architecture

1. **Hot tail (0 → replay window).** Confluent Cloud topic with tiered storage enabled by default on the cluster. Set total `retention.ms` to the compliance-independent replay window; Confluent manages the local↔tiered offload beneath it.  
2. **Cold archive (window → full retention).** A fully-managed Azure sink, Kafka Connect Azure Data Lake Storage Gen2 Sink, or Tableflow materializing the topic to Iceberg/Delta, writes Parquet/Avro to ADLS Gen2 with time-based partitioning. This is the compliance system of record.  
3. **Lifecycle tiering.** An ADLS lifecycle policy ages blobs Hot → Cool → Archive by partition date, matching access frequency to price. This is Azure-side and independent of Confluent. If Tableflow/Iceberg is chosen as the path forward, **Azure Lifecycle tiering to the Archive tier should be avoided or tightly scoped only to raw connector-landed files,** not Iceberg tables, unless we are prepared to pause all query access to those historical partitions.  
4. **Schema durability.** Register schemas in Confluent Cloud Schema Registry with FULL / FULL\_TRANSITIVE compatibility so cold data stays self-describing and replayable years later.

**Why the sink connector, not Confluent's own tiered layer** Confluent Cloud tiered storage keeps data in Kafka log format and bound by the topic's `retention.ms`: it is a replay accelerator, not an archive. To realize object-storage economics and a durable system of record, land the data as Parquet/Avro in ADLS via the sink connector or Tableflow, outside Kafka's retention accounting.

## Replaying from Cold Storage

Once data has aged past the topic's retention and survives only as ADLS files, replay is a **re-ingestion** operation, not a Kafka seek. You are reading files back out of the lake and producing them into a topic. The path depends on how you landed the data.

### Path A: Kafka Connect ADLS Gen2 Source (replay into a topic)

1. Identify the partition prefixes covering the replay window (e.g. `topic/year=2026/month=02/day=03/`). Time-based partitioning is what makes this a bounded scan rather than a full-lake read.  
2. If any objects are in the Archive access tier, rehydrate them first, set the blob tier back to Hot/Cool and wait for rehydration (minutes to hours). Archive blobs cannot be read in place.  
3. Deploy an ADLS Gen2 Source connector scoped to those prefixes, targeting a dedicated replay topic (e.g. `orders.replay`) so you never collide with live production traffic.  
4. The connector reads each Parquet/Avro object, and—because the files were written schema-aware—reconstructs records and produces them to the replay topic. Schema Registry resolves the writer schema so consumers deserialize correctly.  
5. Point your replay consumer at the replay topic. Tear the connector and topic down when the replay completes.  
6. Because the data is produced into a *new* replay topic (`orders.replay`), consumer group offsets from the original `orders` topic will not match. Consumers must be configured to read from `EARLIEST` on the new replay topic.  
7. Furthermore, if downstream applications are actively producing side-effects (like hitting external payment gateways), they must handle these replayed events idempotently since the message headers/payloads will look like brand-new production traffic to them.  
   

### Path B: Tableflow / Iceberg (query in place, selective replay)

If you landed via Tableflow, the archive is an Iceberg/Delta table. You can query the window directly with any Iceberg-aware engine (Flink, Spark, Trino, Databricks, Synapse) and re-produce only the rows you need into a topic.  Far cheaper than replaying whole partitions when you only need a slice.

### How the payload is delivered

- **Format on disk:** Parquet or Avro (whatever the sink wrote), one logical record per row, schema embedded or resolvable via Schema Registry.  
- **On replay:** the source connector reconstitutes each row into a Kafka record, key, value, and (where preserved in the sink config) original headers and timestamp, and produces it to the target topic. Consumers receive normal Kafka records and are generally unaware the data round-tripped through the lake.  
- **Timestamp caveat:** replayed records carry a new produce-time timestamp unless you configured the sink to persist the original event time and the source to restore it. If event-time ordering matters downstream, carry the original timestamp as a field and have consumers read it rather than relying on the Kafka record timestamp.  
- **Ordering caveat:** per-partition order is preserved only if the sink partitioned files consistently and the source reads them in order. Cross-partition global ordering is not guaranteed on replay. As above, offsets will have changed. Design consumers to tolerate those issues.   
- **Replay is not free** Reading archived objects incurs ADLS read/transaction charges, Archive-tier rehydration fees and latency if the data went cold, and Confluent Cloud ingress plus retained-storage cost for the re-produced traffic. Budget replay as an occasional operation, and scope it tightly with partition prefixes.

## Configuration Reference

Three knobs, three places: topic retention in Confluent Cloud, the sink connector in Confluent Cloud, and the lifecycle policy in Azure. There is no fourth knob. Confluent Cloud manages its internal local↔tiered split and does not expose `local.retention.*`. Snippets below use the `confluent` and `azurerm` Terraform providers; treat them as skeletons, not drop-in modules.

### 1\. Topic retention: the replay window (Confluent Cloud)

Age is the only eviction trigger: `retention.ms` is the window, `retention.bytes = -1` disables size-based eviction so the window never silently shrinks on high-volume days.

| resource "confluent\_kafka\_topic" "orders" {  kafka\_cluster { id \= confluent\_kafka\_cluster.main.id }  topic\_name       \= "orders"  partitions\_count \= 12  config \= {    "retention.ms"    \= 604800000   \# 7-day replay window    "retention.bytes" \= \-1          \# age is the only limit    "cleanup.policy"  \= "delete"  }} |
| :---- |

### 2\. Sink connector: continuous copy to ADLS (Confluent Cloud)

Runs from day one and lands records in ADLS as they arrive, the archive is populated in parallel with the hot tail, not at expiry. Time-based partitioning is what makes future replays a bounded prefix scan.

| resource "confluent\_connector" "adls\_sink" {  environment { id \= confluent\_environment.main.id }  kafka\_cluster { id \= confluent\_kafka\_cluster.main.id }  config\_sensitive \= {    "azure.datalake.gen2.access.key" \= var.adls\_access\_key  }  config\_nonsensitive \= {    "connector.class"                   \= "AzureDataLakeGen2Sink"    "name"                              \= "orders-adls-archive"    "topics"                            \= "orders"    "azure.datalake.gen2.account.name"  \= azurerm\_storage\_account.archive.name    "topics.dir"                        \= "topics"    "output.data.format"                \= "PARQUET"    "path.format"                       \= "'year'=YYYY/'month'=MM/'day'=dd/'hour'=HH"    "time.interval"                     \= "HOURLY"    "flush.size"                        \= "10000"    "kafka.auth.mode"                   \= "SERVICE\_ACCOUNT"    "kafka.service.account.id"          \= confluent\_service\_account.sink.id    "behavior.on.null.values"           \= "ignore"      "store.kafka.keys"                  \= "true"      "store.kafka.headers"               \= "true"       "tasks.max"                         \= "2"   }} |
| :---- |

### store.kafka.keys and store.kafka.headers aren’t *required*, but if you want to be able to fully recreate the state in a Path A replay, these settings guarantee exact payload fidelity. 

### 3\. Lifecycle policy: Hot → Cool → Archive (Azure)

Pure Azure-side aging on your storage account; Confluent has no involvement or awareness. The account is Standard GPv2 with hierarchical namespace enabled (that is what makes it ADLS Gen2). Days below are examples,  tune to your access pattern and any compliance immutability requirements.

| resource "azurerm\_storage\_account" "archive" {  name                     \= "fsikafkaarchive"  resource\_group\_name      \= azurerm\_resource\_group.main.name  location                 \= azurerm\_resource\_group.main.location  account\_tier             \= "Standard"  account\_replication\_type \= "ZRS"  account\_kind             \= "StorageV2"  is\_hns\_enabled           \= true   \# Blob \+ HNS \= ADLS Gen2}resource "azurerm\_storage\_management\_policy" "archive\_aging" {  storage\_account\_id \= azurerm\_storage\_account.archive.id  rule {    name    \= "age-kafka-archive"    enabled \= true    filters {      prefix\_match \= \["archive/topics/"\]      blob\_types   \= \["blockBlob"\]    }    actions {      base\_blob {        tier\_to\_cool\_after\_days\_since\_creation\_greater\_than    \= 30        tier\_to\_archive\_after\_days\_since\_creation\_greater\_than \= 180      }    }  }} |
| :---- |

**Provider and connector names drift** Confluent's managed connector class names, config keys, and Terraform provider schemas change across versions. Validate against the current `confluentinc/confluent` and `hashicorp/azurerm` provider docs before applying, especially the sink connector's auth and `path.format` keys.

## Recommendation

Set the replay window to the shortest interval that satisfies operational re-consumption needs, commonly 3 to 7 days for FSI streaming workloads, and sink everything older to ADLS Gen2 as Parquet/Avro with lifecycle tiering. On Confluent Cloud, enforce the window with the topic's total `retention.ms` (size infinite via `retention.bytes = -1` if age should be the only limit), and let the managed sink connector or Tableflow build the durable, queryable, cheap compliance archive alongside it.

## FAQ

### 1\. Where does the archived data live?

In your own Azure Data Lake Storage Gen2 account, a Standard general-purpose v2 storage account with hierarchical namespace enabled, inside the container and path the sink connector (or Tableflow) is configured to write to. It is *your* storage, in your subscription and region, not Confluent-managed storage. Confluent's own tiered-storage layer is separate, Kafka-format, and bound by topic retention; it is not the archive. The archive is the ADLS files you control.

### 2\. How is it named and versioned?

The sink connector controls layout. Typical ADLS Gen2 Sink output is a deterministic, partitioned key hierarchy, for example:

\<container\>/\<topics-dir\>/\<topic\>/year=2026/month=02/day=03/hour=14/\<topic\>+\<partition\>+\<startOffset\>.parquet

Files are named by topic, Kafka partition, and starting offset, under time-based partition directories. That offset-in-filename scheme is the connector's exactly-once / idempotency mechanism, re-runs land the same offsets in the same object names rather than duplicating. "Versioning" in the SCM sense does not apply; the offset+partition coordinate is the identity. If you want true object versioning, enable **blob versioning on the storage account**, that is an Azure feature, independent of Confluent. Tableflow instead maintains Iceberg/Delta table metadata, which gives you snapshot-level versioning and time-travel natively.

### 3\. Can I access, copy, or move those files?

Yes, they are ordinary blobs in your account. You can read, copy, move, tier, and delete them with any Azure tool: the portal, `az storage` / `azcopy`, Storage Explorer, ADLS SDKs, or any Iceberg/Parquet-aware analytics engine. Two cautions: (a) if the connector is still running against that path, moving or renaming files out from under it can break its offset bookkeeping, replay copies elsewhere rather than relocating live archive; and (b) files in the Archive access tier must be rehydrated to Hot/Cool before their contents can be read or copied. Governance (RBAC, ACLs, private endpoints, immutability/WORM policies for compliance holds) is entirely yours to set on the storage account.

---

*Illustrative list rates only; Confluent Cloud retained-storage and Azure tier rates vary by region and contract. Replace with contracted figures before client use. Reframed from the original self-managed model to Confluent Cloud on Azure.*  
