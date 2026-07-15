# dbtobsb capture

`dbtobsb-capture` is the offline P1.1 artifact-pair inspector. It validates one
pinned dbt Core `manifest.json` v12 and `run_results.json` v6 pair without
Databricks, dbt, network, environment, clock, or subprocess access.

The result is `PAIR_VALID` or `PAIR_INVALID`. Pair validity does not say that dbt
succeeded and does not prove the later dbtobsb capture state.

Start with the
[artifact-pair tutorial](../docs/developers/tutorials/inspect-an-artifact-pair.md),
then use the [CLI reference](../docs/developers/reference/cli-report-and-exit-codes.md)
or [Python API reference](../docs/developers/reference/python-api.md).
