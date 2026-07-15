# Diagnose an invalid artifact pair

Use this guide when the inspector returns `PAIR_INVALID`, exits `10`, or emits `DBTOBSB_INPUT_READ_ERROR` with exit `3`.

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

| Code family | What to do |
| --- | --- |
| `*_INPUT_READ_ERROR` exit path | Supply two existing, closed, regular files no larger than 128 MiB each; do not use symlinks, devices, or pipes. |
| `*_JSON_*` | Recollect the unmodified UTF-8 JSON file from the pinned build target directory. |
| `*_SCHEMA_*` or `DBT_CORE_VERSION_UNSUPPORTED` | Use the exact supported artifact schemas and Core version, or qualify a new compatibility row separately. |
| `DBT_INVOCATION_ID_*` | Recollect both files from the same completed build target directory. |
| `DBT_ADAPTER_TYPE_UNSUPPORTED` or `DBT_COMMAND_UNSUPPORTED` | Use the pinned dbt-databricks `build` path; do not relabel another command. |
| `DBT_EMPTY_EXECUTION` | Fix the selector or executable-node set, then run the approved build again. |
| `DBT_RESULT*` or `DBT_MANIFEST_RESOURCE*` | Recollect the pair; do not select, remove, or reinterpret a resource manually. |
| `DBT_TIMING_INVALID` or `DBT_FAILURE_COUNT_INVALID` | Recollect unmodified output from the pinned build. |

The complete code registry is in [CLI, report, and exit codes](../reference/cli-report-and-exit-codes.md).

## Recover an input-read error

Exit `3` means one or both inputs could not be read as closed regular files within 128 MiB. Provide two existing, closed, non-symlink regular files no larger than 128 MiB, then rerun the same command. Do not replace the path with a pipe, device, or symbolic link. The CLI intentionally does not reveal which path failed.

## Confirm the recovery

Rerun the command. Exit `0` and `PAIR_VALID` confirm only pair validity. Check `status_counts` separately for the native dbt outcome, and do not claim a complete capture from this command.

If the error is exit `3`, follow its static next action; the tool never echoes the path. If the error is exit `4`, retain the product version and safe command form, then report `DBTOBSB_INTERNAL_ERROR` without attaching raw artifacts to an ordinary ticket.
