# Databricks platform focused second re-review: P0 planning baseline 0.3

- Reviewed input: frozen author-owned planning file set
- Author-input SHA-256: `3e81a74f338000c7441bcb0a643991e958b34f469d71112d81e18b555a5561ae`
- Date: 2026-07-15
- Reviewer: independent Databricks product and platform specialist
- Verdict: `CHANGES_REQUIRED`
- Blockers: none; the private Databricks App plus plain-YAML Bundle direction remains sound
- Cloud mutation: none; no Azure or Databricks resource was created, started, or changed

## Immutable input verification

The author-input scope in `resolution.md` is `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path. I independently hashed every scoped file and then hashed the sorted `shasum -a 256` output. The result was exactly:

```text
3e81a74f338000c7441bcb0a643991e958b34f469d71112d81e18b555a5561ae
```

Reviewer-owned files and the resolution ledger are not author input. I read the ledger and both earlier Databricks reports for finding history. This report is the only file I created or changed.

## Executive outcome

Baseline 0.3 correctly updates the platform baseline to GA Databricks CLI `1.7.0` and the GA Direct engine, pins both in Bundle YAML, removes unused Terraform/HashiCorp inputs, separates Bundle resource deployment from App code deployment/start, adds the narrow App table resources, and defines a deny-by-default FastAPI policy independently of App `CAN_USE`. `DBX-P0-004` and the maturity, pinning, state, drift, and restricted-egress portions of `DBX-P0-009` are resolved for P0.

Two current correctness and security conditions remain:

1. The plan assumes `X-Forwarded-User` is an opaque stable identifier that the installer can obtain from a workspace identity lookup. The official header page only calls it an IdP-provided identifier. The first-party CLI `1.7.0` local Apps proxy populates that header with `iam.User.UserName`, which is normally an email-style Databricks username. The added identity-management sources do not establish an exact, GA mapping from an installer-selected Databricks identity ID to the production header value. This leaves both authorization operability and the stated no-email ledger contract unproved.
2. The human action-role administrator is granted only table `SELECT` and `MODIFY` in the plan. An installer running SQL as that human also needs `CAN_USE` on the selected SQL warehouse, `USE CATALOG`, and `USE SCHEMA`; the claimed time-bounded administration grant has no enforced revoke path. Separately, the approved Direct plan is not bound to `bundle deploy`, and CLI `1.7.0` makes bare `databricks apps deploy` in a Bundle project run another Bundle deployment before starting the App. The canonical installer must state commands that apply the exact approved plan once and do not silently repeat resource deployment in the App-code stage.

These defects are correctable without changing the accepted architecture, but they cannot be deferred as P3/P6 follow-ups because they determine whether the P0 authorization and no-mutation-before-approved-plan contracts are executable.

## Current official primary sources checked

### CLI, Direct engine, and App deployment lifecycle

- [Databricks CLI release types](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/)
- [Databricks CLI 1.7.0 immutable release and assets](https://github.com/databricks/cli/releases/tag/v1.7.0)
- [Databricks CLI 1.3.0: Direct became GA and the default for new deployments](https://github.com/databricks/cli/releases/tag/v1.3.0)
- [Bundle configuration reference](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/reference)
- [Direct-engine state, precedence, drift, and compatibility behavior](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/direct)
- [Manage Apps with Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial)
- [Bundle App resources, including UC table and Job permissions](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/resources)
- [CLI 1.7.0 `bundle deploy --plan` implementation](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/cmd/bundle/deploy.go#L27-L44)
- [CLI 1.7.0 Bundle-aware `apps deploy` implementation](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/cmd/apps/deploy_bundle.go#L89-L111)
- [Bundles in an air-gapped environment](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/airgapped-environment)

### Apps, actor identity, and Unity Catalog authorization

- [App authorization](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/auth)
- [App permissions](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/permissions)
- [App HTTP headers](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/http-headers)
- [CLI 1.7.0 local Apps proxy header construction](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/libs/apps/runlocal/headers.go#L8-L17)
- [App resources](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/resources)
- [Unity Catalog table resources for Apps](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/tables)
- [Unity Catalog permission concepts](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/access-control/permissions-concepts)
- [SQL warehouse permissions](https://learn.microsoft.com/en-us/azure/databricks/compute/sql-warehouse/create)
- [Statement Execution API prerequisites](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/sql-execution-tutorial)
- [Identity-management best practices](https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/best-practices)
- [Manage groups](https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/manage-groups)
- [Automatic identity management and external-ID cautions](https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/automatic-identity-management/)
- [Workspace Users API maturity](https://docs.databricks.com/api/workspace/users)
- [`SHOW USERS` output contract](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-syntax-aux-show-users)

### Runtime dependency and restricted-egress boundary

- [Manage App dependencies](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/dependencies)
- [Configure App networking](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/networking)
- [Serverless network policies](https://learn.microsoft.com/en-us/azure/databricks/security/network/serverless-network-security/network-policies)

## Finding disposition

| Finding | Second re-review outcome | Evidence and remaining condition |
|---|---|---|
| `DBX-P0-001` | `RESOLVED_FOR_P0` | No regression. The cross-Job Run Job topology and independent job-level run-as principals remain explicit, with live positive and negative permission tests assigned to P2/P3. |
| `DBX-P0-002` | `RESOLVED_FOR_P0` | No regression. Bounded scheduled/operator reconciliation, a 20-minute target, degraded behavior, and exactly-once fixtures remain explicit. |
| `DBX-P0-003` | `PARTIALLY_RESOLVED` | Stable App authorization, optional Preview enrichment, product roles, separation of duties, and a product ledger are selected. The actor subject key and administrator privilege path are not yet executable as written; see `DBX-P0-008`. |
| `DBX-P0-004` | `RESOLVED_FOR_P0` | The workspace gates, environment 5/Python 3.12.3, exact dbt pair, GA CLI 1.7.0, explicitly pinned Direct engine, and Current-channel SQL warehouse form a typed candidate contract. Support remains conditional on the planned fixtures and staging qualification. |
| `DBX-P0-005` | `RESOLVED_FOR_P0` | No regression. Public runtime egress is zero; build/deploy inputs are separately locked, signed/checksummed, mirrored/offline or allowlisted. The Direct path correctly removes Terraform/HashiCorp destinations. |
| `DBX-P0-006` | `RESOLVED_FOR_P0` | No regression. The App has no broad system-schema access, system enrichment is scoped and optional, and shared-warehouse cost stays allocated/estimated. |
| `DBX-P0-007` | `RESOLVED_FOR_P0` | No regression. Named App groups, no broad default group, separate ACL/resource diffs, and scoped uninstall removal remain explicit. |
| `DBX-P0-008` | `PARTIALLY_RESOLVED` | The App's `MODIFY`-only ledger resource, `SELECT`-only binding resource, deny-by-default checks, individual roles, expiry/revocation, same-person denial, and Preview-disabled tests are now present. The header-to-binding identity join, Personal Data treatment, and complete enforced human-administration grant remain unresolved. |
| `DBX-P0-009` | `PARTIALLY_RESOLVED` | GA status, exact pins, Direct precedence, state/drift qualification, separate App deployment, and recalculated egress are correct. The canonical deploy step does not yet consume the exact approved JSON plan, and the App-code stage does not name a command that avoids a second implicit Bundle deployment. |

## Required P0 corrections and exact acceptance

### DBX-P0-008: The human subject key and action-role administration path are not yet executable

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: ADR **Decision**; product plan **Runtime identity model**, **Human action authorization**, **Human role and prerequisite model**, P3, P6, and P7; source register identity/header rows
- Evidence:
  - Databricks says shared App authorization gives all App users the service principal's resource permissions and does not provide user-level authorization. The custom FastAPI policy is therefore the actual human safety boundary.
  - The Apps header page says `X-Forwarded-User` is an identifier supplied by the IdP; it does not call the value an opaque Databricks principal ID or guarantee that it equals an ID returned by workspace/account identity lookup.
  - CLI `1.7.0`'s first-party local proxy sets `X-Forwarded-User` to `iam.User.UserName`. Azure Databricks user names are ordinarily email addresses. Automatic identity management separately warns that `externalId` can change and recommends that custom workflows not depend on it.
  - The stable user-list/join path is not established by the two added identity sources. The Workspace Users API is Public Preview, IAM v2 identity resolution is Beta, and documented `SHOW USERS` returns principal names rather than a documented opaque forwarded subject.
  - UC requires `USE CATALOG`, `USE SCHEMA`, and the table operation privilege. Statement Execution also requires `CAN_USE` on the warehouse. Product-plan line 106 gives the action-role administrator only table `SELECT` and `MODIFY`, and records a review/expiry date without an enforced revoke mechanism.
- User/system impact: Authorized people can be denied because the selected ID never matches the header, or an implementation can silently fall back to email as the authorization key and ledger actor despite the no-email promise. A role administrator can also fail at runtime, receive an unreviewed broad grant, or retain direct binding-table write access beyond the approved window.
- Required change:
  1. Select one source-backed production actor-key and enrollment flow. It must derive the binding key from the same proxy-authenticated value FastAPI checks, avoid Preview/Beta identity APIs on the required path, and never ask a user to paste an ID. If the raw header can contain a username/email, classify it as Personal Data and persist only a defined pseudonymous derivative unless an explicit reviewed decision permits the raw value.
  2. Define normalization, tenant/workspace scope, collision handling, identifier rename/recreation behavior, key rotation, binding migration, expiry, revocation, and safe failure. An unsupported or ambiguous identity state must block action enablement.
  3. Name the identity that executes role-binding SQL and grant it exactly `CAN_USE` on the chosen warehouse, `USE CATALOG`, `USE SCHEMA`, and table-level `SELECT` plus `MODIFY` on `action_role_bindings`. It receives no schema/catalog `MODIFY`, ownership, `MANAGE`, normalized-table write, or diagnostic Volume access.
  4. Make the administration window real: either grant just in time and revoke in a `finally`/recovery path, or define another enforced expiry mechanism. A date displayed in the plan is not an expiring UC grant. Preserve and distinguish pre-existing customer grants.
  5. Keep the App principal's existing narrow resources: warehouse `CAN_USE`, parent usage, `SELECT` on bindings, and `MODIFY` only on the ledger. It must never modify its authorization source.
- Testable acceptance:
  1. In a production-mode Azure Databricks App request, two distinct selected users map deterministically to two distinct binding keys; the installer and FastAPI compute the same key without storing or displaying the raw header/email. A local simulated header cannot authorize a deployed action.
  2. Missing, blank, malformed, ambiguous, renamed, recreated, cross-tenant, expired, revoked, and wrong-workspace subjects all fail closed before approval or Job start. Identifier recovery has an explicit administrator action and ledger trail.
  3. A read-only `CAN_USE` user receives the stable denial response through direct API access, no Job run starts, and an in-App denial is safely ledgered.
  4. The action-role administrator can perform an authorized binding change with only the listed warehouse/UC grants. The same operation fails when each grant is independently removed.
  5. Success, process failure, cancellation, and interrupted resume each end with the temporary administrator table-write grant removed; pre-existing grants are unchanged.
  6. The App can read bindings and write the ledger but cannot change bindings, normalized evidence, unrelated tables, or the diagnostic Volume. The required journey passes with App user authorization, IAM v2, Workspace Users API, and `system.access.audit` unavailable.

### DBX-P0-009: The reviewed Direct plan is not bound to deploy, and App deployment can repeat Bundle mutation

- Classification: `CHANGES_REQUIRED`
- Severity: medium
- Affected contract: ADR **Consequences**; product plan **Runtime egress and supply chain**, **Bootstrap the product**, P3, and P8
- Evidence:
  - CLI versions 1.0.0+ are GA; the immutable CLI 1.7.0 release and SHA-256 asset exist. CLI 1.3.0 made Direct GA/default. The Bundle reference supports an exact CLI constraint and an explicit `bundle.engine: direct` that takes precedence over the environment. These baseline corrections are valid.
  - Direct keeps local and remote state separately and documents drift behavior. CLI 1.7.0 can emit JSON plans and `bundle deploy --plan <file>` can apply a saved Direct plan.
  - The plan currently runs `bundle plan -o json`, obtains approval, and later runs plain `bundle deploy`, which can calculate a different plan. It does not bind the approved plan, target, profile, configuration hash, or installer checkpoint to the mutation.
  - Official App Bundle guidance says Bundle deployment does not deploy App code to compute. In CLI 1.7.0, however, bare `databricks apps deploy` inside a Bundle project executes Bundle deployment and then runs the App. An unnamed APP_DEPLOY command can therefore repeat resource mutation after the approved Bundle stage.
- User/system impact: A changed local file or remote state can make deployment mutate something the administrator did not approve. A resumed App-code stage can also re-enter Bundle deployment, weakening idempotency, recovery reporting, and the promised cost/start boundary.
- Required change:
  1. Persist the JSON Direct plan as a secret-free checkpoint artifact with its SHA-256, target, canonical host/profile identity, Bundle/input hash, engine, CLI checksum/version, and creation time. Approval records that exact digest.
  2. Apply the approved plan with the CLI 1.7.0 Direct saved-plan path, or document an equally strong fail-closed binding. Any target/profile/engine/config/remote-state mismatch requires a new plan and approval before mutation.
  3. Name the exact App-code deployment/start command or API. It must not invoke a second Bundle resource deployment after `BUNDLE_DEPLOY`. Generated policy must keep `lifecycle.started` absent/false for the new-install Bundle resource stage so paid App compute begins only in the explicit App stage.
  4. Keep the already-correct egress split: exact signed/checksummed wrapper and CLI inputs; App Python/Node build sources or UC Volume/private mirror; workspace/App domains; no unused Terraform provider, Terraform registry, or HashiCorp destination.
- Testable acceptance:
  1. Generated YAML contains exact `databricks_cli_version: '1.7.0'` and `engine: direct`; an engine environment variable cannot override it.
  2. The reviewed JSON-plan digest is the digest passed to deploy. Editing YAML, switching profile/target, changing engine, or creating representative remote drift after approval fails before mutation and requires a new plan.
  3. New-install `BUNDLE_PLAN` and `BUNDLE_DEPLOY` do not start App compute. `APP_DEPLOY` deploys code/starts once without re-entering Bundle deployment; resume after each stage performs no duplicate non-idempotent mutation.
  4. Create, no-op, update, rollback, destroy, unsupported-field, and documented drift fixtures cover every v1 resource and grant, including both App UC table resources.
  5. A restricted-egress install/start succeeds using only the disclosed Direct/App dependency destinations; observed outbound denials prove no Terraform/HashiCorp destination is attempted. Cleanup leaves the App stopped and test schedules paused.

## P0-P10 Databricks part matrix

| Part | Outcome | Databricks conclusion and exact remaining evidence |
|---|---|---|
| P0 — Product contract | `CHANGES_REQUIRED` | Close the remaining `DBX-P0-008` and `DBX-P0-009` conditions in the author contract and freeze/re-review the affected input. They are current safety/operability requirements, not later enhancements. |
| P1 — Capture library | `PASS_WITH_FOLLOW_UP` | No regression. Keep typed attempt identity, actual compatibility metadata, and no live Databricks dependency. |
| P2 — Collector and reconciliation | `PASS_WITH_FOLLOW_UP` | No regression. Live proof still must assert both effective run-as principals, both negative permission boundaries, cancellation/timeout recovery, and one AttemptKey. |
| P3 — Bundle installer | `CHANGES_REQUIRED` | The plan must include the executable administrator warehouse/UC grants, enforced revoke, exact approved-plan application, non-redeploying App-code command, and stopped-before-App-stage assertion. |
| P4 — App read-only MVP | `PASS_WITH_FOLLOW_UP` | No regression. Curated-only reads, no broad system access, statelessness, cost confidence, and accessibility scope remain sound. Keep mutation routes disabled until P6 passes. |
| P5 — Job onboarding | `PASS_WITH_FOLLOW_UP` | No regression. Preserve five scanner states, source-controlled semantic-change review, Run Job topology, grants, and rollback visibility. |
| P6 — Controlled actions | `CHANGES_REQUIRED` | The deny-by-default policy shape is good, but the exact production subject-key/enrollment contract and no-email evidence must exist before controlled actions can be accepted. |
| P7 — Security and operations | `CHANGES_REQUIRED` | Access review, revocation, incident handling, export/deletion, and uninstall must cover the pseudonymous actor key, binding migration, enforced administrator-grant removal, and preservation of customer grants. |
| P8 — Bounded live proof | `PASS_WITH_FOLLOW_UP` | The cost/cleanup envelope remains sufficient. Add the approved-plan digest proof, zero second Bundle deployment, actor mapping, and restricted-egress observations to the scoped live evidence. |
| P9 — Optional intelligence | `PASS_WITH_FOLLOW_UP` | No regression. AI remains outside authorization, command construction, capture, and validation. |
| P10 — Private alpha | `PASS_WITH_FOLLOW_UP` | Retain Preview-disabled and separated-role journeys. Include identity rename/recreation recovery and one non-author install where no raw actor email enters persisted product evidence. |

## Final verdict

`CHANGES_REQUIRED`

There is no architecture blocker. The GA CLI/Direct correction is accepted, and the App's narrow resource-grant direction is right. P0 can return for another focused Databricks review after the author makes the subject-key/enrollment contract source-backed, completes and enforces the human administrator grant set, and binds the exact approved Direct plan to a non-redeploying App start sequence.
