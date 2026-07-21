# Prepare a dbt project

Use this guide before a fresh dbtobsb installation. Version `0.4.0` installs one
observed dbt Core project and does not replace a project in place.

## Create the minimum project

Put the project in its own child directory below the dbtobsb repository root. Do
not make the repository root itself the dbt project: its `.git` and `.github`
directories are not valid project inputs. You provide two YAML files; dbtobsb adds
a third file, `profiles.yml`, to the installed snapshot.

Start with this layout:

```text
customer_weather/
├── dbt_project.yml
├── selectors.yml
└── models/
    └── observation_count.sql
```

Create `dbt_project.yml`:

```yaml
name: customer_weather
version: "1.0"
config-version: 2
profile: customer_weather
model-paths: [models]
```

The `profile` value is a name, not a connection. It must start with a letter, may
then contain letters, numbers, underscores, or hyphens, and may be at most 128
characters long. The installer uses the same name in the profile it generates.

Create `selectors.yml`:

```yaml
selectors:
  - name: weather_release
    description: Models observed by dbtobsb.
    definition:
      method: path
      value: models
```

This release accepts exactly one entry below `selectors`. Its name follows the same
character rules as the profile name and is at most 64 characters. The generated Job
runs `dbt build --selector weather_release`, so the definition must select every
model, seed, snapshot, and test that you want to observe. Do not add a second named
selector.

Create `models/observation_count.sql`:

```sql
select 1 as observation_count
```

For the same three copy-ready files, see the repository's
[minimal customer-weather project](https://github.com/MiguelElGallo/dbtobsb/tree/main/examples/customer_weather),
including its
[`dbt_project.yml`](https://github.com/MiguelElGallo/dbtobsb/blob/main/examples/customer_weather/dbt_project.yml)
and
[`selectors.yml`](https://github.com/MiguelElGallo/dbtobsb/blob/main/examples/customer_weather/selectors.yml).
This example deliberately has no `profiles.yml`.
The dbt documentation explains the general
[`dbt_project.yml` format](https://docs.getdbt.com/reference/dbt_project.yml) and
[YAML selectors](https://docs.getdbt.com/reference/node-selection/yaml-selectors).

## Keep connection details out

Do not add credentials to the project. dbtobsb ignores any source `profiles.yml`
and does not copy it. During installation, it creates a credential-free runtime
`profiles.yml` from the approved Azure Databricks host, warehouse, catalog, schema,
and observed Job identity. The source `logs` and `target` directories are also not
copied.

Do not set the top-level `flags`, `log-path`, `packages-install-path`, or
`target-path` keys in `dbt_project.yml`. dbtobsb controls those values so each run's
logs and result files go to the expected location.

The selected project directory must not contain hidden files, hidden directories,
or symbolic links. `selectors.yml` must contain only the top-level `selectors` key,
exactly one selector entry, and no Jinja. The installer stops with a safe
`DBTOBSB_ONBOARDING_...` code when one of these checks fails. See the complete
[dbt project input contract](../reference/dbt-project-input.md) for file limits and
all accepted or ignored inputs.

## Lock package dependencies

Skip this section if the project has no dbt packages.

If it has packages, commit exactly one `packages.yml` or `dependencies.yml` file
and the matching `package-lock.yml` created by dbt Core `1.11.12`. Run `dbt deps`
in the project's normal development environment, review the changes, and commit
both files. Do not hand-edit the lock file. The installer rejects a missing or
mismatched lock. See the dbt
[`deps` command](https://docs.getdbt.com/reference/commands/deps) for the standard
workflow.

## Check the installer preview

Continue with [Install the private release](install-private-release.md). Select this
project when the installer asks for the **dbt Core project to snapshot**.

Before you approve anything, the preview must show the project you selected, its
profile name, the single selector, and a command ending in
`dbt build --selector <your-selector>`. If the installer prints an onboarding code,
do not approve or edit generated files. Correct the source project and start the
installation again.

## Change an installed project

A project, selector, dependency, profile-name, or target change requires a fresh
installation and a new empty evidence schema. First handle the existing installation
with [uninstall](stop-or-uninstall.md) in retain or delete mode under the customer's
retention and legal-hold policy. `dbtobsb stop` is a safe preliminary action, but it
does not remove the installed state or allow project replacement. Do not delete
existing evidence merely to reuse its schema.

A change to the dbt command, runtime packages, artifact paths, or other fixed
runtime behavior requires a new dbtobsb release. It is not a project-preparation
choice.

After handling the old installation, return to
[Install the private release](install-private-release.md) with the changed project
and a new empty evidence schema.
