A realistic FSI shared-types library showing how subjects, versions, and schema IDs actually look in the registry.

**Example 1: `com.nfcu.common.Money`, a stable shared type**

Initial registration:

| Subject: com.nfcu.common.MoneyVersion: 1Schema ID: 1001Compatibility: FULL\_TRANSITIVE{  "type": "record",  "name": "Money",  "namespace": "com.nfcu.common",  "fields": \[    {"name": "amount", "type": {"type": "bytes", "logicalType": "decimal", "precision": 18, "scale": 4}},    {"name": "currency", "type": "string"}  \]} |
| :---- |

Six months later, someone wants to add an optional `asOfTimestamp` for FX-converted amounts. FULL\_TRANSITIVE means the field needs a default to be both backward and forward compatible:

| Subject: com.nfcu.common.MoneyVersion: 2Schema ID: 1247Compatibility: FULL\_TRANSITIVE{  "type": "record",  "name": "Money",  "namespace": "com.nfcu.common",  "fields": \[    {"name": "amount", "type": {"type": "bytes", "logicalType": "decimal", "precision": 18, "scale": 4}},    {"name": "currency", "type": "string"},    {"name": "asOfTimestamp", "type": \["null", {"type": "long", "logicalType": "timestamp-millis"}\], "default": null}  \]} |
| :---- |

Subject `com.nfcu.common.Money` now has versions 1 and 2, mapped to schema IDs 1001 and 1247\. Both remain resolvable forever.

**Example 2: `com.nfcu.common.MemberId`, a wrapped primitive**

| Subject: com.nfcu.common.MemberIdVersion: 1Schema ID: 1002Compatibility: FULL\_TRANSITIVE{  "type": "record",  "name": "MemberId",  "namespace": "com.nfcu.common",  "fields": \[    {"name": "value", "type": "string"},    {"name": "issuingBranch", "type": \["null", "string"\], "default": null}  \]} |
| :---- |

Wrapping primitives in records is a deliberate choice, it lets you evolve (add `issuingBranch` later, add validation metadata, add a check digit field) without breaking consumers, which a bare `string` wouldn't allow. The cost is verbosity; the benefit is evolvability. For shared identifiers in regulated domains, worth it.

**Example 3: `com.nfcu.common.Address`, US-specific**

| Subject: com.nfcu.common.UsAddressVersion: 1Schema ID: 1003Compatibility: FULL\_TRANSITIVE{  "type": "record",  "name": "UsAddress",  "namespace": "com.nfcu.common",  "fields": \[    {"name": "line1", "type": "string"},    {"name": "line2", "type": \["null", "string"\], "default": null},    {"name": "city", "type": "string"},    {"name": "state", "type": {      "type": "enum",      "name": "UsState",      "symbols": \["AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY","DC","PR","VI","GU","AS","MP","AA","AE","AP"\]    }},    {"name": "postalCode", "type": "string"},    {"name": "country", "type": "string", "default": "US"}  \]} |
| :---- |

Naming it `UsAddress` rather than `Address` is the right call, it signals that international addresses are a different type, not a variant of this one. The military APO/FPO codes and territories are in the enum because for NFCU specifically (Navy Federal-adjacent if I'm reading the engagement right) those will come up.

**Example 4: a domain schema that references the shared types**

| Subject: payments-valueVersion: 1Schema ID: 2891Compatibility: BACKWARD\_TRANSITIVEReferences:  \- name: com.nfcu.common.Money    subject: com.nfcu.common.Money    version: 2  \- name: com.nfcu.common.MemberId    subject: com.nfcu.common.MemberId    version: 1{  "type": "record",  "name": "WireTransfer",  "namespace": "com.nfcu.payments",  "fields": \[    {"name": "transferId", "type": "string"},    {"name": "fromMember", "type": "com.nfcu.common.MemberId"},    {"name": "toMember", "type": "com.nfcu.common.MemberId"},    {"name": "amount", "type": "com.nfcu.common.Money"},    {"name": "initiatedAt", "type": {"type": "long", "logicalType": "timestamp-millis"}},    {"name": "status", "type": {      "type": "enum",      "name": "TransferStatus",      "symbols": \["INITIATED", "PENDING", "COMPLETED", "FAILED", "REVERSED"\]    }}  \]} |
| :---- |

What you see in the registry: `payments-value` v1, schema ID 2891, with explicit references to `com.nfcu.common.Money` v2 and `com.nfcu.common.MemberId` v1. The registry stores those references and validates them at registration, if you try to register a subject referencing a non-existent subject-version, it fails.

**What this looks like across the full library:**

| Subject                              Versions   Latest ID   Compatibilitycom.nfcu.common.Money                1, 2       1247        FULL\_TRANSITIVEcom.nfcu.common.MemberId             1          1002        FULL\_TRANSITIVEcom.nfcu.common.AccountId            1          1004        FULL\_TRANSITIVEcom.nfcu.common.UsAddress            1          1003        FULL\_TRANSITIVEcom.nfcu.common.RoutingNumber        1          1005        FULL\_TRANSITIVEcom.nfcu.common.Timestamp            1          1006        FULL\_TRANSITIVEcom.nfcu.common.TransactionType      1, 2       1389        FULL\_TRANSITIVEcom.nfcu.common.AccountType          1          1008        FULL\_TRANSITIVEpayments-value                       1, 2, 3    2913        BACKWARD\_TRANSITIVEmembers-value                        1, 2       2456        BACKWARD\_TRANSITIVEaccounts-value                       1          2502        BACKWARD\_TRANSITIVEaccount-events-value                 1, 2       2887        BACKWARD\_TRANSITIVE |
| :---- |

A few things worth noting in this layout:

The shared-type schema IDs (1001-1500 range) and domain schema IDs (2000+) aren't actually segregated by the registry, IDs are assigned sequentially across all registrations. I'm showing them in clusters here for illustration, but in practice they're interleaved chronologically. If you want logical grouping for governance, that comes from the subject naming convention (`com.nfcu.common.*` prefix), not from ID ranges.

Shared types stay on low version numbers because they evolve rarely, that's the point. If your `Money` is on v8 after six months, something is wrong with your shared-types governance and you should pull back to a more conservative review process.

Domain subjects evolve faster, which is fine, they're owned by domain teams and their compatibility scope is bounded.

The reference from `payments-value` v1 to `com.nfcu.common.Money` v2 is *pinned*, if `Money` later evolves to v3, `payments-value` v1 still references v2 and resolves to v2's content. To pick up `Money` v3, you'd register `payments-value` v2 with an updated reference. This is important: shared-type evolution doesn't automatically propagate, which is actually what you want, domain teams control when they adopt new shared-type versions.

