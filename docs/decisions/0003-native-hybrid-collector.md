# Decision 0003: use a native hybrid collector

- Status: Accepted for the P2 engineering preview
- Date: 2026-07-16

## Context

dbt Core leaves versioned JSON artifacts and logs after a Databricks dbt task. dbtobsb must retrieve the exact native task archive, preserve it customer-locally, classify incomplete evidence, and publish safe SQL evidence without an external telemetry platform.

The implementation could parse everything with Databricks SQL, use arbitrary custom Python end to end, or combine native Databricks services with a small strict parser.

## Decision

Use a native hybrid design:

1. Databricks Jobs API and the pinned Python SDK correlate the parent Job, dbt task, and task-run output, then obtain the ephemeral archive link and required headers.
2. Fixed bounded Python transport consumes that archive without logging or persisting link material.
3. The exact closed bytes are written to a Unity Catalog managed Volume and verified by size and SHA-256 readback.
4. A small strict Python parser reads the tar stream without extraction, rejects unsafe archive/JSON structures, validates the complete pinned dbt schemas, and enforces cross-file invariants.
5. Typed Spark DataFrames and Delta `MERGE` publish allowlisted fields idempotently.
6. Databricks SQL views are the ordinary operator surface.

This is native-first, not Python-for-everything. Custom code exists only where the evidence contract requires strict byte-level and cross-document behavior.

## Why not SQL `read_files` as the acceptance boundary

Databricks `read_files` is useful for exploratory and typed ingestion of JSON files ([Azure function reference](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/functions/read_files)). It is not the authoritative parser here because this product must prove:

- tar member type, path, count, and expanded-size safety before file interpretation;
- rejection of duplicate tar members and duplicate primary basenames;
- rejection of duplicate JSON object keys and non-finite constants;
- complete immutable JSON Schema validation;
- exact manifest/run-results invocation equality; and
- result-node membership and status invariants across two documents.

A permissive SQL read can be an analysis tool after acceptance. It cannot silently replace those gates.

## Why not a fully custom persistence layer

Spark and Delta already provide the customer-local typed write and transaction primitives needed for this release. The sink uses fixed schemas, parameterized key reads, deterministic `MERGE`, child-count readback, and a root `PUBLISHED` sentinel. Operators consume normal SQL views. Reimplementing those capabilities would increase code and reduce Databricks-native visibility.

## Security consequence

The exact archive remains the restricted source evidence. SQL tables contain only an allowlisted projection. The ephemeral signed link and headers never enter either surface.

One Azure serverless run returned an internal HTTP Databricks-hosted link while external access returned HTTPS. The preview added a narrow SDK-derived capability to consume that internal link. This behavior is not a regulated transport qualification; it remains a documented limitation until Databricks supplies a canonical HTTPS path or authoritative contract.

## Operational consequence

Installation and collection are separate entry points:

- `BOOTSTRAP_ALLOWED` may create the fixed objects, including in production when an authorized administrator intentionally targets it; and
- `RUNTIME_DML_ONLY` writes to existing objects and cannot enable bootstrap through a runtime flag.

The current preview proves this code separation but not production identity/permission separation.

## Rejected alternatives

| Alternative | Reason |
| --- | --- |
| SQL-only permissive JSON ingestion | Cannot prove the full archive, duplicate-key, immutable-schema, and cross-file acceptance contract. |
| Parse dbt human log messages as primary evidence | Messages are less stable and can contain sensitive content; primary artifacts are the versioned contract. |
| Store only normalized rows | Loses exact-byte custody needed to investigate invalid and future-version artifacts. |
| External observability agent or SaaS | Violates the customer-local, no-extra-telemetry-platform requirement. |
| App as the first release surface | Adds billable compute and identity/UI work before the core evidence path is proven; SQL views are usable now. |
