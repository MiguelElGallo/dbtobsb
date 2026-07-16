# Compatibility and limitations

This page describes the private `v0.3.0` release candidate qualified on Azure Databricks. Marketplace distribution remains out of scope.

## Qualified combination

| Component | Qualified value |
| --- | --- |
| Cloud | Azure Databricks |
| Deployment CLI | Databricks CLI `1.7.0` |
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

The release uses native Databricks services wherever they preserve the contract:

- Jobs API/SDK for authenticated run correlation;
- Files API for bounded, verified transfer through `dbtobsb_stage`;
- Unity Catalog Volume for customer-local raw custody;
- Spark typed DataFrames and Delta `MERGE` for publication; and
- Databricks SQL views for user-facing analysis.

It does not use SQL `read_files` as the acceptance parser. Permissive file ingestion cannot enforce duplicate JSON-key rejection, the complete pinned JSON Schemas, tar safety, and cross-file invocation/node invariants. See [Decision 0003](../../decisions/0003-native-hybrid-collector.md).

## Known release limitations

- Private Bundle release only; Marketplace packaging is not included.
- The supported topology is the combined-administrator route. Separated duties are not claimed.
- The installer retains schema/object-owner authority as an explicit trusted root.
- Primary artifacts must be exactly the sealed per-attempt `manifest.json` and `run_results.json`; unexpected paths fail closed.
- Structured dbt logs are bounded and retained, but compiled SQL, catalog artifacts, source freshness results, and query history are not normalized.
- A failing product-runner dbt build still requires a dedicated live release-capture fixture; partial and invalid states are covered by offline fixtures.
- Automated raw retention, legal hold, export, purge, restore, and permission-separation tests are not shipped.
- The release does not include an SBOM, signed installer, Marketplace package, upgrade migration, or rollback automation.
- Default Storage was proven in a disposable serverless catalog; other managed/external storage topologies are unqualified.

These limitations are release boundaries, not suggested workarounds. Do not bypass them by weakening validation or granting a personal owner broader production access.
