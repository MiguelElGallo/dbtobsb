# Compatibility and limitations

This page describes the qualified private `v0.5.0` release. Its complete Azure
qualification is recorded in the
[v0.5.0 acceptance evidence](../../evidence/v0.5.0-live-acceptance-2026-07-22.md).
Marketplace distribution remains out of scope.

> **Platform boundary:** This release does not support Databricks Free Edition,
> the retired Community Edition, AWS Databricks, or GCP Databricks. “Personal
> Edition” is not a current official name; Databricks directs personal-use users
> to Free Edition. Use a customer Azure Databricks workspace with its canonical
> `adb-...azuredatabricks.net` URL.

## Qualified combination

| Component | Qualified value |
| --- | --- |
| Cloud | Azure Databricks only; Free Edition excluded |
| Deployment CLI | Databricks CLI `1.9.0` |
| Bundle engine | Direct |
| dbt process compute | Serverless Jobs environment client `5` |
| dbt SQL target | Existing Databricks SQL warehouse |
| Python | `3.12` package floor and tested local runtime |
| dbt Core | `1.11.12` |
| dbt-databricks | `1.12.2` |
| Databricks SDK for Python | `0.117.0` |
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

The required live proof uses `dbt build` with the fixed named selector
`weather_release`. Its run-results arguments must attest:

```text
which=build
selector=weather_release
select=[]
exclude=[]
indirect_selection=eager
full_refresh=null
```

The strict pair validator enforces every value above. The installed customer-project command is sealed, and arbitrary existing dbt Jobs are outside the support boundary until they are onboarded through the supported launcher.

## Databricks manifest compatibility exception

The exact qualification fixture contains this macro field, and the required live
pair must reproduce it:

```json
{"supported_languages":["sql","python","javascript"]}
```

It appears only at `macros.macro.dbt.materialization_function_default`. The immutable Core 1.11 manifest schema permits only SQL and Python, while the exact dbt-databricks dependency graph adds JavaScript support. The validator accepts only this exact schema error at this exact macro and path. Any extra language, different macro, or additional schema error fails closed.

The same exception applies to a manifest-only archive, so a legitimate early failure is classified `PARTIAL`, not invalid. The primary pair attests Core version and adapter type. The raw dbt log observed dbt-databricks `1.12.2`; the artifacts do not attest the transitive `dbt-adapters` distribution version, so explicit environment pins are a separate control.

## Native parser boundary

The release uses native Databricks services wherever they preserve the contract:

- Jobs API/SDK for authenticated run correlation;
- Files API for bounded, verified transfer through `dbtobsb_stage`;
- Unity Catalog Volume for customer-local raw custody;
- Spark typed DataFrames and Delta `MERGE` for publication; and
- Databricks SQL views for user-facing analysis.

It does not use SQL `read_files` as the acceptance parser. Permissive file ingestion cannot enforce duplicate JSON-key rejection, the complete pinned JSON Schemas, tar safety, and cross-file invocation/node invariants. See [Decision 0003](../../decisions/0003-native-hybrid-collector.md).

## Known release limitations

- Databricks Free Edition, AWS Databricks, and GCP Databricks are unsupported.
- Private Bundle release only; Marketplace packaging is not included.
- The supported topology is the combined-administrator route. Separated duties are not claimed.
- The installer retains schema/object-owner authority as an explicit trusted root.
- Primary artifacts must be exactly the sealed per-attempt `manifest.json` and `run_results.json`; unexpected paths fail closed.
- Structured dbt logs are bounded and retained, but compiled SQL, catalog artifacts, source freshness results, and query history are not normalized.
- The live proof must cover an early product-runner failure with no retrievable archive; node-level failure, partial, and invalid states additionally have offline fixtures.
- Retain- and delete-uninstall must pass the live matrix before publication, but automated retention policy, legal hold, export, scheduled purge, and restore are not shipped.
- The release installer contains a generated SPDX SBOM for its native helper dependencies, but it is not signed and does not include Marketplace packaging, upgrade migration, or rollback automation.
- The qualified storage topology is a Unity Catalog managed catalog with a
  catalog-level managed storage root. The customer-owned evidence schema inherits
  that storage and has no schema-level managed location. The product tables and
  Volumes are managed; external storage topologies are not qualified by this
  release packet.

These limitations are release boundaries, not suggested workarounds. Do not bypass them by weakening validation or granting a personal owner broader production access.
