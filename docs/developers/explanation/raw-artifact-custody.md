# Handle raw dbt artifacts safely

P1.1 produces a deliberately small safe report, but its input files are raw evidence. The output boundary does not change the confidentiality, retention, or deletion requirements of `manifest.json`, `run_results.json`, or any copies.

## Why the inputs are sensitive

The dbt schemas permit data such as invocation and user identifiers, environment metadata, project and resource names, database and relation topology, local paths, descriptions, configuration, raw or compiled SQL, adapter responses, and error messages. Those values can contain Personal Data, credentials or other secrets, proprietary code, and operational security information.

The exact field boundary is versioned. Review the official [dbt artifact overview](https://docs.getdbt.com/reference/artifacts/dbt-artifacts), [manifest reference](https://docs.getdbt.com/reference/artifacts/manifest-json), [run-results reference](https://docs.getdbt.com/reference/artifacts/run-results-json), and the project [dbt source register](../../research/source-register.md#dbt-core-and-adapter-baseline) before changing a supported artifact version.

## What P1.1 does and does not do

| Boundary | P1.1 behavior |
| --- | --- |
| CLI input | Opens the two caller-supplied regular files and reads their bytes within the documented size limit. |
| Python input | Receives caller-provided bytes; the API does not open a caller path. |
| Inspection | Reads only installed checksum-pinned schemas and performs no runtime network, dbt, or Databricks call. |
| Returned report | Retains only allowlisted schema, version, command, status-count, state, and static issue facts. It retains no raw bytes. |
| Persistence and transfer | Does not persist, copy, upload, or transmit raw inputs. |
| Caller-owned files | Does not delete, encrypt, relocate, govern, or make the originals and other copies policy-compliant. |

## Apply the caller's evidence lifecycle

Before using real artifacts:

- keep them only in policy-approved local storage with least-privilege access;
- apply required encryption, access logging, endpoint controls, and approved transfer restrictions;
- include extracts and backups in the same classification, retention, and deletion decision;
- do not commit, upload, paste into chat, or attach raw files or fragments to an ordinary support ticket; and
- delete the caller-owned originals and copies only under the customer's approved retention schedule and legal-hold process.

The normal support payload is the product version, safe command shape, exit or static issue code, and allowlisted report. If raw evidence is exceptionally required, use a separately approved restricted-evidence process with a named authorized recipient, approved transfer method, explicit access boundary, and retention/deletion decision. P1.1 does not implement an evidence-upload endpoint.

## Two meanings of customer-local

P1.1 currently processes files on the operator's local execution host. Its no-network behavior keeps inspection local to that host, but does not prove that the workstation, its backups, or its support processes satisfy the future product boundary.

The target product is designed to keep runtime data and compute inside the customer's Databricks environment. Archive retrieval, collector storage, runtime retention, deletion, and uninstall remain later reviewed parts. Do not describe this workstation-side candidate as proof of the future Databricks-local custody model.

For report interpretation, read [Pair validity, dbt outcome, and capture state](pair-validity-vs-dbt-outcome-vs-capture-state.md). For a failed inspection, use [Diagnose an invalid artifact pair](../how-to/diagnose-an-invalid-artifact-pair.md). For the machine contract, use [CLI, report, and exit codes](../reference/cli-report-and-exit-codes.md).
