# CLI, report, and exit codes

The packaged command is non-interactive, text-only, and safe for a non-TTY:

```text
dbtobsb-capture inspect-artifact-pair \
  --manifest PATH \
  --run-results PATH \
  [--json] \
  [--no-color]
```

`--manifest` and `--run-results` are required and cannot be abbreviated. `--json` emits compact, sorted-key JSON. `--no-color` is accepted for automation consistency; output never uses color. `NO_COLOR` also has no effect because color is never produced.

## Exit codes

| Exit | Stable meaning | Output |
| ---: | --- | --- |
| `0` | Inspection completed and the pair is valid. | Safe report on stdout. |
| `10` | Inspection completed and the pair is invalid. | Safe report on stdout. |
| `2` | Command usage is invalid. | Usage plus `DBTOBSB_CLI_USAGE_ERROR` on stderr. |
| `3` | An input could not be read safely. | Static code, impact, next action, and local help route on stderr. |
| `4` | An internal tool failure occurred. | `DBTOBSB_INTERNAL_ERROR` on stderr. |

The tool accepts regular files only, rejects symbolic links where the operating system supports `O_NOFOLLOW`, and caps each primary file at 128 MiB. Read and internal errors do not echo a path, exception, or artifact fragment.

Exit `3` emits exactly:

```text
DBTOBSB_INPUT_READ_ERROR
impact: One or both inputs could not be read as closed regular files within 128 MiB.
next_action: Provide existing, closed, non-symlink regular files no larger than 128 MiB.
help: docs/developers/how-to/diagnose-an-invalid-artifact-pair.md#recover-an-input-read-error
```

## Sensitive input boundary

The CLI reads caller-owned raw artifacts but does not persist, copy, upload, delete, or govern them. Those files can contain Personal Data, secrets, SQL, messages, paths, topology, and identities. Use policy-approved storage and least-privilege access; never commit, upload, paste, or attach them to an ordinary ticket. Apply the custody, support, retention, backup, and deletion controls in [Handle raw dbt artifacts safely](../how-to/handle-raw-dbt-artifacts-safely.md).

## Machine report

The top-level fields are:

| Field | Meaning |
| --- | --- |
| `schema_version` | Exactly `dbtobsb.artifact-pair-report.v1`. |
| `pair_state` | `PAIR_VALID` or `PAIR_INVALID`. |
| `summary` | Allowlisted pair facts for a valid pair; otherwise `null`. |
| `issues` | Zero for a valid pair; one to 20 unique static issues for an invalid pair. |

The `summary` contains exact schema URLs, dbt version, adapter type, command, and a closed native-status count object. The result total is the sum of that object's integer values; the JSON omits a redundant total that could disagree. It contains no resource or invocation identity. Every issue contains only `code`, `component`, `field`, `observed_category`, `impact`, and `next_action`; observed evidence is never interpolated. `issues[0]` is the primary issue under the shared v1 registry, so the JSON omits a second copy that could disagree. The schema rejects a first issue if an earlier-precedence issue is also present.

The v1 schema is closed: it rejects invented state/status/code/text values, more than 20 or duplicate issues, reversed primary precedence, legacy redundant fields, and extra properties. Statuses are object keys, so one status cannot occur twice. Public Python constructors additionally reject wrong object types and require the complete issue tuple to use canonical precedence.

## Issue registry

The rows follow primary-selection precedence. “Recollect” means obtain fresh unmodified output from the pinned build; it never means editing evidence to pass.

<!-- BEGIN: issue-registry -->

| Code | Exact safe impact | Classification | Exact primary action | Recovery |
| --- | --- | --- | --- | --- |
| `DBT_MANIFEST_SIZE_LIMIT_EXCEEDED` | The manifest cannot be inspected within the bounded local memory policy. | Correct input or recollect | Collect a complete manifest within 128 MiB; do not split or truncate it. | [Recover file, JSON, or schema inputs](../how-to/diagnose-an-invalid-artifact-pair.md#recover-file-json-or-schema-inputs) |
| `DBT_RUN_RESULTS_SIZE_LIMIT_EXCEEDED` | The run-results file cannot be inspected within the bounded local memory policy. | Correct input or recollect | Collect a complete run_results.json within 128 MiB; do not split or truncate it. | [Recover file, JSON, or schema inputs](../how-to/diagnose-an-invalid-artifact-pair.md#recover-file-json-or-schema-inputs) |
| `DBT_MANIFEST_JSON_INVALID` | The manifest is not one unambiguous UTF-8 JSON document. | Recollect | Collect manifest.json again from the pinned dbt build target directory. | [Recover file, JSON, or schema inputs](../how-to/diagnose-an-invalid-artifact-pair.md#recover-file-json-or-schema-inputs) |
| `DBT_RUN_RESULTS_JSON_INVALID` | The run-results file is not one unambiguous UTF-8 JSON document. | Recollect | Collect run_results.json again from the pinned dbt build target directory. | [Recover file, JSON, or schema inputs](../how-to/diagnose-an-invalid-artifact-pair.md#recover-file-json-or-schema-inputs) |
| `DBT_MANIFEST_JSON_DUPLICATE_KEY` | A duplicate JSON key makes the manifest interpretation ambiguous. | Recollect | Collect a new manifest from the pinned dbt build; do not repair it by hand. | [Recover file, JSON, or schema inputs](../how-to/diagnose-an-invalid-artifact-pair.md#recover-file-json-or-schema-inputs) |
| `DBT_RUN_RESULTS_JSON_DUPLICATE_KEY` | A duplicate JSON key makes the run-results interpretation ambiguous. | Recollect | Collect new run results from the pinned dbt build; do not repair them by hand. | [Recover file, JSON, or schema inputs](../how-to/diagnose-an-invalid-artifact-pair.md#recover-file-json-or-schema-inputs) |
| `DBT_MANIFEST_JSON_NESTING_LIMIT_EXCEEDED` | The manifest exceeds the bounded JSON nesting policy. | Recollect | Collect a normal unmodified manifest from the pinned dbt build. | [Recover file, JSON, or schema inputs](../how-to/diagnose-an-invalid-artifact-pair.md#recover-file-json-or-schema-inputs) |
| `DBT_RUN_RESULTS_JSON_NESTING_LIMIT_EXCEEDED` | The run-results file exceeds the bounded JSON nesting policy. | Recollect | Collect normal unmodified run results from the pinned dbt build. | [Recover file, JSON, or schema inputs](../how-to/diagnose-an-invalid-artifact-pair.md#recover-file-json-or-schema-inputs) |
| `DBT_MANIFEST_SCHEMA_INVALID` | The manifest does not satisfy the vendored dbt manifest v12 schema. | Recollect or compatibility review | Re-run the pinned dbt build and collect its unmodified manifest.json. | [Recover file, JSON, or schema inputs](../how-to/diagnose-an-invalid-artifact-pair.md#recover-file-json-or-schema-inputs) |
| `DBT_RUN_RESULTS_SCHEMA_INVALID` | The run-results file does not satisfy the vendored dbt run-results v6 schema. | Recollect or compatibility review | Re-run the pinned dbt build and collect its unmodified run_results.json. | [Recover file, JSON, or schema inputs](../how-to/diagnose-an-invalid-artifact-pair.md#recover-file-json-or-schema-inputs) |
| `DBT_SCHEMA_VERSION_UNSUPPORTED` | The files are not the exact artifact-schema pair qualified by P1.1. | Unsupported compatibility | Use manifest v12 and run-results v6, or qualify a new pair before inspection. | [Recover file, JSON, or schema inputs](../how-to/diagnose-an-invalid-artifact-pair.md#recover-file-json-or-schema-inputs) |
| `DBT_CORE_VERSION_UNSUPPORTED` | The files were not both produced by the qualified dbt Core version. | Unsupported compatibility | Run the supported job with dbt-core 1.11.12 and collect both artifacts again. | [Recover file, JSON, or schema inputs](../how-to/diagnose-an-invalid-artifact-pair.md#recover-file-json-or-schema-inputs) |
| `DBT_INVOCATION_ID_INVALID` | The files cannot be bound to one parseable dbt invocation. | Recollect pair | Collect both closed artifacts from one completed pinned dbt build invocation before another dbt command runs. | [Recover pair metadata](../how-to/diagnose-an-invalid-artifact-pair.md#recover-pair-metadata) |
| `DBT_INVOCATION_ID_MISMATCH` | The files do not have the same dbt invocation identity. | Recollect pair | Collect both closed artifacts from one completed pinned dbt build invocation before another dbt command runs. | [Recover pair metadata](../how-to/diagnose-an-invalid-artifact-pair.md#recover-pair-metadata) |
| `DBT_ADAPTER_TYPE_UNSUPPORTED` | The manifest is not from the qualified Databricks adapter path. | Unsupported compatibility | Use the pinned dbt-databricks job or qualify another adapter separately. | [Recover pair metadata](../how-to/diagnose-an-invalid-artifact-pair.md#recover-pair-metadata) |
| `DBT_COMMAND_UNSUPPORTED` | The result artifact is not evidence from the supported primary dbt build command. | Unsupported compatibility | Run the approved named-selector dbt build and collect that run_results.json. | [Recover pair metadata](../how-to/diagnose-an-invalid-artifact-pair.md#recover-pair-metadata) |
| `DBT_EMPTY_EXECUTION` | An empty result array does not satisfy the supported execution contract. | Correct and rerun | Fix the selector or executable-node set, then run the pinned dbt build again. | [Recover result evidence](../how-to/diagnose-an-invalid-artifact-pair.md#recover-result-evidence) |
| `DBT_RESULTS_DUPLICATE_ID` | One dbt resource appears more than once in the execution results. | Recollect pair | Collect a fresh unmodified artifact pair from the pinned dbt build. | [Recover result evidence](../how-to/diagnose-an-invalid-artifact-pair.md#recover-result-evidence) |
| `DBT_RESULT_ID_UNRESOLVED` | An executed result cannot be resolved to the supported manifest inventory. | Recollect pair | Collect manifest.json and run_results.json from the same build invocation. | [Recover result evidence](../how-to/diagnose-an-invalid-artifact-pair.md#recover-result-evidence) |
| `DBT_RESULT_ID_UNSUPPORTED_RESOURCE` | A result resolves only to a resource type that P1.1 does not accept for build results. | Unsupported compatibility | Use the supported dbt build contract or qualify this evidence type separately. | [Recover result evidence](../how-to/diagnose-an-invalid-artifact-pair.md#recover-result-evidence) |
| `DBT_RESULT_ID_AMBIGUOUS` | A result identifier has more than one possible manifest resource. | Recollect pair | Collect a fresh unmodified artifact pair; do not choose a resource manually. | [Recover result evidence](../how-to/diagnose-an-invalid-artifact-pair.md#recover-result-evidence) |
| `DBT_MANIFEST_RESOURCE_ID_MISMATCH` | A matched manifest resource contradicts its enclosing identifier. | Recollect pair | Collect a fresh unmodified manifest from the pinned dbt build. | [Recover result evidence](../how-to/diagnose-an-invalid-artifact-pair.md#recover-result-evidence) |
| `DBT_RESULT_RESOURCE_TYPE_UNSUPPORTED` | A matched manifest collection contains a resource type that BuildTask does not accept. | Unsupported compatibility | Collect a fresh pair from the pinned build or qualify the resource type separately. | [Recover result evidence](../how-to/diagnose-an-invalid-artifact-pair.md#recover-result-evidence) |
| `DBT_RESULT_STATUS_UNSUPPORTED` | The native dbt status is not valid for the matched resource type. | Unsupported compatibility | Collect a fresh pair from the pinned build; do not reinterpret the status. | [Recover result evidence](../how-to/diagnose-an-invalid-artifact-pair.md#recover-result-evidence) |
| `DBT_TIMING_INVALID` | The artifact contains a timing value that cannot represent elapsed execution time. | Recollect | Collect a fresh unmodified run_results.json from the pinned dbt build. | [Recover numeric evidence](../how-to/diagnose-an-invalid-artifact-pair.md#recover-numeric-evidence) |
| `DBT_FAILURE_COUNT_INVALID` | The artifact contains a negative dbt failure count. | Recollect | Collect a fresh unmodified run_results.json from the pinned dbt build. | [Recover numeric evidence](../how-to/diagnose-an-invalid-artifact-pair.md#recover-numeric-evidence) |

<!-- END: issue-registry -->

Codes, text, primary-selection precedence, and JSON shape are versioned contract. Adding or changing one requires a reviewed contract version decision.

Result compatibility issues use the exact [BuildTask result compatibility matrix](python-api.md#buildtask-result-compatibility). P1.1's pre-release correction to invocation recovery text is recorded in [Decision 0002](../../decisions/0002-correct-p1.1-invocation-recovery-text.md).
