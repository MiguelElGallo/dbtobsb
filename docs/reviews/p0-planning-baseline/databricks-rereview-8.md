# Databricks platform/security eighth re-review: P0 planning baseline

- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform/security reviewer
- Immutable author input SHA-256: `ca6df928ba9353ffa240f7a5c21ab9a7cccf68bf682145d58ad18f83de536d1a`
- Verdict: `CHANGES_REQUIRED`
- Cloud mutation: none

## Immutable input verification

I recomputed the requested digest before reviewing. The input set was `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path. Each file was hashed with SHA-256, the resulting records were concatenated in sorted order, and that stream was hashed again.

The result was exactly:

```text
ca6df928ba9353ffa240f7a5c21ab9a7cccf68bf682145d58ad18f83de536d1a
```

No author file or earlier review was changed. This report is the only file written. I made no Azure, Databricks, authentication, SQL, warehouse, App, Job, or Unity Catalog call; this was a static author-set and current official-documentation review.

## Executive assessment

Baseline 0.9 is substantially stronger than baseline 0.8. It resolves the previous Statement Execution recovery, attestation ordering, and runtime-boundary findings:

- `CAN_MONITOR` is now an explicit, privacy-reviewed permission on a dedicated installer-only warehouse. It supports the planned cross-user Query History visibility while the original submitting user remains the only user allowed to fetch Statement Execution results.
- Every request contains one operation, `wait_timeout=50s` is within the documented 5-50 second range, `on_wait_timeout=CANCEL` is explicit, cancellation is nonterminal, and HTTP timeout/cancel races are reconciled against Query History plus live Unity Catalog state without blind mutation retry.
- A verified read-only preparation marker precedes every mutation. The full-text marker carries a closed operation locator and exact cleanup target, and the recovery actor scans a narrow dedicated-warehouse/time window through the GA Query History API before using the native Query History cancellation UI. That is a suitable bounded cleanup locator; it is not misrepresented as the durable business receipt.
- The Delta row is correctly called `DATA_APPLIED_PENDING_REVOKE`, contains completed prior Statement Execution IDs but not its own unknown ID, and makes no post-revoke claim. Runtime acceptance comes from a later composite observation.
- The composite separates exact product direct-grant absence, current effective `SELECT`/`MODIFY`, ownership/`MANAGE` self-grant capability, trusted residual roots, the mode gate, and indeterminate-query state. `SHOW GRANTS` completeness is conservatively tied to object/container ownership or `MANAGE`; workspace-admin status alone is not used as the Unity Catalog proof.
- The collector, base/P6 App, role-administration Job, optional enrichment Job, and observed Job have explicit and internally consistent DML sets. Job/App managers, service-principal roles, deployment principals, object owners, and administrators are named as trusted roots rather than being described as platform-resistant.

Two current-scope correctness gaps remain.

1. The required path promises complete transitive group, service-principal-role, Job/App-manager, grant, and configuration observation before data or actions are presented as trusted, but it does not define one supported observer, privilege set, API/SQL algorithm, identity-model constraints, freshness rule, or cadence capable of producing that complete result. This is especially material for automatic identity management, nested groups that are not API-referenceable, and Service Principal User/Manager rules exposed through a Public Preview account-access-control API. The base App and runtime writers do not possess the declared administrative visibility.
2. The seal verifier is explicitly a workspace administrator. Azure Databricks gives workspace administrators `CAN MANAGE` on workspace objects, so the same verifier effectively has warehouse management authority even though the plan repeatedly says the two operator groups receive `CAN_MONITOR`, “not ... `CAN_MANAGE`,” and reserves stop/escalation for a named warehouse manager. The direct group ACL can be `CAN_MONITOR`; the effective actor authority cannot be described that way.

Both gaps affect claims required in P0 and the regulated P3/P6/P7/P8 paths. The first is high severity because it controls whether the composite seal and later runtime evidence may be labeled verified. The second is medium severity because it changes the actual recovery and trusted-root boundary. Under the repository's review policy, P0 therefore remains `CHANGES_REQUIRED`.

## Current primary evidence checked

All sources below are current official Microsoft/Databricks documentation or first-party API reference.

### Statement Execution and Query History

- The [Statement Execution API tutorial](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/sql-execution-tutorial) documents `wait_timeout` values from 5 through 50 seconds, the `on_wait_timeout: CANCEL` request behavior, warehouse/data privilege prerequisites, and that only the user who executed a statement can fetch its results. Baseline 0.9 uses those boundaries correctly and does not let a replacement actor fetch another user's result.
- [Query History](https://learn.microsoft.com/en-us/azure/databricks/sql/user/queries/query-history) documents that a user with at least `CAN VIEW` on the warehouse can see another user's query runs, including complete query text and execution details, and can cancel a running query started by another user. `CAN_MONITOR` supplies the intended monitored-query experience while also allowing execution.
- The [Query History API](https://docs.databricks.com/api/azure/workspace/queryhistory/list) lists statements with warehouse, user, status, statement, and time filters plus pagination. It is appropriate for the plan's dedicated-warehouse/narrow-time client-side marker match. Cancellation remains a native Query History UI action in the frozen design; the listing API is not falsely described as a cancellation endpoint.
- Query tags and the `system.query.history` table are not required. This preserves the baseline's GA required path.

### Warehouse effective authority

- The [SQL warehouse ACL table](https://learn.microsoft.com/en-us/azure/databricks/security/auth/access-control/#sql-warehouse-acls) distinguishes query use/monitoring from warehouse management. A raw `CAN_MONITOR` grant is not warehouse ownership and does not itself confer stop/edit/delete/permission management.
- The broader [workspace access-control model](https://learn.microsoft.com/en-us/azure/databricks/security/auth/access-control/) states that workspace administrators have `CAN MANAGE` on all workspace objects. Because the frozen verifier is a workspace administrator, testing only the directly assigned `CAN_MONITOR` group ACL does not establish the verifier's effective warehouse boundary.

### Unity Catalog grants and composite observation

- [Unity Catalog privilege concepts](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/access-control/permissions-concepts) distinguishes parent `USE`, table `SELECT`/`MODIFY`, dynamically expanded `ALL PRIVILEGES`, object ownership, and `MANAGE`. `MANAGE` is not current data access but permits self-grant; owners have all capabilities on the object. Baseline 0.9's direct/current-DML/self-grant split matches that model.
- [`SHOW GRANTS`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/security-show-grant) and [manage Unity Catalog privileges](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/manage-privileges/) support all-affecting grant inspection by an appropriate administrator, owner, or `MANAGE` holder with the necessary parent use. Requiring object/container ownership or `MANAGE` is a conservative complete-visibility prerequisite and also correctly names the verifier as a self-grant trusted root.
- The [effective permissions API](https://docs.databricks.com/api/azure/workspace/grants/geteffective) returns effective inherited permissions and paginates them. Baseline 0.9 correctly requires every page, including continuation after an empty page with a next token. That API does not by itself define the complete identity-group and service-principal-role inventory algorithm promised by the runtime-trust manifest.

### Groups, nesting, and observation freshness

- [Manage groups](https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/manage-groups) documents account-group administration and the workspace-domain Account Groups proxy, and states that automatic identity management supports nested groups whereas SCIM provisioning does not. A stable account-group proxy is available; the defect is not absence of any group API.
- [Automatic identity management](https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/automatic-identity-management/) documents that authorization refreshes transitive membership on activity-dependent schedules, only for groups added to Databricks. It also documents that nested groups and service principals not directly provisioned to the account can be visible in the UI but cannot be retrieved or managed through Databricks APIs or Terraform. A recursive walk of API-returned direct members therefore is not a complete algorithm for every supported automatic-identity configuration.
- [`SHOW GROUPS`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-syntax-aux-show-groups) can show the direct and indirect groups containing one named user or group, but it requires an administrator. It is a possible GA building block only after the plan freezes the caller, the complete set of principals queried, the interaction with API-invisible nested identities, paging/enumeration, and the observation freshness rule.
- The [workspace Groups API reference](https://docs.databricks.com/api/azure/workspace/groups) is Public Preview and concerns workspace groups. It must not silently replace the account-group/automatic-identity model in the required path.

### Jobs, Apps, and service-principal roles

- [Lakeflow Jobs privileges](https://learn.microsoft.com/en-us/azure/databricks/jobs/privileges) states that Job `CAN MANAGE` can edit tasks, configuration, and permissions and that runs execute as the configured run-as identity. The baseline correctly treats every Job owner/manager and relevant Service Principal User as a runtime trusted root.
- [Roles for managing service principals](https://learn.microsoft.com/en-us/azure/databricks/security/auth/access-control/service-principal-acl) states that Service Principal User and Manager are account-level roles, that account administrators are managers on every service principal, and that a non-account-admin needs Service Principal Manager on a service principal to manage its role assignments. A workspace administrator is not thereby a complete service-principal-role observer.
- The [Account Access Control Proxy API](https://docs.databricks.com/api/azure/workspace/accountaccesscontrolproxy) used to inspect role rule sets is Public Preview. Baseline 0.9's policy says Preview features are optional unless a reviewed decision explicitly accepts them, yet no such exception or stable alternative is frozen for the required runtime-integrity claim.
- [Databricks App permissions](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/permissions) separates who can use/manage an App from what its service principal can access. The base App's declared `CAN_USE` warehouse and curated-view `SELECT` bindings do not grant it Job ACL, account-group, or service-principal-role inventory authority.

## Ranked findings

| Rank | Finding | Severity | P0 effect |
|---:|---|---|---|
| 1 | `DBX-P0-018` - complete composite/runtime-trust visibility has no frozen supported observer contract | High | Blocks P0; `CHANGES_REQUIRED` |
| 2 | `DBX-P0-019` - the workspace-admin verifier has effective warehouse `CAN_MANAGE`, not a `CAN_MONITOR`-only boundary | Medium | Blocks P0; `CHANGES_REQUIRED` |

### DBX-P0-018: complete composite/runtime-trust visibility has no frozen supported observer contract

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Affected contract:
  - `README.md`, runtime-trust-manifest drift detection before affected output is trusted
  - `AGENTS.md`, complete transitive membership audit and pre-output live runtime-integrity verification
  - `docs/decisions/0001-private-app-bundle.md`, composite observation and runtime-integrity decision
  - `docs/plans/product-plan.md`, runtime identities, runtime-trust manifest, `RECOVERY_AUDIT`, composite acceptance, P2/P3/P4/P6/P7/P8/P10, and readiness
  - `docs/plans/review-process.md`, complete authority/runtime-drift review and tests
  - `docs/plans/documentation-plan.md`, runtime-integrity, recovery, permissions, and trusted-root pages
  - `docs/research/source-register.md`, group/service-principal observation source and feature-status register
- Evidence:
  1. The plan requires `RECOVERY_AUDIT` to consume every nested account-group page and requires composite acceptance to contain complete live owner/grant/group observation plus a transitive-membership digest.
  2. The runtime-trust manifest includes every relevant Job/App manager, Service Principal User/Manager assignment, UC grant, trusted-root group, and membership snapshot. The wrapper verifies this graph before App start; each writer self-checks before DML; the App compares live settings before presenting evidence as trusted; P8 must detect out-of-band manager, role, grant, and configuration drift.
  3. The declared base App has only warehouse `CAN_USE` and curated-view bindings. The collector and other runtime writers have their exact business DML/Job access. None has the workspace/account administration, Service Principal Manager, or account-group visibility needed to inspect the complete graph they are said to self-check continuously.
  4. The deployment/seal verifier is a workspace administrator and can inventory workspace resources, but it is not required to be an account administrator or Service Principal Manager for every runtime service principal. Those are the roles Databricks documents for complete service-principal-role management/inspection.
  5. The Account Access Control Proxy that exposes service-principal role rule sets is Public Preview. It cannot be a hidden dependency under the frozen “Preview is optional” policy.
  6. The workspace-domain Account Groups proxy is a useful supported source for provisioned account identities, but the plan names no endpoint, caller, page algorithm, cycle/duplicate rule, group-source constraint, or snapshot freshness. Automatic identity management can confer transitive membership through nested identities that are visible in UI but not retrievable through Databricks APIs/Terraform unless explicitly provisioned.
  7. Administrator-only `SHOW GROUPS WITH USER|GROUP` can return direct and indirect memberships for a named principal. The author set neither selects it nor defines which principals must be enumerated, how API-invisible nested identities are handled, or how an activity-refreshed membership snapshot becomes a “fresh point-in-time” security observation.
  8. `RUNTIME_INTEGRITY_UNVERIFIED` is a correct fail-closed state, but the acceptance path still promises `RUNTIME_INTEGRITY_VERIFIED` and pre-presentation drift gating without an actor or process that can compute it. Merely naming `UNVERIFIED` does not make the positive state implementable.
- User/system impact: the product can label a composite seal or evidence as verified while an unobserved transitive group member, Job/App manager, or Service Principal User/Manager retains or gains authority. Alternatively, a literal least-privilege implementation can never leave `RUNTIME_INTEGRITY_UNVERIFIED`, blocking first value and controlled actions. In a regulated product, an unverifiable positive integrity label is more serious than a visible unsupported state.
- Required acceptance condition:
  1. Freeze one complete observation matrix. For each input—UC direct/effective grants, owners/`MANAGE`, Job/App owner and ACL, run-as, App binding, Service Principal User/Manager rule, account/workspace admin, and group membership—name the exact API or SQL command, feature status, caller, required privileges, page/token behavior, canonicalization, observation timestamp, and denied/malformed result.
  2. Select the observer and cadence for initial seal, runtime apply, App start, every writer's pre-DML gate, every App read/presentation gate, reconciliation, and controlled actions. If only an attended administrator can observe the graph, do not claim that the low-privilege App or writer performs a live complete check between administrator observations. Bind outputs to the last observation and expose its age.
  3. Resolve service-principal-role visibility without a hidden Preview dependency. Either explicitly accept and govern the Public Preview Account Access Control API in a reviewed decision, require an account-admin/Service Principal Manager attended verifier and a supported alternative evidence path, or narrow the v1 claim and keep affected output `RUNTIME_INTEGRITY_UNVERIFIED`.
  4. Constrain supported identity topology or define a complete group algorithm. State whether v1 supports automatic identity management, SCIM-provisioned direct-only groups, nested account groups, API-invisible nested identities, external identities, and service principals inside groups. If completeness cannot be proven, fail readiness with a stable code before mutation.
  5. If using `SHOW GROUPS`, freeze administrator identity, all queried principals/groups, result canonicalization, direct/indirect semantics, freshness/propagation handling, and cross-check with the account-group proxy. A direct-member recursive walk alone is insufficient for the documented automatic-identity case.
  6. Alternatively, make each granted group principal itself an explicit trusted root and stop claiming a complete member snapshot. Then prove only the named actors' eligibility, describe membership governance as customer-controlled residual authority, and remove continuous member-drift detection claims.
  7. Add P8 cases for nested direct/indirect users, nested service principals, an unprovisioned automatic-identity child, role-rule visibility denied, preview API disabled/unavailable, membership refresh delay, group cycle/duplicate defense, post-start Job/App manager change, Service Principal User/Manager change, and observation expiry. Only a demonstrably complete result may produce `VERIFIED`.

### DBX-P0-019: the workspace-admin verifier has effective warehouse `CAN_MANAGE`, not a `CAN_MONITOR`-only boundary

- Verdict: `CHANGES_REQUIRED`
- Severity: medium
- Affected contract:
  - `AGENTS.md`, dedicated warehouse permission and escalation boundary
  - `docs/decisions/0001-private-app-bundle.md`, verifier authority and warehouse recovery
  - `docs/plans/product-plan.md`, fixed constraint, installer identity, readiness step 1, recovery/escalation, P3/P7/P8, and trusted roots
  - `docs/plans/documentation-plan.md`, combined/separated prerequisites, query-history recovery, permission reference, and escalation guidance
  - `docs/research/source-register.md`, SQL warehouse ACL and workspace-admin interpretation
- Evidence:
  1. The author set correctly grants the migration-operator and seal-verifier groups direct `CAN_MONITOR` on the installer-only warehouse and states that a raw `CAN_MONITOR` principal cannot manage the warehouse.
  2. The actual deployment/seal-verifier identity is also required to be a workspace administrator for identity/runtime-graph visibility.
  3. Azure Databricks documents that workspace administrators have `CAN MANAGE` on all workspace objects. Therefore the verifier can manage warehouse permissions and has effective warehouse management authority regardless of the group's direct `CAN_MONITOR` row.
  4. Product-plan readiness says the two groups receive `CAN_MONITOR`, “not warehouse ownership or `CAN_MANAGE`,” and assigns exceptional stop/escalation to a named warehouse owner/manager. That statement is true only of the direct group ACL, not of the actual verifier actor. The named manager is a procedural escalation owner, not the exclusive platform principal able to stop/manage the warehouse.
  5. P8 tests a raw `CAN_MONITOR` principal's inability to stop the warehouse but does not test or disclose the effective composite role used by the verifier in the regulated path.
- User/system impact: an installer or security approver can approve a least-privilege diagram that understates the verifier's ability to stop, edit, delete, or change permissions on the recovery warehouse. Recovery behavior also becomes ambiguous: the verifier may possess an emergency management action even though the product says it must escalate to someone else. The verifier is already a named workspace-admin trusted root, so this is a truthfulness and control-boundary defect rather than an undisclosed administrator-resistant bypass.
- Required acceptance condition:
  1. Distinguish direct ACL from effective authority everywhere. State that both groups receive direct `CAN_MONITOR`, but a verifier who is a workspace administrator also has effective workspace-object `CAN MANAGE` including warehouse management.
  2. Decide whether workspace-admin status is truly required. If not, replace it with the exact narrow workspace/resource permissions needed for inventory. If it is required, include warehouse `CAN_MANAGE` in the verifier's trusted-root row, plan preview, risk acknowledgement, composite acceptance, and documentation.
  3. Clarify that the named warehouse manager is the accountable procedural escalation owner, not necessarily the only identity technically capable of warehouse stop/edit/delete/ACL changes. Freeze which exceptional actions the wrapper permits or refuses for the verifier despite its underlying platform power.
  4. Test both actors: a non-admin with only direct `CAN_MONITOR`, and the actual workspace-admin-plus-`CAN_MONITOR` verifier. Verify query visibility/cancel behavior, warehouse lifecycle/ACL authority, product UI wording, escalation, and audit output for each.

## Specific recovery and seal verification outcome

| Question | Eighth re-review outcome |
|---|---|
| Can a `CAN_MONITOR` recovery actor see another user's query? | Yes. Query History requires at least `CAN VIEW`; `CAN_MONITOR` provides monitored query-history access and execution. The full-query/identity exposure is explicitly disclosed and isolated to a dedicated warehouse. |
| Can that actor fetch another user's Statement Execution result? | No. The plan correctly limits result retrieval to the submitting actor. |
| Is `wait_timeout=50s` valid? | Yes. It is the documented maximum. `on_wait_timeout=CANCEL` requests cancellation; it does not establish rollback or terminal state. The plan correctly resolves timeout/cancel/commit races through Query History plus live UC post-state and does not retry blindly. |
| Can Query History cancel another user's running query? | The native Query History UI documents this for a user with sufficient warehouse visibility. The frozen plan uses the listing API to locate and the UI deep link to cancel; it does not invent an API cancel method. |
| Is the preparation marker a sufficient cleanup locator? | Yes for the frozen short, dedicated-warehouse recovery window. It is verified before mutation, contains exact group/securable/action/digests, is client-matched after narrow API filtering, and is never treated as the permanent attestation. Zero/multiple matches fail closed. |
| Is the own-statement-ID problem fixed? | Yes. The pending row contains only completed prior Statement Execution IDs and explicitly cannot contain its own not-yet-known ID or claim the later revoke. |
| Is the post-revoke acceptance point implementable? | Its data/grant semantics are implementable: the matching pending row plus a later live observation is the acceptance point. The positive “complete group/runtime-trust observation” still needs `DBX-P0-018`'s observer contract. |
| Are direct grants, current DML, and self-grant capability separated? | Yes. Exact direct ledger-pair absence, effective `SELECT`/`MODIFY`, and ownership/`MANAGE` self-grant capability are distinct states. Trusted residual roots are named. |
| Is `SHOW GRANTS` completeness based only on workspace admin? | No. The plan requires object/container ownership or `MANAGE` and parent use. That conservative prerequisite is acceptable and also correctly discloses self-grant capability. |
| Are runtime DML sets exact? | Yes. The observed Job and base App write none; collector, P6 App, role Job, and optional enrichment have closed table sets and are denied ledger DML, ownership/`MANAGE`, and DDL. |
| Are Job/App/SP/admin trusted roots named? | Yes. The remaining gap is not naming them; it is proving that one supported observer can see their live role/membership/configuration state at each promised gate. |

## Prior-finding disposition

| Finding | Eighth re-review disposition |
|---|---|
| `DBX-P0-001` | `RESOLVED_FOR_P0`; observed and collector Jobs remain separate run-as identities. |
| `DBX-P0-002` | `RESOLVED_FOR_P0`; reconciliation is bounded, visible, and degradable. |
| `DBX-P0-003` | `RESOLVED_FOR_P0`; App access and human action authorization remain distinct. |
| `DBX-P0-004` | `RESOLVED_FOR_P0`; platform prerequisites are typed and fail closed. |
| `DBX-P0-005` | `RESOLVED_FOR_P0`; required runtime egress is zero and deployment egress is separately governed. |
| `DBX-P0-006` | `RESOLVED_FOR_P0`; system enrichment is separate, disabled by default, scope-filtered, and removable. |
| `DBX-P0-007` | `RESOLVED_FOR_P0`; App use/manage permission remains separate from App resource bindings. |
| `DBX-P0-008` | `RESOLVED_FOR_P0`; optional controlled-action identity and DML boundaries are closed and explicit. |
| `DBX-P0-009` | `RESOLVED_FOR_P0`; saved Direct plans and stopped-then-explicit-start lifecycle remain coherent. |
| `DBX-P0-010` | `RESOLVED_FOR_P0`; Direct owns supported resources while the attended fixed data plane owns DDL/DML. |
| `DBX-P0-011` | `RESOLVED_FOR_P0`; exact preapproved revoke, cleanup-first recovery, query terminalization, and post-revoke composite acceptance are now explicit. |
| `DBX-P0-012` | `RESOLVED_FOR_P0`; targeted privilege operations preserve unrelated customer assignments. |
| `DBX-P0-013` | `RESOLVED_FOR_P0`; no privileged migration Job, migration service principal, or editable remote migration code path exists. |
| `DBX-P0-014` | `RESOLVED_FOR_P0`; temporary ledger DML, exact revoke, pending Delta attestation, sanitized view, and no Jobs receipt carrier are frozen. |
| `DBX-P0-015` | `RESOLVED_FOR_P0`; dedicated-warehouse `CAN_MONITOR`, one-operation/50-second cancel policy, GA Query History locator/UI takeover, no cross-user result fetch, exact cleanup locator, bounded terminalization, and two-user tests are specified. |
| `DBX-P0-016` | `RESOLVED_FOR_P0`; the row is explicitly pre-revoke/pending, excludes its own ID, and only a later composite live observation accepts the state. Direct/current/self-grant facts are separate. |
| `DBX-P0-017` | `RESOLVED_FOR_P0`; exact runtime DML and the deployment/runtime/trusted-manager boundary no longer contradict one another. Completeness of the proposed live drift observer is a distinct defect reopened as `DBX-P0-018`. |
| `DBX-P0-F01` | `REOPENED_IN_PART_AS_DBX-P0-018`; the direct/inherited/ownership/`MANAGE`/pagination model is resolved, but “all transitive memberships” lacks a complete supported observation algorithm across the identity models the plan otherwise supports. |
| `DBX-P0-F02` | `RESOLVED_FOR_P0`; optional enrichment retains exact pair scope, source-scope disclosure, snapshot destinations, and removal gates. |

## Author-file outcome

| Author file or set | Outcome | Databricks conclusion |
|---|---|---|
| `README.md` | `CHANGES_REQUIRED` | The architecture summary overstates live role/membership/configuration drift detection before output is trusted. |
| `AGENTS.md` | `CHANGES_REQUIRED` | Complete transitive membership and runtime-role checks need one supported observer contract; the workspace-admin verifier's effective warehouse management authority must be stated. |
| `docs/index.md` | `PASS` | The planning index introduces no independent platform or security claim. |
| `docs/decisions/0001-private-app-bundle.md` | `CHANGES_REQUIRED` | The core App-plus-Direct decision remains sound, but its positive composite/runtime-integrity and warehouse-role invariants need findings 018 and 019 resolved. |
| `docs/plans/product-plan.md` | `CHANGES_REQUIRED` | This is the primary affected file: it promises live completeness without an observer capable of computing it and describes only the verifier's direct warehouse ACL, not effective authority. |
| `docs/plans/review-process.md` | `CHANGES_REQUIRED` | P3/P6/P7/P8 require tests whose positive result is not yet implementable from the declared identities and sources. |
| `docs/plans/documentation-plan.md` | `CHANGES_REQUIRED` | D2 and runtime-integrity pages would teach a stronger verification and narrower warehouse boundary than the frozen platform design can prove. |
| `docs/research/source-register.md` | `CHANGES_REQUIRED` | Add Account Groups proxy/AIM nesting and freshness, administrator-only `SHOW GROUPS`, Public Preview Account Access Control Proxy, the exact service-principal-role observer, and effective workspace-admin warehouse authority. |

## P0-P10 Databricks coverage matrix

These are planning outcomes. They do not claim that implementation or live evidence already exists.

| Part | Planning outcome | Databricks conclusion and required next evidence |
|---|---|---|
| P0 - Product contract | `CHANGES_REQUIRED` | Resolve `DBX-P0-018` and `DBX-P0-019`, then re-review the immutable author set. The selected private App plus Direct Bundle remains the recommended architecture. |
| P1 - Capture library | `PASS` | Closed artifact/event schemas, sensitive-field allowlists, attempt identity, and local parser logic remain platform-independent and sound. |
| P2 - Collector and reconciliation | `CHANGES_REQUIRED` | Exact DML/no-DDL and reconciliation are sound, but the claim that the writer performs a complete pre-DML runtime-trust self-check needs a real observer or a narrower signed-snapshot/age contract. |
| P3 - Bundle installer | `CHANGES_REQUIRED` | Freeze group/SP-role/resource observation sources and actor privileges; disclose the verifier's effective warehouse `CAN_MANAGE`; then prove both immutable modes and no hidden Preview dependency. |
| P4 - Read-only App MVP | `CHANGES_REQUIRED` | Curated-view bindings are least privilege, but the base App cannot make the promised live complete Job/App/SP/group comparison under its declared permissions. |
| P5 - Existing-job onboarding | `PASS` | The scanner/source-patch/owner-approval design does not depend on the defective positive integrity observer. Runtime trust must still pass before onboarded output is labeled trusted. |
| P6 - Controlled actions | `CHANGES_REQUIRED` | Actions cannot be unlocked or drift-locked on a live graph the App cannot completely observe. Preserve the exact App/role-Job DML boundary while adding or narrowing the observer contract. |
| P7 - Security and operations | `CHANGES_REQUIRED` | Runbooks must name the actual observer, freshness/expiry, Preview status, unsupported identity topologies, effective workspace-admin warehouse authority, and fail-closed recovery. |
| P8 - Bounded live proof | `CHANGES_REQUIRED` | Existing two-user query/cancel/revoke/race tests are well specified. Add the finding 018/019 identity, visibility, freshness, role-drift, and effective-role cases before a regulated claim. End with the already required stopped/absent-resource inventory. |
| P9 - Optional intelligence | `PASS` | Genie/AI remains optional, read-only over curated data, and outside capture, migration, seal, authorization, and runtime-integrity authority. |
| P10 - Private alpha | `CHANGES_REQUIRED` | Do not label evidence `RUNTIME_INTEGRITY_VERIFIED` or the verifier `CAN_MONITOR`-only until both findings pass in representative customer identity configurations. |

## Explicit verdict

`CHANGES_REQUIRED`

The private Databricks App deployed through a plain-YAML Direct Bundle remains the recommended starting point. Baseline 0.9 now has a credible attended Statement Execution recovery contract, a truthful pre-revoke Delta attestation, a composite post-revoke authority model, exact runtime DML, and explicit administrator/Job/App/service-principal trusted roots.

It cannot yet be accepted as the regulated P0 baseline. The positive composite/runtime-integrity state has no frozen supported observer capable of seeing every group, service-principal-role, Job/App, grant, and configuration input at the promised gates, and the actual workspace-admin verifier has effective warehouse `CAN_MANAGE` despite the `CAN_MONITOR`-only wording. Resolve `DBX-P0-018` and `DBX-P0-019`, update the source register and affected P0-P10 gates, and request another independent Databricks re-review.
