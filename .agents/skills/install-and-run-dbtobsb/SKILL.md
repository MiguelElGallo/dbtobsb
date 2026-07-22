---
name: install-and-run-dbtobsb
description: Fresh-install or safely resume dbtobsb v0.5.0 in Azure Databricks, run the approved installed dbt Core weather or qualification workload, prove model results, structured logs, collection state, and dashboard trends in customer-local evidence views, and finish with compute stopped. Use when a user asks an agent to install dbtobsb, run the demo or qualification project, make a first observed run, execute the v0.5 live qualification matrix, test capture end to end, or verify dbt observability after cloning this repository.
---

# Install and run dbtobsb

Complete one attended path from a clean clone to a captured dbt run. Assume the
user has the required authority, but never assume their workspace, resource, data,
cost, or retention choices.

## Enforce the platform gate

Run this skill only for an Azure Databricks workspace deployed in the customer's
Azure subscription and reached through its canonical
`https://adb-...azuredatabricks.net` per-workspace URL. Stop before local or cloud
mutation for AWS, GCP, Databricks Free Edition, or the retired Community Edition.
“Personal Edition” is not a current Databricks product name: Databricks sends
personal-use users to Free Edition, which dbtobsb does not support.

## Read the supported contract

Before acting, read these repository files:

1. `docs/site/how-to-guides/install-private-release.md`
2. `docs/site/how-to-guides/add-a-dbt-project.md`
3. `docs/site/tutorials/see-your-first-run.md`
4. `docs/site/how-to-guides/stop-or-uninstall.md`
5. `docs/site/reference/dbt-project-input.md`

Treat `docs/releases/v0.5.0-support-contract.md` and the packaged support manifest as authoritative when another
document is ambiguous. Do not use the legacy App-shell smoke path in `README.md`.

## Preserve the product boundaries

- v0.5.0 supports a fresh installation or resume of its own v2 state only. It has
  no upgrade, adoption, or legacy-install migration path. Reject a legacy v1 state,
  prior App, product Job, product object, or Terraform state before mutation.
- Use only the attended `dbtobsb bootstrap` installer and the installed
  `dbtobsb-observed` Job. Do not call the internal onboarding entry point.
- Do not run dbt directly, edit the generated Job, or accept a command, selector,
  Job ID, target path, log path, flag, variable, SQL statement, or compute override
  from the user.
- Discover the exact installed Job by name. Never use a user-supplied Job ID.
- Use only the fixed read-only verification queries in this skill. Substitute only
  the installer-approved catalog and schema after validating them as ordinary
  identifiers.
- Never display or retain raw logs, SQL, artifacts, tokens, local installer state,
  workspace URLs, operational IDs, or customer data in the final answer.
- Never delete evidence or uninstall unless the user separately requests it after
  the successful run.
- Keep the App stopped and the reconciler schedule paused. Create no schedule.

## 1. Perform read-only discovery

From the repository root:

1. Confirm the tracked worktree is clean. Require `installer/pyproject.toml` and
   the support manifest to identify v0.5.0, recompute the manifest canonical
   SHA-256 through `load_support_manifest()`, record the current 40-hex Git commit,
   and require the sealed official Databricks CLI 1.9.0 executable identity. Do not
   compare the source to a v0.3 tag or infer v0.5 integrity from a legacy release.
2. Check Python, `uv`, Databricks CLI, and `jq` against the supported-environment
   page.
3. Run `databricks auth profiles --output json`. Keep only valid Azure OAuth
   profiles whose canonical host matches
   `^https://adb-[0-9]{1,20}\.[0-9]{1,20}\.azuredatabricks\.net$`. Present every
   remaining profile and its workspace host; never select one automatically. If
   none remain, stop with the supported-platform explanation rather than offering
   an AWS, GCP, Free Edition, Community Edition, regional, or custom-URL profile.
4. After the user chooses a profile, verify it with `databricks auth describe` and
   `databricks current-user me` using the explicit `--profile` flag.
5. Read-only list the candidate active service principals, non-system groups, SQL
   warehouses, catalogs, schemas, and dbt projects that the installer can select.
6. Check for `.dbtobsb/release-installation-v2.json` without printing its contents.
   Preserve it. It may resume only when its release version, support-manifest
   digest, source commit, wheel identities, and CLI seal all match v0.5.0. Preserve
   but reject `.dbtobsb/release-installation-v1.json`; do not create an upgrade path.

Treat resource names, identities, the workspace host, and local state as sensitive
operational information. Show them only in the private attended choice prompt and
do not repeat them in the final receipt.

## 2. Ask before any mutation or paid compute

Ask one consolidated question and wait for all answers. Do not run `uv sync`,
`bootstrap`, a Job, the App, or a SQL query before this response.

Ask the user to choose or confirm:

1. **Workspace and Azure Databricks profile** — ask the user to confirm that the
   workspace is not Free Edition and choose one discovered named Azure profile;
   never `DEFAULT`. If they call it “Personal Edition”, explain that the current
   official personal-use offering is Free Edition and stop.
2. **dbt project** — recommend `examples/customer_weather` for one harmless model;
   offer `qualification_dbt` for the documented three-model, one-seed, five-test
   result; or accept another isolated child project that passes the input contract.
3. **Observed and collector service principals** — two different active discovered
   identities.
4. **Job-manager/App-viewer group** — one discovered non-system group.
5. **SQL warehouse** — one existing warehouse the observed principal may use; ask
   whether it is dedicated and may be stopped directly or is shared and must use
   its configured auto-stop.
6. **Empty evidence schema and dbt target schema** — the current actor owns the
   evidence schema; the observed principal owns the target schema. Their existing
   catalogs may differ, and the preview must show both fully qualified targets.
7. **Mutation scope** — allow the installer to create or verify the nine product
   objects in the evidence schema and allow dbt to create the chosen example's
   relations in the target schema.
8. **Compute scope and deadline** — allow bounded serverless installation Jobs,
   one bounded App deployment check plus stopped viewer-ACL readback, the exact approved observed-run workload,
   collector runs, and fixed SQL verification. Record the user's maximum elapsed
   and compute-hour windows.
9. **Finish state** — recommend leaving the installation present with the App
   stopped, reconciler paused, every product run terminal, and evidence retained.

Do not ask whether the user has administrator rights; assume that as requested.
Still let the installer verify identity, ownership, and access. If a required
resource is absent, stop and explain that v0.5.0 requires it to exist. Do not
provision a substitute or choose a different resource silently.

Summarize the answers without secrets or numeric IDs. Ask the user to confirm the
summary once unless they have already explicitly confirmed those choices. Do not
ask them to repeat an answer. This confirmation authorizes only the stated
installation and one run; it does not authorize deletion, retention changes, a
second run, or unrelated workspace changes.

Once the user authorizes the summarized installation-and-run task, answer the
installer's later confirmation prompts on their behalf. This includes typing
`APPROVE` at every matching preview without asking the user again. The task
authorization remains valid across clean retries and preview-digest changes while
the workspace, resource choices, mutations, workload, cost ceiling, and finish
state stay within the confirmed scope. If a preview materially expands that scope,
stop because the action is outside the authorized task, explain the difference,
and obtain direction for the expanded work.

## 3. Validate the chosen project locally

- For `examples/customer_weather`, require exactly the two source YAML files and
  the model shown in the preparation guide. Expect one successful model result.
- For `qualification_dbt`, treat its source `profiles.yml` as local qualification
  support only; confirm that the installer will ignore it. Expect three successful
  models, one successful seed, and five passing tests.
- For another project, enforce `docs/site/reference/dbt-project-input.md`. Require
  at least one executable selected node. Never repair the selector by changing the
  installed command.

Run the relevant local onboarding tests or project parse checks. Do not use cloud
compute for a failure that local validation can detect.

## 4. Run the attended installation

Run:

```console
uv sync --project installer --locked
uv run --project installer --no-sync dbtobsb bootstrap
```

Use a PTY and answer the installer's numbered prompts from the confirmed choices.
Do not pipe or prequeue answers.

When the installer displays **Installation preview**, pause. It must show one
canonical preview digest and the exact v0.5 release identity, fresh-state
classification, nine objects, grants, workspace ACL, three runtime Jobs, temporary
Jobs, four App resources and environment bindings, end-user ACL, project policy,
one bounded App deployment check plus stopped viewer-ACL readback, warehouse state/size/auto-stop and non-management
notice, cost boundary, and terminal finish state. Show the user that exact preview
without exposing numeric IDs or local state, then type `APPROVE` without asking
again when it matches the authorized task. A new digest by itself does not require
renewed authorization; compare the preview against the confirmed scope. The
installer must repeat the full read-only preflight and fail if the digest changes
before saving state or mutating anything.

If interrupted, run the same bootstrap command and let the installer resume. Never
delete or edit the state file. App deployment checks can be quiet for several
minutes. Inspect the live App deployment read-only if needed, but do not interrupt
or restart a still-running bootstrap merely because the terminal is quiet.
Continue only after the installation receipt identifies `INSTALLED`, App `STOPPED`,
and reconciler `PAUSED`; reject extra, missing, or mismatched lifecycle state.

## 5. Run the approved observed Job workload

For an ordinary first-run request, run exactly one observed Job. For an explicitly
approved v0.5 release qualification, run only the bounded cases in the v0.5 support
manifest, including two deterministic complete runs, one failure or partial-artifact
case, and missed-collection reconciliation. Never turn release qualification into
an unbounded extra run.

1. List Jobs using the exact name `dbtobsb-observed` and the confirmed profile.
   Require exactly one match.
2. Read the Job and require task keys `dbt_build` and `collect_dbt_evidence`, no
   active run, `max_concurrent_runs = 1`, and the installed service-principal
   run-as identity. Reject a mismatch instead of editing the Job.
3. Generate one idempotency token and keep it for this attempt. Invoke
   `databricks jobs run-now` on the discovered Job with the explicit profile,
   that token, no parameters, no JSON body, and no overrides. Wait up to the
   approved deadline.
4. If the response is lost or times out, do not create a second token or run.
   Reconcile the exact Job's active and recent runs first.
5. Require both tasks to become terminal. A failure in `dbt_build` does not permit
   skipping the collector check, but the selected dummy project's final acceptance
   requires a successful dbt task.

Do not print native run output or raw log text. Retain the derived parent run ID
only in memory for the fixed read-only verification.

## 6. Prove model and structured-log capture

Read the installed profile, warehouse ID, evidence catalog, and evidence schema
from the protected local state in memory. Do not print the file. Require the
catalog and schema to match `^[A-Za-z_][A-Za-z0-9_]{0,127}$` before interpolation.

Use the confirmed profile and installed warehouse with
`databricks experimental aitools tools query`. Send SQL through standard input,
not a shell argument. Bind the derived run ID as the named `LONG` parameter
`run_id`. Run only these fixed read-only queries.

Run evidence and structured-log health:

```sql
SELECT
  lakeflow_result_state,
  retrieval_state,
  capture_state,
  pair_state,
  structured_log_state,
  structured_log_file_count,
  structured_log_size_bytes,
  logs_truncated,
  result_count,
  status_counts_json,
  published_at
FROM `<catalog>`.`<evidence-schema>`.`dbt_run_health`
WHERE observed_job_run_id = :run_id
LIMIT 1
```

Require exactly one row with:

- `lakeflow_result_state = SUCCESS`;
- `retrieval_state = RETRIEVED`;
- `capture_state = COMPLETE`;
- `pair_state = PAIR_VALID`;
- `structured_log_state = VALID`;
- `structured_log_file_count >= 1` and `structured_log_size_bytes > 0`;
- `logs_truncated = false`; and
- `result_count >= 1`.

Run model outcomes:

```sql
SELECT resource_type, status, COUNT(*) AS node_count
FROM `<catalog>`.`<evidence-schema>`.`dbt_node_health`
WHERE observed_job_run_id = :run_id
GROUP BY resource_type, status
ORDER BY resource_type, status
```

Require at least one successful model. For `examples/customer_weather`, require one
successful model. For `qualification_dbt`, require exactly three successful models,
one successful seed, and five passing tests.

Run publication health:

```sql
SELECT collector_state, collection_issue_code, collection_attempt_count
FROM `<catalog>`.`<evidence-schema>`.`dbt_collection_health`
WHERE observed_job_run_id = :run_id
LIMIT 1
```

Require exactly one row with `collector_state = PUBLISHED`, a null issue, and at
least one collection attempt. These view rows—not raw log output—are the supported
proof that the model ran and its bounded structured logs were captured.

For v0.5 release qualification, also execute the exact fixed aggregate used by
the App over the newest approved run count. It must select only `PAIR_VALID` runs,
order newest-first inside the bounded CTE, join `dbt_run_health` to
`dbt_node_health` on workspace, observed Job, observed Job run, dbt task run, and
observed task key, count every `error` or `fail` node, count every model status,
group by the complete common attempt axes, and return oldest-first chart points.
Require one bounded point per selected accepted attempt, zero counts for an
accepted run with no matching nodes, and the expected failure/model totals for
each qualification run. Do not substitute caller-written SQL.

Then prove SQL/API/App parity under the already approved cost boundary:

1. Run `dbtobsb start` and type `START` only after showing its App-compute cost
   acknowledgement.
2. Open the installed App in the authenticated browser. Confirm the landing page
   performs no query, then click **Load observability** once. This may auto-start
   the bound SQL warehouse and incur warehouse cost.
3. Read `/api/v1/trends` with the same fixed limit and the accessible chart table.
   Require identical oldest-first timestamps, failed-node counts, and model counts
   across the fixed SQL result, API response, SVG labels, and table cells. Do not
   expose operational IDs or raw customer values in the final receipt.
4. Capture the required browser accessibility/keyboard evidence, then immediately
   continue to the stop gate below. Closing the browser does not stop compute.

## 7. Stop and verify the finish state

Run:

```console
uv run --project installer --no-sync dbtobsb stop
```

Require the exact stop receipt documented in the lifecycle guide. Then verify:

- the observed and collector runs are terminal;
- all three exact-name product Jobs have no active run;
- `dbtobsb-reconciler` remains `PAUSED`;
- the `dbtobsb-smoke` App is `STOPPED`; and
- the selected warehouse is `STOPPED`.

If the warehouse is dedicated and the user approved direct stop, stop only that
exact warehouse. Otherwise wait for its configured auto-stop and verify it. Never
stop, resize, or delete an unrelated or shared warehouse.

If the compute deadline is approaching, prioritize stop and terminal readback over
additional diagnosis. If any product compute cannot be proven stopped, report the
exact remaining resource category and continue bounded cleanup; do not declare
success.

## Final receipt

Report only:

- installation verified;
- selected project label;
- each approved observed run terminal, with the expected success or intentional
  qualification failure classification;
- model/seed/test counts;
- dashboard trend SQL/API/SVG/table parity state;
- capture, pair, structured-log, and publication states;
- whether logs were complete and not truncated;
- App, reconciler, Job-run, and warehouse final states; and
- elapsed time against the approved compute window.

Do not include workspace names or URLs, identities, numeric IDs, schema names,
archive locations, raw log messages, SQL text, local state, tokens, or customer
data. Link the user to `docs/site/tutorials/see-your-first-run.md` and
`docs/site/how-to-guides/query-observability-data.md` for next steps.
