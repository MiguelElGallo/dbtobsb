# dbtobsb documentation

The repository contains a reviewed product contract, an intentionally small P0 Databricks App smoke, and the offline-after-installation P1.1 artifact-pair inspector.

## Start here

- [Product and delivery plan](plans/product-plan.md)
- [Review process](plans/review-process.md)
- [Documentation plan](plans/documentation-plan.md)
- [Decision 0001: private Databricks App plus Bundle](decisions/0001-private-app-bundle.md)
- [Research source register](research/source-register.md)
- [Review records](reviews/README.md)
- [Sanitized P0 live-smoke evidence](evidence/p0-live-smoke-2026-07-15.md)
- [P0 private run-record template](templates/p0-smoke-run-record.md)
- [Developer documentation](developers/index.md)
- [P1.1 local compatibility evidence](evidence/p1.1-local-artifact-pair-2026-07-15.md)

## Run the P0 smoke

The [repository README](../README.md#run-the-p0-smoke) contains the local quality gates, exact live-smoke inputs, cost boundary, and cleanup contract. The P0 endpoint proves only App process liveness; dbt execution and artifact ingestion begin in later slices.

## Inspect a dbt artifact pair

Start with [Inspect an artifact pair](developers/tutorials/inspect-an-artifact-pair.md). Before substituting real files, read [Handle raw dbt artifacts safely](developers/explanation/raw-artifact-custody.md). After its locked runtime is installed, P1.1 validates one pinned pair offline; it does not retrieve an archive, run dbt, prove a Databricks attempt, or assign a capture state.
