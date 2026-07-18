# dbtobsb documentation

The repository contains the supported private v0.3 release, its machine-readable support contract, a stopped-by-default read-only Databricks App, the observed/collector/reconciler Jobs, and the offline artifact-pair inspector.

## Start here

- [Operator documentation](operators/index.md)
- [Install the private v0.3 release](operators/tutorials/install-private-release.md)
- [Wire a supported dbt Job](operators/how-to/wire-a-dbt-job.md)
- [v0.3 supported-release contract](releases/v0.3.0-support-contract.md)
- [v0.3.0 stable Azure Databricks acceptance](evidence/v0.3.0-stable-acceptance-2026-07-18.md)
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

## Run the legacy P0 App-shell smoke

The [repository README](../README.md#run-the-legacy-app-shell-development-smoke) retains the local quality gates, exact live-smoke inputs, cost boundary, and cleanup contract for the historical empty App shell. It is not the v0.3 installation route.

## Inspect a dbt artifact pair

Start with [Inspect an artifact pair](developers/tutorials/inspect-an-artifact-pair.md). Before substituting real files, follow [Handle raw dbt artifacts safely](developers/how-to/handle-raw-dbt-artifacts-safely.md). After its locked runtime is installed, P1.1 validates one pinned pair offline; it does not retrieve an archive, run dbt, prove a Databricks attempt, or assign a capture state.

## Operate v0.3

The [operator landing page](operators/index.md) separates task guides, reference, and explanation. v0.3 uses an attended fixed bootstrap for product DDL and a DML-only collector for steady-state evidence. SQL views remain usable while the read-only App is stopped.
