# Usability and onboarding re-review: P0 planning baseline 0.2

- Reviewed input: frozen author-owned planning file set; repository has no commit yet
- Frozen author-input SHA-256: `483a3a4e1ccfe063a8af07a15483ac48abf5d090c44f1817a4cee8e810483965`
- Hash scope: `README.md`, `AGENTS.md`, `docs/index.md`, and all Markdown files under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path; SHA-256 of the sorted per-file SHA-256 records
- Date: 2026-07-15
- Reviewer: independent usability and onboarding re-review
- Verdict: `CHANGES_REQUIRED`
- Cloud mutation: none

## Scope and method

This re-review independently read the current `README.md`, `AGENTS.md`, `docs/index.md`, every decision, plan, and research Markdown file, the initial usability review, and the resolution ledger. The frozen hash was recomputed and matched before review. Author-owned files were not edited.

The review checks the complete administrator and operator journey, every P0-P10 delivery part, the resolution of `UX-P0-001` through `UX-P0-006` and `UX-P0-F01`/`UX-P0-F02`, and the specific revised contracts for bootstrap, authentication, accessibility, asynchronous operations, usability measurement, lifecycle safety, and scanner outcomes.

Baseline 0.2 resolves all six original required usability findings at the planning-contract level. One new current-source accuracy defect prevents P0 acceptance: three frozen statements still label pinned Databricks CLI `1.7.0` Public Preview, while current official Azure Databricks documentation classifies every CLI version `1.0.0` and above as GA. This is conservative rather than privilege-widening, but it gives a regulated administrator the wrong product-maturity and exception-approval information.

## Current primary sources checked

- [Databricks CLI release types](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/) — versions `1.0.0` and above are GA.
- [Databricks CLI 1.7.0 release](https://github.com/databricks/cli/releases/tag/v1.7.0) — immutable release with a verified-signed commit; an explicitly selected profile now takes precedence over authentication environment variables.
- [Install or update the Databricks CLI](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/install) — platform/architecture-specific binaries and checksum verification.
- [Bundle authentication](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/authentication) — OAuth U2M and configuration profiles are the recommended attended path; omitted profile selection may use `DEFAULT`.
- [Databricks CLI authentication commands](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/reference/auth-commands) — profile validation, host/identity description, and `current-user me` behavior.
- [Databricks CLI troubleshooting](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/troubleshooting) — CLI `1.0.0+` secure token storage and the possible plaintext fallback when secure storage is not explicitly required.
- [Manage Apps with Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial) — Bundle deployment and App code deployment/start are distinct stages; Bundle summary exposes the App URL.
- [WCAG 2.2 Recommendation](https://www.w3.org/TR/WCAG22/) and [Understanding conformance](https://www.w3.org/WAI/WCAG22/Understanding/conformance.html) — Level AA includes every A/AA criterion, full pages, complete processes, and automated plus human evaluation.
- [RFC 9457 Problem Details](https://www.rfc-editor.org/rfc/rfc9457.html) and [RFC 9110: 202 Accepted](https://www.rfc-editor.org/rfc/rfc9110.html#name-202-accepted) — safe standardized errors and status-monitor semantics.
- [Microsoft Azure REST API Guidelines](https://github.com/microsoft/api-guidelines/blob/vNext/azure/Guidelines.md) — operation location, idempotency, polling, retry, and terminal-state conventions.
- [GOV.UK usability benchmarking](https://www.gov.uk/service-manual/measuring-success/usability-benchmarking-a-website-or-whole-service) — relevant tasks, completion, time, abandonment/false success, ease/confidence, and no more than five tasks per participant as a rule of thumb.

## Original-finding resolution

`RESOLVED` below means that the planning contract now contains a testable requirement. It does not substitute for the implementation evidence assigned to P1-P10.

| Finding | Outcome | Revised evidence and independent result |
|---|---|---|
| `UX-P0-001` | `RESOLVED` | `docs/plans/product-plan.md:239-263` selects the signed wrapper and one command, embeds the exact CLI, confirms profile/host/current user, propagates explicit `--profile`, handles no-profile login, fails closed on insecure token storage, separates Bundle/App stages, names resumable stages, defines checkpoint retention, supplies accessible output modes, and hands off the App URL. The documentation starts from the same action at `docs/plans/documentation-plan.md:114`. P3 still needs the non-blocking workstation package matrix below. |
| `UX-P0-002` | `RESOLVED` | `docs/plans/product-plan.md:86-120` separates four runtime identities, seven human roles, acting stages, minimum permissions, grant owners, residual access, combined/separated-duty paths, missing-grant rechecks, and App ACL versus resource-grant presentation. |
| `UX-P0-003` | `RESOLVED` | `docs/plans/product-plan.md:274-282` adds `ACCESS_BLOCKED` and `CHECK_FAILED`, reserves `UNSUPPORTED` for successfully inspected unsupported patterns, requires independent failure fixtures, and prevents scanner failure from enabling Apply or generating a patch. |
| `UX-P0-004` | `RESOLVED` | `docs/plans/product-plan.md:322` and `docs/plans/documentation-plan.md:160,182,196` scope the entire App and rendered site as full pages and complete processes, require zero known A/AA failure, combine automation with keyboard/screen-reader evaluation, test the required states and responsive/semantic behavior, reserve “conforms” for a fully passing scope, and give the CLI a separate terminal-accessibility contract. |
| `UX-P0-005` | `RESOLVED` | `docs/plans/product-plan.md:288-292` defines separate pollable Operation and RFC 9457 Problem contracts, exact statuses and fields, `202`/location/retry behavior, idempotency and conflict semantics, mutation state, safe recovery, and forbidden raw content. |
| `UX-P0-006` | `RESOLVED` | `docs/plans/product-plan.md:341-352` commits four non-author personas plus fresh confirmation participants, at most five tasks, 100% safety-critical success, zero safety failures/false success/abandonment, numeric active-time thresholds, separate platform-wait measurement, ease/confidence thresholds, and no unresolved high or critical usability finding. The sample is correctly described as formative rather than statistically generalizable. |
| `UX-P0-F01` | `RESOLVED`; P8 evidence pending | `docs/plans/product-plan.md:354-363` now requires a pre-approved minute/DBU envelope, auto-stop and schedule state, cancellation deadline, cleanup owner, final inventory command, stopped/paused default test end state, and DBU-versus-currency labeling. |
| `UX-P0-F02` | `RESOLVED`; P3/P7 evidence pending | `docs/plans/product-plan.md:265-272` and the separate pages/stages at `docs/plans/documentation-plan.md:47-50,147-148,173-174` distinguish stopping App compute, removing code/configuration, retaining/exporting evidence, and irreversible verified deletion. |

## Focused contract checks

### Canonical bootstrap and regulated authentication

The revised bootstrap is coherent and testable. It begins before the App exists, has one primary command, requires an explicitly selected and re-confirmed workspace identity, avoids `DEFAULT`, and includes the separate App deployment/start stage required by Databricks. The secure-store rule correctly closes the documented CLI plaintext-fallback path. The profile behavior also benefits from the pinned `1.7.0` change that makes explicit profile selection take precedence over ambient authentication environment variables.

The primary path remains zero-guess for Databricks resource IDs, paths, YAML, and dbt flags. `--plan`, `--json`, `--no-color`, append-only progress, safe failure state, and remote-state revalidation make both attended use and assistive-terminal use reviewable.

### Full-scope accessibility

The revised wording is stronger than the initial acceptance condition. It no longer treats an automated severity scan or isolated critical components as WCAG conformance. The entire App and rendered documentation scope must meet Level A and AA criteria across full pages/states and complete processes, with manual keyboard and representative screen-reader evaluation. The CLI is correctly evaluated as a separate text interface instead of receiving a misleading WCAG web-content claim.

### Operation, error, and recovery behavior

Operation and Problem are now distinct, allowlisted contracts. The statuses include partial success and timeout, the API supports status monitoring and safe retry decisions, and the user receives mutation state plus recovery rather than a generic spinner or raw Databricks exception. Job, dbt, collector, and capture outcomes also remain separate elsewhere in the plan.

### Scanner and lifecycle behavior

The five scanner states prevent access or API failures from masquerading as unsupported dbt patterns. Only `NEEDS_CHANGES` may produce a proposed patch, and the plan explicitly warns that migration to `build` can alter semantics. Stop, removal, evidence retention/export, and verified deletion are separate actions rather than one destructive “uninstall” control.

### Measurable first-time use

The provisional thresholds are explicit product gates, not presented as universal research standards. Active user time is separated from platform wait, which prevents slow Databricks provisioning from masking interaction difficulty. Safety-critical outcomes are evaluated per participant rather than hidden by an average.

## New required finding

### UX-P0-007: Correct the Databricks CLI maturity claim

- Classification: `CHANGES_REQUIRED`
- Severity: medium
- Affected evidence: `docs/decisions/0001-private-app-bundle.md:45`, `docs/plans/product-plan.md:286`, and `docs/research/source-register.md:12` state that pinned CLI `1.7.0` is Public Preview.
- Primary-source evidence: The current official [Azure Databricks CLI release-type page](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/) says versions `1.0.0` and above are GA. The first-party [v1.7.0 release](https://github.com/databricks/cli/releases/tag/v1.7.0) is immutable and points to a verified-signed commit.
- User impact: A regulated customer can reject the install, request an unnecessary Preview exception, or receive a misleading readiness result because the product overstates the deployment tool's maturity risk. It also violates this repository's own current-source policy.
- Required change: Mark CLI `1.7.0` GA everywhere while retaining the exact binary/checksum pin, deployment-only boundary, secure-storage requirement, and requalification-on-update rule. Do not change the independently assessed maturity of Bundle direct deployment, App user authorization, audit-system-table enrichment, App telemetry, or AI features.
- Acceptance conditions:
  1. The ADR, product plan, source register, readiness output contract, and future installer/help copy identify `Databricks CLI 1.7.0` as `GA, exact pinned deployment-only dependency`.
  2. No frozen source claims that CLI `1.0.0+` is Public Preview.
  3. The source register cites both the current official release-type page and the immutable `1.7.0` release.
  4. Pinning, signature/checksum verification, secure U2M storage, explicit profile confirmation, and update requalification remain unchanged.

## Non-blocking follow-ups

### UX-P0-F03: Publish the private-alpha workstation package matrix

- Classification: `PASS_WITH_FOLLOW_UP`
- Severity: medium
- Target: P3 before wrapper release
- Evidence: `docs/plans/product-plan.md:241-249` says “supported workstation” and embeds a platform-specific CLI but does not yet name the private-alpha OS/version/architecture combinations or wrapper asset names.
- Acceptance: Select at least one supported private-alpha OS/architecture and secure-store combination; publish the exact signed asset, verification command, shell/browser prerequisites, profile recovery, and unsupported-platform message. Test every claimed asset from a clean workstation. Databricks publishes distinct macOS, Linux, and Windows architecture assets, so one generic binary claim is insufficient.

### UX-P0-F04: Make P8 cleanup a scoped before/after inventory

- Classification: `PASS_WITH_FOLLOW_UP`
- Severity: medium
- Target: P8
- Evidence: `docs/plans/product-plan.md:308,359-363` requires no active warehouse after proof while also preferring an existing warehouse. An unqualified global-zero assertion could fail because of unrelated resources or encourage stopping a pre-existing shared warehouse.
- Acceptance: Record pre-test state, identify product/test-owned versus reused resources, stop every resource started or created by the proof, restore reused resources to their approved pre-test state, and compare a post-test inventory against the baseline. Cleanup must never stop unrelated customer compute.

### UX-P0-F05: Use one severity gate phrase everywhere

- Classification: `PASS_WITH_FOLLOW_UP`
- Severity: low
- Target: P10 before task evidence is accepted
- Evidence: `docs/plans/product-plan.md:310,352` says no unresolved “high-severity” finding, while the normative gate at line 343 correctly says no high **or critical** finding.
- Acceptance: Every part table, usability rule, and documentation gate uses “no unresolved high or critical usability finding”; lower findings retain an owner and target part.

## P0-P10 re-review matrix

These verdicts assess whether baseline 0.2 provides an adequate plan for each future part. They do not pre-approve unimplemented code, UI, documentation, or live evidence.

| Part | Re-review verdict | Usability/onboarding result |
|---|---|---|
| P0 — Product contract | `CHANGES_REQUIRED` | The core journey and all original UX findings are resolved, but `UX-P0-007` must correct the current-source maturity claim before baseline acceptance. |
| P1 — Capture library | `PASS_WITH_FOLLOW_UP` | The fail-closed field contract is strong. P1 fixtures must turn validator failures into safe code/path-or-category/impact/remediation without returning raw evidence. |
| P2 — Collector and reconciliation | `PASS_WITH_FOLLOW_UP` | Attempt recovery, exactly-once behavior, and distinct Job/dbt/collector/capture outcomes are clear; implementation must prove each denial/cancellation/timeout state and deep link. |
| P3 — Bundle installer | `PASS_WITH_FOLLOW_UP` | Canonical bootstrap, secure authentication, human roles, planning-before-mutation, resumability, and App handoff pass. Close `UX-P0-F03` before publishing wrapper assets. |
| P4 — App read-only MVP | `PASS` | The plan now has full-scope WCAG wording, safe asynchronous status/error behavior, curated-only access, and distinct outcomes. Actual accessibility and authorization evidence remains a P4 gate. |
| P5 — Job onboarding | `PASS` | Five scanner states, proposed-patch-only behavior, semantic-change review, approval gating, and rollback are testable and safe. |
| P6 — Controlled actions | `PASS_WITH_FOLLOW_UP` | Actor correlation, narrow authorization, idempotency, and Operation status are sound. The implemented approval screen must show bound Job, selector, acting principal, cost/compute implication, writes, cancellation behavior, and approver/run-initiator roles. |
| P7 — Security and operations | `PASS_WITH_FOLLOW_UP` | Lifecycle choices are correctly separate. P7 must prove distinct authorization/confirmation, recovery limits, orphan-free removal, and verified deletion. |
| P8 — Bounded live proof | `PASS_WITH_FOLLOW_UP` | Numerical envelope and unconditional cleanup are present. Close `UX-P0-F04` so the inventory proves no test-created activity remains without touching unrelated resources. |
| P9 — Optional intelligence | `PASS` | AI remains advisory and optional; the complete install, capture, investigation, and operation path works with it disabled. |
| P10 — Private alpha | `PASS_WITH_FOLLOW_UP` | Personas, tasks, numeric thresholds, fresh confirmation users, and severity gates are measurable. Execute the sessions and normalize the wording through `UX-P0-F05`. |

## Documentation-plan re-review

The revised Diataxis architecture remains `PASS`. It now starts before the App exists, carries the role/grant model, scanner and operation contracts, complete WCAG scope, measurable participant walkthroughs, and separate lifecycle pages into documentation gates. Subject, information-architecture, FastAPI-style, security/compliance, usability/accessibility, and rendered-site passes remain appropriately independent.

The only current P0 documentation blocker is inherited from `UX-P0-007`: maturity labels and readiness/help copy must not describe CLI `1.7.0` as Preview. The wrapper-platform matrix, scoped cleanup proof, and severity wording are correctly bounded later-part follow-ups.

## Final verdict

`CHANGES_REQUIRED` for frozen baseline 0.2.

All original required usability findings are resolved at the planning-contract level, and both original non-blocking follow-ups now have explicit delivery requirements. Correct `UX-P0-007`, recompute the author-input hash, and request a focused usability re-review of the maturity wording. No Azure or Databricks resource was created or started by this review.
