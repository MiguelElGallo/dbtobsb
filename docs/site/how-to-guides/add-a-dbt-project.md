# Add a dbt project

Use this guide before a fresh dbtobsb installation. Version `0.3.0` installs one
observed dbt Core project and does not replace a project in place.

## Prepare the project

Put the project under the [Bundle](../reference/glossary.md#bundle) repository root.
It must contain:

- `dbt_project.yml` with a valid profile name;
- `selectors.yml` with exactly one supported selector; and
- either no package dependencies, or a committed dependency file with its matching
  `package-lock.yml`.

Do not put credentials in the project. A source `profiles.yml` is not required and
is not copied. dbtobsb generates the runtime profile from resources discovered and
approved during installation. The project `logs` and `target` directories are also
not copied.

## Start a fresh installation

From the repository root, run:

```console
uv run --project installer --no-sync dbtobsb bootstrap
```

Select the project when the installer shows the **dbt Core project to snapshot**
prompt. The installer discovers the workspace host, warehouse, catalog, and schemas
through the authenticated named profile. Do not type or pipe those connection
fields into a separate onboarding command.

At the installation preview, verify the workspace, evidence schema, dbt target,
project, and both runtime identities. Type `APPROVE` only when every value is
correct. The installer then creates a content-addressed project snapshot, generates
its credential-free runtime profile and observed Job definition, deploys them, and
ends with:

```json
{"app_state":"STOPPED","event":"dbtobsb_installation_verified","reconciler_state":"PAUSED","stage":"INSTALLED"}
```

## Change an installed project

A project, selector, dependency, profile-name, or target change requires a fresh
installation and a new empty evidence schema. First handle the existing installation
with [uninstall](stop-or-uninstall.md) in retain or delete mode under the customer's
retention and legal-hold policy. `dbtobsb stop` is a safe preliminary action, but it
does not remove the installed state or allow project replacement. Do not delete
existing evidence merely to reuse its schema.

A change to the dbt command, runtime packages, artifact paths, or other sealed
runtime behavior requires a new dbtobsb release. It is not a project-onboarding
choice.
