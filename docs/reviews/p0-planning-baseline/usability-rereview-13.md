# Usability, onboarding, and accessibility thirteenth re-review: P0 planning baseline 0.14

- Reviewed input: frozen author-owned planning file set
- Frozen author-input SHA-256: `3402e6cb5c96844be04a4d259fb8ca00d6fd60903e0f801fe2559c048334507a`
- Hash scope: `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file immediately under `docs/decisions`, `docs/plans`, and `docs/research`, globally sorted by path; SHA-256 of the path-ordered per-file SHA-256 records
- Date: 2026-07-15
- Reviewer: independent usability, onboarding, service-design, and accessibility thirteenth re-review
- Verdict: `PASS_WITH_FOLLOW_UP`
- Open P0 usability blockers: none
- Open non-blocking implementation follow-up: `UX-P0-F03`, hard P3 release gate
- Cloud mutation: none

## Immutable input and method

I computed the frozen author digest with exactly this command:

```sh
{
printf '%s\n' README.md AGENTS.md docs/index.md
find docs/decisions docs/plans docs/research -type f -name '*.md'
} | LC_ALL=C sort | while IFS= read -r file; do shasum -a 256 "$file"; done | shasum -a 256
```

The result before review was:

```text
3402e6cb5c96844be04a4d259fb8ca00d6fd60903e0f801fe2559c048334507a  -
```

The exact author scope was:

- `AGENTS.md`
- `README.md`
- `docs/decisions/0001-private-app-bundle.md`
- `docs/index.md`
- `docs/plans/documentation-plan.md`
- `docs/plans/product-plan.md`
- `docs/plans/review-process.md`
- `docs/research/source-register.md`

I read all eight author files, the complete twelfth usability report, the twelfth Databricks finding and acceptance conditions for `DBX-P0-028` and `DBX-P0-029`, and the twelfth dbt boundary review. I then walked every P0-P10 journey with focused checks for admission versus quiescence, the physical and derived fence states, lost Jobs responses, lease expiry, stopped-App recovery, cost and downtime, actor ownership, explicit reopening, collector-observed versus current trust, canonical-number teaching, and `UX-P0-F03`.

This report is outside the author hash scope. I edited no author file or earlier report. I made no Azure, Databricks, authentication, account-console, SQL, warehouse, App, Job, Unity Catalog, or dbt call.

## Current usability and accessibility evidence checked

- The normative [WCAG 2.2 Recommendation](https://www.w3.org/TR/WCAG22/) requires complete pages and processes to meet the applicable success criteria. In particular, status messages must be programmatically determinable without taking focus.
- The W3C [Understanding Status Messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html) guidance treats waiting, progress, results, and errors as status information and warns against needless focus interruption or overly chatty announcements. This supports the plan's append-only milestones, programmatic announcements, and no per-second countdown.
- The W3C [Understanding Focus Order](https://www.w3.org/WAI/WCAG22/Understanding/focus-order.html) guidance requires keyboard focus order to preserve meaning and operability. This supports presenting the current state, consequence, owner, and one next action in that reading order.
- The UK Government Service Manual's [testing with assistive technologies](https://www.gov.uk/service-manual/technology/testing-with-assistive-technologies) guidance calls for testing actual information access, understandability, and interface operation with screen readers, magnification, speech input, and representative users. The plan correctly requires manual assistive-technology and non-author task testing in addition to automation.

These sources do not prove a future implementation conforms. They support the scope and test method frozen in the plan.

## Executive verdict

Baseline 0.14 passes the P0 usability, onboarding, service-design, and accessibility contract. It replaces the unsafe mental model that “a new trust generation immediately locks actions” with a user-verifiable fence protocol:

1. A same-row claim commit admits at most one dbtobsb action.
2. A same-row drain commit blocks every later dbtobsb admission.
3. An action admitted earlier may still dispatch, queue, run, or have an unknown response.
4. Maintenance is safe only after terminal or definitive no-request reconciliation and the same fence reaches `CLOSED`.
5. Trust acceptance leaves controlled actions locked.
6. A matching verifier must perform a separate, confirmed reopen against the new accepted snapshot.

The UI and wrapper must expose those facts even when the App is stopped. They show whether a prior action may still run, current native compute and possible cost, the fixed cancel-or-wait policy, the responsible actor, the last confirmed server time, downtime, escalation, an append-only milestone history, and exactly one primary next action. No route offers force-open or asks the user for a fence version, action ID, native run ID, Jobs token, SQL, path, profile, or YAML.

The collector repair is also understandable. **Trust observed by collector** is an immutable observation-time fact on the AttemptKey root. **Current runtime trust** is a separate live query. The required three-step teaching example explicitly permits trust to change between the collector read and the evidence-row commit without changing dbt evidence or outcomes.

The decimal-string repair remains implementation detail in the correct place: the trust/fence reference and golden-vector contract. Ordinary tasks say that users never type or see this serialization. This avoids turning a cross-language integrity rule into an installer burden.

No new critical, high, medium, or low P0 usability finding is opened. `UX-P0-F03` remains a hard P3 release gate because the signed installer, concrete supported workstation matrix, and real one-/two-account interaction evidence still do not exist.

## Controlled-action state and recovery review

The following is the minimum safe projection already constrained by `product-plan.md:362-461`, `documentation-plan.md:86-94,253-272,304-305`, and the P6/P8 task gates. It is a review interpretation of the frozen contract, not a new state machine.

| Physical/control fact | Required user meaning | Required consequence and owner |
|---|---|---|
| `OPEN` with one fresh accepted bound snapshot | **Controlled actions available** | An authorized action user may prepare the one allowed action. |
| `ACTION_CLAIMED` before a drain | **One controlled action is active** | No second action is admitted. The App/action owner journals, dispatches, or reconciles the existing action. |
| Lost/indeterminate response after `DISPATCH_INTENT` | **Actions blocked — action outcome unknown** | The same stored request and token are reconciled; the user never supplies a token or run ID. Cost may still accrue. |
| Drain committed over an earlier claim, physical `DRAINING` | **New actions blocked — resolving one prior action** | Admission is blocked, but the prior request may still dispatch or run. The verifier/recovery owner follows the fixed cancel-or-wait path. Maintenance must not start. |
| Terminal/no-request proof plus release to `CLOSED` | **Actions locked — maintenance can proceed** | Controlled-action quiescence is proven. The named maintenance actor may perform only the planned trust/lifecycle operation. |
| `CLOSED` while maintenance/trust work is incomplete | **Actions locked — operation in progress** or **Actions locked — runtime trust must be revalidated** | The wrapper remains the durable status surface if App compute is stopped and exposes one safe resume/recovery action. |
| New accepted trust while the fence remains `CLOSED` | **Runtime trust accepted — actions remain locked** | Acceptance is not reopening. The matching verifier receives the separate reopen action. |
| Successful verifier-owned `CLOSED` to `OPEN` transition | **Controlled actions available** | The transition must bind the exact new generation, snapshot, and component and must be confirmed by readback. |
| `RETIRED` | **Controlled actions permanently unavailable** | There is no outgoing transition or force-open path. |

This projection avoids the most dangerous false success: `DRAINING` is not quiescence. It also prevents a timeout, lease expiry, accepted cancellation request, or stopped App from being presented as terminal evidence.

### Focused acceptance checks

| Check | Thirteenth-review outcome | Reason |
|---|---|---|
| Admission blocked versus maintenance-safe | `PASS` | The strict promise is repeated in the ADR, contributor contract, product plan, review gates, documentation page contract, usability tasks, and emergency wording. Only the `CLOSED` commit after reconciliation authorizes mutation. |
| Physical versus derived states | `PASS_AT_PLANNING_GATE` | Five physical states and seven action phases are closed, while plain-language states derive from physical state, phase, current trust, and lifecycle checkpoint. P6 must fixture every projection and ensure only one primary action renders. |
| Lost Run Now response | `PASS_AT_PLANNING_GATE` | `DISPATCH_INTENT` means the request may have reached Databricks. Recovery reuses only the stored deterministic token/body, keeps the fence occupied, exposes possible cost, and requires terminal/no-request proof. |
| Lease expiry | `PASS` | Expiry permits only reconciled takeover. It cannot release, close, reopen, prove quiescence, or stop cost by itself. Users are not given a force-open or “lease expired, continue” path. |
| Cancellation | `PASS` | Cancel acceptance is explicitly asynchronous. Only terminal Get Run evidence plus the terminal action-ledger fact supports release. A non-cancellable run is allowed to finish while the UI keeps cost and wait ownership visible. |
| Cost and downtime | `PASS_AT_PLANNING_GATE` | Every P6-aware task must show native compute, possible continuing cost, policy, deadline/escalation owner, read-only availability, and expected controlled-action downtime before confirmation. P8 measures wait, downtime, startup, polling, and cost separately from active-human time. |
| App stopped during recovery | `PASS_AT_PLANNING_GATE` | The signed wrapper remains the durable status surface and exposes the append-only milestone timeline, current fence/action/run facts, responsible actor, and one safe action while the App is unavailable. P8 explicitly kills the App/executor and tests this promise. |
| Actor responsibility | `PASS` | The App owns claim/journal/dispatch under its disclosed trusted authority. The verifier/trust committer owns drain, reconciled takeover, closed-before-mutation, and reopen. The action-role administrator owns enrollment/role changes through a separate fixed Job. Combined and separated human modes remain explicit. |
| Explicit reopen | `PASS` | Installation, refresh, upgrade, rollback, and P6 enablement keep the fence closed through acceptance. Only a separate matching-verifier transition against the fresh accepted pair reopens it. |
| No internal input or bypass | `PASS` | Display names and approved deep links are used. The workflow never asks for action/run/fence/deployment IDs, tokens, SQL, paths, profiles, checkpoints, capsules, flags, or YAML, and no force-open/continue-anyway control exists. |
| External-caller and compromised-root boundary | `PASS` | The text does not imply the fence blocks customer schedules/direct callers or resists App code/managers, the verifier, owners, or administrators. Customers needing that stronger property must keep P6 disabled. |

## Collector trust teaching review

The baseline now cleanly separates four questions:

| Question | Label/source | Must not imply |
|---|---|---|
| What happened in Lakeflow/dbt? | Native Job, invocation, node/test, collector, archive, and capture facts | Trust changes alter a native outcome. |
| What trust did the collector read for this AttemptKey root? | **Trust observed by collector** with snapshot, generation, state, and status-view query-evaluation time | Trust was still current when the evidence row committed. |
| What is trusted now? | **Current runtime trust** from the latest summary query | The historical collector stamp is rewritten or promoted. |
| When was the runtime graph/roster evidence observed? | Pre-start transition audit, post-start machine freshness, and original roster freshness | Any of those server query-start times is a Delta commit time or continuous verification. |

`product-plan.md:637-643` gives the honest race: the collector reads accepted snapshot N, trust changes, then the root write may commit with its earlier N observation. `documentation-plan.md:246,294,328` requires that timeline in task guidance and real evidence. The provenance tuple is excluded from AttemptKey, hashes, artifact validation, capture precedence, result resolution, and native outcomes. This resolves the user-facing portion of `DBX-P0-028` without rewriting historical evidence.

## Canonical decimal-string usability review

`DBX-P0-029` is resolved without imposing a new human task:

- The SQL data stays typed numeric and range-checked.
- Canonical trust/fence JSON uses quoted unsigned base-10 strings with exact lexical rules and cross-language boundary vectors.
- `documentation-plan.md:304` confines the representation detail to the trust/fence reference, explicitly says users never type these strings, and forbids ordinary workflows from exposing it.
- Contributor, platform, test, and reference contracts carry the detail; installer, operator, investigation, and lifecycle pages carry only the plain-language integrity result and recovery action.

This is the correct progressive-disclosure boundary. A future UI that asks a user to enter or compare one of these numeric strings would violate the frozen no-guess journey.

## Prior finding disposition

`RESOLVED` below means the P0 planning contract remains implementable and testable; it does not claim later-part code or live evidence exists.

| Finding | Thirteenth disposition |
|---|---|
| `UX-P0-001` through `UX-P0-003` | `RESOLVED — NO REGRESSION`; one signed entry, two explicit modes, and distinct readiness outcomes remain intact. |
| `UX-P0-004` | `RESOLVED_AT_CONTRACT`; WCAG 2.2 AA applies to complete pages/processes, with manual keyboard, screen-reader, zoom, reflow, status, error, and non-color testing. |
| `UX-P0-005` | `RESOLVED — NO REGRESSION`; each Operation/Problem surface exposes actor, mutation, temporary authority, compute, trust/deployment/fence state, and one safe action without raw platform detail. |
| `UX-P0-006` | `RESOLVED — NO REGRESSION`; every participant has a concrete start/end task and active time excludes platform wait while retaining human recovery/reopen work. |
| `UX-P0-F01` and `UX-P0-F02` | `RESOLVED_AT_CONTRACT`; cost/cleanup bounds and the four distinct lifecycle choices remain mandatory live evidence. |
| `UX-P0-007` through `UX-P0-013` | `RESOLVED — NO REGRESSION`; CLI scope, attended mutation chronology, two-account handoff, complete combined path, verifier-owned roster review, phase/time/source semantics, and actor-capability recovery remain coherent. |
| `UX-P0-F03` | `OPEN_NONBLOCKING_P0_HARD_P3_GATE`; no concrete installer asset or supported workstation claim exists yet. |
| `UX-P0-F04` through `UX-P0-F06` | `RESOLVED_AT_CONTRACT`; scoped inventories, severity gates, and immutable action/approval summaries remain present. |
| `DBX-P0-028` user-facing portion | `RESOLVED_FOR_P0`; the plan now states the exact admission and quiescence linearization points, earlier-action consequence, persistent recovery surface, cost, actor, and separate reopen. |
| `DBX-P0-029` user-facing portion | `RESOLVED_FOR_P0`; canonical numeric strings are reference/test machinery and never user input. |

### Remaining `UX-P0-F03` acceptance

P3 must publish and test before any installer/platform combination is described as supported:

- exact supported OS versions and architectures;
- signed wrapper/embedded-CLI asset names, signatures, checksums, and verification workflow;
- native secure-store backend, success/failure behavior, and non-mutating unsupported messages;
- one-account combined operation;
- two-account spool ACLs, atomicity, session release, restart/reboot, and removal;
- exact same-account-separated, separate-workstation, third-reviewer, and non-admin-verifier errors;
- real stage/final approvals, no-ID deployment reconciliation, drain/lost-response/stopped-App recovery, explicit reopen, and three-time/two-clock presentation;
- uninstall with no leftover capsule, credential, query, temporary grant, App/Job/test compute, or test-started warehouse.

This remains a P3 implementation and evidence gate, not a missing P0 safety control. Baseline 0.14 does not claim that a concrete installer/platform combination already works.

## Author-file outcome

| Author file or set | Outcome | Usability conclusion |
|---|---|---|
| `README.md` | `PASS` | The product principles now give the admission/drain/quiescence boundary, explicit reopen, collector/current-trust separation, and named-root limitation without overwhelming the entry point. |
| `AGENTS.md` | `PASS` | Contributor invariants prohibit false quiescence, auto-release/reopen, internal user input, commit-current trust language, and ordinary exposure of trust-number serialization. |
| `docs/index.md` | `PASS` | The planning index introduces no competing product journey. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | The decision explains why the fence exists, what it cannot guarantee, who acts, and why acceptance alone is not reopening. |
| `docs/plans/product-plan.md` | `PASS` | The physical protocol, derived labels, actor/cost/status requirements, stopped-App wrapper, collector timeline, and P0-P10 evidence are coherent and testable. |
| `docs/plans/review-process.md` | `PASS` | Every relevant part now reviews admission versus quiescence, same-token recovery, lease takeover, cost/downtime, explicit reopen, and no force-open. |
| `docs/plans/documentation-plan.md` | `PASS` | Dedicated how-to/reference/explanation routes teach drain, unknown dispatch, reopen, collector provenance, and canonical strings at the correct level of detail. |
| `docs/research/source-register.md` | `PASS` | Current primary platform and accessibility sources support honest statuses, idempotent recovery, per-table limits, programmatic status, and complete-process testing. |

## P0-P10 usability matrix

These outcomes assess planning adequacy, not implementation or live proof.

| Part | Thirteenth usability outcome | Required next evidence |
|---|---|---|
| P0 — Product contract | `PASS` | Record this immutable-hash verdict with the Databricks and dbt re-reviews. No P0 usability blocker remains. |
| P1 — Capture library | `PASS` | Implement safe actionable validation, immutable collector-trust types, decimal-string codec vectors, and zero raw diagnostic leakage. |
| P2 — Collector and reconciliation | `PASS` | Prove one immutable AttemptKey-root observation tuple, before/after-read barriers, indeterminate-root readback, stale continuation, and unchanged native/capture outcomes. |
| P3 — Bundle installer | `PASS_WITH_FOLLOW_UP` | Implement both modes, both App approvals, automatic no-ID deployment reconciliation, exact trust/fence DDL, stopped-wrapper recovery, explicit reopen, and the signed workstation matrix. Close `UX-P0-F03` before supported release. |
| P4 — App read-only MVP | `PASS_AT_PLANNING_GATE` | Render accessible setup-only, evidence, investigation, current/collector-trust, cost, recovery, and lifecycle states with one primary next action and no focus-stealing status updates. |
| P5 — Job onboarding | `PASS` | Prove five scanner outcomes, semantic-change preview, dbt-owner review, rollback, and no silent customer-Job mutation. |
| P6 — Controlled actions | `PASS_AT_PLANNING_GATE` | Fixture every physical-state/action-phase/current-trust/lifecycle projection; both claim/drain orders; lost response; asynchronous cancel; non-cancellable wait; lease takeover; App stop; exact actor; possible cost; terminal proof; explicit reopen/retire; and no ID/token/force-open path. |
| P7 — Security and operations | `PASS_WITH_FOLLOW_UP` | Publish and rehearse drain/recovery/reopen, refresh, upgrade/rollback, retained/deleted fence history, App/workstation restart, cost/downtime, and supported-platform runbooks. |
| P8 — Bounded live proof | `PASS_AT_PLANNING_GATE` | Exercise two SQL sessions and real bounded Jobs fault hooks in both human modes; prove one native run, closed-before-mutation, durable stopped-App status, no false cost cessation, explicit reopen, and zero active resource/temporary authority at exit. |
| P9 — Optional intelligence | `PASS` | Keep installation, capture, investigation, authorization, refresh, and lifecycle complete with AI disabled; AI never supplies a fence, action, trust, dbt, or deployment input. |
| P10 — Private alpha | `PASS_AT_PLANNING_GATE` | Non-author participants must distinguish admission blocked from maintenance safe, recover one lost response, explain lease/cancel limits, reopen without an ID, complete both install modes and lifecycle, and make zero safety-critical or false-success errors. |

## Final disposition

`PASS_WITH_FOLLOW_UP`.

Baseline 0.14 is a coherent and testable P0 service contract. It tells users exactly when new controlled actions are blocked, when one earlier action may still dispatch or run, when maintenance is actually safe, who owns recovery, whether cost can continue, what remains available while the App is stopped, and why trust acceptance still requires an explicit reopen. It keeps collector-observed trust separate from current trust and keeps canonical decimal strings out of ordinary workflows.

No new P0 usability finding remains. `UX-P0-F03` is still the correct hard P3 gate for the real signed installer, supported workstation claims, and observed one-/two-account interaction quality. No cloud resource was created, started, stopped, queried, changed, or deleted by this review.
