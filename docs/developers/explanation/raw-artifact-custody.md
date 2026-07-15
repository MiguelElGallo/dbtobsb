# Why safe reports do not make raw artifacts safe

P1.1 deliberately returns a small allowlisted report. That output boundary does not change the confidentiality, retention, or deletion requirements of the `manifest.json` and `run_results.json` inputs or any copies.

## Raw artifacts preserve operational context

The dbt schemas permit invocation and user identifiers, environment metadata, project and resource names, database and relation topology, local paths, descriptions, configuration, raw or compiled SQL, adapter responses, and error messages. Those values can contain Personal Data, credentials or other secrets, proprietary code, and operational security information.

The exact field boundary is versioned. The official [dbt artifact overview](https://docs.getdbt.com/reference/artifacts/dbt-artifacts), [manifest reference](https://docs.getdbt.com/reference/artifacts/manifest-json), [run-results reference](https://docs.getdbt.com/reference/artifacts/run-results-json), and project [dbt source register](../../research/source-register.md#dbt-core-and-adapter-baseline) define the supported evidence context.

## Inspection and custody are different controls

| Boundary | P1.1 behavior |
| --- | --- |
| CLI input | Opens the two caller-supplied regular files and reads their bytes within the documented size limit. |
| Python input | Receives caller-provided bytes; the API does not open a caller path. |
| Inspection | Reads only installed checksum-pinned schemas and performs no runtime network, dbt, or Databricks call. |
| Returned report | Retains only allowlisted schema, version, command, status-count, state, and static issue facts; it retains no raw bytes. |
| Persistence and transfer | Creates no durable file copy or external transfer of raw inputs. Transient in-process parsing still occurs. |
| Caller-owned files | Does not delete, encrypt, relocate, govern, or make originals and other copies policy-compliant. |

The safe report is therefore a separate, lower-data output. It is not a declassification decision for the evidence from which it was derived. Encryption, access logging, endpoint controls, backups, retention, deletion, and legal hold remain properties of the caller's environment and evidence lifecycle.

## Workstation-local is not Databricks-local

P1.1 currently processes files on the operator's local execution host. Its no-network inspection path keeps processing local to that host, but does not prove that the workstation, its backups, or its support processes satisfy the future product boundary.

The target product is designed to keep runtime data and compute inside the customer's Databricks environment. Archive retrieval, collector storage, runtime retention, deletion, and uninstall remain later reviewed parts. This workstation-side candidate is not proof of the future Databricks-local custody model.

For the real-work controls, use [Handle raw dbt artifacts safely](../how-to/handle-raw-dbt-artifacts-safely.md). For report interpretation, read [Pair validity, dbt outcome, and capture state](pair-validity-vs-dbt-outcome-vs-capture-state.md). For the machine contract, use [CLI, report, and exit codes](../reference/cli-report-and-exit-codes.md).
