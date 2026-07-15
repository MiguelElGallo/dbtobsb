# Databricks platform/security seventh re-review: P0 planning baseline

- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform/security reviewer
- Immutable author input SHA-256: `185113f8218872fc934f40ecce588b255507fdfd400bdbde6f0c7755e48ebe3f`
- Verdict: `CHANGES_REQUIRED`
- Cloud mutation: none

## Immutable input verification

I recomputed the requested digest before reviewing. The input set was `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path. Each file was hashed with SHA-256, the resulting records were concatenated in sorted order, and that stream was hashed again.

The result was exactly:

```text
185113f8218872fc934f40ecce588b255507fdfd400bdbde6f0c7755e48ebe3f
```

No author file or previous review was changed during this review. This report is the only file written.

## Executive assessment

Baseline 0.8 resolves the decisive migration-Job custody defect from the sixth review. There is no privileged migration Job, migration service principal, or Jobs-output receipt carrier. The protected data path is now an attended OAuth U2M actor executing signed, fixed, parameter-bound statements through the Statement Execution API. The Direct runtime Bundle is structurally separated from the customer-owned schema, grants, DDL, ledger write, and receipt seal. That is a materially safer and simpler architecture, and `DBX-P0-013` is resolved for P0.

Baseline 0.8 also resolves most of `DBX-P0-014`: it names exact temporary ledger `SELECT` and `MODIFY`, exact targeted revokes, a closed durable Delta row, a sanitized read-only view, duplicate/conflict behavior, and the fact that Jobs output is not authoritative. The remaining seal and recovery semantics are not yet implementable exactly as written:

1. The plan promises that a different eligible UC actor can inspect, poll, or cancel an indeterminate Statement Execution operation and complete cleanup, but the minimum prerequisite is only warehouse `CAN_USE`. Databricks documents that only the executing user can fetch that statement's results. Cross-user query inspection/cancellation instead relies on Query History and at least warehouse `CAN VIEW`, a different and more revealing authority that the plan does not grant or threat-model. The API also continues a statement after its wait timeout unless `on_wait_timeout: CANCEL` is selected.
2. The claimed terminal receipt row is written while the UC actor still has ledger `SELECT` and `MODIFY`; only afterward are those privileges revoked and their absence checked. That row cannot contain an observed post-revoke authority digest or terminal seal outcome. In addition, a schema owner or `MANAGE` holder can manage child objects and grant itself data privileges, so removing the direct temporary pair is not the same as removing the actor's effective capability. The plan acknowledges that customer UC authority is a trusted residual, but several seal claims still say effective authority is absent.
3. The platform boundary is described inconsistently. The product plan correctly gives the collector, optional enrichment Job, role Job, and optional App narrowly enumerated DML. The review and documentation plans then say the runtime Bundle, App, collectors, and all other Jobs cannot mutate product data. This can produce an impossible P2/P4/P6/P8 test contract and overstates runtime evidence integrity. The deployment/product administrator that can manage runtime Job definitions and use their run-as service principals is also a trusted runtime-code/evidence root unless the product introduces separate post-deploy custody.

These are fail-closed design gaps rather than a reason to abandon the private App plus Direct Bundle starting point. They do, however, affect recovery from actor loss, residual privilege truthfulness, and evidence integrity in the regulated path, so P0 cannot pass yet.

## Current primary evidence checked

All sources below are official Microsoft/Databricks documentation or first-party Databricks source.

### Statement Execution identity, timeout, and recovery

- [Statement Execution API tutorial](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/sql-execution-tutorial) states that the authenticated caller needs Databricks SQL entitlement, warehouse `CAN USE`, and the Unity Catalog privileges used by each statement. It also states that only the user who executed a statement can fetch that statement's results.
- The same [Statement Execution API tutorial](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/sql-execution-tutorial) documents a `wait_timeout` of 5-50 seconds and that a statement continues by default when the wait expires. `on_wait_timeout: CANCEL` must be selected to request cancellation at that boundary.
- [Query History](https://learn.microsoft.com/en-us/azure/databricks/sql/user/queries/query-history) states that another user can view query runs with at least `CAN VIEW` on the warehouse and documents cancelling a running query started by another user. That is broader than the baseline's `CAN USE` prerequisite and exposes query text and execution details, so it must be an explicit recovery authority and disclosure if selected.
- [Query History system table](https://learn.microsoft.com/en-us/azure/databricks/admin/system-tables/query-history) is Public Preview and account-wide/current-region. It cannot be silently introduced into the GA required recovery path, especially because the base product otherwise excludes query-history system access.

### Unity Catalog receipt authority

- [Unity Catalog permissions model concepts](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/access-control/permissions-concepts) states that table reads require parent `USE` plus `SELECT`, writes require parent `USE` plus `MODIFY`, ownership implies all capabilities on the owned object, and `MANAGE` does not itself grant data access but lets its holder grant that access to itself.
- The same permissions model states that ownership does not inherit downward, but a catalog or schema owner can manage all child objects. Consequently, transferring the ledger to a receipt-security group does not isolate it from an attended actor who remains the parent schema owner or another named `MANAGE`/administrator root.
- [Manage Unity Catalog privileges](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/manage-privileges/) confirms that an object owner, parent catalog/schema owner, `MANAGE` holder, or applicable administrator can grant and revoke privileges. The self-grant/revoke lifecycle therefore needs one exact residual authority model.
- [`GRANT`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/security-grant), [`REVOKE`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/security-revoke), and [parameter markers](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-parameter-marker) support a fixed, typed implementation. Parameter markers separate literal values from SQL structure, and `IDENTIFIER` can bind object names. They do not solve the post-revoke attestation ordering problem by themselves.

### Runtime Bundle, App resources, and Job trust

- [Direct Bundle deployment engine](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/direct) remains the current GA/new-product direction. The baseline appropriately pins it and separates Direct resources from the attended data plane.
- First-party CLI 1.7.0 [`grants.go`](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/dresources/grants.go#L120-L193) computes remote principals absent from desired state and sends `REMOVE ALL_PRIVILEGES`. Omitting Direct schema grants is therefore still the correct customer-grant-preservation decision.
- [Add a Unity Catalog table resource to a Databricks App](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/tables) confirms that an App table/view binding refers to an existing object and automatically grants the App principal exact parent use plus `SELECT` or table `MODIFY`. Views are select-only. The baseline correctly plans bindings only after data-object verification.
- [Lakeflow Jobs identities and permissions](https://learn.microsoft.com/en-us/azure/databricks/jobs/privileges) states that `CAN MANAGE` can edit a Job's tasks, configuration, and permissions and that a run uses the configured run-as identity. [Service-principal roles](https://learn.microsoft.com/en-us/azure/databricks/security/auth/access-control/service-principal-acl) separately governs who can run Jobs as a service principal. These facts no longer endanger a privileged migration Job, because none exists, but they do make runtime Job managers trusted for the DML and actions available to each runtime principal.
- [Restrict workspace admins](https://learn.microsoft.com/en-us/azure/databricks/admin/workspace-settings/restrict-workspace-admins) remains defense in depth for owner/run-as changes. Baseline 0.8 correctly treats account/workspace/metastore and data owners as trusted roots rather than claiming admin-resistant separation.

### Current feature direction

- [Non-interactive transaction mode](https://learn.microsoft.com/en-us/azure/databricks/transactions/transaction-modes) is a current Statement Execution capability for compatible SQL warehouses. P3 may evaluate it for bounded groups of supported DML, but the P0 design is correct not to claim that heterogeneous multi-object DDL, ownership changes, grants, and revokes are one atomic transaction without qualification.
- App OpenTelemetry, App user authorization, query-history system tables, Genie/MCP features, and audit-table enrichment remain outside the required GA path in this baseline. Their optional/Preview treatment is appropriate.

## Ranked findings

| Rank | Finding | Severity | P0 effect |
|---:|---|---|---|
| 1 | `DBX-P0-015` - replacement-actor Statement Execution recovery lacks a supported authority and bounded-operation contract | High | Blocks P0; `CHANGES_REQUIRED` |
| 2 | `DBX-P0-016` - the durable row is written before the revoke it claims to seal, and direct-grant absence is conflated with effective capability | High | Blocks P0; `CHANGES_REQUIRED` |
| 3 | `DBX-P0-017` - runtime data-plane and trusted-manager claims contradict the required collector/action DML | Medium | Must be corrected across P0/P2/P4/P6/P8 before acceptance |

### DBX-P0-015: replacement-actor Statement Execution recovery lacks a supported authority and bounded-operation contract

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Affected contract:
  - `AGENTS.md`, Product boundaries, the UC operator's poll/cancel/recovery ownership
  - `docs/decisions/0001-private-app-bundle.md`, Decision, recovery audit, and mandatory cleanup
  - `docs/plans/product-plan.md`, data-plane steps 3-6, bootstrap recovery steps 2/8, platform readiness, P3/P7/P8, staging interruption tests, and cost cleanup
  - `docs/plans/documentation-plan.md`, interrupted migration and residual-authority recovery routes
- Evidence:
  1. Baseline 0.8 requires each normal actor only to have warehouse `CAN_USE` and its own U2M profile.
  2. It promises that an eligible replacement UC actor can inspect an original actor's indeterminate Statement Execution operation, cancel or complete it, revoke the original actor's exact temporary ledger privileges, and seal safely.
  3. Databricks documents that only the user who executed the statement can fetch its Statement Execution results. A different actor does not inherit that result authority merely by having the same UC data privileges.
  4. Databricks documents cross-user query visibility/cancellation through Query History when the second user has at least warehouse `CAN VIEW`. Baseline 0.8 neither grants this permission nor accepts its access to other users' full query text and execution details. The optional `system.query.history` source is Public Preview and is not a valid hidden base dependency.
  5. Statement Execution continues after the normal wait timeout unless the request uses `on_wait_timeout: CANCEL`. The plan says bounded and polled but does not freeze this request policy, the maximum statement lifetime, or the behavior when a cancellation request is accepted but execution still reaches a race terminal state.
  6. The actor-owned checkpoint intentionally stores no raw identity or rendered revoke statement. A replacement actor still needs an unambiguous durable mapping from the product-created direct grant to the exact principal that must be revoked; deriving that by broadly revoking an unexpected live principal is prohibited and unsafe.
- User/system impact: loss or lock of the original actor's U2M profile can leave an operation uninspectable through the promised API path, a warehouse query still active, and temporary receipt-table authority unresolved. The product correctly blocks runtime, but a permanent fail-closed stall is not the claimed recoverable cleanup path and can violate the no-running-resource and revocation evidence promised for P7/P8.
- Required acceptance condition:
  1. Select one exact GA cross-actor recovery design and document its minimum privileges, information exposure, owner, and denial behavior. If it uses Query History, require and review warehouse `CAN VIEW`, use a stable API/UI path that is live-qualified, and disclose that the recovery actor can see other query text/details on the selected shared warehouse. Do not depend on the Preview query-history system table.
  2. Alternatively, explicitly prohibit a replacement from fetching the original Statement Execution result. Bound every mutation with a reviewed per-request timeout/cancel policy and a maximum terminalization window, then let the replacement reconstruct state only after that window from durable ledger/UC post-state. Do not claim cross-user poll/cancel in that variant.
  3. Freeze `wait_timeout`, `on_wait_timeout`, one-request/one-operation behavior, cancel-race precedence, response-loss behavior, warehouse auto-stop interaction, and the longest time before replacement cleanup may proceed. A cancellation request is not proof that a statement did not commit.
  4. Before the direct grant is applied, durably record an exact, privacy-reviewed cleanup locator that a replacement can map to one principal and one privilege pair without carrying credentials, relying on another actor's private checkpoint, or revoking a foreign grant. State whether this restricted locator is Personal Data and how it is removed/retained.
  5. Add P8 tests with two genuinely different U2M users: original actor process death and secure-store loss before/after submit, wait-timeout continuation/cancel, accepted-cancel/commit race, replacement visibility denial, replacement exact revoke, no unrelated query exposure beyond the accepted model, and a final inventory with no active statement or product-created temporary grant.

### DBX-P0-016: the durable row is written before the revoke it claims to seal, and direct-grant absence is conflated with effective capability

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Affected contract:
  - `README.md` and `AGENTS.md`, terminal Delta seal and effective-absence claims
  - `docs/decisions/0001-private-app-bundle.md`, terminal receipt fields and runtime unlock
  - `docs/plans/product-plan.md`, data-object boundary steps 4-9, human residual access, bootstrap receipt stages, readiness, upgrade/uninstall, and P3/P7/P8 evidence
  - `docs/plans/documentation-plan.md`, every Delta-seal, residual-authority, migration, and lifecycle page
- Evidence:
  1. The UC actor writes the one “terminal” ledger row while the actor still has direct ledger `SELECT` and `MODIFY`.
  2. The wrapper then revokes those privileges and only afterward checks direct/inherited/ownership/`ALL PRIVILEGES`/`MANAGE`/group paths.
  3. A row written before the revoke cannot contain an observed post-revoke effective-authority digest or attest that the revoke and subsequent verification completed. At most it can bind the intended final authority state or record `DATA_VERIFIED_PENDING_REVOKE`.
  4. The plan gives the attended UC actor ownership or sufficient complete-visible authority to create/transfer product objects and grant/revoke the ledger pair. If that authority is schema ownership or `MANAGE`, Databricks says the actor can manage the child ledger and grant itself data privileges even after the direct pair is removed.
  5. The plan elsewhere correctly calls that customer-provided UC authority a trusted residual and says the receipt is not tamper-proof against the receipt owner, UC/metastore authority, or administrators. The phrases “effective absence,” “terminal row,” and “remote row ... unlocks runtime” do not consistently preserve that distinction.
- User/system impact: an implementation can place an expected, pre-revoke digest in a row and present it as observed terminal evidence, or can reject every valid schema-owner operator because that actor retains implied child-management authority. Either result weakens the audit meaning of the seal. A malicious or compromised trusted UC/schema authority remains able to regrant itself access; that may be an accepted customer trust root, but the receipt must not claim otherwise.
- Required acceptance condition:
  1. Define an implementable two-phase semantic contract. For example, the actor-owned row can be a durable `DATA_APPLIED_PENDING_REVOKE` attestation containing the expected final authority digest; after revoke, the returning actor independently reads live permissions and accepts only the tuple `(matching remote data row, matching observed final authority, no indeterminate statement, mode gate)`. In that design, stop calling the row alone terminal or sealed.
  2. If a customer-security-owned remote terminal row must itself attest the post-revoke observation, add a distinct finalizer identity/actor that does not rely on the revoked writer's DML and define its exact privilege, invocation, custody, recovery, and receipt fields. Do not reintroduce an editable privileged Job.
  3. Separate these facts in the schema and UI: exact product-created direct grant removed; effective `SELECT`/`MODIFY` through any other path; ability to self-grant through ownership/`MANAGE`; named trusted residual authorities; and the exact observation time/actor. Never label direct-grant removal as total effective-capability absence.
  4. Freeze which Statement Execution IDs can be written. The receipt-writing statement cannot know its own API statement ID before submission; either exclude it, record only prior operation IDs, or add a later finalization mechanism.
  5. Test an operator who is the schema owner, one with table `MANAGE`, one with inherited `ALL PRIVILEGES`, and one with only bounded create/transfer authority. The resulting receipt and readiness outcome must state the residual truth and must preserve foreign customer grants.

### DBX-P0-017: runtime data-plane and trusted-manager claims contradict the required collector/action DML

- Verdict: `CHANGES_REQUIRED`
- Severity: medium
- Affected contract:
  - `docs/plans/review-process.md`, Databricks reviewer remit and P8 matrix
  - `docs/plans/documentation-plan.md`, production bootstrap and writing rules
  - `docs/plans/product-plan.md`, runtime identities, P2/P4/P6/P8, trusted roots, and tests
- Evidence:
  1. The product plan correctly grants the collector principal `SELECT` plus `MODIFY` on the three normalized evidence tables. Optional enrichment writes three snapshots. P6 gives the App and role-administration Job exact DML on restricted action tables.
  2. The review process and documentation plan say the runtime Bundle, App, collectors, and other Jobs cannot mutate “product data,” and the P8 usability focus says there is no runtime mutation of data or receipt.
  3. Direct deployment itself need not run SQL or mutate the data contract, but Jobs that Direct creates are deliberately runtime DML actors. Conflating resource deployment with resource execution makes the least-privilege contract internally impossible.
  4. The deployment/product administrator can manage those Job definitions. Under the Jobs permission model, a `CAN MANAGE`/owner principal can change tasks/configuration/permissions, and runs use the configured service principal. Unless custody is separately transferred, that administrator is a trusted root for collector evidence integrity, optional enrichment output, and role-Job authorization state.
- User/system impact: implementation tests can either prohibit the collector behavior needed for observability or silently weaken the documentation claim. More importantly, a regulated customer could infer that normalized evidence and optional action state are protected from the runtime deployer when the current Job/Service Principal User model does not provide that protection.
- Required acceptance condition:
  1. Replace “cannot mutate product data” with the exact boundary: the Direct **deployment path** and runtime graph contain no schema/table/view DDL, migration SQL, ledger DML, or receipt write; each runtime principal may DML only its enumerated tables during execution.
  2. Keep receipt DML prohibited for every runtime principal. Name normalized evidence, enrichment snapshots, and action-state tables separately rather than using an ambiguous “product data.”
  3. Either add the deployment/product administrator and any principal with Job `CAN MANAGE` plus relevant Service Principal User/Manager authority to the explicit runtime-code/evidence trusted-root register, or define and test post-deploy Job ownership/manager/run-as custody. Do not imply that the durable migration receipt protects later runtime evidence from an authorized Job editor.
  4. Add negative tests that each runtime principal cannot cross its table set, plus a drift test showing how an out-of-band Job edit is detected and presented before its evidence is trusted.

## Prior-finding disposition

| Finding | Seventh re-review disposition |
|---|---|
| `DBX-P0-001` | `RESOLVED_FOR_P0`; the observed Job and collector Job retain different run-as identities and only the collector has exact evidence-table DML. |
| `DBX-P0-002` | `RESOLVED_FOR_P0`; bounded scheduled and operator reconciliation cover collector-not-started attempts, with visible degradation. |
| `DBX-P0-003` | `RESOLVED_FOR_P0`; App access remains separate from the optional server-side human action policy. |
| `DBX-P0-004` | `RESOLVED_FOR_P0`; tier, Apps, Unity Catalog, warehouse, identity, region, and compliance prerequisites are typed and fail closed. |
| `DBX-P0-005` | `RESOLVED_FOR_P0`; required runtime public-internet egress is zero and build/deployment supply-chain routes are explicit. |
| `DBX-P0-006` | `RESOLVED_FOR_P0`; system enrichment is absent from base, separately installed, dedicated-principal, pair-filtered, and removable. P4/D4E/P8 evidence remains mandatory before enablement. |
| `DBX-P0-007` | `RESOLVED_FOR_P0`; App `CAN_USE`/`CAN_MANAGE` is separate from App resource bindings. |
| `DBX-P0-008` | `RESOLVED_FOR_P0` for the actor/browser policy; the role-Job manager's runtime trust must now be stated under `DBX-P0-017`. |
| `DBX-P0-009` | `RESOLVED_FOR_P0`; protected saved Direct plans, stopped App lifecycle, and separate `bundle run` remain coherent. |
| `DBX-P0-010` | `RESOLVED_FOR_P0`; Direct owns supported App/Job resources, the attended fixed data plane owns DDL, and bindings require existing objects. |
| `DBX-P0-011` | `PARTIALLY_RESOLVED`; cleanup-first behavior and exact revokes are present, but cross-actor operation recovery and terminal seal ordering remain open as `DBX-P0-015`/`016`. |
| `DBX-P0-012` | `RESOLVED_FOR_P0`; Direct schema grants remain prohibited and fixed targeted changes preserve unrelated assignments. |
| `DBX-P0-013` | `RESOLVED_FOR_P0`; baseline 0.8 removes the privileged migration Job, its editable code path, its migration service principal, and the Jobs-output attestation path. No deployer-owned remote Job can execute the temporary data authority. |
| `DBX-P0-014` | `PARTIALLY_RESOLVED`; exact temporary ledger DML, targeted revoke, closed Delta row/view, conflict behavior, and no Jobs carrier are frozen. Post-revoke receipt semantics and replacement recovery remain open as `DBX-P0-015`/`016`. |
| `DBX-P0-F01` | `RESOLVED_FOR_P0`; the contract expands ownership, implied privileges, `MANAGE`, transitive groups, caller visibility, and pagination. P3 must implement the visibility algorithm and distinguish direct-grant removal from residual effective capability. |
| `DBX-P0-F02` | `RESOLVED_FOR_P0`; optional enrichment retains the exact workspace/Job pair scope, regional/account-global disclosure, three snapshots, exclusions, DML-only scope updates, and disabled base. |

## Author-file outcome

| Author file or set | Outcome | Databricks conclusion |
|---|---|---|
| `README.md` | `CHANGES_REQUIRED` | The migration Job/SP removal is correct, but the durable row is described as the terminal seal before the post-write revoke is observed. |
| `AGENTS.md` | `CHANGES_REQUIRED` | Strong fixed-SQL and runtime-Bundle boundaries; cross-actor Statement Execution recovery and “effective absence” need implementable semantics. |
| `docs/index.md` | `PASS` | Navigation only; no independent platform defect. |
| `docs/decisions/0001-private-app-bundle.md` | `CHANGES_REQUIRED` | Recommended architecture remains sound, but the accepted decision overclaims replacement poll/cancel and terminal receipt semantics. |
| `docs/plans/product-plan.md` | `CHANGES_REQUIRED` | DBX-P0-013 is resolved; DBX-P0-015/016/017 affect P3/P6/P7/P8 and the regulated trust boundary. |
| `docs/plans/review-process.md` | `CHANGES_REQUIRED` | It incorrectly says the collector and all runtime Jobs cannot mutate product data despite required narrow DML. |
| `docs/plans/documentation-plan.md` | `CHANGES_REQUIRED` | D2/D5 would teach an impossible terminal-row ordering and an overbroad no-runtime-DML claim. |
| `docs/research/source-register.md` | `CHANGES_REQUIRED` | Add Statement Execution result identity, timeout/cancel behavior, Query History cross-user `CAN VIEW`/query-text exposure, and the selected cross-actor recovery decision. |

## P0-P10 Databricks coverage matrix

These are planning-contract outcomes, not implementation acceptance.

| Part | Planning outcome | Databricks conclusion and next evidence |
|---|---|---|
| P0 - Product contract | `CHANGES_REQUIRED` | Resolve `DBX-P0-015`/`016` and correct `017`; then freeze and re-hash the complete contract. |
| P1 - Capture library | `PASS` | Pure parsing, closed schemas, hashing, and allowlists remain platform-independent and appropriately bounded. |
| P2 - Collector and reconciliation | `PASS_WITH_FOLLOW_UP` | Separate run-as, exact three-table DML, no DDL, `ALL_DONE`, and bounded reconciliation are sound; wording must explicitly allow this narrow runtime DML and name its manager trust. |
| P3 - Bundle installer | `CHANGES_REQUIRED` | Add an implementable Statement Execution timeout/replacement model and two-phase seal semantics while retaining no migration Job/SP, no Direct schema grants, and verified existing-object bindings. |
| P4 - App read-only MVP | `PASS_WITH_FOLLOW_UP` | Curated-view base and disabled system enrichment remain sound; correct the ambiguous no-runtime-mutation claim and validate App binding grant/removal behavior. |
| P5 - Job onboarding | `PASS` | Five-state scan, owner approval, source patch, and no direct default mutation of customer Jobs remain sound. |
| P6 - Controlled actions | `CHANGES_REQUIRED` | Its attended data upgrade inherits `DBX-P0-015`/`016`; role-Job managers are trusted for action-state integrity unless separate custody is added. |
| P7 - Security and operations | `CHANGES_REQUIRED` | Recovery, actor loss, trusted residual authority, direct-grant versus effective capability, runtime-manager trust, upgrade, rollback, and uninstall runbooks must use the corrected contracts. |
| P8 - Bounded live proof | `CHANGES_REQUIRED` | Test two-user Statement Execution recovery permissions, timeout/cancel races, exact cleanup locator, schema-owner/`MANAGE` residuals, two-phase receipt acceptance, runtime DML boundaries, and zero running resources. |
| P9 - Optional intelligence | `PASS` | AI remains optional and outside capture, migration, receipt, runtime authorization, and cleanup enforcement. |
| P10 - Private alpha | `CHANGES_REQUIRED` | Combined/separated journeys are coherent, but neither may claim recoverable actor loss or a terminal remote seal until P3/P7/P8 prove the corrected platform contract. |

## Cloud-mutation statement

This review made no Azure or Databricks authentication call, REST/CLI workspace call, SQL statement, Bundle operation, App/Job/warehouse action, identity/grant change, resource creation, resource deletion, or paid-compute start. It used only local read-only repository inspection, current public first-party web research, and this review-file write.

## Explicit verdict

`CHANGES_REQUIRED`

The private Databricks App deployed through a pinned plain-YAML Direct Bundle remains the recommended starting point. Baseline 0.8 successfully eliminates the privileged migration Job/service-principal custody problem and replaces the expiring Jobs carrier with a customer-owned durable Delta authority.

P0 still cannot pass because the contract promises cross-actor Statement Execution recovery without the permission and bounded-operation mechanism that Databricks requires, and it labels a row written before privilege revocation as the terminal post-revoke seal. Correct those semantics, distinguish a removed product direct grant from residual trusted management authority, and state the exact narrow runtime DML and runtime-manager trust boundary. Then request another focused Databricks re-review against one new immutable author-set hash.
