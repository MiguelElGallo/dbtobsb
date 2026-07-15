# Databricks platform sixth re-review: P0 planning baseline 0.7

- Author-set SHA-256: `85eab368552b9614eba555dd8f44feb1b8850d0eb66cdcc250cf98d6a502c893`
- Date: 2026-07-15
- Reviewer: independent Databricks platform specialist
- Verdict: `CHANGES_REQUIRED`
- Cloud mutation: none; no Azure or Databricks authentication, API, App, Job, warehouse, compute, or Unity Catalog mutation was attempted
- Pinned CLI source retained from the fifth review: Databricks CLI `v1.7.0`, commit `2f68ee4951ef96fa9d99e40c8ebadccf08412d58`

## Method and immutable input

The author input was limited to `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`. I sorted those paths, calculated SHA-256 for each file, sorted the records by path, and hashed that stream. The pre-review digest independently reproduced the requested value:

```text
85eab368552b9614eba555dd8f44feb1b8850d0eb66cdcc250cf98d6a502c893
```

I read the complete changed contract, compared it with the fifth Databricks review, and performed bounded current verification against official Azure Databricks documentation. I did not inspect another reviewer's draft before reaching the findings. This report is outside the author-set hash and is the only file written by this review.

## Executive outcome

Baseline 0.7 materially improves the regulated handoff and closes the two fifth-review follow-ups at the P0 contract level:

- Separated duties now means one supported customer-controlled workstation with two distinct managed OS accounts. Each actor owns a complete OAuth U2M profile, native secure-store credential, browser session, and private checkpoint.
- Cross-account coordination is limited to a system-owned, auto-discovered, signed, expiring, replay-resistant, digest-bound, nonsecret capsule. The capsule never authorizes runtime deployment.
- The UC operator is intended to retain control from privilege lease through fixed migration Job completion or cancellation, targeted revoke, complete effective-authority verification, data verification, seal, OS-account release, and deployment-account return.
- `RECOVERY_AUDIT` now explicitly expands direct and inherited grants, ownership, implied `ALL PRIVILEGES`, effective `MANAGE`, transitive groups, caller visibility, and all pages.
- Optional enrichment now has a product-owned `(workspace_id, job_id)` scope table whose sole writer is the fixed migration Job, a DML-only update envelope, three named snapshots, explicit regional Lakeflow versus account-global billing exposure, and snapshot-semantics gates.
- A second idempotent invocation of the fixed migration Job is intended to turn a digest-only seal attestation into a Databricks Jobs-anchored terminal receipt before the deployer can resume.

However, the claimed exclusive UC-operator lease phase is not enforced by the Databricks permissions model as written. The deployment operator creates and manages the migration Job and has the Service Principal User role needed to configure its migration run-as principal. Databricks makes the Job creator its owner; an owner or `CAN_MANAGE` principal can edit tasks, configuration, and permissions, and a run still executes with the configured run-as principal's Unity Catalog privileges. Locking or leaving the deployment OS session neither removes that remote authority nor prevents another authenticated session. During the temporary `CREATE TABLE` lease, a compromised or non-cooperating deployment actor could replace or invoke code under the migration principal and could undermine the authenticity of the Jobs receipt. This is a high-severity separation-of-duties defect, so P0 cannot pass.

A second, medium finding freezes the remaining platform details of the seal. `MANAGE` on a Unity Catalog table does not itself grant `SELECT` or `MODIFY`, schema ownership does not confer child-table data access, and Jobs run output has a concrete task/output contract and 60-day retention limit. Baseline 0.7 does not yet name the UC operator's exact temporary ledger DML grant/revoke or the exact receipt carrier, schema, lookup, retention, and ambiguity rules.

## Current primary evidence checked

### Job custody and run-as

- [Lakeflow Jobs identities, permissions, and privileges](https://learn.microsoft.com/en-us/azure/databricks/jobs/privileges) states that the Job creator receives `IS OWNER`, workspace admins receive `CAN MANAGE` by default, `CAN MANAGE` can edit the Job definition, tasks, configuration, and permissions, and `CAN_MANAGE_RUN` can trigger and cancel runs. Runs use the configured run-as principal's privileges, regardless of who triggers them. Databricks recommends granting `CAN MANAGE` or ownership only to principals trusted to modify production code.
- [Roles for managing service principals](https://learn.microsoft.com/en-us/azure/databricks/security/auth/access-control/service-principal-acl) states that Service Principal User is an account-level role that lets a workspace user run Jobs as the service principal.
- [Bundle resource permissions](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/permissions) confirms that a Bundle can assign Job `IS_OWNER`, `CAN_MANAGE`, `CAN_MANAGE_RUN`, and `CAN_VIEW`. The architecture can therefore model exact Job custody, but baseline 0.7 does not yet do so for the lease interval.
- [Restrict workspace admins](https://learn.microsoft.com/en-us/azure/databricks/admin/workspace-settings/restrict-workspace-admins) is a current account-admin setting that limits workspace-admin owner and run-as changes. It does not turn a human Job owner or `CAN_MANAGE` principal into a read-only actor, so it is supporting defense and an explicit residual-admin boundary, not a substitute for fixing the migration Job ACL/ownership design.

### Unity Catalog attestation authority and receipt retrieval

- [Unity Catalog permissions model](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/access-control/permissions-concepts) states that `ALL PRIVILEGES` and ownership can imply capabilities not listed as individual grants, that ownership does not inherit downward, and that `MANAGE` does not grant table data privileges. A `MANAGE` holder can grant itself those privileges, but the product must model and revoke that exact change rather than assume DML access.
- [Jobs CLI run and output reference](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/reference/jobs-commands) states that `get-run` paginates task, parameter, cluster, and repair arrays beyond 100 elements. `get-run-output` returns a notebook task's `dbutils.notebook.exit()` value, is limited to the first 5 MB, and Job runs are automatically removed after 60 days.
- [Task values](https://learn.microsoft.com/en-us/azure/databricks/jobs/task-values) provides another Databricks-anchored value mechanism for Python notebook tasks, with JSON and size constraints and values visible in run output. The product must select and test one exact mechanism rather than say only “through Databricks Jobs.”

### Prior follow-up verification

- [Unity Catalog effective permissions API](https://docs.databricks.com/api/workspace/grants/geteffective), the pinned CLI `grants get-effective` implementation, and the Unity Catalog ownership/inheritance rules remain consistent with baseline 0.7's fail-closed complete-authority contract. P3 still has to implement and live-qualify the algorithm.
- [Jobs system tables](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs) states that `system.lakeflow` covers every workspace in the account in the same cloud region and that `job_id` is unique only within a workspace. Baseline 0.7 correctly scopes by the workspace/Job pair.
- [Billing usage system table](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/billing) states that account billable usage is global and routed to all regions. Baseline 0.7 now distinguishes this from Lakeflow's regional scope.

These are design checks only. They do not replace the P3/P7/P8 staging proofs required by the plan.

## Ranked findings

| Rank | Finding | Severity | P0 effect |
|---:|---|---|---|
| 1 | `DBX-P0-013` — deployment authority bypasses UC-exclusive migration custody | High | Blocks P0; `CHANGES_REQUIRED` |
| 2 | `DBX-P0-014` — attestation DML and Jobs receipt contract are underspecified | Medium | Must be frozen before P3; affected P0 text must be corrected with finding 013 |

### DBX-P0-013: Deployment authority bypasses UC-exclusive migration custody

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Affected contract:
  - `AGENTS.md`, Product boundaries: “The UC operator owns the entire lease...”
  - `docs/decisions/0001-private-app-bundle.md`, Decision and Consequences
  - `docs/plans/product-plan.md`, Target architecture, Runtime identity model, Data-object and migration boundary steps 1-8, Bootstrap steps 4-11, readiness, P3/P6/P7/P8/P10, and staging kill-boundary tests
  - `docs/plans/documentation-plan.md`, every separated-duties and anchored-receipt route
- Evidence:
  1. Baseline 0.7 authorizes the deployment operator to create/manage the product Jobs and ACLs and requires Service Principal User on each configured Job run-as service principal.
  2. The resource-bootstrap plan is applied by that deployment identity before the UC handoff. Databricks grants the Job creator `IS OWNER` by default.
  3. `IS OWNER`/`CAN MANAGE` includes the ability to edit tasks, code references, configuration, run-as, and permissions. It also includes lower Job permissions.
  4. A run executes with the configured migration service principal's Unity Catalog privileges, including the temporary direct `CREATE TABLE` lease, no matter which permitted actor triggers it.
  5. The plan locks or leaves the deployer's local OS session but does not remove the deployer's Databricks Job ownership/management or account-level service-principal-use authority. Another browser, workstation, CLI profile, compromised refresh credential, transitive group, or workspace administrator remains outside the local capsule/session control.
  6. The same mutable Job is later treated as the source of the Databricks-anchored seal receipt. A principal able to edit/run it can weaken the receipt unless the run's immutable task/config/code identity and custody are independently constrained and verified.
- User/system impact: The deployment actor can obtain a path to arbitrary code execution under the temporarily privileged migration principal during the nominal UC-only phase. That violates the no-arbitrary-SQL contract, undermines independent approval, and lets the same actor influence both the protected change and the evidence that supposedly unlocks runtime. A local two-account handoff is not a platform separation-of-duties control while this remote authority remains.
- Required acceptance condition:
  1. Define an exact platform-enforced custody state for the migration Job. Before any DDL lease, no deployment human, deployment group, or transitive group may retain `IS_OWNER` or `CAN_MANAGE` on the Job. The UC operator group may retain only the intended `CAN_MANAGE_RUN`; name the single non-human Job owner and every residual administrator boundary.
  2. Audit and bind Job owner, complete Job ACL, task definitions, code artifact/location permissions, run-as identity, and relevant Service Principal User/Manager grants before lease, at both invocations, before revoke, before receipt acceptance, and before restoring deployment control. Visibility denial or an unexpected administrator/group path fails closed.
  3. Remove the deployment actor's ability to use or reconfigure the migration run-as principal for the lease interval. If Bundle deployment requires temporary Service Principal User or Job management, make its exact grant, removal, proof, later restoration, and owning account/workspace administrator part of the reviewed resource/identity plan. Do not leave the role merely because the deployer needed it during bootstrap.
  4. Choose a Bundle topology that still permits the later runtime plan without silently regranting migration-Job control while the lease is active. Acceptable designs can include a dedicated non-human owner, separately managed bootstrap/runtime bundles, or a reviewed custody-transfer resource operation; the saved plan must show the transition and rollback.
  5. Treat default workspace-admin `CAN MANAGE` and owner/run-as reassignment as an explicit residual control. Read and report `RestrictWorkspaceAdmins`; require the customer-approved setting or document the named trusted-admin exception. The setting alone does not cure human Job ownership or `CAN_MANAGE`.
  6. Bind an accepted receipt to the exact run/task definition and immutable code/source digest, run-as principal, invoking actor, two allowed parameters, terminal state, and attested ledger row. Restoring a Job definition after an unauthorized run must not make that run acceptable.
  7. Add adversarial staging cases: deployment actor attempts edit, permission change, alternate code, run-as change, concurrent run, and second invocation from another session during every lease/Job/revoke/attestation boundary. Each must be denied by Databricks permissions, not only detected by a later local check.

### DBX-P0-014: Attestation DML and Jobs receipt contract are underspecified

- Verdict: `PASS_WITH_FOLLOW_UP` once `DBX-P0-013` is resolved
- Severity: medium
- Owner and target: P3 installer/migration owner, revalidated in P7 and P8
- Affected contract: migration-ledger ownership, `SEAL_ATTEST`, second idempotent migration Job invocation, deployment return, recovery after actor/token/process loss, and receipt retention
- Evidence:
  1. The data-object boundary gives persistent ledger read/write only to the migration principal and says the UC operator may perform one digest-only attestation write.
  2. The UC-operator identity row names ownership or `MANAGE`, parent use, warehouse `CAN_USE`, and Job `CAN_MANAGE_RUN`, but does not name table `MODIFY`/`SELECT` on `dbtobsb_migration_ledger` or an exact temporary grant/revoke.
  3. Unity Catalog `MANAGE` allows privilege management but does not itself grant data access, and schema ownership does not confer child-table data privileges.
  4. The plan says the second fixed Job “publishes” a terminal receipt through Jobs but does not select a task/output mechanism, safe schema, task-run lookup, pagination, retention, duplicate/repair precedence, or the response when the Databricks run has aged out.
- User/system impact: A literal implementation can fail at the attestation write or can improvise a broader table grant that the approved envelope and effective-authority audit do not show. An ambiguous or expired Jobs result can strand the deployer, or a weak output check can accept the wrong run. These are fail-closed implementation gaps rather than proof that the design is infeasible.
- Required implementation acceptance:
  1. Either add the UC operator's exact, temporary, envelope-bound parent use plus ledger `SELECT`/`MODIFY` privileges and their targeted revoke/effective verification, or redesign attestation so the fixed Job can derive the approved invoking actor and verified seal without a human table DML grant. `MANAGE` must not be described as data access.
  2. Freeze the allowed fixed statement/state transition and row predicate. No SQL, table name, operation mode, actor identity, or arbitrary payload may arrive through Job parameters; the only Job inputs remain the nonsecret migration ID and approved digest.
  3. Specify the second invocation's deterministic state machine: an already-applied migration plus matching attestation and absent effective DDL emits the same receipt; every other state fails without DDL or unrelated DML.
  4. Select one GA Jobs carrier and exact task type, such as a small notebook exit value or bounded task value. Define the receipt's closed JSON schema and size, its run/task lookup, every `get-run` page, repair/duplicate precedence, output-limit behavior, and the permissions needed by the returning deployer.
  5. Bind the receipt to installation/migration/envelope/source/build digests, Job and task run IDs, exact task/config/code digest, run-as principal, safe invoking-actor fingerprint, the same two parameters, attestation fingerprint, no-effective-DDL fingerprint, terminal result, and issuance time. Reject a locally copied value without the matching current Jobs run and ledger state.
  6. Account for Databricks' 60-day run retention. The 30-day local checkpoint can be compatible only if runtime return and every recovery are bounded within the shorter verified window; otherwise require re-attestation or a separately permissioned durable Databricks receipt object. Test the aged-out, unavailable, repaired, duplicate, and ambiguous cases.

## Prior-finding disposition

| Finding | Sixth re-review disposition |
|---|---|
| `DBX-P0-001` | `RESOLVED_FOR_P0`; observed and collector Jobs retain distinct run-as identities. |
| `DBX-P0-002` | `RESOLVED_FOR_P0`; bounded reconciliation and visible degradation remain explicit. |
| `DBX-P0-003` | `RESOLVED_FOR_P0`; shared App identity remains separate from human action authorization. |
| `DBX-P0-004` | `RESOLVED_FOR_P0`; platform prerequisites remain typed and fail closed. |
| `DBX-P0-005` | `RESOLVED_FOR_P0`; required runtime public egress remains zero and deployment supply-chain inputs are bounded. |
| `DBX-P0-006` | `RESOLVED_FOR_P0`; enrichment is absent from base, separately installed, dedicated-principal, pair-filtered, and removable. Optional enablement still needs its planned P4/D4E/P8 evidence. |
| `DBX-P0-007` | `RESOLVED_FOR_P0`; App access groups and resource authorization remain separate. |
| `DBX-P0-008` | `RESOLVED_FOR_P0`; optional action identities, tables, secret scope, and fixed role Job remain isolated. |
| `DBX-P0-009` | `RESOLVED_FOR_P0`; protected Direct plans and stopped-then-`bundle run` App lifecycle remain correct. |
| `DBX-P0-010` | `RESOLVED_FOR_P0`; Direct manages supported resources, fixed migration code owns DDL, bindings require verified existing objects, and collectors have no DDL. |
| `DBX-P0-011` | `RESOLVED_FOR_P0`; revoke is approved with the lease, cleanup-first recovery is mandatory, and seal runs after cancel/wait. The authenticity of Job custody/receipt is reopened separately as `DBX-P0-013`/`014`. |
| `DBX-P0-012` | `RESOLVED_FOR_P0`; no Direct schema grants exist and exact targeted changes preserve foreign assignments. |
| `DBX-P0-F01` | `RESOLVED_FOR_P0`; baseline 0.7 now explicitly covers ownership, implied `ALL PRIVILEGES`, `MANAGE`, transitive groups, caller visibility, and pagination. P3/P7/P8 implementation qualification remains mandatory. |
| `DBX-P0-F02` | `RESOLVED_FOR_P0`; baseline 0.7 names the `(workspace_id, job_id)` scope table, migration-Job sole writer, DML-only updates, exact regional/global disclosure, three snapshots, exclusions, and snapshot-semantics gate. It remains disabled until optional P4/D4E evidence passes. |

## Author-file outcome

| Author file or set | Outcome | Databricks conclusion |
|---|---|---|
| `README.md` | `CHANGES_REQUIRED` | The two-account/capsule model is clear, but the claim that the UC operator controls lease-to-seal is stronger than the current Job ACL/owner model. |
| `AGENTS.md` | `CHANGES_REQUIRED` | The rules correctly prohibit arbitrary SQL and unsafe resume, but must also prohibit deployment Job ownership/management and migration-SP use during the lease. |
| `docs/index.md` | `PASS` | The planning index introduces no independent platform claim. |
| `docs/decisions/0001-private-app-bundle.md` | `CHANGES_REQUIRED` | The accepted decision needs a platform-enforced migration Job custody transition and exact attestation/receipt contract. |
| `docs/plans/product-plan.md` | `CHANGES_REQUIRED` | The end-to-end journey is coherent but its decisive separation-of-duties invariant is not enforced by Databricks permissions. |
| `docs/plans/review-process.md` | `PASS_WITH_FOLLOW_UP` | The reviewer remit is sound; add Job owner/manager/run-as-custody and receipt-authenticity checks to P3/P6/P7/P8. |
| `docs/plans/documentation-plan.md` | `CHANGES_REQUIRED` | D2 and related pages would currently teach a local handoff as sufficient despite retained remote Job authority. |
| `docs/research/source-register.md` | `CHANGES_REQUIRED` | Add current Job creator/owner/CAN_MANAGE semantics, Bundle `IS_OWNER` support, `RestrictWorkspaceAdmins`, Unity Catalog `MANAGE` versus DML, and Jobs output/60-day retention before revising the contract. |

## P0-P10 Databricks coverage matrix

These are planning outcomes, not claims that implementation evidence already exists.

| Part | Planning outcome | Databricks conclusion and next evidence |
|---|---|---|
| P0 — Product contract | `CHANGES_REQUIRED` | Resolve `DBX-P0-013`; freeze `DBX-P0-014`; re-review the complete changed identity/resource/migration/receipt path. |
| P1 — Capture library | `PASS` | Pure parsing, closed schemas, allowlists, and no platform mutation remain appropriate. |
| P2 — Collector and reconciliation | `PASS` | Separate collector run-as, exact DML, no DDL, `ALL_DONE`, and bounded reconciliation are unaffected. |
| P3 — Bundle installer | `CHANGES_REQUIRED` | Add platform-enforced migration Job custody, migration-SP role lifecycle, immutable code/run receipt binding, and exact attestation/receipt mechanics before implementation acceptance. |
| P4 — App read-only MVP | `PASS_WITH_FOLLOW_UP` | Curated-only base remains sound; optional enrichment stays disabled until the named scope/snapshot/live-denial evidence passes. |
| P5 — Job onboarding | `PASS` | Five-state scanner, owner approval, source patch, and no direct customer-Job mutation remain sound. |
| P6 — Controlled actions | `CHANGES_REQUIRED` | Its repeated migration-envelope handoff inherits `DBX-P0-013`; do not reuse the unsafe custody path for action objects. |
| P7 — Security and operations | `CHANGES_REQUIRED` | Runbooks must audit/revoke Job owner/manager and service-principal-use paths, not only Unity Catalog grants and local profiles. |
| P8 — Bounded live proof | `CHANGES_REQUIRED` | Add permission-enforced adversarial custody tests, exact receipt retrieval/retention cases, and final owner/ACL/SP-role inventory. Keep cost bounded and resources stopped. |
| P9 — Optional intelligence | `PASS` | AI remains outside capture, privilege, migration, seal, and authorization. |
| P10 — Private alpha | `CHANGES_REQUIRED` | Do not present the two-account route as regulated separated duties until the remote Databricks custody boundary passes P3/P7/P8. |

## Explicit verdict

`CHANGES_REQUIRED`

The private Databricks App deployed through a plain-YAML Direct Bundle remains the recommended product starting point. Baseline 0.7 also establishes a strong local two-account handoff, complete effective-authority contract, customer-grant preservation model, and optional enrichment boundary.

It cannot yet be accepted as the P0 regulated separated-duties baseline. Distinct OS accounts and a signed local capsule do not remove the deployment actor's Databricks `IS_OWNER`/`CAN_MANAGE` and migration-service-principal authority. Until the migration Job has platform-enforced custody for the entire lease-to-receipt interval, the deployer can influence the privileged code path and its purported remote receipt. Resolve `DBX-P0-013`, freeze `DBX-P0-014`, then request a seventh Databricks re-review of the complete changed author set.
