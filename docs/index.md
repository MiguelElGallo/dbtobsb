# dbtobsb documentation

The repository contains a reviewed product contract, a working SQL-first P2 engineering preview, an intentionally small stopped P0 Databricks App smoke, and the offline-after-installation artifact-pair inspector.

## Start here

- [Operator documentation](operators/index.md)
- [Capture the first dbt run](operators/tutorials/first-capture.md)
- [Sanitized P2 live capture](evidence/p2-live-capture-2026-07-16.md)
- [Product and delivery plan](plans/product-plan.md)
- [Review process](plans/review-process.md)
- [Documentation plan](plans/documentation-plan.md)
- [Decision 0001: private Databricks App plus Bundle](decisions/0001-private-app-bundle.md)
- [Decision 0002: correct P1.1 invocation recovery before first release](decisions/0002-correct-p1.1-invocation-recovery-text.md)
- [Research source register](research/source-register.md)
- [Review records](reviews/README.md)
- [Sanitized P0 live-smoke evidence](evidence/p0-live-smoke-2026-07-15.md)
- [P0 private run-record template](templates/p0-smoke-run-record.md)
- [Developer documentation](developers/index.md)
- [P1.1 local compatibility evidence](evidence/p1.1-local-artifact-pair-2026-07-15.md)

## Run the P0 smoke

The [repository README](../README.md#run-the-p0-smoke) contains the local quality gates, exact live-smoke inputs, cost boundary, and cleanup contract. The P0 endpoint proves only App process liveness; dbt execution and artifact ingestion begin in later slices.

## Inspect a dbt artifact pair

Start with [Inspect an artifact pair](developers/tutorials/inspect-an-artifact-pair.md). Before substituting real files, follow [Handle raw dbt artifacts safely](developers/how-to/handle-raw-dbt-artifacts-safely.md). After its locked runtime is installed, P1.1 validates one pinned pair offline; it does not retrieve an archive, run dbt, prove a Databricks attempt, or assign a capture state.

## Operate the SQL-first preview

The [operator landing page](operators/index.md) separates the tutorial, task guides, reference, and explanation. The preview uses an attended fixed bootstrap for product DDL and a DML-only collector for steady-state evidence. It does not require the stopped App.
