# Query observability data

Use the three health views for normal investigation. Replace `<catalog>` and
`<evidence-schema>` in each query with the values selected during installation.

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
ORDER BY task_start_time DESC;
```

Read the result in this order:

1. `lakeflow_result_state` — did the Databricks task succeed?
2. `retrieval_state` — did the collector obtain the staged files?
3. `capture_state` — which primary artifacts were present and safe to inspect?
4. `pair_state` — did the two dbt JSON files form a valid pair?

## Summarize dbt nodes

```sql
SELECT
  resource_type,
  status,
  COUNT(*) AS node_count,
  ROUND(SUM(execution_time), 3) AS execution_seconds
FROM `<catalog>`.`<evidence-schema>`.`dbt_node_health`
GROUP BY resource_type, status
ORDER BY resource_type, status;
```

This view contains one allowlisted row for each accepted model, seed, test, and
other supported dbt result. It does not expose compiled SQL or raw messages.

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
ORDER BY task_start_time DESC;
```

`PUBLISHED` with no issue means normalized evidence was committed and read back.
For any other state, follow [Recover missing evidence](recover-missing-evidence.md).

## Keep restricted data restricted

Normal readers should query only the three health views. The four backing tables
and two Volumes contain operational identifiers, archive locations, or raw dbt
evidence and need narrower access.
