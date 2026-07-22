# Recover missing evidence

Use this guide when an observed dbt run has no published collection or when
`dbt_collection_health` is not `PUBLISHED`.

Do not edit artifacts, enter a run ID, widen the scan window, or reset a collection
row.

## Before you begin

You need a Databricks SQL warehouse you are allowed to use, `SELECT` on
`dbt_collection_health`, and membership in the installed Job-manager group. Open a
Databricks SQL editor and replace `<catalog>` and `<evidence-schema>` below with the
values selected during installation.

## 1. Check the collection state

```sql
SELECT
  task_start_time,
  collector_state,
  collection_issue_code,
  collection_attempt_count,
  last_attempted_at,
  last_reconciliation_run_id,
  CASE
    WHEN last_attempted_at IS NULL THEN true
    ELSE current_timestamp() >= last_attempted_at + INTERVAL 20 MINUTES
  END AS recovery_lease_ready
FROM `<catalog>`.`<evidence-schema>`.`dbt_collection_health`
ORDER BY task_start_time DESC;
```

Use this table:

| State | What to do |
| --- | --- |
| `PUBLISHED` | No collection action is needed. |
| `DISCOVERED` | Run the fixed reconciler once. |
| `COLLECTING` | Wait until `recovery_lease_ready` is `true`, then run the reconciler once. |
| `RETRYABLE` | Run the reconciler once. Fewer than three attempts have been used. |
| `TERMINAL_FAILURE` | Stop retrying and escalate the safe issue code. |

See [Statuses and issue codes](../reference/statuses-and-issues.md) for the meaning
of each state and code. Do not run the reconciler while
`recovery_lease_ready` is `false`.

If the query returns no row for a completed observed run from the last 24 hours,
run the reconciler once. Version `0.5.0` cannot discover a run after that 24-hour
window. If an older run is absent, preserve only its safe identifiers and escalate;
do not widen the scan or create a row by hand.

## 2. Run the reconciler

In **Databricks Jobs & Pipelines**:

1. Open `dbtobsb-reconciler`.
2. Confirm its schedule is **Paused** and no run is active.
3. Select **Run now** without parameters or overrides.
4. Wait for the run to finish.

The reconciler checks at most 100 parent runs from the previous 24 hours, at most
500 task runs, and at most 20 eligible collection attempts. It uses serverless
compute and has a 15-minute task timeout.

Open the completed run's **Output** panel. A successful output looks like this:

```json
{
  "attempted": 1,
  "backlog": false,
  "discovered": 1,
  "event": "dbtobsb_reconciliation_completed",
  "published": 1,
  "retryable": 0,
  "terminal_failure": 0
}
```

If `backlog` is `true`, wait for the run to become terminal and run the unchanged
Job again.

## 3. Check the final row

Run the first query again. A recovered attempt is `PUBLISHED`, has no issue, and
shows the reconciliation run in `last_reconciliation_run_id`.

If the Job prints `denied` or the row reaches `TERMINAL_FAILURE`, preserve only the
static issue code and sanitized states. Do not paste native exceptions, SQL, logs,
artifact paths, or raw files into an ordinary support ticket.

## 4. Finish safely

Confirm the reconciler run is terminal and its schedule is still paused. Serverless
Job compute stops when the run ends. If you opened the App, use
[`dbtobsb stop`](stop-or-uninstall.md#stop-compute) because closing the browser does
not stop it.
