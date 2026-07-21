# Install the private v0.4 release

This is the supported route for one Azure Databricks workspace and one dbt Core project. The installer discovers existing customer resources, shows the selected boundary, and leaves the read-only App stopped. It does not require an external telemetry service or Databricks Marketplace.

> **Azure Databricks only:** Do not use this procedure with Databricks Free
> Edition, the retired Community Edition, AWS, or GCP. “Personal Edition” is not a
> current Databricks product name; personal-use signup means Free Edition. Use a
> customer Azure Databricks workspace with its canonical
> `adb-...azuredatabricks.net` URL.

## Before you begin

Use a managed Apple-silicon Mac with Python 3.12, `uv`, and Databricks CLI `1.8.0`. Run from a private checkout of this repository. The signed-in person must use a named Azure Databricks OAuth U2M profile and must be both account and workspace administrator.

Prepare these customer-owned resources first:

- one existing catalog whose name is a simple SQL identifier;
- one empty, dedicated evidence schema owned by the signed-in administrator;
- one dbt target schema owned by the observed Job service principal;
- distinct active service principals whose display names contain `observed` and `collector`;
- one customer group for Job management and App viewing;
- one existing SQL warehouse on which the observed principal already has `CAN_USE`; and
- one dbt project below the repository root with `dbt_project.yml`, `profiles.yml`, `selectors.yml`, and exactly one supported selector.

The installer will not create or delete either selected schema. Keep real credentials out of project files: the generated runtime profile uses Databricks' task-scoped `DBT_ACCESS_TOKEN`.

## Install

Install the locked local environment, then start the attended launcher:

```console
uv sync --project installer --locked
uv run --project installer --no-sync dbtobsb bootstrap
```

Select the named profile, service principals, group, warehouse, empty evidence schema, dbt target schema, and dbt project. The two schemas may use different existing catalogs. Review the displayed workspace, fully qualified data targets, project, and identities. Type `APPROVE` only when every selection is correct.

The launcher snapshots and seals the project, deploys three Jobs and the App through the Bundle, runs one temporary serverless bootstrap Job, applies the fixed grants, verifies the deployment, and removes the temporary Job. Successful completion ends with:

```json
{"app_state":"STOPPED","event":"dbtobsb_installation_verified","reconciler_state":"PAUSED","stage":"INSTALLED"}
```

Installation may take several minutes while Databricks allocates serverless compute. The selected SQL warehouse is not started by bootstrap.

## Resume safely

The private `.dbtobsb/release-installation-v2.json` file records the last completed stage and is created with owner-only permissions. If the terminal or network is interrupted, do not delete it and do not edit generated Bundle files. v0.4.0 has no upgrade or legacy-state adoption path; a v1 state or prior product installation blocks before mutation. Run the same command again:

```console
uv run --project installer --no-sync dbtobsb bootstrap
```

The launcher reads remote state and continues from the durable stage. An indeterminate remote result fails closed instead of replaying an unproven mutation.

## Run and inspect dbt

The deployed observed Job is the supported dbt entry point. It runs as the observed service principal and always invokes the collector through an `ALL_DONE` edge. Follow [Wire a supported dbt Job](../how-to/wire-a-dbt-job.md) to understand the sealed command, artifact paths, and evidence readback.

The App remains stopped until an operator explicitly acknowledges App compute cost:

```console
printf 'START\n' | uv run --project installer --no-sync dbtobsb start
uv run --project installer --no-sync dbtobsb stop
```

Starting the App does not itself start the SQL warehouse. Selecting **Load observability** in the App can start the bound warehouse.

## Uninstall

Choose retention before running the command. Retain removes runtime resources and product grants but keeps the nine product objects and raw archives under the installing administrator's existing ownership:

```console
printf 'RETAIN\n' | uv run --project installer --no-sync dbtobsb uninstall --retain
```

Delete removes those exact nine objects but preserves the selected schema. It requires a second acknowledgement for retention, legal hold, and verified exports:

```console
printf 'DELETE\nDELETE PRODUCT DATA\n' \
  | uv run --project installer --no-sync dbtobsb uninstall --delete
```

See [Stop compute and uninstall](../how-to/cleanup.md) for the final inventory checks and recovery rules.
