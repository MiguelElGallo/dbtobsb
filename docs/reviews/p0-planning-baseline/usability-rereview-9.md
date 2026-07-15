# Usability and onboarding ninth re-review: P0 planning baseline 0.10

- Reviewed input: frozen author-owned planning file set; repository has no commit yet
- Frozen author-input SHA-256: `2fa25d8bef4e2499de9feb0541b405430599400059172e206b1ec7bf89f9a8a1`
- Hash scope: `README.md`, `AGENTS.md`, `docs/index.md`, and all Markdown files under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path; SHA-256 of the sorted per-file SHA-256 records
- Date: 2026-07-15
- Reviewer: independent usability, onboarding, and service-design ninth re-review
- Verdict: `CHANGES_REQUIRED`
- Cloud mutation: none

## Immutable input and method

I independently recomputed the author-input hash before review. It exactly matched the assigned digest. This report is outside that hash scope and is the only file written by this review.

I read the complete frozen author set and the prior review record, with particular attention to the eighth usability and Databricks reports. I walked both installer modes, each human role, every P0-P10 usability gate, the complete documentation plan, interruption recovery, first evidence, upgrade, rollback, retain/delete, uninstall, the new runtime-trust observation matrix, and the 24-hour expiry path. I did not edit an author-owned file or an earlier review report.

No Databricks or Azure authentication, API, CLI, workspace, compute, storage, identity, or resource operation was performed.

## Current authoritative guidance checked

- [Azure Databricks service-principal roles](https://learn.microsoft.com/en-us/azure/databricks/security/auth/access-control/service-principal-acl) gives the account-admin manual route as **Account console → User management → Service principals → service-principal name → Permissions**. The page shows the assigned principals and roles and provides search. This supports a display-name-driven attended comparison, but it does not itself define how dbtobsb hands a signed expected roster to a different human or records that person's product attestation.
- [WCAG 2.2 status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html) requires important status changes to be programmatically determinable without forcing focus. The plan's page-level observation time, age, qualifier, stale status, and action lock are appropriate; the final accepted snapshot still needs one unambiguous lifecycle.
- [GOV.UK usability benchmarking](https://www.gov.uk/service-manual/measuring-success/usability-benchmarking-a-website-or-whole-service) supports task completion, time, abandonment, ease, and confidence measures. The plan correctly makes its small private-alpha study formative rather than statistically generalizable, but each separately supported participant needs an executable task start and handoff.

## Ninth-pass persona and journey walkthroughs

| Persona or route | Result | Frozen-plan evidence and user consequence |
|---|---|---|
| Combined personal administrator | `PASS_WITH_REQUIRED_CLARIFICATION` | One eligible account administrator uses one OS account/profile, sees both independence flags as false, performs the native roster check personally, and emits no capsule/release/return state. A non-account-admin is explicitly unsupported. The final post-start trust acceptance and whether roster-review time is inside the 20-minute target still need one rule under `UX-P0-012`. |
| Separated deployment verifier plus UC operator, where the verifier is also the account reviewer | `PASS_WITH_REQUIRED_CLARIFICATION` | The two-account capsule/return choreography remains zero-guess and the deployment actor can perform both GA observation and manual account review. Final snapshot acceptance after App code/start and refresh initiation remain underspecified. |
| Separated install with a different enterprise account identity reviewer | `FAIL` | The human-role table explicitly allows a separate reviewer, but the executable branch defines only deployment and UC OS-account handoffs. There is no command, actor-owned state, signed nonsecret handoff, expected-roster delivery, approval record, or return transition for the third person. See `UX-P0-011`. |
| UC operator interrupted during a marked statement | `PASS_WITH_REQUIRED_FIX` | Query History, cancellation-as-nonterminal, exact revoke, terminal reconstruction, and manager escalation remain safe. The common numbered path says only a migration operator may recover, while the separated branch and repository rule authorize the seal verifier's disclosed `MANAGE` for exact recovery. See `UX-P0-013`. |
| Read-only operator with a fresh snapshot | `PASS` | Every evidence page must expose snapshot ID, observation time, age, scope, and `ADMIN_ATTESTED`, while still saying the evidence is point-in-time and named roots can change it afterward. Job, dbt, collector, and capture outcomes remain separate. |
| Read-only operator after 24 hours | `PASS` at state-contract level | Base collection can continue, but new and existing output is visibly `RUNTIME_TRUST_STALE` and unverified. The migration state is not rewritten. The exact human refresh journey is part of `UX-P0-012`. |
| P6 action initiator or approver | `PASS_WITH_REQUIRED_FIX` | A stale, unverified, or drifted snapshot locks actions, and the immutable action summary remains complete. A user cannot regain actions until the attended two-evidence refresh is executable under `UX-P0-011` and `UX-P0-012`. |
| Warehouse privacy and recovery approver | `PASS` | Direct group `CAN_MONITOR`, complete query/user visibility, and the workspace-admin verifier's effective `CAN_MANAGE` are now consistently separate. The plan states that the verifier can stop, edit, delete, and change ACLs; the separately named manager is the procedural escalation owner, not the only technical manager. |
| Governance reviewer assessing group authority | `PASS` | Every granted group is visibly a customer-governed trusted root. `SHOW GROUPS WITH USER`/`WITH GROUP` is limited to named migration actors/groups and is not mislabeled as complete member enumeration or continuous drift detection. |
| Cost-conscious personal tester | `PASS` | Schedules start paused, App start is explicit, the installer warehouse uses the lowest supported auto-stop, failed readiness stops App compute by default, and every live proof requires a bounded budget plus a scoped final inventory. No live resource is used by this review. |

## What baseline 0.10 resolves well

The two Databricks findings that drove this revision are understandable from the user's perspective:

- Runtime trust is now a mixed-evidence, point-in-time result. Machine-observed GA fields and the account-admin-attested service-principal roster are visibly different evidence classes.
- `RUNTIME_TRUST_ACCEPTED_ADMIN_ATTESTED`, `RUNTIME_TRUST_STALE`, `RUNTIME_CODE_OR_CONFIG_DRIFT`, `RUNTIME_AUTHORITY_DRIFT`, and `RUNTIME_TRUST_UNVERIFIED` have distinct meanings and consequences. The plan never calls the result continuous verification.
- Low-privilege writers stamp the last snapshot and age rather than pretending to inspect the complete graph.
- The 24-hour threshold is a clear policy: stale evidence remains queryable but unverified, enrichment degrades, and controlled actions lock.
- A personal combined route is supported only when the one accountable person is an account administrator. The plan does not silently weaken or skip the manual roster review.
- Direct versus effective warehouse authority, exact direct-grant removal versus current DML, and current access versus self-grant capability are all exposed as separate facts.

The remaining problems are not requests for more warning prose. They are missing or contradictory executable human transitions in a product whose zero-guess contract forbids improvised transfer.

## Findings

### `UX-P0-011`: make the separate account-identity-reviewer handoff executable

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: `docs/plans/product-plan.md`, **Runtime-trust observation contract**, **Human role and prerequisite model**, **Bootstrap the product**, common runtime step 11, P3/P6/P7/P8/P10, and **Usability validation**; `docs/plans/documentation-plan.md`, account-roster and refresh routes; `AGENTS.md`, immutable installer topology
- Evidence:
  1. The human-role table says the account identity reviewer may be “a separate enterprise reviewer,” and the usability gate assigns that person an independent non-author task.
  2. The canonical separated journey defines exactly two managed OS accounts and a signed capsule only between the deployment/seal-verifier and UC operator. The deployment account owns the runtime plan, expected roster, and protected state.
  3. Common runtime step 11 says the account reviewer opens every native Permissions page, compares the signed expected roster, and approves `SP_ROLE_ROSTER_ADMIN_ATTESTED`, but it does not say what this third person runs, how they receive the exact signed roster, how the decision is bound to installation/workspace/plan without entering an ID, or how control returns.
  4. The product forbids file, chat, screen-sharing, profile, checkpoint, path, ID, screenshot, and ad hoc state transfer. Those good prohibitions remove the obvious improvised workarounds.
  5. The account-console documentation provides a manual display-name/Permissions route, but the native page does not create a dbtobsb-signed attestation. Product choreography is therefore still required.
- User/system impact: a valid enterprise customer whose account administrator is not the deployment operator reaches a safety-critical dead end after runtime Apply. The team must either share prohibited state/screen content, give the deployment actor a new account-admin role, invent an unreviewed approval channel, or remain unable to start the App. An implementation can also record an administrator-attested result without proving which reviewer saw which expected roster.
- Required change and acceptance:
  1. Choose and freeze the supported v1 topology. Either require the deployment/seal-verifier actor also to be the account identity reviewer, or define a third-actor route with its own authenticated start, actor-owned session/state, nonsecret digest-bound handoff, and explicit return. Do not leave both possibilities implied.
  2. If a separate reviewer remains supported, give that person one exact first action. It may reuse `dbtobsb bootstrap` only if the product defines discovery, signature, installation/workspace binding, expiry/replay behavior, and least-privilege access for this role. The reviewer must not receive another actor's profile, checkpoint, plan file, path, token, or screen.
  3. Present each runtime service principal by a safe display name and an approved native navigation/deep-link route, with the expected principal/role set, group-root qualifier, progress, and one compare/approve-or-block decision. No internal ID, YAML, screenshot, or copied raw identity is a user input or durable receipt.
  4. Define durable states such as `SP_ROLE_REVIEW_REQUIRED`, `SP_ROLE_REVIEW_ACTIVE`, `SP_ROLE_ROSTER_ADMIN_ATTESTED`, `BLOCKED_SP_ROLE_VISIBILITY`, and `SP_ROLE_REVIEW_RETURN_REQUIRED`, including wrong actor/account/workspace, denial, unexpected assignment, browser/session loss, expiry, abandonment, and resume.
  5. Bind the administrator-attested digest to the exact expected roster, runtime plan/trust manifest, service-principal set, installation/workspace, account context, reviewer fingerprint, observation time, and expiry. A changed plan, principal set, or roster invalidates the decision before App start.
  6. Prove one separated install with a genuinely different account reviewer and one where an explicitly supported dual-role deployment reviewer performs both tasks. If v1 selects only the dual-role option, the readiness matrix, role table, documentation, and private-alpha participants must say so consistently.

### `UX-P0-012`: close the final-snapshot, post-start, and refresh lifecycle

- Classification: `CHANGES_REQUIRED`
- Severity: medium
- Affected contract: `docs/plans/product-plan.md`, runtime-trust lines 148-162, resumable stages, common runtime step 11, operation codes, staging, usability timing, and P4/P6/P7/P8; `docs/plans/documentation-plan.md`, roster review, refresh, drift/expiry, evidence badges, and D2/D5/D6
- Evidence:
  1. The required observation runs after runtime Apply and before App start. Common runtime step 11 accepts a matching snapshot and then runs `bundle run`, which deploys App code and starts compute.
  2. That same step says it recomputes the composite tuple and GA-visible observation after `bundle run`, but the stage list has no post-start observation/acceptance state and does not say whether the still-valid roster attestation is rebound or the account reviewer must act again.
  3. The App must show one accepted snapshot ID/time/age/scope/qualifier on every evidence page. Without a final post-code-deploy acceptance transition, the first App page can inherit a pre-deployment snapshot, show unverified state without a recovery action, or claim acceptance before the post-start observation is accepted.
  4. The documentation plan names a refresh how-to, and staging says a refresh returns to accepted state, but the product journey does not identify the initiating command/UI action, the two required actors, handoff/resume behavior, or the terminal operation that updates the badge.
  5. Usability validation says account-review time is measured separately while also requiring the combined actor to reach App readiness within 20 active minutes. The two statements do not unambiguously say whether the same person's roster work counts toward that target.
- User/system impact: immediately after install, after a runtime change, or at 24-hour expiry, operators can see a stale/unverified badge without knowing which human acts next or when trust is restored. More seriously, an implementation could show `RUNTIME_TRUST_ACCEPTED_ADMIN_ATTESTED` for an App code deployment not covered by the accepted machine observation. Controlled actions remain safely locked, but support burden and false confidence remain high.
- Required change and acceptance:
  1. Freeze one lifecycle from Apply through code/start: pre-start observation, roster review, provisional acceptance if needed, `APP_CODE_START`, post-start GA observation, final combination with a still-matching roster attestation, `RUNTIME_TRUST_ACCEPT`, readiness, and URL. If the post-start machine observation fails, the default is stopped App compute and one safe recovery action.
  2. State exactly when an unchanged roster attestation can be reused and rebound versus when the account reviewer must repeat the native comparison. Any plan, service-principal, expected-roster, installation/account, or 24-hour mismatch fails closed.
  3. Add the missing resumable Operation stages and make the first App page consume only the final accepted snapshot. Every transition exposes observation time, age, scope, machine-observed fields, admin-attested fields, expiry, running-compute state, and next actor without a focus jump or per-second countdown.
  4. Define one exact refresh entry action for install, upgrade, rollback, identity/ACL/grant/configuration change, manual recovery, and 24-hour expiry. It must reuse the supported account-review choreography from `UX-P0-011`, leave base read-only evidence available as unverified, and keep P6 locked until final acceptance.
  5. Test expiry while a page is open, expiry between prepare/approve/run, browser/session loss during roster review, post-start code/config drift, unchanged-roster reuse, changed roster, denied review, failed post-start observation, App stop, and successful refresh. The badge and Operation must never imply that a post-observation change was already detected.
  6. Make the timing denominator explicit: say whether combined-mode account-roster work is inside or outside the 20-minute active-actor target and use the same rule in the ADR, product plan, documentation plan, and participant evidence.

### `UX-P0-013`: use one recovery-actor rule in every installer view

- Classification: `CHANGES_REQUIRED`
- Severity: medium
- Affected contract: `docs/plans/product-plan.md`, common path step 2 and separated-duties step 8; `AGENTS.md`, exact-recovery rule; account/role/error documentation
- Evidence: common path step 2 says only an eligible migration operator follows Query History recovery and exact revoke. Separated step 8 and `AGENTS.md` explicitly allow the deployment/seal verifier to locate/cancel, reconstruct state, and use disclosed object-scoped `MANAGE` for the exact signed revoke when the UC actor is lost. The human-role table also assigns that recovery to the verifier.
- User/system impact: at the highest-risk interruption, the same verifier can be shown both “not the required actor” and “the approved recovery actor.” An operator may wait unnecessarily for an unavailable UC actor, over-escalate, or improvise around the wrapper even though a bounded recovery path exists.
- Required change and acceptance:
  1. Replace the conflicting prose with one decision table for original UC operator, replacement migration operator, deployment/seal verifier, and procedural warehouse manager.
  2. For each actor, separate native Query History visibility/cancel, Statement Execution result retrieval, UC post-state reconstruction, exact revoke authority, independent final observation, and prohibited mutation.
  3. The Operation's `required_actor_role`, error copy, deep link, and next action must derive from that same table. A verifier using `MANAGE` remains a disclosed trusted root and does not become the ordinary data-plan operator.
  4. Test original-actor loss, wrong actor, each approved replacement, manager escalation, and return to independent observation without broad revoke or mode change.

No additional critical, high, medium, or low planning finding was identified.

## Prior finding dispositions

`RESOLVED` means the planning contract remains complete enough to implement and test; it does not pre-approve P1-P10 implementation or live evidence.

| Finding | Ninth disposition |
|---|---|
| `UX-P0-001` | `RESOLVED` — one signed wrapper/command, explicit actor-owned profile, resumable stages, App start, and URL handoff remain intact. |
| `UX-P0-002` | `REOPENED_IN_PART_AS_UX-P0-011` — the original role/prerequisite matrix remains strong, but the new separately supported account-reviewer role has no executable handoff. |
| `UX-P0-003` | `RESOLVED` — scanner outcomes remain distinct and safely gated. |
| `UX-P0-004` | `RESOLVED` at contract level — complete-process WCAG 2.2 AA evidence remains mandatory. |
| `UX-P0-005` | `RESOLVED_WITH_FOCUSED_CORRECTION` — the Operation/Problem contract remains sound; new trust-review stages and one recovery-actor rule are required by `UX-P0-011` through `UX-P0-013`. |
| `UX-P0-006` | `REOPENED_IN_PART_AS_UX-P0-011_AND_012` — the measures remain appropriate, but the separate account-review task lacks an executable start/handoff and the combined timing denominator is ambiguous. |
| `UX-P0-F01` | `RESOLVED` at contract level — live-proof budget and final inventory remain P8 evidence. |
| `UX-P0-F02` | `RESOLVED` at contract level — stop, remove, retain/export, and irreversible delete/verify remain separate. |
| `UX-P0-007` | `RESOLVED` — CLI `1.7.0` remains exact, pinned, GA, and deployment-only. |
| `UX-P0-F03` | `OPEN`, non-blocking for P0 and still a hard P3 release gate — publish and test the exact OS/architecture, signed assets and verification, native secure-store combination, two-account spool/ACL/session-release behavior, one-account combined behavior, restart/reboot resume, uninstall, and explicit unsupported-platform/topology errors before claiming support. It cannot absorb the new P0 actor/lifecycle findings. |
| `UX-P0-F04` | `RESOLVED` — scoped before/after inventory preserves reused and unrelated resources. |
| `UX-P0-F05` | `RESOLVED` — normative gates consistently prohibit unresolved high or critical findings. |
| `UX-P0-F06` | `RESOLVED` at contract level — controlled-action summaries and same-person denial remain explicit. |
| `UX-P0-008` | `RESOLVED` — the attended fixed-data chronology and cleanup-first restart remain coherent. |
| `UX-P0-009` | `RESOLVED` for the deployment/UC two-account handoff; it does not define the newly added account-reviewer handoff. |
| `UX-P0-010` | `RESOLVED` — combined mode remains a complete one-actor route when that actor is an account administrator. |

`UX-P0-F03` can and should remain a P3 hard implementation gate rather than a P0 blocker. No installer asset or supported platform claim exists yet, and the planning contract already fails closed when secure storage/topology is unsupported. By contrast, `UX-P0-011` through `UX-P0-013` concern the advertised product journey and must be resolved in P0.

## P0-P10 outcomes

| Part | Ninth usability outcome | Reason |
|---|---|---|
| P0 — Product contract | `CHANGES_REQUIRED` | The new manual roster evidence is honest, but the separate reviewer, final accepted snapshot, refresh, and recovery-actor transitions are not yet one executable contract. |
| P1 — Capture library | `PASS` | Capture validation remains deterministic, fail-closed, local, and capable of returning safe actionable states. |
| P2 — Collector and reconciliation | `PASS` | Job, dbt, collector, archive, and capture outcomes remain separate; writers truthfully stamp the last trust snapshot instead of claiming live observation. |
| P3 — Bundle installer | `CHANGES_REQUIRED` | Resolve all three new findings, then retain `UX-P0-F03` as the release gate for each concrete platform combination. |
| P4 — App read-only MVP | `CHANGES_REQUIRED` | Page-level badges and stale behavior are well specified, but first-page trust depends on the missing final post-start acceptance transition. |
| P5 — Job onboarding | `PASS` | Five scanner outcomes, semantic-change preview, dbt-owner review, and rollback remain distinct; no customer Job is silently mutated. |
| P6 — Controlled actions | `CHANGES_REQUIRED` | Stale/unverified/drifted trust correctly locks actions, but the account-review handoff and refresh needed to unlock them are incomplete. |
| P7 — Security and operations | `CHANGES_REQUIRED` | Runbooks need the exact account-reviewer handoff, final snapshot/refresh lifecycle, and one recovery-actor decision table. Direct/effective authority and lifecycle choices otherwise pass. |
| P8 — Bounded live proof | `CHANGES_REQUIRED` | Add a genuinely separate account reviewer, post-start acceptance, expiry/refresh, denied/abandoned review, and consistent replacement-actor tests to the otherwise strong cost/race/cleanup suite. |
| P9 — Optional intelligence | `PASS` | AI remains optional, advisory, read-only where applicable, and outside authorization, capture, validation, and required operation. |
| P10 — Private alpha | `CHANGES_REQUIRED` | The combined route remains measurable, but an advertised separated enterprise route cannot yet complete when account review belongs to a third person. |

## Documentation-plan usability outcome

The information architecture is strong: it gives account-roster review, trust refresh, and drift/expiry their own how-to pages; preserves machine-observed versus administrator-attested reference material; and plans visible time, age, scope, stale status, direct/effective authority, whole-group roots, and sanitized real evidence.

Documentation cannot repair a missing product transition. D0/D2/D5/D6 must not write the separate-reviewer or refresh procedures until `UX-P0-011` and `UX-P0-012` freeze the executable task. After resolution, the documentation usability reviewer should test search-to-task routing for `trust stale`, `admin attested`, `service principal permissions`, `review blocked`, `refresh trust`, and `who acts next`, including a different account reviewer and the combined dual-role administrator.

## Final verdict

`CHANGES_REQUIRED`.

Baseline 0.10 substantially improves truthfulness: group principals are roots rather than silently “enumerated,” the workspace-admin verifier's effective warehouse authority is explicit, service-principal custody is administrator-attested rather than mislabeled machine verification, snapshot age is visible, and stale output/actions fail safely.

The planning baseline is not yet zero-guess for the new human evidence source. A separate enterprise account reviewer has no supported handoff or return; the final post-App-start accepted snapshot and later refresh do not have a complete Operation lifecycle; and the recovery actor is contradictory in two user-facing steps. Resolve those transitions and request another full usability re-review. `UX-P0-F03` remains the sole appropriate non-blocking P3 implementation follow-up.

No Azure or Databricks resource was created, started, stopped, changed, or deleted by this review.
