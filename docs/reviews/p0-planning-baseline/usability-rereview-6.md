# Usability and onboarding sixth re-review: P0 planning baseline 0.7

- Reviewed input: frozen author-owned planning file set; repository has no commit yet
- Frozen author-input SHA-256: `85eab368552b9614eba555dd8f44feb1b8850d0eb66cdcc250cf98d6a502c893`
- Hash scope: `README.md`, `AGENTS.md`, `docs/index.md`, and all Markdown files under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path; SHA-256 of the sorted per-file SHA-256 records
- Date: 2026-07-15
- Reviewer: independent usability and onboarding sixth re-review
- Verdict: `CHANGES_REQUIRED`
- Cloud mutation: none

## Scope and method

I independently recomputed the frozen author hash before reviewing. It exactly matched the assigned value. I read the complete author-owned scope, all earlier usability reviews, and the current resolution ledger. I did not edit an author-owned file, an earlier review, or a cloud resource.

This was a focused but complete P0-P10 no-regression review. I traced both choices presented on the first bootstrap screen and concentrated on `UX-P0-009`: one regulated topology; distinct managed OS accounts; the workstation-administrator step; actor-owned profile, secure store, and checkpoint; honest OAuth-cache behavior; an auto-discovered nonsecret capsule; one command per actor; UC control from lease through seal; replacement cleanup; Databricks-anchored receipt; OS-account release and deployer return; stable actor/error states; same-account and separate-workstation rejection; no SQL, ID, path, profile-name, capsule, checkpoint, or YAML entry; task timing; accessibility; and recovery.

The new regulated separated-duties contract resolves `UX-P0-009`. It chooses exactly one topology, gives each actor a private OS-account boundary, keeps every profile/checkpoint with its owner, makes the capsule nonauthoritative navigation state, gives the UC account uninterrupted control from lease through anchored seal, supports a cleanup-only replacement actor, and prevents runtime until the deployer independently proves remote seal and return. The profile is honestly retained in its owner's account rather than described as deleted or revoked. Same-account “separation” and improvised separate-workstation transfer fail explicitly. This is a substantial and testable correction.

One high-severity usability defect remains outside that corrected two-person route. The product presents `Combined personal role` as an allowed first-screen mode, but the only numbered bootstrap sequence always creates a cross-account capsule, tells the deployer to leave the OS session, requires a distinct UC account with a different Databricks actor, and later requires deployment-account return. No combined-role branch says which handoff states are skipped, how one actor changes from deployer approval to UC execution and back, or how interruption recovery works. The advertised personal path therefore has no complete executable journey.

## Current guidance reused and checked

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) remains the current W3C Recommendation and applies conformance to complete processes, including every page/state needed to complete the process. The baseline's focus, status, error, reflow, keyboard, and screen-reader gates remain appropriate.
- [Azure Databricks OAuth U2M authorization](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/auth/oauth-u2m), the current [`auth` command reference](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/reference/auth-commands), and [configuration-profile guidance](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/auth/config-profiles) support browser-authenticated actor-owned profiles, explicit current-user/profile checks, local cached credential state, and explicit-profile selection. Baseline 0.7 now describes that boundary honestly.
- [GOV.UK moderated usability testing](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing) and [usability benchmarking](https://www.gov.uk/service-manual/measuring-success/usability-benchmarking-a-website-or-whole-service) support realistic role-specific tasks and measurement of completion, time, abandonment or false success, ease, and confidence. A selectable mode with no terminal task path cannot pass that standard.
- The [PatternFly CLI handbook](https://www.patternfly.org/content-design/writing-guides/cli-handbook/) supports specific text, text in addition to color, keyboard-accessible prompts, and automation-safe output. The baseline's append-only progress, `--no-color`, JSON, stable actor/error codes, and exact safe next action align with that guidance.

## Focused acceptance review

| Criterion | Result | Independent evidence |
|---|---|---|
| Exactly one regulated topology | `PASS` | `product-plan.md:30,105,172-189,361-394` consistently chooses one supported customer-controlled workstation with distinct deployment and UC OS accounts. Same-account separation and ad hoc separate-workstation transfer return `HANDOFF_TOPOLOGY_UNSUPPORTED`. |
| Workstation-administrator prerequisite | `PASS_WITH_FOLLOW_UP` | `product-plan.md:179,367-371,500-506` names the local administrator, component, account, ACL, atomicity, session-release, removal, and task-test boundary. Exact supported assets/OS behavior remains correctly assigned to `UX-P0-F03`. |
| Actor-owned OAuth, checkpoint, and secure-store honesty | `PASS` | `product-plan.md:116,174-189,367-377` keeps complete profiles, native secure-store entries, browser sessions, and checkpoints inside the owning account; rejects fallback/injected auth; never invokes sensitive auth output; and states that dbtobsb neither copies nor deletes the profile. |
| Auto-discovered capsule with no manual transfer | `PASS` | `product-plan.md:369-377,381-394` defines a signed, expiring, replay-resistant, atomic, auto-discovered, nonsecret capsule. Users enter no path, profile name, capsule, checkpoint, SQL, token, internal ID, or YAML. A capsule cannot authorize runtime. |
| One command per separated-duties actor | `PASS` | Deployment, UC, and deployment-return stages all use `dbtobsb bootstrap`; the wrapper discovers the correct operation and reports the current actor/consequence. No second shell vocabulary is required. |
| UC owns lease through anchored seal | `PASS` | `product-plan.md:130-139,373,386-390` keeps approval, cleanup checkpoint, lease, fixed Job, wait/cancel, revoke, full effective audit, data verification, attestation, and anchored terminal receipt in the UC account without returning control while DDL is active. |
| Replacement cleanup actor | `PASS` | An eligible replacement UC account on the same managed workstation can claim only an expiring cleanup capsule, seal, and stop; it cannot continue the migration. Wrong actor/profile/host/digest fails before mutation. |
| Anchored receipt and deployment return | `PASS` | Runtime unlock depends on the Databricks-anchored terminal receipt, independent live state, `OS_ACCOUNT_RELEASED`, and `DEPLOYER_RETURN_VERIFIED`. A return capsule is only a locator. |
| Stable states, recovery, and accessibility | `PASS` | Privilege and actor states are separate, Operation and RFC 9457 Problem fields name the required actor and safe consequence, CLI output is accessible text/JSON/no-color, and full App/site processes target WCAG 2.2 AA with manual evidence. |
| Combined-role honesty | `PASS_WITH_REQUIRED_FIX` | `product-plan.md:174,189,367` truthfully says combined mode is not separation of duties. However, `product-plan.md:381-392` has no executable combined branch and always requires a different actor/account. Honest labeling alone does not make the selected journey completable; see `UX-P0-010`. |
| Customer-owned schema, no manual internals | `PASS` | Schema ownership, required actor, foreign grants, exact lease/revoke, and object consequences are visible; the user chooses display names and supplies no SQL, IDs, paths, profile names, capsules, checkpoints, or YAML. |
| Optional system enrichment | `PASS` | The capability remains disabled/absent in base and has a separate owner, principal, paused Job, explicit regional/global source risk, pair-scope table, three snapshots, cost/freshness semantics, and removal route. |
| Lifecycle and first value | `PASS` | App start is separate and cost-bearing; `Observable` requires queried evidence; stop/remove/retain-export/delete/uninstall remain distinct; runtime and test cleanup are explicit. |
| Workstation support evidence | `PASS_WITH_FOLLOW_UP` | `UX-P0-F03` remains a well-bounded hard P3 release gate for exact OS/architecture, signed assets, local component, secure stores, account isolation, reboot, unsupported topology, and clean uninstall. It would be the sole pre-existing usability follow-up once `UX-P0-010` is resolved. |

## Ranked finding

### `UX-P0-010`: Give the selectable combined-personal mode a complete state path

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Owner: P0 product-contract and P3 installer owners, with usability and documentation re-review
- Affected evidence: `docs/decisions/0001-private-app-bundle.md:27,54`; `docs/plans/product-plan.md:10,30,172-189,357-394,441-447,483-506`; `docs/plans/documentation-plan.md:9-13,36-50,182-235,336-344`
- Baseline evidence: The first installer screen offers `Combined personal role` or `Separated duties`, the human-role model says the personal path is allowed, and the documentation outcome includes a combined-role user. But the canonical numbered procedure has only the separated route: step 6 always publishes `UC_HANDOFF_REQUIRED` and asks the deployer to leave; step 7 requires a distinct UC OS account and a Databricks actor different from the deployer; steps 9-10 require OS-account release and deployer return. The stage list has no combined-role actor state or bypass, and the validation suite exercises only a two-person clean install.
- User and system impact: A personal user can select an advertised supported mode and then be unable to proceed, be told their own actor is invalid, or be tempted to misclassify same-account activity as separated duties. The likely outcomes are abandonment, improvised account/profile handling, or an implementation that silently skips the wrong security gates. This affects the personally funded validation workspace and every small customer whose accountable installer legitimately holds both roles.
- Required change:
  1. Define one explicit combined-role state-machine branch. One accountable human in one managed OS account and one actor-owned U2M profile must prove both deployer and UC prerequisites. The receipt must record `COMBINED_ROLE` and state plainly that no independent human separation occurred.
  2. Preserve every security boundary that does not depend on two people: recovery audit first; resource plan approval; exact migration envelope; durable cleanup checkpoint before lease; execution binding; uninterrupted lease-to-Job-to-revoke-to-complete-effective-verification; Databricks-anchored seal; independent data verification; fresh runtime plan; stopped App; explicit App start.
  3. State exactly which cross-account mechanics are not used in combined mode. Do not emit or ask the user to transfer a UC handoff/return capsule, do not require a different actor, and do not claim OS-account release or deployer return. If an internal local continuation marker is retained, give it a different plain-language state and make clear that it is not separation evidence.
  4. Add combined actor states and safe errors, or explicitly map existing states without misleading labels. `HANDOFF_TOPOLOGY_UNSUPPORTED` must reject an attempt to claim same-account **separation**, not reject an intentional `COMBINED_ROLE` choice.
  5. On interruption, the same actor must resume cleanup-only from their own checkpoint, reauthenticate when needed, cancel/wait, revoke, verify, and anchor before any runtime action. Wrong workspace/profile/digest and incomplete authority still fail closed.
  6. Add a clearly separate personal-mode section to the bootstrap how-to/reference and a non-author task. Show the missing independent approval as a residual-risk consequence before mutation, not only as a receipt label.
  7. Test fresh install, process/network death at every lease/seal boundary, restart/reboot, upgrade, retain, delete, rollback, and uninstall in combined mode. Also prove that selecting separated mode from one account fails. The participant uses only `dbtobsb bootstrap`, enters no SQL/ID/path/profile/capsule/checkpoint/YAML, reaches first queryable evidence, and understands that no separation was exercised.
  8. Give combined mode its own active-time target and measurement. Do not calculate it by adding two actor targets or omit it from the private-alpha task set.
- Acceptance condition: A non-author personal administrator with both required Databricks roles selects `Combined personal role`, understands the missing independent-human control, completes install and first evidence through one documented command/state path, recovers from abrupt interruption cleanup-first, and completes upgrade and both lifecycle dispositions without a second OS account or misleading handoff state. The same person cannot select `Separated duties` and pass the distinct-actor gate. There is zero false success, moderator takeover, improvised transfer, wrong-workspace mutation, residual DDL, or unplanned running compute.

No other new high, critical, or blocking usability finding was found.

## Prior finding and follow-up disposition

| Finding | Baseline 0.7 disposition | Sixth re-review result |
|---|---|---|
| `UX-P0-001` | One signed wrapper/command per actor, explicit profile/identity, resumable stages, secure checkpoints, URL handoff | `RESOLVED` for the regulated separated route; `UX-P0-010` separately affects the advertised combined branch |
| `UX-P0-002` | Ten roles, grant owner, residual access, workstation owner, combined and separated paths | `RESOLVED` for role naming and honest combined-mode classification; combined execution remains incomplete under `UX-P0-010` |
| `UX-P0-003` | Five scanner outcomes; only `NEEDS_CHANGES` can propose a patch | `RESOLVED` |
| `UX-P0-004` | Full-page/complete-process WCAG 2.2 AA scope plus manual and automated evidence | `RESOLVED` at contract level; implementation evidence remains required |
| `UX-P0-005` | Separate pollable Operation and RFC 9457 Problem contracts | `RESOLVED` |
| `UX-P0-006` | Six-plus non-author participants, role tasks, safety/time/ease/confidence thresholds | `REOPENED IN PART` by `UX-P0-010`: the two-person task contract passes, but the offered personal mode has no participant, task, or time target |
| `UX-P0-F01` | Numerical live-proof ceiling, cancellation, owner, stopped/paused inventory | `RESOLVED` at contract level; P8 evidence pending |
| `UX-P0-F02` | Stop, remove configuration, retain/export, irreversible delete/verify are separate | `RESOLVED` at contract level; P7 evidence pending |
| `UX-P0-007` | CLI 1.7.0 exact, pinned, GA, deployment-only | `RESOLVED` |
| `UX-P0-F03` | Exact OS/architecture/assets/component/secure-store/topology behavior | `OPEN`; bounded hard P3 implementation gate and the only pre-existing usability follow-up |
| `UX-P0-F04` | Scoped pre/post inventory protects reused/unrelated resources | `RESOLVED`; P8 evidence pending |
| `UX-P0-F05` | “High or critical” gate wording is consistent | `RESOLVED` |
| `UX-P0-F06` | Immutable controlled-action summary and digest/revalidation | `RESOLVED` at contract level; P6 evidence pending |
| `UX-P0-008` | Correct lease/seal chronology, cleanup-only recovery, exact receipts | `RESOLVED` |
| `UX-P0-009` | One regulated topology, actor-owned local state, capsule isolation, UC lease-to-seal, anchored receipt, release/return | `RESOLVED`; every requested handoff and recovery boundary is explicit and testable in the separated route |

## P0-P10 no-regression matrix

| Part | Sixth re-review verdict | Usability and onboarding result |
|---|---|---|
| P0 — Product contract | `CHANGES_REQUIRED` | The regulated separated path now passes and `UX-P0-009` is resolved. The product contract still advertises an incomplete combined-personal path under `UX-P0-010`. |
| P1 — Capture library | `PASS` | Artifact/event validation, fail-closed states, safe messages, and distinct outcomes remain testable without Databricks. |
| P2 — Collector and reconciliation | `PASS` | DML-only collection, bounded reconciliation, cancellation recovery, and separate Job/dbt/collector/capture outcomes remain clear. |
| P3 — Bundle installer | `CHANGES_REQUIRED` | The two-account installer now has a zero-guess, actor-bound, cleanup-first journey. The first-screen combined choice has no executable branch. `UX-P0-F03` remains the bounded release gate after that is fixed. |
| P4 — App read-only MVP | `PASS` | Base App remains useful without optional system data/actions; accessible status/recovery, cost confidence, and read-only handoff remain adequate gates. |
| P5 — Job onboarding | `PASS` | Scanner states, source patch, semantic-change review, owner approval, and rollback remain understandable and safe. |
| P6 — Controlled actions | `CHANGES_REQUIRED` | The optional upgrade correctly inherits the regulated UC handoff, but an allowed combined-role installation also needs a defined combined migration/seal branch before actions can be enabled safely. |
| P7 — Security and operations | `CHANGES_REQUIRED` | Lifecycle distinctions, ownership transfer, grant preservation, profile ownership, and two-person recovery pass. Combined-mode upgrade, incident, retain/delete, and uninstall recovery are not yet specified. |
| P8 — Bounded live proof | `CHANGES_REQUIRED` | The two-person capsule/profile/reboot/kill suite is strong. Add a clean combined-mode install and recovery proof plus same-account-separated rejection. |
| P9 — Optional intelligence | `PASS` | AI remains optional/advisory and outside authorization, mutation, command construction, capture, and validation. |
| P10 — Private alpha | `CHANGES_REQUIRED` | The two-person non-author alpha path is measurable. The selectable personal path needs its own completion, recovery, timing, confidence, and lifecycle evidence before the product can claim it is supported. |

## Re-review condition

Freeze a revised author set after `UX-P0-010` is resolved. The next usability pass may focus on the combined-mode branch but must re-check P0, P3, P6, P7, P8, and P10; mode selection; actor and privilege states; recovery audit; exact lease-to-anchor sequence; runtime unlock; documentation routes; private-alpha tasks/timing; and `HANDOFF_TOPOLOGY_UNSUPPORTED`. If that branch is complete and no regression is introduced, `PASS_WITH_FOLLOW_UP` with only `UX-P0-F03` would be appropriate.
