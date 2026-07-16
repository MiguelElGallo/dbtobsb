# Operate the SQL-first preview

This documentation is for the maintainer-operated private engineering preview. It uses Azure Databricks, Unity Catalog, serverless Jobs, one existing SQL warehouse for dbt, and dbt Core. No external telemetry platform receives evidence.

The preview is for personal/test workspaces and synthetic data. It is not a production, regulated, Marketplace, or separation-of-duties claim.

## Learn by doing

- [Capture the first dbt run](tutorials/first-capture.md)

## Complete a task

- [Wire a supported dbt Job](how-to/wire-a-dbt-job.md)
- [Recover a non-complete capture](how-to/recover-capture-states.md)
- [Stop compute and remove the preview](how-to/cleanup.md)

## Look up facts

- [Evidence tables and views](reference/evidence-schema.md)
- [Security and permissions](reference/security-and-permissions.md)
- [Compatibility and limitations](reference/compatibility-and-limitations.md)

## Understand the design

- [Raw artifact custody](../developers/explanation/raw-artifact-custody.md)
- [Pair validity, dbt outcome, and capture state](../developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md)
- [Decision 0003: native hybrid collector](../decisions/0003-native-hybrid-collector.md)

## See real evidence

- [Sanitized Azure Databricks capture from 2026-07-16](../evidence/p2-live-capture-2026-07-16.md)
