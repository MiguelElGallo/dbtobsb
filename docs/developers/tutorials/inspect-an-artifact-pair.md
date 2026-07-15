# Inspect an artifact pair

In this tutorial you will validate a successful pair, a pair whose dbt result is an error, and an invalid pair. After the one-time runtime installation, all three inspections are offline and normally take less than five minutes.

## Prerequisites

You need Python 3.12 and [uv](https://docs.astral.sh/uv/). Run commands from the repository root. You do not need Databricks credentials, dbt, a SQL warehouse, or any other compute.

On a clean machine, the first command can download the locked runtime packages from the configured Python index. In a regulated environment, configure the customer-approved registry or mirror first, or use a policy-approved populated uv cache. P1.1 does not yet ship a disconnected wheelhouse; without an approved reachable source or complete cache, stop before installation.

> **Sensitive input boundary:** This tutorial uses synthetic sanitized fixtures. Real `manifest.json` and `run_results.json` files can contain Personal Data, secrets, SQL, messages, paths, topology, and identities. Keep them in policy-approved storage with least-privilege access; do not commit, upload, paste, or attach them to an ordinary support ticket. Read [Handle raw dbt artifacts safely](../explanation/raw-artifact-custody.md) before substituting real files.

Create the locked environment:

```bash
uv sync --project capture --locked --no-dev
```

## 1. Inspect a valid successful pair

```bash
uv run --project capture --no-sync dbtobsb-capture inspect-artifact-pair \
  --manifest capture/tests/fixtures/artifact_pair/valid_success/manifest.json \
  --run-results capture/tests/fixtures/artifact_pair/valid_success/run_results.json \
  --no-color
```

The exact output is:

```text
PAIR_VALID
The files satisfy the pinned artifact-pair contract.
dbt_version: 1.11.12
adapter_type: databricks
command: build
result_count: 1
status_counts: success=1
next_action: Evaluate outer run and archive evidence before claiming capture state.
```

The command exits `0`. The pair is valid and its one native dbt result is `success`. A complete capture has not been proven.

## 2. Keep pair validity separate from dbt success

```bash
uv run --project capture --no-sync dbtobsb-capture inspect-artifact-pair \
  --manifest capture/tests/fixtures/artifact_pair/valid_dbt_failure/manifest.json \
  --run-results capture/tests/fixtures/artifact_pair/valid_dbt_failure/run_results.json \
  --json \
  --no-color
```

This command also exits `0`. Its compact JSON contains:

```json
{"issues":[],"pair_state":"PAIR_VALID","schema_version":"dbtobsb.artifact-pair-report.v1","summary":{"adapter_type":"databricks","command":"build","dbt_version":"1.11.12","manifest_schema":"https://schemas.getdbt.com/dbt/manifest/v12.json","run_results_schema":"https://schemas.getdbt.com/dbt/run-results/v6.json","status_counts":{"error":1}}}
```

`PAIR_VALID` says the evidence pair is internally valid. `status_counts.error=1` says dbt did not succeed. These facts are intentionally independent.

## 3. Inspect an invalid pair

```bash
uv run --project capture --no-sync dbtobsb-capture inspect-artifact-pair \
  --manifest capture/tests/fixtures/artifact_pair/invalid_invocation_mismatch/manifest.json \
  --run-results capture/tests/fixtures/artifact_pair/invalid_invocation_mismatch/run_results.json \
  --no-color
```

The exact output is:

```text
PAIR_INVALID
code: DBT_INVOCATION_ID_MISMATCH
impact: The files cannot be trusted as one dbt invocation.
next_action: Collect both artifacts from the same build target directory.
```

Exit `10` means inspection completed and found invalid evidence. Follow the printed `next_action`; do not edit an artifact to make it pass.

## 4. Use the Python API

Run the checked-in complete API example from the repository root:

```bash
uv run --project capture --no-sync python capture/examples/inspect_valid_fixture.py
```

The exact output is:

```text
PAIR_VALID
{"issues":[],"pair_state":"PAIR_VALID","schema_version":"dbtobsb.artifact-pair-report.v1","summary":{"adapter_type":"databricks","command":"build","dbt_version":"1.11.12","manifest_schema":"https://schemas.getdbt.com/dbt/manifest/v12.json","run_results_schema":"https://schemas.getdbt.com/dbt/run-results/v6.json","status_counts":{"success":1}}}
```

The example loads bytes outside the API, prints `PairState`, and serializes only the safe allowlisted dictionary. Use the [Python API reference](../reference/python-api.md) to look up the complete function, types, limits, and status vocabulary.

## What you have proved

You can now answer three separate questions:

1. Is the pair valid? Read `pair_state`.
2. What native outcomes did dbt record? Read `summary.status_counts` only when the pair is valid.
3. Is the dbtobsb capture complete? P1.1 cannot answer this. Later collection must add Databricks attempt, archive-retrieval, and log evidence.

Next, use [Diagnose an invalid artifact pair](../how-to/diagnose-an-invalid-artifact-pair.md), look up the [CLI report and exit-code contract](../reference/cli-report-and-exit-codes.md), or understand [why pair validity, dbt outcome, and capture state are separate](../explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md).
