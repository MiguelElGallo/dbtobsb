# Install the private release

Use this guide to install dbtobsb `v0.3.0` in one Azure Databricks workspace.
The installation is attended: one accountable administrator reviews the selected
resources before any change is made.

## Before you begin

Use a managed Apple-silicon Mac with:

- Python `3.12`;
- `uv`;
- Databricks CLI `1.7.0`;
- a private checkout of the `v0.3.0` release; and
- a named Azure Databricks OAuth profile. Do not use `DEFAULT`.

The signed-in person must be both an Azure Databricks account administrator and
workspace administrator. The same person must own the existing evidence schema.
This release does not provide independent separation of duties.

Prepare these customer-owned resources:

- one existing Unity Catalog catalog;
- one empty, dedicated evidence schema;
- one dbt target schema owned by the observed Job service principal;
- separate active service principals for the observed and collector Jobs;
- one group that may manage the Jobs and use the App;
- one existing SQL warehouse that the observed principal can use; and
- one dbt project under the repository root.

The dbt project must contain `dbt_project.yml`, `selectors.yml`, and exactly one
supported named selector. A source `profiles.yml` is not required and is not copied;
the installer generates the runtime profile from approved resources. Keep
credentials out of the project.

!!! warning "Installation can change production data objects"

    The attended bootstrap creates the fixed dbtobsb tables, views, and Volumes in
    the evidence schema you approve. It can target production when the administrator
    deliberately chooses that destination. Ordinary collection does not create
    objects.

## 1. Prepare the local installer

From the repository root, install the locked environment:

```console
uv sync --project installer --locked
```

## 2. Start the attended installation

Run:

```console
uv run --project installer --no-sync dbtobsb bootstrap
```

The installer asks you to select the named profile, service principals, group,
warehouse, catalog, schemas, and dbt project. Review the full summary. Type
`APPROVE` only when every value is correct.

The installer then:

1. copies and seals the approved dbt project;
2. deploys the observed, collector, and paused reconciler Jobs;
3. creates and verifies the nine fixed Unity Catalog objects;
4. applies the exact product permissions;
5. starts and stops the read-only App during two bounded deployment checks; and
6. leaves the App stopped.

Serverless bootstrap Job compute and the two bounded App deployment checks can run
for several minutes and incur usage. Bootstrap verifies that the App is stopped
after each check and before success. It does not start the selected SQL warehouse.

A successful installation ends with:

```json
{"app_state":"STOPPED","event":"dbtobsb_installation_verified","reconciler_state":"PAUSED","stage":"INSTALLED"}
```

## 3. Resume an interrupted installation

The local `.dbtobsb/release-installation-v1.json` file records completed stages and
uses owner-only permissions. It also contains sensitive operational identifiers,
including the actor, workspace host, resource IDs, identity and group names, and
schema names. Keep it on the managed installation workstation; do not commit, copy,
or attach it to an ordinary support ticket. Do not edit or delete it after an
interruption.

Run the same command again:

```console
uv run --project installer --no-sync dbtobsb bootstrap
```

The installer compares the saved stage with remote state and continues safely. It
does not repeat a change when the previous result is unknown.

## 4. Continue to a first run

The App remains stopped and the reconciler schedule remains paused. Continue with
[See your first observed dbt run](../tutorials/see-your-first-run.md).

If the installer reports a stable code instead of success, preserve that code and
the local state file. Do not edit Jobs, grants, App bindings, or evidence objects by
hand.
