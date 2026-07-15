# Usability and onboarding re-review: P0 planning baseline 0.3

- Reviewed input: frozen author-owned planning file set; repository has no commit yet
- Frozen author-input SHA-256: `3e81a74f338000c7441bcb0a643991e958b34f469d71112d81e18b555a5561ae`
- Hash scope: `README.md`, `AGENTS.md`, `docs/index.md`, and all Markdown files under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path; SHA-256 of the sorted per-file SHA-256 records
- Date: 2026-07-15
- Reviewer: independent usability and onboarding second re-review
- Verdict: `PASS_WITH_FOLLOW_UP`
- Cloud mutation: none

## Scope and method

I independently recomputed the frozen hash before reviewing baseline 0.3. It exactly matches the value above and the value recorded in `resolution.md`. I read the author-owned scope, the initial usability review, the first usability re-review, and the resolution ledger. I did not edit author-owned files or previous reports.

This review focuses on the reopened Databricks CLI maturity statement, clean-workstation and secure-storage behavior, scoped P8 cleanup, severity-gate wording, action-role selection and approval, exact installer stages, and regressions across P0-P10. `RESOLVED` in this report means that the planning contract is testable; it does not pre-approve implementation evidence assigned to a later part.

## Current primary sources checked

- [Databricks CLI release types](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/) — versions `1.0.0` and above are GA.
- [Databricks CLI 1.7.0 release](https://github.com/databricks/cli/releases/tag/v1.7.0) — immutable release with a verified-signed commit; explicit `--profile` selection takes precedence over authentication environment variables.
- [Databricks CLI troubleshooting](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/troubleshooting) — CLI `1.0.0+` uses OS-native U2M token storage, but default login can silently fall back to plaintext when secure storage is unavailable; explicit secure mode fails instead.
- [Install or update the Databricks CLI](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/install) — binaries and verification inputs are OS- and architecture-specific.
- [Bundle authentication](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/authentication) — U2M profiles are the recommended attended path, `--profile` selects one explicitly, and omitted selection can use `DEFAULT`.
- [Databricks CLI 1.3.0 release](https://github.com/databricks/cli/releases/tag/v1.3.0) — the Direct engine became GA and the default for new deployments.
- [Direct deployment engine](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/direct) — `bundle.engine: direct` overrides the environment, `bundle plan -o json` provides a detailed diff, and Direct has separate local/remote-state and drift behavior that must be qualified.
- [Manage Apps with Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial) — Bundle resource deployment and App code deployment/start are distinct lifecycle actions.
- [WCAG 2.2 Recommendation](https://www.w3.org/TR/WCAG22/), [Nielsen Norman usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/), and [GOV.UK usability benchmarking](https://www.gov.uk/service-manual/measuring-success/usability-benchmarking-a-website-or-whole-service) — error prevention, status visibility, recovery, full-process accessibility, and representative task evidence remain appropriate review criteria.

## Acceptance criteria reviewed

| Criterion | Result | Independent evidence |
|---|---|---|
| Frozen input is the intended baseline 0.3 | `PASS` | Independent recomputation produced `3e81a74f338000c7441bcb0a643991e958b34f469d71112d81e18b555a5561ae`. |
| `UX-P0-007`: CLI `1.7.0` is correctly GA | `PASS` | The ADR calls it GA and deployment-only; the compatibility plan pins it; readiness says `GA CLI 1.7.0`; the source register says `1.0.0+` and exact `1.7.0` are GA. No author-owned frozen input calls CLI `1.7.0` Preview. Bare version/pin references do not introduce another maturity claim. The historical first re-review retains the old wording only as an immutable finding record. |
| Clean-workstation authentication is safe now | `PASS_WITH_FOLLOW_UP` | The wrapper verifies signatures/checksums, confirms profile/host/current user, passes `--profile` to every child, refuses `DEFAULT`, guides OAuth login, and blocks mutation on plaintext fallback or an unavailable secure store. The exact private-alpha OS/architecture asset matrix remains `UX-P0-F03`, due before P3 wrapper release. |
| Planning and approval precede mutation | `PASS` | The exact order is `SELECT_WORKSPACE`, `PREFLIGHT`, `CHOOSE_RESOURCES`, `BUNDLE_VALIDATE`, `BUNDLE_PLAN`, `APPROVE`, `BUNDLE_DEPLOY`, `APP_DEPLOY`, `APP_READY`, `HANDOFF`. `bundle validate` and machine-readable `bundle plan -o json` precede explicit approval; App deployment/readiness is not conflated with Bundle deployment. |
| Human action-role selection is zero-guess and least privilege | `PASS` | The installer presents eligible individuals by display name, disambiguates selection, never asks for an opaque ID, persists only the opaque ID, discards lookup display/email data, shows the binding-table grant and expiry, and keeps App ACL, runtime grants, role bindings, and ledger grants separate. Missing, expired, revoked, wrong-scope, same-person-production, and untrusted-identity checks fail closed at prepare, approve, and run. |
| Controlled-action approval is ready to enter P6 | `PASS_WITH_FOLLOW_UP` | The policy, identities, separation of duties, no-cache rechecks, ledger, idempotency, and Operation contract are adequate. The exact human approval summary from the prior P6 review note is still not a normative contract. Close `UX-P0-F06` before P6 implementation; no controlled-action UI may ship first and define this afterward. |
| P8 cleanup is scoped and restores prior state | `PASS` | P8 and Cost discipline now require a scoped before/after inventory, distinguish product/test-owned, reused, and unrelated resources, stop/remove everything the proof starts/creates, restore reused resources to their approved prior state, and never stop unrelated compute. This resolves `UX-P0-F04`; live evidence remains the P8 gate. |
| Severity gate is consistent | `PASS` | P10, Usability validation, and the global part rule all use “no unresolved high or critical usability finding”; lower findings require an owner and target part. No author-owned frozen input retains “high-severity” as the normative gate. This resolves `UX-P0-F05`. |
| P0-P10 planning contracts have not regressed | `PASS_WITH_FOLLOW_UP` | The complete matrix below retains the previously accepted capture, scanner, accessibility, operation, lifecycle, optional-AI, and measurement boundaries. Only the already bounded workstation follow-up and the explicit optional-P6 approval-summary gate remain. |

## Disposition of prior findings and follow-ups

| Finding | Disposition in baseline 0.3 | Re-review result |
|---|---|---|
| `UX-P0-001` | Canonical signed wrapper, one command, secure profile selection, named resumable stages, separate App deployment/readiness, and URL handoff | `RESOLVED`; P3 implementation evidence pending |
| `UX-P0-002` | Eight human roles, prerequisite owners, residual access, separated duties, display-name grant requests, and distinct ACL/resource/action-role presentation | `RESOLVED`; selection usability passes |
| `UX-P0-003` | Five scanner outcomes; only `NEEDS_CHANGES` may propose a patch | `RESOLVED` |
| `UX-P0-004` | Full-page and complete-process WCAG 2.2 AA contract, manual plus automated evidence, separate CLI text-interface pass | `RESOLVED` |
| `UX-P0-005` | Separate pollable Operation and RFC 9457 Problem contracts with exact statuses, retry/idempotency behavior, mutation state, and safe fields | `RESOLVED` |
| `UX-P0-006` | Named non-author personas, numeric task/safety/ease thresholds, fresh confirmation participants, separate active/platform wait, and common severity gate | `RESOLVED` |
| `UX-P0-F01` | Numerical minute/DBU envelope, cancellation deadline, owner, schedule/auto-stop state, and final inventory | `RESOLVED` at contract level; P8 proof pending |
| `UX-P0-F02` | Stop compute, remove code/configuration, retain/export evidence, and irreversible delete/verify are separate choices | `RESOLVED` at contract level; P7 evidence pending |
| `UX-P0-007` | CLI `1.7.0` is GA, exact pinned, deployment-only, and requalified on update | `RESOLVED` |
| `UX-P0-F03` | OS/architecture, signed asset, verification command, secure-store combination, clean-workstation proof, and unsupported-platform message are explicitly due before P3 release | `OPEN`, non-blocking for P0; hard P3 release gate |
| `UX-P0-F04` | Scoped before/after inventory and reused/unrelated-resource protection added | `RESOLVED` |
| `UX-P0-F05` | One “high or critical” phrase used throughout normative gates | `RESOLVED` |
| Prior P6 approval-summary note | Policy is resolved; the user-facing approval summary is not yet enumerated | Formalized as `UX-P0-F06` below |

## Focused journey findings

### `UX-P0-F03`: publish and test the private-alpha workstation matrix

- Classification: `PASS_WITH_FOLLOW_UP`
- Severity: medium
- Owner: P3 Bundle-installer owner
- Target: before any P3 wrapper asset is released or documented as supported
- Current safety: The regulated path already fails before mutation when secure storage is unavailable or plaintext, and P0 ships no installer asset. This follow-up therefore does not defer a current mutation-safety requirement.
- Acceptance:
  1. Name each supported OS version and architecture, wrapper asset, embedded CLI asset, shell/browser prerequisite, signature/checksum command, and OS-native secure-store backend.
  2. Give unsupported platforms a stable preflight code and non-mutating recovery message.
  3. Test signature/checksum verification, no-profile recovery, explicit profile propagation, secure-store success/failure, resume, App URL handoff, and uninstall from a clean instance of every claimed combination.

### `UX-P0-F06`: freeze the controlled-action approval summary before P6 implementation

- Classification: `PASS_WITH_FOLLOW_UP`
- Severity: medium
- Owner: P6 controlled-actions owner, with usability re-review
- Target: before the first P6 prepare/approve/run UI or API is accepted
- Current journey boundary: Controlled actions are optional P6 scope. The current private install, fixture/real capture proof, and read-only investigation journey do not require them. If P6 is started, this is an entry gate, not a post-release improvement.
- Evidence: `product-plan.md` specifies individual bindings, scope, expiry, separation of duties, prepare/approve/run rechecks, ledger fields, and asynchronous status. It does not yet enumerate what the initiator and approver must see and confirm as one immutable request summary.
- User impact: Without one summary contract, the UI can collect a valid approval while hiding the selected Job, execution identity, selector, compute/cost consequence, expected writes, or cancellation behavior. The approver may authorize a materially different action than the initiator prepared.
- Acceptance:
  1. Prepare produces an immutable, expiring request with a digest and shows action/environment, bound Job by display name, approved selector, initiator, required approver, platform caller, actual Job run-as identity, compute/running-cost implication, expected writes, cancellation/reconciliation behavior, and idempotency/retry consequence.
  2. Approve shows the same digest and summary, identifies every change since preparation, and requires an explicit decision; production self-approval is unavailable and rejected by the API.
  3. Run revalidates the request digest, binding revision/scope/expiry/revocation, distinct production actors, and bound Job. A stale or changed request fails closed and requires a new preparation.
  4. Denial, expiry, revocation, same-person rejection, approval, run, cancellation, and idempotent retry have plain-language states, stable codes, safe ledger evidence, and no arbitrary parameters or internal IDs in ordinary UI.
  5. A non-author initiator/approver task test proves that both people can state what will run, as whom, where, at what compute/cost consequence, what it writes, and what cancellation does before approving.

## Exact installer-stage review

The stage sequence is coherent and complete for the chosen local-wrapper path:

```text
SELECT_WORKSPACE
PREFLIGHT
CHOOSE_RESOURCES
BUNDLE_VALIDATE
BUNDLE_PLAN
APPROVE
BUNDLE_DEPLOY
APP_DEPLOY
APP_READY
HANDOFF
```

The plan provides a safe user meaning for every transition: select and confirm identity; perform read-only readiness; choose display-name resources; validate; compute the Direct-engine JSON diff; explicitly approve; mutate Bundle resources; deploy/start App code; wait for readiness; return the URL and resumable record. Retry is installation-ID based, successful non-idempotent mutations are not repeated, and failure output identifies changed resources, remaining stages, running state, and the exact resume or cleanup action.

`APPROVE` here is installation-plan approval, while P6 also has an action-approval concept. The Operation `kind` and stage context must keep those labels distinguishable in implementation and documentation; this is covered by the existing stable-operation and documentation contracts and is not a new P0 finding.

## P0-P10 no-regression matrix

These verdicts assess the adequacy of the baseline 0.3 plan. They do not pre-approve unimplemented code, documentation, accessibility evidence, or live tests.

| Part | Second re-review verdict | Usability/onboarding result |
|---|---|---|
| P0 — Product contract | `PASS_WITH_FOLLOW_UP` | `UX-P0-007`, scoped cleanup, and severity wording are resolved. `F03` and optional-P6 `F06` are explicit later-part gates and do not defer the current P0 journey. |
| P1 — Capture library | `PASS_WITH_FOLLOW_UP` | No regression in fail-closed validation. P1 must still prove safe field/category/impact/remediation messages without returning raw evidence. |
| P2 — Collector and reconciliation | `PASS_WITH_FOLLOW_UP` | Distinct Job/dbt/collector/capture outcomes, bounded recovery, denial, cancellation, timeout, and safe deep-link requirements remain testable at P2. |
| P3 — Bundle installer | `PASS_WITH_FOLLOW_UP` | Exact stages, planning before mutation, explicit profile propagation, secure-store fail-closed behavior, resumability, and App handoff pass. Close `UX-P0-F03` before release. |
| P4 — App read-only MVP | `PASS` | Curated-only access, full-scope WCAG 2.2 AA, status/recovery, cost confidence, and distinct outcomes remain intact. |
| P5 — Job onboarding | `PASS` | Five scanner states, source-controlled proposed patch, semantic-change review, rollback, and no direct default mutation remain intact. |
| P6 — Controlled actions | `PASS_WITH_FOLLOW_UP` | Authorization and ledger policy are strong. Close `UX-P0-F06` before accepting the first prepare/approve/run implementation. |
| P7 — Security and operations | `PASS_WITH_FOLLOW_UP` | Separate lifecycle actions, role review/revocation, orphan prevention, and deletion verification remain explicit; implementation evidence is still a P7 gate. |
| P8 — Bounded live proof | `PASS` | The previous cleanup ambiguity is resolved by scoped pre/post inventory, ownership classification, restoration of reused state, and protection of unrelated compute. |
| P9 — Optional intelligence | `PASS` | AI remains advisory and optional; no AI feature constructs or authorizes an executable dbt action, and the core journey works with AI disabled. |
| P10 — Private alpha | `PASS` | The wording now consistently excludes unresolved high or critical findings, while personas, tasks, timing, safety, ease, and fresh confirmation evidence remain measurable P10 gates. |

## Documentation-plan re-review

The documentation plan remains `PASS`. It carries the canonical pre-App action, installer platforms/secure storage, human/action roles, exact stages, scoped cleanup, distinct lifecycle choices, full-process accessibility, and real sanitized evidence into independent subject, Diataxis, FastAPI-style, security, usability/accessibility, and rendered-site passes.

The future `reference/installer-platforms-and-secure-storage.md` must close `UX-P0-F03`. The future `reference/action-roles-and-approval.md` must close `UX-P0-F06` before controlled actions are documented as usable. These are appropriately separated reference contracts; the relevant task guides must still show consequences and confirmation in context.

## Final verdict

`PASS_WITH_FOLLOW_UP` for frozen baseline 0.3.

The current P0 install, capture-proof, read-only investigation, recovery, cost, and lifecycle journey has no unresolved blocking usability requirement. Databricks CLI `1.7.0` is correctly treated as GA throughout the author-owned baseline, secure storage fails closed, the exact installer sequence plans before mutation, P8 cleanup is scoped, and the “high or critical” gate is consistent. `UX-P0-F03` is a hard gate before publishing P3 wrapper support; `UX-P0-F06` is a hard gate before implementing optional P6 controlled actions. Neither may be postponed past its named part. No Azure or Databricks resource was created, started, stopped, or deleted by this review.
