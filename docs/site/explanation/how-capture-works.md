# How capture works

dbtobsb adds an evidence path around a normal dbt build. It does not replace dbt's
own results or Databricks' native Job history.

The complete path is shown below. The collector starts after dbt even when the dbt
task fails.

```text
Observed Job -> dbt build -> staging Volume
      |
      +---- after dbt ----> Collector <---- staged files
                                |
                    +-----------+-----------+
                    |                       |
              raw archive          normalized tables
                                            |
                                    three health views
                                       /          \
                              read-only App   Databricks SQL
```

## The observed Job runs dbt

Installation copies and seals one approved project. At runtime, the observed Job:

1. checks the installed project and policy;
2. runs the fixed `dbt build` command without a shell;
3. writes files to a task-local attempt directory;
4. uploads only `manifest.json`, `run_results.json`, and bounded structured logs;
5. reads each uploaded file back and verifies its size and SHA-256 hash; and
6. returns dbt's exit code.

The paths include the Databricks task attempt, so a retry or repair does not
overwrite earlier evidence.

## The collector handles evidence

The collector runs after the dbt task whether dbt succeeds or fails. It:

1. verifies the parent Job, task, attempt, installed source, and runtime policy;
2. reads only the fixed files from the staging Volume;
3. builds one deterministic bounded archive;
4. writes and reads back the exact archive in the restricted raw Volume;
5. validates archive safety and the pinned dbt JSON schemas;
6. checks that both primary files belong to the same invocation; and
7. writes allowlisted fields to the evidence tables.

The exact archive is preserved before parsing, so invalid or partial evidence is
not silently discarded.

## Readers use curated views

The App and normal SQL users read three views:

- run health;
- node health; and
- collection health.

They do not receive raw SQL, log messages, archive paths, adapter responses, or
environment values.
