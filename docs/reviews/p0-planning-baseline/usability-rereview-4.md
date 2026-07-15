# Usability and onboarding fourth re-review: P0 planning baseline 0.5

- Reviewed input: frozen author-owned planning file set; repository has no commit yet
- Frozen author-input SHA-256: `974745400db1efe497938afbce9bd41e6b03d37aa0f10b6c5eb33e0d9cfd8f84`
- Hash scope: `README.md`, `AGENTS.md`, `docs/index.md`, and all Markdown files under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path; SHA-256 of the sorted per-file SHA-256 records
- Date: 2026-07-15
- Reviewer: independent usability and onboarding fourth re-review
- Verdict: `CHANGES_REQUIRED`
- Cloud mutation: none

## Scope and method

I independently recomputed the frozen hash before this review. It exactly matched the assigned value. I read the complete author-owned scope, every earlier usability report, and the current resolution ledger. I also inspected the pinned Databricks CLI 1.7.0 implementation of Direct plan calculation, saved-plan state validation, and grant removal. I did not edit an author-owned file, an earlier review, or a cloud resource.

This pass re-evaluates every P0-P10 planning contract and all author documentation. Its main change focus is the new multi-plan installation: one signed entry command; no user-entered SQL, internal IDs, constructed paths, or YAML; separate resource-bootstrap, data, seal, runtime-binding, and App-start consequences; accountable permission handoffs; interruption recovery; first evidence; cost; lifecycle choices; P6 action summaries; and complete-process accessibility. `PASS` below means that a planning contract is testable. It does not pre-approve implementation or live evidence assigned to P1-P10.

The revised baseline improves the mental model substantially, but it has one high-severity safety and trust defect. It says that an executable saved Direct seal plan is prepared before the resource-bootstrap plan creates the temporary `CREATE TABLE` grant. The pinned Direct engine calculates a saved plan from the state that exists when the plan is generated. On a fresh deployment, that pre-bootstrap state cannot yield a removal of a grant that does not yet exist. The installer therefore cannot truthfully tell the approver that a valid executable seal is ready before applying the bootstrap plan.

## Current primary sources checked

- The pinned CLI's [`CalculatePlan`](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/bundle_plan.go#L117-L129) computes a Direct plan by comparing local configuration with current remote state. When a resource is not in deployment state, the planner classifies it as a create rather than an update or removal ([source](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/bundle_plan.go#L207-L214)).
- Direct saved-plan validation rejects a changed lineage or serial, but explicitly skips that validation when an initial plan has no lineage ([CLI 1.7.0 source](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/bundle_plan.go#L42-L58)). Two plans generated against the same empty first-deployment state are therefore not a safe before/after pair.
- The Direct grants adapter identifies removals from principals present in the plan's remote grant state and absent from desired assignments ([CLI 1.7.0 source](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/dresources/grants.go#L168-L192)). A plan generated before the temporary principal is present cannot encode that principal as a removal through this path.
- [Manage Apps with Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial) keeps Bundle resource deployment distinct from `bundle run <app-resource-key>`, which starts/deploys the App. The baseline retains that understandable cost boundary.
- [Add resources to a Databricks App](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/resources) recommends bindings instead of hard-coded resource IDs and requires the resource to exist. The zero-ID runtime-binding journey remains appropriate.
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) applies conformance to full pages and complete processes and includes status, error identification, labels, focus, reflow, and non-color requirements. The baseline's full-process AA scope remains stronger and more precise than isolated component checks.
- [RFC 9110 section 15.3.3](https://www.rfc-editor.org/rfc/rfc9110.html#name-202-accepted) says `202 Accepted` does not mean processing completed and calls for a status monitor. [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) defines Problem Details separately. The baseline correctly keeps a pollable Operation distinct from terminal Problem representation.
- [GOV.UK moderated usability testing](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing) recommends realistic goal-based tasks with actual or likely users. [Usability benchmarking](https://www.gov.uk/service-manual/measuring-success/usability-benchmarking-a-website-or-whole-service) measures completion, time, abandonment/false success, ease, and confidence. These support the baseline's role-specific multi-plan task tests and separate active time from platform wait.

## Focused acceptance review

| Criterion | Result | Independent evidence |
|---|---|---|
| One signed entry point | `PASS` | `product-plan.md:340-372` retains one signed `dbtobsb` wrapper and one first command, `dbtobsb bootstrap`. The wrapper embeds the pinned CLI, verifies the release, confirms profile/host/current user, and owns all child commands. |
| No entered SQL, internal IDs, paths, or YAML | `PASS` | Resources are selected by display name, fixed SQL is review-only, commands receive generated values, and `product-plan.md:372` plus the usability task gates prohibit those manual inputs. The protected data plan may display fixed secret-free SQL without asking the user to author or paste it. |
| Resource, data, seal, runtime, and App-start consequences are distinct | `PASS_WITH_REQUIRED_FIX` | `product-plan.md:111-126,352-370` and `documentation-plan.md:41-44,112-114,213,223` establish a sound vocabulary and order. The claimed pre-bootstrap executable seal is invalid, and the documentation still says “both approved plan digests” despite more than two distinct approvals/receipts. See `UX-P0-008`. |
| Human permission handoffs | `PASS` | `product-plan.md:155-170` names the deployment operator, UC/data-plan owner, Job owner, warehouse owner, dbt owner, product administrator, action-role administrator, and read-only operator; it gives the grant owner, residual access, single-person path, separated-duties path, display-name error, and recheck rule. |
| No mutation before an understandable approval | `PASS_WITH_REQUIRED_FIX` | Resource and data mutation each have exact previews and approval. Cleanup intent is included in the resource approval, but the executable saved seal plan cannot yet be generated from the post-bootstrap state. If prior approval is reused for that later plan, exact equivalence to the approved cleanup intent must be proven; otherwise the later plan needs approval. |
| Safe interruption and cleanup | `FAIL` | `finally` handles a live wrapper process, but not termination of the workstation/process after temporary authority is applied. The currently described precomputed seal does not safely cover that gap. A resume must become cleanup-only and derive a valid seal from actual post-bootstrap state before any migration or runtime action. |
| App remains unavailable until verified and sealed | `PASS` | `DATA_VERIFY`, `DATA_SEAL`, fresh runtime planning, stopped lifecycle, explicit `APP_CODE_START`, and readiness are correctly gated. A failed seal blocks bindings and App start. This control must remain after fixing the seal-plan chronology. |
| First value is real evidence, not deployment success | `PASS` | The App performs a packaged fixture, offers one cost-confirmed real one-model run, queries the expected evidence row, and only then marks the installation `Observable`. Job, capture, collector, invocation, and node/test outcomes remain distinct. |
| Cost and no-running-compute state | `PASS` | Migration and role Jobs are unscheduled and bounded; schedules start paused; App start is explicit; every live test shows its ceiling, owner, cancellation, and cleanup; failed readiness defaults to stopping; and scoped inventory protects reused and unrelated resources. |
| Lifecycle decision safety | `PASS` | Stop App, remove code/configuration, retain/export, irreversible delete/verify, and uninstall are separate choices. Upgrade quiesces first; uninstall removes App bindings before data; retain/export is default; deletion requires its own plan and verification. |
| P6 immutable summary and optionality | `PASS` | The optional upgrade remains locked until resource, secret, data, seal, runtime, and identity conditions pass. Prepare/approve/run bind the same action, environment, Job display name, selector, actor roles, run-as identity, cost, writes, cancellation, retry, expiry, and digest. `UX-P0-F06` remains resolved. |
| Accessibility and status/recovery | `PASS` | Full pages and complete processes target WCAG 2.2 AA; manual keyboard and representative screen-reader checks supplement automation; CLI output is text/JSON/no-color; and Operation/Problem fields exclude unsafe raw content. |
| Workstation support | `PASS_WITH_FOLLOW_UP` | The regulated path already blocks plaintext/unavailable secure storage and always passes the explicit profile. `UX-P0-F03` remains correctly bounded as a hard P3 release/documentation gate. |

## Multi-plan journey review

The human-facing mental model is otherwise coherent:

1. **Resource bootstrap** creates only supported product resources and grants temporary migration authority. It does not claim to create a table or App binding.
2. **Data plan** shows every fixed table/view operation, owner, schema version, exact non-App grant, cost, rollback class, and fingerprint. The user reviews SQL but never supplies SQL.
3. **Data apply and verify** run signed fixed code with only a nonsecret migration ID and approved digest, then independently compare the actual objects and grants.
4. **Seal** removes temporary DDL authority and proves the grant is absent.
5. **Runtime plan** binds the App only to verified existing objects and leaves App compute stopped.
6. **App start** is the separate cost-bearing action, followed by readiness, fixture evidence, one real run, and read-only handoff.

That sequence is teachable, and the non-author UC/data-plan-owner task is exactly the right test. The flaw is not that the user sees too many plans. The flaw is that the seal artifact is generated at the wrong state boundary while being described as executable recovery. Direct plans are state-derived artifacts, so a plan to remove the temporary grant must be calculated after that grant exists in the tracked and remote state.

On a fresh install, a pre-bootstrap “seal” plan can contain create/desired-state actions rather than the later removal. Because the pinned CLI skips lineage/serial validation for a plan with no initial lineage, it cannot be relied on to reject that stale first-deployment plan. On a later upgrade, a state-changing bootstrap apply should make a precomputed seal's serial stale and cause rejection. Neither behavior satisfies “failure always seals.”

## New required finding

### `UX-P0-008`: Generate and prove the executable seal from post-bootstrap state

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Owner: P3 Bundle-installer owner, with Databricks and usability re-review
- Affected evidence: `docs/decisions/0001-private-app-bundle.md:23,45,53-55`; `docs/plans/product-plan.md:117-126,352-370,434,452,463,478-479`; `docs/plans/documentation-plan.md:41-44,112-114,213,223,247-250,284`
- Baseline evidence: Installation step 5 says to prepare the saved seal plan “in parallel with approval,” before applying the resource-bootstrap plan that creates the schema/grant. The ADR calls it a pre-approved saved seal and promises that failure always seals. The P3/P8 gates then rely on that promise.
- Primary-source evidence: CLI 1.7.0 calculates the Direct plan from the current deployment and remote state, treats an absent resource as a create, derives removed grant principals only from remote assignments, and skips saved-plan lineage/serial validation when an initial plan has no lineage. A plan computed before the grant exists is therefore not a valid saved plan for its later removal.
- User impact: An approver can be told that an executable cleanup is ready when it is not. If bootstrap succeeds and the wrapper, terminal, workstation, or network dies before a valid post-state seal is generated/applied, temporary `CREATE TABLE` can remain. A subsequent attempt can reject the stale plan or apply a plan that never encoded the revocation. App start is blocked, but residual authority is still a security and operational incident; the user has no truthful “safe to resume” state.
- Required change:
  1. Separate approval of cleanup intent from creation of the executable Direct plan. After resource-bootstrap apply, refresh tracked and live grant state and generate the saved seal plan from that post-bootstrap state. Bind it to the current lineage/serial, principal, target, source/build, selection, and expected exact removal before starting the migration Job.
  2. If the original approval is reused, prove that the generated post-state plan is exactly the pre-approved cleanup intent and contains only the expected temporary-grant removal. Any difference requires approval. Do not ask the person to enter SQL, an internal ID, path, or YAML.
  3. Define visible states such as `TEMPORARY_DDL_ACTIVE`, `SEAL_PLAN_READY`, `SEALED`, and `SECURITY_CLEANUP_REQUIRED`. No data apply may start until `SEAL_PLAN_READY`; no runtime plan or App start may occur until `SEALED` is independently verified.
  4. On every wrapper start/resume, detect temporary authority before other mutation. If authority exists without a valid current seal plan, enter cleanup-only recovery, generate/apply/verify the revocation from actual state, and report whether anything is running. Do not run the migration, collector, role Job, or App in that recovery mode.
  5. Kill-test every boundary: after resource apply but before seal-plan generation; after seal-plan generation but before migration; during migration; after migration/verification but before seal apply; during seal apply; and after an apparent seal before independent verification. Test fresh empty lineage, ordinary serial mismatch, remote drift, process death, network loss, cancellation, and timeout. Every terminal path proves no temporary `CREATE TABLE`, no App binding/start, and no migration compute remains.
  6. Apply the same chronology and cleanup-only recovery to the P6 action-data upgrade.
  7. Update user-facing evidence to enumerate the resource-bootstrap receipt, data-plan approval/apply/verification receipt, post-state seal plan/receipt, runtime-plan receipt, and App-start result. Replace ambiguous “both approved plan digests” language.
- Acceptance condition: A non-author deployment operator and UC/data-plan owner can identify when temporary authority becomes active, prove that a valid current seal is ready before migration, recover from abrupt interruption using the displayed action, and verify the grant is absent without entering SQL, IDs, paths, or YAML. There is zero false-success or residual-authority outcome.

No other new `CHANGES_REQUIRED` or `BLOCKER` usability finding was found.

## Prior finding and follow-up disposition

| Finding | Baseline 0.5 disposition | Fourth re-review result |
|---|---|---|
| `UX-P0-001` | One signed wrapper and command, explicit profile/identity, resumable stages, URL handoff | `RESOLVED`; the new multi-plan stages preserve the canonical entry point |
| `UX-P0-002` | Human-role table, exact prerequisites, owner routing, residual access, separated duties | `RESOLVED`; multi-plan ownership is now more explicit |
| `UX-P0-003` | Five scanner outcomes; only `NEEDS_CHANGES` can propose a patch | `RESOLVED` |
| `UX-P0-004` | Full-page and complete-process WCAG 2.2 AA scope with manual and automated evidence | `RESOLVED`; implementation evidence remains at each relevant part |
| `UX-P0-005` | Separate pollable Operation and RFC 9457 Problem contracts with safe fields and recovery | `RESOLVED`; the seal states/recovery above must use this contract |
| `UX-P0-006` | Named non-author personas, safety/time/ease/confidence thresholds, fresh confirmation users | `RESOLVED`; the new UC/data-plan-owner task is an appropriate extension |
| `UX-P0-F01` | Numerical live-proof ceiling, cancellation, owner, stopped/paused end state, scoped inventory | `RESOLVED` at contract level; P8 live proof pending |
| `UX-P0-F02` | Stop, remove configuration, retain/export, irreversible delete/verify are separate | `RESOLVED` at contract level; P7 evidence pending |
| `UX-P0-007` | CLI 1.7.0 is consistently exact, pinned, GA, and deployment-only | `RESOLVED` |
| `UX-P0-F03` | Exact OS/architecture, assets, secure-store backend, prerequisites, clean-machine tests, unsupported errors | `OPEN`; sole pre-existing usability follow-up and hard P3 release gate |
| `UX-P0-F04` | Scoped pre/post inventory protects reused and unrelated resources | `RESOLVED`; P8 evidence pending |
| `UX-P0-F05` | All normative gates use “high or critical” consistently | `RESOLVED` |
| `UX-P0-F06` | Immutable controlled-action summary and digest/change/revalidation behavior | `RESOLVED` at contract level; P6 task/API evidence pending |

## P0-P10 no-regression matrix

| Part | Fourth re-review verdict | Usability/onboarding result |
|---|---|---|
| P0 — Product contract | `CHANGES_REQUIRED` | The product and review contracts are otherwise measurable, but `UX-P0-008` makes the current seal/recovery promise false. |
| P1 — Capture library | `PASS` | Fail-closed validation, safe messages, exact artifact/event states, and no raw evidence remain testable; P1 supplies fixture evidence. |
| P2 — Collector and reconciliation | `PASS` | The collector is DML-only, identities and grants are narrow, and Job/dbt/collector/capture outcomes plus cancellation reconciliation remain distinct. |
| P3 — Bundle installer | `CHANGES_REQUIRED` | One-command, zero-guess, multi-plan installation is sound except for the invalid pre-bootstrap saved seal. Fix and test the post-state seal chronology; close `UX-P0-F03` before release. |
| P4 — App read-only MVP | `PASS` | Read-only curated access, distinct outcomes, safe asynchronous recovery, cost confidence, and full-process accessibility remain adequate planning gates. |
| P5 — Job onboarding | `PASS` | Five scanner states, source-controlled proposed patch, semantic-change review, dbt-owner approval, rollback, and no direct default mutation remain intact. |
| P6 — Controlled actions | `CHANGES_REQUIRED` | The immutable summary, identity/device model, exact grants, and no-half-enabled policy pass, but action-data enablement inherits `UX-P0-008` and cannot rely on a pre-bootstrap seal. |
| P7 — Security and operations | `CHANGES_REQUIRED` | Lifecycle choices, access review, export/delete, rollback, and uninstall are sound, but “no residual schema `CREATE TABLE`” is not yet supported by an executable interruption-recovery sequence. |
| P8 — Bounded live proof | `CHANGES_REQUIRED` | Cost/inventory boundaries pass. The proof cannot claim failed migration always seals until abrupt interruption and stale/empty-lineage seal cases pass after `UX-P0-008`. |
| P9 — Optional intelligence | `PASS` | AI remains advisory, optional, and outside authorization, mutation, capture, and validation. |
| P10 — Private alpha | `PASS` | Representative roles, first-value timing, safety-critical success, ease/confidence, fresh participants, and the high-or-critical gate remain measurable; inherited P3/P7 gates still block alpha execution until resolved. |

## Documentation-plan re-review

The documentation information architecture remains strong from a usability perspective. It separates the controlled fixture tutorial from production bootstrap; gives deployment operator, UC/data-plan owner, dbt owner, operator, governance administrator, action users, optional AI, and future Marketplace distinct task routes; separates procedures from reference; and requires real sanitized evidence and six independent review passes.

The content contract is `CHANGES_REQUIRED` only because it currently teaches the unsafe seal chronology. `bootstrap-the-private-app.md`, `review-and-apply-a-resource-bootstrap-plan.md`, `review-and-apply-a-data-migration.md`, `recover-an-interrupted-data-migration.md`, and `verify-and-apply-a-runtime-bundle-plan.md` must all use the corrected post-bootstrap seal lifecycle and cleanup-only resume state. `documentation-plan.md:213` must not say “both approved plan digests and receipts” when the reader needs distinct resource-bootstrap, data, seal, and runtime evidence. The evidence list at lines 247-250 is otherwise exactly the right publication gate once the executable sequence is corrected.

The future `reference/installer-platforms-and-secure-storage.md` must still close `UX-P0-F03` before any workstation combination is described as supported. Optional controlled-action material remains a separate D6 route, and the P6 immutable summary remains adequate.

## Final verdict

`CHANGES_REQUIRED` for frozen baseline 0.5.

The one-command, zero-entered-SQL/ID/path/YAML journey; role handoffs; first evidence; cost; lifecycle choices; P6 summary; and accessibility contracts pass. `UX-P0-F03` remains a properly bounded P3 release gate. Baseline acceptance is blocked by one new high-severity finding: generate and validate the executable saved seal plan from actual post-bootstrap state, and make abrupt interruption cleanup-only before any migration or runtime action. No Azure or Databricks resource was created, started, stopped, or deleted by this review.
