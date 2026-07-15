# Usability and onboarding eighth re-review: P0 planning baseline 0.9

- Reviewed input: frozen author-owned planning file set; repository has no commit yet
- Frozen author-input SHA-256: `ca6df928ba9353ffa240f7a5c21ab9a7cccf68bf682145d58ad18f83de536d1a`
- Hash scope: `README.md`, `AGENTS.md`, `docs/index.md`, and all Markdown files under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path; SHA-256 of the sorted per-file SHA-256 records
- Date: 2026-07-15
- Reviewer: independent usability, onboarding, and safety eighth re-review
- Verdict: `PASS_WITH_FOLLOW_UP`
- Cloud mutation: none

## Immutable input and method

I independently recomputed the author-input hash before review. It exactly matched the assigned digest. This report is outside that hash scope and is the only file written by this review.

I read the complete frozen author set, the seventh usability report, and the resolution ledger. I traced both executable bootstrap branches from mode selection through readiness, migration-envelope approval, bounded Statement Execution, interruption recovery, pending attestation, exact revoke, live composite acceptance, Direct runtime planning, runtime-integrity verification, explicit App start, first evidence, upgrade, rollback, retain/delete, and uninstall. I also reviewed every P0-P10 usability gate and the complete documentation plan.

No Databricks or Azure authentication, API, CLI, workspace, compute, storage, identity, or resource operation was performed.

## Current authoritative guidance checked

- [Azure Databricks Query History](https://learn.microsoft.com/en-us/azure/databricks/sql/user/queries/query-history) says another user with at least warehouse `CAN VIEW` can inspect prior query runs, including complete query text and user/compute details, and can cancel a currently running query from the native UI. Baseline 0.9 correctly treats that visibility as a privacy consequence, uses a dedicated warehouse, avoids copying raw text into dbtobsb, and treats accepted cancellation as nonterminal until remote state agrees.
- [Azure Databricks workspace-object ACLs](https://learn.microsoft.com/en-us/azure/databricks/security/auth/access-control/#sql-warehouse-acls) distinguish warehouse viewing, monitoring/execution, and management/stop capabilities. The plan accurately separates approved `CAN_MONITOR` actors from the named warehouse manager and makes full-query visibility, execution authority, and inability to stop/manage the warehouse part of readiness and test evidence.
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) applies conformance to complete pages and complete processes. The plan keeps the complete install, recovery, investigation, retention, deletion, and uninstall flows in scope and requires automated checks plus keyboard and representative screen-reader evidence.
- [GOV.UK usability benchmarking](https://www.gov.uk/service-manual/measuring-success/usability-benchmarking-a-website-or-whole-service) supports measuring completion, time, abandonment, ease, and confidence against realistic tasks. The plan uses those measures as provisional private-alpha gates and explicitly avoids presenting its small formative sample as statistically generalizable.

## Focused eighth-pass journey review

| Acceptance condition | Result | Frozen-plan evidence and user consequence |
|---|---|---|
| Executable combined route | `PASS` | `docs/plans/product-plan.md`, **Bootstrap the product**, gives one common start, a numbered `Combined-role branch`, and a shared runtime path. One accountable actor uses one OS account and one actor-owned profile, emits no capsule/release/return state, and records both independence flags as false. |
| Executable separated route | `PASS` | The same section gives a numbered `Separated-duties branch`: deployment actor publishes an auto-discovered nonsecret capsule, the different UC actor runs the same `dbtobsb bootstrap` command, performs the attended fixed sequence, releases the OS session, and the original deployment/seal-verifier account returns for independent live observation. |
| No guessed or entered internals | `PASS` | The primary route requires only `dbtobsb bootstrap`. People select display-name resources and a safe profile label inside their own account. No person enters, copies, or transfers SQL, query/Job/resource IDs, file or workspace paths, profile names, capsules, checkpoints, flags, privileges, YAML, tokens, or rendered plans. The native Query History route is reached through an approved deep link and an exact visible cancel action. |
| Lost UC execution is recoverable with the two existing separated actors | `PASS` | The UC actor normally owns apply, attestation, and revoke. If that actor/process is lost, the already participating deployment/seal-verifier actor can locate the unique marked operation in GA Query History, request native cancellation, wait for terminal state, reconstruct Unity Catalog state, and use its disclosed object-scoped `MANAGE` only for the exact signed cleanup/revoke. Zero/multiple matches or a ten-minute nonterminal query escalates to the already named warehouse manager and blocks safely. Recovery means safe containment and exact cleanup; it is not mislabeled as successful installation when privileged data work is incomplete. |
| Combined interruption recovery | `PASS` | The same actor reauthenticates the immutable actor/profile/host/workspace binding and enters `COMBINED_CLEANUP_REQUIRED`. Only Query History recovery, exact revoke, live reconstruction, attestation verification, and status are available until the state is safe. The route does not invent a second person or reuse separated-mode handoff state. |
| `CAN_MONITOR` privacy and authority are understandable | `PASS` | Readiness names the installer-only warehouse, full query text, user, error, timing, metrics, and profile visibility, the actors receiving `CAN_MONITOR`, the fact that they can execute queries, and the separate manager who can stop/manage the warehouse. An unrelated workload on that warehouse is unsupported. The non-author tasks require both actors to explain the exposure before mutation. |
| Native cancel/recovery is actionable | `PASS` | One read-only marker precedes each mutation, the wrapper finds exactly one operation, and the product UI exposes status plus an approved native deep link without copying raw query text. Accepted cancellation remains visibly nonterminal; polling, reconstructed state, escalation owner, ten-minute boundary, and allowed next action are all explicit. |
| Pending attestation versus composite seal is comprehensible | `PASS` | `DATA_APPLIED_PENDING_REVOKE` is consistently described as a pre-revoke row, not a terminal seal. The lifecycle visibly proceeds through revoke and live observation. Runtime unlock requires the matching row, exact direct-pair absence, complete current-DML and self-grant classification, no indeterminate query, verifier/time, mode gate, and canonical seal digest. Participant tasks must explain the distinction. |
| `MANAGE` and other trusted roots are disclosed honestly | `PASS` | The deployment/seal-verifier's object-scoped `MANAGE` is described as self-grant/revoke capability, not current data access or administrator-resistant separation. Workspace/account/metastore, object/receipt, deployment, App/Job-management, and Service Principal role administrators are named roots. Unsupported administrator-resistant custody fails readiness instead of being implied. |
| Migration acceptance and runtime integrity stay separate | `PASS` | The data-contract composite seal is point-in-time. A separate runtime-trust manifest and the plain stable states `RUNTIME_INTEGRITY_VERIFIED`, `RUNTIME_CODE_OR_CONFIG_DRIFT`, `RUNTIME_AUTHORITY_DRIFT`, and `RUNTIME_INTEGRITY_UNVERIFIED` govern whether later evidence is trusted. Drift consequences for collector, enrichment, and controlled actions are testable and do not rewrite migration history. |
| State and action consequences are visible | `PASS` | Every long-running Operation reports required actor, actor state, mutation/temporary-authority/running-compute state, display names, retry/cancel capability, and one safe next action. Unknown state never becomes success. Pollable Operation state and terminal RFC 9457 Problem Details remain distinct and exclude raw platform material. |
| Cost and cleanup are explicit | `PASS` | The installer-only warehouse uses the lowest supported auto-stop and has a named manager. App start is a separate, cost-bearing action. Every live proof declares elapsed-time and DBU bounds, cancellation deadline, cleanup owner, prior state, and final inventory. Tests must end with no nonterminal query, temporary grant, App/Job/test compute, or unrestored test-started warehouse; unrelated resources are never stopped. |
| Twenty-minute combined target is a gate, not a claim | `PASS` | The plan calls 20 minutes a provisional active-actor target, excludes platform wait, marks combined handoff wait not applicable, assigns it to a non-author P3/P10 rehearsal, and permits rebaselining only through an approved decision backed by evidence. It does not claim that an implementation has already met the target. |

The revised recovery and trust model adds concepts, but it does not add manual configuration or an unowned handoff. Each concept has a visible state, accountable actor, consequence, recovery boundary, documentation route, and non-author comprehension task.

## Documentation-plan usability review

| Area | Result | Reason |
|---|---|---|
| Entry and routing | `PASS` | The home and mode landing pages route personal combined administrators and the two separated actors to visibly different procedures before mutation. Read-only operators are not sent through setup navigation. |
| End-to-end installation | `PASS` | `bootstrap-the-private-app.md` is planned as the controlling procedure from signed-installer verification through explicit App start. It routes to combined or separated mode-specific steps while the related how-to pages expose deeper recovery and verification without requiring the reader to construct a workflow. |
| Recovery discoverability | `PASS` | Stable codes, responsible actor, native deep link, query terminality, exact revoke, current DML/self-grant classification, manager escalation, runtime drift, and lifecycle recovery each have planned how-to and reference coverage. |
| Mental model | `PASS` | Dedicated explanations distinguish resource versus data plans, attended migration, pending row versus seal, combined versus separated roles, migration seal versus runtime integrity, and trusted administrative capability. Reference pages catalogue states and grants without replacing procedures. |
| Page-level safety | `PASS` | Every task page must show audience/environment, exact prerequisite and residual access, cost/mutation note, expected output, outcome verification, recovery, cleanup/rollback, and related concepts in a fixed order. |
| Evidence and privacy | `PASS` | The real-capture plan includes both modes, full-query exposure, cancel recovery, attestation/composite evidence, trusted-root/runtime drift, elapsed-time proof, and final inventory. It requires source-image, metadata, OCR, history, rendered-site, and CI-artifact safety checks. |
| Accessibility and review cadence | `PASS` at planning level | Complete-process WCAG 2.2 AA, text-only CLI behavior, keyboard/screen-reader checks, responsive/zoom/contrast requirements, page-by-page reviews, and rendered-site validation are explicit. Rendered-page evidence is correctly deferred until pages exist; D0 does not claim a rendered-site pass. |

The number of planned pages is large, but the audience/task landing pages, controlling bootstrap procedure, page registry, inheritance rules, and route re-review gate prevent the reader from receiving a flat file catalogue. D0 must still prove those routes in a rendered navigation prototype before prose is scaled out.

## Prior finding dispositions

`RESOLVED` means the planning contract is complete enough to implement and test; it does not pre-approve the P1-P10 implementation or live evidence.

| Finding | Eighth disposition |
|---|---|
| `UX-P0-001` | `RESOLVED` — one signed wrapper/command, explicit actor-owned profile selection, safe progress, App start, and URL handoff remain intact. |
| `UX-P0-002` | `RESOLVED` — prerequisites, grant owners, residual access, and human roles are actionable in both modes. |
| `UX-P0-003` | `RESOLVED` — scanner states remain distinct and only `NEEDS_CHANGES` can generate a source patch. |
| `UX-P0-004` | `RESOLVED` at contract level — complete-process WCAG 2.2 AA evidence remains mandatory. |
| `UX-P0-005` | `RESOLVED` — safe pollable Operations and terminal Problems remain distinct. |
| `UX-P0-006` | `RESOLVED` — representative roles, task limits, safety, timing, completion, ease, and confidence gates include both modes. |
| `UX-P0-F01` | `RESOLVED` at contract level — bounded live-proof cost and final inventory remain P8 evidence. |
| `UX-P0-F02` | `RESOLVED` at contract level — stop, remove, retain/export, and irreversible delete/verify remain separate consequences. |
| `UX-P0-007` | `RESOLVED` — CLI `1.7.0` is exact, pinned, GA, and deployment-only. |
| `UX-P0-F03` | `OPEN`, non-blocking for P0 and a hard P3 release gate — publish and test the exact OS/architecture, signed assets and verification, native secure-store combination, two-account spool/ACL/session-release behavior, one-account combined behavior, restart/reboot resume, uninstall, and explicit unsupported-platform/topology errors before claiming support. |
| `UX-P0-F04` | `RESOLVED` — scoped before/after inventory preserves reused and unrelated resources. |
| `UX-P0-F05` | `RESOLVED` — normative gates consistently prohibit unresolved high or critical usability findings. |
| `UX-P0-F06` | `RESOLVED` at contract level — optional controlled-action summaries and same-person denial remain explicit. |
| `UX-P0-008` | `RESOLVED` — the attended fixed-data chronology and cleanup-first restart remain coherent after removal of the migration Job. |
| `UX-P0-009` | `RESOLVED` — the two-account topology, actor-owned state, capsule, account release, and return remain executable, while the second actor can perform exact recovery of a lost UC request. |
| `UX-P0-010` | `RESOLVED` — combined mode remains a complete, measurable one-actor route without borrowed separated-mode gates. |

No new critical, high, medium, or low planning finding was identified.

## P0-P10 outcomes

| Part | Eighth usability outcome | Reason |
|---|---|---|
| P0 — Product contract | `PASS_WITH_FOLLOW_UP` | Both modes, recovery, privacy, seal, trusted-root, runtime-integrity, cost, and documentation contracts are coherent. Only `UX-P0-F03` remains open. |
| P1 — Capture library | `PASS` | Capture validation remains deterministic, fail-closed, fixture-testable, and capable of returning safe actionable states without Databricks. |
| P2 — Collector and reconciliation | `PASS` | Job, dbt, collector, archive, and capture outcomes remain separate; reconciliation is bounded and users can see when evidence is delayed or unavailable. |
| P3 — Bundle installer | `PASS_WITH_FOLLOW_UP` | The combined and two-account separated journeys are zero-guess; Query History takeover, exact revoke, pending/composite distinction, trusted roots, runtime drift, and cleanup are explicit. Close `UX-P0-F03` before release. |
| P4 — App read-only MVP | `PASS` | Setup health, investigation, distinct outcomes, cost confidence, recovery status, accessibility, and base-product operation without optional system access are adequate implementation gates. |
| P5 — Job onboarding | `PASS` | Five scanner outcomes, source patch, semantic-change warning, dbt-owner review, and rollback are distinct; no customer Job is silently mutated. |
| P6 — Controlled actions | `PASS` | The optional upgrade inherits the immutable mode, marked recovery, pending/composite truth, exact runtime DML, trusted managers, runtime-drift lock, and separate initiator/approver controls. |
| P7 — Security and operations | `PASS` | Privacy, owners, direct versus effective authority, self-grant capability, runtime trust, export/delete, rollback, uninstall, profile preservation, and orphan prevention have visible consequences and owners. |
| P8 — Bounded live proof | `PASS` at planning-contract level | Two genuine U2M users, cross-user result-fetch denial, native cancel, timeout/race/escalation, exact revoke, composite observation, runtime drift, and zero-active-resource inventory are required. Live proof remains pending by design. |
| P9 — Optional intelligence | `PASS` | AI remains optional, advisory, read-only where applicable, and outside authorization, dbt command construction, capture, validation, and required operation. |
| P10 — Private alpha | `PASS` at planning-contract level | Non-author combined and separated journeys cover first evidence, interruption, lifecycle, comprehension, support burden, and provisional timing. The 20-minute combined threshold remains evidence to collect, not a shipped claim. |

## Private-alpha implementation gate

`UX-P0-F03` remains the sole usability follow-up. Its owner is the P3 installer/workstation implementation, and its acceptance evidence is one clean test matrix for every supported OS/architecture covering signed-asset verification, native secure storage, combined one-account flow, separated two-account spool/ACL/session release, restart/reboot resume, component removal, secure-store failure, same-account separated rejection, separate-workstation rejection, and plain recovery errors. No installer platform may be advertised as supported before that matrix passes.

## Final verdict

`PASS_WITH_FOLLOW_UP`.

Baseline 0.9 addresses the seventh Databricks recovery, seal-ordering, and runtime-trust findings without introducing a usability regression. The combined route remains executable and honestly one-person; the separated route gives the two existing actors a bounded native recovery path; the user never has to enter or copy technical internals; pending attestation, composite seal, and runtime integrity are distinct; cost and cleanup are visible; and the 20-minute combined threshold is correctly a P3 validation hypothesis. The planning baseline may be accepted from the usability/onboarding perspective, subject only to `UX-P0-F03` before a P3 platform combination is released.

No Azure or Databricks resource was created, started, stopped, changed, or deleted by this review.
