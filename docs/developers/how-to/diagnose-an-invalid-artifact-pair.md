# Diagnose an invalid artifact pair

Use this guide when the inspector returns `PAIR_INVALID`, exits `10`, or emits `DBTOBSB_INPUT_READ_ERROR` with exit `3`.

> **Before using real files:** Raw dbt artifacts can contain Personal Data, secrets, SQL, messages, paths, topology, and identities. Use policy-approved local storage and least-privilege access. Do not commit, upload, paste, or attach the files to an ordinary ticket. Inspection does not delete or govern the originals; follow [Handle raw dbt artifacts safely](../explanation/raw-artifact-custody.md).

## Get the primary recovery action

Run the same pair in text mode:

```bash
uv run --project capture --no-sync dbtobsb-capture inspect-artifact-pair \
  --manifest '<closed-local-path>/manifest.json' \
  --run-results '<closed-local-path>/run_results.json' \
  --no-color
```

Read the first `code` and its `next_action`. Issue order is deterministic, and the first issue is the primary recovery path.

## Recover by issue family

| Code family | Classification | What to do |
| --- | --- | --- |
| `*_INPUT_READ_ERROR` exit path | Correct local input | Supply two existing, closed, regular files no larger than 128 MiB each; do not use symlinks, devices, or pipes. |
| `*_JSON_*` | Recollect | Recollect the unmodified UTF-8 JSON file from the pinned build target directory. |
| `*_SCHEMA_*`, `DBT_SCHEMA_VERSION_UNSUPPORTED`, or `DBT_CORE_VERSION_UNSUPPORTED` | Compatibility or recollect | Use the exact supported artifact schemas and Core version, or qualify a new compatibility row separately. |
| `DBT_INVOCATION_ID_*` | Recollect pair | Recollect both files from the same completed build target directory. |
| `DBT_ADAPTER_TYPE_UNSUPPORTED` or `DBT_COMMAND_UNSUPPORTED` | Unsupported compatibility | Use the pinned dbt-databricks `build` path; do not relabel another command. |
| `DBT_EMPTY_EXECUTION` | Correct and rerun | Fix the selector or executable-node set, then run the approved build again. |
| `DBT_RESULT*` or `DBT_MANIFEST_RESOURCE*` | Recollect pair | Recollect the pair; do not select, remove, or reinterpret a resource manually. |
| `DBT_TIMING_INVALID` or `DBT_FAILURE_COUNT_INVALID` | Recollect | Recollect unmodified output from the pinned build. |

### Recover file, JSON, or schema inputs

For size, JSON, schema, or version issues, recollect the affected complete file from the pinned build target directory. Use only the supported schema/Core row. Do not truncate, split, repair, or rewrite the evidence; a new version requires separate compatibility qualification.

### Recover pair metadata

For invocation identity, adapter, or command issues, collect both files from one completed pinned Databricks `build`. Do not combine directories or relabel another adapter or command.

### Recover result evidence

For empty, duplicate, unresolved, ambiguous, mismatched, unsupported-resource, or unsupported-status results, fix an empty selector only when directed and run a new approved build; otherwise recollect the pair. Never delete, choose, or reinterpret a result inside an existing artifact.

### Recover numeric evidence

For timing or failure-count issues, recollect unmodified output from the pinned build. Do not clamp or replace the value.

The complete code registry is in [CLI, report, and exit codes](../reference/cli-report-and-exit-codes.md).

## Recover an input-read error

Exit `3` means one or both inputs could not be read as closed regular files within 128 MiB. Provide two existing, closed, non-symlink regular files no larger than 128 MiB, then rerun the same command. Do not replace the path with a pipe, device, or symbolic link. The CLI intentionally does not reveal which path failed.

## Confirm the recovery

Rerun the command. Exit `0` and `PAIR_VALID` confirm only pair validity. Check `status_counts` separately for the native dbt outcome, and do not claim a complete capture from this command.

If the error is exit `3`, follow its static next action; the tool never echoes the path. If the error is exit `4`, retain the product version and safe command form, then report `DBTOBSB_INTERNAL_ERROR`.

For any issue, the ordinary support payload is limited to the product version, safe command shape, exit or static issue code, and allowlisted report. Never attach raw artifacts to an ordinary ticket. If an accountable support owner exceptionally requires raw evidence, use a separately approved restricted-evidence process that names the authorized recipient, transfer method, access boundary, and retention/deletion decision; P1.1 provides no upload endpoint.

For the interpretation behind the recovery check, read [Pair validity, dbt outcome, and capture state](../explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md). For input custody and lifecycle, read [Handle raw dbt artifacts safely](../explanation/raw-artifact-custody.md).
