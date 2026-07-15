# Databricks platform/security tenth re-review: P0 planning baseline

- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform/security reviewer
- Immutable author input SHA-256: `4c033d3a47ebd9c11b695177d1e166986af5c74d404ded76cfed828c088d8073`
- Baseline: 0.11
- Verdict: `CHANGES_REQUIRED`
- Cloud mutation: none

## Immutable input verification

I read every frozen author file: `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`. I also read the ninth Databricks, dbt Core, and usability re-reviews before forming this independent platform/security conclusion.

I recomputed the requested digest by sorting the author paths, hashing each file with SHA-256, concatenating those path-ordered hash records, and hashing that stream. The result was exactly:

```text
4c033d3a47ebd9c11b695177d1e166986af5c74d404ded76cfed828c088d8073
```

The hash still matched immediately before this report was written. No author file or earlier review was changed. This report is the only file written. I made no Azure, Databricks, authentication, account-console, SQL, warehouse, App, Job, or Unity Catalog call.

## Executive assessment

Baseline 0.11 makes substantial and correct progress on the two ninth-review blockers:

- `DBX-P0-020`'s core trust order is fixed. The actual App code is deployed before a candidate exists; the App is stopped and finally bound; explicit `databricks apps start <name>` starts the last active deployment; a same-ID post-start observation precedes positive acceptance. A candidate never unlocks runtime behavior.
- `DBX-P0-021`'s missing durable carrier is fixed. A customer-security-owned managed Delta `runtime_trust_ledger` and sanitized `runtime_trust_status_v` are named, the verifier/trust-committer is the only product writer, runtime principals read only the view, expiry is evaluated with server `current_timestamp()`, and refresh, retention, export, restart, upgrade, and uninstall are addressed.

The recommended architecture remains a private Databricks App deployed through a plain-YAML Direct Bundle, with customer-local Unity Catalog data and an attended fixed Statement Execution plane for data/control events. Apps and the Direct Bundle engine are GA; the required path still correctly excludes Preview identity APIs.

P0 nevertheless remains blocked by three implementation-level defects exposed by the more precise lifecycle:

1. The plan generates both saved Direct plans before applying either one. A saved final-binding plan cannot be valid after the stage plan changes Direct state. On a fresh install it replays create actions; on an existing installation its saved serial is stale.
2. One invocation of the pinned `bundle run` implementation is not equivalent to exactly one deployment submission. It starts the last active deployment before deploying, and its helper can reissue the deployment POST after any first-call error. The baseline neither inventories the deployment set nor defines fail-closed reconciliation.
3. The durable trust objects now exist, but the ledger's event cardinality, event-specific schema, authoritative time capture, signature trust anchor, and current-view reduction are not frozen consistently enough to implement the promised fail-closed gate.

The first and third findings are high severity. The second is medium severity because the zero-authority/no-user-access stage bounds data exposure, but it still breaks exact deployment identity, recovery, and billed-compute claims. All three must be resolved before implementation starts.

## Current primary evidence checked

All platform claims below were checked against current official Microsoft/Databricks documentation or the exact first-party CLI source pinned by the plan.

### Bundle plans and Direct state

- [Bundle direct deployment engine](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/direct) documents Direct's separate local and remote state and saved plan/apply workflow. [Databricks CLI v1.3.0](https://github.com/databricks/cli/releases/tag/v1.3.0) records Direct as GA/default for new deployments; the plan pins [CLI v1.7.0](https://github.com/databricks/cli/releases/tag/v1.7.0).
- In pinned CLI 1.7.0, [`ValidatePlanAgainstState`](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/bundle_plan.go#L42-L57) requires the saved plan's lineage and serial to match current Direct state. It skips validation only for an initial plan with empty lineage.
- The pinned [`bundle deploy --plan` path](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/cmd/bundle/utils/process.go#L240-L265) performs that validation before file operations. A stage Apply therefore cannot be followed by an independently precomputed update plan from the old serial.
- Direct plan calculation chooses `Create` when the resource has no state entry. The pinned [Direct App create adapter](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/dresources/app.go#L96-L144) treats an already-existing, non-deleting App as a hard create error. Empty-lineage validation skipping does not make two first-install create plans composable.
- The same [Direct App adapter](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/dresources/app.go#L146-L240) supports changing App resources while stopped and makes `lifecycle.started:true` start compute and deploy code. Retaining explicit `false` in both stage and final plans is correct.

### App deployment and start behavior

- [Manage Databricks Apps using Declarative Automation Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial) states that Bundle deploy creates or updates the App resource but does not deploy code to compute; `bundle run <app-key>` is the separate code-deploying operation.
- The [Apps CLI reference](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/reference/apps-commands) documents `apps start` as starting the last active deployment and provides `get-deployment` and paginated `list-deployments` surfaces. It does not give `start` a deployment-ID precondition.
- The pinned [`bundle run` App runner](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/run/app.go#L48-L95) calls App start when compute is stopped and then always calls deploy. On upgrade or rollback, the start step can temporarily run the previous last active deployment before the new deployment is created.
- The pinned [deployment builder](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/appdeploy/app.go#L21-L50) always requests `SNAPSHOT`, which supports the selected mode.
- The pinned [deployment helper](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/appdeploy/app.go#L80-L112) retries the deploy POST after any first-call error once it has fetched the App and waited for active/pending deployments. If the first POST committed but its response was lost, that path can submit a second deployment.
- The first-party explicit [`apps deploy APP_NAME`](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/cmd/workspace/apps/apps.go#L691-L772) supports a caller-supplied deployment ID and renders the resulting deployment. That is a possible protocol building block, not a recommendation to change commands without qualification.
- [Get started with Databricks Apps](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/get-started) shows the successful deployment ID, immutable deployment-artifact path, `SNAPSHOT` mode, and terminal status that the wrapper must reconcile.

### Durable trust state

- [ACID guarantees on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/acid) supports using one Delta table for an atomic authoritative event write. Multi-table transactions remain an unnecessary dependency for this design.
- [Delta `MERGE INTO`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/delta-merge-into) supports the fixed idempotent insert-if-absent approach, but an implementation still has to freeze the merge key, source cardinality, event payload, and post-write conflict checks.
- [Constraints on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/tables/constraints) confirms that informational primary/foreign keys are not enforcement. The baseline correctly does not rely on them; its SQL/view protocol must therefore detect every invalid cardinality itself.
- [Roles for managing service principals](https://learn.microsoft.com/en-us/azure/databricks/security/auth/access-control/service-principal-acl) continues to support the native account-console Permissions roster and the plan's explicit Service Principal User/Manager trusted roots. The machine-readable [Account Access Control Proxy API](https://docs.databricks.com/api/azure/workspace/accountaccesscontrolproxy) remains Public Preview and is correctly prohibited in the required path.

## Ranked findings

| Rank | Finding | Severity | P0 effect |
|---:|---|---|---|
| 1 | `DBX-P0-022` - the precomputed final-binding Direct plan is stale or a second create plan | High | Blocks P0; `CHANGES_REQUIRED` |
| 2 | `DBX-P0-024` - the durable trust ledger/view contract is not yet executable or internally cardinality-consistent | High | Blocks P0; `CHANGES_REQUIRED` |
| 3 | `DBX-P0-023` - one `bundle run` is not a one-submission deployment protocol | Medium | Blocks P0 lifecycle acceptance; `CHANGES_REQUIRED` |

### DBX-P0-022: the precomputed final-binding Direct plan is stale or a second create plan

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: ADR two-plan decision; product-plan common stages and runtime steps 10-12; P3/P7/P8/P10; review process; bootstrap, upgrade, rollback, recovery, and lifecycle documentation.
- Evidence:
  1. Product-plan step 10 says to generate a signed manifest **and two Direct plans** before either Apply.
  2. The common stage sequence has `APP_STAGE_PLAN`, `APP_STAGE_DEPLOY`, and `APP_STAGE_STOP_VERIFY`, followed directly by `APP_FINAL_BINDINGS_APPLY`; it has no post-stage final-plan and approval stages.
  3. The ADR likewise describes two plans, and the documentation plan teaches stage-plan Apply followed by final-binding-plan Apply without regenerating the latter from current Direct state.
  4. Direct plans carry the state lineage and serial present when calculated. A successful stage Apply changes Direct state before the final plan is loaded.
  5. On an existing installation, both precomputed plans have the same pre-stage serial. After the stage Apply, the final plan fails pinned CLI validation because its serial no longer matches current state.
  6. On a first install, both plans are calculated with no resource entry, so both contain create actions. The final plan's empty lineage bypasses the normal validation, but the stage has already created the App. The pinned App adapter treats the second create as a hard `RESOURCE_ALREADY_EXISTS` error.
  7. `bundle run` and the explicit stop also change the remote App deployment/lifecycle facts that a true final-binding plan should read. A pre-stage remote snapshot cannot prove the final Apply is based on the deployment that was just staged and stopped.
- User/system impact:
  - A clean install cannot reliably reach final bindings.
  - Upgrade and rollback stop at saved-plan validation after they have already removed authority/staged state and may have incurred App-compute cost.
  - Bypassing validation would replace a useful concurrency guard with stale remote assumptions, contrary to the regulated review promise.
  - Recovery stages and time/cost estimates describe a path the pinned CLI cannot execute literally.
- Required acceptance condition:
  1. Make the plans sequential, not simultaneously precomputed: generate/review/apply the no-authority stage plan; run/reconcile the one intended code deployment; stop and prove zero authority; **then** calculate a fresh final-binding plan against current Direct state and live remote App state.
  2. Add explicit `APP_FINAL_BINDINGS_PLAN` and `APP_FINAL_BINDINGS_APPROVE` states before `APP_FINAL_BINDINGS_APPLY`. Bind the fresh plan's new lineage/serial, semantic remote digest, CLI checksum, actor/profile/host/workspace, manifest, composite seal, expected roster, source, build, and resource selection.
  3. Prove the fresh final diff changes only the reviewed existing-object bindings/ACLs and remains `lifecycle.started:false`; source, build, App command/environment/configuration, deployment ID, and code artifact must remain unchanged. Stop and re-observe after Apply.
  4. Define recovery if staging succeeded but the final plan has not yet been created, if remote state changes during final approval, and if final Apply partially fails. Resume must re-plan rather than reuse an old serial.
  5. Propagate this sequence through install, no-op, refresh, upgrade, rollback, P6 extension, retain/remove, and uninstall. A true unchanged trust refresh should not generate either code-staging plan.
  6. Add pinned-CLI fixtures for first install, existing final-to-stage-to-final transition, concurrent Direct mutation, killed process after stage Apply, killed process after deployment/stop, changed remote binding during approval, and stale-plan rejection. Assert that no workaround disables lineage/serial validation.

### DBX-P0-024: the durable trust ledger/view contract is not yet executable or internally cardinality-consistent

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: `runtime_trust_ledger`, `runtime_trust_status_v`, every runtime writer/read gate, P2-P4/P6-P8/P10, refresh/upgrade/rollback, and retain/delete-uninstall.
- Evidence:
  1. The plan now correctly chooses one managed Delta event table and one sanitized current-status view. It also says each event is one transaction, each retry reads back exactly one matching event, and only one atomic `SNAPSHOT_ACCEPTED` event commits.
  2. The frozen field list contains a singular `component` digest, while the current view must return one row per installation/component and runtime writers verify their own component digest. The plan does not say whether one accepted row contains a typed component map/array that the view explodes or whether one transaction inserts multiple component rows.
  3. The latter interpretation conflicts with “exactly one matching event” and “one `SNAPSHOT_ACCEPTED` event” unless event identity and row identity are separately frozen. The former lacks the structured SQL type, component key/cardinality rules, canonical ordering, and view expansion contract.
  4. `MANIFEST_REGISTERED` is written before a fresh deployment exists, yet the global frozen field list includes an exact deployment ID. Event-specific required/null fields are not defined. The same problem applies to an invalidation caused before deployment or before both evidence components exist.
  5. “Server-anchored” machine and roster completion times are security inputs, but only status evaluation with `current_timestamp()` is exact. The plan does not specify the fixed server-side statement that captures each completion time or prevent a client parameter from backdating/forward-dating those inputs. `accepted_at` cannot repair an unanchored earlier evidence clock.
  6. The ledger stores an asymmetric signature, signer fingerprint, and signature material in the view, but no trusted public-key source, enrollment/rotation/revocation/recovery rule, canonical signed bytes, or verifying component is frozen. Merely exposing a signature cannot make the SQL view fail closed on a bad signature.
  7. The current-view prose names many invalid states but does not freeze a deterministic reduction for latest generation, event order, prior-generation binding, duplicate rows, conflicting payloads, component completeness, invalidation precedence, and expiry. Different correct-looking SQL implementations can therefore disagree on whether P6 is unlocked.
  8. The customer owner and verifier group remain correctly disclosed trusted roots with `MODIFY`; this finding does not demand administrator-resistant immutability. It requires the product's own fixed writer/view to have one testable meaning.
- User/system impact:
  - The App, collector, and P6 writer can disagree about the current accepted snapshot or component row.
  - A malformed or partial generation can be accepted by one implementation and rejected by another.
  - A client-controlled evidence time can extend or prematurely expire the 24-hour gate despite the server-time wording.
  - Signatures may appear security-enforcing in the UI while no authority actually verifies them.
  - Upgrade, refresh, replay, conflict, and uninstall tests have no exact expected rows to assert.
- Required acceptance condition:
  1. Freeze executable SQL types, nullability, and event-specific required fields for all four event types. Distinguish `event_id`, physical row identity, snapshot ID, generation, and component identity.
  2. Choose one atomic representation: one accepted row containing a typed canonical component collection, or multiple component rows inserted by one single-table Delta statement. Define exact cardinality and readback rules for the selected representation and reconcile the “one event” wording.
  3. Freeze the deterministic ID and payload-digest construction, including canonical byte encoding, component ordering, prior-generation link, and conflict behavior. Exact retries may no-op; a same ID/different payload, additional accepted row, missing component, or conflicting component must fail closed.
  4. Define the fixed server-side time-anchor protocol for machine completion, roster completion, commit, and `valid_until`. A client may refer to a server-issued occurrence but cannot supply or extend the authoritative timestamp. Preserve the oldest component time across an early refresh that reuses roster evidence.
  5. Either define signature authority end to end—algorithm, canonical bytes, trusted public-key registry/reference, key enrollment/rotation/revocation/recovery, and which writer/view/App verifies it—or mark the signature as non-authoritative audit metadata and remove it from positive-gate reasoning.
  6. Freeze the semantic definition (preferably reference SQL) for `runtime_trust_status_v`: latest-generation selection, required event chain, one accepted snapshot, component expansion, invalidation/supersession precedence, digest checks, and `current_timestamp()` expiry. Define exactly what P6's conditional DML joins.
  7. Add single-table SQL fixtures for fresh registration without a deployment, exact retry, same-ID/different-payload, concurrent candidates/acceptance, missing/duplicate/conflicting component, invalidation before/after acceptance, replayed generation, expired/reused roster evidence, bad signature, owner tamper, unreadable view, refresh, upgrade/rollback, restart, and retain/delete-uninstall.

### DBX-P0-023: one `bundle run` is not a one-submission deployment protocol

- Verdict: `CHANGES_REQUIRED`
- Severity: medium
- Affected contract: stage deployment, upgrade/rollback, deployment-ID capture, recovery audit, billed intervals, stop-on-failure, source register, and P3/P7/P8/P10 tests.
- Evidence:
  1. The plan equates “run exactly one `bundle run` command” with “one successful `SNAPSHOT` deployment” and then says to capture that deployment ID.
  2. The pinned runner first calls App start when compute is stopped, then unconditionally deploys. For an App with an older active deployment, that briefly starts old code before the new deployment request.
  3. The pinned helper retries the deploy POST once after **any** first-call error. It fetches the App, waits for active/pending deployment completion, then issues a second POST. A committed first request with a lost response can therefore be followed by another successful `SNAPSHOT` request.
  4. The runner's success return does not itself establish the before/after deployment set. `apps start` later has no deployment-ID precondition and starts the last active deployment, so selecting an arbitrary successful ID is unsafe if staging was ambiguous.
  5. The zero-authority stage is a strong containment measure: old/new code has no product data, warehouse, Job, secret, Volume, or user access. That reduces confidentiality/integrity impact, but does not remove compute cost, lifecycle ambiguity, or exact trust-binding failure.
- User/system impact:
  - Upgrade/rollback may run prior code for a billed interval, a behavior the current journey does not disclose.
  - A transport error can leave one or two new deployments even though the wrapper reports a single failed/successful command attempt.
  - The later “start last active deployment” step can race with an unaccounted pending or second deployment.
  - Candidate acceptance may bind the wrong deployment ID, or cleanup may stop compute without explaining which artifacts remain.
- Required acceptance condition:
  1. Before staging, capture the complete paginated deployment inventory plus active/pending IDs and statuses. After every success **or error**, stop by default, consume all deployment pages again, and reconcile the set difference.
  2. Require no pending deployment and exactly the selected policy outcome. The safest baseline is exactly one new terminal successful `SNAPSHOT` with matching source/build/artifact/config digest; more than one new or an unknown deployment fails closed, invalidates the generation, and never reaches candidate.
  3. Explicitly disclose that pinned `bundle run` may start the previous last active deployment during upgrade/rollback. Prove its zero-authority/no-user-access state before the command, bound the interval, stop on every exit, and include it in cost/status output.
  4. If the product replaces `bundle run` with explicit named `apps deploy` and a deterministic deployment ID, qualify that exact pinned-CLI/API protocol, source staging, idempotency behavior, output, timeout, and recovery before changing the ADR. Do not infer idempotency merely from the presence of a caller-supplied ID.
  5. Prohibit no-argument Bundle-aware `apps deploy` throughout the wrapper path, not only after candidate. Permit only the frozen staging command and later explicit `apps start`/`stop`/`get`/`get-deployment`/`list-deployments` calls.
  6. Add tests for first-response loss after server acceptance, conflicting/pending deployment, old active deployment, failed start, failed stop, two successful same-digest deployments, pagination, App auto-sync, start race, cleanup after wrapper death, and a final proof of stopped compute plus zero pending deployment.

## Focused disposition of DBX-P0-020 and DBX-P0-021

### DBX-P0-020

`RESOLVED_FOR_CORE_ORDERING; FOLLOW-ON_LIFECYCLE_FINDINGS_OPEN`

The ninth-review impossibility is gone. Baseline 0.11 no longer accepts runtime trust before the intended code deployment exists. It stages a zero-authority App, deploys code, stops, applies final bindings, creates only a candidate from pre-start evidence, explicitly starts the last deployment, re-observes the same ID, and accepts only afterward. Setup-only behavior and stop-on-failure are explicit.

This resolution should be preserved. `DBX-P0-022` and `DBX-P0-023` are narrower follow-on defects in how the two saved plans and the pinned runner actually behave; they do not justify reverting to pre-deployment acceptance.

### DBX-P0-021

`PARTIALLY_RESOLVED_FOR_P0`

The missing-carrier/access/lifecycle defect is resolved in substance:

- customer-local `runtime_trust_ledger` and `runtime_trust_status_v` are named;
- the verifier/trust committer has persistent `SELECT`+`MODIFY` on the ledger;
- runtime principals cannot promote trust and read only the sanitized view;
- the App and writers have an explicit durable read path after restart/workstation loss;
- expiry uses server evaluation time and stale behavior is separated from migration truth;
- refresh, history, retention/export, ownership transfer, and delete-uninstall are addressed;
- the owner, `MANAGE` principals, verifier group, administrators, and other control roots are disclosed.

Full P0 acceptance remains open because the ninth review also required an exact snapshot/deployment/component schema, terminal commit semantics, authoritative clock, and duplicate/conflict/replay rules. Baseline 0.11 lists the fields and outcomes but does not resolve their cardinality and verification consistently. That residual is tracked precisely as `DBX-P0-024`; it is no longer a complaint that no durable object exists.

## Prior-finding disposition

| Finding | Tenth re-review disposition |
|---|---|
| `DBX-P0-001` through `DBX-P0-008` | `RESOLVED_FOR_P0`; no regression found in identity separation, bounded reconciliation, App/action authorization, prerequisites, egress, optional enrichment, App permission/resource separation, or P6 identity/DML boundaries. |
| `DBX-P0-009` | `REOPENED_IN_PART_BY_DBX-P0-022`; Direct saved plans remain the right mechanism, but two plans made from the same pre-stage state are not a valid sequential lifecycle. |
| `DBX-P0-010` through `DBX-P0-019` | `RESOLVED_FOR_P0`; no regression found in deployment/data-plane separation, recoverable fixed DML, targeted grants, migration identity, pending/composite truth, warehouse/Query History recovery, exact runtime DML, whole-group roots, or direct-versus-effective warehouse authority. |
| `DBX-P0-020` | `RESOLVED_FOR_CORE_ORDERING`; implementation remains blocked by follow-on saved-plan and runner reconciliation findings 022/023. |
| `DBX-P0-021` | `PARTIALLY_RESOLVED_FOR_P0`; durable carrier, access, expiry, and lifecycle are present, but exact ledger/view semantics remain blocked by 024. |
| `DBX-P0-F01` | `RESOLVED_FOR_P0`; current DML, inheritance, ownership/`MANAGE`, visibility, pagination, and whole-group roots remain explicit. |
| `DBX-P0-F02` | `RESOLVED_FOR_P0`; optional enrichment remains separate, pair-scoped, disabled by default, and removable. |

## Author-file outcome

| Author file or set | Outcome | Databricks conclusion |
|---|---|---|
| `README.md` | `CHANGES_REQUIRED` | The architecture remains recommended, but “staged once” and durable fail-closed trust depend on deployment reconciliation and an executable ledger contract. |
| `AGENTS.md` | `CHANGES_REQUIRED` | The security invariants are directionally strong; add sequential final planning, complete deployment-set reconciliation, and exact ledger/signature/time semantics. |
| `docs/index.md` | `PASS` | The index introduces no independent platform/security contradiction. |
| `docs/decisions/0001-private-app-bundle.md` | `CHANGES_REQUIRED` | Preserve the stage-stop-bind-candidate-start-accept decision, but state that final planning occurs after staging and freeze how the intended deployment is uniquely reconciled. |
| `docs/plans/product-plan.md` | `CHANGES_REQUIRED` | Primary location of all three blockers: precomputed plans, hidden runner retry/old-deployment start, and under-specified trust-event/view cardinality. |
| `docs/plans/review-process.md` | `CHANGES_REQUIRED` | Add explicit review gates for post-stage final-plan lineage/serial, deployment before/after inventory/retry ambiguity, and executable ledger/view/signature/time fixtures. |
| `docs/plans/documentation-plan.md` | `CHANGES_REQUIRED` | Tutorials currently teach a final plan without a post-stage planning/approval step and promise captures whose deployment/ledger expected state is not yet deterministic. |
| `docs/research/source-register.md` | `CHANGES_REQUIRED` | It records saved-plan validation and the broad App runner boundary, but must record the sequential-plan consequence, old-deployment start, deployment helper reissue path, deployment inventory surfaces, and chosen mitigation. |

## P0-P10 Databricks coverage matrix

These are planning outcomes; they do not claim implementation or live evidence exists.

| Part | Planning outcome | Databricks conclusion and required next evidence |
|---|---|---|
| P0 - Product contract | `CHANGES_REQUIRED` | Resolve 022-024 and re-review a new immutable author set. The private App plus Direct Bundle remains the recommended architecture. |
| P1 - Capture library | `PASS_WITH_FOLLOW_UP` | dbt artifact/event parsing remains portable. Before P1 exit, freeze the accepted snapshot/component identifier that evidence rows stamp. |
| P2 - Collector and reconciliation | `CHANGES_REQUIRED` | Exact three-table DML/no-DDL boundaries remain sound, but the collector's component-specific status lookup and stale stamp depend on 024. |
| P3 - Bundle installer | `CHANGES_REQUIRED` | Implement sequential Direct planning, complete App-deployment reconciliation, and the executable trust-event commit/view contract; prove every interruption state with pinned CLI 1.7.0. |
| P4 - Read-only App MVP | `CHANGES_REQUIRED` | Setup-only safe boot and view-only reads remain sound. Every-page accepted/stale state needs one deterministic `runtime_trust_status_v` result. |
| P5 - Existing-job onboarding | `PASS` | Scanner, proposed patch, owner approval, and rollback classification do not depend on these lifecycle defects. Evidence cannot be labeled trusted until P3/P4 pass. |
| P6 - Controlled actions | `CHANGES_REQUIRED` | Conditional DML must join one exact fresh component/snapshot row; candidates, duplicate/conflicting acceptance, ambiguous deployment, and expiry must all lock actions. |
| P7 - Security and operations | `CHANGES_REQUIRED` | Document sequential plan/re-plan recovery, hidden old-code interval, deployment inventory, event/key/time lifecycle, trusted-root tamper limits, retention/export, and retain/delete-uninstall. |
| P8 - Bounded live proof | `CHANGES_REQUIRED` | Add stale-plan, first-response-loss, multiple deployment, pagination, old-deployment start, ledger cardinality/concurrency/signature/time, restart, and final zero-compute/pending-deployment cases. |
| P9 - Optional intelligence | `PASS` | Genie/AI remains optional and outside capture, deployment, data seal, authorization, and runtime-trust authority. No Preview AI feature is required for the base path. |
| P10 - Private alpha | `CHANGES_REQUIRED` | Non-author installs/upgrades cannot be accepted until the exact pinned lifecycle reaches final bindings and one durable trust state deterministically after failures. |

## Explicit verdict

`CHANGES_REQUIRED`

Baseline 0.11 preserves the recommended Azure Databricks product architecture and correctly repairs the broad deployment-before-acceptance order. It also supplies the previously missing durable customer-local trust carrier and least-privilege reader/writer boundary. No new required Preview dependency was found.

The baseline is not yet implementable as written. Generate the final-binding Direct plan only after the stage plan, deployment, and stop have established current Direct/remote state; reconcile the full before/after App deployment set around the pinned runner's start-and-retry behavior; and freeze one executable, cardinality-consistent Delta event/current-view contract with authoritative time and either verified or explicitly non-authoritative signatures. Propagate those decisions through P0-P10, the ADR, source register, review process, and documentation plan, then request another independent Databricks platform/security review.
