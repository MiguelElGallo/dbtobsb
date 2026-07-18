# Statuses and issue codes

dbtobsb keeps different outcomes in different fields. Read each field for the
question it answers.

## Retrieval

| State | Meaning |
| --- | --- |
| `RETRIEVED` | The collector acquired the approved staged files and assembled the bounded archive. |
| `UNAVAILABLE` | The collector could not acquire valid staged input. Read `issue_code`. |

## Capture

| State | Meaning | Next action |
| --- | --- | --- |
| `COMPLETE` | Both primary artifacts were present and accepted. | Read `pair_state` and dbt statuses. |
| `PARTIAL` | A valid manifest exists but `run_results.json` was not produced. | Treat it as early-failure evidence and run a new attempt after fixing dbt. |
| `NOT_PRODUCED` | Neither primary artifact was produced. | Check the dbt startup failure and the sealed output configuration. |
| `ARCHIVE_UNAVAILABLE` | Staged evidence could not be read and assembled. | Fix runner, Volume, or Files API access, then run a new dbt attempt. |
| `INVALID_CAPTURE_CONTRACT` | The archive or files broke a safety, schema, duplicate, or cross-file rule. | Preserve the raw archive and escalate the safe code. Do not weaken validation. |

## Artifact pair

| State | Meaning |
| --- | --- |
| `PAIR_VALID` | The manifest and run results satisfy the pinned schemas and belong to one invocation. |
| `PAIR_INVALID` | One or more pair rules failed. Use the static issue code and action. |

`PAIR_VALID` does not mean that every dbt node succeeded.

## Collection

| State | Meaning | Next action |
| --- | --- | --- |
| `DISCOVERED` | Reconciliation found the attempt. | Run the fixed reconciler. |
| `COLLECTING` | A collector owns the current recovery lease. | Wait for the 20-minute lease before retrying. |
| `RETRYABLE` | A bounded attempt failed and fewer than three tries were used. | Run the fixed reconciler once. |
| `TERMINAL_FAILURE` | Three attempts failed or a non-retryable conflict occurred. | Stop and escalate the code. |
| `PUBLISHED` | Normalized evidence and readback agree. | No collection action. |

## Structured logs

Log state is separate from primary-artifact state:

`UNAVAILABLE`, `NOT_INITIALIZED`, `TRUNCATED`, `MALFORMED`, `MISSING`,
`UNKNOWN_VERSION`, `ARTIFACT_INVOCATION_MISMATCH`, or `VALID`.

A log problem does not silently change a valid artifact pair. It remains visible as
its own evidence.

## Common code families

| Prefix or family | Owner | Action |
| --- | --- | --- |
| `DBTOBSB_DBT_RUNNER_*` | Administrator or dbt owner | Fix the sealed runtime, authentication, command, upload, or readback problem before a new run. |
| `DBT_VOLUME_ARTIFACT_*` | Administrator | Check staging Volume access and bounded file metadata. |
| `DBT_JOBS_*` | Administrator or Job operator | Check the installed Job shape, task state, and native correlation. Do not enter replacement IDs. |
| `DBTOBSB_RECONCILIATION_*` | Job operator, then administrator | Follow the fixed reconciliation guide. Stop after a denied or terminal result. |
| `DBTOBSB_APP_*` | Administrator | Keep the App read-only and check its configuration, binding, warehouse, or view contract. |
| `DBTOBSB_ATTEMPT_ROOT_CONFLICT` | Administrator and evidence custodian | Preserve the original rows and raw archive. Do not overwrite the attempt. |

Share only the static code, supported versions, sanitized states, counts, and an
approved hash prefix. Do not share raw artifacts, logs, SQL, identifiers, archive
locations, or native exception text in an ordinary ticket.
