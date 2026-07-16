# Recover a non-complete capture

Use this guide when a row in `dbt_run_health` is not `COMPLETE` and `PAIR_VALID`.

Do not edit, reconstruct, or manually pair raw dbt artifacts. Preserve the original evidence row and fix the producing Job or collector path for the next attempt.

## 1. Read all three outcomes

```sql
SELECT
  task_start_time,
  lakeflow_result_state,
  retrieval_state,
  capture_state,
  pair_state,
  issue_code,
  logs_truncated
FROM `<catalog>`.`<schema>`.`dbt_run_health`
ORDER BY task_start_time DESC;
```

Interpret the columns independently:

- `lakeflow_result_state` is the Databricks task result;
- `retrieval_state` says whether the native archive was downloaded;
- `capture_state` says what primary artifacts the archive contained and whether they were safe to inspect; and
- `pair_state` says whether the two primary JSON documents passed the pinned dbt schema and cross-file contract.

A successful Lakeflow task does not prove complete evidence. A failed Lakeflow task does not imply invalid evidence.

## 2. Match the capture state

| Capture state | Meaning | Next action |
| --- | --- | --- |
| `ARCHIVE_UNAVAILABLE` | No usable native artifact link was obtained or downloaded. | Check `issue_code`, then run a new dbt attempt after fixing access or transport. Do not invent artifacts. |
| `NOT_PRODUCED` | The archive was retrieved but neither primary artifact was present. | Confirm `--write-json`, the exact `target` path, and that dbt reached artifact production. |
| `PARTIAL` | A valid manifest was present but `run_results.json` was not produced. | Treat this as real early-failure evidence. Fix the dbt failure and run a new attempt. |
| `INVALID_CAPTURE_CONTRACT` | The archive or primary documents violated a safety, schema, duplicate, or cross-file rule. | Quarantine the raw archive to its restricted support path. Do not publish its fields or weaken validation. |
| `COMPLETE` | Both primary artifacts were present and accepted. | Continue with `pair_state` and the native dbt outcome. |

Common unavailable codes include `DBT_ARCHIVE_LINK_UNAVAILABLE`, `DBT_ARCHIVE_LINK_EXPIRED_OR_DENIED`, `DBT_ARCHIVE_TRANSPORT_UNAVAILABLE`, and `DBT_ARCHIVE_LINK_NOT_HTTPS`. Retrieval links are ephemeral; the product never persists or logs their signed query or headers.

## 3. Check the Job shape

For `NOT_PRODUCED` or `PARTIAL`, compare the deployed task with [Wire a supported dbt Job](wire-a-dbt-job.md):

- one dbt invocation per task;
- `--write-json`;
- `--target-path target`;
- `--log-path logs/dbtobsb-primary`;
- a fixed selector; and
- an `ALL_DONE` collector edge using native dynamic references.

Do not add a cleanup step between the dbt task and collector. Do not reuse the same target directory for multiple dbt commands.

## 4. Preserve invalid evidence

When retrieval succeeded, the exact archive is already stored in the restricted managed Volume before parsing. Keep access to that Volume and `dbt_artifact_registry` narrower than access to the health views.

The P2 preview does not provide a supported raw-artifact export or automated retention workflow. If policy requires investigation, an authorized custodian should follow the customer's approved Databricks procedure without copying content into an issue, chat, email, or ordinary support ticket.

## 5. Run a new attempt

After correcting the source Job or permission, run the observed Job again. The new Databricks task-run ID creates a new immutable attempt key. The old row remains as evidence of the original outcome.

Re-running the collector for an identical attempt is idempotent. If the normalized content for the same attempt key changes, publication fails with `DBTOBSB_ATTEMPT_ROOT_CONFLICT`; it does not overwrite the first record.

## 6. Escalate contract failures

Escalate when:

- the same supported version pair repeatedly produces `INVALID_CAPTURE_CONTRACT`;
- an archive link is repeatedly denied before its first collector attempt;
- an identical replay conflicts; or
- a `COLLECTING` registry row cannot complete after the original child rows are verified.

Share only the static `issue_code`, supported versions, sanitized state columns, and an approved archive hash. Raw artifacts, SQL, messages, IDs, signed links, and Volume locators stay in the customer's restricted Databricks boundary.
