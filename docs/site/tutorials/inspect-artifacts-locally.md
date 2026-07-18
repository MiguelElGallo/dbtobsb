# Inspect dbt artifacts locally

In this tutorial, we will inspect synthetic dbt artifacts without connecting to
Databricks. You will see the difference between a valid pair and a successful dbt
run.

## Before you start

You need Python `3.12`, `uv`, and a private checkout of this repository. The first
environment setup can download packages from your configured Python package source.
Use a customer-approved registry or cache in a regulated environment.

This tutorial uses sanitized test files. Real `manifest.json` and
`run_results.json` files can contain sensitive operational data.

Create the locked environment:

```console
uv sync --project capture --locked --no-dev
```

## 1. Inspect a valid successful pair

Run:

```console
uv run --project capture --no-sync dbtobsb-capture inspect-artifact-pair \
  --manifest capture/tests/fixtures/artifact_pair/valid_success/manifest.json \
  --run-results capture/tests/fixtures/artifact_pair/valid_success/run_results.json \
  --no-color
```

The output is:

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

`PAIR_VALID` means the files have matching parseable invocation IDs and satisfy the
supported schema. It does not authenticate their origin or prove that nobody
modified them. The status line separately says that the files record one successful
dbt result.

## 2. Inspect a valid failed result

Run:

```console
uv run --project capture --no-sync dbtobsb-capture inspect-artifact-pair \
  --manifest capture/tests/fixtures/artifact_pair/valid_dbt_failure/manifest.json \
  --run-results capture/tests/fixtures/artifact_pair/valid_dbt_failure/run_results.json \
  --json \
  --no-color
```

The command still exits with `0` and reports `PAIR_VALID`, but the status count is:

```json
{"status_counts":{"error":1}}
```

The evidence is valid even though dbt recorded an error.

## 3. Inspect a mismatched pair

Run:

```console
uv run --project capture --no-sync dbtobsb-capture inspect-artifact-pair \
  --manifest capture/tests/fixtures/artifact_pair/invalid_invocation_mismatch/manifest.json \
  --run-results capture/tests/fixtures/artifact_pair/invalid_invocation_mismatch/run_results.json \
  --no-color
```

The output is:

```text
PAIR_INVALID
code: DBT_INVOCATION_ID_MISMATCH
impact: The files do not have the same dbt invocation identity.
next_action: Collect both closed artifacts from one completed pinned dbt build invocation before another dbt command runs.
```

Exit code `10` means the inspection completed and found invalid evidence. Do not
edit the files to make them pass. Collect a fresh pair from one dbt invocation.

## What you have seen

You can now answer two different questions:

- `pair_state` tells you whether the artifacts form a valid pair.
- `status_counts` tells you what dbt recorded inside a valid pair.

Neither one proves that the artifacts were retrieved and published in Databricks.
That is the collector's job.
