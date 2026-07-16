# Wire a supported dbt Job

Use this guide when you want a dbt Core task to leave a native Databricks artifact archive that dbtobsb can collect.

The P2 preview supports Jobs created from the repository pattern. It does not scan or rewrite arbitrary existing Jobs.

## Use one artifact-producing dbt invocation

Pin the qualified versions and keep the build selector fixed:

```yaml
environments:
  - environment_key: dbt
    spec:
      client: "4"
      dependencies:
        - dbt-core==1.11.12
        - dbt-databricks==1.12.2
        - dbt-adapters==1.24.5
        - dbt-common==1.37.5
        - dbt-spark==1.10.3
        - dbt-protos==1.0.541
        - databricks-sdk==0.117.0
        - databricks-sql-connector==4.3.0
```

Use the generated command shape:

```text
dbt --no-send-anonymous-usage-stats \
  --no-upload-to-artifacts-ingest-api \
  --write-json \
  --log-format-file json \
  --log-level-file info \
  --log-path logs/dbtobsb-primary \
  --no-use-colors \
  build --target-path target --selector observability_demo
```

The P2 Bundle pins this selector and dependency combination. The artifact
validator enforces the exact selector plus the artifact-attested dbt Core
version and adapter type; artifacts do not attest every installed transitive
distribution. Any selector, package-version, or dependency-resolution change
requires a new compatibility qualification.

These flags do four jobs:

- `--write-json` produces `manifest.json` and, once execution reaches that point, `run_results.json`;
- `--target-path target` gives Databricks one known artifact directory to archive;
- `--log-path logs/dbtobsb-primary` gives the native task archive one known file-log directory; and
- the two telemetry flags keep dbt usage data and artifact upload disabled.

Do not run a second dbt command into the same `target` directory before collection. A later command can overwrite the first invocation's primary artifacts. Use one task per observed invocation.

## Add the collector edge

Define the collector as a separate unscheduled Job. From the observed Job, invoke it with a Run Job task after the dbt task:

```yaml
- task_key: collect_dbt_evidence
  depends_on:
    - task_key: dbt_build
  run_if: ALL_DONE
  run_job_task:
    job_id: ${resources.jobs.dbtobsb_collector.id}
    job_parameters:
      workspace_id: "{{workspace.id}}"
      observed_job_id: "{{job.id}}"
      observed_job_run_id: "{{job.run_id}}"
      dbt_task_run_id: "{{tasks.dbt_build.run_id}}"
      observed_task_key: dbt_build
      repair_count: "{{job.repair_count}}"
      execution_count: "{{tasks.dbt_build.execution_count}}"
      catalog: ${var.evidence_catalog}
      schema: ${var.evidence_schema}
      raw_volume_name: ${var.raw_volume_name}
```

`ALL_DONE` is essential: a failed dbt task can still leave useful partial evidence. Native [dynamic value references](https://learn.microsoft.com/en-us/azure/databricks/jobs/dynamic-value-references) correlate the collector with the exact parent Job, task, and task run. The collector cross-checks those values against the Jobs API before accepting the artifact link.

Do not ask an operator to copy a Job ID, run ID, task-run ID, Volume path, selector, or SQL statement. Do not expose these values as free-form App inputs.

## Keep the preview destination controlled

The installed demo passes one catalog, evidence schema, and managed Volume automatically. In P2 these remain overridable Job parameters, so this is a trusted personal/test convention rather than a sealed authorization boundary. Restrict Run Now and Run Job access accordingly. A production release must bind these names to signed installed configuration and reject caller overrides before any write.

Before enabling the edge, run the fixed bootstrap once against that destination. The bootstrap may create the product objects in production when an authorized administrator deliberately targets a production catalog. Ordinary collection remains `RUNTIME_DML_ONLY` and has no flag that enables DDL.

## Understand what is captured

Azure Databricks makes the dbt task's output archive available through Jobs run output. Databricks documents that dbt task artifacts are available after the task, including files written under the target directory ([Azure dbt task documentation](https://learn.microsoft.com/en-us/azure/databricks/jobs/how-to/use-dbt-in-workflows)).

The observed live archive contained:

```text
target/manifest.json
target/run_results.json
target/semantic_manifest.json
logs/dbtobsb-primary/dbt.log
```

dbtobsb preserves the complete archive with restricted access. It parses only `manifest.json` and `run_results.json` for the P2 evidence tables. It does not normalize `dbt.log`, compiled SQL, relation names, adapter responses, or environment values.

## Verify the result

Run the Job and query the two read views:

```sql
SELECT capture_state, pair_state, lakeflow_result_state, issue_code
FROM `<catalog>`.`<schema>`.`dbt_run_health`
ORDER BY task_start_time DESC;
```

For a complete pair, `capture_state` is `COMPLETE` and `pair_state` is `PAIR_VALID`. A failed dbt build can still have those evidence states; inspect `lakeflow_result_state` and node statuses separately.

If capture is not complete, follow [Recover a non-complete capture](recover-capture-states.md).
