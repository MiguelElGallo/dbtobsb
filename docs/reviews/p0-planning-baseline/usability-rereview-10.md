# Usability and service-design tenth re-review: P0 planning baseline 0.11

- Reviewed input: frozen author-owned planning file set
- Frozen author-input SHA-256: `4c033d3a47ebd9c11b695177d1e166986af5c74d404ded76cfed828c088d8073`
- Hash scope: `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, globally sorted by path; SHA-256 of the sorted per-file SHA-256 records
- Date: 2026-07-15
- Reviewer: independent usability, onboarding, and service-design tenth re-review
- Verdict: `PASS_WITH_FOLLOW_UP`
- Open P0 usability blockers: none
- Cloud mutation: none

## Immutable input and review method

I independently recomputed the assigned author-input digest before reviewing. It was exactly:

```text
4c033d3a47ebd9c11b695177d1e166986af5c74d404ded76cfed828c088d8073
```

I read the complete frozen author set and all three ninth specialist reports. I then walked every P0-P10 journey and re-tested the user consequences of all prior UX findings, with focused checks for `UX-P0-011`, `UX-P0-012`, `UX-P0-013`, and the still-open implementation follow-up `UX-P0-F03`. I also checked the baseline 0.11 response to the ninth Databricks findings: the two-plan App lifecycle and the durable runtime-trust ledger/view.

This report is outside the frozen hash scope and is the only file written by this review. I did not change an author file or an earlier review. I made no Azure, Databricks, authentication, account-console, SQL, warehouse, App, Job, Unity Catalog, or dbt call.

## Executive verdict

Baseline 0.11 passes P0 usability and service-design review. The three ninth-pass P0 findings are resolved without weakening the zero-guess or fail-closed contract:

- `UX-P0-011` is resolved by choosing one supportable v1 topology instead of implying a missing third-person handoff. Separated mode has exactly two Databricks actors: an account-and-workspace-admin verifier, who also owns the native service-principal-roster task, and a different UC operator. A third identity reviewer and a non-account-admin verifier are rejected before mutation or compute. Combined mode has one account-admin actor and records every independence flag as false.
- `UX-P0-012` is resolved by one executable stage/deploy/stop/bind/candidate/direct-start/post-observe/accept lifecycle, a setup-only App before acceptance, one explicit refresh entry action, bounded roster-attestation reuse, two separately visible evidence clocks, oldest-component age, and one timing denominator that includes active roster work.
- `UX-P0-013` is resolved by one recovery decision table. The Operation `required_actor_role`, native deep link, permitted cleanup, and prohibited actions derive from the same actor row.

The ninth Databricks blockers are also closed from the user's perspective. The actual `SNAPSHOT` deployment is created once, stopped, bound, reviewed, restarted without a code deployment, and accepted only after same-ID post-start observation. Runtime trust is durable in a named customer-security-owned Delta event ledger with a sanitized current-status view; the App and bounded writers can read but cannot promote it.

No new critical, high, medium, or low P0 usability finding is opened. `UX-P0-F03` remains deliberately open as a hard P3 release gate. It is not waived, absorbed into prose, or treated as completed implementation. That future evidence is why this verdict is `PASS_WITH_FOLLOW_UP` rather than an unqualified implementation pass.

## End-to-end journey walkthroughs

| Journey | Tenth-review outcome | User-facing reason |
|---|---|---|
| Combined personal bootstrap | `PASS` | One account administrator runs `dbtobsb bootstrap` in one actor-owned OS account/profile, acknowledges that independent human, data-observer, and SP-role-review controls are absent, sees all flags as false, performs the fixed data path and native roster task, and reaches the URL only after final same-deployment acceptance. No capsule, release, return, copied profile, or handoff state is emitted. |
| Separated regulated bootstrap | `PASS` | Preflight requires the verifier administrator and a different UC operator in distinct managed OS accounts on one supported workstation. The system-owned spool carries only an auto-discovered signed nonsecret capsule. The UC actor owns data mutation and exact revoke; the returning verifier owns later data observation, App stage/stop/bind, GA observation, native roster comparison, trust commit, and accept-or-stop decision. A third identity reviewer fails before mutation as `UNSUPPORTED_ACCOUNT_REVIEW_TOPOLOGY`. |
| Actor-owned native roster task | `PASS` | The verifier performs the review inside the same returning bootstrap invocation and their own account-admin browser session. The wrapper presents one safe display name, expected role set, and group-root qualifier at a time; the only decisions are **Matches exactly** or **Block**. Browser loss returns to `SP_ROLE_REVIEW_REQUIRED`; denial or mismatch blocks. No raw identity, screenshot, internal ID, or copied roster is the handoff or receipt. |
| Normal interruption and recovery | `PASS` | Recovery audit always precedes resume. The original UC operator may use their own result and complete exact cleanup; a registered replacement may locate/cancel, reconstruct after eligibility, and revoke only the recorded pair; the verifier may do the same through disclosed `MANAGE` and later perform final observation; the warehouse manager may use the native UI for the unique deep-linked query but cannot select among ambiguous queries or mutate UC. No route permits blind retry or broad revoke. |
| Trust refresh | `PASS` | The verifier or combined administrator reruns `dbtobsb bootstrap`; after recovery audit the checkpoint offers **Refresh runtime trust**. An unchanged refresh needs no UC handoff. Early reuse of the same unexpired roster evidence cannot extend its expiry; a 24-hour renewal repeats the native comparison. Changed scope, manifest, service-principal set, expected roster, deployment, or reviewer fingerprint requires new evidence, while code/config/binding changes re-enter the stopped staged lifecycle. |
| Upgrade and rollback | `PASS` | A new manifest generation immediately makes the previous snapshot non-current and locks P6. The App stops and final bindings are removed before new or rolled-back code is staged with zero product authority. The exact new deployment is stopped, bound, made a candidate, started directly, reobserved, and accepted. Old acceptance cannot authorize the new deployment. |
| P6 expiry races | `PASS_AT_PLANNING_GATE` | Authorization is read without a cache at prepare, approve, and run. The run stage revalidates actor, device, epoch, role/scope, expiry, revision, revocation, approval digest, distinct actors, and every binding. Its conditional data operation requires a matching accepted ledger row whose machine and roster components are both fresh; candidate, stale, drift, conflict, or a new manifest generation locks the action before Job start. Expiry between prepare and approve or between approve and run therefore fails closed and requires a new prepare or trust refresh. The P6 and P8 gates still require explicit expiry-during-action implementation tests; this review does not pre-approve those future results. |
| First evidence | `PASS` | The App stays setup-only before `SNAPSHOT_ACCEPTED` and exposes no trusted evidence, collection, or controlled action. After acceptance, setup health runs a packaged fixture and offers one explicit cost-confirmed one-model dbt run. The installation becomes `Observable` only after the App queries the expected evidence row. Job, dbt, collector, archive, capture, and trust outcomes remain distinct. |
| App lifecycle and failure states | `PASS` | The stage plan has no product data, warehouse, Job, secret, Volume, or user access. Exactly one `bundle run <app-key>` creates the real deployment. The wrapper captures the deployment facts, explicitly stops it, proves no authority, applies final bindings while stopped, appends only a candidate, then uses only `databricks apps start <name>` to start the last deployment. A mismatch or ambiguous trust commit remains unverified and stops by default. A failed stop is visibly `APP_STOP_FAILED_RUNNING_UNVERIFIED`, not success. |
| Stale and setup-only read paths | `PASS` | Every relevant Operation or App surface shows machine-evidence time, roster-evidence time, oldest-component time/age, expiry, qualifier, and running-compute state. Existing and new base evidence can remain readable but is visibly unverified after expiry; collection may continue with a stale stamp. P6 stays locked. Acceptance time never refreshes an older component clock. |
| Personal cost control | `PASS` | Before the first billed App deployment, the user sees App size, DBU/hour, maximum stage and safe-boot intervals, stop owner, warehouse budget/auto-stop, and the fact that failed readiness stops App compute by default. A failed stop exposes running/unverified state and an accountable owner. Staging ends with a scoped inventory and no test-started App, Job, query, warehouse, or temporary grant left running. |
| Retain, export, delete, and uninstall | `PASS` | Stop and binding removal precede data changes. Retain/export is the default and transfers product objects, both control histories, the status view, and residual-authority disclosure to a named customer owner. Irreversible deletion is a separate attended plan with trust-ledger export and verification. Foreign grants and the customer-owned schema are not removed by implication. |

The non-author workstation administrator remains a support participant who verifies assets and provisions/removes the two-account local handoff component without Databricks access. The runtime control topology and `human_actor_count` refer to the one or two Databricks actors who execute or attest product operations; the P3 platform/topology evidence under `UX-P0-F03` must prove that boundary in the concrete installer.

## Focused resolution of the ninth findings

### `UX-P0-011`: resolved

Baseline 0.11 makes a product decision rather than adding another warning. A separate enterprise identity reviewer is unsupported in v1. The same verifier must be both account administrator and workspace administrator, and preflight rejects a third-reviewer request or a non-account-admin verifier before mutation or compute. That rule is consistent in the README, repository invariants, ADR, product plan, readiness matrix, documentation routes, staging tests, usability participant tasks, and P10 gate.

The supported roster task is actor-owned and executable: it starts from the verifier's existing `dbtobsb bootstrap` invocation, uses the verifier's own account-console session, displays one safe comparison at a time, retains no screenshot/raw identity, and has explicit required/active/attested/blocked/resume states. The plan no longer needs an undefined cross-person roster transfer or return path.

### `UX-P0-012`: resolved

The final accepted snapshot now has one lifecycle and one durable authority source:

1. Register a manifest generation, making old trust non-current.
2. Apply a zero-authority/no-user-access stage plan.
3. Run exactly one code-deploying `bundle run` to create the actual `SNAPSHOT` deployment.
4. Capture its ID/artifact/configuration, stop it explicitly, and prove no authority.
5. Apply byte-identical final bindings while stopped.
6. Complete pre-start GA observation and the verifier-owned native roster review.
7. Append `TRUST_CANDIDATE`, which unlocks nothing.
8. Recheck the last deployment and use direct `apps start`, with no code deployment.
9. Keep the running App setup-only while trust is absent.
10. Reobserve after `ACTIVE`, prove the same deployment and all bindings/ACLs/grants/roster, and append one atomic `SNAPSHOT_ACCEPTED`.
11. Only then show the App URL and accepted status.

The refresh path now has an initiating command, actor, next-action label, reuse limits, expiry behavior, change routing, durable event generation, and terminal user-visible status. Combined active time is at most 20 minutes including roster work; separated active time is at most 15 minutes per Databricks actor with roster work in the verifier's denominator; unchanged refresh is at most 10 active verifier minutes. Automated polling, App/warehouse startup, platform wait, and handoff wait are measured separately.

### `UX-P0-013`: resolved

One normative table now separates, for each recovery actor, Query History locate/cancel, own-result access, UC reconstruction, exact revoke, final separated observation, and prohibited work. The common numbered path matches it. The Operation's `required_actor_role`, error copy, native deep link, and tests derive from that table. Zero or multiple marker matches remain blocked and never let a warehouse manager pick an operation.

## Prior UX finding disposition

`RESOLVED` below means the frozen planning contract is implementable and testable; it does not claim that P1-P10 assets or live evidence already exist.

| Finding | Tenth disposition |
|---|---|
| `UX-P0-001` | `RESOLVED — NO REGRESSION`; one signed wrapper, explicit actor-owned authentication, stable Operations, and final App URL handoff remain coherent. |
| `UX-P0-002` | `RESOLVED`; the role/prerequisite model now selects exactly one supported separated topology, rejects a third reviewer/non-admin verifier before mutation, and preserves the complete combined route. |
| `UX-P0-003` | `RESOLVED — NO REGRESSION`; `READY`, `NEEDS_CHANGES`, `UNSUPPORTED`, `ACCESS_BLOCKED`, and `CHECK_FAILED` remain distinct and safely gated. |
| `UX-P0-004` | `RESOLVED_AT_CONTRACT`; whole-process WCAG 2.2 AA, keyboard, screen-reader, zoom/reflow, status, and error evidence remain mandatory before conformance is claimed. |
| `UX-P0-005` | `RESOLVED`; the Operation/Problem contract now includes the complete trust lifecycle, required actor, mutation/temporary-authority/running-compute state, both evidence times, oldest age, stable codes, and one safe next action. |
| `UX-P0-006` | `RESOLVED`; every advertised participant has an executable start, supported handoff or explicit rejection, measurable terminal task, and one consistent active-time denominator. |
| `UX-P0-F01` | `RESOLVED_AT_CONTRACT`; budget, running-cost state, stop owner, and final scoped inventory remain hard P8 evidence. |
| `UX-P0-F02` | `RESOLVED_AT_CONTRACT`; stop, remove configuration, retain/export, irreversible delete, and verification remain visibly separate lifecycle choices. |
| `UX-P0-007` | `RESOLVED — NO REGRESSION`; the deployment CLI is exact, pinned, GA, and absent from product runtime. |
| `UX-P0-F03` | `OPEN_NONBLOCKING_P0_HARD_P3_GATE`; no installer asset or supported platform claim exists yet. P3 must publish and test exact OS/architecture support, signed assets/checksums, native secure-store behavior, two-account spool/ACL/session release, one-account combined behavior, restart/reboot, uninstall, and explicit unsupported-platform/topology errors. This evidence is not waived by the P0 pass. |
| `UX-P0-F04` | `RESOLVED — NO REGRESSION`; before/after inventory distinguishes product/test-owned, reused, and unrelated resources and restores only what the proof changed. |
| `UX-P0-F05` | `RESOLVED — NO REGRESSION`; no part gate may waive an unresolved high or critical finding. |
| `UX-P0-F06` | `RESOLVED_AT_CONTRACT`; controlled-action summaries, distinct production actors, same-person denial, cost/expiry consequences, and recovery remain explicit. |
| `UX-P0-008` | `RESOLVED — NO REGRESSION`; attended data mutation, pending row, exact revoke, reconstruction, and later composite observation retain one safe chronology. |
| `UX-P0-009` | `RESOLVED`; separated mode has one two-account data handoff/return, while the verifier-owned roster task occurs without a third handoff. |
| `UX-P0-010` | `RESOLVED — NO REGRESSION`; combined mode remains a complete one-account-admin route with no false separation claim. |
| `UX-P0-011` | `RESOLVED`; v1 rejects the third identity reviewer and requires the verifier administrator to own the native roster task in their own invocation/session. |
| `UX-P0-012` | `RESOLVED`; final same-deployment acceptance, setup-only safe boot, refresh/reuse/expiry rules, both evidence clocks, and timing denominators are frozen. |
| `UX-P0-013` | `RESOLVED`; every recovery surface now derives from one actor/capability/prohibition decision table. |

No new numbered finding is opened.

## Documentation-plan outcome

The documentation plan passes at P0. It now has executable product truth to document rather than asking prose to bridge missing workflow transitions.

- The Diataxis split is complete: tutorials, task-focused how-tos, exact reference, explanation, operation/error recovery, security/operations, and optional-capability routes are separate.
- The bootstrap documentation starts before the App exists and preserves the exact stage/deploy/stop/bind/candidate/start/reobserve/accept sequence. Combined and separated procedures are visibly distinct; a third-reviewer request is an unsupported-path result, not an improvised handoff.
- Dedicated pages cover native roster review, trust refresh, drift/expiry, recovery actors, App lifecycle, cost, retain/export, irreversible deletion, and uninstall.
- Page requirements include both evidence times, oldest age, expiry, running-compute state, candidate versus accepted state, setup-only behavior, plain-language labels, stable codes, and the actor who acts next.
- The review model includes information-architecture, Diataxis, FastAPI-style readability, technical accuracy, security/compliance/privacy, and documentation usability/accessibility passes, plus rendered-site and real-capture verification.
- Real captures are required for both modes, failure/recovery, stage authority, candidate/acceptance, unchanged refresh, page-open expiry, failed stop/running cost, first evidence, and zero active-resource cleanup. Publication-safety review excludes real workspace/account/user identifiers, credentials, raw SQL, paths, and Personal Data.

`UX-P0-F03` still constrains the eventual installer how-tos: documentation may describe the frozen contract now, but it must not claim a concrete OS/architecture or secure-store/topology combination is supported until P3 publishes and proves that combination.

## P0-P10 usability matrix

These are planning outcomes, not claims that later implementation or live evidence already exists.

| Part | Tenth usability outcome | Required next evidence |
|---|---|---|
| P0 — Product contract | `PASS` | Record this immutable-hash verdict with the Databricks and dbt specialist outcomes. No open P0 usability blocker remains. |
| P1 — Capture library | `PASS` | Implement actionable, allowlisted validation errors and the complete malformed/partial/unsupported fixture set without exposing raw diagnostics. |
| P2 — Collector and reconciliation | `PASS` | Prove separate Job/dbt/collector/archive/capture outcomes, durable trust-status stamping, stale continuation, exactly-once behavior, and visible 20-minute recovery state. |
| P3 — Bundle installer | `PASS_WITH_FOLLOW_UP` | Implement the exact two-mode journeys, actor-owned roster task, recovery table, durable event lifecycle, setup-only safe boot, stop/cost states, and same-deployment acceptance. Close `UX-P0-F03` before any supported installer release. |
| P4 — App read-only MVP | `PASS` | Build accessible setup-only, health, evidence, investigation, stale, recovery, running-cost, and lifecycle pages. The first evidence page must consume only final accepted status and remain useful when optional enrichment is disabled. |
| P5 — Job onboarding | `PASS` | Prove the five scanner outcomes, semantic-change preview, owner review, rollback, and no silent mutation of customer Jobs. |
| P6 — Controlled actions | `PASS_AT_PLANNING_GATE` | Implement and test uncached prepare/approve/run checks, the conditional fresh-event gate, both evidence clocks, expiry between phases, page-open expiry, same-person denial, immutable summaries, recovery, and candidate/stale/drift/conflict lock. |
| P7 — Security and operations | `PASS_WITH_FOLLOW_UP` | Publish and rehearse refresh, recovery, upgrade/rollback, App/workstation restart, cost/failure, retain/export/delete/uninstall, trusted-root, and exact supported-platform runbooks. `UX-P0-F03` remains the concrete installer release gate. |
| P8 — Bounded live proof | `PASS_AT_PLANNING_GATE` | Execute the planned two-user, combined, lifecycle, kill/race, expiry/refresh, browser-loss, failed-stop, trust-conflict, first-evidence, cost, and scoped zero-resource inventory tests without leaving paid resources running. |
| P9 — Optional intelligence | `PASS` | Keep all core journeys complete with AI disabled and prevent AI from becoming an authorization, capture, trust, migration, or free-form dbt command path. |
| P10 — Private alpha | `PASS_AT_PLANNING_GATE` | Non-author participants must prove both supported modes, third-reviewer/non-admin-verifier rejection, first evidence, recovery, refresh, upgrade, retain/delete/uninstall, timing targets, confidence, and zero safety-critical error or moderator takeover. |

## Final disposition

`PASS_WITH_FOLLOW_UP`.

Baseline 0.11 is a coherent, fail-closed P0 product journey. It truthfully narrows regulated separated mode to two Databricks actors, gives the verifier an actor-owned native roster task, rejects unsupported reviewer topology before mutation, makes the real App deployment observable before acceptance, persists trust in a customer-local control ledger/view, shows both evidence clocks and oldest age, defines one refresh and recovery route, locks P6 across candidate/stale/drift/conflict state, and makes running-cost/failure consequences visible.

No safety or zero-guess issue is waived. `UX-P0-F03` remains open and is a hard P3 release gate for the real signed installer and supported workstation combinations. All other prior UX findings are resolved at the planning level, and no new P0 usability finding is opened.

No Azure or Databricks resource was created, started, stopped, queried, changed, or deleted by this review.
