# Usability and onboarding fifth re-review: P0 planning baseline 0.6

- Reviewed input: frozen author-owned planning file set; repository has no commit yet
- Frozen author-input SHA-256: `96257d1f55152d92d303852a9f057a419c0d77bdc5a553cb4d92cea0cf4b173e`
- Hash scope: `README.md`, `AGENTS.md`, `docs/index.md`, and all Markdown files under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path; SHA-256 of the sorted per-file SHA-256 records
- Date: 2026-07-15
- Reviewer: independent usability and onboarding fifth re-review
- Verdict: `CHANGES_REQUIRED`
- Cloud mutation: none

## Scope and method

I independently recomputed the frozen hash before reviewing. It exactly matched the assigned value. I read the complete author-owned scope, the earlier usability reviews, and the current finding-resolution record. I did not edit an author-owned file, an earlier review, or a cloud resource.

This pass re-evaluates every P0-P10 contract for a safe and understandable non-author experience. The focused checks were: one signed entry point; no user-entered SQL, internal IDs, constructed paths, or YAML; the customer-owned schema handoff; actor, plan, receipt, and state distinctions; attended OAuth U2M handoffs; cleanup-only `SEAL_REQUIRED` recovery; optional system-enrichment separation; reversible versus destructive lifecycle choices; closure of `UX-P0-008`; the bounded `UX-P0-F03` workstation follow-up; task success, error recovery, and accessibility.

The baseline now fixes the invalid saved-Direct-seal design. It keeps Direct away from customer-schema grants, approves one exact targeted lease and matching revoke, audits before every mutation, makes residual authority cleanup-only, cancels or waits for migration compute before the revoke, independently verifies the effective seal, and blocks App binding/start until seal and data verification both pass. The resource, data, seal, runtime, and App-start receipts are distinguishable. Those changes resolve the substance of `UX-P0-008`.

One high-severity journey defect remains. The enterprise path says separated duties are normative and promises a resumable handoff, but the executable bootstrap is still rooted in one workstation user's local mode-`0600` checkpoint and one selected profile. It does not define how the deployment operator hands the active operation to the attended UC operator, how the correct actor/profile is proved before lease and seal, how control returns, or how a U2M credential cached in the local user's profile is released. That is not a prose detail: the exact handoff is the authorization and recovery boundary for temporary schema DDL.

## Current sources checked

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) is still the current W3C Recommendation and applies conformance to full pages and complete processes. Its relevant AA requirements include visible and unobscured focus, error identification, labels/instructions, accessible authentication, and programmatically determinable status messages.
- [Azure Databricks OAuth U2M authorization](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/auth/oauth-u2m) states that browser login creates or uses a configuration profile and caches the OAuth credential in the user's home context. The product therefore cannot equate “dbtobsb does not persist a token” with “the borrowed operator credential leaves no local residue.”
- The current [Azure Databricks `auth` command reference](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/reference/auth-commands) says `auth describe` exposes the selected profile and current user, `auth logout` clears cached OAuth tokens, and `auth logout --delete` may also remove a profile. It also warns that profiles and cached tokens are local authentication state that can be shared or selected ambiguously.
- [Azure Databricks configuration profiles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/auth/config-profiles) documents named profiles, the local configuration location, explicit profile selection, and the `DEFAULT` fallback. This supports the baseline's explicit-profile rule but makes the missing cross-actor profile lifecycle material.
- [GOV.UK moderated usability testing](https://www.gov.uk/service-manual/user-research/using-moderated-usability-testing) recommends realistic, goal-based tasks with actual or likely users. [GOV.UK usability benchmarking](https://www.gov.uk/service-manual/measuring-success/usability-benchmarking-a-website-or-whole-service) measures completion, time, abandonment or false success, ease, and confidence. The baseline's role-specific tasks and separation of active time from platform wait remain appropriate.
- The [PatternFly CLI handbook](https://www.patternfly.org/content-design/writing-guides/cli-handbook/) recommends specific text rather than vague failure, text in addition to color, keyboard-accessible prompts, and non-interactive-safe behavior. The baseline's append-only text, `--no-color`, JSON, stable codes, and explicit recovery actions align with that guidance.

## Focused acceptance review

| Criterion | Result | Independent evidence |
|---|---|---|
| One signed entry point | `PASS_WITH_REQUIRED_FIX` | `product-plan.md:350-382` keeps one signed wrapper and first command, `dbtobsb bootstrap`, with verified assets, explicit workspace/profile, resumable stages, and URL handoff. The one-person path is coherent. The two-person path lacks an executable actor handoff; see `UX-P0-009`. |
| No entered SQL, internal IDs, paths, or YAML | `PASS` | Resource choice uses display names, migration SQL is fixed review material rather than input, Job parameters are closed, and `product-plan.md:375-382` expressly prohibits those manual inputs. |
| Customer-owned schema handoff | `PASS` | `product-plan.md:116-135,164-180,370-377` makes the schema a typed prerequisite, names its accountable owner, distinguishes direct from inherited grants, preserves foreign assignments, and gives missing ownership/privilege a responsible next actor. The documentation plan has dedicated preparation, migration-envelope, residual-authority, and runtime-plan tasks. |
| Resource, migration, seal, runtime, and App-start consequences | `PASS` | `product-plan.md:122-133,362-380` gives each plane its own stage, approval, receipt, mutation boundary, and success condition. `documentation-plan.md:230` enumerates seven distinct receipts rather than collapsing them into “both plans.” |
| Attended U2M separated-duties handoff | `FAIL` | `product-plan.md:166,172,180` calls the separated path normative and promises resumable handoffs, but `product-plan.md:352-380` begins from one user's profile/checkpoint and has no actor-handoff, temporary-profile, credential-release, or return-of-control contract. Current Databricks U2M stores local profile/cache state. See `UX-P0-009`. |
| Cleanup-only `SEAL_REQUIRED` recovery | `PASS_WITH_REQUIRED_FIX` | The state and permitted actions are now correct: audit first, cancel/wait, exact revoke, verify direct/effective absence, start nothing else. Recovery still depends on obtaining the right UC operator without a defined safe handoff and without silently reusing another person's cached token. |
| App unavailable until seal and independent verification | `PASS` | Runtime binding is generated only after `DATA_SEAL_VERIFY` and `DATA_VERIFY`; runtime apply leaves the App stopped; App code/start is a separate cost-bearing action. |
| First value proves observability | `PASS` | Fixture evidence, an explicitly cost-confirmed real one-model run, and a query of the expected row precede `Observable`. Job, dbt, collector, and capture outcomes remain distinct. |
| Optional system enrichment | `PASS` | It is absent and disabled in the base route. Its separate route names the data owner, principal, paused Job, exact broad source scope, immediate filter, three snapshots/views, cost/freshness/degradation, and complete removal. |
| Cost and running-resource trust | `PASS` | Plans show cost before compute; Jobs are unscheduled/bounded; schedules start paused; App start is explicit; test envelopes name ceilings, cancellation, cleanup owner, and scoped final inventory. |
| Lifecycle decision safety | `PASS` | Stop compute, remove code/configuration, retain/export, irreversible delete/verify, and uninstall are separate outcomes. Retain is default, ownership transfer is visible, and customer schema/grants are never removed by implication. |
| Accessibility and status/recovery | `PASS` | The complete App/site processes target WCAG 2.2 AA with manual keyboard/screen-reader evidence; CLI output has append-only text, `--no-color`, JSON, stable exits, no spinner-only state, and specific safe recovery. Operation and RFC 9457 Problem representations remain separate. |
| Workstation support | `PASS_WITH_FOLLOW_UP` | The baseline correctly leaves exact supported OS/architecture/assets/secure-store behavior as `UX-P0-F03`, a hard P3 release gate. That bounded implementation follow-up does not excuse the product-level two-actor handoff gap. |

## Ranked finding

### `UX-P0-009`: Make the attended UC-operator handoff executable and release its local credential state

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Owner: P3 installer owner, with Databricks, security, documentation-usability, and usability re-review
- Affected evidence: `docs/decisions/0001-private-app-bundle.md:25-27,51-53`; `docs/plans/product-plan.md:108,122-131,164-180,350-380,425-433,482-496`; `docs/plans/documentation-plan.md:36-49,177-230,289-315`; `docs/research/source-register.md:14-16,42-44`
- Baseline evidence: The deployment begins with one selected profile and a per-user mode-`0600` local checkpoint. Every child command must use that profile. The normative enterprise path nevertheless assigns the lease and seal to a different attended UC operator and promises a resumable handoff. The named stages jump from migration-envelope approval to lease apply without defining where the second person works, how they receive the exact immutable operation, how the wrapper switches profiles without `DEFAULT` or stale-environment precedence, how the deployment actor regains control, or how cached U2M state is removed or deliberately retained for cleanup.
- Primary-source evidence: Databricks documents U2M as a browser login that saves a configuration profile and caches a credential in the local user's context. The current CLI can describe the actual profile/user and can clear cached OAuth state with `auth logout`, optionally deleting a profile. Profiles can be ambiguous and are usable by other unified-auth tools. The security boundary therefore includes local profile/cache ownership and cleanup, not only whether dbtobsb copies a token.
- User and system impact: A deployment operator can accidentally execute the lease as themselves, a UC operator can leave a powerful cached credential in another person's OS account, or two people on separate workstations can reach a dead end because the protected checkpoint/envelope has no supported handoff. After process death in `TEMPORARY_DDL_ACTIVE`, the deployment operator may see “reauthenticate the UC operator” but have no safe way to do so. These are wrong-actor mutation, residual-credential, abandonment, and false-recovery risks at the highest-trust installation boundary.
- Required change:
  1. Choose and document exactly one supported separated-duties topology for v1. Define where each actor runs the wrapper, where the protected checkpoint and envelope stay, how a nonsecret digest-bound handoff is conveyed, and how control returns. Mark other topologies `UNSUPPORTED`; do not leave the user to improvise file sharing, screen sharing, or profile reuse.
  2. Keep `dbtobsb bootstrap` as the canonical entry. Add visible actor-bound handoff stages before approval/lease and before cleanup when required. Each stage must show role, profile display name, canonical host, current user, operation/migration digest, exact allowed next consequence, and who resumes afterward. A wrong human, profile, host, digest, expired handoff, or changed state must fail before mutation.
  3. Specify the local OAuth lifecycle honestly. If v1 uses an ephemeral UC-operator profile on a controlled workstation, the wrapper must create an unambiguous wrapper-owned name, never overwrite/reuse a customer profile, never rely on `DEFAULT`, explain that Databricks caches a short-lived credential, and clear/delete only that wrapper-owned profile/cache after a verified seal and again on abandoned-operation cleanup. If a pre-existing operator-owned profile is supported, it must remain on that person's managed OS account and the design must define a customer-local handoff that does not copy its token or the deployer's private checkpoint.
  4. Do not discard the only usable cleanup authority while `TEMPORARY_DDL_ACTIVE`. Process death, token expiry, logout failure, operator unavailability, wrong-profile recovery, and multiple profiles sharing a token need explicit visible states and safe actions. They may block installation, but must never unlock migration, runtime binding, App start, or another mutation.
  5. Add a handoff/credential receipt that records only safe facts: pseudonymous or display-safe actor reference, profile label, current-user verification occurrence, host/workspace binding, authentication time/expiry class, operation digest, lease/seal action, and credential-release result. It must contain no raw token, forwarded identity, email in public evidence, config path, or token-cache content.
  6. Add the handoff to the installation how-to/page registry and error-code routes. The user-facing recovery must say who is needed, whether temporary authority or compute remains, what that person will be asked to approve, and what will be safe after completion.
  7. Kill-test the two-actor path on every claimed workstation combination: wrong actor/profile/host; stale environment authentication precedence; pre-existing same-host profiles; process/network death before and after lease; token expiry; failed logout; return to deployment control; and cleanup-only resume. No participant manually enters SQL, an internal ID, a path, or YAML.
- Acceptance condition: A non-author deployment operator and a different non-author UC operator complete fresh install, abrupt-interruption recovery, upgrade, and retain/delete lifecycle rehearsals through one documented topology. Neither shares credentials nor improvises a checkpoint transfer; every mutation is attributed to the intended current person; every handoff returns to the right operation; a wrong or unavailable actor fails closed with a clear next step; the final receipt proves effective DDL absent, no migration/App compute running, and no wrapper-created borrowed U2M profile/cache left usable. Safety-critical task success is 100% with zero false success, abandonment, wrong-workspace/wrong-actor mutation, or moderator takeover.

No other new high, critical, or blocking usability finding was found.

## Prior finding and follow-up disposition

| Finding | Baseline 0.6 disposition | Fifth re-review result |
|---|---|---|
| `UX-P0-001` | Signed wrapper, one first command, explicit profile/identity, resumable stages, secure checkpoint, URL handoff | `REOPENED IN PART` by `UX-P0-009`: the one-person path passes, but the canonical command does not yet define the second human's profile/checkpoint handoff |
| `UX-P0-002` | Nine roles, grant owner, residual access, combined and separated paths | `REOPENED IN PART` by `UX-P0-009`: role names and prerequisites pass; promised separated-duties choreography is not executable |
| `UX-P0-003` | Five scanner outcomes; only `NEEDS_CHANGES` can propose a patch | `RESOLVED` |
| `UX-P0-004` | Full-page and complete-process WCAG 2.2 AA scope with manual and automated evidence | `RESOLVED` at contract level; implementation evidence remains required per part |
| `UX-P0-005` | Separate pollable Operation and RFC 9457 Problem contracts with safe fields and recovery | `RESOLVED` |
| `UX-P0-006` | Role-specific non-author tasks, safety/time/ease/confidence thresholds, and fresh confirmation users | `RESOLVED` as a test contract; `UX-P0-009` adds the missing two-actor handoff rehearsal |
| `UX-P0-F01` | Numerical live-proof ceiling, cancellation, owner, stopped/paused end state, scoped inventory | `RESOLVED` at contract level; P8 evidence pending |
| `UX-P0-F02` | Stop, remove configuration, retain/export, irreversible delete/verify are separate | `RESOLVED` at contract level; P7 evidence pending |
| `UX-P0-007` | CLI 1.7.0 is exact, pinned, GA, and deployment-only | `RESOLVED` |
| `UX-P0-F03` | Exact workstation/architecture, assets, prerequisites, secure-store backend, and unsupported errors | `OPEN`; bounded hard P3 release gate. Extend its clean-machine matrix with the accepted `UX-P0-009` actor/profile lifecycle, but do not merge the product-level handoff decision into this implementation-only follow-up |
| `UX-P0-F04` | Scoped pre/post inventory protects reused and unrelated resources | `RESOLVED`; P8 evidence pending |
| `UX-P0-F05` | Normative gates use “high or critical” consistently | `RESOLVED` |
| `UX-P0-F06` | Immutable controlled-action summary and digest/change/revalidation behavior | `RESOLVED` at contract level; P6 evidence pending |
| `UX-P0-008` | Post-lease targeted seal, cleanup-only restart, exact receipts, interruption tests, no manual SQL/IDs/paths/YAML | `RESOLVED` for lease/seal chronology and state semantics. `UX-P0-009` is the distinct human-authentication handoff needed to execute that correct recovery design safely |

## P0-P10 no-regression matrix

| Part | Fifth re-review verdict | Usability and onboarding result |
|---|---|---|
| P0 — Product contract | `CHANGES_REQUIRED` | The baseline is coherent for one person, and `UX-P0-008` is resolved. The normative separated-duties journey is not complete until `UX-P0-009` defines its actor/profile/checkpoint/credential-release boundary. |
| P1 — Capture library | `PASS` | Artifact/log validation, fail-closed states, safe messages, and distinct outcome models remain testable without Databricks. |
| P2 — Collector and reconciliation | `PASS` | DML-only collection, separate run/capture outcomes, bounded reconciliation, operator action, and cancellation/timeout states remain clear. |
| P3 — Bundle installer | `CHANGES_REQUIRED` | One command, typed schema, exact plans, no manual internals, cleanup-first seal, and stopped App lifecycle pass. The required two-actor U2M path and credential release do not. `UX-P0-F03` also remains the bounded release gate. |
| P4 — App read-only MVP | `PASS` | Base App is useful without system enrichment or actions; status/recovery, cost confidence, full-process accessibility, and read-only handoff remain adequate planning gates. |
| P5 — Job onboarding | `PASS` | Five scanner states, source-controlled patch, semantic-change review, owner approval, and rollback remain understandable and safe. |
| P6 — Controlled actions | `CHANGES_REQUIRED` | The optional action journey is otherwise explicit and locked until complete, but its data upgrade inherits the same attended UC-operator lease/seal handoff and must adopt `UX-P0-009` before P6 acceptance. |
| P7 — Security and operations | `CHANGES_REQUIRED` | Retain/delete, ownership transfer, grant preservation, export, rollback, and uninstall choices pass. Credential release and wrong/unavailable-operator cleanup must become part of the incident, access-review, upgrade, and uninstall runbooks. |
| P8 — Bounded live proof | `CHANGES_REQUIRED` | Cost, grant preservation, no-op, App-query, kill-boundary, and no-running-resource evidence are well scoped. The proof must add two-actor profile/cache and return-of-control cases from `UX-P0-009`. |
| P9 — Optional intelligence | `PASS` | AI remains visibly optional, read-only/advisory, and outside authorization, command construction, mutation, capture, and validation. |
| P10 — Private alpha | `CHANGES_REQUIRED` | The alpha cannot claim a repeatable enterprise install or upgrade until two different non-author humans complete the normative U2M handoff and recovery without credential sharing, improvised transfer, false success, or moderator takeover. |

## Re-review condition

Freeze a revised author set after `UX-P0-009` is resolved. The next usability pass should be focused but must re-check P0, P3, P6, P7, P8, and P10; the one-command and no-manual-internal promises; the human-role table; all named stages and receipts; `SEAL_REQUIRED`; the installation and recovery documentation routes; and `UX-P0-F03` ownership. `PASS_WITH_FOLLOW_UP` is appropriate only if the U2M handoff is fully specified and the sole remaining usability item is the bounded P3 clean-workstation evidence gate.
