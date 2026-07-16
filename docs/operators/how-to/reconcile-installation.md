# Reconcile an installation

Use this procedure when dbtobsb reports a deployment, seal, resource-binding, authentication, or
view-contract code. These conditions are not fixed by rerunning the collector.

## Before you start

Use the same signed release, immutable installation mode, approved workstation, actor-owned OAuth
profile, customer-owned schema, dedicated installer warehouse, and named principals used by the
installed record. Actor responsibility depends on the immutable mode:

The v1 installer accepts only catalog and schema names that match
`^[A-Za-z_][A-Za-z0-9_]{0,127}$`. A name that requires Unity Catalog quoting—for example, one with
a hyphen, space, punctuation, or Unicode—is unsupported in v1. The canonical launcher must report
that during resource selection, before it creates an approval or sends a mutation. Choose a
dedicated supported-name schema; do not rename or substitute an existing installed schema during
recovery.

- In `SEPARATED_DUTIES`, the deployment/seal verifier performs the read-only recovery audit and
  deployment observation, hands the fixed data operation to the different UC operator, waits for
  that operator to finish query recovery, data verification, and exact temporary-grant revoke,
  then resumes only after the supported handoff returns control.
- In `COMBINED_ROLE`, one accountable administrator acknowledges that data-mutation observation and
  service-principal role review are not independent, then performs both actor stages without a
  handoff. The workflow must not report separation.

Keep the App stopped. Do not run the observed, collector, or reconciler Jobs while the installed
graph is unverified. Do not edit App environment values, resource bindings, Job tasks, resolved
wheel paths, service principals, grants, tables, views, or the manifest row by hand.

The installer warehouse can accrue cost and its monitors can see complete query history. It must
be dedicated to dbtobsb installation work, not shared with unrelated queries.

## Preserve the safe diagnostic

Record only the static diagnostic code and a correlation value when the App emitted one. Job and
installer diagnostics do not necessarily have an App correlation value. Do not copy a native
exception, query text, raw log, artifact path, manifest content, identifier, or other Personal Data
into an ordinary support ticket.

Use this routing:

| Code family | Check |
| --- | --- |
| `DBTOBSB_DEPLOYMENT_*`, `DBTOBSB_RECONCILIATION_BINDING_MISMATCH`, `DBTOBSB_RECONCILIATION_MANIFEST_MISMATCH` | Packaged runtime seal, current Bundle Jobs, resolved environment, and installed manifest must all agree. |
| `DBTOBSB_RUNTIME_TRUST_OBSERVATION_INVALID`, `DBTOBSB_RUNTIME_TRUST_OBSERVATION_UNAVAILABLE` | Keep collection stopped. Reconcile the accepted generation, exact `BASE_OBSERVABILITY` component, and sanitized status-view readability; do not alter evidence rows. |
| `DBTOBSB_DELTA_INSTALLATION_BINDING_MISMATCH`, `DBTOBSB_DELTA_ATTEMPT_BINDING_MISMATCH` | The collector's sealed catalog/schema/workspace/observed-Job/task binding and resolved attempt must agree before the status view or registry is read. |
| `DBT_JOBS_DBT_*`, `DBT_JOBS_INSTALLED_*`, `DBT_JOBS_WORKSPACE_BINDING_MISMATCH`, `DBT_JOBS_RESOLVED_ATTEMPT_BINDING_MISMATCH` | The observed Job, collector Job, immutable command, source, target, task policy, and current deployment must match the sealed release. |
| `DBTOBSB_CONFIGURATION_INVALID`, `DBTOBSB_APP_AUTH_INVALID` | The stopped App's fixed environment-to-resource mappings, App identity, warehouse binding, and grants must match the approved bound-unshared and user-access-only plans. |
| `DBTOBSB_APP_RUN_VIEW_CONTRACT_MISMATCH`, `DBTOBSB_APP_NODE_VIEW_CONTRACT_MISMATCH`, `DBTOBSB_APP_COLLECTION_VIEW_CONTRACT_MISMATCH`, `DBTOBSB_APP_TRUST_VIEW_CONTRACT_MISMATCH` | The three sanitized evidence views and one runtime-trust status view must have the exact release schema and remain the only views bound to the App. |
| `DBTOBSB_APP_RUNTIME_TRUST_NOT_ACCEPTED` | The one-row runtime-trust summary must identify this installation and base component, be structurally valid, accepted, and unexpired. Keep all evidence reads held until the attended lifecycle restores an accepted point-in-time snapshot. |
| Any other installation code | Stop and use the release's attended recovery audit; do not improvise a repair. |

## Run the attended recovery audit

1. Confirm the App is stopped and there is no pending App deployment, active product Job run, or
   active installer query.
2. Start or resume the signed attended installer through the release's canonical launcher. The
   supported launcher is still a release blocker until its final entrypoint is implemented and
   qualified; do not substitute the developer-only seal utility. Do not pass a Job ID, App
   deployment ID, wheel path, SQL statement, YAML fragment, or destination override.
3. Review its read-only inventory: workspace and actor, installation mode, schema and object
   ownership, complete visible grants, named trusted roots, runtime Job identities and ACLs,
   resolved dependency tuple, App lifecycle and deployment set, and installer-warehouse query
   history.
4. If the installer reports an indeterminate statement or incomplete authority observation, stop
   ordinary recovery. Follow its exact Query History cleanup route; never resubmit a mutating
   request by guesswork.
5. In `SEPARATED_DUTIES`, the verifier hands off at the fixed checkpoint. The UC operator alone
   approves and executes the fixed data envelope, resolves Query History, verifies data, removes
   the exact temporary grant, and returns control through the supported handoff. In
   `COMBINED_ROLE`, the one acknowledged actor performs this stage directly.
6. The deployment/seal verifier recomputes live state after the data stage. Preserve foreign grants
   and customer-owned objects.
7. For a fresh installation, require an App shell with no deployment. Review and apply a fresh
   bound-unshared plan whose only additions are the exact five read-only resources and their five
   deploy-time environment mappings; it grants no user `CAN_USE`. Require an empty paginated
   deployment baseline, invoke the pinned Bundle App runner exactly once, stop on every exit, and
   reconcile exactly one new successful matching `SNAPSHOT` with no pending deployment. After the
   App is proved `STOPPED`, review and apply a third fresh user-access-only plan whose sole delta is
   `CAN_USE` for the approved App-user group. Do not rerun the Bundle App runner or deploy code
   again. If any deployment existed before the bound invocation, return
   `UNSUPPORTED_EXISTING_APP_DEPLOYMENT`; v1 has no qualified in-place recovery or upgrade path.

## Verify before runtime resumes

Require every condition below:

- every Statement Execution request is terminal in GA Query History;
- the exact migration-group grant/revoke pair is absent;
- object definitions, owners, grants, manifest row, packaged seal, current Job graph, and resolved
  environment agree with the release;
- the App has no Job, secret, Volume, raw table, schema-wide, `MODIFY`, `CAN MANAGE`, or owner
  binding;
- the stopped App has exactly the five reviewed resource bindings and five environment mappings,
  only the approved user-group `CAN_USE`, no pending deployment, and the same uniquely reconciled
  deployment;
- the collector and observed dbt Jobs still run as two distinct service principals; and
- no product-created test warehouse, classic cluster, active Job run, active query, or running App
  remains unintentionally active.

Start the App only through the signed lifecycle flow after those checks and its separate approval.
If any check is incomplete, keep setup stopped and escalate the static code.

## Finish safely

Stop any product-owned test compute that this recovery started. Do not stop or change a shared
customer warehouse or unrelated resource. Closing a browser does not stop App compute or a SQL
warehouse.
