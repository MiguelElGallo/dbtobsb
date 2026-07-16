# Security and permissions

The private `v0.3.0` candidate keeps evidence customer-local and is designed for regulated deployment constraints. Its first supported route still uses one combined administrator; it does not claim independent separation of duties.

## Trust boundary

Evidence remains inside the customer's Azure Databricks workspace:

- exact archives are stored in a managed Unity Catalog Volume;
- normalized evidence is stored in managed Delta tables;
- operators query curated SQL views; and
- no external telemetry service receives dbt content.

Customer-local does not mean non-sensitive. Raw dbt artifacts can contain Personal Data, secrets, SQL, messages, relation names, paths, environment-derived values, logs, and workspace topology.

## Two separate authority paths

| Entry point | Intended authority | Allowed behavior |
| --- | --- | --- |
| `BOOTSTRAP_ALLOWED` | Authorized, attended installer | Create missing fixed schema, tables, views, and managed Volume; verify the versioned object manifest. It may intentionally target production. |
| `RUNTIME_DML_ONLY` | Ordinary collector | Preserve an archive in the existing Volume and perform fixed Delta DML against existing evidence tables. It has no runtime switch into bootstrap. |

The first row corrects an important misconception: creating production tables is not inherently invalid. It is valid when the customer deliberately authorizes the fixed installation or upgrade operation. What is invalid is allowing an ordinary collection request to acquire DDL capability implicitly.

The current preview's reusable bootstrap Job runs as the deploying owner and verifies visible schemas, not the full production ownership, table-format, view-definition, grant, and authority-retirement contract. That is one reason this release is not production-qualified.

## Minimum Unity Catalog capabilities

The supported route uses the exact grant manifest rendered by the attended installer.

An installer that creates a new schema needs `USE CATALOG` and `CREATE SCHEMA` on the selected catalog. Databricks documents those requirements in [Create schemas](https://learn.microsoft.com/en-us/azure/databricks/schemas/create-schema). Within an existing dedicated schema, object creation additionally requires the applicable schema create privileges.

A steady-state collector needs:

- `USE CATALOG` and `USE SCHEMA` on the selected parents;
- table data privileges sufficient for the fixed `MERGE`, readback, and final `UPDATE`; and
- `READ VOLUME` plus `WRITE VOLUME` on the raw archive Volume.

The observed runner receives parent usage and `READ VOLUME` plus `WRITE VOLUME` only on `dbtobsb_stage`. The collector receives `READ VOLUME` on staging; the observed runner cannot read normalized tables or the raw-custody Volume.

Databricks documents that creating or updating files requires both `READ VOLUME` and `WRITE VOLUME` with parent usage privileges ([Volume privileges](https://learn.microsoft.com/en-us/azure/databricks/volumes/privileges)). Because table `MODIFY` can also permit schema-altering operations, the runtime identity and its code/job managers remain trusted roots; a production installer must review that residual authority explicitly.

Ordinary readers should receive parent usage and `SELECT` on `dbt_run_health` and `dbt_node_health`, not the raw Volume or restricted tables.

## Job identities

The observed Job runs as its dedicated observed service principal. The collector and reconciler run as a distinct collector service principal. Job ACLs and the restricted `/Workspace/dbtobsb` Bundle root separate runtime reads from deployment management. Databricks documents the `run_as` separation used here in [Bundle run identity](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/run-as).

## Parameter sealing

Catalog, schema, Job IDs, principals, project bytes, runtime policy, package graph, and artifact roots are packaged into the finalized deployment seal. The observed-to-collector edge carries only Databricks dynamic correlation values. The collector rejects direct Run Now, parameter overrides, identity drift, source drift, and Job-graph drift before opening Spark or reading Unity Catalog.

## Artifact transport

The supported transport does not depend on a signed Jobs artifact URL. The product-owned runner writes only allowlisted files to a fixed customer-local Unity Catalog staging Volume through the authenticated Files API and verifies exact-byte readback. The collector reads those files through the same API, reconstructs a deterministic bounded archive, and writes exact-byte custody to `dbtobsb_raw` before parsing.

## Archive safety

Before parsing, the collector:

- limits the archive to 256 MiB, expanded content to 512 MiB, 4,096 members, and bounded path length;
- rejects absolute paths, traversal, links, special file types, duplicate members, and duplicate primary artifacts;
- reads the tar stream without extracting files to disk;
- rejects duplicate JSON keys, non-finite constants, excessive nesting, and unsupported schemas; and
- stores only allowlisted projections in the SQL evidence tables.

The exact archive is retained first so invalid or partial evidence is not silently destroyed.

## Logging and support

The collector's successful structured event contains only states and node count. Expected acquisition failures use static issue codes and do not include signed URLs, headers, response bodies, or raw evidence. Unhandled SDK, Spark, or platform failures can still produce Databricks-managed tracebacks with operational identifiers, so restrict Job-output access and apply the customer's log-retention policy. No application log path should be treated as a guaranteed declassification boundary.

For support, share static issue codes, qualified versions, sanitized counts, and approved hash prefixes. Do not paste raw artifacts into an ordinary ticket.
