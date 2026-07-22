# Documentation plan

- Status: Baseline 0.20 P0 acceptance candidate; immutable verdicts are recorded under `docs/reviews/p0-planning-baseline/`
- Updated: 2026-07-15
- Structure: Diataxis
- Readability benchmark: FastAPI documentation
- Visual benchmark: the established bricks-cli documentation style, subject to accessibility review

> **v0.3.0 documentation overlay:** The [v0.3.0 supported-release contract](../releases/v0.3.0-support-contract.md) is authoritative for current release documentation. v0.3.0 documents only combined-role installation, the temporary serverless bootstrap Job, nine customer objects, real `WORKSPACE` dbt onboarding, the read-only three-view App, and the six supported lifecycle operations. Separated duties, Statement Execution migration, runtime-trust ledgers, controlled actions, system enrichment, upgrade, and rollback below are future information architecture, not current instructions or release gates.

## Documentation outcome

A personal administrator can select `COMBINED_ROLE`, acknowledge that neither independent data observation nor independent SP-role review occurs, and complete a fresh install, failed-install cleanup, first evidence, trust refresh, and supported lifecycle through one actor/account/profile without handoff gates. An account-and-workspace-admin verifier and a different UC operator can instead complete `SEPARATED_DUTIES` without sharing credentials or checkpoints; v1 rejects a third identity reviewer before mutation. Both routes use an installer-only warehouse; distinguish direct `CAN_MONITOR` from effective `CAN_MANAGE`; recover through GA Query History; distinguish a Delta pending attestation from the live composite seal; treat each group as a customer-governed root; create a stopped zero-resource/no-user/no-deployment App shell; add exactly five read-only resources and five deploy-time mappings in a fresh bound-unshared plan; reconcile and stop the one deployment created by one pinned Bundle-runner invocation; add only approved-group `CAN_USE` in a fresh user-access plan; and explicitly start and accept the uniquely reconciled deployment. An App with an existing deployment is rejected because v1 does not qualify in-place upgrade or rollback. Mixed-evidence trust persists as one physical row per event with an exhaustive schema, canonical whole-generation component array, and one customer-security-owned latest-generation summary view. Each event records server `statement_evaluated_at` at query-evaluation start, not commit. Collector evidence separately freezes trust as observed when its AttemptKey root is written and never claims trust at commit. Optional controlled actions use one Serializable singleton fence: readers can tell when new admissions are blocked, whether one earlier action may still run, when quiescence is proven, and who must explicitly reopen after trust acceptance. An operator can investigate without raw diagnostics while every App page separates the pre-start transition-audit time from the post-start machine-freshness and original-roster-freshness times, shows their two validity ages and oldest validity-component age, and reports expiry and stale/unverified status. Client signatures do not authorize anything.

Documentation is part of the product contract. If a required flag, path, privilege, cleanup step, or lifecycle transition exists only in source code, the product is not ready.

## Information architecture

Use the four Diataxis modes inside an audience- and task-oriented hierarchy. The future product-documentation home is `index.md`; each mode has an overview landing page, and long lists are grouped by a reader-recognizable concern. The current `docs/index.md` remains a planning index until D0 replaces it deliberately.

P1.1 additionally has an implemented developer/integrator route under `developers/`. It uses the same four modes while the future customer/operator site remains planned:

- tutorial: `developers/tutorials/inspect-an-artifact-pair.md`;
- how-to: `developers/how-to/diagnose-an-invalid-artifact-pair.md` and `developers/how-to/handle-raw-dbt-artifacts-safely.md`;
- reference: `developers/reference/python-api.md` and `developers/reference/cli-report-and-exit-codes.md`; and
- explanation: `developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md` and `developers/explanation/raw-artifact-custody.md`.

This route labels all examples synthetic and sanitized. It never presents local pair validation as archive retrieval, Databricks runtime evidence, dbt success, capture completeness, or a qualified support row.

### Tutorials

One learning-oriented, safe, choice-free experience starts in a dedicated non-production fixture environment and ends with mandatory cleanup:

- `tutorials/index.md` — tutorial outcome, bounded cost, controlled start state, and chapter navigation.
- `tutorials/set-up-the-fixture-environment.md`
- `tutorials/install-the-fixture-instance.md`
- `tutorials/observe-the-fixture-run.md`
- `tutorials/investigate-the-fixture-failure.md`
- `tutorials/clean-up-the-fixture-instance.md`

These files are chapters of one tutorial, not alternative entry points. Each has previous/next navigation and a guaranteed checkpoint. The path uses packaged data and failures only, never silently starts paid compute, and cannot be mistaken for production bootstrap. A real one-model validation is a linked how-to after the learner completes cleanup.

### How-to guides

`how-to/index.md` routes readers to one real-work outcome. Proposed pages are grouped as follows.

Installation and handoff:

- `how-to/check-workspace-readiness.md`
- `how-to/prerequisite-recovery/index.md` — landing page grouped by stable preflight code and responsible owner, not one generic procedure.
- `how-to/prepare-a-customer-owned-product-schema.md`
- `how-to/bootstrap-the-private-app.md`
- `how-to/review-and-apply-a-migration-envelope.md`
- `how-to/verify-the-data-attestation-and-composite-seal.md` — prove the pending row, terminal Query History, exact direct-pair revoke, current effective DML, self-grant paths, named roots, mode gate, and live seal before runtime planning.
- `how-to/complete-a-combined-personal-install.md` — one actor/account/profile, no independent data observer or SP-role reviewer, no handoff states, pending/composite and candidate/accepted states, and same-actor recovery.
- `how-to/complete-an-attended-uc-handoff.md` — two distinct accounts, auto-discovered capsule, bounded marked Statement Execution, pending attestation/revoke, and independent deployment-verifier return.
- `how-to/recover-with-query-history.md` — use the exact native deep link without copying query text or entering a statement ID; terminate, wait, reconstruct, and escalate safely.
- `how-to/recover-residual-migration-authority.md` — exact group revoke plus separate current-DML/self-grant classification before any other mutation.
- `how-to/recover-an-interrupted-data-migration.md`
- `how-to/recover-an-interrupted-uc-handoff.md`
- `how-to/bind-deploy-share-and-accept-the-app.md` — approve/apply the zero-resource shell and fresh bound-unshared plans, prove the empty deployment baseline, invoke the pinned runner once, automatically reconcile exactly one new `SNAPSHOT`, stop, separately approve the fresh user-access-only plan, create a candidate, start the reconciled deployment, reobserve, accept, or stop safely.
- `how-to/recover-an-ambiguous-app-deployment.md` — resume paginated reconciliation after error, timeout, process loss, pending deployment, prior-code start, or multiple new deployments; never rerun deployment or ask the reader to choose an ID.
- `how-to/recover-a-stale-app-plan.md` — return from changed Direct lineage/serial, remote binding drift, interrupted shell/bound/user-access Apply, or intent mismatch to a fresh plan and approval without bypassing validation; reject any pre-existing deployment on the fresh-install route.
- `how-to/review-the-service-principal-role-roster.md` — the v1 verifier administrator compares every runtime principal's native Permissions page with the signed expected roster inside the returning bootstrap invocation; no third-person handoff, Preview API, or screenshot.
- `how-to/refresh-the-runtime-trust-snapshot.md` — when P6 exists, drain and prove controlled-action quiescence first; then inventory and stop the existing App, register `UNCHANGED_REFRESH`, prove a zero-sized deployment difference with byte-equal inventories, observe `STOPPED`, restart and observe the same deployment `ACTIVE`, perform any required native roster review, append a new accepted event while actions remain closed, explicitly reopen, and show the pre-start audit plus post-start-machine/original-roster validity times, oldest validity-component age, expiry, and qualifier without rewriting migration truth or extending reused roster evidence.
- `how-to/recover-runtime-trust-drift-or-expiry.md`
- `how-to/grant-operator-access.md`
- `how-to/validate-one-real-model.md`

dbt Job onboarding:

- `how-to/create-an-observable-dbt-job.md`
- `how-to/connect-an-existing-dbt-job.md`
- `how-to/review-a-generated-dbt-job-source-patch.md` — source/semantic change only, distinct from a Direct resource plan.

Investigation and recovery:

- `how-to/investigate-capture-failure.md`
- `how-to/reconcile-a-missing-attempt.md`
- `how-to/investigate-dbt-failure.md`
- `how-to/recover-an-interrupted-operation.md`

Governance and lifecycle:

- `how-to/lifecycle/index.md` — compares stop, remove configuration, retain/export, irreversible delete, and uninstall before mutation.
- `how-to/configure-retention.md`
- `how-to/export-governed-evidence.md`
- `how-to/delete-and-verify-evidence.md`
- `how-to/stop-the-app.md`
- `how-to/remove-code-and-configuration.md`
- `how-to/upgrade.md` — drains optional controlled actions before any trust/App/binding/data mutation and reopens only after the new accepted snapshot.
- `how-to/roll-back.md` — uses the same drain/quiescence/revalidation/reopen contract and states compatibility limits.
- `how-to/uninstall.md` — drains, removes App action/fence authority, retires the fence, requires an explicit evidence-disposition choice, and links to export/delete rather than combining them.

Optional controlled actions:

- `how-to/enable-optional-controlled-actions.md`
- `how-to/enroll-your-first-browser-profile.md`
- `how-to/approve-a-first-actor-and-role.md`
- `how-to/approve-an-additional-browser-profile.md`
- `how-to/drain-controlled-actions-for-maintenance.md` — block new admissions, disclose one earlier admitted action, apply the one approved cancel-or-wait policy, prove terminal state, and reach `CLOSED` before trust or lifecycle mutation.
- `how-to/recover-an-unknown-action-dispatch.md` — reuse the same Jobs idempotency token through the product workflow, reconcile one run, cancel/wait to terminal, and never enter a token or run ID.
- `how-to/reopen-controlled-actions-after-trust-acceptance.md` — show that acceptance leaves actions locked, verify the exact new generation/snapshot/component, and perform the separate verifier-owned reopen.
- `how-to/recover-action-identity.md`
- `how-to/remove-action-access-from-one-browser.md`
- `how-to/revoke-and-offboard-an-actor.md`
- `how-to/rotate-the-action-identity-key.md`

Optional system enrichment:

- `how-to/enable-optional-system-enrichment.md`
- `how-to/verify-system-enrichment-scope-and-freshness.md`
- `how-to/disable-and-remove-system-enrichment.md`

These pages are a separately installed, disabled-by-default route. They never imply that the base App, collector, runtime Bundle, attended data-migration plane, or ordinary operator can query `system`.

Optional AI:

- `how-to/install-the-optional-genie-code-skill.md`
- A read-only Genie Agent how-to is added only after P9 accepts that separate capability; it is not implied by the Genie Code page.

### Reference

`reference/index.md` groups neutral product machinery for lookup.

Compatibility, dbt, and evidence:

- `reference/support-matrix.md`
- `reference/installer-platforms-and-secure-storage.md`
- `reference/readiness-checks.md`
- `reference/capture-contract.md`
- `reference/supported-dbt-commands-and-artifacts.md`
- `reference/resolved-dbt-flags-and-paths.md`
- `reference/dbt-command-templates-and-configuration-conflicts.md`
- `reference/attempt-key.md`
- `reference/collector-trust-observation-provenance.md`
- `reference/artifact-and-log-fields.md`
- `reference/capture-states.md`
- `reference/observability-tables-and-views.md`

Deployment and data migration:

- `reference/bundle-variables-and-targets.md`
- `reference/direct-plan-source-and-drift-binding.md`
- `reference/app-deployment-inventory-and-reconciliation.md`
- `reference/customer-owned-product-schema.md`
- `reference/data-contract-manifest.md`
- `reference/resource-migration-attestation-composite-and-runtime-plans.md`
- `reference/attended-statement-execution-migration-contract.md`
- `reference/query-history-recovery-and-warehouse-permissions.md`
- `reference/fixed-data-envelope-and-composite-seal.md`
- `reference/attended-data-migration-and-seal-states.md`
- `reference/customer-owned-delta-attestation-and-view.md`
- `reference/runtime-trust-observation-matrix.md`
- `reference/runtime-trust-ledger-schema-and-canonical-identifiers.md`
- `reference/runtime-trust-ledger-and-current-view.md`
- `reference/runtime-trust-manifest-and-states.md`
- `reference/runtime-authorization-fence.md` — exact ordered create/`UTF8_BINARY`/isolation/eleven-`ADD CONSTRAINT`/singleton envelope, partial-state recovery, nullability/state/phase contract, grants, versions, leases, transition matrix, and external-run/trusted-root boundary.
- `reference/controlled-action-dispatch-and-idempotency.md` — identical-token dispatch, current-first/legacy-fallback Get Run projection, terminal `INTERNAL_ERROR`, final inventory, and indeterminate-state table.
- `reference/data-migration-error-codes.md`

Permissions and identities:

- `reference/permissions/index.md` — overview and links, not a duplicate grant catalogue.
- `reference/bootstrap-modes-and-states.md`
- `reference/human-roles-and-handoffs.md`
- `reference/oauth-u2m-handoff-and-profile-lifecycle.md`
- `reference/local-handoff-capsule-and-error-codes.md`
- `reference/app-access-and-resource-grants.md`
- `reference/runtime-dml-and-trusted-root-register.md`
- `reference/action-roles-and-approval.md`
- `reference/action-identity-and-browser-enrollment.md`
- `reference/role-administration-job-and-table-grants.md`
- `reference/action-identity-error-codes.md`

Application and operations:

- `reference/app-pages-and-api.md`
- `reference/operation-statuses.md`
- `reference/error-codes.md`
- `reference/cost-and-running-resources.md`
- `reference/retention-and-deletion.md`
- `reference/runtime-egress-and-dependencies.md`
- `reference/action-ledger-and-audit-enrichment.md`
- `reference/system-enrichment-job-permissions-and-snapshots.md`
- `reference/glossary.md`

### Explanation

`explanation/index.md` groups concept-oriented material by the mental model it develops:

- `explanation/product-tour.md`
- `explanation/why-a-private-app-and-bundle.md`
- `explanation/why-resource-and-data-plans-are-separate.md`
- `explanation/why-data-migration-is-attended.md`
- `explanation/why-migration-uses-a-dedicated-warehouse.md`
- `explanation/why-the-delta-row-is-not-the-seal.md`
- `explanation/why-bundle-schema-grants-are-not-used.md`
- `explanation/how-dbt-evidence-is-captured.md`
- `explanation/job-outcome-versus-capture-outcome.md`
- `explanation/why-logs-stay-local-until-closed.md`
- `explanation/customer-local-security-model.md`
- `explanation/identity-and-permission-model.md`
- `explanation/combined-personal-mode-and-residual-risk.md`
- `explanation/why-separated-duties-use-two-os-accounts.md`
- `explanation/why-controlled-actions-are-a-separate-upgrade.md`
- `explanation/why-controlled-actions-use-a-single-row-fence.md`
- `explanation/why-a-drain-is-not-yet-quiescence.md`
- `explanation/pseudonymous-actor-and-browser-profile-model.md`
- `explanation/forwarded-identity-and-account-recreation-limitations.md`
- `explanation/why-a-saved-plan-needs-a-source-and-drift-sidecar.md`
- `explanation/why-stage-and-final-direct-plans-are-generated-sequentially.md`
- `explanation/why-one-bundle-run-can-produce-an-ambiguous-deployment-set.md`
- `explanation/why-collection-uses-a-separate-job.md`
- `explanation/why-collector-trust-is-observation-time.md`
- `explanation/data-contract-seal-versus-runtime-trust.md`
- `explanation/why-group-principals-are-trusted-roots.md`
- `explanation/why-service-principal-roles-need-an-admin-attestation.md`
- `explanation/why-runtime-trust-has-three-times-and-two-validity-clocks.md`
- `explanation/why-roster-refresh-reuses-only-the-original-self-anchor.md`
- `explanation/how-cancellation-reconciliation-works.md`
- `explanation/development-versus-production.md`
- `explanation/cost-model.md`
- `explanation/optional-system-enrichment-boundary.md`
- `explanation/optional-ai-boundary.md`
- `explanation/marketplace-roadmap.md`

`product-tour.md` is cognition-oriented context, not a tutorial chapter. Optional-AI and Marketplace explanations appear only in visibly separate optional/future routes.

### Navigation and page traceability contract

D0 must produce the home, four mode landing pages, grouped side navigation, and these visible task routes:

1. Validate one pinned dbt artifact pair locally as a developer/integrator.
2. Learn safely with fixtures.
3. Check, install, verify, and hand off the base product.
4. Create or connect a dbt Job.
5. Investigate and reconcile a run.
6. Govern cost, retention, and evidence.
7. Upgrade, stop, remove, export, delete, or uninstall through a lifecycle chooser.
8. Decide whether to enable, verify, and remove optional system enrichment.
9. Enable and administer optional controlled actions.
10. Use optional AI with the core product still functional when AI is disabled.
11. Understand the future Marketplace path without mistaking it for an available capability.

Audience entry points map library developers/integrators to route 1; combined personal administrators, workstation administrators, deployment operators, and UC/data-plan operators to route 3, with deployment and UC/data-plan operators also using route 7; dbt/Job owners to route 4; read-only operators to route 5; governance/product administrators to routes 6 and 7; optional system-data owners to route 8; and action-role administrators/action users to route 9. Setup is not primary navigation for read-only operators.

Every planned page record includes audience, product-part dependency, documentation stage, accountable owner, prerequisite/next pages, publication state (`base`, `optional installed capability`, or `future/not available`), search synonyms and stable error codes, and required evidence. Site/category landing pages provide overviews rather than file lists. Breadcrumbs, tutorial previous/next links, related-task links, version/feature-status markers, and the lifecycle chooser are required navigation, and affected routes are re-reviewed whenever a page moves, splits, changes name, or changes optionality.

The D0 page registry expands these mandatory inheritance rules; no page can enter drafting without one matching row and its page-specific prerequisites/evidence:

| Page family | Audience and product dependency | Stage and owner | Publication state and minimum evidence |
|---|---|---|---|
| Home, mode/category landing pages, glossary, product tour | All audiences; P0 terminology/routes | D0; documentation lead plus IA owner | `base`; route and search-term review |
| P1.1 developer tutorial, invalid-pair and raw-artifact-handling how-tos, API/CLI reference, and pair/outcome/capture plus raw-custody explanations | Library developer/integrator; P1.1 | D1P; capture-library owner plus dbt and security documentation owners | `base`; exact runnable fixture commands/output, synthetic-data notice, issue/exit/API contracts, input-custody/support/lifecycle controls, deterministic and installed-wheel tests, and explicit non-claim of dbt success, capture completeness, or Databricks-local custody |
| All `tutorials/` chapters | Learner; P3/P4 fixture path | D1; tutorial owner | `base`; ordered fixture checkpoints, mandatory cleanup, non-author walkthrough |
| Installation/handoff how-tos and deployment/migration/base-permission references/explanations | Combined administrator, workstation administrator, verifier administrator, and UC/data-plan operator; P2/P3/P4 | D2; platform documentation owner | `base`; immutable modes; combined false independence flags; exactly-two-person separated topology and third-reviewer rejection; customer schema; warehouse direct/effective authority and full-query disclosure; marked Statement Execution/Query History recovery; one recovery-actor table; pending data attestation versus composite seal; current-DML/self-grant/group roots; App stage-plan/apply, paginated deployment reconciliation, stop, fresh-final-plan/approval/apply, start sequence; one-row-per-event ledger/latest-generation summary; native SP-role attestation by the verifier; pre-start audit plus post-start-machine/original-roster validity times and oldest validity age; Direct versus runtime DML; mode gates and bounded cost |
| dbt Job onboarding how-tos and command/artifact/flag references | dbt/Job owner; P1/P5 | D3; dbt documentation owner | `base`; scanner/source-patch fixtures and semantic-change proof |
| Investigation/reconciliation how-tos and run/capture/App-operation references | Read-only operator; P2/P4 | D4; operator documentation owner | `base`; real sanitized run/failure evidence, separate **Trust observed by collector** and **Current runtime trust** states, observation-read-to-commit timeline, and read-only task test |
| Governance/lifecycle how-tos plus retention/cost/deletion/upgrade explanations | Product/governance administrator and UC/data-plan operator; P7/P8 | D5; operations documentation owner | `base` plus optional-P6 callouts; lifecycle-choice, rollback limit, foreign-grant preservation, retained ownership transfer, deletion proof, drain-before-mutation, terminal-run proof, retired fence, explicit reopen, and no-force-open recovery |
| Optional system-enrichment how-tos, reference, and explanation | System-data owner and governance administrator; optional P4/P7/P8 | D4E; enrichment documentation owner | `optional installed capability`; disabled-base proof, regional Lakeflow/account-global billing disclosure, exact principal/source/scope-table/filter/snapshot/cadence/cost/freshness evidence, pair-collision/cross-workspace denial, and removal proof |
| Controlled-action how-tos plus every action/identity/role/fence/dispatch reference or explanation | Action user/approver/verifier/administrator; P6/P7 | D6; controlled-actions documentation owner | `optional installed capability`; exact ordered singleton create/collation/property/eleven-constraint/row envelope and partial-state recovery; state/phase/grants; admission/drain/quiescence linearization; same-token dispatch recovery; current-first/legacy-fallback Get Run table including terminal `INTERNAL_ERROR`; final inventory; lease-takeover rule; explicit reopen/retire; App/external-caller residual; cost/downtime evidence; P6 task evidence; and AI/Preview-disabled proof |
| Genie Code/Agent how-tos and optional-AI explanation | dbt author or read-only analyst; P9 | D7; optional-intelligence owner | `optional installed capability`; current feature status, curated-input proof, AI-disabled core test |
| Marketplace roadmap/provider material | Prospective provider/customer administrator; post-P10 | D8; distribution owner | `future/not available`; written provider/install/update/rollback confirmation before capability language |

### Implemented P1.1 page registry

Every implemented P1.1 page is `base` and depends on the offline capture library only. It must not imply archive retrieval, live Databricks execution, dbt success, capture completeness, or production compatibility.

| Page | Audience and dependency | Stage and accountable owner | Prerequisite and next route | Search synonyms and stable codes | Required evidence |
| --- | --- | --- | --- | --- | --- |
| `developers/tutorials/inspect-an-artifact-pair.md` | Library developer/integrator; P1.1 synthetic fixtures | D1P; capture-library owner plus dbt documentation owner | Python 3.12, uv, approved dependency source; next invalid-pair recovery or pair-state explanation | inspect artifacts, `PAIR_VALID`, `PAIR_INVALID`, dbt outcome | Exact commands/output, sanitized fixture proof, documentation contract, installed-wheel gate |
| `developers/how-to/diagnose-an-invalid-artifact-pair.md` | Library developer/integrator; P1.1 inspector | D1P; capture-library owner plus dbt documentation owner | Existing inspection failure and safe report; next CLI registry or pair-state explanation | diagnose invalid pair, exit `3`, exit `10`, `DBTOBSB_INPUT_READ_ERROR`, `DBT_*` | Every issue in canonical precedence, exact action/classification, real recovery fragments, safe-support boundary |
| `developers/how-to/handle-raw-dbt-artifacts-safely.md` | Library developer/integrator and accountable data/security owner; caller-owned real artifacts | D1P; security documentation owner plus capture-library owner | Approved host/storage/access/lifecycle decision; next inspection, failure recovery, or custody explanation | raw artifacts, Personal Data, secrets, retention, legal hold, support payload | Input warning, ordered custody/support/lifecycle controls, verification and deletion consequence, security review |
| `developers/reference/python-api.md` | Python integrator; P1.1 library API | D1P; capture-library owner | Installed runtime; next tutorial for first use or recovery how-to for invalid output | Python API, `inspect_artifact_pair`, `ArtifactPairReport`, 128 MiB, nesting | Reflected signature/types/limits/statuses, exact executable example/output, constructor/schema tests |
| `developers/reference/cli-report-and-exit-codes.md` | CLI integrator and support engineer; P1.1 console contract | D1P; capture-library owner plus dbt documentation owner | Installed runtime; next symptom-specific recovery how-to | CLI, exit codes, report schema, `DBT_*`, `DBTOBSB_*` | Exact exits/output, full issue registry, static-text and fragment binding, installed console-entry-point gate |
| `developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md` | Library developer/integrator; P1.1 interpretation boundary | D1P; dbt documentation owner | Tutorial or report result; next tutorial, recovery how-to, or CLI reference | pair validity, dbt outcome, capture state, `COMPLETE` | Valid-success, valid-dbt-failure, and mismatched-pair fixtures plus explicit completeness non-claim |
| `developers/explanation/raw-artifact-custody.md` | Library developer/integrator and security reviewer; P1.1 data-flow boundary | D1P; security documentation owner plus capture-library owner | Raw-artifact handling how-to or API/CLI reference; next handling how-to or machine reference | safe report, sensitive input, custody, workstation-local, Databricks-local | First-party dbt artifact sources, implementation data-flow check, security review, explicit future-product non-claim |

## Page contract

Every task page contains, in this order where applicable:

1. A one-sentence outcome.
2. Audience and environment.
3. Prerequisites with exact permission and cost implications.
   Include the acting human role, who grants a missing prerequisite, how preflight reports it, and what access remains afterward.
4. A short safety note before any mutation.
5. Numbered steps with copyable commands or UI labels.
6. Expected output after consequential steps.
7. Verification that proves the outcome, not merely command success.
8. Recovery for the most likely failure.
   Distinguish a pollable long-running Operation from RFC 9457 terminal Problem Details. Use the stable code, safe evidence reference, retry rule, and native deep link; do not paste raw platform exceptions.
9. Cleanup or rollback.
10. Related reference and explanation links.

Reference pages define types, allowed values, defaults, compatibility, security classification, and examples. They catalogue stable codes, meaning, and retryability and link to symptom-specific recovery tasks; they do not embed procedures. Explanation pages do not masquerade as procedures.

Every controlled-action or P6-aware lifecycle task additionally shows, before confirmation: whether new admission is allowed; whether one previously admitted action may still run; safe action/Job display names; required and eligible actor; current milestone and last confirmed server time; native compute and whether cost can still accrue; fixed cancel-or-wait policy; deadline/escalation owner; read-only App availability; expected controlled-action downtime; and exactly one primary next action. Its verification distinguishes drain commit from terminal-run/quiescence proof and trust acceptance from explicit reopen. No task offers **Continue anyway** or force-open, asks for an action/run ID or token, or treats lease expiry/cancel acceptance as terminal.

The fixture tutorial begins in a controlled non-production environment and does not duplicate production bootstrap. `bootstrap-the-private-app.md` starts before the App exists: verify the installer; choose one immutable mode; audit recovery; confirm schema, owner/operator/verifier groups, account-and-workspace-admin verifier, trust-ledger authority, and warehouse; accept Query History/direct/effective authority; validate the Bundle; review and execute the fixed migration envelope; resolve exact revoke; verify pending data attestation plus composite seal; then register a trust generation, review/apply the stopped zero-resource/no-user/no-deployment App-shell plan, generate/review/apply the fresh bound-unshared plan with exactly five resources and five deploy-time mappings, capture the empty fully paginated deployment baseline, invoke the pinned Bundle runner once without a wrapper retry, stop and reconcile exactly one new matching `SNAPSHOT`, generate/review/apply a fresh stopped user-access-only plan whose sole delta is approved-group `CAN_USE`, complete pre-start GA and native roster evidence, append a candidate, explicitly start the reconciled deployment, reobserve it, append final acceptance, and only then show the App URL. Any existing deployment, error, timeout, process loss, stale plan, or deployment ambiguity routes to stop/reconcile/re-plan or the explicit unsupported-existing-deployment outcome rather than a second deploy invocation or a human ID choice. The mode choice routes to two visibly separate procedures:

- `COMBINED_ROLE` uses one account-administrator actor/account/profile and records all independence flags false. The same actor performs Query History cleanup, exact revoke, pending-attestation/composite verification, App staging, GA observation, native roster review, and trust commits. A non-account-admin is unsupported. It emits no handoff state and targets 20 total active minutes including roster work, excluding platform wait.
- `SEPARATED_DUTIES` retains exactly an account-and-workspace-admin verifier plus a distinct UC actor, actor-owned profiles/checkpoints, signed capsules, UC-owned schema/data apply/pending attestation/revoke, verified account release, and deployment return. The verifier performs the native roster task; a third reviewer is unsupported. If the UC actor is lost, the recovery decision table permits only the exact eligible action before the verifier independently observes the data seal.

Both procedures show envelope/execution digests; warehouse privacy/direct/effective authority; Query History and recovery actor; pending data attestation; exact revoke; current DML/self-grant/group roots; composite seal; separately approved shell, bound-unshared, and user-access-only plans; Direct lineage/serial; before/after deployment-set summaries; exact reconciled `SNAPSHOT`; trust candidate versus accepted event; one-row-per-event/component-array cardinality; distinct pre-start/post-start machine observations; original roster self-anchor; all three query-start statement times; two validity ages; oldest validity-component age/expiry; stale consequence; and safe-start/stop result. When P6 is installed they also show closed-before-mutation, any earlier admitted action, terminal proof, trust acceptance while still locked, and the separate reopen. Only separated mode shows handoff/account-return state and data mutation/observer separation; neither mode claims independent SP-role review. The reader never enters/transfers SQL, tokens, profile names, capsules, deployment/action/run IDs, paths, checkpoints, screenshots, or YAML. Direct executes no SQL/UC DDL/DML; the verifier writes only fixed trust/fence operations; optional client signatures are audit metadata; runtime principals write only enumerated tables and never either ledger. Optional capabilities remain separate.

## Writing and example style

- Lead with the outcome.
- Use short sections and progressive disclosure.
- Introduce one new concept at a time.
- Prefer concrete names in examples, then explain which values vary.
- Show expected output and visible state transitions.
- Keep `Databricks job run`, `task run`, `dbt invocation`, `artifact`, `diagnostic log`, and `capture` distinct.
- Keep Bundle validation, migration envelope, Query History marker, bounded Statement Execution, exact revoke, pending data attestation, composite seal, App-shell plan/apply, bound-unshared plan/apply, empty paginated deployment baseline, single wrapper `bundle run` invocation, stop/reconciliation, fresh user-access-only plan/approval/apply, pre-start candidate, direct `apps start`, post-start observation, and final trust event distinct. Explain that the pinned runner starts compute before deployment and may internally reissue deployment after an error; never call one invocation one submission or the bound interval zero-authority. Never describe data operations or trust-event DML as Direct resources. Enumerate runtime DML and universal control-ledger/DDL denials separately.
- Keep `COMBINED_ROLE` and `SEPARATED_DUTIES` visibly distinct and immutable. Combined uses one actor/account/profile and all false independence flags. Separated uses exactly a verifier-administrator OS account and a distinct UC-operator OS account with private profiles/checkpoints, signed capsule, release, and return. It separates UC data mutation from later observation but not SP-role review. A capsule only locates state; same-account and third-reviewer attempts are unsupported rather than improvised.
- State that the product schema is customer-owned and typed, Direct has no schema `grants` list, and targeted operations preserve unrelated direct and inherited assignments. Explain the CLI 1.9.0 omitted-principal reconciliation risk in reference/explanation, not as an unexplained warning inside every task.
- Give `NO_ATTESTATION`, `DATA_MUTATION_ACTIVE`, `DATA_APPLIED_PENDING_REVOKE`, `REVOKE_REQUIRED`, `DIRECT_GRANT_REMOVED_PENDING_OBSERVATION`, `COMPOSITE_SEALED`, `RUNTIME_BOUND`, and every fail-closed query/visibility/DML state exact meanings. Never label the pending row terminal or direct-pair removal total effective-authority absence.
- Give combined/separated actor and recovery-table states exact meanings. Every error states mode, needed actor, Query History/trust-event status, whether mutation/temporary grant/compute remains, and one safe consequence. Runtime trust distinguishes registered/candidate/accepted/invalidated/stale/code-drift/authority-drift/unverified; always labels the pre-start time as transition audit, the post-start-machine and original-roster times as validity inputs, their two ages and oldest validity-component age, expiry, and running state; and never silently changes migration truth.
- Use **Trust observed by collector** and **Current runtime trust** as separate labels. Explain with a three-step timeline that the collector may read snapshot N, trust may then change, and the evidence root may still commit its earlier N observation. Never say trust at commit, trust when evidence was saved, or imply the stamp authorizes/refreshes trust.
- Keep forwarded subject fingerprint, stable actor, identity epoch, browser-profile credential, device binding, role binding, enrollment request, and platform run-as identity distinct.
- Use `Personal Data`, not `PII`.
- Mark GA, Preview, Beta, and Experimental features visibly.
- Use admonitions only for real safety, cost, compatibility, or data-handling consequences.
- Never publish live customer or personal workspace values. Use clearly synthetic IDs and domains.
- Keep raw logs and compiled SQL out of ordinary screenshots and examples.
- The migration-envelope how-to/reference may show the full fixed secret-free DDL/DML/owner/grant/query-marker/revoke/attestation text needed for approval. Signed code re-renders it and sends one parameter-bound operation per request with the frozen timeout/cancel policy; no privileged migration Job or reader/plan-supplied SQL exists. Ordinary UI never copies Query History text, but documentation must disclose that warehouse monitors can see complete text and user details and Databricks-managed history is not deleted by dbtobsb.
- State that the Delta row contains only completed prior Statement Execution IDs and cannot contain its own ID or a later revoke observation. The composite seal is point-in-time and distinguishes direct-pair absence, current DML, self-grant capability, named roots, verifier/time, visibility completeness, and independent-observer flag.
- State that a data-contract seal does not protect later evidence from named App/Job/deployment/group/SP-role/trust-ledger administrators. Show the runtime-trust manifest, closed GA matrix, dual-role verifier-admin native roster review, Public Preview exclusion, one physical row per logical event, exhaustive DDL, exact four-operation required/null matrix, literal canonical domains and golden vectors, lifecycle-free deployment inventories, the one-new-record versus unchanged-refresh zero-difference rule, complete component array, distinct `STOPPED` pre-start and `ACTIVE` post-start observations with one stable graph, original self-anchored roster source and complete source-chain revalidation, query-start rather than commit timestamps, latest-generation summary reduction, invalidation precedence, exact P6 summary/component/fence claim, three statement times/two validity clocks/oldest validity age/expiry, stale/drift consequences, and unsupported custody/third-reviewer policies. Optional client signatures are explicitly non-authoritative audit metadata. Never call `SP_ROLE_ROSTER_ADMIN_ATTESTED` machine verification or independent review.
- In the trust/fence reference only, explain that integral identity properties are base-10 text so SQL, Python, and browser implementations hash the same bytes. Show quoted JSON boundary vectors and the exact `0|[1-9][0-9]*` ASCII rule; reject signs, leading zeros, whitespace, Unicode digits, decimal/exponent, overflow, and JSON-number forms. SQL columns remain numeric, nullable SQL remains JSON `null`, users never type these strings, and ordinary workflows do not expose serialization detail.
- Give the physical fence states/phases and their plain-language projections exact meanings. Say **new actions blocked** at the drain commit and **maintenance safe to begin** only after terminal reconciliation, final paginated inventory, and `CLOSED`. Show the one-action limit, same-token Jobs recovery, asynchronous cancel, current-status-first/legacy-fallback Get Run terminal proof, terminal-failure `INTERNAL_ERROR`, unknown/conflicting evidence that remains held, takeover-without-release, explicit reopen, irreversible retire, and append-only milestones. Never call Delta plus Jobs atomic, say `DRAINING` means no run can launch, promise that a new trust generation stops an earlier admission, claim all Job callers are fenced, or imply resistance to compromised App/admin roots.
- State that every granted group principal is a customer-governed authority root. Use `SHOW GROUPS WITH USER`/`WITH GROUP` only to classify the named migration actors/groups; do not claim to list every direct/indirect member or detect membership changes continuously.
- Distinguish a group's direct warehouse `CAN_MONITOR` row from an actor's effective authority. The workspace-admin verifier can stop, edit, delete, and change ACLs on the warehouse; another named manager is the procedural escalation owner, not the exclusive technical manager.
- State plainly which collector authority mode is active. `BOOTSTRAP_ALLOWED` executes only the versioned fixed product-object manifest and verifies its postconditions; `RUNTIME_DML_ONLY` performs ordinary idempotent collection into the three evidence tables. Document whether the bootstrap actor is an attended operator or the personal/test collector principal, when bootstrap authority ends, which authority remains, and that App bindings still require verified existing objects. Table-level `MODIFY` remains residual schema-alter authority; name the collector principal, its code deployers, and Job managers as trusted roots. Its immutable trust tuple is observation-time provenance on the AttemptKey root and is excluded from AttemptKey, dbt hashes/validation, capture precedence, and native outcomes.
- State plainly that optional system enrichment is absent from the base manifest and grants. Its separate pages name the dedicated principal/paused Job, Lakeflow's account/current-region and billing's account-global source visibility, the attended signed migration plane as sole writer of the `(workspace_id, job_id)` scope table through approved fixed DML-only Statement Execution updates, immediate pair filter, three snapshots plus sanitized views, excluded identity/user-controlled fields, snapshot semantics, freshness, cost, retention, denial-to-`DEGRADED`, and uninstall; the App never receives `system` access.
- Give every machine state a plain-language label and stable code. Keep Job, dbt invocation, node/test, collector, and capture outcomes separate.
- Keep capture state separate from structured-log state; document unavailable, logger-not-initialized, truncated, malformed, missing, unknown, and valid `log_version` evidence per command ordinal without weakening a valid primary artifact pair. A `deps` event cannot prove the primary build started.
- CLI examples use `--no-color`, text progress, meaningful exit codes, and JSON where automation consumes output; they never rely on spinner or color state.
- Reserve `UNSUPPORTED` for an inspected unsupported pattern; document `ACCESS_BLOCKED` and `CHECK_FAILED` as distinct recovery paths.
- Mark cost confidence as exact/attributed, allocated/estimated, pending, or unavailable.
- Use display-name resources in reader-facing examples and synthetic internal IDs only in clearly marked reference examples.
- Never imply `X-Forwarded-User` is an opaque Databricks ID; explain that it may be a username/email and remains request-local. Pseudonymous actor/device/governance records are still Personal Data.
- Never show a raw forwarded value, browser credential, HMAC material, complete fingerprint, secret-scope value, or reusable enrollment secret. A role-Job example may contain only a clearly labeled nonsecret synthetic request locator.
- Call the browser notice an **enrollment acknowledgement**, not Databricks **user consent**, which refers to the optional Preview user-authorization flow.

## Real evidence and screenshots

The product documentation should eventually include real sanitized captures of:

- Combined-mode preflight, all false independence flags, one account-admin actor/profile, Query History cleanup, pending data attestation/composite seal, shell/bound/deploy-stop/share App lifecycle, native roster task, accepted trust event, ≤20-minute total active work including roster review, and no handoff state—with no credential/path shown.
- Separated-mode preflight plus the verifier-admin and distinct UC OS accounts, actor-owned secure profiles, auto-discovered capsule, prompts, account release, and deployment return—with no credential/path shown; same-account, non-account-admin-verifier, and third-reviewer attempts fail before mutation/compute.
- Customer-owned dedicated-schema owner/marker plus separate direct and inherited grant snapshot, with unrelated customer assignments visibly preserved.
- Bundle validation and graph evidence proving Direct plan/apply/hooks contain no SQL, schema grant, UC DDL/DML, privileged migration Job/SP, ledger write, missing-object binding, or hidden mutation.
- Installer-only warehouse readiness and privacy warning; `CAN_USE`/`CAN_VIEW`/direct `CAN_MONITOR` contrast; effective workspace-admin `CAN_MANAGE`; one read-only recovery marker; full query/user exposure using synthetic data; cross-user result-fetch denial; native cancel deep link; terminal Query History; procedural escalation owner; and no copied raw query in the product UI.
- Full fixed envelope, exact migration-group ledger pair/revokes, execution binding, complete direct/current-DML/self-grant/group audit, bounded Statement Execution evidence, `DATA_APPLIED_PENDING_REVOKE` view, and live composite tuple. Separated evidence shows independent verifier/account return; combined shows those states absent and `independent_observer=false`.
- Approved stopped zero-resource/no-user/no-deployment shell plan; approved fresh bound-unshared plan with exactly five read-only resources and five deploy-time mappings; every page of the empty before-set; one wrapper Bundle-runner invocation; every page of the after-set; exactly one reconciled new terminal matching `SNAPSHOT`; explicit stop; fresh user-access-only plan with new lineage/serial and a diff limited to approved-group `CAN_USE`; separate approval; pre-start GA observation and native Permissions-roster comparison by the verifier administrator; `TRUST_CANDIDATE`; direct `apps start`; same-deployment post-start observation; final `SNAPSHOT_ACCEPTED`; one-row-per-event ledger rows and sanitized latest-generation summary; complete component array; the pre-start transition-audit, post-start machine-freshness, and original-roster-freshness query-start times; two validity ages, oldest validity-component age, and expiry; and disclosed group/App/Job/SP/admin/committer roots. It visibly says the bound interval is point-in-time, fail-closed but not zero-authority, non-independent, and not continuous; no deployment ID is entered or chosen.
- One sanitized attempt whose **Trust observed by collector** remains snapshot N while **Current runtime trust** has moved to N+1 or invalidated. Show the trust-read, trust-change, and evidence-root-commit order; the identical AttemptKey, artifact hashes, capture result, and Lakeflow/dbt/node outcomes; and no claim that N was current at commit.
- A true unchanged trust refresh with no code deployment, a successful App query after restart, no extended roster expiry, and proof that synthetic customer grants and trust history survived.
- Abrupt interruption before/after every data/trust/fence mutation, shell and bound plan/apply, empty deployment baseline/invocation/reconciliation/stop, fresh user-access plan/approval/apply, roster review, candidate, direct start, post-start observation, final commit, and reopen. Capture query/cancel races, recovery actors, secure-store/browser loss, stale Direct serial, remote drift during approval, first-response loss, pinned-runner start-before-deploy, internal POST reissue, zero/multiple/pending/paginated deployment results, trust nullability/component duplicates/conflicts/replay/invalidation, non-authoritative signatures, decimal-string boundaries, query-start timestamp boundaries, missing/swapped pre/post phases, stable-graph mismatch, original self-anchor and orphan/intermediate/transitive anchor rejection, source-chain invalidation/deletion/tamper, shell zero-authority and bound-authority denial, existing-deployment rejection, deployment-ID race, failed stop/running-cost warning, Preview APIs disabled, group roots, page-open expiry, unchanged/changed roster refresh, next-observation drift, collector read/commit race, claim/drain orderings, indeterminate dispatch, async cancel, lease takeover, explicit reopen/retire, workstation loss, App restart, and zero active query/grant/compute.
- App readiness and URL handoff.
- One successful observed run.
- One dbt failure with a valid artifact.
- One early failure with `NOT_PRODUCED`.
- The run timeline and capture-state distinction.
- A normalized node/test query result.
- Cost/running-resource inventory.
- Stop and uninstall confirmation.
- The four distinct lifecycle choices: stop App compute, remove code/configuration, retain/export governed evidence, and irreversibly delete/verify evidence.
- Retain-uninstall ownership transfer and residual-access receipt versus separate verified-empty-schema deletion.
- A scoped pre/post live-proof inventory that distinguishes product/test-owned, reused, and unrelated resources and restores reused resources to their prior state.
- An optional-action first-browser request, immutable administrator summary, approved additional-browser state, actor-wide revoke, browser-only revoke, and key-rotation recovery, all sanitized so no raw subject, complete fingerprint, credential, or governance reference is visible. Include the real closed fence after install; explicit first reopen; claim-before-drain and drain-before-claim outcomes; **New actions blocked — resolving one prior action**; lost-response same-token recovery; terminal native run; `CLOSED`; trust acceptance while still locked; explicit reopen; possible-cost/downtime fields; and durable wrapper progress while the App is stopped, without an action/run ID or token on screen.
- Optional system enrichment disabled with no objects/Job/grants, plus a separately enabled capture of its dedicated principal, paused Job, attended fixed DML-only scope-table update, three snapshots/sanitized views, regional/global disclosure, workspace/Job pair-filter proof, freshness/cost state, pair-collision/cross-workspace denial, and complete disable/uninstall grant removal.

Capture review is a separate publication-safety pass. Scan the source image, metadata, OCR text, repository history, rendered site, and CI artifact for emails, user names, workspace/account IDs, hostnames, tokens, signed URLs, Git URLs, raw SQL, and Personal Data.

## Documentation review passes

Each file or substantial section is reviewed in this sequence:

1. **Subject accuracy** — the relevant Databricks or dbt owner verifies current behavior and exact commands; both review only pages that cross the platform/dbt boundary.
2. **Diataxis architecture** — verifies the page type, reader need, scope, and navigation.
3. **FastAPI-style readability** — verifies clarity, progressive examples, expected output, and scannability.
4. **Security/compliance** — verifies identity, data classification, egress, retention, secrets, and safe examples.
5. **Usability/accessibility** — follows the task as a representative reader and verifies recovery paths. WCAG 2.2 Level AA applies to every complete App page/state and every page in each complete rendered-documentation process, with zero known A/AA failures; the CLI receives a separate text-interface pass.
6. **Rendered-site validation** — links, navigation, search terms, code blocks, alt text, contrast, responsive layout, and publication safety.

Review the architecture separately from prose and style. The six passes apply to every completed file or substantial section; a D-stage gate is additional, never a substitute. D0 may review planning artefacts before a rendered page exists, but its navigation is re-reviewed after each category and after any move, split, rename, or optionality change. Re-review after every material edit.

## Documentation implementation stages

| Stage | Output | Gate |
|---|---|---|
| D0 | Product home; four overview landing pages; grouped navigation; audience/task routes; glossary; and a page registry mapping every proposed page to audience, product part, stage, owner, prerequisites, publication state, and evidence | IA plus all three product reviewers approve the planning artefacts; rendered-page passes are explicitly deferred until pages exist |
| D1 | One controlled fixture tutorial from setup through observation, failure investigation, and mandatory cleanup | Six universal passes; non-author learner completes the choice-free sequence; clean rendered build and no unplanned compute |
| D2 | Production install in both modes; combined false-independence route; exactly-two-person verifier-admin/UC route and unsupported topology errors; customer schema/groups; warehouse direct/effective authority; Statement Execution/Query History/recovery actors; pending data attestation/composite seal; sequential stage-plan, deployment-reconcile-stop, fresh-final-plan, bind-start lifecycle; one-row-per-event ledger/latest-generation summary; whole-group roots; GA matrix; non-independent native roster attestation; pre-start audit plus post-start-machine/original-roster validity times/ages/stale/drift; collector observation-time provenance; data/capture/log contracts | Six passes plus platform/dbt/security approval; two real U2M users prove cross-user recovery; actual verifier/admin/committer authority is disclosed; Preview APIs disabled; no Direct SQL/UC DDL/DML or credential transfer; stage has no authority/user access; full deployment pagination/internal retry/stale-plan cases fail closed; exact DDL/matrix/decimal-string golden-vector, phase, original-anchor/source-chain, row/candidate/component-cardinality unlock tests fail closed; same reconciled deployment is accepted post-start; collector read/commit timeline and outcome invariance, trust conflict/restart/query-start-time/expiry, and foreign-grant tests pass; all active query/grant/compute cleanup and time targets pass |
| D3 | New/existing dbt Job onboarding and generated source-patch recovery | Six universal passes plus dbt-owner task test, semantic-change example, and rollback proof |
| D4 | Operator run history, investigation, reconciliation, cost confidence, and distinct outcome set | Six universal passes plus read-only operator task test and real sanitized capture review |
| D4E | Separately installed optional system-enrichment enable/verify/disable path, dedicated principal/paused Job, one scope table, three snapshots/sanitized views, exact regional/global source scope, pair filter, snapshot semantics, freshness, cost, retention, and failure state | Six universal passes plus system-data-owner/security approval; base-without-system proof; pair-collision/cross-workspace/unonboarded-Job denial; late/no-op/retry evidence; paused/removed resource and grant inventory |
| D5 | Unsupported existing-deployment/upgrade/rollback boundary, retention/export/delete, stop/remove/uninstall, warehouse/history cleanup, authority/trusted-root/control-ledger/fence review, trust refresh, mode recovery, and ownership transfer | Six passes plus destructive safety, foreign-grant preservation, exact revoke, pending/composite proof, zero-authority empty shell, disclosed bound fail-closed interval, fully reconciled sole fresh-install deployment, user-access-only plan, explicit rejection of in-place upgrade/rollback, trust/fence-history retain/delete, P6 drain and terminal-run proof before mutation, explicit reopen or irreversible retire, App/workstation restart, three statement times/two validity clocks, original self-anchor source revalidation, unchanged reuse/no expiry extension, required 24-hour roster review, drift handling, mode completion, no-force-open recovery, and deletion verification |
| D6 | Optional controlled-action nine-table data upgrade through the same recoverable/composite, deployment-reconciled, sequential-plan, and staged-trust planes; actor/browser administration; approval; singleton admission/drain/recovery/reopen; offboarding; key recovery; and role/App trust handling | Six passes plus current feature/privacy/security review; exact marked create/`UTF8_BINARY`/isolation/eleven-`ADD CONSTRAINT`/singleton operations, readback, partial-state recovery, nullability/state/phase, and DML/group/manager/committer roots; initial closed state; conditional latest-summary/exact-`CONTROLLED_ACTIONS` same-row claim; two-claim and both claim/drain orders; action-ledger-before-dispatch; identical Jobs token and zero duplicate runs; asynchronous cancel/current-first Get Run proof including legacy terminal `INTERNAL_ERROR`, conflicts and final inventory; lease takeover without release; closed-before-trust/lifecycle; explicit reopen/retire; external-caller and compromised-App boundary; cost/downtime/status accessibility; candidate/stale/drift/conflict/cardinality denial; browser/actor revoke; same-person denial; and optionality proof |
| D7 | Optional Genie Code skill and any separately accepted read-only Genie Agent material | Six universal passes plus P9 feature-status/security review, curated-input proof, and complete core-product operation with AI disabled |
| D8 | Future Marketplace/provider distribution roadmap only | Six universal passes; remains `future/not available` until provider packaging, install/update/rollback, security review, and commercial claims receive written confirmation |

## Publishing stack decision

Zensical plus GitHub Pages is the current candidate because it supports the desired static navigation style and matches the prior documentation workflow. It is not accepted until the documentation reviewers confirm:

- Accessible theme and navigation behavior.
- WCAG 2.2 AA automated checks plus manual keyboard-only and representative screen-reader tests for complete install, error recovery, investigation, retention, and uninstall processes.
- Stable version and dependency policy.
- Local strict build and link checking.
- Search behavior across the four Diataxis sections.
- Private-repository Pages constraints and intended publication audience.
- Publication-safety controls for generated artifacts and reachable history.

## Documentation definition of done

- A reader can complete the stated outcome without undocumented knowledge.
- Commands and examples are tested against the supported matrix or clearly marked as illustrative.
- Cost, mutation, permissions, and cleanup are visible before the consequential step.
- Expected output and failure recovery are present.
- All required reviews are recorded and resolved.
- The entire rendered site is tested against WCAG 2.2 Level AA as full pages and complete processes with zero known A/AA failure; “conforms” is reserved for a fully passing scope. Critical paths work by keyboard with visible focus, logical order, programmatic status, associated text errors/correction guidance, 200% zoom, 320 CSS-pixel reflow, sufficient contrast, semantic headings/labels, and no color-only meaning.
- At least eight non-author participants cover workstation admin, two fresh verifier administrators, UC operator, combined administrator, dbt owner, read-only operator, and product administrator, plus optional roles. The combined actor understands all false independence flags and meets the 20-minute total-active target including roster work. The verifier-admin and UC actors complete separated apply, killed-actor recovery, App staging, native roster review, trust acceptance/refresh, and lifecycle without credentials, copied query text, SQL, IDs, paths, profiles, capsules, checkpoints, screenshots, or YAML. They distinguish pending data row, direct revoke/current DML/self-grant, composite seal, group roots, direct/effective warehouse authority, candidate versus accepted event, non-independent machine/admin evidence, pre-start transition audit versus post-start-machine/original-roster validity, two validity ages/oldest age/stale, and named roots. No critical task may produce accidental mutation, false success, moderator takeover, abandonment, unplanned running resources, active query, or temporary migration grant; record all active/handoff/platform/escalation/roster/stage time and ease/confidence.
- Real captures are sanitized and independently verified.
