# Why outcomes stay separate

One word such as “success” cannot describe the whole evidence path.

Consider two examples:

- A dbt model test fails, but dbt still writes a valid manifest and run-results
  file. The dbt outcome is a failure, while evidence capture can be complete.
- dbt finishes successfully, but a staging permission blocks the collector. The
  dbt outcome is a success, while evidence retrieval is unavailable.

If dbtobsb collapsed these cases into one status, operators could mistake a data
quality failure for an observability failure—or miss an evidence gap after a
successful build.

## Five questions

dbtobsb keeps five questions separate:

| Question | Field or surface |
| --- | --- |
| Did the Databricks task finish successfully? | `lakeflow_result_state` |
| Did the collector obtain the files? | `retrieval_state` |
| Which primary files were present and safe? | `capture_state` |
| Do the primary files form a valid pair? | `pair_state` |
| Were normalized rows published? | `collector_state` |

Only after reading the relevant fields should you inspect dbt's node statuses.

## Complete does not mean successful

`COMPLETE` means both primary artifacts were found and accepted. `PAIR_VALID` means
they satisfy the supported contract and belong together. Neither means every model,
seed, or test passed.

This separation preserves dbt's native meaning while making evidence failures
visible in their own right.
