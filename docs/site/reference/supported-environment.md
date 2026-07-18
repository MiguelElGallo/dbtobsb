# Supported environment

dbtobsb `v0.3.0` is supported only for the combination on this page. A newer
compatible-looking version is not supported until it passes the same tests and live
Azure qualification.

!!! danger "Not Databricks Free Edition"

    Install only in an Azure Databricks workspace deployed in the customer's
    Azure subscription. dbtobsb does not support AWS, GCP, **Databricks Free
    Edition**, or the retired Community Edition. “Personal Edition” is not a
    current Databricks product name; the official personal-use offering is Free
    Edition and is unsupported here.

## Platform

| Part | Supported value |
| --- | --- |
| Cloud | Azure Databricks only |
| Workspace offering | Customer Azure Databricks workspace; Free Edition unsupported |
| Workspace URL | Canonical `https://adb-<workspace-id>.<number>.azuredatabricks.net` URL |
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

## Why Free Edition is excluded

[Databricks Free Edition](https://learn.microsoft.com/en-us/azure/databricks/getting-started/free-edition)
is the current official name for the no-cost personal-use product. It replaced
Community Edition in 2025. Databricks does not document a separate product named
“Personal Edition.”

Free Edition is a serverless-only, quota-limited, non-commercial offering without
account-level APIs, compliance enforcement, private networking configuration, a
support policy, or an SLA. It can expose individual features also used by dbtobsb,
but the complete dbtobsb installation and governance contract has not been
qualified there and is explicitly unsupported. See the official
[Free Edition limitations](https://learn.microsoft.com/en-us/azure/databricks/getting-started/free-edition-limitations).

The installer accepts only the canonical Azure per-workspace URL documented by
[Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/workspace/per-workspace-urls).
AWS and GCP workspace hosts are outside the release contract.

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

- Databricks Free Edition, AWS Databricks, or GCP Databricks support;
- Databricks Marketplace distribution;
- independent separation of duties;
- in-place upgrade or rollback automation;
- automatic retention, legal hold, export, purge, or restore;
- normalized compiled SQL, source-freshness results, or Databricks query history;
- optional system-table enrichment; or
- Genie or another AI feature as part of the required path.

Regulated use needs the customer's own governance approval. The release is not a
compliance certification or external attestation.
