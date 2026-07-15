# Diátaxis information-architecture review: P0 planning baseline 0.4

- Reviewed input: frozen author-owned planning file set; repository has no commit yet
- Frozen author-input SHA-256: `8504d49ed1397e218a5760885673c87458d4ecd16d60936191ea0a2d89f48c98`
- Hash scope: `README.md`, `AGENTS.md`, `docs/index.md`, and all Markdown files under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path; SHA-256 of the sorted per-file SHA-256 records
- Date: 2026-07-15
- Reviewer: independent Diátaxis information-architecture reviewer
- Verdict: `CHANGES_REQUIRED`
- Cloud mutation: none

## Scope and method

I independently recomputed the frozen author hash before reviewing. It exactly matches the value above and the focused third re-review input recorded in `resolution.md`.

I reviewed `README.md`, `AGENTS.md`, `docs/index.md`, the product plan, documentation plan, review process, architecture decision, source register, review-record rules, resolution ledger, and relevant specialist review history. I did not edit an author-owned file or a previous review report.

This review judges the P0 documentation planning contract. It does not require future D1-D6 pages, rendered navigation, screenshots, production captures, or live task-test evidence to exist now when the plan already assigns that proof to a later gate. It does require the plan to place and name the proposed pages coherently, define the journeys and navigation that D0 must produce, and give each later page an unambiguous stage and review gate.

## Current primary sources checked

All sources below are the current official Diátaxis site, checked on 2026-07-15:

- [Diátaxis](https://diataxis.fr/) — the four documentation needs are distinct but related; the approach concerns content, architecture, and form.
- [The compass](https://diataxis.fr/compass/) — action versus cognition and acquisition versus application determine the appropriate mode.
- [Tutorials](https://diataxis.fr/tutorials/) — a tutorial is a safe, reliable, learning-oriented experience with one guided path, concrete steps, and visible results.
- [Tutorials and how-to guides](https://diataxis.fr/tutorials-how-to/) — a tutorial serves study in a controlled setting; a how-to serves real work and may branch around real-world conditions.
- [How-to guides](https://diataxis.fr/how-to-guides/) — a how-to is organized around one human goal or problem and contains action rather than teaching or reference material.
- [Reference](https://diataxis.fr/reference/) — reference neutrally describes the machinery and should mirror its logical structure rather than instruct the reader through a task.
- [Explanation](https://diataxis.fr/explanation/) — explanation develops understanding, context, tradeoffs, and reasons without becoming a procedure or technical catalogue.
- [Diátaxis in complex hierarchies](https://diataxis.fr/complex-hierarchies/) — home and category landing pages provide overviews; long lists should be grouped; complex products may add hierarchy while keeping modes distinct.
- [Diátaxis as a guide to work](https://diataxis.fr/how-to-use-diataxis/) — documentation improves through small, responsive iterations rather than creating an empty four-box scheme.

## Acceptance criteria reviewed

| Criterion | Result | Independent evidence |
|---|---|---|
| Frozen input is the intended baseline 0.4 | `PASS` | Independent recomputation produced `8504d49ed1397e218a5760885673c87458d4ecd16d60936191ea0a2d89f48c98`. |
| Four reader needs are explicitly recognized | `PASS` | The plan defines tutorials as learning-oriented, how-to guides as goal-oriented, reference as lookup, and explanation as concept/tradeoff material. |
| Every proposed page has a mode-consistent placement and name | `CHANGES_REQUIRED` | The tutorial entry points overlap the production bootstrap task, two reference names combine lookup with recovery action, and two destructive/identity how-to names combine outcomes the product contract says must remain separate. |
| One progressive route exists from pre-App bootstrap to evidence, investigation, recovery, and removal | `CHANGES_REQUIRED` | All required subjects exist, but the plan does not yet freeze one ordered learning route, one operational route, or a lifecycle chooser that resolves the overlapping stop/remove/export/delete/uninstall pages. |
| Each audience can find its next task without understanding the repository structure | `CHANGES_REQUIRED` | D0 names an audience/task inventory but does not define required audience entry points, task routes, category landing pages, or subgroup navigation. |
| Optional P6, P9, and future Marketplace content cannot be mistaken for the base product | `CHANGES_REQUIRED` | Base tutorial separation is good, but D6 combines three independently governed tracks under one output and gate. |
| Page contract preserves task/reference/explanation boundaries | `PASS` | Outcome, audience, prerequisites, safety, steps, expected output, proof, recovery, cleanup, and related conceptual material are explicit; reference and explanation contracts are separately stated. |
| Review cadence keeps architecture, prose, security, usability, and rendering independent | `PASS_WITH_CLARIFICATION` | The six passes and material-edit re-review are strong. D2-D6 must explicitly say their stage-specific gate is additional to, not a replacement for, the universal per-file passes. |
| D0-D6 stages cover and gate every planned page | `CHANGES_REQUIRED` | Several page families have no explicit stage assignment, and D6 has incompatible controlled-action, AI, and Marketplace acceptance evidence in one row. |
| Future implementation evidence is not incorrectly treated as a P0 defect | `PASS` | Real captures, rendered accessibility, non-author walkthroughs, clean-workstation proofs, and destructive-path/live proofs are already later gates and are not findings here. |

## Page-by-page placement audit

`PASS` means the proposed mode and name are sound at planning level. `CONDITIONAL` means the placement is sound only under the boundary stated here. `CHANGE` maps to a finding below.

### Tutorials

| Proposed page | Result | IA evidence |
|---|---|---|
| `tutorials/understand-the-product.md` | `CHANGE` | “Understand” serves cognition. Make it the explicitly named tutorial landing page or move it to explanation; do not present a conceptual overview as a practical lesson. |
| `tutorials/install-a-private-development-instance.md` | `CHANGE` | Its title promises the same real-work outcome as `how-to/bootstrap-the-private-app.md`. It can be a chapter only inside one controlled fixture-backed learning experience with a distinct study purpose. |
| `tutorials/observe-your-first-dbt-run.md` | `CONDITIONAL` | Appropriate as an ordered tutorial chapter using guaranteed fixtures and visible evidence; the optional real-customer run must not branch the required lesson. |
| `tutorials/investigate-your-first-failure.md` | `CONDITIONAL` | Appropriate as the next controlled lesson chapter with a packaged failure and guaranteed recovery. |
| `tutorials/stop-and-clean-up-the-tutorial.md` | `CONDITIONAL` | Appropriate as the mandatory final safety chapter of the same tutorial, not as the production lifecycle procedure. |

### How-to guides

| Proposed page | Result | IA evidence |
|---|---|---|
| `how-to/check-workspace-readiness.md` | `PASS` | One administrator goal before mutation. |
| `how-to/bootstrap-the-private-app.md` | `PASS` | Canonical real-work private deployment procedure. |
| `how-to/resolve-a-missing-prerequisite.md` | `CHANGE` | The outcome is too broad for one guide across different owners and grants; use it as a prerequisite-recovery landing page or split it by stable preflight condition. |
| `how-to/create-an-observable-dbt-job.md` | `PASS` | Clear new-job owner goal. |
| `how-to/connect-an-existing-dbt-job.md` | `PASS` | Clear migration goal distinct from new-job creation. |
| `how-to/verify-and-apply-an-approved-direct-plan.md` | `PASS` | Clear deployment-operator task with an approval boundary. |
| `how-to/review-and-apply-a-bundle-patch.md` | `CONDITIONAL` | Keep only if its user goal and input differ explicitly from the saved Direct-plan apply and dbt source-patch journeys. |
| `how-to/configure-retention.md` | `PASS` | Clear governance task. |
| `how-to/grant-operator-access.md` | `PASS` | Clear handoff task; it should link to neutral role/grant reference. |
| `how-to/investigate-capture-failure.md` | `PASS` | Clear symptom-based operator task. |
| `how-to/reconcile-a-missing-attempt.md` | `PASS` | Clear recovery goal. |
| `how-to/investigate-dbt-failure.md` | `PASS` | Clear operator task distinct from capture failure. |
| `how-to/upgrade.md` | `PASS` | Clear lifecycle task. |
| `how-to/roll-back.md` | `PASS` | Clear recovery task. |
| `how-to/export-and-delete-evidence.md` | `CHANGE` | Export/retain and irreversible deletion are separate decisions in the product contract and must not share one task title or confirmation flow. |
| `how-to/stop-the-app.md` | `PASS` | Correctly isolates stopping billed App compute. |
| `how-to/remove-code-and-configuration.md` | `PASS` | Correctly isolates removal from data disposition. |
| `how-to/uninstall.md` | `CONDITIONAL` | Appropriate only if it begins with an explicit lifecycle-choice map and states whether governed evidence is retained, exported, or separately deleted. |
| `how-to/install-the-optional-genie-code-skill.md` | `CONDITIONAL` | Correct goal-oriented placement, but it belongs only in the P9 optional-AI route and must not imply Genie Agent installation or enforcement. |
| `how-to/enable-optional-controlled-actions.md` | `CONDITIONAL` | Correct P6 entry task if segregated from the base product and P9/Marketplace routes. |
| `how-to/enroll-your-first-browser-profile.md` | `CONDITIONAL` | Correct P6 first-device task with the separate administrator approval handoff. |
| `how-to/approve-an-action-enrollment.md` | `CONDITIONAL` | Correct action-role-administrator task if the title states first actor/role approval rather than a generic browser approval. |
| `how-to/approve-an-additional-browser-profile.md` | `CONDITIONAL` | Correctly distinct from first actor/role enrollment. |
| `how-to/revoke-action-access-and-offboard-an-actor.md` | `CHANGE` | Browser-only revocation and actor-wide offboarding are distinct product outcomes and must have separate guides and verification. |
| `how-to/rotate-the-action-identity-key.md` | `CONDITIONAL` | Correct P6/P7 security operation with migration and fail-closed branches. |

### Reference

| Proposed page | Result | IA evidence |
|---|---|---|
| `reference/support-matrix.md` | `PASS` | Neutral compatibility lookup. |
| `reference/installer-platforms-and-secure-storage.md` | `PASS` | Neutral workstation/platform support lookup. |
| `reference/readiness-checks.md` | `PASS` | Machine-oriented check catalogue; link task recovery outward. |
| `reference/capture-contract.md` | `PASS` | Authoritative product contract. |
| `reference/supported-dbt-commands-and-artifacts.md` | `PASS` | Authoritative command/artifact catalogue. |
| `reference/resolved-dbt-flags-and-paths.md` | `PASS` | Exact resolved values and paths. |
| `reference/dbt-command-templates-and-configuration-conflicts.md` | `PASS` | Exact templates and invalid combinations. |
| `reference/attempt-key.md` | `PASS` | Precise identifier semantics. |
| `reference/artifact-and-log-fields.md` | `PASS` | Precise allowed field catalogue. |
| `reference/capture-states.md` | `PASS` | Precise state model. |
| `reference/observability-tables-and-views.md` | `PASS` | Mirrors the stored/queryable product structure. |
| `reference/bundle-variables-and-targets.md` | `PASS` | Bundle input/target catalogue. |
| `reference/direct-plan-source-and-drift-binding.md` | `PASS` | Exact saved-plan/sidecar contract. |
| `reference/permissions.md` | `CONDITIONAL` | Use as the permissions overview/landing page; otherwise it overlaps the more specific grant references. |
| `reference/human-roles-and-handoffs.md` | `CONDITIONAL` | Keep neutral role, owner, prerequisite, and residual-access definitions here; the act of handoff belongs in `grant-operator-access.md`. |
| `reference/app-access-and-resource-grants.md` | `PASS` | Exact App ACL/resource-grant distinction. |
| `reference/action-roles-and-approval.md` | `PASS` | Exact P6 role/approval contract. |
| `reference/action-identity-and-browser-enrollment.md` | `PASS` | Exact P6 identity/device model. |
| `reference/role-administration-job-and-table-grants.md` | `PASS` | Mirrors the fixed Job and grant machinery. |
| `reference/action-identity-errors-and-recovery.md` | `CHANGE` | Keep codes, states, and retryability in reference; move recovery actions to symptom-based how-to guides. |
| `reference/app-pages-and-api.md` | `PASS` | Product/UI/API lookup. |
| `reference/operation-status-and-recovery.md` | `CHANGE` | Operation states belong in reference; recovery is a task and needs a how-to destination. |
| `reference/error-codes.md` | `PASS` | Stable error catalogue with links to recovery tasks. |
| `reference/cost-and-running-resources.md` | `PASS` | Precise cost confidence and resource-state lookup. |
| `reference/retention-and-deletion.md` | `PASS` | Neutral retention/deletion policy and semantics, not execution steps. |
| `reference/runtime-egress-and-dependencies.md` | `PASS` | Precise boundary and dependency inventory. |
| `reference/action-ledger-and-audit-enrichment.md` | `PASS` | Exact required/optional audit evidence contract. |
| `reference/glossary.md` | `PASS` | Canonical terminology lookup. |

### Explanation

| Proposed page | Result | IA evidence |
|---|---|---|
| `explanation/why-a-private-app-and-bundle.md` | `PASS` | Reasons, alternatives, and tradeoffs. |
| `explanation/how-dbt-evidence-is-captured.md` | `PASS` | Conceptual system behavior. |
| `explanation/job-outcome-versus-capture-outcome.md` | `PASS` | Builds the reader's mental model. |
| `explanation/why-logs-stay-local-until-closed.md` | `PASS` | Explains a security/operability design choice. |
| `explanation/customer-local-security-model.md` | `PASS` | Context and trust boundary. |
| `explanation/identity-and-permission-model.md` | `PASS` | Conceptual identity/grant relationships. |
| `explanation/why-controlled-actions-are-a-separate-upgrade.md` | `PASS` | Explains optional P6 isolation. |
| `explanation/pseudonymous-actor-and-browser-profile-model.md` | `PASS` | Explains actor/device separation. |
| `explanation/forwarded-identity-and-account-recreation-limitations.md` | `PASS` | Explains a platform limitation and consequence. |
| `explanation/why-a-saved-plan-needs-a-source-and-drift-sidecar.md` | `PASS` | Explains plan integrity design. |
| `explanation/why-collection-uses-a-separate-job.md` | `PASS` | Explains identity and lifecycle separation. |
| `explanation/how-cancellation-reconciliation-works.md` | `PASS` | Conceptual recovery behavior. |
| `explanation/development-versus-production.md` | `PASS` | Appropriate comparison/context page. |
| `explanation/cost-model.md` | `PASS` | Explains attribution limits and confidence. |
| `explanation/optional-ai-boundary.md` | `CONDITIONAL` | Correct explanation placement; publish only in the P9 route with the AI-disabled core boundary visible. |
| `explanation/marketplace-roadmap.md` | `CONDITIONAL` | Correct as explicitly future context; it must not appear in a navigation group of currently available capabilities. |

## Findings

### `DOC-IA-P0-001`: freeze one learning tutorial and separate it from production bootstrap

- Verdict: `CHANGES_REQUIRED`
- Severity: medium
- Affected contract: `docs/plans/documentation-plan.md`, **Tutorials**, **Page contract**, and D1
- Evidence: The plan lists `understand-the-product.md` and `install-a-private-development-instance.md` as tutorials, then says the install tutorial starts with the same signed wrapper and `dbtobsb bootstrap` used for real administration. It also offers a real one-model run from the fixture lesson. Diátaxis distinguishes a controlled learning experience from a guide used to complete real work and says the tutorial path should avoid choices and alternatives.
- User impact: A learner can mistake real workspace mutation for a sandbox lesson, while an administrator searching for the production procedure can land in a teaching sequence. Duplicate installation entry points also make troubleshooting and maintenance diverge.
- Required change and acceptance:
  1. Define one named tutorial learning outcome and one ordered sequence with explicit start state, fixture environment, guaranteed checkpoints, mandatory cleanup, and previous/next navigation.
  2. Treat the five tutorial files as chapters of that one experience or reduce them to one tutorial. Declare the tutorial landing page explicitly.
  3. Move `understand-the-product.md` to explanation/site overview unless it is only the tutorial landing page that introduces the practical lesson.
  4. Keep the required tutorial path fixture-backed and choice-free. A real one-model validation is a linked how-to after the lesson, or a single controlled tutorial step whose safety and successful outcome are guaranteed; it is not an optional branch inside the lesson.
  5. State how `install-a-private-development-instance.md` differs in purpose, environment, and end state from `bootstrap-the-private-app.md`; ordinary search results and page introductions must prevent interchangeability.

### `DOC-IA-P0-002`: keep irreversible evidence and identity outcomes as separate tasks

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: `docs/plans/documentation-plan.md`, **How-to guides** and **Real evidence and screenshots**
- Evidence: The product and evidence contract correctly distinguish retaining/exporting evidence from irreversibly deleting and verifying it, yet the inventory proposes `export-and-delete-evidence.md`. The plan likewise requires browser-only revocation and actor-wide revoke/offboarding evidence but proposes one `revoke-action-access-and-offboard-an-actor.md` guide.
- User impact: Combining reversible preservation with irreversible deletion, or one-device revocation with actor-wide offboarding, creates unsafe titles, ambiguous confirmations, and search results that do not tell the reader which scope will be affected.
- Required change and acceptance:
  1. Replace `export-and-delete-evidence.md` with separate `export-governed-evidence.md` and `delete-and-verify-evidence.md` tasks.
  2. Replace the combined revoke/offboard page with separate browser-profile revocation and actor-wide revoke/offboarding tasks.
  3. Add one lifecycle-choice landing page or decision map that compares stop App compute, remove code/configuration, retain/export evidence, irreversibly delete/verify evidence, and uninstall before linking to the individual procedures.
  4. Make `uninstall.md` state its evidence disposition before mutation and link, rather than inline, the separate export and deletion tasks.
  5. Give each destructive task its own prerequisites, exact affected scope, confirmation, verification, rollback limit, and sanitized proof gate.

### `DOC-IA-P0-003`: remove instruction from reference and replace generic recovery buckets

- Verdict: `CHANGES_REQUIRED`
- Severity: medium
- Affected contract: `docs/plans/documentation-plan.md`, **How-to guides**, **Reference**, and **Page contract**
- Evidence: `operation-status-and-recovery.md` and `action-identity-errors-and-recovery.md` combine product descriptions with actions. `resolve-a-missing-prerequisite.md` names a broad class of different human problems rather than one executable goal. The plan otherwise states that reference pages define types and values and that task pages own recovery.
- User impact: Readers diagnosing a stable code will have to scan procedural text in a catalogue, while administrators with different missing owners/grants are pushed into a generic guide that cannot give one coherent sequence.
- Required change and acceptance:
  1. Rename/scope the references as neutral catalogues, for example `operation-statuses.md` and `action-identity-error-codes.md`, with stable codes, meaning, retryability, and links only.
  2. Add symptom/task how-to pages for interrupted operations and action-identity recovery, or map each state to an already specific enroll/revoke/rotate guide.
  3. Make `resolve-a-missing-prerequisite.md` a landing page grouped by preflight code/responsible owner, or split it into specific task guides.
  4. State that `human-roles-and-handoffs.md` contains only neutral role/handoff definitions; `grant-operator-access.md` owns the handoff procedure.
  5. Define the unique goal of `review-and-apply-a-bundle-patch.md` relative to saved Direct-plan apply and dbt source-patch review, or remove the duplicate entry point.

### `DOC-IA-P0-004`: replace the flat folder inventory with audience- and task-oriented navigation

- Verdict: `CHANGES_REQUIRED`
- Severity: medium
- Affected contract: `docs/plans/documentation-plan.md`, **Information architecture**, D0, and **Publishing stack decision**
- Evidence: The plan proposes 25 how-to guides, 28 reference pages, and 16 explanations in flat folder lists. It does not name a future site home, category landing pages, within-category groups, tutorial sequence navigation, or required audience entry points. The current `docs/index.md` is correctly a planning index but is not a contract for the eventual product-documentation home. Diátaxis recommends overview landing pages and grouping long lists, and warns that user needs—not a four-box scheme—must drive complex hierarchies.
- User impact: Deployment operators, grant owners, dbt owners, read-only operators, product/action administrators, and governance readers would need to understand the repository taxonomy before finding the next task. Optional and destructive pages would be visually adjacent to ordinary read-only operation.
- Required change and acceptance:
  1. Expand D0 to require a product-documentation home plus landing pages for tutorial, how-to, reference, and explanation; each landing page contains an overview, not only a file list.
  2. Define visible task routes for: learn with fixtures; check/install/handoff; create or connect a dbt Job; investigate/reconcile; govern cost/retention/evidence; upgrade/remove; enable/administer optional actions; use optional AI; and understand the future Marketplace path.
  3. Map the human roles in the product plan to those routes, including the owner who grants a missing prerequisite and the read-only operator who should not see setup as a primary task.
  4. Group long lists inside each Diátaxis mode by user-recognizable concerns such as installation, onboarding, investigation, governance/lifecycle, capture machinery, deployment machinery, permissions, and optional capabilities. Avoid unstructured lists longer than a few items.
  5. Require breadcrumbs, previous/next tutorial links, related-task links, stable search synonyms/error codes, version/feature-status markers, and a lifecycle chooser in the D0 navigation deliverable.

### `DOC-IA-P0-005`: split optional documentation lanes and make D0-D6 gates traceable

- Verdict: `CHANGES_REQUIRED`
- Severity: medium
- Affected contract: `docs/plans/documentation-plan.md`, **Documentation implementation stages**, and `docs/plans/review-process.md`, **Documentation review cadence**
- Evidence: D6 combines P6 controlled-action identity/role administration, P9 Genie, and future Marketplace material, although the product plan gives them different readiness, security, and publication conditions. The D0-D6 table does not map every proposed page to a stage, product dependency, owner, or publication state. D2-D6 list selected reviewers/evidence but do not say explicitly whether those are additional to the universal six per-file passes.
- User impact: One optional track could appear complete because an unrelated track passed; future Marketplace content could look like a shipped capability; and pages such as new-job creation, App/API reference, grant handoff, optional Genie Agent setup, or conceptual explanations have no unambiguous delivery/review owner.
- Required change and acceptance:
  1. Replace D6 with separately gated lanes: controlled actions (P6/P7), optional AI/Genie (P9), and future Marketplace/provider distribution. They may share a release number only if each retains its own entry/exit evidence.
  2. Controlled-action gates cover actor/browser/admin/offboarding and destructive identity tests; optional-AI gates cover Genie Code and any separately planned read-only Genie Agent, feature status, safe curated inputs, and core-product operation with AI disabled; Marketplace material remains roadmap-only until provider/install/update/rollback claims are confirmed.
  3. Give every proposed page an audience, product-part dependency, documentation stage, owner, prerequisite pages, publication state (`base`, `optional installed capability`, or `future/not available`), and required evidence.
  4. State that every completed file/substantial section receives the six universal review passes and that each D-stage gate is additive. Keep D0's planning-only exception explicit where no rendered page exists yet.
  5. Require re-review of category navigation after each completed category and of all affected task routes after a page is moved, split, renamed, or changes optionality.

## Section-by-section evidence

| Reviewed section | Result | Evidence |
|---|---|---|
| `README.md` | `PASS` | Clearly identifies the private planning state, customer-local product boundary, review requirement, and planning links without pretending product documentation already exists. |
| `AGENTS.md` | `PASS` | Requires independent Diátaxis and readability passes, file/section-sized review, safe terminology, bounded live tests, and current primary sources. |
| `docs/index.md` | `PASS` for planning | Appropriate compact planning index. A separate future product-documentation home is required by `DOC-IA-P0-004`; this file need not be that home now. |
| Product plan: boundary, architecture, roles, install, operation, lifecycle | `PASS` as source material | Supplies concrete audiences, separations, states, and journeys from which task documentation can be derived. It consistently keeps P6, P9, and Marketplace outside the read-only base. |
| Product plan: delivery parts and usability gates | `PASS` | P0-P10 ownership and later implementation evidence are sufficiently explicit; D-stage traceability still needs the mapping in `DOC-IA-P0-005`. |
| Documentation plan: four modes and page contract | `PASS_WITH_CHANGES` | The mode definitions and page contract are strong. The five findings address the remaining mode, navigation, lifecycle, optionality, and staging defects. |
| Documentation plan: real evidence and screenshots | `PASS` | Evidence types follow the product journey and correctly defer actual sanitized captures to later review. The distinct lifecycle evidence exposes the combined-page defect in `DOC-IA-P0-002`. |
| Documentation plan: six review passes | `PASS` | Architecture, prose/style, subject accuracy, security, usability/accessibility, and rendered validation are independent, with material-edit re-review. |
| Documentation plan: D0-D6 | `CHANGES_REQUIRED` | Correct broad progression, but page coverage, additive universal gates, and optional-lane separation are not yet deterministic. |
| Documentation plan: publishing stack | `PASS` | Zensical/Pages remains a candidate behind accessibility, strict-build, search, audience, and publication-safety validation; no tool decision is presented as final. |
| Review process | `PASS` | Small independent parts, immutable inputs, finding lifecycle, re-review, and category navigation review align with iterative documentation work. |
| ADR 0001 | `PASS` | Explains the private App/Bundle decision and explicitly rejects Marketplace-first and AI-as-execution, giving explanation pages a stable conceptual source. |
| Source register | `PASS_WITH_FOLLOW_UP` | It links the Diátaxis root and FastAPI examples. The resolution should add the specific official Diátaxis pages used above so later authors can apply the same mode and hierarchy criteria. |
| Review records and resolution history | `PASS` | Immutable reports and baseline hashes remain traceable. Product-review implementation proofs assigned to later parts were not converted into documentation P0 defects. |

## Final verdict

`CHANGES_REQUIRED` for frozen baseline 0.4.

The planning baseline has a strong documentation product contract: all four Diátaxis needs are recognized, the technical subject inventory is unusually complete, the page contract is safe and testable, the six review passes are independent, and later live/rendered evidence is correctly gated. No architecture blocker was found.

P0 cannot yet claim information-architecture approval because the tutorial and production bootstrap entry points overlap, irreversible lifecycle and identity outcomes are combined, recovery action leaks into reference, the future site is a flat inventory rather than a task/audience navigation contract, and P6/P9/Marketplace material shares one non-traceable D6 gate. Resolve the exact acceptance conditions above, recompute a new frozen author hash, and request focused Diátaxis re-review. No Azure or Databricks resource was created, started, stopped, changed, or deleted by this review.
