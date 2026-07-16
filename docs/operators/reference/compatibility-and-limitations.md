# Compatibility and limitations

This page describes the exact P2 `v0.2.0-alpha.1` engineering preview tested on 16 July 2026.

The `v0.2.0-alpha.1` release maps to evidence manifest `dbtobsb.evidence.v0.2.0-alpha.1`, capture package `0.2.0a3`, collector package `0.2.0a14`, and the unchanged P0 App shell `0.1.0`.

## Qualified combination

| Component | Qualified value |
| --- | --- |
| Cloud | Azure Databricks |
| Deployment CLI | Databricks CLI `1.7.0` |
| Bundle engine | Direct |
| dbt process compute | Serverless Jobs environment client `4` |
| dbt SQL target | Existing Databricks SQL warehouse |
| Python | `3.12` package floor and tested local runtime |
| dbt Core | `1.11.12` |
| dbt-databricks | `1.12.2` |
| Databricks SDK for Python, collector | `0.120.0` |
| Databricks SDK for Python, dbt environment | `0.117.0` |
| dbt-adapters | `1.24.5` |
| dbt-common | `1.37.5` |
| dbt-spark | `1.10.3` |
| dbt-protos | `1.0.541` |
| Databricks SQL Connector | `4.3.0` |
| Manifest schema | Vendored dbt manifest v12 |
| Run-results schema | Vendored run-results v6 |
| File log | dbt log version `3`, retained raw but not normalized |

Exact package pins are a release control. A range-compatible future version is not supported until its real task archive passes the same fixtures and live proof.

## Qualified dbt command

The live proof used one `dbt build` with the fixed named selector `observability_demo`. Its run-results arguments attested:

```text
which=build
selector=observability_demo
select=[]
exclude=[]
indirect_selection=eager
full_refresh=null
```

The strict pair validator enforces every value above. The installed demo command is fixed, and arbitrary existing dbt Jobs are outside the support boundary.

## Databricks manifest compatibility exception

The exact live pair emitted this macro field:

```json
{"supported_languages":["sql","python","javascript"]}
```

It appears only at `macros.macro.dbt.materialization_function_default`. The immutable Core 1.11 manifest schema permits only SQL and Python, while the exact dbt-databricks dependency graph adds JavaScript support. The validator accepts only this exact schema error at this exact macro and path. Any extra language, different macro, or additional schema error fails closed.

The same exception applies to a manifest-only archive, so a legitimate early failure is classified `PARTIAL`, not invalid. The primary pair attests Core version and adapter type. The raw dbt log observed dbt-databricks `1.12.2`; the artifacts do not attest the transitive `dbt-adapters` distribution version, so explicit environment pins are a separate control.

## Native parser boundary

P2 uses native Databricks services wherever they preserve the contract:

- Jobs API/SDK for authenticated run correlation and artifact discovery;
- Unity Catalog Volume for customer-local raw custody;
- Spark typed DataFrames and Delta `MERGE` for publication; and
- Databricks SQL views for user-facing analysis.

It does not use SQL `read_files` as the acceptance parser. Permissive file ingestion cannot enforce duplicate JSON-key rejection, the complete pinned JSON Schemas, tar safety, and cross-file invocation/node invariants. See [Decision 0003](../../decisions/0003-native-hybrid-collector.md).

## Known release limitations

- Personal/test engineering preview only; no production, regulated, compliance, or Marketplace claim.
- The App is a stopped process-liveness shell. SQL views are the usable release surface.
- No dedicated collector service principal, `run_as`, or Job ACL separation.
- Bootstrap is a reusable Job and does not retire authority after installation.
- Bootstrap verifies visible field schemas but not the complete object type, Delta properties, owners, grants, managed-Volume properties, or view definitions.
- Destination and source IDs are caller-overrideable Job parameters, not sealed installation configuration.
- Source Job/task allowlisting is not implemented. The collector does reject
  nonterminal or unknown task states before requesting task output.
- Internal HTTP artifact transport is live-observed but not vendor-qualified for a regulated boundary; the published row does not record which transport branch was used.
- The dbt task's current custom profile relies on task-provided connection environment behavior; the live Azure run succeeded, but the documented profile contract needs to be aligned before broader support.
- Primary artifacts must be exactly `target/manifest.json` and `target/run_results.json`; an unexpected primary basename path fails closed.
- `dbt.log`, `semantic_manifest.json`, compiled SQL, catalog artifacts, sources results, and query history are not normalized.
- A native failing dbt build has not yet been captured live in this P2 path; partial and invalid states are covered by offline fixtures.
- Automated raw retention, legal hold, export, purge, restore, and permission-separation tests are not shipped.
- The release does not include an SBOM, signed installer, Marketplace package, upgrade migration, or rollback automation.
- Default Storage was proven in a disposable serverless catalog; other managed/external storage topologies are unqualified.

These limitations are release boundaries, not suggested workarounds. Do not bypass them by weakening validation or granting a personal owner broader production access.
