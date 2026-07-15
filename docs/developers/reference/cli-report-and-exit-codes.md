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

## Machine report

The top-level fields are:

| Field | Meaning |
| --- | --- |
| `schema_version` | Exactly `dbtobsb.artifact-pair-report.v1`. |
| `pair_state` | `PAIR_VALID` or `PAIR_INVALID`. |
| `summary` | Allowlisted pair facts for a valid pair; otherwise `null`. |
| `issues` | Zero or more static issues, bounded to 20. |

The `summary` contains exact schema URLs, dbt version, adapter type, command, and a closed native-status count object. The result total is the sum of that object's integer values; the JSON omits a redundant total that could disagree. It contains no resource or invocation identity. Every issue contains only `code`, `component`, `field`, `observed_category`, `impact`, and `next_action`; observed evidence is never interpolated. `issues[0]` is the primary issue, so the JSON omits a second copy that could disagree.

The v1 schema is closed: it rejects invented status/code/text values, legacy redundant fields, and extra properties. Statuses are object keys, so one status cannot occur twice. Public Python constructors enforce the same vocabulary and canonical status ordering.

## Issue registry

| Stage | Codes |
| --- | --- |
| Size | `DBT_MANIFEST_SIZE_LIMIT_EXCEEDED`, `DBT_RUN_RESULTS_SIZE_LIMIT_EXCEEDED` |
| Strict JSON | `DBT_MANIFEST_JSON_INVALID`, `DBT_RUN_RESULTS_JSON_INVALID`, `DBT_MANIFEST_JSON_DUPLICATE_KEY`, `DBT_RUN_RESULTS_JSON_DUPLICATE_KEY`, `DBT_MANIFEST_JSON_NESTING_LIMIT_EXCEEDED`, `DBT_RUN_RESULTS_JSON_NESTING_LIMIT_EXCEEDED` |
| Full schema | `DBT_MANIFEST_SCHEMA_INVALID`, `DBT_RUN_RESULTS_SCHEMA_INVALID` |
| Pair metadata | `DBT_SCHEMA_VERSION_UNSUPPORTED`, `DBT_CORE_VERSION_UNSUPPORTED`, `DBT_INVOCATION_ID_INVALID`, `DBT_INVOCATION_ID_MISMATCH`, `DBT_ADAPTER_TYPE_UNSUPPORTED`, `DBT_COMMAND_UNSUPPORTED` |
| Results | `DBT_EMPTY_EXECUTION`, `DBT_RESULTS_DUPLICATE_ID`, `DBT_RESULT_ID_UNRESOLVED`, `DBT_RESULT_ID_UNSUPPORTED_RESOURCE`, `DBT_RESULT_ID_AMBIGUOUS`, `DBT_MANIFEST_RESOURCE_ID_MISMATCH`, `DBT_RESULT_RESOURCE_TYPE_UNSUPPORTED`, `DBT_RESULT_STATUS_UNSUPPORTED` |
| Numeric invariants | `DBT_TIMING_INVALID`, `DBT_FAILURE_COUNT_INVALID` |

Codes, text, precedence, and JSON shape are versioned contract. Adding or changing one requires a reviewed contract version decision.
