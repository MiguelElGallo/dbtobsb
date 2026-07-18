# Query observability data

Use the three health views for normal investigation. Open a Databricks SQL editor,
select a warehouse you are allowed to use, and run the queries as a user with
`SELECT` on the health views. Replace `<catalog>` and `<evidence-schema>` with the
values selected during installation.

## Check recent runs

```sql
SELECT
  task_start_time,
  lakeflow_result_state,
  retrieval_state,
  capture_state,
  pair_state,
  issue_code,
  dbt_version,
  command,
  result_count,
  status_counts_json
FROM `<catalog>`.`<evidence-schema>`.`dbt_run_health`
WHERE task_start_time >= current_timestamp() - INTERVAL 7 DAYS
ORDER BY task_start_time DESC
LIMIT 100;
```

Read the result in this order:

1. `lakeflow_result_state` — did the Databricks task succeed?
2. `retrieval_state` — did the collector obtain the staged files?
3. `capture_state` — which primary artifacts were present and safe to inspect?
4. `pair_state` — did the two dbt JSON files form a valid pair?

A successful dbt run with complete evidence has `SUCCESS`, `RETRIEVED`, `COMPLETE`,
and `PAIR_VALID` in those four columns. A failed dbt run can still have
`RETRIEVED`, `COMPLETE`, and `PAIR_VALID`; these fields describe different outcomes.
See [Why outcomes stay separate](../explanation/why-outcomes-stay-separate.md).

The [first-run tutorial](../tutorials/see-your-first-run.md#2-read-the-run-summary)
shows a real sanitized row captured from the Azure qualification workspace. If the
query returns no rows, first confirm that an observed Job has finished. Then use
[Recover missing evidence](recover-missing-evidence.md) if collection did not
publish.

## Summarize dbt nodes

```sql
SELECT
  resource_type,
  status,
  COUNT(*) AS node_count,
  ROUND(SUM(execution_time), 3) AS execution_seconds
FROM `<catalog>`.`<evidence-schema>`.`dbt_node_health`
WHERE task_start_time >= current_timestamp() - INTERVAL 7 DAYS
GROUP BY resource_type, status
ORDER BY resource_type, status;
```

This view contains one allowlisted row for each accepted model, seed, test, and
other supported dbt result. It does not expose compiled SQL or raw messages.
The [first-run node summary](../tutorials/see-your-first-run.md#3-see-model-seed-and-test-results)
shows real sanitized model, seed, and test counts.

## Check collection retries

```sql
SELECT
  task_start_time,
  collector_state,
  collection_issue_code,
  collection_attempt_count,
  last_attempted_at,
  published_at
FROM `<catalog>`.`<evidence-schema>`.`dbt_collection_health`
WHERE task_start_time >= current_timestamp() - INTERVAL 7 DAYS
ORDER BY task_start_time DESC
LIMIT 100;
```

`PUBLISHED` with no issue means normalized evidence was committed and read back.
For any other state, follow [Recover missing evidence](recover-missing-evidence.md).
The same real run produced `PUBLISHED`, no issue, and one collection attempt.

## Keep restricted data restricted

Normal readers should query only the three health views. The four backing tables
and two Volumes contain operational identifiers, archive locations, or raw dbt
evidence and need narrower access.

For the complete column contract, see [Evidence data](../reference/evidence-data.md).
