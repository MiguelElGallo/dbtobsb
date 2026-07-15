# Usability and onboarding re-review: P0 planning baseline 0.4

- Reviewed input: frozen author-owned planning file set; repository has no commit yet
- Frozen author-input SHA-256: `8504d49ed1397e218a5760885673c87458d4ecd16d60936191ea0a2d89f48c98`
- Hash scope: `README.md`, `AGENTS.md`, `docs/index.md`, and all Markdown files under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path; SHA-256 of the sorted per-file SHA-256 records
- Date: 2026-07-15
- Reviewer: independent usability and onboarding third re-review
- Verdict: `PASS_WITH_FOLLOW_UP`
- Cloud mutation: none

## Scope and method

I independently recomputed the frozen hash before reviewing baseline 0.4. It exactly matches the value above and the value recorded in `resolution.md`. I read the complete author-owned scope, all three earlier usability reports, and the resolution ledger. I did not edit author-owned files or previous reports.

This review re-evaluates all P0-P10 planning contracts and focuses on the changed identity and installation journeys: stable actor versus browser binding, the nonsecret enrollment locator and accountable identity verification, enrollment acknowledgement and browser-cookie behavior, CSRF and accessibility, the immutable controlled-action approval summary, the workstation gate, exact saved-plan application and `APP_CODE_START`, and cost/recovery. `PASS` means the planning contract is testable; it does not pre-approve implementation evidence assigned to P1-P10.

## Current primary sources checked

- [Databricks App HTTP headers](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/http-headers) identifies `X-Forwarded-User` only as an IdP-provided user identifier, distinguishes it from the forwarded email field, and says forwarded headers exist only inside Databricks Apps. The baseline therefore correctly avoids treating it as a documented opaque workspace-principal ID and rejects locally simulated identity for controlled actions.
- [Databricks App authorization](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/auth) confirms that App authorization uses one dedicated App service principal and cannot itself provide user-level access control; user authorization remains Public Preview. A separate deny-by-default human policy is therefore necessary for the GA shared-App-principal path.
- [Databricks App permissions](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/permissions) distinguishes App `CAN_USE`/`CAN_MANAGE` from data and resource authorization. The baseline preserves this distinction and never treats `CAN_USE` as action authorization.
- [Databricks App secret resources](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/secrets) grants App access at secret-scope level, not per secret. The dedicated per-installation action-key scope containing only required current/previous keys is the understandable least-privilege response.
- [Manage Apps with Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial) documents `bundle run <app-resource-key>` as the command that starts the App resource and shows that Bundle resource deployment does not by itself deploy the App to compute.
- The pinned Databricks CLI 1.7.0 sources expose [`bundle deploy --plan`](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/cmd/bundle/deploy.go#L27-L44), show that a saved plan skips build/pre-deploy checks and that a CLI-version difference only warns in the [saved-plan processing path](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/cmd/bundle/utils/process.go#L240-L265), and implement App start/code deployment in the [`bundle run` App runner](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/run/app.go#L44-L99). These details justify the wrapper's stronger source/build/identity/drift binding and separate `APP_CODE_START` stage.
- [Jobs CLI run representation](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/reference/jobs-commands) includes retained `job_parameters` in run results. The role-administration Job must therefore receive only the explicitly nonsecret request locator, as planned.
- [OWASP session management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) recommends a host-only `__Host-` cookie with `Secure`, `HttpOnly`, `SameSite=Strict`, and `Path=/`, while explicitly warning that `HttpOnly` does not stop CSRF. [OWASP CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) requires independent protection for state-changing requests. The baseline contains both controls rather than confusing them.
- [WCAG accessible authentication](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html) treats copy/paste as a valid way to avoid transcription. [WCAG timing adjustable](https://www.w3.org/WAI/WCAG22/Understanding/timing-adjustable.html), [status messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html), and [error identification](https://www.w3.org/WAI/WCAG22/Understanding/error-identification) support the planned selectable reference, absolute expiry and regenerate path, programmatic status announcements without focus movement, and textual recovery errors.

## Focused acceptance review

| Criterion | Result | Independent evidence |
|---|---|---|
| Frozen input is baseline 0.4 | `PASS` | Independent recomputation produced `8504d49ed1397e218a5760885673c87458d4ecd16d60936191ea0a2d89f48c98`. |
| Stable accountable actor is distinct from a browser profile | `PASS` | `product-plan.md:111-123` keeps the raw forwarded value request-local, maps a versioned installation HMAC alias to a random stable `actor_id` plus identity epoch, keys roles and separation of duties to that actor, and independently binds each browser with a random credential. Actor revocation affects every browser; device revocation affects one. Changed headers, key migration, cookie loss, offboarding, same-string recreation limits, and `UNSUPPORTED` fallback are explicit. |
| Enrollment locator is not mistaken for authorization | `PASS` | `product-plan.md:116-118,365-366` labels the locator nonsecret, gives it one-time/expiry/context checks, makes it the sole retained Job parameter, and keeps the actual approval boundary at the named administrator's `CAN_MANAGE_RUN` permission plus out-of-band accountable-person verification and a constrained governance reference. The App cannot invoke or edit the role Job. |
| Enrollment acknowledgement, cookie, CSRF, and accessibility form one usable journey | `PASS` | `product-plan.md:115,123,365-369` explains the strictly necessary browser credential and Personal Data handling, permits selecting/copying the reference, uses the recommended host-only cookie properties, separately mandates CSRF protection on every state-changing endpoint, keeps read-only access available on identity failure, announces state changes without focus jumps, and provides absolute expiry/copy/regenerate recovery. `documentation-plan.md:155-157` prevents raw identity/credential examples and correctly calls this an acknowledgement rather than Preview App user-authorization consent. |
| `UX-P0-F06` immutable action summary is frozen before P6 | `PASS` | `product-plan.md:120` now enumerates action/environment, bound Job display name, selector, initiator/approver fingerprints, platform caller, actual Job run-as display name, compute/cost consequence, writes, cancellation/reconciliation, retry/idempotency, digest, change detection, and stable outcomes. `product-plan.md:366,448` applies the summary to role approval and non-author task evidence. The contract is resolved; implementation and API-denial evidence remain a P6 gate. |
| Workstation support is safe but not yet published | `PASS_WITH_FOLLOW_UP` | The wrapper already blocks mutation when secure storage is unavailable or plaintext and passes the selected profile explicitly. `product-plan.md:501` correctly retains the exact OS/architecture/assets/secure-store matrix as `UX-P0-F03`, due before any P3 wrapper release. |
| Approved plan is the plan applied | `PASS` | `product-plan.md:330-344` binds the saved Direct plan to the exact CLI, engine, target, profile, host, workspace, principal, variables, Bundle identity/configuration, staged source/build digest, and semantic remote state; immediately re-hashes and re-plans; returns any change to approval; and applies exactly `bundle deploy ... --plan ... --auto-approve`. This compensates for the pinned CLI's warning-only version check and skipped build/pre-deploy phases. |
| Bundle apply and App code/start are understandable separate consequences | `PASS` | The stage is now unambiguously `APP_CODE_START`. `product-plan.md:341-344` leaves managed Apps stopped through Bundle apply, invokes exactly `bundle run <app-resource-key>`, prohibits Bundle-aware bare `apps deploy`, avoids a second Bundle deployment, and defaults to stopping App compute if run/readiness fails. |
| Cost and recovery are visible before commitment | `PASS` | `product-plan.md:334,339,342,352-355,456-461` shows running behavior and App stop/start consequences before approval, separates four lifecycle choices, shows App DBU/hour before start, bounds every live proof, makes the role Job unscheduled and cost-disclosed, stops on failed readiness by default, restores reused resources, and never stops unrelated compute. |

## Identity and enrollment journey review

The revised model has a coherent human mental model and enforcement model:

1. Databricks authenticates the App request and supplies a request-local IdP identifier.
2. The product derives an installation-scoped pseudonymous alias and resolves it to one stable actor and identity epoch.
3. The current browser must also present its separately approved random credential.
4. A first or replacement browser creates an immutable request identified by a nonsecret locator.
5. A named administrator verifies the accountable person outside the App, reviews the stored summary, and invokes a narrow fixed-code Job.
6. FastAPI rechecks actor, browser, role, expiry, revision, revocation, identity epoch, digest, and distinct production actors without an authorization cache before prepare, approve, and run.

This prevents two browser profiles from becoming two human approvers, avoids placing identity or credentials in retained Job parameters, and gives users separate recovery for browser-only loss/revocation and actor-wide offboarding. The plan also states the platform limitation honestly: identical forwarded values after account recreation cannot be detected from this GA header. Customers that require guaranteed detection get `UNSUPPORTED` for actions while retaining read-only observability.

The actor/device expiry and HMAC migration window remains an explicit decision due before P6. That is a legitimate P6 policy and recovery-design gate, not a P0 usability defect. P6 must still prove changed-header linking/re-enrollment, first and additional browsers, same-person denial, cookie loss, key migration, actor/device revocation, CSRF rejection, expiry, and accessible error recovery with non-author users.

## Installation and recovery journey review

The exact primary path is now zero-guess and auditable:

```text
SELECT_WORKSPACE
PREFLIGHT
CHOOSE_RESOURCES
BUNDLE_VALIDATE
BUNDLE_PLAN
APPROVE
BUNDLE_DEPLOY
APP_CODE_START
APP_READY
HANDOFF
```

The administrator begins with one signed wrapper and `dbtobsb bootstrap`, confirms the profile, canonical host, and current identity, selects resources by display name, reviews a plan bound to the deployer's actual context and frozen source/build, approves it, applies that saved plan, and separately starts/deploys App code. A failure reports what changed, what is running, which stages remain, and an exact resume or cleanup action. The protected plan is retained only while an incomplete operation is resumable and otherwise deleted after handoff, rollback, or uninstall.

This resolves the earlier ambiguous `APP_DEPLOY` label. The source-level CLI check also confirms why the wrapper cannot trust the plan file alone: applying a saved plan skips some normal build/pre-deploy work and a CLI-version mismatch warns instead of failing. The stronger sidecar and immediate semantic re-plan are visible, reviewable user protections rather than hidden implementation detail.

## Prior finding and follow-up disposition

| Finding | Baseline 0.4 disposition | Third re-review result |
|---|---|---|
| `UX-P0-001` | Signed wrapper, one command, explicit profile/identity, resumable stages, exact saved-plan apply, separate App code/start, readiness, URL handoff | `RESOLVED`; P3 implementation evidence pending |
| `UX-P0-002` | Eight human roles, minimum grants, owners, residual access, separated duties, and distinct ACL/resource/action-role views | `RESOLVED` |
| `UX-P0-003` | Five scanner outcomes; only `NEEDS_CHANGES` can propose a patch | `RESOLVED` |
| `UX-P0-004` | Full-page and complete-process WCAG 2.2 AA contract with manual and automated evidence | `RESOLVED`; implementation evidence remains at each relevant part |
| `UX-P0-005` | Separate pollable Operation and RFC 9457 Problem contracts with safe recovery | `RESOLVED` |
| `UX-P0-006` | Named non-author personas, numeric task/safety/ease thresholds, and fresh confirmation users | `RESOLVED`; sessions remain a P3-P10 gate |
| `UX-P0-F01` | Numerical live-proof ceiling, cancellation, owner, end state, and scoped inventory | `RESOLVED` at contract level; P8 live proof pending |
| `UX-P0-F02` | Stop, remove configuration, retain/export, and irreversible delete/verify are separate actions | `RESOLVED` at contract level; P7 evidence pending |
| `UX-P0-007` | CLI 1.7.0 is consistently an exact pinned GA deployment-only dependency | `RESOLVED` |
| `UX-P0-F03` | Exact supported workstation/architecture, signed assets, verification, secure store, prerequisites, and unsupported-platform behavior due before release | `OPEN`; only remaining usability follow-up and hard P3 release gate |
| `UX-P0-F04` | Scoped pre/post inventory protects reused and unrelated resources | `RESOLVED`; P8 live proof pending |
| `UX-P0-F05` | All normative gates use “high or critical” consistently | `RESOLVED` |
| `UX-P0-F06` | Immutable action summary and change/digest/revalidation behavior now enumerated | `RESOLVED` at contract level; P6 task and API evidence pending |

## Remaining finding

### `UX-P0-F03`: publish and test the private-alpha workstation matrix

- Classification: `PASS_WITH_FOLLOW_UP`
- Severity: medium
- Owner: P3 Bundle-installer owner
- Target: before any P3 wrapper asset is released or documented as supported
- Current safety: P0 publishes no installer asset, and the regulated path already blocks mutation when secure storage is unavailable or plaintext. This does not defer a current mutation-safety control.
- Acceptance:
  1. Name every supported OS version and architecture, signed wrapper asset, embedded CLI asset, shell/browser prerequisite, verification command, and OS-native secure-store backend.
  2. Give unsupported combinations a stable preflight code and non-mutating recovery message.
  3. From a clean instance of every claimed combination, test signature/checksum verification, no-profile recovery, explicit profile propagation, secure-store success and failure, plan review, exact saved-plan apply, resume, `APP_CODE_START`, URL handoff, and uninstall.

No new `CHANGES_REQUIRED` or `BLOCKER` finding was found.

## P0-P10 no-regression matrix

These verdicts assess the adequacy of baseline 0.4 planning. Later-part evidence named below remains mandatory and is not being treated as already implemented.

| Part | Third re-review verdict | Usability/onboarding result |
|---|---|---|
| P0 — Product contract | `PASS_WITH_FOLLOW_UP` | The current install, read-only use, identity, action-approval, recovery, cost, and lifecycle contracts are testable. Only `UX-P0-F03` remains, correctly bounded before P3 release. |
| P1 — Capture library | `PASS` | Safe fail-closed validation and user-facing field/category/impact/remediation requirements remain intact; P1 fixtures must supply the evidence. |
| P2 — Collector and reconciliation | `PASS` | Job, dbt, collector, and capture outcomes, recovery bounds, cancellation, timeout, and safe deep links remain distinct and testable; P2 must prove them. |
| P3 — Bundle installer | `PASS_WITH_FOLLOW_UP` | The exact saved-plan and `APP_CODE_START` journey, explicit profile, secure-store fail-closed behavior, resumability, cost consequence, and handoff pass. Close `UX-P0-F03` before release. |
| P4 — App read-only MVP | `PASS` | Curated-only access, distinct outcomes, safe Operation/Problem recovery, cost confidence, and full-process accessibility remain intact; P4 supplies implementation evidence. |
| P5 — Job onboarding | `PASS` | Five scanner states, source-controlled proposed patch, semantic-change review, approval, rollback, and no direct default mutation remain intact. |
| P6 — Controlled actions | `PASS` | Stable actor plus browser binding, nonsecret locator, accountable administration, cookie/CSRF/accessibility, exact grants, immutable summary, same-person denial, and no-cache revalidation form an adequate planning contract. `UX-P0-F06` is resolved; P6 implementation, denial, and non-author task evidence remain mandatory. |
| P7 — Security and operations | `PASS` | Actor/device/role review, identity epoch/key rotation, offboarding, separate lifecycle choices, orphan prevention, and deletion verification are explicit; P7 must prove them. |
| P8 — Bounded live proof | `PASS` | The numeric envelope, unconditional cleanup, scoped inventory, reused-state restoration, and unrelated-resource protection remain explicit; live evidence is correctly deferred to P8. |
| P9 — Optional intelligence | `PASS` | AI remains advisory and optional and cannot construct, authorize, capture, or validate a dbt action. |
| P10 — Private alpha | `PASS` | Non-author personas, safety-critical task success, time/ease thresholds, fresh confirmation, and the common high-or-critical severity gate remain measurable. |

## Documentation-plan re-review

The documentation plan remains `PASS`.

It carries the exact pre-App bootstrap, saved-plan/source/drift evidence, `bundle run` App start, human and runtime roles, stable actor/browser vocabulary, enrollment acknowledgement, nonsecret locator, action approval summary, accessibility/recovery behavior, cost, and four lifecycle choices into distinct tutorial, how-to, reference, and explanation pages. It also preserves independent subject, Diataxis, FastAPI-style, security/compliance, usability/accessibility, and rendered-site passes.

The future `reference/installer-platforms-and-secure-storage.md` must close `UX-P0-F03` before the wrapper is described as supported. The optional controlled-action documentation remains a D6 deliverable and must use real sanitized first/additional-browser, approval-summary, revocation, and key-recovery evidence only after the P6 task tests pass. These are appropriate later-part gates, not missing P0 implementation.

## Final verdict

`PASS_WITH_FOLLOW_UP` for frozen baseline 0.4.

The changed identity and installation contracts resolve `UX-P0-F06` and introduce no new blocking usability defect. The design now keeps the stable human actor separate from browser credentials, treats the enrollment reference as a nonsecret locator rather than authorization, requires accountable out-of-band verification, combines secure cookie properties with independent CSRF protection, supports accessible enrollment recovery, applies exactly the approved saved plan, and makes App code/start and its cost consequence explicit. `UX-P0-F03` remains a hard gate before publishing P3 workstation support and may not move past that part. No Azure or Databricks resource was created, started, stopped, or deleted by this review.
