# Databricks platform/security ninth re-review: P0 planning baseline

- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform/security reviewer
- Immutable author input SHA-256: `2fa25d8bef4e2499de9feb0541b405430599400059172e206b1ec7bf89f9a8a1`
- Baseline: 0.10
- Verdict: `CHANGES_REQUIRED`
- Cloud mutation: none

## Immutable input verification

I recomputed the requested digest before reviewing. The frozen input set was `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path. Each file was hashed with SHA-256, the resulting records were sorted by path and concatenated, and that stream was hashed again.

The result was exactly:

```text
2fa25d8bef4e2499de9feb0541b405430599400059172e206b1ec7bf89f9a8a1
```

No author file or earlier review was changed. This report is the only file written. I made no Azure, Databricks, authentication, SQL, warehouse, App, Job, account-console, or Unity Catalog call. This was a static frozen-author-set review with current official Microsoft/Databricks documentation and first-party Databricks CLI sources.

## Executive assessment

Baseline 0.10 correctly resolves both findings that triggered this focused review:

- `DBX-P0-018` is resolved. The design no longer promises a continuously complete member inventory. Every granted group is a whole customer-governed trusted root. GA `SHOW GROUPS WITH USER` and `WITH GROUP` are limited to the named migration actors and operator/verifier groups needed to classify current-DML paths. The runtime-trust matrix names each machine-observed input, observer, authority, canonicalization/completeness rule, failure state, timestamp, 24-hour expiry, and the separate account-admin native service-principal-role-roster attestation. The Public Preview Account Access Control and Workspace Groups APIs are prohibited in the required path. Low-privilege components explicitly do not claim live graph observation.
- `DBX-P0-019` is resolved. The direct group ACL and the actor's effective authority are now kept separate throughout the author set: both operator groups receive direct `CAN_MONITOR`, while the actual workspace-admin verifier has effective `CAN_MANAGE` and can stop, edit, delete, or change ACLs. The named warehouse manager is the accountable procedural escalation owner, not the only technically capable manager. P8 includes both actor cases.

The private Databricks App deployed through a plain-YAML Direct Bundle remains the recommended product architecture. Current first-party evidence supports Apps as a generally available product and Direct as the current GA/default Bundle engine. Baseline 0.10 also retains the sound split between a resource-deployment plane with no SQL/Unity Catalog DDL/DML and an attended fixed data plane.

Two newly exposed runtime-trust implementation blockers prevent P0 acceptance:

1. The required first-install sequence accepts a complete runtime-trust snapshot before `bundle run`, but its closed matrix requires the App's actual code deployment. Official Bundle behavior says `bundle deploy` creates or updates the App resource but does not deploy the App to compute; `bundle run <app-key>` is the separate code-deploy/start operation. On a fresh install there is no App deployment to observe. On an upgrade the pre-run deployment is the old code, not the new code that `bundle run` will deploy. The positive pre-start snapshot is therefore either impossible or about the wrong deployment.
2. The accepted runtime-trust snapshot has no named persistent customer-local carrier, writer, reader, schema, grant, refresh, or lifecycle contract. The closed base object manifest contains no runtime-trust object. The exact DML table grants provide no principal that can commit the accepted observation. The App and writers nevertheless must read its ID/time/age, stamp it, mark output stale, refresh it after 24 hours, and lock P6. A local installer sidecar or checkpoint cannot serve those runtime readers, and Databricks documents App memory and local files as ephemeral.

These are not documentation polish issues. The first makes the fresh positive trust gate unsatisfiable; the second leaves the central security state unavailable to the components that enforce and display it. Both are high severity and affect P0, P2-P4, P6-P8, and P10. P0 remains `CHANGES_REQUIRED`.

## Current primary evidence checked

All sources below are current official Microsoft/Databricks documentation or first-party Databricks sources.

### App and Bundle lifecycle

- The [May 2025 Azure Databricks release notes](https://learn.microsoft.com/en-us/azure/databricks/release-notes/product/2025/may) record Databricks Apps as generally available. The product choice itself is not a Preview dependency.
- [Manage Databricks Apps using Declarative Automation Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial) explicitly says that `bundle deploy` creates the App resource but does not automatically deploy the App to compute. The page then uses `bundle run <app-resource-key>` to start the App in the workspace. This is the decisive lifecycle boundary for `DBX-P0-020`.
- [Get started with Databricks Apps](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/get-started) shows the result of an App deployment: a deployment ID, immutable deployment-artifact source-code path, deployment status, and “App started successfully.” Those deployment facts exist after the code-deploy/start operation; creating the resource is not equivalent to observing that deployment.
- The first-party [CLI 1.7.0 App Bundle runner](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/run/app.go#L44-L99) likewise implements App `bundle run` as a separate code-deploy/start stage. Baseline 0.10's source register already cites this correctly.
- [Databricks CLI v1.3.0](https://github.com/databricks/cli/releases/tag/v1.3.0) records Direct as GA and the default for newly initialized Bundles; [v1.7.0](https://github.com/databricks/cli/releases/tag/v1.7.0) is the currently selected first-party release in this frozen plan. This supports retaining the selected Direct architecture; it does not repair the App deployment ordering defect.

### Durable App state

- [Key concepts in Databricks Apps](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts#app-state) states that App in-memory state and local files are lost when the App restarts. It identifies Databricks tables, workspace files, and Unity Catalog volumes as persistent alternatives.
- [Add resources to a Databricks App](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/resources) documents explicit resource declaration/configuration and managed credentials/permissions. A persistent trust carrier therefore needs a real resource and access contract; an unnamed “runtime record” is not an App-readable binding.
- The author set itself states that product state cannot live on App disk or in memory and that the base App has curated-view `SELECT` only. That is correct, but it makes the missing persistent runtime-trust object and grant path material.

### Identity and point-in-time observation

- [`SHOW GROUPS`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-syntax-aux-show-groups) is administrator-only and reports direct/indirect parent groups for one named user or group. Baseline 0.10 now uses it only for the closed set of named migration actors and operator/verifier groups; it no longer misuses it as a complete membership export.
- [Automatic identity management](https://learn.microsoft.com/en-us/azure/databricks/admin/users-groups/automatic-identity-management/) documents transitive nested membership and activity-dependent refresh, plus nested identities that can be visible in the UI but unavailable through APIs/Terraform. Treating the granted group principal itself as the trusted root is the correct regulated-v1 limitation.
- [Roles for managing service principals](https://learn.microsoft.com/en-us/azure/databricks/security/auth/access-control/service-principal-acl) documents account-level Service Principal User and Manager roles and the native account-console Permissions roster. Baseline 0.10 now truthfully calls the required roster result `SP_ROLE_ROSTER_ADMIN_ATTESTED`, not machine verification.
- The [Account Access Control Proxy API](https://docs.databricks.com/api/azure/workspace/accountaccesscontrolproxy) is Public Preview. Prohibiting it in the required path and failing closed when the attended native comparison cannot be completed is coherent.

### Warehouse and Unity Catalog authority

- [Workspace access control](https://learn.microsoft.com/en-us/azure/databricks/security/auth/access-control/) states that workspace administrators have `CAN MANAGE` on workspace objects. Its SQL warehouse ACL table distinguishes direct `CAN_MONITOR` from management. Baseline 0.10 now represents both facts and the associated stop/edit/delete/ACL powers.
- [Manage Unity Catalog privileges](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/manage-privileges/) and [Unity Catalog privilege concepts](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/access-control/permissions-concepts) support the frozen separation between current direct/effective DML and owner/`MANAGE` self-grant capability. The verifier's object-scoped authority remains an explicit trusted root.

## Ranked findings

| Rank | Finding | Severity | P0 effect |
|---:|---|---|---|
| 1 | `DBX-P0-020` - complete App deployment observation is required before the deployment exists | High | Blocks P0; `CHANGES_REQUIRED` |
| 2 | `DBX-P0-021` - accepted runtime trust has no durable carrier or runtime access contract | High | Blocks P0; `CHANGES_REQUIRED` |

### DBX-P0-020: complete App deployment observation is required before the deployment exists

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Affected contract:
  - `docs/decisions/0001-private-app-bundle.md`, install ordering and stopped-then-run consequence
  - `docs/plans/product-plan.md`, runtime observation matrix, common stages/path, fresh install, upgrade/rollback, P3/P4/P6/P7/P8/P10, and readiness
  - `docs/plans/review-process.md`, P3/P6/P8 lifecycle and trust gates
  - `docs/plans/documentation-plan.md`, bootstrap, refresh, upgrade, recovery, and runtime-trust pages
  - `README.md` and `AGENTS.md`, only insofar as their positive snapshot language relies on this impossible ordering
- Evidence:
  1. The closed runtime observation matrix requires “App code deployment, configuration, service principal, bindings, owner, and ACL.” A missing or unknown field fails the snapshot as `RUNTIME_TRUST_UNVERIFIED`.
  2. The common stage list orders `RUNTIME_GA_OBSERVE`, `SP_ROLE_ROSTER_REVIEW`, and `RUNTIME_TRUST_ACCEPT` before `APP_CODE_START`.
  3. The common runtime path says the saved runtime plan Apply leaves App compute stopped, every GA-visible matrix input is then observed, and only a matching `RUNTIME_TRUST_ACCEPTED_ADMIN_ATTESTED` snapshot may proceed. Only after that gate does the wrapper execute `databricks bundle run <app-resource-key>`.
  4. Official Databricks Bundle documentation says `bundle deploy` does not deploy the App to compute. `bundle run <app-resource-key>` is the separate operation that deploys the App code and starts the App.
  5. On a fresh install, the author set itself says no App exists before the runtime plan. After Apply there is an App resource but no actual code deployment. A complete pre-run observation cannot include deployment ID/artifacts/status for the intended code.
  6. On upgrade or rollback, an existing stopped App can have an earlier deployment, but the pre-run observation sees that earlier deployment. The newly approved source is not the active deployment until `bundle run`. A snapshot of the previous deployment cannot authorize the new deployment.
  7. The path says it recomputes the observation after `bundle run`, which is directionally correct but occurs after the positive snapshot has already authorized start. The plan does not define a safe-boot state that denies evidence trust and controlled actions until that post-deployment observation is committed.
  8. `APP_READY`, first evidence, and the user-visible URL are downstream of an ordering that cannot reach the positive state literally on a clean install.
- User/system impact:
  - A literal implementation fails every fresh install at `RUNTIME_GA_OBSERVE` because the required App deployment is absent.
  - A permissive implementation silently omits the deployment input, falsely calls an incomplete snapshot accepted, and starts unobserved code.
  - An upgrade implementation can authorize new code using an observation of the old deployment.
  - A failed or malicious code deployment can run before the promised complete runtime-trust gate, including before P6 action locks are demonstrably active.
- Required acceptance condition:
  1. Split pre-start resource readiness from post-deployment trust acceptance. The pre-start state may prove the App resource, intended source/build digest, ACLs, bindings, service principal, and stopped lifecycle, but it must not be called `RUNTIME_TRUST_ACCEPTED_ADMIN_ATTESTED` or claim observation of the not-yet-active deployment.
  2. Freeze one supportable bootstrap protocol. A viable pattern is: apply the App resource; start/deploy into a closed safe-boot mode; expose no trusted evidence and permit no controlled action; observe the resulting deployment ID/artifact/code/configuration/status plus all other matrix inputs; complete the account-admin roster attestation; atomically commit the accepted snapshot; then unlock reads/actions. If post-start observation or snapshot commit fails, keep the App setup-only and stop it by default.
  3. If a different two-start or deploy-stop-observe-start protocol is selected, name every platform command, state transition, billed interval, failure route, and which exact deployment ID is accepted. Never use a plan/source digest as a substitute for observing the resulting deployment.
  4. Define upgrade and rollback separately. The old deployment, intended new source, new deployment, and accepted deployment ID must be distinguishable; old-snapshot acceptance cannot cross the code-deployment boundary.
  5. Update the immutable stage order, ADR consequence, documentation tutorial, P3/P6/P7 gates, and readiness wording. “Before App start” must become the precise safe-boot/deployment boundary actually implemented.
  6. Add staging cases for a fresh App with no deployment, an old stopped deployment during upgrade, deployment failure, source/artifact mismatch, App crash before observation, account-review failure after start, post-start snapshot-commit failure, and cleanup proving no App/test compute remains.

### DBX-P0-021: accepted runtime trust has no durable carrier or runtime access contract

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Affected contract:
  - `README.md`, App trust-age and stale-output claims
  - `AGENTS.md`, writer stamping, App status, 24-hour action gate, and durable-state invariant
  - `docs/decisions/0001-private-app-bundle.md`, point-in-time trust state and ephemeral App state
  - `docs/plans/product-plan.md`, closed object manifest, exact runtime DML, runtime record, evidence schema, refresh, App display, P2-P4/P6-P8/P10, retention, and uninstall
  - `docs/plans/review-process.md`, snapshot expiry/refresh and enforcement review
  - `docs/plans/documentation-plan.md`, bootstrap, refresh, permissions, reference, recovery, retention, and uninstall pages
- Evidence:
  1. The base closed data manifest contains `dbtobsb_migration_ledger`; three evidence tables; and three sanitized views. It contains no runtime-trust snapshot table, view, Volume, workspace file, or other persistent authority object. The P6 and optional-enrichment extensions also add no such object.
  2. The exact runtime write table grants are closed: the collector writes only the three evidence tables; the base App writes none; the P6 App writes two action tables; the role Job and enrichment Job write only their named sets. No runtime principal is authorized to commit an accepted observation record.
  3. The attended wrapper must combine a machine-observation digest with a separate account-admin native-roster attestation after runtime Apply. The plan calls the result a “runtime record” but does not identify where it is stored, who owns it, who writes it, how the two approvals are joined, or how conflicts/partial writes are resolved.
  4. The protected Direct plan and sidecar are local to the deployment account and are deleted after accepted completion. Per-actor checkpoints are local recovery aids and explicitly are not remote authority. Neither is readable by the Databricks App or collector Job.
  5. The App must display snapshot ID, observation time, age, scope, and qualifier on every evidence/action page; derive stale/unverified state after 24 hours; and unlock again after attended refresh. The collector and other low-privilege writers must validate and stamp the last accepted snapshot ID and age before DML. No reader binding or query contract supplies that state.
  6. The author set correctly forbids product state on App disk or in memory. Official Databricks guidance confirms that App memory and local files are lost on restart and points to tables, workspace files, or Unity Catalog volumes for persistence.
  7. Treating an evidence row's self-stamped ID as the authority would invert the trust boundary: the low-privilege writer would be asserting the acceptance it is only allowed to reference. It also would not provide one current status for existing rows, App pages, and P6 locks.
  8. Embedding the accepted snapshot into App configuration/environment after review is not currently specified and creates a cycle: another Bundle apply changes configuration, which the observation matrix says must be re-observed. It also provides no frozen collector read path or atomic 24-hour refresh protocol.
- User/system impact:
  - The App cannot reliably know whether an accepted snapshot exists, which deployment it covers, or whether it expired.
  - Writers cannot truthfully stamp the accepted snapshot or fail on a mismatch under their declared grants.
  - Existing evidence cannot become visibly stale at 24 hours without a durable observation timestamp and a defined authoritative clock/read.
  - P6 cannot enforce “snapshot no older than 24 hours” or remain locked through partial/failed refresh.
  - App restart, installer workstation loss, upgrade, or cleanup can erase or strand the only possible record while the UI still promises customer-local durable trust state.
- Required acceptance condition:
  1. Select and name one persistent customer-local trust carrier. A restricted Unity Catalog Delta table plus a sanitized current-status view is a natural fit, but another supported persistent resource is acceptable if it meets the same access, atomicity, governance, and restart requirements. A local installer file, App memory, or App local disk is not sufficient.
  2. Add every object to the signed closed data-contract manifest and attended migration envelope. Freeze schema, owner, exact grants, App/collector bindings, retention, export, upgrade, rollback, retain/delete-uninstall, and the trusted administrators capable of tampering. Any new table/view is a manifest-version change before P3, not an undocumented implementation detail.
  3. Define the commit protocol that joins the workspace-admin machine observation and account-admin native-roster approval. Name the authenticated actors, pseudonymous signer/reviewer fields, snapshot/deployment/component scope, observation and expiry times, source/build/config/authority/roster digests, previous-generation binding, outcome, idempotency key, and accepted terminal state. Partial, duplicate, conflicting, replayed, denied, or clock-invalid records must fail closed.
  4. Define the sole accepted-snapshot writer and its exact temporary or persistent DML. Low-privilege collector/App/role/enrichment principals must not be able to create or promote an accepted snapshot. If the attended data plane writes it, include its marked Statement Execution, pending/composite semantics, exact temporary grants/revokes, and recovery. If another mechanism is selected, review its equivalent authority and failure envelope.
  5. Define narrow reader contracts. The App needs a sanitized current-status read. Each writer that stamps a snapshot needs only the minimum fields for its own component and deployment. Specify behavior for absent, expired, mismatched, superseded, ambiguous, and unreadable state.
  6. Derive age from a frozen observation/expiry timestamp and an authoritative time source; do not trust a mutable client-supplied age. Specify whether collection continues, how new and existing output is labeled, and how P6 locks across expiry and refresh.
  7. Make refresh work without circular trust claims. An attended refresh must commit a new immutable generation atomically, become visible to App/writers without relying on ephemeral state, preserve the previous record for audit, and never briefly unlock on a partial roster or machine observation.
  8. Add staging tests for App stop/restart, installer workstation loss after completion, 24-hour expiry, successful refresh without code redeploy, denied carrier read/write, writer attempt to forge acceptance, concurrent/conflicting reviewers, tamper by each disclosed trusted root, failed commit, retention/export, upgrade/rollback binding, and retain/delete uninstall.

## Focused disposition of DBX-P0-018 and DBX-P0-019

### DBX-P0-018

`RESOLVED_FOR_P0`

The author set now freezes a supportable point-in-time observation model:

- every GA-machine-observed resource class has a source, observer, privilege, canonicalization, pagination/completeness, and failure rule;
- every granted group is a whole trusted root, so v1 does not need to claim impossible continuous member enumeration;
- `SHOW GROUPS` is limited to named actors/groups whose current-DML paths must be classified;
- the Service Principal User/Manager roster is an attended account-admin native-console attestation, explicitly not machine verification;
- Preview Account Access Control and Workspace Groups APIs are prohibited;
- a matching two-observer snapshot expires after 24 hours;
- low-privilege runtime principals validate only their local contract/reference and do not claim live platform observation;
- post-observation change is detected only at the next attended observation, while stale output is explicitly unverified.

This resolution should not be reopened merely because whole-group membership remains customer-governed. The whole group is now intentionally inside the trusted boundary. `DBX-P0-021` is different: it concerns how the accepted point-in-time result becomes durable and consumable.

### DBX-P0-019

`RESOLVED_FOR_P0`

The author set consistently states:

- both operator groups have direct `CAN_MONITOR`;
- the actual workspace-admin verifier has effective `CAN_MANAGE`;
- that effective authority includes stop, edit, delete, and ACL management;
- the named warehouse manager owns the procedure/escalation, not exclusive technical capability;
- the verifier is a disclosed trusted root;
- staging tests cover both a non-admin direct-`CAN_MONITOR` actor and the real workspace-admin verifier.

No residual `CAN_MONITOR`-only claim was found in the frozen operational path.

## Runtime-trust implementability outcome

| Question | Ninth re-review outcome |
|---|---|
| Is the whole-group trusted-root model supportable? | Yes. It avoids an unsupportable all-member/continuous-drift claim while retaining named-actor path classification. |
| Is the service-principal-role evidence honestly labeled? | Yes. It is `SP_ROLE_ROSTER_ADMIN_ATTESTED` from a native account-admin review, and the Public Preview API is prohibited. |
| Is the verifier's effective warehouse authority truthful? | Yes. Direct `CAN_MONITOR` and effective workspace-admin `CAN_MANAGE` are distinct and tested. |
| Does `bundle deploy` deploy the App code to compute? | No. Official Bundle documentation says the App code deployment/start is separate. |
| Can a clean pre-`bundle run` snapshot observe the intended App deployment? | No. On first install it does not yet exist; on upgrade the observed deployment is the prior one. |
| Does the post-run re-observation sentence by itself fix the order? | No. The positive snapshot has already authorized start, and no safe-boot/unlock protocol is frozen. |
| Is there a persistent accepted-snapshot object in the closed manifest? | No. No table, view, Volume, workspace file, or equivalent authority carrier is named. |
| Can the App and writers read the local installer sidecar/checkpoint? | No. Those records are workstation-local, protected/deleted by installer lifecycle, and are not App/Job resources. |
| Can the evidence writer make its own stamped ID authoritative? | No. That would let a bounded writer manufacture the trust state it is only allowed to reference. |
| Can App memory or local files carry the state? | No. Both the author invariant and official Databricks guidance treat them as ephemeral. |
| Is the selected App-plus-Direct architecture still recommended? | Yes. The blockers are protocol/data-contract gaps, not a reason to replace the architecture. |

## Prior-finding disposition

| Finding | Ninth re-review disposition |
|---|---|
| `DBX-P0-001` | `RESOLVED_FOR_P0`; observed and collector Jobs remain separate run-as identities. |
| `DBX-P0-002` | `RESOLVED_FOR_P0`; reconciliation is bounded, visible, and degradable. |
| `DBX-P0-003` | `RESOLVED_FOR_P0`; App access and human action authorization remain distinct. |
| `DBX-P0-004` | `RESOLVED_FOR_P0`; platform prerequisites are typed and fail closed. |
| `DBX-P0-005` | `RESOLVED_FOR_P0`; required runtime egress is zero and deployment egress is separately governed. |
| `DBX-P0-006` | `RESOLVED_FOR_P0`; system enrichment is separate, disabled by default, scope-filtered, and removable. |
| `DBX-P0-007` | `RESOLVED_FOR_P0`; App use/manage permission remains separate from App resource bindings. |
| `DBX-P0-008` | `RESOLVED_FOR_P0`; optional controlled-action identity and DML boundaries are closed and explicit. |
| `DBX-P0-009` | `RESOLVED_FOR_P0`; Direct saved plans and explicit App run remain the selected lifecycle, subject to the newly identified trust-order defect `DBX-P0-020`. |
| `DBX-P0-010` | `RESOLVED_FOR_P0`; Direct owns supported resources while the attended fixed data plane owns DDL/DML. A new trust carrier must follow that same ownership rule. |
| `DBX-P0-011` | `RESOLVED_FOR_P0`; exact preapproved revoke, cleanup-first recovery, query terminalization, and post-revoke composite acceptance remain explicit. |
| `DBX-P0-012` | `RESOLVED_FOR_P0`; targeted privilege operations preserve unrelated customer assignments. |
| `DBX-P0-013` | `RESOLVED_FOR_P0`; no privileged migration Job, migration service principal, or editable remote migration code path exists. |
| `DBX-P0-014` | `RESOLVED_FOR_P0`; temporary ledger DML, exact revoke, pending Delta attestation, sanitized view, and no Jobs receipt carrier remain frozen. |
| `DBX-P0-015` | `RESOLVED_FOR_P0`; dedicated-warehouse `CAN_MONITOR`, one-operation/50-second cancel policy, GA Query History recovery, no cross-user result fetch, bounded terminalization, and two-user tests remain specified. |
| `DBX-P0-016` | `RESOLVED_FOR_P0`; the row is pre-revoke/pending, excludes its own ID, and only a later composite live observation accepts the data state. |
| `DBX-P0-017` | `RESOLVED_FOR_P0`; exact runtime DML and the deployment/runtime/trusted-manager boundary are coherent. The absent runtime-trust carrier is a different closed-manifest defect tracked as `DBX-P0-021`. |
| `DBX-P0-018` | `RESOLVED_FOR_P0`; the point-in-time mixed-evidence observer contract, whole-group-root model, manual SP-role attestation, feature status, expiry, and fail-closed states are frozen. |
| `DBX-P0-019` | `RESOLVED_FOR_P0`; direct `CAN_MONITOR` and effective workspace-admin `CAN_MANAGE` are now truthful and tested. |
| `DBX-P0-F01` | `RESOLVED_FOR_P0`; direct/inherited/owner/`MANAGE`/pagination semantics are explicit, and group principals are trusted whole roots rather than incompletely enumerated member sets. |
| `DBX-P0-F02` | `RESOLVED_FOR_P0`; optional enrichment retains exact pair scope, source-scope disclosure, snapshot destinations, and removal gates. |

## Author-file outcome

| Author file or set | Outcome | Databricks conclusion |
|---|---|---|
| `README.md` | `CHANGES_REQUIRED` | The high-level trust-age/stale-output promise needs the durable carrier and safe-boot ordering that would make it true. |
| `AGENTS.md` | `CHANGES_REQUIRED` | The invariants correctly resolve 018/019, but writer stamping and App enforcement lack a storage/read path and the positive snapshot is ordered before the App deployment exists. |
| `docs/index.md` | `PASS` | The planning index introduces no independent platform/security contradiction. |
| `docs/decisions/0001-private-app-bundle.md` | `CHANGES_REQUIRED` | The architecture decision remains recommended, but its consequence orders complete observation before `bundle run` and simultaneously forbids ephemeral state without naming a durable trust carrier. |
| `docs/plans/product-plan.md` | `CHANGES_REQUIRED` | This is the primary affected file: the common runtime path is unsatisfiable on clean deploy/upgrade, and the closed manifest/DML sets contain no authoritative runtime-trust state accessible to App/writers. |
| `docs/plans/review-process.md` | `CHANGES_REQUIRED` | P3/P6/P7/P8 review gates assume a persisted accepted snapshot and a pre-start code observation that the planned platform lifecycle cannot produce. |
| `docs/plans/documentation-plan.md` | `CHANGES_REQUIRED` | The bootstrap page teaches the impossible order, and refresh/stale/uninstall pages do not yet have an exact trust-record carrier or lifecycle to document. |
| `docs/research/source-register.md` | `PASS` | It already records the decisive Bundle App lifecycle and App-ephemeral-state facts. The selected carrier will need its own authoritative source and access model when chosen. |

## P0-P10 Databricks coverage matrix

These are planning outcomes. They do not claim that implementation or live evidence already exists.

| Part | Planning outcome | Databricks conclusion and required next evidence |
|---|---|---|
| P0 - Product contract | `CHANGES_REQUIRED` | Resolve `DBX-P0-020` and `DBX-P0-021`, then re-review a new immutable author set. The private App plus Direct Bundle remains the recommended architecture. |
| P1 - Capture library | `PASS` | Artifact/event parsing, allowlists, AttemptKey, and local schema logic remain sound. Before P1 exit, evidence metadata must reference the finalized durable snapshot identifier/time semantics rather than inventing a carrier. |
| P2 - Collector and reconciliation | `CHANGES_REQUIRED` | Exact three-table DML and no-DDL boundaries are sound, but the collector cannot read/stamp/expire an accepted snapshot until the carrier and narrow reader grant are frozen. |
| P3 - Bundle installer | `CHANGES_REQUIRED` | Implement a supportable safe-boot or equivalent deployment-observation sequence and a durable accepted-snapshot commit/read contract. Prove fresh, no-op, upgrade, rollback, failed start, failed observation, and failed commit. |
| P4 - Read-only App MVP | `CHANGES_REQUIRED` | Curated-view-only behavior is sound, but every-page time/age/scope/stale display needs an App-readable durable source and setup-only behavior before post-deployment acceptance. |
| P5 - Existing-job onboarding | `PASS` | Scanner/change-preview/owner-approval logic does not depend on the defective App-start order. Onboarded output still cannot be labeled trusted until findings 020/021 pass. |
| P6 - Controlled actions | `CHANGES_REQUIRED` | The 24-hour gate and drift/stale lock require an authoritative persisted current snapshot. Safe boot must keep actions unavailable before post-deployment acceptance and through every partial refresh. |
| P7 - Security and operations | `CHANGES_REQUIRED` | Freeze trust-record ownership, DML/read access, trusted-root tamper limits, expiry/refresh, retention/export, incident recovery, upgrade/rollback, and retain/delete-uninstall. Include the App deployment bootstrap failure path. |
| P8 - Bounded live proof | `CHANGES_REQUIRED` | Existing query/revoke/authority tests remain strong. Add clean no-deployment, old-deployment upgrade, safe-boot, post-start observation failure, durable-state restart/loss, refresh/concurrency/tamper, and final zero-compute/object-grant inventory cases. |
| P9 - Optional intelligence | `PASS` | Genie/AI remains optional, read-only over curated data, and outside capture, deployment, seal, authorization, and runtime-trust authority. |
| P10 - Private alpha | `CHANGES_REQUIRED` | A non-author install cannot be accepted until the actual deployed code is covered by the accepted snapshot and that snapshot survives App/workstation lifecycle with demonstrable stale/action behavior. |

## Explicit verdict

`CHANGES_REQUIRED`

Baseline 0.10 resolves `DBX-P0-018` and `DBX-P0-019`. Its mixed point-in-time observer contract, whole-group trusted-root limitation, manual account-admin roster attestation, Preview exclusion, and direct-versus-effective warehouse authority are now suitable P0 decisions.

The baseline still cannot be accepted for regulated implementation. The positive runtime-trust state is required before `bundle run` even though the intended App deployment does not exist until that operation, and the accepted result has no durable customer-local carrier that the App and bounded writers can read. Resolve `DBX-P0-020` with a precise safe-boot/deploy-observe-unlock protocol (or an equally supportable alternative), resolve `DBX-P0-021` with a closed persistent object/commit/grant/refresh/lifecycle contract, propagate both through P0-P10 and the documentation plan, and request another independent Databricks re-review.
