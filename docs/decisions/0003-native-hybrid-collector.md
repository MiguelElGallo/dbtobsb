# Decision 0003: use a Databricks-native staged collector

- Status: Accepted for the v0.3 supported release
- Date: 2026-07-16

## Context

dbt Core leaves versioned JSON artifacts and logs after each invocation. Azure Databricks documentation describes automatic artifact archiving for native dbt tasks, but live qualification did not return `dbt_output.artifacts_link` consistently enough to make that response a supported regulated-industry transport. dbtobsb must therefore place the exact supported files at a deterministic customer-local location, preserve a closed archive, classify incomplete evidence, and publish safe SQL evidence without an external telemetry platform.

The implementation could parse everything with Databricks SQL, use arbitrary custom Python end to end, or combine native Databricks services with a small strict parser.

## Decision

Use a native hybrid design:

1. The sealed `run-dbt` Python wheel task receives only product-generated arguments, runs the pinned dbt command without a shell, and writes artifacts and structured logs to attempt-local temporary directories.
2. The runner uploads only the allowlisted `manifest.json`, `run_results.json`, and bounded structured logs to the managed `dbtobsb_stage` Unity Catalog Volume through the Databricks Files API. Every upload uses no-overwrite semantics and exact-byte readback.
3. The Jobs API and pinned Python SDK attest and correlate the parent Job, runner task, task attempt, run-as identity, environment, and deterministic six-axis AttemptKey.
4. The collector reads only the fixed staged members, enforces metadata and byte limits, and builds a deterministic gzip USTAR archive in memory.
5. The exact closed archive is written to a separate restricted managed Volume and verified by size and SHA-256 readback.
6. A small strict Python parser reads the tar stream without extraction, rejects unsafe archive/JSON structures, validates the complete pinned dbt schemas, and enforces cross-file invariants.
7. Typed Spark DataFrames and Delta `MERGE` publish allowlisted fields idempotently. Databricks SQL views are the ordinary operator surface.

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

The exact archive remains the restricted source evidence. SQL tables contain only an allowlisted projection. The supported path does not depend on signed artifact links, undocumented headers, DBFS mounts, or FUSE behavior. It uses only Databricks Jobs, serverless Python, Unity Catalog Volumes, the Files API, Spark/Delta, and Databricks SQL inside the selected workspace.

## Operational consequence

Installation and collection are separate entry points:

- `BOOTSTRAP_ALLOWED` may create the fixed objects, including in production when an authorized administrator intentionally targets it; and
- `RUNTIME_DML_ONLY` writes to existing objects and cannot enable bootstrap through a runtime flag.

The release qualification runs the observed task and collector as separate service principals and gives each only its declared Job and Volume/table privileges. Workspace administrators and the customer-selected object owner remain disclosed trust roots.

## Rejected alternatives

| Alternative | Reason |
| --- | --- |
| SQL-only permissive JSON ingestion | Cannot prove the full archive, duplicate-key, immutable-schema, and cross-file acceptance contract. |
| Parse dbt human log messages as primary evidence | Messages are less stable and can contain sensitive content; primary artifacts are the versioned contract. |
| Store only normalized rows | Loses exact-byte custody needed to investigate invalid and future-version artifacts. |
| External observability agent or SaaS | Violates the customer-local, no-extra-telemetry-platform requirement. |
| App as the first release surface | Adds billable compute and identity/UI work before the core evidence path is proven; SQL views are usable now. |
