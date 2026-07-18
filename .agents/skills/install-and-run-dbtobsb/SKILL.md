---
name: install-and-run-dbtobsb
description: Install or safely resume dbtobsb v0.3.0 in Azure Databricks, run exactly one installed dbt Core weather or customer project, prove that model results and structured logs were captured into the customer-local evidence views, and finish with product compute stopped. Use when a user asks an agent to install dbtobsb, run the demo or qualification project, make a first observed run, test capture end to end, or verify dbt observability after cloning this repository.
---

# Install and run dbtobsb

Complete one attended path from a clean clone to a captured dbt run. Assume the
user has the required authority, but never assume their workspace, resource, data,
cost, or retention choices.

## Read the supported contract

Before acting, read these repository files:

1. `docs/site/how-to-guides/install-private-release.md`
2. `docs/site/how-to-guides/add-a-dbt-project.md`
3. `docs/site/tutorials/see-your-first-run.md`
4. `docs/site/how-to-guides/stop-or-uninstall.md`
5. `docs/site/reference/dbt-project-input.md`

Treat `docs/releases/v0.3.0-support-contract.md` as authoritative when another
document is ambiguous. Do not use the legacy App-shell smoke path in `README.md`.

## Preserve the product boundaries

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

1. Confirm the worktree is clean. The skill and weather example were added after
   tag `v0.3.0`, so a current `main` checkout is expected. Require the release
   runtime to remain unchanged from that tag with
   `git diff --quiet v0.3.0 -- app capture collector contracts installer native qualification databricks.yml`.
   If that check fails, state that the runtime is modified and ask whether to test
   unsupported source before any cloud mutation.
2. Check Python, `uv`, Databricks CLI, and `jq` against the supported-environment
   page.
3. Run `databricks auth profiles --output json`. Present every valid Azure OAuth
   profile and its workspace host; never select one automatically.
4. After the user chooses a profile, verify it with `databricks auth describe` and
   `databricks current-user me` using the explicit `--profile` flag.
5. Read-only list the candidate active service principals, non-system groups, SQL
   warehouses, catalogs, schemas, and dbt projects that the installer can select.
6. Check for `.dbtobsb/release-installation-v1.json` without printing its contents.
   Preserve it. An existing file means resume or verify the same lifecycle; never
   edit or delete it.

Treat resource names, identities, the workspace host, and local state as sensitive
operational information. Show them only in the private attended choice prompt and
do not repeat them in the final receipt.

## 2. Ask before any mutation or paid compute

Ask one consolidated question and wait for all answers. Do not run `uv sync`,
`bootstrap`, a Job, the App, or a SQL query before this response.

Ask the user to choose or confirm:

1. **Azure Databricks profile** — one discovered named profile; never `DEFAULT`.
2. **dbt project** — recommend `examples/customer_weather` for one harmless model;
   offer `qualification_dbt` for the documented three-model, one-seed, five-test
   result; or accept another isolated child project that passes the input contract.
3. **Observed and collector service principals** — two different active discovered
   identities.
4. **Job-manager/App-viewer group** — one discovered non-system group.
5. **SQL warehouse** — one existing warehouse the observed principal may use; ask
   whether it is dedicated and may be stopped directly or is shared and must use
   its configured auto-stop.
6. **Catalog, empty evidence schema, and dbt target schema** — the current actor
   owns the evidence schema; the observed principal owns the target schema.
7. **Mutation approval** — allow the installer to create or verify the nine product
   objects in the evidence schema and allow dbt to create the chosen example's
   relations in the target schema.
8. **Compute approval and deadline** — allow bounded serverless installation Jobs,
   two bounded App deployment checks, one observed Job run, its collector run, and
   one SQL verification. Record the user's maximum elapsed compute window.
9. **Finish state** — recommend leaving the installation present with the App
   stopped, reconciler paused, every product run terminal, and evidence retained.

Do not ask whether the user has administrator rights; assume that as requested.
Still let the installer verify identity, ownership, and access. If a required
resource is absent, stop and explain that v0.3.0 requires it to exist. Do not
provision a substitute or choose a different resource silently.

Summarize the answers without secrets or numeric IDs. Ask the user to confirm the
summary once. This confirmation authorizes only the stated installation and one
run; it does not authorize deletion, retention changes, a second run, or unrelated
workspace changes.

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

When the installer displays **Installation preview**, pause. Show the user the
workspace display, evidence destination, dbt target, project, and identity display
names without exposing numeric IDs or local state. Ask for final approval. Type
`APPROVE` only after the user approves that exact preview.

If interrupted, run the same bootstrap command and let the installer resume. Never
delete or edit the state file. App deployment checks can be quiet for several
minutes. Inspect the live App deployment read-only if needed, but do not interrupt
or restart a still-running bootstrap merely because the terminal is quiet.
Continue only after this exact receipt:

```json
{"app_state":"STOPPED","event":"dbtobsb_installation_verified","reconciler_state":"PAUSED","stage":"INSTALLED"}
```

## 5. Run exactly one observed Job

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
- one observed run terminal and successful;
- model/seed/test counts;
- capture, pair, structured-log, and publication states;
- whether logs were complete and not truncated;
- App, reconciler, Job-run, and warehouse final states; and
- elapsed time against the approved compute window.

Do not include workspace names or URLs, identities, numeric IDs, schema names,
archive locations, raw log messages, SQL text, local state, tokens, or customer
data. Link the user to `docs/site/tutorials/see-your-first-run.md` and
`docs/site/how-to-guides/query-observability-data.md` for next steps.
