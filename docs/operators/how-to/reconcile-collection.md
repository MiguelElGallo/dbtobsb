# Reconcile missing dbt evidence

Use the fixed `dbtobsb-reconciler` Job to discover and retry supported dbt attempts without
entering Job IDs, paths, selectors, flags, SQL, or destination values.

## Before you start

You must belong to the customer group installed as `job_manager_group_name`. The Bundle grants
that group `CAN_MANAGE` on the reconciler Job. The Job uses serverless compute and has a fixed
15-minute run/task timeout. Platform startup and billing records determine actual billable usage;
the timeout is not a billed-duration ceiling. The 15-minute schedule is installed **paused**. A
manual run does not unpause it.

The supported first release scans at most 100 completed parent runs that started in the preceding
24 hours, at most 500 task-run IDs, and attempts collection for at most 20 eligible task attempts
per reconciliation run. Between zero and 20 may reach `PUBLISHED`.
A repair of a parent that started more than 24 hours ago is outside this release's automatic
reconciliation window and must be escalated; do not widen the scan or supply an older run ID.

## Run the fixed reconciliation

1. In **Databricks Jobs & Pipelines**, open the installed Job named `dbtobsb-reconciler`.
2. Confirm its schedule is **Paused** and there is no active reconciler run. If a run is active,
   wait for it to become terminal. If the schedule is unpaused, do not edit or run the Job; ask the
   customer group installed as `job_manager_group_name` to restore the reviewed Job definition.
3. Select **Run now**. Do not add parameters or overrides.
4. Wait for the run to become terminal. The fixed Job timeout is 15 minutes.
5. Open the run output and look for one sanitized event like this:

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

The counts contain no SQL, artifact paths, log text, or raw Personal Data. `backlog: true` means
the bounded run found more eligible work than it was allowed to replay; run the same fixed Job
again after the current run is terminal.

The counters have fixed meanings:

- `discovered` is the number of supported task-attempt contexts in the bounded scan;
- `attempted` is the number of collection attempts claimed by this reconciler execution;
- `published` is the number of collection calls that returned successfully, not an exclusively
  attributed count of row transitions;
- `retryable` is the number of failed calls left eligible for another bounded attempt;
- `terminal_failure` includes matching rows already terminal plus rows newly made terminal; and
- `backlog` says more eligible work remained after the 20-attempt limit.

## Check the result

Open the dbtobsb App only if you accept that App compute is already running and the read can
auto-start its bound SQL warehouse. On **Collection health**, match the Lakeflow reconciliation
Run ID to the **Reconciliation run** column. The **Task run** column identifies each affected dbt
attempt. Verify final state separately: a healthy completed attempt is `PUBLISHED` with issue
`None`. Do not use the aggregate `published` counter as exclusive transition attribution when a
direct collector could overlap.

| State | Meaning | Next action |
| --- | --- | --- |
| `PUBLISHED` | The normalized evidence and publication sentinel agree. | No collection action. |
| `DISCOVERED` | The attempt was found but not yet claimed. | Run the fixed reconciler again. |
| `COLLECTING` | A claim is active or still inside its 20-minute recovery lease. | Wait 20 minutes, then run the fixed reconciler once. |
| `RETRYABLE` | A bounded attempt failed and fewer than three attempts were used. | Run the fixed reconciler again. |
| `TERMINAL_FAILURE` | Three attempts failed. | Escalate the displayed safe issue code; do not reset the row. |

The App's `/api/v1/collection` endpoint exposes the same sanitized state. Reading it has the same
SQL-warehouse auto-start and cost effect as loading the observability page.

## If the Job output says `denied`

Use the code shown in the Job output. Do not copy native exception text into tickets.

| Codes | Responsible actor | Action |
| --- | --- | --- |
| `DBTOBSB_DEPLOYMENT_BINDING_NOT_FINALIZED`, `DBTOBSB_DELTA_INSTALLATION_BINDING_MISMATCH`, `DBTOBSB_DELTA_ATTEMPT_BINDING_MISMATCH` | Deployment/seal verifier | Stop collection and follow [Reconcile an installation](reconcile-installation.md). |
| `DBTOBSB_RECONCILIATION_BINDING_MISMATCH`, `DBTOBSB_RECONCILIATION_MANIFEST_MISMATCH` | Deployment/seal verifier | Follow [Reconcile an installation](reconcile-installation.md). |
| `DBTOBSB_RECONCILIATION_PARENT_LIMIT_EXCEEDED`, `DBTOBSB_RECONCILIATION_TASK_LIMIT_EXCEEDED` | Data operator | Stop retrying. Wait for the rolling 24-hour window to fall below the fixed bound, or escalate the code. |
| `DBTOBSB_RECONCILIATION_PARENT_PAGINATION_INVALID`, `DBTOBSB_RECONCILIATION_PARENT_INVALID`, `DBTOBSB_RECONCILIATION_TASK_CONTEXT_INVALID` | Data operator | Stop retrying and escalate the code as a Jobs-evidence compatibility incident. |
| `DBTOBSB_RECONCILIATION_FAILED` | Data operator | Stop retrying and escalate this sanitized catch-all code. |

## If Collection health shows an issue

These codes are stored in the **Issue** column; they are not reconciliation Job-output codes.

| Codes | Responsible actor | Action |
| --- | --- | --- |
| `DBT_JOBS_DBT_SOURCE_UNSUPPORTED`, `DBT_JOBS_DBT_PROJECT_BINDING_MISMATCH`, `DBT_JOBS_DBT_COMMAND_CONTRACT_MISMATCH`, `DBT_JOBS_DBT_ENVIRONMENT_CONTRACT_MISMATCH`, `DBT_JOBS_DBT_TARGET_BINDING_INVALID`, `DBT_JOBS_DBT_TASK_POLICY_MISMATCH`, `DBT_JOBS_DBT_OVERRIDE_UNSUPPORTED`, `DBT_JOBS_INSTALLED_JOB_BINDING_MISMATCH`, `DBT_JOBS_INSTALLED_COLLECTOR_BINDING_MISMATCH`, `DBT_JOBS_DBT_SOURCE_ATTESTATION_FAILED`, `DBT_JOBS_WORKSPACE_BINDING_MISMATCH`, `DBT_JOBS_RESOLVED_ATTEMPT_BINDING_MISMATCH`, `DBT_JOBS_DBT_CONFIGURATION_NOT_READY` | Deployment/seal verifier | Stop retrying and follow [Reconcile an installation](reconcile-installation.md). |
| `DBT_JOBS_PARENT_CORRELATION_MISMATCH`, `DBT_JOBS_PARENT_PAGINATION_INVALID`, `DBT_JOBS_TASK_CORRELATION_MISMATCH`, `DBT_JOBS_TASK_NOT_TERMINAL`, `DBT_JOBS_TASK_RESULT_UNAVAILABLE`, `DBT_JOBS_OUTPUT_CORRELATION_MISMATCH`, `DBT_JOBS_EVIDENCE_FAILED` | Data operator | Confirm the observed dbt Job is terminal, then run the unchanged reconciler once. If the state reaches `TERMINAL_FAILURE`, stop retrying and escalate the code. |
| `DBTOBSB_ATTEMPT_ROOT_CONFLICT`, `DBTOBSB_ATTEMPT_ROOT_WRITE_INDETERMINATE`, `DBTOBSB_CHILD_READBACK_MISMATCH`, `DBTOBSB_PUBLISH_SENTINEL_NOT_COMMITTED`, or another displayed collection issue | Data operator | Stop retrying and preserve the three evidence tables for investigation. |

## If the App cannot load Collection health

App codes appear in the App UI or `/api/v1/collection`; they are not stored collection issues.

| Codes | Responsible actor | Action |
| --- | --- | --- |
| `DBTOBSB_APP_QUERY_FAILED` | Data operator, then deployment/seal verifier | Check that the dedicated App warehouse is available and reload once. If the same code persists, stop retrying and route the code to the deployment/seal verifier; do not repair App identity or bindings. |
| An App configuration, binding, authentication, or view-contract code | Deployment/seal verifier | Follow [Reconcile an installation](reconcile-installation.md). |

## Finish safely

Confirm the manual reconciler run is terminal and its schedule is still paused. A serverless Job run
stops its own compute when terminal. If you opened the App, remember that closing the browser does
not stop App compute or the bound SQL warehouse. Stop only product-owned test compute that you are
authorized to stop; do not stop, resize, or delete a shared customer warehouse or unrelated
resource.
