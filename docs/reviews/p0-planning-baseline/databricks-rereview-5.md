# Databricks platform fifth re-review: P0 planning baseline 0.6

- Author-set SHA-256: `96257d1f55152d92d303852a9f057a419c0d77bdc5a553cb4d92cea0cf4b173e`
- Date: 2026-07-15
- Reviewer: independent Databricks platform specialist
- Verdict: `PASS_WITH_FOLLOW_UP`
- Cloud mutation: none; no Azure or Databricks API, App, Job, warehouse, compute, or Unity Catalog object was created, changed, or started
- Pinned CLI source reviewed: Databricks CLI `v1.7.0`, commit `2f68ee4951ef96fa9d99e40c8ebadccf08412d58`

## Immutable input verification

The review input was limited to:

- `README.md`
- `AGENTS.md`
- `docs/index.md`
- every Markdown file under `docs/decisions`
- every Markdown file under `docs/plans`
- every Markdown file under `docs/research`

I sorted the paths, calculated SHA-256 for each file, sorted those records by path, and hashed that stream. The pre-review digest independently reproduced the requested value exactly:

```text
96257d1f55152d92d303852a9f057a419c0d77bdc5a553cb4d92cea0cf4b173e
```

The same digest was reproduced after this report was written. This report is outside the author-set scope. No author file changed during the review.

## Executive outcome

Baseline 0.6 is safe to accept as the Databricks P0 architecture. It selects the preservation model recommended by the fourth review:

- The dedicated schema is an existing, typed, customer-owned prerequisite. The Bundle does not create, adopt, destroy, or attach a Direct `grants` list to it.
- The initial saved Direct plan selects only the fixed migration Job. Direct continues to manage supported Job/App resources and ACLs, not table/view DDL or customer-schema privileges.
- One reviewed migration envelope describes only product-recorded targeted parent-use grants, one direct temporary migration-principal `CREATE TABLE` lease, its identical targeted revoke, and fixed data/object operations.
- An attended OAuth U2M Unity Catalog operator sends the signed privilege statements through the Statement Execution API. Neither a plan, user, App, Job parameter, nor AI supplies executable SQL.
- `RECOVERY_AUDIT` runs before every mutation or resume. Residual direct or effective DDL authority forces cleanup-only `SEAL_REQUIRED`; runtime remains unavailable until cancellation/wait, targeted revoke, and independent absence verification succeed.
- The fixed migration Job owns DDL and non-App object grants. The collector and optional enrichment Job are DML-only.
- App bindings are regenerated only after seal and object verification, reference only existing objects, and remain the sole owner of App-generated parent/object grants.
- Retain-uninstall transfers product-object ownership to a named customer owner, removes only product-recorded privileges, and leaves the customer schema intact. Schema deletion is a separate customer-approved operation.
- Optional system enrichment is absent and `DISABLED` in the base install. Its optional extension has a dedicated principal, paused fixed-code Job, exact source schemas, three snapshot tables, sanitized App views, and no App `system` access.

There is no blocking or high-severity finding. Two bounded implementation follow-ups remain: P3 must freeze and qualify a complete effective-authority audit rather than treating one metadata row set as sufficient, and optional P4/D4E must freeze the onboarded-Job allowlist plus snapshot semantics while accurately distinguishing regional Lakeflow scope from account-global billing scope. Both capabilities already fail closed in baseline 0.6, so neither blocks P0 acceptance.

## Current authoritative sources checked

### Apps, Bundles, and lifecycle

- [Azure Databricks Apps](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/) — Apps run on billed serverless compute, require Premium, and require explicit workspace-admin enablement for compliance-security-profile workspaces.
- [Direct Bundle engine](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/direct) — Direct is the default for new Bundles from CLI 1.3.0, keeps local and remote state separately, supports detailed plans, and is the recommended direction as the Terraform engine heads toward deprecation.
- [Bundle resource reference](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/resources) and [CLI 1.7.0 resource types](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/config/resources.go) — Jobs, Apps, schemas, and other platform resources exist, but there is no generic managed Delta table/view collection.
- [Add a Unity Catalog table resource to an App](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/tables) — a bound table/view must already exist; the App service principal receives parent use plus object access automatically; binding removal removes the App's object grant and attempts hierarchical parent revocation.
- [Manage Apps with Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial) and [CLI 1.7.0 App runner](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/run/app.go#L44-L99) — resource deployment and App code/start are separate; `bundle run <app-key>` is the correct Bundle lifecycle.

### Authentication, SQL execution, and Unity Catalog

- [OAuth U2M](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/auth/oauth-u2m) — OAuth is the preferred attended user authorization path for the CLI, SDK, and REST APIs; unified authentication handles short-lived access tokens.
- [Statement Execution API](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/sql-execution-tutorial) — an authenticated OAuth user with Databricks SQL entitlement, warehouse `CAN_USE`, and the required object privileges can execute statements on a SQL warehouse.
- [`GRANT`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/security-grant) and [`REVOKE`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/security-revoke) — exact additive grants and targeted idempotent revokes are supported; they do not require authoritative replacement of all assignments.
- [`SHOW GRANTS`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/security-show-grant) and [`SCHEMA_PRIVILEGES`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/information-schema/schema_privileges) — inherited and direct privileges can be distinguished, but result visibility depends on the caller.
- [Unity Catalog permissions concepts](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/access-control/permissions-concepts) — catalog privileges inherit to schemas, schema ownership implies all schema capabilities without an explicit grant row, and `ALL PRIVILEGES` implies applicable privileges such as schema `CREATE TABLE` without expanding them into separate rows.
- [Get effective permissions API](https://docs.databricks.com/api/workspace/grants/geteffective) and [CLI 1.7.0 GA `grants get-effective`](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/cmd/workspace/grants/grants.go#L139-L185) — the GA endpoint reports direct plus parent-inherited privileges and must be paginated until `next_page_token` is absent.
- [Service principals](https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/service-principals) — service principals can belong to groups, so effective authorization review must account for group membership as well as direct assignments.

### CLI 1.7.0 behavior

- [Selected-resource traversal](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/deployplan/plan.go#L210-L243) — a selected resource includes existing grants/permissions subnodes and transitive dependencies. Because baseline 0.6 has no schema resource in the Bundle, no customer-schema grants node is selected.
- [Direct grants adapter](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/dresources/grants.go#L120-L193) — every plan-time remote principal omitted from desired assignments is treated as removed. Baseline 0.6 correctly avoids this adapter for the customer schema.
- [Direct saved-plan state](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/bundle_plan.go#L42-L115) and [plan-time action calculation](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/bundle_plan.go#L207-L305) — a saved plan captures Direct state and a fixed action. Baseline 0.6 no longer attempts to precompute a Direct privilege seal against a future bootstrap state.
- [Direct deploy phase](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/phases/deploy.go#L131-L205) — current staged source and pre-deploy behavior justify the plan sidecar and the explicit prohibition on mutation-bearing pre-deploy scripts.

### Optional system enrichment

- [Jobs system tables](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs) — `system.lakeflow` includes all account workspaces in the same cloud region, has schema-wide access, exposes identity and user-controlled fields, and now also contains Pipeline tables, two of which are Preview.
- [System tables](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/) — a principal needs `USE CATALOG` plus schema-level `USE SCHEMA` and `SELECT`; exact table-only source grants are not available for this design.
- [Billing system table](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/billing) — `system.billing.usage` is account-global and routed to every region, not limited to the current workspace or region.
- [Monitor Lakeflow Job costs](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs-cost) — direct Job attribution and allocated shared-resource cost must remain distinct.

### Read-only local validation

- Confirmed the installed binary reports `Databricks CLI v1.7.0`.
- Verified the immutable `v1.7.0` source checkout is commit `2f68ee4951ef96fa9d99e40c8ebadccf08412d58`.
- Ran `go test ./bundle/direct ./bundle/deployplan ./bundle/direct/dresources ./cmd/workspace/grants`; all packages passed (`cmd/workspace/grants` has no test files).
- Confirmed CLI 1.7.0 exposes GA `grants get-effective` with pagination and includes no generic managed Delta table/view resource.

These checks did not authenticate to or mutate a Databricks workspace. They do not replace the bounded P3/P8 workspace qualification required by the plan.

## Recommended-practice and feature-status check

| Topic | Current position | Baseline 0.6 outcome |
|---|---|---|
| Private Databricks App | Supported, Premium, billed while running; compliance-profile workspaces require explicit enablement | `PASS`; explicit start, bounded tests, stop/default cleanup, and readiness gates are present |
| Direct Bundles | Current recommended direction and default for new CLI 1.3+ Bundles; Terraform engine is headed for deprecation | `PASS`; exact CLI 1.7.0 and `bundle.engine: direct` remain pinned |
| Managed table/view resources | No generic Delta table/view Bundle resource in CLI 1.7.0 | `PASS`; fixed migration Job owns DDL and bindings wait for verified objects |
| Direct schema grants | Authoritative reconciliation can remove omitted principals | `PASS`; the customer schema is absent from Direct and no schema `grants` block exists |
| Targeted privilege mutation | GA SQL `GRANT`/`REVOKE`, OAuth U2M, and Statement Execution are supported | `PASS`; signed fixed statements, no arbitrary SQL, exact diff, and cleanup-first recovery are appropriate |
| Effective permissions | GA API/CLI support parent inheritance; ownership, implied `ALL PRIVILEGES`, group membership, visibility, and pagination still require explicit evaluation | `PASS_WITH_FOLLOW_UP`; see `DBX-P0-F01` |
| System enrichment | System-schema grants are broad; Lakeflow covers the account's workspaces in the current cloud region, while billing is account-global | `PASS_WITH_FOLLOW_UP`; base is safely disabled and isolated; see `DBX-P0-F02` |
| App telemetry | Public Preview | `PASS`; optional and disabled for regulated v1 |
| AppKit | Active first-party direction but still pre-1.0 | `PASS`; evaluation is deferred and not a regulated-MVP dependency |
| Experimental `job_runs` | Not needed by this design | `PASS`; ordinary Job resources plus `bundle run` remain the required path |
| Marketplace | A later distribution path, not required for private product validation | `PASS`; provider/package claims remain gated on written confirmation |

No new feature justifies widening the baseline. In particular, App telemetry, AppKit, AI, Preview audit enrichment, ABAC grant policies, and Experimental Bundle resources should not replace the deterministic base path.

## Focused acceptance

| Acceptance condition | Outcome | Databricks conclusion |
|---|---|---|
| Customer-owned schema and no Direct schema grants | `PASS` | Schema, owner, marker/emptiness, retention, and App-binding authority are typed inputs; the Bundle has no schema resource or grant node. |
| Saved Direct resource bootstrap | `PASS` | Selection contains only the fixed migration Job and its dependencies/ACL; it contains no schema, App binding, table/view DDL, or hidden mutation. |
| Attended U2M targeted lease and revoke | `PASS` | Statement Execution runs fixed signed `GRANT`/`REVOKE` as the authorized human operator. The migration Job receives only a nonsecret ID and digest and cannot execute supplied SQL. |
| Seal ready before migration compute | `PASS` | One envelope approval covers an identical-principal lease/revoke pair; live lease verification and current operator authority precede Job start. |
| Cleanup-first resume | `PASS` | Every invocation audits first. `SEAL_REQUIRED` permits only cancel/wait, targeted revoke, verification, and safe output; no App, collector, role, enrichment, or further migration work may start. |
| Effective/inherited authority verification | `PASS_WITH_FOLLOW_UP` | The fail-closed contract is correct. P3 must implement and qualify ownership, implied privileges, group membership, visibility, and pagination explicitly. |
| Foreign and App grant preservation | `PASS` | Exact `GRANT`/`REVOKE` statements affect one product principal/privilege pair. Foreign assignments are context, not desired state. App bindings remain App-managed. |
| Runtime binding order | `PASS` | Runtime plan is regenerated only after `SEALED` plus independent object/owner/version/grant verification and binds only existing objects. |
| Collector/no hidden DDL | `PASS` | Collector is DML-only on three named evidence tables. Mutation-bearing pre-deploy hooks and required Experimental `job_runs` remain prohibited. |
| Retained ownership and uninstall | `PASS_WITH_FOLLOW_UP` | The ordering is correct: remove App bindings, transfer retained objects, remove exact product grants, remove Jobs, leave customer schema; P7/P8 must prove view-owner and residual-access state. |
| Optional isolated system enrichment | `PASS_WITH_FOLLOW_UP` | Dedicated principal/paused Job/exact schemas/three targets/no App source access close the P0 identity gap. Filter and snapshot details remain an optional enablement gate. |

## Prior-finding disposition

| Finding | Fifth re-review disposition |
|---|---|
| `DBX-P0-001` | `RESOLVED_FOR_P0`; separate observed and collector Jobs/run-as identities plus `ALL_DONE` invocation remain intact. |
| `DBX-P0-002` | `RESOLVED_FOR_P0`; bounded reconciliation, visible degradation, 20-minute target, and idempotent AttemptKey path remain intact. |
| `DBX-P0-003` | `RESOLVED_FOR_P0`; shared App platform identity remains distinct from deny-by-default actor/browser/role authorization. |
| `DBX-P0-004` | `RESOLVED_FOR_P0`; tier, compliance, UC, identity, CLI/Direct, environment, Python, dbt, SQL-channel, and egress readiness stay typed. |
| `DBX-P0-005` | `RESOLVED_FOR_P0`; zero required runtime public egress and signed/locked deployment inputs remain explicit. |
| `DBX-P0-006` | `RESOLVED_FOR_P0_WITH_FOLLOW_UP`; enrichment is absent from base and has a dedicated principal, paused fixed Job, exact system schemas, DML-only three-snapshot target, sanitized views, and removal proof. `DBX-P0-F02` must close before optional enablement. |
| `DBX-P0-007` | `RESOLVED_FOR_P0`; named App groups and separate App ACL/resource grants remain exact. |
| `DBX-P0-008` | `RESOLVED_FOR_P0`; action principal/table/Job/secret boundaries and fixed role Job remain unchanged. |
| `DBX-P0-009` | `RESOLVED_FOR_P0`; protected saved Direct plans, stopped App lifecycle, and non-redeploying `bundle run` sequence remain intact. |
| `DBX-P0-010` | `RESOLVED_FOR_P0`; Direct manages supported runtime resources only, the customer schema is typed input, fixed migration code owns DDL/non-App grants, bindings wait for verified objects, collector DDL is prohibited, and no hidden pre-deploy or required Experimental path remains. |
| `DBX-P0-011` | `RESOLVED_FOR_P0`; the invalid pre-bootstrap Direct seal is gone. The signed targeted revoke is approved with the lease, is ready before compute, runs after cancel/wait in `finally`, and is the only mutation allowed on a dirty restart. |
| `DBX-P0-012` | `RESOLVED_FOR_P0`; the Bundle contains no customer-schema grant node, so Direct cannot reconcile away App or customer grants. Product privilege changes are exact targeted statements, and uninstall removes only recorded product additions. |

## Findings

There are no blocking or high-severity findings.

| Rank | Count | P0 effect |
|---|---:|---|
| Blocking | 0 | None |
| High | 0 | None |
| Medium | 2 | Safe, fail-closed follow-ups assigned to P3 and optional P4/D4E |
| Low | 0 | None |

### DBX-P0-F01: Freeze the complete effective-authority audit before P3 acceptance

- Classification: `PASS_WITH_FOLLOW_UP`
- Severity: medium
- Owner and target: P3 installer/security owner; validate again in P7 and P8
- Affected contract: `RECOVERY_AUDIT`, `PRIVILEGE_LEASE_VERIFY`, `DATA_SEAL_VERIFY`, readiness, upgrade/resume, and delete-uninstall
- Evidence:
  - `SHOW GRANTS` and `SCHEMA_PRIVILEGES` expose direct/inherited rows, but caller visibility is bounded.
  - GA `grants get-effective` covers direct plus parent-object inheritance and is paginated; it does not remove the need to interpret principals and capabilities.
  - `ALL PRIVILEGES` implies `CREATE TABLE` without an explicit `CREATE TABLE` row.
  - Schema ownership implies all schema capabilities without an explicit grant row.
  - Service principals can be group members; nested/group-owned paths can convey authority not represented as a direct grant to the service principal.
- Why this does not block P0: Baseline 0.6 already defines the correct fail-closed invariant, assigns negative/live tests, and prohibits progress whenever the proof is incomplete. No author claim permits a visibility-limited result to become `SEALED`.
- Required implementation acceptance:
  1. Resolve and bind the migration service principal's immutable identity plus current canonical SQL principal; a renamed or replaced identity invalidates the envelope.
  2. Use a caller that can see the complete object grant set. Treat permission denial, partial visibility, malformed output, or an unconsumed page token as `SECURITY_CLEANUP_REQUIRED`, never “absent.”
  3. Enumerate direct and parent-inherited assignments, schema/catalog ownership, effective `MANAGE`, `ALL PRIVILEGES`, and every transitive group membership that applies to the migration principal. Expand implied privileges before evaluating `CREATE TABLE`.
  4. Keep product direct assignments distinct from customer/group/inherited paths. The product may revoke only its exact direct lease; every other path names the responsible customer owner and blocks.
  5. Fixture direct schema `CREATE TABLE`, catalog-inherited `CREATE TABLE`, schema/catalog `ALL PRIVILEGES`, schema-owner and owner-group capability, direct/nested group membership, pagination including an empty page with a next token, visibility loss, principal rename/recreation, and a clean no-authority state.
  6. Live P8 qualification must prove the chosen API/SQL/identity combination reports the same authority that the migration Job actually receives; do not use a mutating canary table as the negative check.

### DBX-P0-F02: Freeze optional enrichment scope and snapshot semantics before enablement

- Classification: `PASS_WITH_FOLLOW_UP`
- Severity: medium
- Owner and target: optional system-enrichment owner; P4/D4E before the capability can be enabled, with P7/P8 removal/live proof
- Affected contract: optional enrichment readiness, fixed Job, three snapshot tables/views, cost confidence, access review, and uninstall
- Evidence:
  - Baseline 0.6 now names the principal, Job, two source schemas, three target tables, and App denial correctly.
  - `system.lakeflow` contains all account workspaces in the same region and grants schema-wide visibility, including tables the fixed code must not consume.
  - `system.billing.usage` is account-global and routed to every region. Several author passages say “account/region,” which is not precise enough for the optional governance approval.
  - The contract says “allowlisted onboarded Jobs” but does not yet name the authoritative allowlist object, its writer, or how the enrichment principal obtains it without gaining raw evidence access.
  - Exact source columns, snapshot keys, watermark/lookback, late-arriving rows, SCD2 handling, idempotent merge/delete behavior, and disabled-to-enabled bootstrap window are deliberately left open.
- Why this does not block P0: The capability is absent from the base manifest, Job set, App bindings, readiness requirement, and grants. Failure leaves it `DISABLED` or visibly `DEGRADED`; base capture and cost-confidence states remain complete.
- Required implementation acceptance:
  1. State the exposure exactly: Lakeflow is account-wide within the current cloud region; billing is account-global. Record that schema grants expose every table in each accepted schema to the dedicated principal even though fixed code queries only an allowlist.
  2. Add one typed, product-owned minimal scope source containing at least the installation workspace and `(workspace_id, job_id)` allowlist, name its only writer, and give the enrichment principal `SELECT` on that scope object only. Do not derive scope from user-supplied Job parameters.
  3. Freeze exact stable source tables/columns and explicitly exclude creator/run-as emails, arbitrary names/descriptions/tags, job parameters, cross-workspace rows, unonboarded Jobs, and all Pipeline data unless a later reviewed extension adds them.
  4. Define each snapshot's key, event/SCD2 semantics, watermark/lookback, late data, deduplication, idempotent MERGE/delete behavior, retention, freshness state, and billing attribution confidence.
  5. Prove that a cross-workspace or unonboarded row cannot be persisted even when its `job_id` collides with an onboarded Job in another workspace. The filter key is the workspace/Job pair.
  6. Test fresh enablement, repeated no-op, late data, source denial, filter-scope change, partial write, retry, disable, retain/delete uninstall, and complete source-grant removal. Base install/uninstall must continue to show zero `system` grant and no enrichment object/Job.

## Author-file outcome

| Author file or set | Outcome | Databricks conclusion |
|---|---|---|
| `README.md` | `PASS` | The customer-local boundary, customer-owned schema, targeted migration envelope, collector no-DDL rule, and optional enrichment isolation are accurate. |
| `AGENTS.md` | `PASS` | The working agreement correctly prevents Direct schema grants, arbitrary SQL, hidden mutation, collector/enrichment DDL, broad App system access, and unsafe resume. |
| `docs/index.md` | `PASS` | The planning index introduces no independent platform claim. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS_WITH_FOLLOW_UP` | The decision is now executable. Clarify Lakeflow regional versus billing global source scope before optional enrichment publication. |
| `docs/plans/product-plan.md` | `PASS_WITH_FOLLOW_UP` | The base resource/privilege/data/runtime order is accepted. P3 and optional P4 must satisfy the two follow-ups above. |
| `docs/plans/review-process.md` | `PASS` | Databricks focus now includes Direct-versus-targeted grants, effective access, enrichment scope, and feature maturity. |
| `docs/plans/documentation-plan.md` | `PASS_WITH_FOLLOW_UP` | D2/D4E/D5 include the right pages and evidence. They must document the final effective-audit algorithm and exact global/regional enrichment scope. |
| `docs/research/source-register.md` | `PASS_WITH_FOLLOW_UP` | Sources are current and primary. Add the GA effective-permissions API/CLI source and make account-global billing scope explicit before P3/D4E implementation. |

## P0-P10 Databricks coverage

These outcomes accept or qualify the planning contract; they do not claim that future implementation evidence already exists.

| Part | Planning outcome | Databricks conclusion and next evidence |
|---|---|---|
| P0 — Product contract | `PASS_WITH_FOLLOW_UP` | Baseline 0.6 is coherent and safe. Carry `DBX-P0-F01` to P3 and `DBX-P0-F02` to optional P4/D4E. |
| P1 — Capture library | `PASS` | Pure parsing, closed artifact schemas, allowlists, and no platform dependency remain appropriate. Optional system rows must not enter canonical artifact parsing. |
| P2 — Collector and reconciliation | `PASS` | Separate run-as, DML on three tables, no DDL/system access, `ALL_DONE` invocation, and bounded reconciliation remain correct. |
| P3 — Bundle installer | `PASS_WITH_FOLLOW_UP` | Customer schema outside Direct, Job-only bootstrap, protected envelope, U2M lease/seal, cleanup-first resume, existing-object bindings, and stopped/run lifecycle are accepted. Complete `DBX-P0-F01` before P3 can pass. |
| P4 — App read-only MVP | `PASS_WITH_FOLLOW_UP` | Curated-only stateless App and honest cost states remain sound. Base must pass with no `system` grant; optional enablement cannot pass until `DBX-P0-F02` closes. |
| P5 — Job onboarding | `PASS` | Existing-owner approval, five scanner states, source-controlled patch, and no direct customer-Job mutation introduce no Databricks regression. |
| P6 — Controlled actions | `PASS_WITH_FOLLOW_UP` | The same targeted envelope and cleanup-first rules apply; P6 must consume the qualified P3 audit rather than implement a second privilege algorithm. |
| P7 — Security and operations | `PASS_WITH_FOLLOW_UP` | Prove persistent owner access, retained-view/table ownership transfer, exact product-grant removal, foreign preservation, and complete optional system-reader removal. |
| P8 — Bounded live proof | `PASS_WITH_FOLLOW_UP` | Required proof is correctly cost-bounded: every kill boundary, effective seal, no-op App query, synthetic customer grant, enrichment isolation, and final stopped/removed inventory. |
| P9 — Optional intelligence | `PASS` | AI stays outside capture, authorization, migration, privilege audit, seal, and validation. Current Preview/recent features remain optional. |
| P10 — Private alpha | `PASS_WITH_FOLLOW_UP` | Repeatability remains plausible after P3/P4 gates. Non-author deployment and UC operators must complete recovery, retain/delete choice, and uninstall without SQL, IDs, paths, or YAML. |

## Final verdict

`PASS_WITH_FOLLOW_UP`

Baseline 0.6 resolves the fourth review's architecture defects without introducing a new high-risk platform dependency. The private Databricks App plus plain-YAML Direct Bundle remains the recommended starting point. Direct manages supported Jobs/App resources; the customer owns the schema; one signed targeted U2M privilege/data envelope controls the temporary DDL lease; cleanup is the only allowed dirty-start behavior; fixed migration code owns data DDL; App bindings wait for verified objects; and optional system enrichment is isolated and absent by default.

`DBX-P0-010`, `DBX-P0-011`, and `DBX-P0-012` are closed for P0. `DBX-P0-006` is closed for P0 with a bounded optional-capability follow-up. P0 may proceed, but P3 must not claim `SEALED` until the full effective-authority algorithm in `DBX-P0-F01` is qualified, and optional enrichment must remain `DISABLED` until `DBX-P0-F02` is closed.
