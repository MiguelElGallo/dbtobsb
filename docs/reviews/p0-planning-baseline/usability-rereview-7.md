# Usability and onboarding seventh re-review: P0 planning baseline 0.8

- Reviewed input: frozen author-owned planning file set; repository has no commit yet
- Frozen author-input SHA-256: `185113f8218872fc934f40ecce588b255507fdfd400bdbde6f0c7755e48ebe3f`
- Hash scope: `README.md`, `AGENTS.md`, `docs/index.md`, and all Markdown files under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path; SHA-256 of the sorted per-file SHA-256 records
- Date: 2026-07-15
- Reviewer: independent usability, onboarding, and accessibility seventh re-review
- Verdict: `PASS_WITH_FOLLOW_UP`
- Cloud mutation: none

## Immutable input and method

I independently recomputed the author-input hash before review. It exactly matched the assigned digest. This report is outside that hash scope and is the only file written by this review.

I read the complete frozen author set, the historical usability reviews, and the resolution ledger. I traced the first-screen mode choice through readiness, migration-envelope approval, fixed Statement Execution, temporary receipt access and revoke, durable remote receipt, runtime planning, App start, first evidence, optional controlled-action enablement, upgrade, rollback, retain/delete, and uninstall. I then rechecked every P0-P10 usability gate, the separated-duties route, scanner outcomes, operation/error contracts, accessibility, cost, and `UX-P0-F03`.

No Databricks or Azure authentication, API, CLI, workspace, compute, storage, identity, or resource operation was performed. Current guidance was researched read-only on the public web.

## Current authoritative guidance checked

- [Azure Databricks Bundle authentication](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/authentication) still recommends OAuth U2M for attended Bundle work, recommends configuration profiles, and documents that `DEFAULT` is selected when no profile or host mapping is supplied. [OAuth U2M authorization](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/auth/oauth-u2m) still uses a browser-authenticated, locally cached user context. The plan's explicit actor-owned profile, host/current-user confirmation, secure-store check, and rejection of implicit `DEFAULT` remain appropriate.
- [NIST SP 800-53 Rev. 5.1 AC-5 and AC-6](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final) distinguish separation of duties among individuals or roles from least privilege. Baseline 0.8 correctly avoids calling the one-human route separation of duties and retains separate technical identities without presenting them as independent human approval.
- [WCAG 2.2 full-page and complete-process requirements](https://www.w3.org/TR/WCAG22/#complete-processes) require every page/state in a process to meet the claimed level. Its [status-message guidance](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html), [error-identification guidance](https://www.w3.org/WAI/WCAG22/Understanding/error-identification.html), and [accessible-authentication guidance](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html) support programmatic progress, text errors and correction guidance, and authentication that permits platform/browser assistance rather than transcription tests. The plan covers complete flows, programmatic status/error behavior, keyboard and screen-reader testing, text-only CLI output, and copyable enrollment input.
- [GOV.UK user-research planning](https://www.gov.uk/service-manual/user-research/plan-user-research-for-your-service) recommends iterative usability rounds with representative groups, commonly four to eight participants per qualitative round, including disabled users or focused accessibility rounds. [GOV.UK usability benchmarking](https://www.gov.uk/service-manual/measuring-success/usability-benchmarking-a-website-or-whole-service) measures completion, time, abandonment/false success, ease, and confidence and recommends no more than five tasks per participant. The provisional seven-role private-alpha task design matches those formative practices and explicitly avoids claiming statistical generalizability.

## Focused disposition of `UX-P0-010`

`UX-P0-010` is resolved at the planning-contract level.

| Acceptance condition | Result | Frozen-plan evidence |
|---|---|---|
| Executable mode choice | `PASS` | `docs/plans/product-plan.md:363-418` gives one common start, then separate numbered `Separated-duties` and `Combined-role` branches before a shared runtime path. The first screen explains both choices before confirmation. |
| One accountable actor/account/profile | `PASS` | `docs/plans/product-plan.md:109,176-195,402-410` requires one managed OS account, one actor-owned OAuth U2M profile, and the union of deployment and UC prerequisites. It never invents a second human or profile. |
| Honest residual-risk acknowledgement | `PASS` | Before mutation, the plan records `COMBINED_ROLE`, `human_actor_count=1`, and `independent_human_separation=false`. The ADR, documentation route, receipts, participant task, and acceptance evidence use the same meaning. |
| Immutable mode and same-account separated rejection | `PASS` | Mode is revalidated on every resume and cannot change after first mutation. `MODE_CHANGE_REQUIRES_CLEANUP` fails safely; a same-account `SEPARATED_DUTIES` attempt returns `HANDOFF_TOPOLOGY_UNSUPPORTED` without silently becoming combined mode. |
| No misleading cross-account mechanics | `PASS` | The combined branch explicitly emits no capsule, spool read/write, account-release proof, `UC_HANDOFF_RECEIPT`, `OWNER_PROFILE_RETAINED`, or deployer-return gate. Tests assert those states are absent, not merely skipped in the UI. |
| Security controls that still apply | `PASS` | Recovery audit, exact change preview, mode-bound execution binding, durable cleanup readiness before data mutation, fixed signed Statement Execution, exact temporary receipt revoke, full effective-authority verification, durable Delta receipt, fresh runtime plan, stopped App apply, and explicit App start remain mandatory. |
| Cleanup-first interruption recovery | `PASS` | The same actor must reauthenticate the same profile and enter `COMBINED_CLEANUP_REQUIRED`. Only exact statement inspection, revoke, verification, safe receipt completion, and status are allowed until the remote state is sealed. Wrong actor/profile/host/workspace/digest fails before mutation. |
| Remote receipt is authoritative | `PASS` | Runtime unlock re-reads the customer-owned sanitized Delta view and live state. A local marker, checkpoint, copied JSON, capsule, or Jobs output cannot substitute. The direct view removes a Jobs-output retrieval/expiry step from the user journey. |
| Lifecycle and optional upgrade coverage | `PASS` | `docs/plans/product-plan.md:427-485,487-518` reuses the immutable selected mode for P6, upgrade, rollback, retain/delete, and uninstall; staging includes abrupt failures at each data/runtime boundary in both modes. Production action-person separation remains independent of the combined installer role. |
| Measurable personal journey | `PASS` | `docs/plans/product-plan.md:519-535` assigns a non-author combined administrator a clean one-account/profile task, the full lifecycle, same-account-separated denial, 100% safety-critical success, no manual internals, and a 20-minute total active-actor bootstrap target with platform and handoff wait recorded separately. |

The previous defect was not closed by wording alone. The revised contract now supplies the missing branch, states, recovery restrictions, terminal gate, documentation route, participant, timing, and lifecycle tests.

## Broader acceptance and no-regression review

| Area | Result | Reason |
|---|---|---|
| Separated-duties clarity | `PASS` | The one-workstation/two-managed-account route still uses one command per actor, actor-owned profiles/checkpoints, an auto-discovered nonauthoritative capsule, uninterrupted UC data control, remote receipt verification, OS-account release, and deployment return. Wrong/same actor and improvised separate-workstation routes fail closed. |
| Receipt and data-plane comprehension | `PASS` | The user sees one fixed migration envelope, one attended data sequence, exact temporary receipt access/revoke, one durable Delta receipt/view, and a separate runtime plan. Removing the privileged migration Job and Jobs-visible receipt carrier reduces actors, mutable code paths, and expiry/recovery concepts without hiding trusted administrator roots. |
| Safe errors and progress | `PASS` | Pollable Operation state is separate from terminal RFC 9457 Problem Details. Each error includes selected mode, required actor, mutation/temporary-authority/running-compute state, retryability, and one safe consequence; raw SQL, exceptions, paths, tokens, internal IDs, and unfiltered platform messages are excluded. Unknown state never becomes success. |
| No manual internals | `PASS` | Primary journeys use `dbtobsb bootstrap`, display-name resource selection, and generated plans. No reader must enter or transfer SQL, resource IDs, paths, profile names, capsules, checkpoints, flags, privileges, YAML, or tokens. |
| First value and observable truth | `PASS` | Deployment success is insufficient. The product becomes `Observable` only after a real expected evidence row is queried, while Job, dbt, collector, and capture outcomes remain separate. |
| Lifecycle safety | `PASS` | Stop compute, remove code/configuration, retain/export, irreversible delete/verify, rollback, and uninstall are distinct consequences. Retain/export is the default; destructive data work has a separate attended plan and verification. |
| Cost and cleanup | `PASS` | Planning uses no compute; schedules start paused; App start is explicit and cost-bearing; each live proof has minute/DBU limits, cancellation and cleanup ownership, and a before/after inventory that preserves unrelated resources. |
| Accessibility | `PASS` at contract level | WCAG 2.2 AA applies to full pages and complete processes with automated plus keyboard/screen-reader evidence, zoom/reflow/contrast/status/error coverage, and no color-only state. CLI output is append-only text with `--no-color`, JSON, meaningful exits, and no spinner-only progress. |
| Optionality | `PASS` | System enrichment, controlled actions, Genie/MCP, and Marketplace remain separate routes. The base read-only product works without system-table access, AI, or action capabilities. |

## Prior finding dispositions

`RESOLVED` here means the planning contract is sufficiently complete and testable; it does not pre-approve implementation or live evidence assigned to P1-P10.

| Finding | Seventh disposition |
|---|---|
| `UX-P0-001` | `RESOLVED` — one signed wrapper/command, explicit actor-owned profile, resumable stages, safe App start, and URL handoff apply to both modes. |
| `UX-P0-002` | `RESOLVED` — human roles, prerequisite owners, residual access, and the distinct combined/separated routes are actionable. |
| `UX-P0-003` | `RESOLVED` — `READY`, `NEEDS_CHANGES`, `UNSUPPORTED`, `ACCESS_BLOCKED`, and `CHECK_FAILED` remain distinct; only `NEEDS_CHANGES` can propose a patch. |
| `UX-P0-004` | `RESOLVED` at contract level — full-page/complete-process WCAG 2.2 AA plus manual and automated evidence remains mandatory. |
| `UX-P0-005` | `RESOLVED` — pollable Operation and terminal Problem contracts remain separate, safe, and recovery-oriented. |
| `UX-P0-006` | `RESOLVED` — the combined participant, lifecycle task, 20-minute active target, and not-applicable handoff wait close the part reopened by `UX-P0-010`. |
| `UX-P0-F01` | `RESOLVED` at contract level; bounded P8 live evidence remains required. |
| `UX-P0-F02` | `RESOLVED` at contract level; P7 destructive-path evidence remains required. |
| `UX-P0-007` | `RESOLVED` — Databricks CLI 1.7.0 remains exact, pinned, GA, and deployment-only. |
| `UX-P0-F03` | `OPEN`, non-blocking for P0 and a hard P3 release gate — publish and test the exact OS/architecture, signed assets and verification, native secure-store combination, two-account handoff component/ACL/session-release behavior, one-account combined behavior, reboot/resume, uninstall, and explicit unsupported-platform/topology errors. |
| `UX-P0-F04` | `RESOLVED` — scoped before/after inventory protects reused and unrelated resources. |
| `UX-P0-F05` | `RESOLVED` — normative gates consistently use “high or critical.” |
| `UX-P0-F06` | `RESOLVED` at contract level — controlled-action summary, digest, change detection, and production same-person denial remain explicit. |
| `UX-P0-008` | `RESOLVED` — attended fixed data chronology, targeted receipt revoke, cleanup-only restart, exact receipts, and no manual internals remain coherent. |
| `UX-P0-009` | `RESOLVED` — separated-duties actor/profile/checkpoint/capsule/receipt/release/return choreography remains complete. |
| `UX-P0-010` | `RESOLVED` — the one-actor combined route is now executable, honest, recoverable, lifecycle-complete, and measurable. |

No new blocker, high, medium, or low planning finding was identified.

## P0-P10 no-regression matrix

| Part | Seventh usability verdict | Result |
|---|---|---|
| P0 — Product contract | `PASS_WITH_FOLLOW_UP` | Both advertised installer modes are coherent and testable. Only the bounded P3 workstation matrix remains open. |
| P1 — Capture library | `PASS` | Validation and capture states remain deterministic, fail closed, and expose safe actionable outcomes without Databricks. |
| P2 — Collector and reconciliation | `PASS` | Job, dbt, collector, and capture outcomes stay separate; cancellation and bounded reconciliation remain understandable and idempotent. |
| P3 — Bundle installer | `PASS_WITH_FOLLOW_UP` | The zero-guess combined and separated journeys, exact plans, cleanup-first recovery, durable receipt, stopped App, and mode-specific completion gates pass. Close `UX-P0-F03` before release. |
| P4 — App read-only MVP | `PASS` | Read-only investigation, accessibility, cost confidence, safe status, and base-product completeness without optional system data remain adequate gates. |
| P5 — Job onboarding | `PASS` | Scanner outcomes, proposed source patch, semantic-change warning, dbt-owner review, and rollback remain distinct and safe. |
| P6 — Controlled actions | `PASS` | The upgrade inherits the selected installer mode and cleanup-first receipt path without weakening the separate production initiator/approver rule. Implementation evidence remains a P6 gate. |
| P7 — Security and operations | `PASS` | Both modes cover upgrade, incident, rollback, retain/export, destructive delete, and uninstall with clear ownership, residual access, and orphan prevention. |
| P8 — Bounded live proof | `PASS` at planning-contract level | One clean run per mode, mode-specific interruption evidence, same-account-separated rejection, foreign-grant preservation, stopped resources, and remote-receipt precedence are required. Live proof is still pending. |
| P9 — Optional intelligence | `PASS` | AI remains advisory, optional, and outside authorization, mutation, command construction, capture, and validation. |
| P10 — Private alpha | `PASS` at planning-contract level | Both non-author mode journeys now have completion, recovery, lifecycle, comprehension, and timing evidence gates. The sessions are still pending. |

## Final verdict

`PASS_WITH_FOLLOW_UP`.

Baseline 0.8 resolves `UX-P0-010` and introduces no usability or accessibility regression across P0-P10. The planning baseline may be accepted from the usability/onboarding perspective. `UX-P0-F03` remains the sole usability follow-up and must close before any P3 workstation/installer combination is published as supported. No Azure or Databricks resource was created, started, stopped, changed, or deleted by this review.
