# Security and permissions

The P2 `v0.2.0-alpha.1` release is a personal/test engineering preview. It proves customer-local acquisition and SQL evidence, but it is not qualified for production or regulated workloads.

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

Actual grants depend on the customer's ownership model. The preview uses a combined personal identity; it does not install grants automatically.

An installer that creates a new schema needs `USE CATALOG` and `CREATE SCHEMA` on the selected catalog. Databricks documents those requirements in [Create schemas](https://learn.microsoft.com/en-us/azure/databricks/schemas/create-schema). Within an existing dedicated schema, object creation additionally requires the applicable schema create privileges.

A steady-state collector needs:

- `USE CATALOG` and `USE SCHEMA` on the selected parents;
- table data privileges sufficient for the fixed `MERGE`, readback, and final `UPDATE`; and
- `READ VOLUME` plus `WRITE VOLUME` on the raw archive Volume.

Databricks documents that creating or updating files requires both `READ VOLUME` and `WRITE VOLUME` with parent usage privileges ([Volume privileges](https://learn.microsoft.com/en-us/azure/databricks/volumes/privileges)). Because table `MODIFY` can also permit schema-altering operations, the runtime identity and its code/job managers remain trusted roots; a production installer must review that residual authority explicitly.

Ordinary readers should receive parent usage and `SELECT` on `dbt_run_health` and `dbt_node_health`, not the raw Volume or restricted tables.

## Job identity limitation

The current Bundle has no dedicated `run_as` service principal or resource ACL separation. Bootstrap, demo, and collector execute as the deploying owner. Databricks recommends a service-principal run identity for production because it separates workflow execution from deployment identity ([Bundle run identity](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/run-as)).

Before production qualification, the product must use separate installer and collector identities, fixed Job permissions, reviewed Unity Catalog grants, and verified removal or recording of temporary bootstrap authority.

## Parameter-sealing limitation

The P2 Job declares catalog, schema, Volume, and source-correlation values as Job parameters. The installed demo supplies them automatically, but a caller with Run Now or Run Job permission can override Job parameters. P2 therefore does not claim that its destination or source Job allowlist is sealed.

A regulated release must load the destination and allowed source Jobs/tasks from signed installed configuration, reject mismatches before any root write, and avoid treating caller-provided parameters as authorization.

## Artifact transport

The collector obtains the short-lived link and required headers only from the authenticated, correlated Jobs API response. It never prints or persists them. Downloads have size and time limits, and redirects cannot change origin.

Externally, the Azure workspace returned an HTTPS artifact link. Inside one serverless collector run, Databricks returned an HTTP link on a Databricks-owned hostname. P2 accepts that internal link only when it came through the correlated SDK response, the authenticated workspace is an exact Azure Databricks HTTPS host, the artifact host has a Databricks suffix, and neither URL contains user information or a port.

That narrow capability made live Azure serverless collection work, but suffix matching is not a vendor-backed regulated transport contract. The successful row does not attest whether HTTPS or the internal branch was used. Regulated qualification must obtain a canonical HTTPS path or a documented Databricks guarantee and record a safe transport-mode classification.

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
