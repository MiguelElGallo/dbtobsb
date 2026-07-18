# Supported environment

dbtobsb `v0.3.0` is supported only for the combination on this page. A newer
compatible-looking version is not supported until it passes the same tests and live
Azure qualification.

## Platform

| Part | Supported value |
| --- | --- |
| Cloud | Azure Databricks |
| Distribution | Private Databricks App and Declarative Automation Bundle |
| Databricks CLI | `1.7.0` |
| Bundle engine | Direct, the built-in Bundle deployment engine |
| Installer workstation | Managed Apple-silicon Mac |
| Local Python | `3.12` |
| Authentication | Named Databricks CLI OAuth user profile |
| dbt and collector compute | Serverless Lakeflow Jobs, environment client `5` |
| dbt SQL target | Existing Databricks SQL warehouse |
| App compute | Databricks Apps serverless compute |

`Direct` means the Bundle uses the Databricks CLI's built-in deployment engine.
Environment client `5` is the serverless Jobs environment generation qualified by
this release. These are fixed compatibility values, not settings to tune during
installation.

## dbt packages

| Package | Version |
| --- | --- |
| dbt Core | `1.11.12` |
| dbt-databricks | `1.12.2` |
| dbt-adapters | `1.24.5` |
| dbt-common | `1.37.5` |
| dbt-spark | `1.10.3` |
| dbt-protos | `1.0.541` |
| Databricks SDK for Python | `0.117.0` |
| Databricks SQL Connector | `4.3.0` |

## dbt contract

The observed Job runs `dbt build` with one installed named selector. It accepts
manifest schema `v12`, run-results schema `v6`, and structured dbt log version `3`.
The project, selector, profile, target, command, package graph, and output paths are
sealed during installation.

## Release limits

The release does not include:

- Databricks Marketplace distribution;
- independent separation of duties;
- in-place upgrade or rollback automation;
- automatic retention, legal hold, export, purge, or restore;
- normalized compiled SQL, source-freshness results, or Databricks query history;
- optional system-table enrichment; or
- Genie or another AI feature as part of the required path.

Regulated use needs the customer's own governance approval. The release is not a
compliance certification or external attestation.
