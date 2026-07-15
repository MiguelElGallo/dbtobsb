# Databricks platform re-review: P0 planning baseline 0.2

- Reviewed input: frozen author-owned planning file set
- Author-input SHA-256: `483a3a4e1ccfe063a8af07a15483ac48abf5d090c44f1817a4cee8e810483965`
- Date: 2026-07-15
- Reviewer: independent Databricks product and platform specialist
- Verdict: `CHANGES_REQUIRED`
- Blockers: none; the private-App-plus-Bundle direction remains sound
- Cloud mutation: none; no Azure or Databricks resource was created, started, or changed

## Immutable input verification

The reviewed author input is `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path. I independently hashed each file, then hashed the sorted `shasum -a 256` output. The result was exactly:

```text
483a3a4e1ccfe063a8af07a15483ac48abf5d090c44f1817a4cee8e810483965
```

I also read the resolution ledger and the original Databricks review. Reviewer-owned files are not part of the author-input hash.

## Executive outcome

Baseline 0.2 materially improves the architecture. It now has an executable cross-Job identity shape, a bounded idempotent reconciliation path, an exact serverless/Python/dbt candidate, zero required public runtime egress, scoped system-table materialization, honest cost-confidence states, and named App ACLs with uninstall evidence.

Five original findings are resolved for planning. `DBX-P0-003` and `DBX-P0-004` remain only partially resolved:

- Shared App authorization gives every App user the App service principal's resource privileges. The plan does not yet define how FastAPI denies controlled actions to the stated read-only operator, and the documented App-principal grants omit the `MODIFY` privilege needed to write the required action ledger.
- Current first-party sources now classify Databricks CLI 1.x as GA and the direct Bundle engine as GA and the default for new deployments. Baseline 0.2 still calls CLI 1.7.0 Public Preview, calls direct Experimental, and selects Terraform as the stable/default engine even though Databricks says Terraform will soon be deprecated.

These are correctable P0 contract defects. They do not require changing the accepted private Databricks App or Declarative Automation Bundle direction.

## Current primary sources checked

### CLI, Bundles, and deployment

- [Databricks CLI release types](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/)
- [Databricks CLI 1.7.0 release](https://github.com/databricks/cli/releases/tag/v1.7.0)
- [Databricks CLI 1.3.0 release: direct engine GA and default](https://github.com/databricks/cli/releases/tag/v1.3.0)
- [Bundle configuration reference](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/reference)
- [Direct deployment engine and Terraform migration](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/direct)
- [Manage Databricks Apps with Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial)
- [Bundles in an air-gapped environment](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/airgapped-environment)

### Apps, identity, and Unity Catalog authorization

- [Databricks Apps overview](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/)
- [App authorization](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/auth)
- [App permissions](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/permissions)
- [App resource bindings](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/resources)
- [Unity Catalog table resources for Apps](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/tables)
- [App HTTP identity and request headers](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/http-headers)
- [Unity Catalog permission concepts](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/access-control/permissions-concepts)
- [App monitoring and log persistence](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/monitor)
- [App telemetry](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/observability)

### Jobs, runtime, networking, and system data

- [Lakeflow Job privileges and Run as](https://learn.microsoft.com/en-us/azure/databricks/jobs/privileges)
- [Run Job task](https://learn.microsoft.com/en-us/azure/databricks/jobs/tasks/run-job)
- [Run-if conditions](https://learn.microsoft.com/en-us/azure/databricks/jobs/run-if)
- [Bundle run-as identities](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/run-as)
- [Native dbt tasks and archived output](https://learn.microsoft.com/en-us/azure/databricks/jobs/how-to/use-dbt-in-workflows)
- [Serverless Jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/run-serverless-jobs)
- [Serverless environment version 5](https://learn.microsoft.com/en-us/azure/databricks/release-notes/serverless/environment-version/five)
- [Configure serverless task environments](https://learn.microsoft.com/en-us/azure/databricks/compute/serverless/dependencies)
- [Serverless egress control](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/network-policies)
- [Manage serverless network policies](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/manage-network-policies)
- [System-table scope and limitations](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/)
- [Jobs system tables](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs)
- [Billable usage metadata](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/billing)
- [Monitor Job costs](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/jobs-cost)
- [Audit system table](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/audit-logs)
- [SQL warehouse channel guidance](https://learn.microsoft.com/en-us/azure/databricks/compute/sql-warehouse/create)

## Original finding outcomes

| Finding | Re-review outcome | Evidence and remaining implementation proof |
|---|---|---|
| `DBX-P0-001` | `RESOLVED_FOR_P0` | The ADR and product architecture now use an `ALL_DONE` Run Job task to trigger a separately configured collector Job. Job `Run as` applies to all tasks in that Job, while the called collector Job retains its own job-level run-as identity. The observed principal receives only `CAN_MANAGE_RUN` on the collector and the collector receives `CAN_VIEW` on onboarded Jobs plus product-write privileges. P2/P3 staging must still prove both effective principals and both negative permission boundaries. |
| `DBX-P0-002` | `RESOLVED_FOR_P0` | The plan no longer treats `ALL_DONE` as a durable finally mechanism. It specifies the same idempotent collector for normal, 15-minute scheduled, and operator-triggered reconciliation, a 20-minute target, visible `DEGRADED` behavior, and cancel/timeout/repair/repeated-reconcile fixtures. P2/P8 must prove exactly one AttemptKey for every case. |
| `DBX-P0-003` | `PARTIALLY_RESOLVED` | Stable shared App authorization, optional Preview user authorization/audit enrichment, named App groups, trusted forwarded actor/request correlation, and the action-ledger schema are selected. The human action-authorization path and the ledger's table-level write grant are not executable under the documented permission table; see `DBX-P0-008`. |
| `DBX-P0-004` | `REOPENED` | Environment 5, Python 3.12.3, exact dbt pins, CLI 1.7.0, and Current-channel serverless SQL are concrete and testable. The CLI and deployment-engine maturity statements are no longer current, and the selected engine is not explicitly aligned with current Databricks direction; see `DBX-P0-009`. |
| `DBX-P0-005` | `RESOLVED_FOR_P0` | Runtime public egress is explicitly zero. Build/deploy egress is separate, locked, signed/checksummed, SBOM-backed, mirror/offline or allowlisted, and checked before mutation. P3/P8 retain restricted-policy startup and negative-destination tests. The egress list must be recalculated when `DBX-P0-009` changes the engine. |
| `DBX-P0-006` | `RESOLVED_FOR_P0` | The App is denied broad direct system-schema access. A separately approved materialization is workspace/onboarded-Job scoped, native sources are optional and delayed, query history is not required, and SQL warehouse cost is allocated/estimated rather than exact. P4/P8 must still prove cross-workspace/job denial and every confidence state. |
| `DBX-P0-007` | `RESOLVED_FOR_P0` | Named operator/admin groups, no broad default group, separate App ACL/resource-grant diffs, read-only operator behavior, and uninstall grant removal are all explicit. P3/P7/P10 must preserve pre-existing customer grants and prove no orphaned product grants. |

## Reviewed-file outcome

| File or set | Outcome | Databricks conclusion |
|---|---|---|
| `README.md`, `AGENTS.md`, `docs/index.md` | `PASS` | The customer-local, deterministic, least-privilege, optional-AI, source-status, and bounded-cost rules remain appropriate. |
| `docs/decisions/0001-private-app-bundle.md` | `CHANGES_REQUIRED` | The architecture is sound, but the CLI/engine maturity statements are stale and the stable action model needs an explicit in-App authorization boundary and ledger table grant. |
| `docs/plans/product-plan.md` | `CHANGES_REQUIRED` | The seven original topics are substantially covered, but the App action identity and current Bundle engine contract fail P0 acceptance as described below. |
| `docs/plans/review-process.md` | `PASS` | Independent immutable-input review, finding format, re-review, and P0-P10 gates are clear and testable. |
| `docs/plans/documentation-plan.md` | `PASS_WITH_FOLLOW_UP` | The planned permissions, App access/resource grants, action ledger, support matrix, egress, reconciliation, operation, and lifecycle pages can document the corrected contract after `DBX-P0-008` and `DBX-P0-009` close. |
| `docs/research/source-register.md` | `CHANGES_REQUIRED` | Its CLI Public Preview and direct-engine Experimental cautions conflict with current first-party sources. Add the App table-resource privilege source as well. |
| `docs/reviews/p0-planning-baseline/resolution.md` | `NOT_AN_APPROVAL_INPUT` | The ledger accurately records the author's intended resolutions, but its closure claims for `DBX-P0-003` and `DBX-P0-004` are not independently accepted by this re-review. |

## P0-P10 Databricks part matrix

| Part | Outcome | Required Databricks evidence or correction |
|---|---|---|
| P0 — Product contract | `CHANGES_REQUIRED` | Close `DBX-P0-008` and `DBX-P0-009`, refresh the ADR/source register, freeze a new author-input hash, and re-review the affected findings. |
| P1 — Capture library | `PASS_WITH_FOLLOW_UP` | Golden fixtures must retain typed workspace/job/task/repair/execution identity, command ordinal, artifact hashes, and actual environment/serverless/SQL/CLI versions without requiring live Databricks. |
| P2 — Collector and reconciliation | `PASS_WITH_FOLLOW_UP` | The planned cross-Job, archive, cancel-before-start, cancel-during-run, task/Job timeout, retry/repair, degraded, and idempotency tests are sufficient. Prove the called collector's effective run-as and negative data/evidence permissions live. |
| P3 — Bundle installer | `CHANGES_REQUIRED` | Adopt the corrected explicit engine contract, update offline/allowlisted dependencies, and include the exact action-role and ledger table grants in plan/apply/upgrade/uninstall diffs. Validate no-op plan, deploy, update, rollback, and destroy with CLI 1.7.0. |
| P4 — App read-only MVP | `PASS_WITH_FOLLOW_UP` | Statelessness, curated-only reads, no broad system access, cost confidence, and WCAG scope are correctly planned. Keep all mutation routes absent until P6's server-side action policy is proven. |
| P5 — Job onboarding | `PASS_WITH_FOLLOW_UP` | The five scanner states and source-controlled semantic-change review are sound. Generated proposals must expose the downstream Run Job topology, run-as/grant effects, and rollback. |
| P6 — Controlled actions | `CHANGES_REQUIRED` | Assign the human initiator/approver role, enforce it server-side independently of App `CAN_USE`, add the narrow ledger write resource, and prove direct-API denial for the read-only operator; see `DBX-P0-008`. |
| P7 — Security and operations | `CHANGES_REQUIRED` | Access review and uninstall must cover the new action-role mapping and ledger resource grant, including removal without disturbing pre-existing grants. Delta/Volume deletion verification remains required. |
| P8 — Bounded live proof | `PASS_WITH_FOLLOW_UP` | The cost envelope, cancellation/timeout matrix, restricted egress, query proof, unconditional cleanup, stopped App/warehouse, paused schedules, and final inventory are all present. Use the corrected engine and action policy. |
| P9 — Optional intelligence | `PASS_WITH_FOLLOW_UP` | AI remains outside command construction, policy, capture, validation, and raw evidence. Refresh Genie/MCP maturity immediately before implementation. |
| P10 — Private alpha | `PASS_WITH_FOLLOW_UP` | Retain the compliance-profile readiness, least-privilege install, cost confidence, two clean installs, upgrade, uninstall, and orphan checks. Include one alpha journey with Preview user authorization, audit-system-table enrichment, App telemetry, and AI all disabled. |

## New findings

### DBX-P0-008: Shared App authorization does not yet enforce the read-only human boundary or authorize ledger writes

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: `docs/plans/product-plan.md`, **Runtime identity model**, **Human role and prerequisite model**, P3, P6, and P7; `docs/decisions/0001-private-app-bundle.md`, **Decision**
- Evidence: The plan grants the App principal `CAN_MANAGE_RUN` on approved Jobs and gives the read-only operator App `CAN_USE`, while also promising that the operator has no mutation privilege. It says FastAPI owns policy but defines no stable role source or server-side decision that distinguishes an action initiator/approver from a read-only `CAN_USE` user. Databricks documents that all users of shared App authorization use the same App service principal permissions and that App permissions control access/manage capability rather than the service principal's resource authorization. Forwarded headers provide an opaque user ID and request ID but no product role. The same App-principal row lists only warehouse use, curated `SELECT`, and Job `CAN_MANAGE_RUN`; it omits the ledger write privilege. A UC table write requires `USE CATALOG`, `USE SCHEMA`, and table `MODIFY`; an App table resource with Modify can grant that narrow set.
- User/system impact: A read-only operator could reach a controlled-action API that runs with the App principal's Job privilege unless application policy is defined correctly. Alternatively, the required action fails to write its durable audit row or implementation adds an unreviewed schema-wide write grant. Either result breaks the regulated action/audit boundary.
- Required change:
  1. Name the human action initiator and approver roles and define a stable, deny-by-default product authorization source keyed by the trusted forwarded user ID. Do not infer permission to run a Job merely from App `CAN_USE` or shared App authorization.
  2. Specify how named-group or individual membership is resolved, refreshed, reviewed, revoked, and removed on uninstall without requiring Preview user authorization.
  3. Add one App UC-table resource with `MODIFY` only for the action-ledger table, including required parent usage privileges. Do not grant the App principal `MODIFY`, ownership, or `MANAGE` on the product schema, normalized evidence tables, or raw Volume.
  4. State that a denial produced inside FastAPI is ledgered, while a request denied by the Databricks reverse proxy before reaching the App cannot be promised in the product ledger; native audit enrichment remains optional.
  5. Add the exact action-role and ledger grants to install, upgrade, access review, rollback, and uninstall diffs and to the permissions/action-ledger documentation pages.
- Testable acceptance:
  1. A read-only operator with App `CAN_USE` calls the action endpoint directly and receives a stable `403`; no Job run starts and a safe product denial row is recorded.
  2. An explicitly authorized action role completes prepare/approve/run; one ledger chain correlates forwarded user ID, request ID, approval, idempotency key, resulting run, and outcome.
  3. Missing or untrusted identity headers fail closed; local-test headers cannot become production authorization evidence.
  4. The App principal can insert/update the action ledger but cannot modify any normalized evidence table, unrelated table, or diagnostic Volume.
  5. Role/grant removal immediately denies future actions, and uninstall removes only product-created mappings/grants.
  6. The entire required journey passes with user authorization and `system.access.audit` disabled.

### DBX-P0-009: CLI and Bundle-engine maturity claims are stale, and the selected engine is no longer the recommended new-product baseline

- Classification: `CHANGES_REQUIRED`
- Severity: medium
- Affected contract: `docs/plans/product-plan.md`, **Candidate compatibility baseline**, **Runtime egress and supply chain**, **Platform readiness matrix**, and P3; `docs/decisions/0001-private-app-bundle.md`, **Consequences**; `docs/research/source-register.md`, **Databricks product baseline**
- Evidence: Current Azure Databricks CLI documentation classifies versions 1.0.0 and above as GA. The first-party CLI 1.3.0 release makes the direct engine GA and the default for new deployments. Current direct-engine guidance recommends migration because Terraform will soon be deprecated. Baseline 0.2 instead says CLI 1.7.0 is Public Preview, calls direct Experimental, and calls Terraform the stable/default engine. With CLI 1.7.0, relying on an assumed default risks a different state engine than the reviewed contract.
- User/system impact: Readiness can report a false maturity risk, a new installation can use an engine other than the one reviewers expected, and a new regulated product can acquire a near-term Terraform migration plus unnecessary HashiCorp download/allowlist surface.
- Required change:
  1. Mark CLI 1.7.0 as GA while retaining the exact binary/checksum pin, deployment-only boundary, and requalification rule.
  2. Select the GA direct engine for the new-product baseline and set `bundle.engine: direct` explicitly so environment variables or changing defaults cannot alter deployment state.
  3. Remove the claim that direct is Preview/Experimental and record the direct engine's different state/diff semantics and documented drift behavior as P3 qualification risks.
  4. Recalculate the connected and offline supply-chain inputs. The direct path must not retain Terraform/HashiCorp egress requirements that it does not use.
  5. Update the ADR, source register, preflight, support matrix, bootstrap outputs, P3/P8 evidence, and rollback/migration documentation together.
- Testable acceptance:
  1. Generated YAML contains both `databricks_cli_version: '1.7.0'` and `engine: direct`; an environment variable requesting Terraform cannot override the file.
  2. CLI 1.7.0 validates and emits a machine-readable plan for every App, Job, schema/table/Volume, permission, grant, and target used by v1.
  3. Staging proves create, App-code deploy/start, no-op plan, update, rollback, and destroy without orphaned resources or grants.
  4. A restricted-egress install succeeds with the declared direct-engine inputs and no unapproved HashiCorp destination.
  5. Any unsupported field, state drift, or engine mismatch fails before mutation with a safe recovery path.

## Final verdict

`CHANGES_REQUIRED`

The architecture is still the recommended starting direction. P0 can return for a narrow re-review after the author closes `DBX-P0-008` and `DBX-P0-009`, refreshes the source register and affected plan/ADR sections, and publishes a new frozen author-input hash. The cross-Job collector and bounded-reconciliation design do not need to be reopened unless those edits change them.
