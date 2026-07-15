# Usability and service-design twelfth re-review: P0 planning baseline 0.13

- Reviewed input: frozen author-owned planning file set
- Frozen author-input SHA-256: `2bde12f3f3eef01efecef33f483015cbcf2588234281666ba192a6d7534c81c7`
- Hash scope: `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, globally sorted by path; SHA-256 of the path-ordered per-file SHA-256 records
- Date: 2026-07-15
- Reviewer: independent usability, onboarding, and service-design twelfth re-review
- Verdict: `PASS_WITH_FOLLOW_UP`
- Open P0 usability blockers: none
- Open non-blocking implementation follow-up: `UX-P0-F03`, hard P3 gate
- Cloud mutation: none

## Immutable input and method

I independently recomputed the aggregate before review and again immediately before completing this report. Both results were exactly:

```text
2bde12f3f3eef01efecef33f483015cbcf2588234281666ba192a6d7534c81c7
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

I read every author file and all three eleventh reports in full. I walked every P0-P10 journey with specific attention to `DBX-P0-025`, `DBX-P0-026`, `DBX-P0-027`, the unchanged-refresh path, the three trust times and two validity clocks, P6 expiry, and every previously recorded UX finding.

This report is outside the hash scope and is the only file written by this review. I did not edit an author file or prior report. I made no Azure, Databricks, authentication, account-console, SQL, warehouse, App, Job, Unity Catalog, or dbt call.

## Executive verdict

Baseline 0.13 passes P0 usability and service-design review. The more exact trust model remains operable and explainable:

- A candidate and acceptance now retain two distinct machine observations. The user sees a stopped-state transition audit before start and a separate active-state machine-freshness proof after start. The system allows only the expected `STOPPED` to `ACTIVE` transition while the deployment and stable graph remain identical.
- Reused roster evidence now points only to the original self-anchored roster event in a complete accepted, uninvalidated source generation. An intermediate refresh cannot move the roster clock. Later deletion, invalidation, conflict, or tamper in that source makes the dependent current generation unverified.
- The product no longer calls `current_timestamp()` a commit time. It accurately labels each server value as `statement_evaluated_at` at query-evaluation start.
- An unchanged refresh is a real re-observation, not a timestamp rewrite: inventory the existing deployment, stop it, prove a zero-sized deployment difference with byte-equal inventories, observe it stopped, restart that same deployment, observe it active, and accept again. It does not run code staging, create a deployment, or require an ID choice.

The user-facing mental model is now three evidence-time facts with only two validity clocks:

1. **Pre-start transition audit** — when the stopped graph was recorded. It proves the safe transition point but does not extend validity.
2. **Post-start machine freshness** — the machine-validity clock after the same deployment is active.
3. **Original roster freshness** — the roster-validity clock from the original eligible native review.

Expiry uses the earlier end of the post-start-machine and original-roster 24-hour windows. The UI also has a current server `evaluated_at` for calculating state; that value is not another evidence event and never resets either clock.

No new critical, high, medium, or low P0 usability finding is opened. `UX-P0-F03` remains appropriate as a hard P3 release gate because no signed installer asset, supported OS/architecture claim, or real two-account interaction exists yet.

## End-to-end journey review

| Journey | Twelfth-review outcome | User-facing conclusion |
|---|---|---|
| Combined personal install | `PASS` | One account-administrator actor uses one OS account and one confirmed U2M profile, acknowledges all false independence flags, performs recovery/data/composite/App/trust work without a capsule or handoff, and reaches the URL only after final acceptance. Same-account separated mode fails rather than silently changing mode. |
| Separated regulated install | `PASS` | Exactly one verifier administrator and one different UC operator use distinct managed OS accounts on one supported workstation. Each runs `dbtobsb bootstrap` and uses only their own profile, secure store, browser, and checkpoint. The signed spool is auto-discovered; no person copies a capsule, path, credential, or checkpoint. The returning verifier owns final data observation, both App approvals, machine observation, roster review, and trust acceptance. |
| Two sequential App approvals | `PASS` | Before mutation, a non-executable intent explains expected bindings, ACLs, principals, and cost. The first approval authorizes only the zero-product-authority stage. After staging, complete deployment reconciliation, and stop, the second approval authorizes a newly generated current-lineage final plan whose diff is limited to the disclosed bindings and ACLs. The user does not approve the same artifact twice. |
| Deployment reconciliation | `PASS` | The wrapper consumes every deployment page and active/pending pointer before and after one staging invocation. It discloses prior-code start and possible internal POST reissue, stops on every exit, and accepts only exactly one new successful terminal matching `SNAPSHOT`. Zero, multiple, pending, auto-sync, mismatched, or unexplained records fail closed. The user never chooses or enters a deployment ID. |
| Deployment failure recovery | `PASS_AT_PLANNING_GATE` | Each state reports the responsible actor, running compute, pending/new count, bindings, mutation/authority state, and exactly one action. Pending or incomplete state stays stopped and resumes reconciliation. Confirmed ambiguity invalidates the generation; the only continuation is a new generation, never selection of one deployment or repetition of the indeterminate invocation. P3 must render the promised single action literally. |
| Final-plan recovery | `PASS` | Review-required, intent-mismatch, stale-lineage, drift, process-loss, and partial-Apply states are distinct. Every route returns to recovery audit and a fresh plan; no UI offers a validation bypass or old-plan reuse. |
| Unchanged trust refresh | `PASS` | The verifier or combined administrator reruns `dbtobsb bootstrap` and receives one action, **Refresh runtime trust**. The wrapper stops and observes the already accepted deployment, proves `new_deployment_count=0` and byte-equal inventories, restarts the same deployment, and obtains the active observation before acceptance. There is no UC handoff, `bundle run`, new deployment, stage/final plan pair, or human ID choice. |
| Early roster reuse | `PASS` | Reuse retains the original self-anchor and its original time. It cannot point at an intermediate refresh candidate or move expiry. The view revalidates the complete source chain on every query; a broken source produces unverified state and P6 denial. A 24-hour renewal repeats the native review and creates a new self-anchor. |
| Trust states and presentation | `PASS` | Registered, candidate, accepted, stale, invalidated, code drift, authority drift, and unverified remain distinct. Candidate never unlocks. The App separates transition-audit time from the two validity inputs, shows both validity ages, oldest validity-component age, expiry, point-in-time/non-independent qualifier, current evaluation, and running state. Equal pre-start and roster values on a new self-anchor are valid and must not be presented as missing evidence. |
| Recovery and wrong actor | `PASS` | One actor-capability table still governs Query History locate/cancel, own-result access, UC reconstruction, exact revoke, final observation, and prohibited actions. Zero/multiple query matches do not let the warehouse manager choose one. Wrong actor, workspace, profile, mode, visibility, or source chain fails before mutation. |
| P6 expiry and source races | `PASS_AT_PLANNING_GATE` | Prepare, approve, and run re-read authorization without a cache. The run DML groups to exactly one current summary and requires the prepared installation/generation/snapshot, accepted state, `evaluated_at < valid_until`, and exactly one matching `CONTROLLED_ACTIONS` component. Expiry, a new registration, source-anchor invalidation, candidate, drift, conflict, null, duplicate, or unreadable view prevents DML before Job start. P6 implementation must test expiry between every phase and page-open-to-run races. |
| First evidence | `PASS` | Before acceptance the App is setup-only and exposes no trusted evidence, collection, or action. After acceptance, a packaged fixture precedes one explicit cost-confirmed one-model run. `Observable` requires the expected evidence row, so App readiness, Lakeflow result, dbt result, collector, archive, capture, and trust never collapse into one success label. |
| Upgrade and rollback | `PASS` | A new registration makes old trust non-current and locks P6. The App stops and final bindings are removed before prior code may briefly run with zero product authority. New code follows full baseline/invoke/stop/reconcile/fresh-plan/candidate/start/reobserve/accept. Compatibility and destructive-data limits remain visible. |
| Retain, delete, and uninstall | `PASS` | Uninstall first stops compute, reconciles deployments, and removes App bindings through a fresh approved plan. Retain/export is default and transfers both ledgers, the status view, product objects, and residual-authority disclosure. Irreversible deletion is separately approved and verified; foreign grants, actor-owned profiles, and the customer-owned schema are not removed by implication. |
| Cost and downtime | `PASS_AT_PLANNING_GATE` | Before the first billed stage, the user sees App size, DBU/hour, prior-code/stage/safe-boot intervals, maximum elapsed time, stop owner, warehouse exposure/auto-stop, and cleanup. Unchanged refresh has no staging deployment but does intentionally stop and restart the App; its page must disclose temporary availability impact, restart billing, running state, and stop owner before confirmation. Final inventory distinguishes product/test-owned, reused, and unrelated resources. |
| No-guess primary path | `PASS` | The primary journey uses display names, safe profile labels, native deep links, fixed wrapper actions, and auto-discovered state. No user writes or pastes SQL, internal Job/App/deployment IDs, paths, profile names, capsules, checkpoints, flags, selectors, YAML, or dbt command fragments. P6's copyable nonsecret request locator is a constrained workflow reference, not guessed platform state or an execution parameter. |

## Three times and two validity clocks

The revised labels are understandable when presented in this order:

| Display concept | Source | What it proves | Validity effect |
|---|---|---|---|
| Pre-start transition audit | Candidate `statement_evaluated_at` with `STOPPED` observation | The selected deployment and stable graph were inspected before start | Audit only; does not extend trust |
| Post-start machine freshness | Acceptance `statement_evaluated_at` with `ACTIVE` observation | The same deployment and stable graph were re-observed after start | Machine clock, 24 hours |
| Original roster freshness | Original self-anchored candidate `statement_evaluated_at` | The verifier completed the native service-principal roster comparison | Roster clock, 24 hours; unchanged reuse never moves it |
| Oldest validity-component age | Earlier of post-start machine and original roster times | Which validity input will expire first | Drives plain-language refresh urgency |
| Current evaluation | View query-start `evaluated_at` | When current state was calculated | No evidence or validity reset |

This corrects the eleventh usability report's shorthand that called the server values “commit times.” Baseline 0.13 now uses the accurate platform meaning. P4 must verify that readers can distinguish these labels, including the expected case where a newly self-anchored roster time equals the pre-start candidate time.

## Disposition of the eleventh Databricks findings

| Finding | Twelfth usability disposition |
|---|---|
| `DBX-P0-025` | `RESOLVED_FOR_P0`; phase-specific fields, lifecycle states, active/pending facts, stable-graph equality, predecessor chain, view output, and failure fixtures now make stopped versus active proof unambiguous. |
| `DBX-P0-026` | `RESOLVED_FOR_P0`; only the original self-anchored event from a complete accepted source chain may be reused, intermediate/transitive pointers are rejected, original expiry never moves, and source invalidation dynamically makes dependents unverified. |
| `DBX-P0-027` | `RESOLVED_FOR_P0`; exhaustive DDL, exact four-event matrix, literal canonical domains/dependency order, golden vectors, exact status-view output/reduction, same-statement P6 predicate, and accurate query-start time naming provide one implementable contract. |

The eleventh dbt verdict remains compatible with these repairs. The new phase, source-anchor, canonical-ID, and time fields stay a control/provenance layer and cannot become dbt argv, AttemptKey, artifact, log, node result, or capture-state evidence.

## Findings and follow-ups

No new numbered usability finding is opened.

`UX-P0-F03` remains `OPEN_NONBLOCKING_P0_HARD_P3_GATE`. P3 must publish and test:

- exact supported OS and architecture combinations;
- signed asset names, signatures, and checksum workflow;
- native secure-store behavior and explicit unsupported fallback;
- one-account combined behavior;
- two-account spool ACLs, atomicity, session release, restart, reboot, and removal;
- exact unsupported same-account, separate-workstation, third-reviewer, and non-admin-verifier messages;
- the real two-approval, one-action recovery, unchanged-refresh stop/start, and three-time/two-clock interaction;
- installer and workstation uninstall with no leftover capsule, credential, compute, or product-created temporary authority.

This follow-up belongs to P3, not P0. The planning contract intentionally does not claim that a concrete installer/platform combination already works.

## Prior UX finding disposition

`RESOLVED` means the planning contract is implementable and testable, not that later-part assets or live evidence already exist.

| Finding | Twelfth disposition |
|---|---|
| `UX-P0-001` | `RESOLVED — NO REGRESSION`; one signed wrapper, actor-owned authentication, durable Operations, and final URL handoff remain coherent. |
| `UX-P0-002` | `RESOLVED — NO REGRESSION`; one combined and one exactly-two-person separated topology are selected before mutation. |
| `UX-P0-003` | `RESOLVED — NO REGRESSION`; readiness, needs-changes, unsupported, access-blocked, and check-failed remain distinct. |
| `UX-P0-004` | `RESOLVED_AT_CONTRACT`; whole-process WCAG 2.2 AA and manual keyboard/screen-reader/zoom/reflow/error evidence remain mandatory before conformance is claimed. |
| `UX-P0-005` | `RESOLVED — NO REGRESSION`; Operation/Problem state reports actor, mutation, temporary authority, compute, trust/deployment state, and one action without raw platform details. |
| `UX-P0-006` | `RESOLVED`; each participant has an executable start and terminal task. Active-time measurement includes authentication, reading, comparison, both App approvals, roster review, confirmation, and recovery. |
| `UX-P0-F01` | `RESOLVED_AT_CONTRACT`; bounded App/warehouse cost, running state, stop owner, downtime, and final scoped inventory remain P8 evidence. |
| `UX-P0-F02` | `RESOLVED_AT_CONTRACT`; stop, remove configuration, retain/export, irreversible delete, and verification remain separate choices. |
| `UX-P0-007` | `RESOLVED — NO REGRESSION`; the CLI is exact, pinned, deployment-only, and absent from product runtime. |
| `UX-P0-F03` | `OPEN_NONBLOCKING_P0_HARD_P3_GATE`; concrete signed installer and supported workstation evidence remains absent and is not waived. |
| `UX-P0-F04` | `RESOLVED — NO REGRESSION`; before/after inventory distinguishes proof-owned, reused, and unrelated resources and restores only scoped changes. |
| `UX-P0-F05` | `RESOLVED — NO REGRESSION`; unresolved high or critical findings cannot be waived at a part gate. |
| `UX-P0-F06` | `RESOLVED_AT_CONTRACT`; controlled-action summaries, distinct production actors, same-person denial, cost/expiry consequences, and recovery remain explicit. |
| `UX-P0-008` | `RESOLVED — NO REGRESSION`; attended data mutation, pending row, exact revoke, reconstruction, and later composite observation retain one chronology. |
| `UX-P0-009` | `RESOLVED — NO REGRESSION`; separated mode has one two-account handoff/return and no third roster handoff. |
| `UX-P0-010` | `RESOLVED — NO REGRESSION`; combined mode remains a complete one-account route with truthful independence flags. |
| `UX-P0-011` | `RESOLVED — NO REGRESSION`; the verifier administrator owns roster review and unsupported reviewer topology fails before mutation. |
| `UX-P0-012` | `RESOLVED`; same-deployment acceptance now has exact stopped/active phase proof, unchanged refresh has zero deployment difference plus stop/start, roster reuse is non-extendable, and the UI has three accurate time facts with two validity clocks. |
| `UX-P0-013` | `RESOLVED — NO REGRESSION`; recovery surfaces still derive from one actor/capability/prohibition table. |

## Documentation-plan outcome

The documentation plan passes at P0.

- The Diataxis split remains sound: one controlled tutorial; outcome-oriented how-tos; neutral reference; mental-model explanations; and visibly separate optional/future routes.
- Production bootstrap preserves the exact two-mode, two-approval, deploy-reconcile-stop-fresh-plan-candidate-start-accept sequence.
- Dedicated pages now cover the trust schema/canonical identifiers, the three-time/two-validity-clock model, original roster self-anchor, unchanged-refresh zero-difference stop/start, ambiguous deployment recovery, and stale final-plan recovery.
- The writing rules prohibit commit-time language, distinguish transition audit from validity, keep deployment and trust events separate from dbt evidence, and require display names rather than internal IDs.
- D2, D5, and D6 require real phase, source-chain, refresh, P6, lifecycle, and recovery evidence. Real captures must include exact stopped/active observations, the original roster time, expiry, second approval, full deployment pages, failed-stop cost state, and no active resource left behind.
- FastAPI-style readability, Diataxis architecture, subject accuracy, security/privacy, usability/accessibility, rendered-site, and publication-safety passes remain independent.

The plan correctly treats these as future pages and evidence. `UX-P0-F03` prevents platform-support and installer-success claims until P3 proves them.

## Author-file outcome

| Author file or set | Outcome | Usability conclusion |
|---|---|---|
| `README.md` | `PASS` | The starting point and corrected three-time/zero-difference-refresh mental model are concise and accurate. |
| `AGENTS.md` | `PASS` | Contributor invariants preserve the zero-guess journeys and accurate trust labels. |
| `docs/index.md` | `PASS` | The planning index introduces no competing user route. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | Combined/separated actors, staged lifecycle, exact trust phases, source anchor, cost, and lifecycle consequences remain coherent. |
| `docs/plans/product-plan.md` | `PASS` | Every required user transition, failure state, trust/time concept, test gate, and no-guess constraint is implementable at the planning level. |
| `docs/plans/review-process.md` | `PASS` | P0-P10 usability focus now includes exact phase, source-anchor, three-time, P6, and refresh checks. |
| `docs/plans/documentation-plan.md` | `PASS` | Page routes, labels, captures, and separate review passes can teach the revised contract without procedure/reference conflation. |
| `docs/research/source-register.md` | `PASS` | Primary-source cautions now support accurate query-start time and lifecycle-free deployment inventory language. |

## P0-P10 usability matrix

These are planning outcomes, not claims that implementation or live evidence already exists.

| Part | Twelfth usability outcome | Required next evidence |
|---|---|---|
| P0 — Product contract | `PASS` | Record this immutable-hash verdict with the Databricks and dbt verdicts. No usability blocker remains in P0. |
| P1 — Capture library | `PASS` | Implement actionable allowlisted errors, exact component/status fixtures, and domain-separated trust-provenance types without exposing raw diagnostics. |
| P2 — Collector and reconciliation | `PASS` | Prove separate Job/dbt/collector/archive/capture outcomes, exact one-summary stamps, stale continuation, source-anchor failure denial, and exactly-once attempts across refresh generations. |
| P3 — Bundle installer | `PASS_WITH_FOLLOW_UP` | Implement both modes, both approvals, full no-ID deployment reconciliation, one-action failures, exact trust DDL/writer/view, unchanged zero-difference stop/start, three-time status, fresh planning, setup-only start, and same-deployment acceptance. Close `UX-P0-F03` before supported release. |
| P4 — App read-only MVP | `PASS_AT_PLANNING_GATE` | Build accessible setup-only, health, evidence, investigation, stale, recovery, cost, and lifecycle pages. Test comprehension of transition audit versus both validity clocks, including equal self-anchor/pre-start values and current evaluation. |
| P5 — Job onboarding | `PASS` | Prove the five scanner outcomes, semantic-change preview, dbt-owner review, rollback, and no silent customer-Job mutation. |
| P6 — Controlled actions | `PASS_AT_PLANNING_GATE` | Prove uncached prepare/approve/run, exact grouped current-summary predicate, both validity clocks, source invalidation and expiry races, same-person denial, immutable summaries, parameterless start, and safe recovery. |
| P7 — Security and operations | `PASS_WITH_FOLLOW_UP` | Publish and rehearse refresh, source-anchor failure, upgrade/rollback, App/workstation restart, cost/downtime, retain/export/delete/uninstall, and supported-platform runbooks. |
| P8 — Bounded live proof | `PASS_AT_PLANNING_GATE` | Exercise both modes; zero/one/multiple/pending deployments; internal reissue/prior-code start; stale plan; failed stop; phase swap/stable-graph drift; original-anchor invalidation; unchanged zero-difference refresh; page-open/P6 expiry; timing targets; first evidence; and zero-resource cleanup. |
| P9 — Optional intelligence | `PASS` | Keep installation, capture, investigation, refresh, and lifecycle complete with AI disabled; AI never supplies deployment, trust, authorization, migration, or dbt input. |
| P10 — Private alpha | `PASS_AT_PLANNING_GATE` | Non-author users must complete combined and separated installs, two approvals, no-ID recovery, first evidence, unchanged refresh, upgrade, retain/delete/uninstall, and timing targets without safety-critical error, guessed state, abandonment, or moderator takeover. |

## Final disposition

`PASS_WITH_FOLLOW_UP`.

Baseline 0.13 is a coherent, fail-closed P0 service design. The two install modes, sequential approvals, deployment reconciliation, unchanged-refresh stop/start, trust states, three accurate evidence-time facts, two validity clocks, source-anchor recovery, P6 expiry, cost, first evidence, upgrade, rollback, and uninstall all provide a deterministic next step without internal ID, SQL, path, profile-name, capsule, checkpoint, selector, flag, or YAML guesswork.

No P0 usability blocker or new finding remains. `UX-P0-F03` is still the correct hard P3 gate for the real signed installer, supported workstation claims, and observed interaction quality. No Azure or Databricks resource was created, started, stopped, queried, changed, or deleted by this review.
