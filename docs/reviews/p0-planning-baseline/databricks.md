# Databricks platform review: P0 planning baseline

- Reviewed input: pre-commit working tree
- Frozen file-set SHA-256: `3a637dae8ac48cf7cea7c84ebbec5c9d39cd63a8cd75105f689f5478a7023d98`
- Date: 2026-07-15
- Reviewer: Databricks product and platform specialist
- Verdict: `CHANGES_REQUIRED`
- Blockers: none; the findings below are correctable without changing the accepted private-App-plus-Bundle direction

## Executive verdict

The private Databricks App, plain-YAML Declarative Automation Bundle, native Lakeflow dbt archive, Unity Catalog storage, and optional-AI boundary are the right platform baseline. The planning set is unusually strong on ephemeral App state, restricted raw evidence, signed URLs, preview labeling, cost cleanup, and proof of capture rather than proof of deployment.

P0 cannot yet be accepted because the current diagram assigns separate dbt and collector identities to tasks that appear to be in one Lakeflow Job even though a job's `Run as` identity applies to its tasks. `ALL_DONE` also does not establish a recovery path when the whole run is cancelled or reaches a job-level timeout. Required audit correlation currently risks depending on the Public Preview audit system table, App action identity is unresolved, and platform readiness, egress, system-table scoping, and cost-attribution behavior need explicit testable contracts.

## Primary sources checked

- [Databricks Apps overview](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/)
- [Key concepts in Databricks Apps](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts)
- [Configure App permissions](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/permissions)
- [Configure App authorization](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/auth)
- [App best practices](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/best-practices)
- [Run dbt transformations in Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/how-to/use-dbt-in-workflows)
- [Lakeflow Job privileges and `Run as`](https://learn.microsoft.com/en-us/azure/databricks/jobs/privileges)
- [Run Job task](https://learn.microsoft.com/en-us/azure/databricks/jobs/tasks/run-job)
- [Run-if conditions](https://learn.microsoft.com/en-us/azure/databricks/jobs/run-if)
- [Jobs system-table reference](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs)
- [System-table scope and limitations](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/)
- [Audit system-table reference](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/audit-logs)
- [Billable usage system-table reference](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/billing)
- [Monitor Lakeflow Job costs](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs-cost)
- [Bundle `run_as`](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/run-as)
- [Bundle direct deployment engine](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/direct)
- [Serverless egress control](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/network-policies)
- [Manage serverless network policies](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/manage-network-policies)

## Reviewed-file matrix

| File | Classification | Evidence and conclusion |
|---|---|---|
| `README.md` | `PASS` | Lines 3-15 state the correct customer-local, artifact-first, least-privilege and bounded-cost direction. |
| `AGENTS.md` | `PASS` | Lines 7-20 and 34-47 correctly prohibit external required services, active Volume appends, unsafe free-form inputs, unpinned dependencies, and unmarked Preview dependencies. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS_WITH_FOLLOW_UP` | The decision at lines 19-40 is sound. After DBX-P0-001 and DBX-P0-002 are resolved, record the selected cross-job identity and reconciliation topology in this ADR or a follow-on ADR. |
| `docs/plans/product-plan.md` | `CHANGES_REQUIRED` | The target architecture, identity, cancellation/timeout, audit, egress, cost and platform-gate contracts require the findings below. |
| `docs/plans/review-process.md` | `PASS` | Lines 73-120 define independent, immutable-input, evidence-backed review and re-review correctly; lines 124-140 cover every delivery part. |
| `docs/plans/documentation-plan.md` | `PASS_WITH_FOLLOW_UP` | The Diataxis split and review passes are appropriate. Add the platform pages listed under DBX-P0-004, DBX-P0-005 and DBX-P0-007 before D1/D2. |
| `docs/research/source-register.md` | `CHANGES_REQUIRED` | It captures most feature boundaries, but needs the Job `Run as`, Run Job task, App user-authorization Preview, serverless egress, system-table scope/latency and SQL-warehouse attribution sources used in this review. |

## Product-plan section review

| Product-plan section | Classification | Databricks review evidence |
|---|---|---|
| Outcome, lines 8-17 | `PASS` | Correctly separates outer Lakeflow state from valid dbt capture. |
| Fixed constraints, lines 19-27 | `CHANGES_REQUIRED` | Add an explicit runtime-egress boundary and a bounded reconciliation exception to “no continuously running collector”; see DBX-P0-002 and DBX-P0-005. |
| Product boundary, lines 29-59 | `PASS_WITH_FOLLOW_UP` | Scope and optional AI/Marketplace boundaries are sound. Clarify that system-table enrichment is optional/degraded when permissions or maturity gates fail. |
| Target architecture, lines 61-78 | `CHANGES_REQUIRED` | The diagram implies one Job with two run identities and does not show a cancellation/timeout reconciliation path; see DBX-P0-001 and DBX-P0-002. |
| Identity model, lines 80-92 | `CHANGES_REQUIRED` | Lakeflow task identity is job-level, and the “optional run-control identity” is not defined as App authorization or Preview user authorization; see DBX-P0-001 and DBX-P0-003. |
| Candidate compatibility baseline, lines 94-104 | `CHANGES_REQUIRED` | `Python 3.10 or later` is not an exact Databricks runtime contract. Pin a serverless environment or Databricks Runtime and effective Python version; see DBX-P0-004. |
| Invocation rules, lines 106-115 | `PASS` | Unique target paths, closed local logs, selector allowlisting and full-attempt retries fit the platform design. |
| Correlation model, lines 117-133 | `PASS_WITH_FOLLOW_UP` | Rename the persisted IDs to distinguish the upstream `dbt_task_run_id` from collector task/run IDs and test repair/retry uniqueness. |
| Evidence priority, lines 135-140 | `PASS` | Lakeflow outer state, native artifact evidence and structured diagnostic events are correctly ordered. |
| Capture states, lines 142-150 | `CHANGES_REQUIRED` | `NOT_PRODUCED` cannot be guaranteed for whole-run cancellation/timeout using only the shown downstream task; see DBX-P0-002. |
| Regulated data model, lines 152-159 | `PASS_WITH_FOLLOW_UP` | The allowlist and TTL cautions are correct. P7 must separately verify deletion of Delta rows/files and diagnostic Volume objects. |
| Installation experience, lines 161-188 | `CHANGES_REQUIRED` | The preflight needs a named platform/maturity/egress matrix and exact App ACL preview; see DBX-P0-004, DBX-P0-005 and DBX-P0-003. |
| Delivery parts and review gates, lines 190-206 | `CHANGES_REQUIRED` | P2, P3, P4, P6-P8 need the acceptance evidence in the findings and per-part matrix below. |
| Local and CI test strategy, lines 208-216 | `PASS_WITH_FOLLOW_UP` | Strong archive and authorization testing. Add generated-Bundle policy tests for identity, App ACLs, network assumptions and stable feature use. |
| Staging test strategy, lines 218-224 | `CHANGES_REQUIRED` | Add cross-job identity, whole-run cancellation/timeout, system-table isolation, App ACL and restricted-egress tests. |
| Compatibility fixtures, lines 226-228 | `PASS_WITH_FOLLOW_UP` | Failure coverage is strong, but cancellation and timeout must include a collector-never-started case. |
| Cost discipline, lines 230-238 | `CHANGES_REQUIRED` | Cleanup is strong, but per-run SQL warehouse cost cannot be represented as exact job cost on a shared warehouse; see DBX-P0-006. |
| Marketplace path, lines 240-249 | `PASS` | Correctly treats Marketplace as later and partner/security-review gated. |
| Decisions still open, lines 251-261 | `CHANGES_REQUIRED` | Add decisions for collector identity topology, cancellation reconciliation, App action authorization/audit, runtime egress and cost confidence. |
| Definition of planning baseline, lines 263-272 | `CHANGES_REQUIRED` | The baseline becomes acceptable only after the required findings are resolved and re-reviewed. |

## P0-P10 Databricks review matrix

| Part | Classification | Required Databricks evidence or follow-up |
|---|---|---|
| P0 — Product contract | `CHANGES_REQUIRED` | Resolve DBX-P0-001 through DBX-P0-007 and update the source register. |
| P1 — Capture library | `PASS_WITH_FOLLOW_UP` | Fixtures must carry a typed upstream `dbt_task_run_id`, job/repair/execution identity and exact runtime metadata without requiring Databricks. |
| P2 — Collector job | `CHANGES_REQUIRED` | Prove the separate run identity topology, idempotent archive fetch and recovery when the collector never starts or is cancelled. |
| P3 — Bundle installer | `CHANGES_REQUIRED` | Prove Premium/UC/compliance/region/serverless gates, exact CLI/engine/runtime pins, OIDC/run-as separation, named App groups and restricted-egress behavior. |
| P4 — App read-only MVP | `CHANGES_REQUIRED` | Prove no direct broad system-schema access, no local-state dependency, unauthorized-user denial, curated-view isolation and honest pending/estimated cost states. |
| P5 — Job onboarding | `PASS_WITH_FOLLOW_UP` | The generated patch must show run-as impact, downstream Run Job/reconciliation topology, grants and exact rollback; never bind an existing job silently. |
| P6 — Controlled actions | `CHANGES_REQUIRED` | Select stable App-principal execution or explicitly accept Preview user authorization; prove actor correlation, approval, `CAN_MANAGE_RUN` only, and inability to edit the job. |
| P7 — Security and operations | `CHANGES_REQUIRED` | Make Preview audit enrichment optional, verify product action records, enforce runtime egress policy, and verify both Delta and Volume deletion. |
| P8 — Bounded live proof | `CHANGES_REQUIRED` | Add cancellation before collector start, job timeout, cross-job permission denial, restricted-egress startup, and post-test App/warehouse/job inventory. |
| P9 — Optional intelligence | `PASS_WITH_FOLLOW_UP` | Optionality is correct. Re-check Genie/MCP maturity and compliance at implementation; raw evidence must remain unavailable to prompts. |
| P10 — Private alpha | `PASS_WITH_FOLLOW_UP` | Include one compliance-profile readiness check, one least-privilege installation, cost-confidence labels and uninstall grant/orphan verification in alpha evidence. |

## Findings

### DBX-P0-001: The collector identity topology is not executable as drawn

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Evidence: `docs/plans/product-plan.md`, **Target architecture**, lines 67-74, places the dbt task and `ALL_DONE` collector in one observed Job; **Identity model**, lines 87-90, assigns distinct dbt and collector principals. `docs/decisions/0001-private-app-bundle.md`, line 21, makes Jobs responsible for both. Databricks documents that the Job `Run as` identity is used by the tasks within the job; it is not a per-task identity. See [Job privileges and `Run as`](https://learn.microsoft.com/en-us/azure/databricks/jobs/privileges).
- User/system impact: The implementation would either fail to create the claimed privilege separation or silently run collection with the dbt workload's broader data privileges.
- Required change: Select and document one topology. The least-privilege candidate is an `ALL_DONE` **Run Job task** that invokes a separately defined collector Job with its own service-principal `run_as`. Grant the observed Job principal only `CAN_MANAGE_RUN` on that collector Job and grant the collector principal only `CAN_VIEW` on explicitly onboarded Jobs plus write access to product-owned UC objects. Alternatively, explicitly accept one shared job identity and remove the separate-principal claim. Update the diagram, identity table, P2/P3 exits and ADR. See [Run Job task](https://learn.microsoft.com/en-us/azure/databricks/jobs/tasks/run-job) and [Bundle `run_as`](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/run-as).
- Acceptance test: Deploy the selected topology with two service principals; prove the collector run reports the collector principal, can retrieve the upstream individual dbt task output, can write only product objects, cannot query dbt project data, and the observed Job principal cannot write observability tables directly.

### DBX-P0-002: `ALL_DONE` alone does not satisfy cancellation and timeout capture

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Evidence: `docs/plans/product-plan.md`, lines 36, 150, 198 and 228, promises capture for cancellation and timeout. `ALL_DONE` runs after dependencies have run, but it is not a durable finally mechanism for a whole run that is cancelled or terminated by a job-level maximum duration. Jobs system tables explicitly represent `CANCELLED`, including platform cancellation when maximum duration is exceeded. See [Run-if conditions](https://learn.microsoft.com/en-us/azure/databricks/jobs/run-if) and [Jobs system-table termination codes](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs).
- User/system impact: A cancelled or timed-out run can have no collector task, so the product can omit the outer attempt it promises and falsely leave a monitoring gap.
- Required change: Add a non-continuous reconciliation path: for example, a bounded scheduled serverless reconciliation Job plus an explicit operator-triggered reconcile action. It must discover observed attempts with no product attempt row through the Jobs API and/or stable Jobs system tables, create exactly one outer record, and attempt native archive recovery when available. State the acceptable reconciliation latency and the degraded behavior when system-table permissions are absent.
- Acceptance test: Cover cancellation before collector scheduling, cancellation during collector execution, task timeout, job timeout and repair. Each case must eventually produce exactly one attempt key with the correct outer termination and capture state; rerunning reconciliation must not duplicate it.

### DBX-P0-003: App action identity and required audit correlation cross a Preview boundary

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Evidence: `docs/plans/product-plan.md`, lines 67, 90, 202 and 238, introduces controlled App runs and requires native audit correlation while preferring “stable audit” sources. `AGENTS.md`, line 20, and the ADR, line 40, require Preview capabilities to remain optional. `system.access.audit` is Public Preview, and Databricks App user authorization is also Public Preview. App authorization otherwise executes as the App's dedicated service principal. See [Audit system-table reference](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/audit-logs), [App authorization](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/auth), and [App permissions](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/permissions).
- User/system impact: A required regulated path could depend on Preview, or native audit could attribute the Job action only to the App principal and lose the approving human actor.
- Required change: Choose the regulated-v1 action model before P6. The stable candidate is App authorization with the App principal granted `CAN_MANAGE_RUN` only on approved bound Jobs, named operator/admin App groups, and a product-owned UC action ledger that records authenticated actor, approval, requested resource, request/run IDs and outcome without raw parameters. Keep `system.access.audit` enrichment optional while Preview. If user authorization is selected, record an explicit Preview/compliance ADR and fallback behavior.
- Acceptance test: Prove unauthorized users cannot open or invoke the action, operators cannot edit the Job, approved and denied attempts produce actor-correlated product records, the platform run uses the intended principal, and disabling Preview audit/user authorization does not break the required product journey.

### DBX-P0-004: Platform readiness and runtime compatibility are not yet an exact contract

- Classification: `CHANGES_REQUIRED`
- Severity: medium
- Evidence: `docs/plans/product-plan.md`, line 102, specifies “Python 3.10 or later”; lines 166-169 describe only generic feature checks. `AGENTS.md`, lines 19-20, requires a tested Python/CLI matrix and feature maturity. Apps require Premium, and a compliance-security-profile workspace requires an administrator to enable Apps on the Previews page. The Bundle direct deployment engine is Experimental. See [Apps overview](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/), [App key concepts](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts), and [direct deployment engine](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/direct).
- User/system impact: Installation can pass on an unsupported workspace or drift to an untested Python, CLI, serverless environment or Bundle engine.
- Required change: Add a versioned readiness matrix with Premium, Unity Catalog privilege model, Azure region/compliance standard, Apps enablement, serverless Jobs/SQL availability, identity federation, required system schemas, selected stable Bundle engine, exact tested CLI range, and exact serverless environment/Databricks Runtime plus effective Python version. Change “Python 3.10 or later” to the exact candidate or mark it unresolved rather than supported. Add corresponding `reference/support-matrix.md` and `how-to/check-workspace-readiness.md` requirements to the documentation plan.
- Acceptance test: A machine-readable preflight returns supported/unsupported/degraded for each gate before mutation; fixtures test missing Premium, Apps disabled, unsupported runtime, missing system schema and disallowed serverless compute.

### DBX-P0-005: Runtime and dependency egress are outside the current threat contract

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Evidence: `README.md`, lines 5 and 9, and `docs/plans/product-plan.md`, lines 21-24, promise a customer-local regulated boundary. The plan does not say whether App Python/npm dependency installation or App/collector runtime may access the public internet. Serverless restricted mode is deny-by-default but Databricks Apps currently have limited support; Bundle UI/deployment paths can also need explicitly allowed GitHub and HashiCorp domains. See [serverless egress control](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/network-policies) and [manage network policies](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/manage-network-policies).
- User/system impact: A customer can approve a “customer-local” product without understanding deployment-time downloads or unrestricted runtime egress, and a locked-down workspace can fail after mutation.
- Required change: Define zero required product runtime internet egress. Separate build/deployment egress from runtime egress, lock Python and Node dependency graphs, document mirrored/vendored or allowlisted installation options, and state the current App network-policy limitation. Add a read-only network-policy preflight and a source-register entry. Do not require the Experimental direct engine merely to avoid Terraform downloads.
- Acceptance test: Build from locks, deploy/start in a representative restricted-policy workspace, query the App and run collector capture with no unapproved destination, then inspect denial/build logs. Repeat with one required domain removed and verify a preflight or actionable failure without widened access.

### DBX-P0-006: System-table scope and per-run cost confidence need a security contract

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Evidence: `docs/plans/product-plan.md`, lines 37, 41, 74 and 200, sends Jobs/billing/audit system tables through the warehouse into product cost and run views. System tables can contain data from multiple workspaces in the account/region and are not real-time. Billing metadata attributes Job cost accurately for serverless or dedicated job compute, but shared SQL warehouse billing is associated with the warehouse rather than a dbt Job run. Databricks' Job-cost examples exclude SQL warehouse workloads. See [system-table scope and limitations](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/), [billable usage metadata](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/billing), and [monitor Job costs](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs-cost).
- User/system impact: Direct App access can expose unrelated workspace/job metadata, and a shared warehouse's spend can be presented as exact cost for one dbt attempt when it is only allocated or estimated.
- Required change: Never grant the App principal broad direct `SELECT` on system schemas. Materialize or expose only workspace- and onboarded-job-filtered product-owned views/tables through a narrowly controlled owner, and denial-test unrelated jobs/workspaces. Define cost confidence per component: exact/attributed for App and supported job compute, allocated/estimated or unavailable for shared SQL warehouse work, and pending while system tables have not updated. Avoid a mandatory query-history join while that system table is Preview.
- Acceptance test: Seed two workspaces/jobs in accessible system data and prove the App can return only the onboarded workspace/job. For a run sharing a warehouse with another workload, prove the UI/API labels the SQL component non-exact and never assigns the warehouse's full cost to the dbt run.

### DBX-P0-007: App access-control defaults and grants are not part of the install diff

- Classification: `CHANGES_REQUIRED`
- Severity: medium
- Evidence: `docs/plans/product-plan.md`, lines 89-92 and 169, distinguishes App resource authorization but does not specify App `CAN_USE`/`CAN_MANAGE` principals or prohibit “Anyone in my organization.” Databricks separates App permissions from App/resource authorization and permits organization-wide `CAN_USE`. See [Configure App permissions](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/permissions).
- User/system impact: A correctly restricted App service principal can still expose all curated observability data to a much broader account audience than the installer intended.
- Required change: Add named operator and administrator groups to installer inputs and the exact change plan. Default to no account-wide access, `CAN_USE` for the operator group, and `CAN_MANAGE` only for the product administrator group/deployer. Include these ACLs in install, upgrade, access review and uninstall evidence.
- Acceptance test: Before App start, inspect the applied ACL; a non-member must be denied, an operator must be read-only, and only an administrator may deploy/change permissions. Uninstall must remove product-created grants without altering pre-existing customer grants.

## Re-review acceptance

Request Databricks re-review after the plan and source register contain testable resolutions for DBX-P0-001 through DBX-P0-007. A new report should identify an immutable commit, retain this report in history, and record the chosen identity/reconciliation/action-auth decisions rather than merely moving them into implementation.
