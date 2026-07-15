# dbtobsb documentation

The repository contains a reviewed product contract and an intentionally small P0 Databricks App smoke implementation.

## Start here

- [Product and delivery plan](plans/product-plan.md)
- [Review process](plans/review-process.md)
- [Documentation plan](plans/documentation-plan.md)
- [Decision 0001: private Databricks App plus Bundle](decisions/0001-private-app-bundle.md)
- [Research source register](research/source-register.md)
- [Review records](reviews/README.md)
- [Sanitized P0 live-smoke evidence](evidence/p0-live-smoke-2026-07-15.md)
- [P0 private run-record template](templates/p0-smoke-run-record.md)

## Run the P0 smoke

The [repository README](../README.md#run-the-p0-smoke) contains the local quality gates, exact live-smoke inputs, cost boundary, and cleanup contract. The P0 endpoint proves only App process liveness; dbt execution and artifact ingestion begin in later slices.
