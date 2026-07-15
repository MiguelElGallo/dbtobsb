# Usability and service-design eleventh re-review: P0 planning baseline 0.12

- Reviewed input: frozen author-owned planning file set
- Frozen author-input SHA-256: `93343ae870073dbe4518765b8949edc29d0a992255b36854b0e62c631f78392b`
- Hash scope: `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, globally sorted by path; SHA-256 of the path-ordered per-file SHA-256 records
- Date: 2026-07-15
- Reviewer: independent usability, onboarding, and service-design eleventh re-review
- Verdict: `PASS_WITH_FOLLOW_UP`
- Open P0 usability blockers: none
- Open non-blocking implementation follow-up: `UX-P0-F03`, hard P3 gate
- Cloud mutation: none

## Immutable input and review method

I independently recomputed the assigned author-input digest before reviewing. It was exactly:

```text
93343ae870073dbe4518765b8949edc29d0a992255b36854b0e62c631f78392b
```

I read the complete frozen author set and all three tenth specialist reports. I walked the combined and separated install journeys, interruption and recovery, refresh, upgrade, rollback, uninstall, first evidence, P6 expiry, cost, and documentation routes. I specifically tested the user consequences of the tenth Databricks findings `DBX-P0-022`, `DBX-P0-023`, and `DBX-P0-024`, and rechecked every prior UX finding including `UX-P0-F03`.

This report is outside the frozen hash scope and is the only file written by this review. I did not change an author file or an earlier report. I made no Azure, Databricks, authentication, account-console, SQL, warehouse, App, Job, Unity Catalog, or dbt call.

## Executive verdict

Baseline 0.12 passes P0 usability and service-design review. It turns the three tenth Databricks blockers into one coherent user journey without reintroducing a hand-authored identifier, an ambiguous authority transition, or a false success state:

- The stage plan and final-binding plan are now sequential. Before the first mutation, a non-executable intent explains the eventual bindings, ACLs, principals, and cost. The user separately approves the executable zero-authority stage plan. Only after code staging, complete deployment reconciliation, and a proved stop does the wrapper create the exact final plan from current lineage, serial, and remote state and request a second approval.
- One wrapper invocation is no longer described as one deployment submission. The user is told that the pinned runner can briefly start prior code and can internally reissue its deployment POST. The wrapper inventories every deployment page before and after, stops on every exit, and proceeds only for exactly one new matching terminal `SNAPSHOT`. The user never chooses or enters a deployment ID.
- Runtime trust now has one understandable physical and presentation model: one Delta row per logical event, one complete canonical component array per generation, and at most one latest-generation installation summary. Server commits anchor the two evidence clocks. Optional client signatures are plainly audit metadata, not an authorization signal.

No new critical, high, medium, or low P0 usability finding is opened. `UX-P0-F03` remains deliberately open as the hard P3 release gate for real signed installer assets, supported workstation combinations, secure-store and two-account local behavior, restart/reboot, and uninstall. This is why the verdict remains `PASS_WITH_FOLLOW_UP` rather than an implementation pass.

## Focused acceptance checks

| User concern | Eleventh-review outcome | Usability conclusion |
|---|---|---|
| Two sequential approvals | `PASS` | The first approval is explicitly the no-product-authority stage plan. The second is explicitly `APP_FINAL_BINDINGS_APPROVE`, created only after deployment reconciliation and stop. The pre-stage intent lets the user understand the complete expected outcome before mutation without mislabeling a stale preview as executable. The final comparison permits only the previously disclosed bindings and ACLs and shows any intent mismatch. |
| Final-plan drift and interruption | `PASS` | Stale lineage/serial, remote drift during review, process death, and partial Apply cannot reuse an old plan. They return to recovery audit and fresh planning. `APP_FINAL_PLAN_REVIEW_REQUIRED`, `APP_FINAL_PLAN_INTENT_MISMATCH`, and `APP_FINAL_PLAN_STALE` keep review, semantic mismatch, and technical staleness distinct. |
| Approval-time fairness | `PASS_AT_PLANNING_GATE` | The active-time denominator explicitly includes authentication, reading, comparing, confirmation, approval, roster review, and recovery. It therefore includes both stage and final approvals; neither can be hidden as platform wait. The combined target remains 20 total active minutes and separated remains 15 active minutes per Databricks actor, with roster work in verifier time. These are provisional targets, not claimed measurements. P3 must rehearse the complete two-approval route and may change a threshold only through an approved rehearsal-backed decision. |
| Prior-code start and internal retry | `PASS` | The plan states that `bundle run` may briefly start the prior deployment and may reissue the deployment POST internally. Before invocation, prior code must have zero product authority and no user access. The UI must disclose the bounded billed interval, current compute state, stop owner, and that one invocation is not one submission. |
| No-ID deployment reconciliation | `PASS` | Every before/after page, active/pending pointer, status, mode, source, artifact, and configuration digest is consumed and compared automatically. Exactly one new terminal matching `SNAPSHOT` is the only success. No UI or recovery step asks the user to select, paste, or enter a deployment ID. |
| Multiple new deployments | `PASS_AT_PLANNING_GATE` | Multiple records cannot be resolved by choosing one. The wrapper stops, completes reconciliation, invalidates the generation, and disables final planning, candidate creation, start, and acceptance. The operation contract permits exactly one safe action and the documentation route is **Recover an ambiguous App deployment**: remain stopped and resume remote reconciliation, never rerun the current staging invocation. Once multiple terminal records are confirmed, the only permitted continuation is a newly registered generation; no second candidate or acceptance may be appended to the invalid generation. P3 must render this as one action, not a choice of records. |
| Pending, timeout, lost response, and failed stop | `PASS` | Stable states distinguish baseline failure, indeterminate invocation, pending timeout, ambiguous set, active mismatch, and failed stop. Every state reports required actor, running compute, pending/new count, binding state, and one safe next action. `APP_STOP_FAILED_RUNNING_UNVERIFIED` visibly exposes continuing cost and only stop/reconcile, never success. |
| Trust object/cardinality model | `PASS` | One physical row equals one event; components are nested, ordered, unique, complete, and generation-wide. Registration, candidate, acceptance, and invalidation have distinct required/null fields. The current view returns at most one installation summary, never one row per component or a cross-generation mixture. This removes the operator guess about which component row is authoritative. |
| Trust labels and clocks | `PASS` | Candidate is never positive trust. Accepted, stale, invalidated, code drift, authority drift, and unverified are distinct. The App shows roster time, machine time, oldest evidence time/age, acceptance time, expiry, evaluation time, and the point-in-time/non-independent qualifier. A client cannot backdate or extend either evidence clock. |
| Refresh | `PASS` | The verifier or combined administrator reruns `dbtobsb bootstrap` and receives one checkpoint action, **Refresh runtime trust**. An unchanged refresh has no UC handoff or code deployment. Exact early roster reuse cannot extend expiry; a 24-hour renewal repeats native review. Code, configuration, or binding change routes back to the stopped staged lifecycle. |
| Upgrade and rollback | `PASS` | A new registration immediately makes old trust non-current and locks P6. The App stops and loses final bindings before the runner can briefly start prior code. The full baseline, one invocation, stop, reconciliation, fresh final plan and approval, candidate, direct start, reobservation, and acceptance sequence is repeated. |
| Retain, delete, and uninstall | `PASS` | Uninstall first stops compute, reconciles the deployment set, and removes bindings through a fresh approved plan. Retain/export remains the default and transfers the trust history/view and residual-authority disclosure. Irreversible deletion remains a separate attended plan with export and verification; foreign grants and the customer-owned schema are not removed by implication. |
| Combined versus separated modes | `PASS` | Combined mode uses one account-administrator actor/profile and records every independence flag false. Separated mode uses exactly a verifier administrator and a different UC operator in distinct managed OS accounts. The verifier owns the roster task. A third reviewer, non-account-admin verifier, same-account separation, or separate-workstation handoff fails before mutation rather than producing an improvised route. |
| P6 controlled actions | `PASS_AT_PLANNING_GATE` | Prepare, approve, and run read authorization without a cache. The run statement must find one fresh latest-generation summary and exactly one matching `CONTROLLED_ACTIONS` component. Candidate, stale, invalidated, drift, conflict, missing/duplicate component, or a new registration locks action execution. The same staged, reconciled, sequential-plan lifecycle applies when P6 is installed. |
| First evidence | `PASS` | Before final acceptance, the running App is setup-only and exposes no trusted evidence, collection, or action. After acceptance, a packaged fixture precedes one explicit cost-confirmed one-model run. `Observable` requires the expected evidence row, so App readiness, dbt result, collector result, archive state, capture state, and trust state cannot collapse into one success label. |

## End-to-end service walkthrough

The normal bootstrap now presents a comprehensible sequence rather than a long undifferentiated deployment operation:

1. Verify mode, actor, workspace, prerequisites, recovery state, data intent, and costs.
2. Complete the attended data envelope, exact revoke, pending attestation, and live composite seal in the selected mode.
3. Review a non-executable final-binding intent and separately approve/apply the zero-authority stage plan.
4. Capture the complete deployment baseline, invoke staging once, stop, and reconcile remotely without asking for an ID.
5. Review and approve the fresh executable final plan generated from the stopped current state.
6. Perform pre-start machine observation and the verifier-owned native roster comparison; record only a candidate.
7. Start the reconciled deployment without deploying code, reobserve the same deployment, and append final acceptance.
8. Show the App URL, both evidence clocks, oldest age, expiry, running-cost state, and the next task.

The two approvals are meaningfully different and use recognizable labels: stage approval authorizes a resource/code staging state with zero product authority; final approval authorizes only the reviewed bindings and ACLs for the already reconciled stopped deployment. The user is not asked to approve the same artifact twice. Intent mismatch, stale plan, and deployment ambiguity each lead to a named recovery route instead of a generic retry.

For multiple-deployment failure, the zero-guess rule is preserved. While the remote state is pending or incomplete, the single action is to remain stopped and resume reconciliation. When reconciliation proves multiple terminal new deployments, the generation is invalid and cannot advance. The product must present the new-generation recovery action without offering either deployment as a selectable candidate. That exact interaction remains required P3 evidence, but the P0 decision is no longer ambiguous.

## Resolution of the tenth Databricks findings from the user perspective

| Databricks finding | Eleventh usability disposition |
|---|---|
| `DBX-P0-022` | `RESOLVED_FOR_P0`; the executable final plan is generated only after stage Apply, deployment reconciliation, and stop; it has current lineage/serial, its own approval, and fresh-plan recovery on drift or interruption. |
| `DBX-P0-023` | `RESOLVED_FOR_P0`; prior-code start and internal POST reissue are disclosed, one invocation is not called one submission, before/after inventories are automatic, every exit stops/reconciles, and no human selects an ID. |
| `DBX-P0-024` | `RESOLVED_FOR_P0`; physical event cardinality, complete component collections, event nullability, deterministic IDs/readback, server time anchors, signature non-authority, and latest-generation view reduction now have one testable meaning. |

## Prior UX finding disposition

`RESOLVED` below means the frozen planning contract is implementable and testable. It does not claim that P1-P10 assets or live evidence already exist.

| Finding | Eleventh disposition |
|---|---|
| `UX-P0-001` | `RESOLVED — NO REGRESSION`; one signed wrapper, actor-owned authentication, durable Operations, and final URL handoff remain coherent. |
| `UX-P0-002` | `RESOLVED — NO REGRESSION`; exactly one combined route and one exactly-two-person separated route are selected before mutation. |
| `UX-P0-003` | `RESOLVED — NO REGRESSION`; readiness, change-needed, unsupported, access-blocked, and check-failed outcomes remain distinct. |
| `UX-P0-004` | `RESOLVED_AT_CONTRACT`; whole-process WCAG 2.2 AA, keyboard, screen-reader, zoom/reflow, status, and error evidence remain mandatory before conformance is claimed. |
| `UX-P0-005` | `RESOLVED`; Operation/Problem state now additionally distinguishes deployment baseline, indeterminate staging, set ambiguity, failed stop, final review, intent mismatch, and stale final plan while preserving one actor and one safe next action. |
| `UX-P0-006` | `RESOLVED`; every participant has an executable start and terminal task, and the active-time denominator expressly includes both approvals and roster work. |
| `UX-P0-F01` | `RESOLVED_AT_CONTRACT`; App size, DBU/hour, prior-code/stage intervals, running state, stop owner, budget, and scoped final inventory remain hard P8 evidence. |
| `UX-P0-F02` | `RESOLVED_AT_CONTRACT`; stop, remove configuration, retain/export, irreversible delete, and verification remain separate lifecycle choices. |
| `UX-P0-007` | `RESOLVED — NO REGRESSION`; the deployment CLI remains exact, pinned, GA, and absent from product runtime. |
| `UX-P0-F03` | `OPEN_NONBLOCKING_P0_HARD_P3_GATE`; no concrete signed installer or supported platform claim exists yet. P3 must publish and test exact OS/architecture support, assets/checksums, native secure-store behavior, two-account spool/ACL/session release, one-account combined behavior, restart/reboot, uninstall, and explicit unsupported-platform/topology errors. It must also exercise the complete two-approval and one-action deployment-recovery UI. |
| `UX-P0-F04` | `RESOLVED — NO REGRESSION`; inventory still distinguishes product/test-owned, reused, and unrelated resources and restores only proof-owned changes. |
| `UX-P0-F05` | `RESOLVED — NO REGRESSION`; no part gate may waive an unresolved high or critical finding. |
| `UX-P0-F06` | `RESOLVED_AT_CONTRACT`; controlled-action summaries, distinct production actors, same-person denial, cost/expiry consequences, and recovery remain explicit. |
| `UX-P0-008` | `RESOLVED — NO REGRESSION`; attended data mutation, pending row, exact revoke, reconstruction, and later observation retain one safe chronology. |
| `UX-P0-009` | `RESOLVED — NO REGRESSION`; separated mode has one two-account data handoff/return and no third roster handoff. |
| `UX-P0-010` | `RESOLVED — NO REGRESSION`; combined mode remains complete without a false separation claim. |
| `UX-P0-011` | `RESOLVED — NO REGRESSION`; the verifier administrator owns native roster review and unsupported reviewer topology fails before mutation. |
| `UX-P0-012` | `RESOLVED`; final same-deployment acceptance, setup-only safe boot, refresh, both clocks, timing denominators, sequential plans, and automatic deployment reconciliation now form one lifecycle. |
| `UX-P0-013` | `RESOLVED — NO REGRESSION`; recovery surfaces still derive from one actor/capability/prohibition table. |

No new numbered usability finding is opened.

## Documentation-plan outcome

The documentation plan passes at P0 and reflects the repaired product truth.

- The Diataxis split remains complete: controlled tutorial, task how-tos, neutral reference, explanation, operations/security, and lifecycle routes have distinct jobs.
- Production bootstrap starts before the App exists and teaches the exact two-approval stage/reconcile/stop/fresh-plan/bind/candidate/start/reobserve/accept sequence.
- Dedicated how-tos cover ambiguous deployment recovery and stale final-plan recovery. They explicitly prohibit a second staging invocation, stale-plan bypass, or human deployment-ID selection.
- Reference material will catalogue plan lineage/serial, deployment inventories, stable codes, trust-event schema/cardinality, component arrays, server clocks, and one-row installation summary without embedding recovery procedure in reference pages.
- Combined and separated routes remain visibly distinct. Cost, prior-code start, internal runner reissue, running state, actor, mutation, authority, and one next action are required content.
- Documentation gates D2, D5, and D6 require real sequential-plan, deployment reconciliation, upgrade/uninstall, and P6 evidence. Real captures must include the second approval, full before/after pages, internal-retry and ambiguity failures, both evidence clocks, and zero active-resource cleanup.
- FastAPI-style readability, information architecture, technical, security/privacy, accessibility, rendered-site, non-author task, and publication-safety reviews remain separate passes.

The plan does not pretend those pages or screenshots already exist. `UX-P0-F03` still prevents the eventual installer documentation from claiming a supported workstation or completed interaction before P3 proves it.

## P0-P10 usability matrix

These are planning outcomes, not claims that later implementation or live evidence exists.

| Part | Eleventh usability outcome | Required next evidence |
|---|---|---|
| P0 — Product contract | `PASS` | Record this immutable-hash verdict with the Databricks and dbt specialist outcomes. No open P0 usability blocker remains. |
| P1 — Capture library | `PASS` | Implement actionable allowlisted validation errors, exact component matching, and malformed/partial/unsupported fixtures without raw diagnostic exposure. |
| P2 — Collector and reconciliation | `PASS` | Prove distinct Job/dbt/collector/archive/capture outcomes, one-summary trust stamping, stale continuation, exactly-once behavior, and visible bounded recovery. |
| P3 — Bundle installer | `PASS_WITH_FOLLOW_UP` | Implement and test the exact two-mode journey, sequential approvals, automatic full deployment reconciliation, prior-code/internal-retry cost disclosure, one-action failure states, fresh-plan recovery, trust ledger/view, setup-only start, and same-deployment acceptance. Close `UX-P0-F03` before supported release. |
| P4 — App read-only MVP | `PASS` | Build accessible setup-only, health, evidence, investigation, stale, recovery, running-cost, and lifecycle pages against one installation summary. |
| P5 — Job onboarding | `PASS` | Prove the five scanner outcomes, semantic-change preview, owner review, rollback, and no silent mutation. |
| P6 — Controlled actions | `PASS_AT_PLANNING_GATE` | Test uncached prepare/approve/run, exactly one fresh `CONTROLLED_ACTIONS` component, both clocks, expiry between phases, candidate/drift/conflict/cardinality locks, same-person denial, recovery, and no parameter override. |
| P7 — Security and operations | `PASS_WITH_FOLLOW_UP` | Publish and rehearse refresh, recovery, upgrade/rollback, App/workstation restart, cost/failure, retain/export/delete/uninstall, and supported-platform runbooks. |
| P8 — Bounded live proof | `PASS_AT_PLANNING_GATE` | Exercise zero/one/multiple/pending deployments, response loss/internal reissue, prior-code start, failed stop, stale final plan, drift during approval, trust conflicts, expiry, both modes, time denominators, first evidence, and final zero-resource inventory. |
| P9 — Optional intelligence | `PASS` | Keep all journeys complete with AI disabled and prevent AI from becoming a deployment, authorization, capture, trust, migration, or free-form dbt path. |
| P10 — Private alpha | `PASS_AT_PLANNING_GATE` | Non-author participants must complete both modes, two approvals, no-ID ambiguity recovery, first evidence, refresh, upgrade, retain/delete/uninstall, and the provisional timing targets with zero safety-critical error or moderator takeover. |

## Final disposition

`PASS_WITH_FOLLOW_UP`.

Baseline 0.12 is a coherent, fail-closed P0 service journey. The second approval has a distinct purpose, a current-state artifact, clear recovery, and explicit inclusion in active-time measurement. The pinned runner's prior-code start and internal retry are disclosed rather than hidden. Deployment reconciliation is automatic; multiple deployments invalidate the generation and never create an ID-choice task. Runtime trust has one physical model, one summary model, two server-anchored clocks, and exact component semantics. Refresh, upgrade, rollback, uninstall, P6, combined/separated modes, first evidence, cost, and documentation routes remain consistent.

No P0 usability blocker remains. `UX-P0-F03` is still appropriate and remains the hard P3 gate for the concrete signed installer, supported workstation claims, and real interaction evidence. No Azure or Databricks resource was created, started, stopped, queried, changed, or deleted by this review.
