# Developer documentation

P1.1 gives library consumers one offline-after-installation operation: validate a pinned dbt artifact pair without running dbt or calling Databricks.

## Start with an outcome

- [Inspect an artifact pair](tutorials/inspect-an-artifact-pair.md) — run all three fixture journeys and learn what the result proves.
- [Diagnose an invalid artifact pair](how-to/diagnose-an-invalid-artifact-pair.md) — recover from `PAIR_INVALID`, exit `10`, or the safe input-read error on exit `3`.

## Look up a contract

- [Python API](reference/python-api.md)
- [CLI, report, and exit codes](reference/cli-report-and-exit-codes.md)

## Understand the boundaries

- [Pair validity, dbt outcome, and capture state](explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md)

The checked-in fixtures are synthetic and sanitized. They prove deterministic local behavior, not a live Databricks capture or a qualified production compatibility row.
