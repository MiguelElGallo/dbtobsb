# Databricks platform fourth re-review: P0 planning baseline 0.5

- Author-set SHA-256: `974745400db1efe497938afbce9bd41e6b03d37aa0f10b6c5eb33e0d9cfd8f84`
- Date: 2026-07-15
- Reviewer: independent Databricks platform specialist
- Verdict: `CHANGES_REQUIRED`
- Cloud mutation: none; no Azure or Databricks API, resource, App, Job, warehouse, or compute was started
- Pinned source reviewed: Databricks CLI `v1.7.0`, commit `2f68ee4951ef96fa9d99e40c8ebadccf08412d58`

## Immutable input verification

The author set was hashed before review by sorting these paths, hashing each file with SHA-256, sorting the resulting records by path, and hashing that stream:

- `README.md`
- `AGENTS.md`
- `docs/index.md`
- all Markdown files under `docs/decisions`
- all Markdown files under `docs/plans`
- all Markdown files under `docs/research`

The independently reproduced pre-review digest was exactly:

```text
974745400db1efe497938afbce9bd41e6b03d37aa0f10b6c5eb33e0d9cfd8f84
```

The same digest was reproduced after the report was written. This review file is outside the author-set scope. No author file changed during the review.

## Executive outcome

Baseline 0.5 fixes the central architecture defect in `DBX-P0-010`:

- CLI 1.7.0 Direct resources create the dedicated schema and fixed migration Job, not Delta tables or views.
- A separate, deterministic, fixed-code migration Job owns table/view DDL and non-App object grants.
- The collector has DML only on three named evidence tables and no schema or object DDL.
- App `uc_securable` bindings are generated only after independent object verification.
- Mutation-bearing Bundle pre-deploy scripts and required Experimental `job_runs` are prohibited.
- Runtime application and App code/start remain separate, with `lifecycle.started: false` and `bundle run <app-key>`.

That is the correct product direction, and it resolves the original unsupported-table-resource claim. It is not yet safe to approve, for three reasons:

1. The plan generates the saved Direct seal before the bootstrap mutation whose state the seal must revoke. Under CLI 1.7.0, that saved plan is stale or contains create actions; it cannot be the promised pre-authorized `finally` cleanup.
2. CLI 1.7.0 treats a schema resource's `grants` list as an authoritative direct-grant set. Principals absent from the desired list are patched with `REMOVE ALL_PRIVILEGES`. The plan does not reconcile that behavior with App resource auto-grants or its promise to preserve customer grants.
3. The optional system-backed views have no executable owner/materializer identity. System-table access is schema-wide and account/region scoped, while every named product principal is denied or omits that access.

`DBX-P0-010` is therefore **substantially but not fully resolved**. Its Direct-versus-data boundary is accepted; the seal and grant lifecycle still need a corrected fifth frozen input.

## Current first-party sources checked

### Platform, Apps, and Unity Catalog

- [Azure Databricks Apps overview](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/) — Apps require Premium, run on billed serverless compute, and have explicit compliance-profile enablement requirements.
- [Declarative Automation Bundles resources](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/resources) — supported Bundle resources include Apps, Jobs, schemas, and volumes, but no generic managed Delta table/view resource; App table bindings use `uc_securable`.
- [Add a Unity Catalog table resource to an App](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/tables) — the object must already exist; adding it automatically grants the App service principal parent `USE CATALOG`, parent `USE SCHEMA`, and table/view access.
- [Unity Catalog privileges reference](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/access-control/privileges-reference) — `CREATE TABLE` creates tables or views; table writes require `MODIFY`; views are select-only securables.
- [Unity Catalog permissions concepts](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/access-control/permissions-concepts) — creators become owners; owners have all object capabilities and can grant/revoke, transfer ownership, and drop the object; `MANAGE` is distinct from data privileges.
- [Create and manage views](https://learn.microsoft.com/en-us/azure/databricks/views/create-views) and [view query requirements](https://learn.microsoft.com/en-us/azure/databricks/views/) — a view creator needs parent use, schema `CREATE TABLE`, and source `SELECT`; on SQL warehouses the view owner's underlying permissions are checked and must persist.
- [System tables reference](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/) and [Jobs system table reference](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs) — access is granted with `USE CATALOG` plus schema-level `USE SCHEMA` and `SELECT`; Jobs data covers the account's workspaces in the same cloud region and includes workspace and identity metadata.

### CLI 1.7.0 Direct behavior

- [CLI 1.7.0 immutable release](https://github.com/databricks/cli/releases/tag/v1.7.0) — exact reviewed release; `job_runs` is experimental, while selected-resource grants/permissions were fixed in this release.
- [Direct deployment guidance](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/direct) — Direct keeps local and remote state separately and produces state-based plans.
- [Saved-plan lineage and serial validation](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/bundle_plan.go#L42-L59) — a nonempty-lineage plan must match both current lineage and serial; validation is skipped for an empty first-deployment lineage.
- [Missing deployment state produces a create action](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/bundle_plan.go#L207-L215) — planning before bootstrap does not discover and encode the future post-bootstrap state.
- [Direct plans capture remote state and calculate a fixed action](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/bundle_plan.go#L240-L305) — saved apply executes the precomputed action rather than recomputing it.
- [Selected resources include their grant and permission subnodes](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/deployplan/plan.go#L210-L243) — selecting the schema also selects its `.grants` node and transitive dependencies.
- [Direct grant update and omitted-principal removal](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/dresources/grants.go#L120-L190) — update reads the plan's remote assignments and sends `REMOVE ALL_PRIVILEGES` for every remote principal absent from desired assignments.
- [CLI acceptance proof for principal removal](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/acceptance/bundle/deploy/readplan/grants-remove-principal/script) — first-party acceptance coverage explicitly verifies that a serialized saved plan revokes an omitted grant principal.
- [Saved-plan processing](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/cmd/bundle/utils/process.go#L240-L265) and [Direct deploy phase](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/phases/deploy.go#L131-L205) — confirms native validation gaps and why a mutation-bearing pre-deploy script cannot substitute for a reviewed resource/data plan.

### Read-only validation performed

- Confirmed the installed binary reports `Databricks CLI v1.7.0`.
- Generated the local CLI 1.7.0 Bundle schema. Its root resource keys include `apps`, `jobs`, `schemas`, `volumes`, and experimental `job_runs`, but no `tables` resource.
- Shallow-cloned the first-party `v1.7.0` tag and verified commit `2f68ee4951ef96fa9d99e40c8ebadccf08412d58`.
- Ran `go test ./bundle/direct ./bundle/deployplan ./bundle/direct/dresources` against that pinned source: all three packages passed.

These checks were local and read-only with respect to Databricks. They do not replace the bounded P3/P8 workspace qualification already required by the plan.

## Focused `DBX-P0-010` acceptance

| Acceptance condition | Fourth re-review outcome | Evidence and conclusion |
|---|---|---|
| Direct manages only supported bootstrap resources | `PASS` | The selected resource plan is limited to the dedicated schema, its direct grants, and a fixed unscheduled migration Job. It makes no table/view resource claim. |
| Fixed migration plane creates tables/views and non-App grants | `PASS_WITH_FOLLOW_UP` | The fixed-code, digest-bound, concurrency-one Job; closed manifest; independent verification; idempotent step ledger; and drift block are appropriate. P3 still must prove the first-ledger/bootstrap race, interruption, and exact retry behavior. |
| Exact migration privilege and ownership boundary | `PASS_WITH_FOLLOW_UP` | Parent use, warehouse `CAN_USE`, temporary schema `CREATE TABLE`, and persistent ownership only of enumerated objects are executable. Ownership gives the migration principal continuing access to restricted evidence; the plan correctly treats that as reviewed residual access. Retained-evidence uninstall must display or transfer that owner explicitly in P7 evidence. |
| Saved seal exists before any migration mutation | `FAIL` | The intent is correct, but the saved plan is prepared before bootstrap apply. CLI state semantics make that plan stale or create-bearing. See `DBX-P0-011`. |
| Runtime/App-binding plan is regenerated after verify and seal | `PASS` | The full plan is generated only after object, owner, version, and grant verification plus seal. Bindings point only to pre-existing objects and App compute remains stopped through resource apply. |
| Schema grants survive no-op, upgrade, rollback, and uninstall safely | `FAIL` | Direct schema grants remove omitted direct principals. App resource auto-grants and customer-added direct grants are not represented by an exact coexistence contract. See `DBX-P0-012`. |
| Failed/cancelled/timed-out migration leaves no DDL authority or compute | `FAIL` | Compute shutdown and fail-closed runtime gates are present, but the pre-bootstrap seal cannot provide deterministic unattended cleanup. A newly generated plan would require a new approval under the current sidecar rule. |
| Collector never executes DDL | `PASS` | The identity table grants only `SELECT`+`MODIFY` on three base tables, and both the working agreement and generated-policy tests prohibit collector table/view creation or replacement. |
| No mutation-bearing pre-deploy hook | `PASS` | The prohibition is explicit in the working agreement, ADR, product plan, source register, and policy tests. |
| No required Experimental `job_runs` | `PASS` | The plan uses `bundle run` against ordinary Job/App resources and explicitly rejects required `job_runs`. |
| Optional system enrichment is least-privilege and executable | `FAIL` | The manifest names system-backed views, but no named principal can own/query or materialize them. See reopened `DBX-P0-006`. |

## Prior finding disposition

| Finding | Fourth re-review disposition |
|---|---|
| `DBX-P0-001` | `RESOLVED_FOR_P0`; no regression in the `ALL_DONE` Run Job topology or separate observed/collector job-level run-as identities. |
| `DBX-P0-002` | `RESOLVED_FOR_P0`; no regression in bounded reconciliation, visible degraded mode, 20-minute target, or exactly-once AttemptKey tests. |
| `DBX-P0-003` | `RESOLVED_FOR_P0`; App authorization remains the platform identity while the product's actor/browser/role decision is separate, deny-by-default, and Preview-free. |
| `DBX-P0-004` | `RESOLVED_FOR_P0`; CLI 1.7.0, Direct, environment, Python, dbt, SQL channel, and typed workspace readiness remain exact candidate gates. |
| `DBX-P0-005` | `RESOLVED_FOR_P0`; zero required public runtime egress and the separate signed/locked deployment boundary remain intact. |
| `DBX-P0-006` | `REOPENED — CHANGES_REQUIRED`; the plan now names optional system-backed views but still has no system-read view owner or materializer identity. |
| `DBX-P0-007` | `RESOLVED_FOR_P0` for App ACLs and access-versus-resource authorization. Grant preservation now has a distinct Direct reconciliation defect, `DBX-P0-012`. |
| `DBX-P0-008` | `RESOLVED_FOR_P0`; actor enrollment, browser binding, fixed role Job, exact action-table privileges, and same-value recreation limitation remain testable. |
| `DBX-P0-009` | `RESOLVED_FOR_P0`; the general saved-plan sidecar, explicit stopped lifecycle, and non-redeploying App `bundle run` sequence remain accepted. The new seal-specific sequencing defect is `DBX-P0-011`. |
| `DBX-P0-010` | `PARTIALLY_RESOLVED`; the unsupported Direct table/view claim is fixed, as are the fixed migration plane, existing-object binding order, collector DDL prohibition, and migration journaling. The saved-seal and authoritative schema-grant defects prevent closure. |

## Active findings

### DBX-P0-011: The saved seal is generated against the wrong Direct state

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: `docs/plans/product-plan.md`, **Data-object and migration boundary**, **Bootstrap the product**, **Enable optional controlled actions**, P3, P6, P7, and P8; `docs/decisions/0001-private-app-bundle.md`; `docs/plans/documentation-plan.md`; `docs/research/source-register.md`
- Evidence:
  - Product-plan step 5 prepares the saved seal “in parallel with” resource-bootstrap approval, before resource-bootstrap apply establishes the schema/grant state.
  - CLI 1.7.0 copies deployment lineage and serial into a Direct plan. A later apply rejects a nonempty-lineage plan after the serial changes. On a first deployment, however, empty-lineage validation is skipped.
  - When a planned resource has no deployment-state entry, CLI 1.7.0 fixes its action as `create`. A pre-bootstrap seal plan therefore cannot encode “update this post-bootstrap schema grant by removing `CREATE TABLE`”; it encodes initial creation/skip semantics against the pre-bootstrap state.
  - On fresh install, applying that empty-lineage stale plan can reach duplicate schema/Job create actions unless the wrapper's semantic comparison blocks it. On upgrade, bootstrap changes the serial and native validation rejects the pre-bootstrap seal.
  - The wrapper's immediate re-plan comparison prevents unsafe apply, but it does not fulfill the cleanup promise: mismatch returns to plan and approval while temporary DDL authority is already present, so a failed migration no longer has a pre-approved deterministic `finally` plan.
- User/system impact: Failure, cancellation, timeout, operator absence, or a lost response can leave temporary schema `CREATE TABLE` authority in place or require an unplanned emergency approval. Runtime remains blocked, but the regulated least-privilege cleanup guarantee is false.
- Required change:
  1. Pre-authorize the exact seal **specification** with resource-bootstrap approval, not a pre-bootstrap saved Direct plan.
  2. Apply and verify the resource-bootstrap plan first.
  3. Immediately generate the saved seal Direct plan against the resulting live Direct state, before `DATA_APPLY` can start. Require nonempty matching lineage/current serial on an established deployment, the exact schema-grant selection, and only the expected removal of migration-principal `CREATE TABLE`; any other action or principal blocks migration.
  4. Bind that post-bootstrap plan and its source/config/selection/state digest to the earlier authorized seal specification. If policy requires a second human approval for the concrete plan digest, obtain it before running the migration, never in the `finally` path.
  5. Apply and independently verify that saved plan in `finally`; reconcile an ambiguous/lost response from live grants and Direct state before deciding whether a new plan is needed.
  6. Use the same ordering for P6 and every upgrade.
- Testable acceptance:
  - Fresh-install and upgrade fixtures prove a pre-bootstrap seal plan is rejected by policy, while the post-bootstrap seal plan has current lineage/serial and exactly one allowed privilege removal.
  - Success, SQL failure, partial DDL, cancellation, timeout, and lost-response fixtures all end with `CREATE TABLE` absent without asking for a new approval after migration starts.
  - A changed principal, extra privilege/principal change, selection change, source change, or foreign state change blocks `DATA_APPLY` before compute starts.
  - A second cleanup attempt first verifies live state and is idempotent rather than blindly replaying a consumed saved plan.

### DBX-P0-012: Direct schema grants can revoke App and customer access

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: `docs/plans/product-plan.md`, **Runtime identity model**, **Data-object and migration boundary**, **Bootstrap the product**, **Upgrade, rollback, and uninstall data order**, P3, P6, P7, and P8; `docs/decisions/0001-private-app-bundle.md`; `docs/plans/documentation-plan.md`; `docs/research/source-register.md`
- Evidence:
  - CLI 1.7.0 selection intentionally includes a selected schema's `.grants` subnode. Resource bootstrap and seal therefore apply the complete configured schema grant list, not only an isolated `CREATE TABLE` bit.
  - The pinned grant adapter reads all direct remote assignments. `removedGrantPrincipals` returns every remote principal absent from desired assignments, and `DoUpdate` sends `REMOVE ALL_PRIVILEGES` for each. The first-party saved-plan acceptance test verifies that revocation behavior.
  - An App table/view binding automatically grants its service principal parent `USE CATALOG` and `USE SCHEMA`.
  - Baseline 0.5 says the Direct schema resource manages exact `USE SCHEMA` grants and temporary migration `CREATE TABLE`, but it never defines phase-specific complete desired grant sets or says how the runtime set contains the App service principal's automatic `USE SCHEMA` grant.
  - If runtime schema grants omit that principal, the next nominal no-op plan sees the automatic App grant as remote-only drift and can remove it while the App resource itself is unchanged. The same mechanism can remove a customer's direct grant, contradicting the preservation promise.
  - Simply adding `${resources.apps.<app>.service_principal_client_id}` to the bootstrap schema grants is not neutral: the selected schema grant node then has a transitive App dependency, violating the promise that bootstrap contains no App resource or binding.
- User/system impact: A no-op deployment or upgrade can break the App's curated-view access, revoke a customer-managed direct schema grant, make rollback non-idempotent, or produce an uninstall diff that does not match the stated retention decision.
- Required change:
  1. Choose and document one exact schema-grant ownership model.
  2. Preferred preservation model: let Direct create and protect the schema without an authoritative `grants` list; use a separate approved, targeted privilege plane to add/remove only product-recorded principals and privileges, with before/after verification and no removal of unrelated assignments. If this replaces the Direct seal, update the decision and acceptance evidence explicitly.
  3. If Direct schema grants and a saved Direct seal are retained, define separate frozen bootstrap, seal, runtime, upgrade, rollback, and uninstall configurations. The runtime desired set must include the App service principal and every deliberately preserved direct grant; the bootstrap/seal set must not pull the App as a transitive dependency. Unknown grants must block for an explicit preserve/remove decision, never be silently revoked.
  4. Make inherited catalog/schema privileges and direct grants visibly distinct. Do not promise preservation of a grant that the chosen Direct configuration will reconcile away.
  5. Define removal ordering for App bindings, schema grants, retained evidence, migration ownership, and final schema deletion. Retained evidence must show the residual owner or an approved ownership transfer.
- Testable acceptance:
  - A second full deployment is a true no-op and leaves the App able to query every bound view.
  - Fresh install, seal, runtime apply, additive upgrade, rollback, retain-uninstall, and delete-uninstall prove exact direct and inherited grants before and after each stage.
  - A synthetic customer direct schema grant survives every non-destructive operation unless a separately approved plan explicitly removes it.
  - App binding removal does not remove a customer grant, and schema reconciliation does not remove an active App parent grant.
  - Static tests prove selected bootstrap has no App dependency or binding and that runtime configuration accounts for the App service principal.

### DBX-P0-006 (reopened): Optional system-backed views have no executable least-privilege identity

- Classification: `CHANGES_REQUIRED`
- Severity: medium
- Affected contract: `docs/plans/product-plan.md`, **Product boundary**, **Target architecture**, **Runtime identity model**, **Data-object and migration boundary**, **Platform readiness matrix**, **Cost confidence**, P4, P7, and P8; `docs/decisions/0001-private-app-bundle.md`; `docs/plans/documentation-plan.md`; `docs/research/source-register.md`
- Evidence:
  - The closed base manifest names `lakeflow_job_run_health`, `lakeflow_dbt_task_run_health`, and `dbt_job_health` as optional system-backed views, while the architecture draws unnamed optional Jobs/billing/audit enrichment into product-owned objects.
  - System-table access requires `USE CATALOG` on `system`, `USE SCHEMA` and `SELECT` on a whole system schema. Jobs tables cover all account workspaces in the cloud region and contain workspace, run-as, creator, name, and tag data.
  - A logical view creator needs source `SELECT`, and on the selected SQL warehouse the view owner must retain the underlying permissions.
  - The migration principal is explicitly denied customer-data privilege; the collector is limited to three product base tables and explicitly onboarded Job API visibility; the App has no broad system access; the role Job has no such grant. No enrichment principal, view owner, Job, schedule, target table, or uninstall path is named.
- User/system impact: Enabling the optional views either fails creation/query, silently broadens the migration or App principal to account/region operational data, or creates an unmanaged privileged owner. That breaks the stated customer-local least-privilege and cross-workspace isolation contract.
- Required change:
  1. Keep this capability `DISABLED` by default and omit its objects/bindings from the required manifest until an enrichment mode is selected.
  2. Define either a dedicated logical-view owner with the exact persistent system-schema grants, or a dedicated bounded enrichment Job/principal that reads exact system schemas and writes only filtered product materialization tables. Do not give this access to the App, collector, migration, or role Job by implication.
  3. Specify workspace/onboarded-Job predicates, sensitive source fields, owner, target objects, schedule/trigger, cost, freshness/latency, failure-to-`DEGRADED` behavior, access review, retention, rollback, and uninstall.
  4. If a customer instead supplies pre-filtered views, type and verify them as explicit readiness prerequisites and bind only those verified objects.
- Testable acceptance:
  - With enrichment disabled, the base install, capture, App, cost-confidence states, and uninstall all pass without any `system` grant.
  - With enrichment enabled, positive tests return only the selected workspace and onboarded Jobs; cross-workspace, unonboarded-Job, identity/tag, and raw-system access tests fail for the App and ordinary operators.
  - Removing each parent/system-schema/target privilege independently produces the expected degraded state without widening access.
  - Access review and uninstall account for the privileged view owner or enrichment Job principal and leave no orphaned system access.

## Reviewed-file outcome

| Author file or set | Outcome | Databricks conclusion |
|---|---|---|
| `README.md` | `PASS` | The high-level product boundary, customer-local posture, resource/data separation, and collector no-DDL statement are accurate. |
| `AGENTS.md` | `PASS` | It correctly prohibits collector DDL, Direct table/view claims, mutation-bearing pre-deploy scripts, arbitrary commands/SQL, and required AI/experimental paths. |
| `docs/index.md` | `PASS` | The planning index is coherent and introduces no independent platform claim. |
| `docs/decisions/0001-private-app-bundle.md` | `CHANGES_REQUIRED` | The private App plus Direct Bundle and separate fixed migration plane remain the recommended starting point, but the decision must fix seal generation, schema-grant authority/preservation, and optional system enrichment identity. |
| `docs/plans/product-plan.md` | `CHANGES_REQUIRED` | The main DBX-P0-010 separation is strong; active findings `DBX-P0-011`, `DBX-P0-012`, and reopened `DBX-P0-006` are executable-path defects. |
| `docs/plans/review-process.md` | `PASS` | Frozen-input independence, finding structure, P0-P10 scope, re-review, and documentation gates remain appropriate. |
| `docs/plans/documentation-plan.md` | `CHANGES_REQUIRED` | The IA is strong, but D2/D5 references and how-tos must teach post-bootstrap seal generation, authoritative-versus-targeted grants, App parent grants, customer-grant preservation, and enrichment ownership. |
| `docs/research/source-register.md` | `CHANGES_REQUIRED` | It has relevant sources, but its saved-plan/grants cautions omit the exact state-ordering and omitted-principal revocation behavior proved by pinned CLI 1.7.0 source. Add the optional system view-owner/materializer consequence as well. |
| `docs/reviews/p0-planning-baseline/resolution.md` | `NOT_AN_APPROVAL_INPUT` | The ledger accurately records author intent, but its statement that `DBX-P0-010` is resolved is not accepted by this independent review. |

## P0-P10 Databricks matrix

| Part | Outcome | Databricks conclusion and required evidence |
|---|---|---|
| P0 — Product contract | `CHANGES_REQUIRED` | Correct `DBX-P0-011`, `DBX-P0-012`, and reopened `DBX-P0-006`; freeze and re-review a fifth author set. |
| P1 — Capture library | `PASS_WITH_FOLLOW_UP` | No Databricks regression. Keep pure parsing, exact schema/version evidence, and no live platform dependency. Optional system enrichment must not enter the canonical artifact parser. |
| P2 — Collector and reconciliation | `PASS_WITH_FOLLOW_UP` | The DML-only collector, exact three-table grants, separate run-as, `ALL_DONE` Run Job, and bounded reconciliation are sound. P2 must remain unable to create/alter objects or read system schemas. |
| P3 — Bundle installer | `CHANGES_REQUIRED` | Generate the seal after bootstrap and before migration; prove current lineage/serial and exact actions; choose a safe schema-grant authority model; prove true no-op, App access, preservation, resume, and uninstall. |
| P4 — App read-only MVP | `PASS_WITH_FOLLOW_UP` | Curated-only, stateless, named App ACLs, and honest cost-confidence states remain sound. The App must be tested after a second no-op deployment, and optional enrichment stays unavailable until its identity contract is accepted. |
| P5 — Job onboarding | `PASS_WITH_FOLLOW_UP` | No regression. Keep the five scanner states, source-controlled patch, existing owner approval, separate collector Job, and no direct customer-Job mutation. |
| P6 — Controlled actions | `CHANGES_REQUIRED` | P6 reuses resource-bootstrap/data/seal/runtime order and schema grants, so both active Direct findings apply. The actor/browser/role-Job authorization contract itself remains accepted. |
| P7 — Security and operations | `CHANGES_REQUIRED` | Access review, upgrade, rollback, retention, and uninstall must prove post-bootstrap seal availability, App/customer grant preservation, retained object ownership, and optional system-reader removal. |
| P8 — Bounded live proof | `CHANGES_REQUIRED` | Add explicit stale-prebootstrap-seal rejection, post-bootstrap saved-seal success, no-op App query, customer-grant preservation, and enrichment-disabled/enabled inventories to the existing cost-bounded proof. |
| P9 — Optional intelligence | `PASS_WITH_FOLLOW_UP` | No regression. Genie/MCP remains outside authorization, migration, schema grants, system enrichment, capture, and validation. Core operation must pass with AI disabled. |
| P10 — Private alpha | `PASS_WITH_FOLLOW_UP` | The alpha journey remains plausible after P3/P7 corrections. A non-author UC owner must complete bootstrap, post-bootstrap seal preparation, data migration, runtime binding, no-op upgrade, retain/delete choice, and uninstall without SQL, IDs, paths, or YAML. |

## Final verdict

`CHANGES_REQUIRED`

The recommended starting architecture remains a private Databricks App deployed through a plain-YAML Direct Bundle, with a separate fixed data-migration Job. Baseline 0.5 correctly removes table/view DDL from Direct and the collector, uses existing-object App bindings, and prohibits hidden pre-deploy mutation and required Experimental resources.

P0 cannot close because the saved seal is generated before the state it must seal, Direct schema grants can reconcile away App/customer access, and optional system-backed views lack a named least-privilege execution identity. These are planning defects, not reasons to abandon the architecture. They can be closed without paid cloud testing by correcting the stage order and grant/identity contract, then freezing a fifth author set. Bounded live qualification remains properly assigned to P3, P6, P7, and P8.
