# Security and permissions

dbtobsb keeps captured evidence and product runtime compute inside the customer's
Azure Databricks workspace. Customer-local does not mean non-sensitive: dbt
artifacts and logs can contain SQL, messages, paths, relation names, secrets,
workspace structure, and Personal Data.

The required installer runs on a managed Mac and keeps an owner-only local state
file. That file contains the actor name, workspace host, resource IDs, service
principal and group names, and schema names. Treat the workstation as a regulated
endpoint. Do not commit, copy, or attach the state file to ordinary support. A
successful uninstall removes it; an interrupted lifecycle operation preserves it
so the same command can resume safely.

## Supported responsibility model

One combined administrator installs `v0.3.0`. This person is an Azure Databricks
account and workspace administrator and owns the selected evidence schema. The
release does not claim independent approval or separation of duties.

After installation, approved people may run the observed Job or use the App without
becoming the installing administrator.

## Runtime identities

| Identity | Required access |
| --- | --- |
| Observed Job service principal | Use the dbt target warehouse and target schema; read and write only the staging Volume in the evidence schema; read deployed files under `/Workspace/dbtobsb`; and start the fixed collector Job. |
| Collector service principal | Read staging; read and write the raw Volume; read the manifest table; read and modify the three evidence tables; use the parent catalog and schema; and read deployed files under `/Workspace/dbtobsb`. |
| App service principal | Use the bound SQL warehouse; select only the three health views; use the parent catalog and schema. |
| Job and App user group | Manage all three installed Jobs, manage deployed files under `/Workspace/dbtobsb`, and use the App as approved by the customer. |

The observed and collector principals must be different. The observed principal
cannot read or modify normalized evidence. The App cannot read raw tables or
Volumes and cannot run Jobs.

`CAN_MANAGE` on `/Workspace/dbtobsb` lets the customer group change deployed code
and Bundle files. Members of that group are therefore trusted roots, not only Job
operators. `CAN_MANAGE_RUN` on the collector Job lets the observed identity start
only the fixed collection path; the collector also verifies the parent and attempt
before writing evidence.

## Installation and runtime authority

Installation and collection use different paths:

- `BOOTSTRAP_ALLOWED` is the attended installation phase. It creates or verifies
  only the fixed product objects and permissions in the approved schema.
- `RUNTIME_DML_ONLY` is ordinary collection. It writes fixed rows to the existing
  evidence tables and exact archives to the existing raw Volume.

Table-level `MODIFY` can permit some schema changes. The collector principal, people
who can change its code or Job, schema and object owners, workspace administrators,
and relevant catalog administrators are trusted roots. dbtobsb does not claim to
protect evidence from a compromised trusted root.

## Safe read surfaces

Give ordinary readers parent `USE` privileges and `SELECT` on:

- `dbt_run_health`;
- `dbt_node_health`; and
- `dbt_collection_health`.

Do not give ordinary App or dashboard users access to the raw Volume, staging
Volume, archive locator, or restricted tables.

## Support and retention

Share static issue codes and sanitized states, counts, versions, and approved hash
prefixes. Do not paste raw artifacts, logs, SQL, environment values, native
tracebacks, or operational identifiers into an ordinary support channel.

The customer decides access, retention, export, legal hold, backup, and deletion.
`v0.3.0` does not automate those policies.
