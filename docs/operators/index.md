# Operate dbtobsb

dbtobsb uses Azure Databricks, Unity Catalog, serverless Jobs, SQL warehouses, and dbt Core. No
external telemetry platform receives evidence.

## v1 release-candidate recovery

These procedures describe the stopped-by-default v1 candidate with distinct observed and collector
service principals, attended installation, bounded collection reconciliation, and a read-only App.
They are not a released or production-qualified claim until the installer, reviews, and live Azure
qualification are complete. Databricks Marketplace is out of scope.

- [Reconcile missing dbt evidence](how-to/reconcile-collection.md)
- [Reconcile an installation](how-to/reconcile-installation.md)

## v0.2 personal/test preview

The remaining tutorial and reference pages describe the older maintainer-operated SQL-first
engineering preview with synthetic data. It is not a production, regulated, Marketplace, or
separation-of-duties claim.

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
