# Usability and onboarding review: P0 planning baseline

- Reviewed input: pre-commit working tree (repository has no commits yet)
- Frozen file-set SHA-256: `3a637dae8ac48cf7cea7c84ebbec5c9d39cd63a8cd75105f689f5478a7023d98`
- Date: 2026-07-15
- Reviewer: independent usability and onboarding review
- Verdict: `CHANGES_REQUIRED`

## Scope and method

This review covers `README.md`, `AGENTS.md`, the accepted private-App decision, every section of `docs/plans/product-plan.md`, the review and documentation plans, and the research source register. It evaluates whether a supported administrator and operator can understand the product boundary, install it without guessed values, prove first value, recover safely, understand cost and permissions, and remove it without orphaned resources or evidence.

The baseline has no usability `BLOCKER`. It is unusually strong on evidence semantics, optional AI, cost cleanup, and documentation structure. P0 is not yet acceptable because the first executable bootstrap, human permission handoff, scanner failure taxonomy, accessibility target, error/recovery contract, and representative-user acceptance tests are not defined precisely enough to test.

## Primary sources checked

- [Manage Databricks Apps using Declarative Automation Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial)
- [Deploy Bundles and run resources from the workspace](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/workspace-deploy)
- [Add resources to a Databricks App](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/resources)
- [Configure permissions for a Databricks App](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/permissions)
- [Configure App compute resources](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/compute-size)
- [Nielsen Norman usability heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)
- [WCAG 2.2 Understanding documents](https://www.w3.org/WAI/WCAG22/Understanding/)
- [WCAG error identification](https://www.w3.org/WAI/WCAG22/Understanding/error-identification)
- [WCAG status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages)

## Product-plan section matrix

| Product-plan section | Exact evidence | Verdict | Usability review |
|---|---|---|---|
| Outcome | `docs/plans/product-plan.md:8-17` | `PASS` | The plan correctly separates Databricks execution outcome from evidence-capture outcome and prevents false “observable” success. |
| Fixed constraints | `docs/plans/product-plan.md:19-27` | `PASS` | Customer-local operation, read-only planning, no continuous collector, and bounded paid tests are clear user protections. |
| Product boundary: in scope | `docs/plans/product-plan.md:29-42` | `PASS` | Setup, migration, health, investigation, cost, and uninstall readiness form a coherent operator product rather than a parser-only tool. |
| Product boundary: optional/not in scope | `docs/plans/product-plan.md:43-60`; `AGENTS.md:7-12` | `PASS` | Optional AI and rejection of arbitrary commands are explicit and understandable. |
| Target architecture | `docs/plans/product-plan.md:61-78`; `docs/decisions/0001-private-app-bundle.md:17-40` | `PASS_WITH_FOLLOW_UP` | The App/Job/collector/storage split is legible. P4 should turn it into role-oriented navigation and avoid exposing component names as the primary mental model. |
| Identity model | `docs/plans/product-plan.md:80-92` | `CHANGES_REQUIRED` | Runtime identities are listed, but the human installer/resource-owner handoff and minimum privileges for binding existing jobs and a warehouse are not actionable. See `UX-P0-002`. |
| Capture baseline | `docs/plans/product-plan.md:94-104` | `PASS` | Candidate status is visible and avoids promising untested compatibility. |
| Invocation rules | `docs/plans/product-plan.md:106-116` | `PASS` | The product prevents memory-based flags and free-form input; this is the right mistake-proofing boundary. |
| Correlation model | `docs/plans/product-plan.md:117-133` | `PASS` | The immutable attempt crosswalk supports stable deep links and understandable retries/repairs. |
| Evidence priority | `docs/plans/product-plan.md:135-140` | `PASS` | The hierarchy makes later failure explanations defensible. |
| Capture states | `docs/plans/product-plan.md:142-150` | `PASS_WITH_FOLLOW_UP` | The machine states are sound. P4/reference docs must add plain-language labels and always display capture state separately from job state. |
| Regulated data model | `docs/plans/product-plan.md:152-160`; `README.md:7-15` | `PASS` | Safe defaults, restricted diagnostics, and verifiable retention are clear. |
| Installation experience | `docs/plans/product-plan.md:161-188`; `docs/decisions/0001-private-app-bundle.md:33-40` | `CHANGES_REQUIRED` | The post-bootstrap sequence is good, but the user-facing entry artifact and the boundary between pre-App bootstrap and in-App setup are undefined. Scanner access failures are also missing. See `UX-P0-001` and `UX-P0-003`. |
| Delivery parts and review gates | `docs/plans/product-plan.md:190-206` | `CHANGES_REQUIRED` | The slicing is strong, but P4 “accessible” and P10 “resolved usability findings” are not measurable exit criteria. See `UX-P0-004` and `UX-P0-006`. |
| Test strategy: local/CI | `docs/plans/product-plan.md:208-217` | `PASS_WITH_FOLLOW_UP` | Fixture and automated UI coverage is strong but does not replace representative human task testing. |
| Test strategy: staging | `docs/plans/product-plan.md:218-225` | `PASS` | Readiness, denial paths, bounded capture, `finally` cleanup, and a separate inventory assertion are excellent confidence signals. |
| Compatibility fixtures | `docs/plans/product-plan.md:226-228` | `PASS` | The failure coverage supports accurate messages instead of generic failure states. |
| Cost discipline | `docs/plans/product-plan.md:230-238`; `AGENTS.md:40-41` | `PASS_WITH_FOLLOW_UP` | The lifecycle rules are safe. Before P8, each live proof still needs a numerical time/DBU boundary and an explicit post-test App state. See `UX-P0-F01`. |
| Marketplace path | `docs/plans/product-plan.md:240-249` | `PASS` | Marketplace is correctly framed as later distribution and does not complicate the private first journey. |
| Decisions still open | `docs/plans/product-plan.md:251-261` | `PASS_WITH_FOLLOW_UP` | The decisions and evidence deadlines are useful. Add accountable owners when each spike starts, especially authorization and UI foundation. |
| Planning-baseline definition | `docs/plans/product-plan.md:263-273`; `docs/plans/review-process.md:73-120` | `PASS` | Acceptance, resolution, re-review, committed baseline, and no-cloud-mutation conditions are explicit. |

## P0-P10 part matrix

| Part | Verdict | Usability/onboarding acceptance review |
|---|---|---|
| P0 — Product contract | `CHANGES_REQUIRED` | Resolve `UX-P0-001` through `UX-P0-006` before accepting the baseline. |
| P1 — Capture library | `PASS_WITH_FOLLOW_UP` | Validator output must identify the safe field/path, expected contract, observed value/category, impact, and remediation without emitting raw evidence. Add golden tests for those messages. |
| P2 — Collector job | `PASS_WITH_FOLLOW_UP` | Preserve the strong outer-attempt rule. The operator view must distinguish dbt outcome, capture outcome, and collector failure and show the appropriate native run link. |
| P3 — Bundle installer | `CHANGES_REQUIRED` | The plan needs a canonical pre-App entry point, explicit acting identity, resumable stages, privilege routing, and separate stop/uninstall/delete-evidence choices. See `UX-P0-001`, `UX-P0-002`, and `UX-P0-F02`. |
| P4 — App read-only MVP | `CHANGES_REQUIRED` | “Accessible UI” and “failure details” need a normative accessibility target and error/status contract. See `UX-P0-004` and `UX-P0-005`. |
| P5 — Job onboarding | `CHANGES_REQUIRED` | `READY`/`NEEDS_CHANGES`/`UNSUPPORTED` cannot safely represent permission denial or an inspection failure. See `UX-P0-003`. |
| P6 — Controlled actions | `PASS_WITH_FOLLOW_UP` | Before implementation, define the approval summary: bound job, selector, target, acting identity, compute/cost implication, expected writes, cancellation behavior, and approver/run initiator roles. |
| P7 — Security and operations | `PASS_WITH_FOLLOW_UP` | The topics are complete. Uninstall must visibly separate stopping compute, removing product code/config, retaining/exporting evidence, and irreversible verified deletion. |
| P8 — Bounded live proof | `PASS_WITH_FOLLOW_UP` | The cleanup inventory is strong. Add a pre-approved numerical budget and assert the App is stopped and schedules/warehouses are paused or stopped after proof. See `UX-P0-F01`. |
| P9 — Optional intelligence | `PASS` | The core journey is explicitly independent of Genie Code, Genie Agents, MCP, and Preview App telemetry. |
| P10 — Private alpha | `CHANGES_REQUIRED` | Repeatable technical installs alone do not prove usability. Require distinct non-author administrator and operator walkthroughs with measurable task-success criteria. See `UX-P0-006`. |

## Required findings

### UX-P0-001: Define the canonical pre-App bootstrap

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Evidence: `docs/plans/product-plan.md:161-180` calls the entry point a guided installer and then starts with choosing a path and selecting a CLI profile, but it does not identify what the administrator opens or runs before the App exists. `docs/decisions/0001-private-app-bundle.md:35` correctly says installation is more than `bundle deploy`.
- Primary-source evidence: Databricks documents that `bundle deploy` creates or updates the App resource but does not deploy the App onto compute; running the App is a separate stage. Workspace-based Bundle deployment also runs code as the current user, while the plan currently implies a local CLI/profile flow.
- User impact: A first-time installer must infer whether to clone a repository, run a script, initialize a Bundle, open a workspace Git folder, edit YAML, or start in the App. That is hidden prerequisite knowledge at the most consequential step.
- Required change: Select one canonical private-alpha bootstrap and name its executable entry artifact, execution location, supported authentication mode, minimum local/workspace prerequisites, and start/end states. Explicitly split `Bootstrap the product` from `Configure the product in the App`. Mark other deployment paths as deferred alternatives rather than mixing them into the main journey.
- Acceptance conditions:
  1. From a clean supported environment, the documented entry artifact performs or guides profile discovery, explicit workspace selection, read-only checks, change preview, Bundle validation/deployment, App run/deploy, readiness polling, and App URL handoff.
  2. The user does not paste an internal resource ID, construct a path, or edit YAML in the primary path.
  3. Every stage is named and resumable or safely retryable after interruption.
  4. An automated fixture journey and a non-author walkthrough both start from the same documented first action.

### UX-P0-002: Make human roles and prerequisite permissions actionable

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Evidence: `docs/plans/product-plan.md:84-90` describes runtime identities, while the outcome only names a generic administrator and operator. The installer boundary at line 86 says it manages the product Bundle and UC destination but does not explain who can approve binding the selected existing job or warehouse.
- Primary-source evidence: Databricks App resources require the person adding a resource to have `CAN MANAGE` on both the App and resource, even when the App receives a narrower runtime permission. App access permissions and App resource authorization are distinct.
- User impact: An analytics engineer may reach the apply step and discover that a workspace, job, warehouse, or catalog owner must participate. In a regulated organization this creates stalled installs, overbroad temporary grants, and unclear accountability.
- Required change: Add a human-role/prerequisite matrix covering workspace administrator, deployment operator, UC owner, existing-job owner, warehouse owner, dbt project owner, and read-only operator. For each installer stage show the acting identity, minimum privilege, why it is needed, who can grant it, whether roles may be combined, how preflight detects it, and what remains afterward. Resolve whether App resource binding or a different reviewed grant path is canonical for each selected resource.
- Acceptance conditions:
  1. A single-person supported path and a separated-duties path are both explicit.
  2. Missing privilege tests fail before mutation and name the exact resource, required level, responsible role, and next action.
  3. The change plan displays App access grants separately from runtime resource grants.
  4. Handoff proves an operator with only the documented read permission can complete the investigation journey and cannot reach setup or raw diagnostics.

### UX-P0-003: Do not classify access and inspection failures as unsupported jobs

- Classification: `CHANGES_REQUIRED`
- Severity: medium
- Evidence: `docs/plans/product-plan.md:182-188` allows only `READY`, `NEEDS_CHANGES`, and `UNSUPPORTED` scanner results.
- User impact: A missing `CAN_VIEW`, deleted job, transient API failure, or incomplete job response could be presented as an unsupported dbt pattern. The user would get the wrong remediation and may unnecessarily rebuild a valid job.
- Required change: Add an explicit `ACCESS_BLOCKED` and `CHECK_FAILED` result, or define an equally explicit outer scanner-status model that prevents those cases from reaching the compatibility classifier. Reserve `UNSUPPORTED` for a successfully inspected pattern that the product intentionally does not support.
- Acceptance conditions:
  1. Tests independently cover missing permission, missing job, transient/API failure, malformed response, and genuinely unsupported job structure.
  2. Every result has a plain-language label, stable code, safe evidence summary, impact, and next action.
  3. Scanner failure cannot produce a patch or enable Apply.

### UX-P0-004: Make accessibility a normative, testable product requirement

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Evidence: P4 at `docs/plans/product-plan.md:200` requires an “accessible UI,” `docs/plans/review-process.md:142-149` requires accessibility checks, and `docs/plans/documentation-plan.md:128-139` says “WCAG-oriented,” but no conformance target or critical-flow acceptance test is defined.
- User impact: Teams can honestly interpret “accessible” differently, allowing a keyboard-inaccessible installer, silent async status changes, color-only capture states, or errors that are not announced to assistive technology.
- Required change: Set WCAG 2.2 AA as the target for all critical P3-P7 product and documentation journeys, with documented exceptions only through a reviewed decision. Add automated accessibility checks plus keyboard-only and screen-reader smoke tests for installer progress, confirmation, errors, job inventory, run investigation, retention, and uninstall.
- Acceptance conditions:
  1. No critical or serious automated accessibility findings remain.
  2. Every critical journey is completable by keyboard with visible focus and logical order.
  3. Async progress and completion use programmatically determinable status messages without unexpected focus movement.
  4. Errors are identified in text, associated with the affected field or stage, summarized at the top where appropriate, and include a correction suggestion.
  5. Job and capture states are not distinguishable by color alone.

### UX-P0-005: Define the product-wide status and failure-recovery contract

- Classification: `CHANGES_REQUIRED`
- Severity: medium
- Evidence: P4 at `docs/plans/product-plan.md:200` promises “failure details”; `docs/plans/review-process.md:43-46` requires progress and recovery; `docs/plans/documentation-plan.md:61` plans an error-code reference. No required content model links an API failure to an operator-safe UI explanation.
- User impact: Each page can invent a different spinner, error message, retry rule, or diagnostic disclosure. Generic errors undermine the intended zero-guess journey and can expose raw platform text.
- Required change: Add a shared user-facing operation/error contract used by installer, scanner, controlled run, retention, and uninstall endpoints. At minimum it contains operation/stage, safe stable code, plain-language summary, user impact, affected resource by display name, whether anything changed, safe evidence reference, recommended next action, retryability/idempotency, and native Databricks deep link where available. Raw exception, SQL, artifact, and log content remain excluded.
- Acceptance conditions:
  1. API and UI fixture tests cover queued, running, succeeded, partially succeeded, failed-before-mutation, failed-after-mutation, cancelled, timed out, retryable, and non-retryable states.
  2. The UI never converts an unknown state into success and never loses the distinction between job, dbt, collector, and capture outcomes.
  3. Retry is disabled unless the operation is proven idempotent or the UI explains the recovery/rollback step first.

### UX-P0-006: Add representative-user tasks and measurable usability exits

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Evidence: local/CI strategy at `docs/plans/product-plan.md:210-217` covers automated journeys; P10 at lines 205-206 requires installations and “resolved usability findings” but does not identify independent users, tasks, metrics, or a severity threshold. Documentation definition of done at `docs/plans/documentation-plan.md:164-172` mentions a representative walkthrough without defining it.
- User impact: The same developers who know the implementation can complete two installations while first-time administrators and operators still fail at permissions, terminology, recovery, or cleanup.
- Required change: Add a usability-validation table with persona, starting state, critical task, metric, pass threshold, evidence, and target part. Include at least a non-author administrator/deployment operator and a non-author read-only operator; include both new-job and existing-job onboarding before private alpha.
- Acceptance conditions:
  1. Critical tasks include readiness interpretation, change-plan/permission review, first queryable capture, job-versus-capture diagnosis, cost/running-resource check, and stop/uninstall with the correct evidence choice.
  2. Every critical task completes without undocumented help, manually entered internal IDs/paths/YAML, or accidental mutation.
  3. No unresolved high-severity usability finding remains at a part gate; lower-severity findings have an owner and target part.
  4. Record active user time, platform wait time, errors, backtracks, help requests, and time to first queryable evidence separately. Set and approve the private-alpha time-to-value threshold before P3 implementation.
  5. P10 evidence identifies distinct non-author participants and includes the resulting changes or accepted-risk decisions.

## Non-blocking follow-ups

### UX-P0-F01: Require a numerical live-proof budget

- Classification: `PASS_WITH_FOLLOW_UP`
- Severity: medium
- Target: P8
- Evidence: `docs/plans/product-plan.md:230-238` and `AGENTS.md:40-41` require a bounded test and cleanup but intentionally do not set the per-run number.
- Required follow-up: Before any live proof, record maximum elapsed minutes, maximum expected App and warehouse DBUs, warehouse auto-stop setting, schedule state, cancellation deadline, cleanup owner, and final inventory command/output. Label DBU estimates separately from customer-specific currency cost. The default P8 outcome is a stopped App and no active scheduled or temporary compute.

### UX-P0-F02: Separate stop, uninstall, retain/export, and verified deletion

- Classification: `PASS_WITH_FOLLOW_UP`
- Severity: medium
- Target: P3 and P7
- Evidence: uninstall readiness appears at `docs/plans/product-plan.md:39`, and P7 includes export/deletion/uninstall at lines 203-204, but the choices are not yet a defined interaction contract.
- Required follow-up: Design four explicit actions with separate consequences and confirmations: stop App compute; remove product code/configuration; retain or export governed evidence; irreversibly delete and verify evidence. The destructive path must require a review screen and must not be bundled into a generic uninstall button.

## Documentation-plan review

The Diataxis split, page contract, real-capture safety pass, and file-by-file review cadence are `PASS`. Exact evidence is `docs/plans/documentation-plan.md:14-96`, `112-139`, and `164-172`. The planned pages cover the administrator and operator lifecycle well.

Required P0 documentation changes are inherited from the product findings:

- The install tutorial must begin with the canonical bootstrap chosen in `UX-P0-001`, not with an already-running App.
- Permissions reference and readiness how-to must implement the human-role matrix from `UX-P0-002`.
- Error-code and capture-state references must include the labels and recovery contract from `UX-P0-003` and `UX-P0-005`.
- The publishing-stack accessibility review must use the normative target and task tests from `UX-P0-004`.
- The “representative walkthrough” in the documentation definition of done must name the persona, starting state, task, and threshold from `UX-P0-006`.

## Resolution and re-review

- Resolution: pending
- Validation: pending
- Re-review verdict: pending
