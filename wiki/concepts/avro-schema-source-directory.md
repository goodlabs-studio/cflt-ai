---
title: Avro Schemas Live in src/main/avro/ — Not Resources
tags: [trip-wire, avro, maven, gradle, schema-registry, confluent-agent-skills]
sources: [raw/vendor/confluent-agent-skills/91d1871e/skills/kafka-streams-programming/SKILL.md]
related: [concepts/kafka-streams-debugging, concepts/kafka-streams-schema-patterns, concepts/kafka-streams-4x-uncaught-exception-handler-import]
confidence: high
last_updated: 2026-05-16
last_validated: 2026-05-16
source: confluent-agent-skills@91d1871ef8c320be92bca955c8e42492a2778cb4
upstream_path: skills/kafka-streams-programming/SKILL.md
---

# Avro Schemas Live in src/main/avro/ — Not Resources

## Summary

Avro `.avsc` schema files live in `src/main/avro/` — the Avro Maven plugin's (and Gradle Avro plugin's) canonical source directory. **NOT** `src/main/resources/avro/`. Putting them in `resources/` silently skips code generation — the build reports `NO-SOURCE` (or no message at all), produces zero generated Java classes, and the build succeeds. Downstream code that tries to instantiate the generated classes then fails to compile with `cannot find symbol`. Validated against context7 (Avro Maven Plugin canonical layout) and confluent-docs (Confluent Schema Registry Maven plugin) via /wiki:ingest Step 3d on 2026-05-16. This trip-wire is encoded as an upstream eval assertion at `skills/kafka-streams-programming/evals/evals.json` — it would fail an upstream merge if violated.

## Detail

Both the Apache Avro Maven plugin (`org.apache.avro:avro-maven-plugin`) and the Gradle Avro plugin (`com.github.davidmc24.gradle.plugin.avro`) default `sourceDirectory` to `src/main/avro/`. The Confluent Schema Registry Maven plugin (`io.confluent:kafka-schema-registry-maven-plugin`) registers from any path you give it but does NOT generate Java classes — it's the Avro plugin doing the codegen.

**Failure mode:** an engineer puts `.avsc` files in `src/main/resources/avro/` (intuitively reasonable — they're "resource files"), reading code that does `new MyRecord()` works in the IDE because the IDE's Avro plugin auto-detects schemas anywhere, then breaks in CI with `cannot find symbol: class MyRecord`. Worse — the IDE's incremental compile can mask this for days before a fresh clone surfaces it.

### Correct pom.xml — explicit sourceDirectory is fine but the default already works

```xml
<plugin>
  <groupId>org.apache.avro</groupId>
  <artifactId>avro-maven-plugin</artifactId>
  <version>1.12.0</version>
  <executions>
    <execution>
      <id>schemas</id>
      <phase>generate-sources</phase>
      <goals><goal>schema</goal></goals>
      <configuration>
        <sourceDirectory>${project.basedir}/src/main/avro</sourceDirectory>
      </configuration>
    </execution>
  </executions>
</plugin>
```

### Correct build.gradle (Gradle Avro plugin)

```groovy
plugins { id "com.github.davidmc24.gradle.plugin.avro" version "1.9.1" }
// sourceDirectory defaults to src/main/avro/ — don't override unless you have a reason
```

### Detection

After `mvn generate-sources` (or `gradle generateAvroJava`), check `target/generated-sources/avro/` (Maven) or `build/generated-main-avro-java/` (Gradle). If empty: the plugin found no schemas. Common cause: schemas in `resources/`.

```bash
# Quick sanity check
mvn generate-sources && ls target/generated-sources/avro/ || echo "FAIL: no generated Avro classes"
```

## Related

- Parent: `concepts/kafka-streams-debugging` — the broader catalogue including build/schema-related symptoms.
- Parent: `concepts/kafka-streams-schema-patterns` — Avro/Protobuf/JSON Schema patterns and Java type mappings.
- Sibling KS-programming trip-wire: `concepts/kafka-streams-4x-uncaught-exception-handler-import` — companion build/compile gotcha.

---

*Source: confluentinc/agent-skills@91d1871e · skills/kafka-streams-programming/SKILL.md · Ingested 2026-05-16 (full MCP-validation gate per D-07) · Apache-2.0*
