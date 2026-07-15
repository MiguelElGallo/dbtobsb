# Databricks platform focused third re-review: P0 planning baseline 0.4

- Reviewed input: frozen author-owned planning file set
- Author-input SHA-256: `8504d49ed1397e218a5760885673c87458d4ecd16d60936191ea0a2d89f48c98`
- Date: 2026-07-15
- Reviewer: independent Databricks product and platform specialist
- Verdict: `CHANGES_REQUIRED`
- Prior findings: `DBX-P0-001` through `DBX-P0-009` are resolved for P0 on this input
- New finding: `DBX-P0-010`
- Cloud mutation: none; no Azure or Databricks resource was created, started, stopped, or changed

## Immutable input verification

I independently hashed `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path. I hashed each file with SHA-256 and then hashed the sorted `shasum -a 256` output. The result was exactly:

```text
8504d49ed1397e218a5760885673c87458d4ecd16d60936191ea0a2d89f48c98
```

The scope contained eight files. Reviewer-owned files and `resolution.md` are outside the author-input hash. I read all eight author files, the resolution ledger, and the three earlier Databricks reports before forming this verdict.

The installed deployment tool was also checked without authentication or a workspace call. It reported `Databricks CLI v1.7.0`; its local help exposed JSON `bundle plan`, `bundle deploy --plan`, and `bundle run` for an App. Its generated Bundle schema confirmed that catalogs, schemas, secret scopes, and volumes are declarative resources, but Unity Catalog tables are not.

## Executive outcome

Baseline 0.4 closes both findings that remained after the focused second re-review:

- `DBX-P0-008` is now an executable GA-only human-authorization contract. It treats the exact forwarded value as request-local Personal Data, derives an installation-scoped HMAC alias, maps that alias to a random actor and epoch, requires an independently approved browser credential, and explicitly acknowledges that the GA header cannot detect deletion and recreation with the same value. A fixed unscheduled role-administration Job runs as a separate service principal; its human group gets only `CAN_MANAGE_RUN`, while the Job and App principals receive enumerated warehouse, parent, table, secret-scope, and Job permissions.
- `DBX-P0-009` now binds approval to a protected Direct plan plus CLI, profile, target, workspace, principal, variables, configuration, source/build, and semantic remote-state evidence. It immediately re-plans before applying the saved plan. Every managed App sets `lifecycle.started: false`, and the only App code/start command is `bundle run <app-resource-key>`.

Those corrections are accepted for P0. The current first-party sources support them, and no regression was found in `DBX-P0-001` through `DBX-P0-007`.

One new platform defect prevents acceptance. Baseline 0.4 says the Direct action plan adds the restricted Delta tables, the role service principal's per-table grants, and the App's table bindings together. Databricks CLI 1.7.0 has no declarative Unity Catalog table resource. An App `uc_securable` resource binds and grants access to an already-existing table; it does not create the table or grant a different service principal. The base normalized tables have the same unresolved bootstrap issue. This is a current installation-order and approval-boundary defect, not a request for later live proof.

## Current first-party sources checked

### Apps, identity, and resource authorization

- [App authorization](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/auth) — shared App authorization uses the App service principal and does not itself provide user-level authorization; user authorization remains Public Preview.
- [App HTTP headers](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/http-headers) — `X-Forwarded-User` is the IdP-provided user identifier; the page does not guarantee an immutable Databricks principal ID.
- [Databricks Apps environment](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/system-env) — `DATABRICKS_APP_NAME`, `DATABRICKS_WORKSPACE_ID`, and `DATABRICKS_HOST` are default App context; account ID is not a default.
- [Add resources to an App](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/resources) — the bound resource must already exist, App access is least privilege, and App resource authorization is separate from App access.
- [App secret resources](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/secrets) — secret permission is scope-wide, so a dedicated scope is the correct boundary; removing the App binding does not delete the secret.
- [App Unity Catalog table resources](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/tables) — the table must already exist; `Modify` grants write capability and implicitly includes `SELECT`.
- [App permissions](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/permissions) — `CAN_USE` permits interaction but not App management; it is not a product action role.

### Jobs and Unity Catalog

- [Lakeflow Job privileges and Run as](https://learn.microsoft.com/en-us/azure/databricks/jobs/privileges) — tasks use the Job's run-as identity; `CAN_MANAGE_RUN` triggers or cancels runs without permitting Job edits.
- [Service Principal User role](https://learn.microsoft.com/en-us/azure/databricks/security/auth/access-control/service-principal-acl) — configuring or running a Job as a service principal requires the distinct Service Principal User role.
- [Unity Catalog privileges](https://learn.microsoft.com/en-us/azure/databricks/data-governance/unity-catalog/access-control/privileges-reference) — table mutation requires table `SELECT` plus `MODIFY`, parent `USE SCHEMA`, and parent `USE CATALOG`.

### Direct plans and App lifecycle

- [CLI 1.3.0 release](https://github.com/databricks/cli/releases/tag/v1.3.0) — the immutable first-party release marks Direct GA and the default for new deployments.
- [CLI 1.7.0 release](https://github.com/databricks/cli/releases/tag/v1.7.0) — the exact reviewed CLI release and commit; its `job_runs` Bundle resource is explicitly experimental.
- [Direct deployment guidance](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/direct) — explicit `bundle.engine: direct` wins over the environment, Direct separates local and remote state, and `lifecycle.started` is Direct-only.
- [Bundle supported resources and App bindings](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/resources) — the supported-resource list contains catalog, schema, secret-scope, and volume resources but no Unity Catalog table resource; `app.resources.uc_securable` identifies an existing table by full name.
- [Manage Apps with Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial) — Bundle deployment creates or updates the App resource, while `bundle run <app-key>` starts/deploys the App code.
- [CLI 1.7.0 saved-plan validation](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/cmd/bundle/utils/process.go#L240-L265) — saved-plan deploy skips build and pre-deploy checks, validates lineage/serial, and only warns on a CLI-version mismatch.
- [CLI 1.7.0 Direct deploy phase](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/phases/deploy.go#L141-L205) — current source/build files are uploaded during deploy, and a Bundle pre-deploy script runs before the saved plan is applied.
- [CLI 1.7.0 App runner](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/run/app.go#L43-L99) — `bundle run` starts stopped compute when needed and then deploys App code without invoking Bundle resource deployment.
- [CLI 1.7.0 App lifecycle implementation](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/dresources/app.go#L119-L128) and [update behavior](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/dresources/app.go#L175-L240) — new `false` Apps use `no_compute`, and update with `false` explicitly stops running compute.

The current Direct migration page, updated 2026-07-10, says new CLI 1.3+ Bundles use Direct by default but retains a contradictory future-tense sentence saying Direct “will become” the default. The immutable CLI 1.3.0 release is explicit that Direct is GA/default. Baseline 0.4 pins the engine in YAML, so that documentation inconsistency does not create an operational ambiguity or a new finding.

## Focused acceptance results

| Focused condition | Third re-review outcome | Evidence and conclusion |
|---|---|---|
| Exact forwarded-user actor model | `RESOLVED_FOR_P0` | The exact single nonblank forwarded value is request-local; malformed, repeated, local-simulated, or wrong-installation input fails closed. HMAC domain separation includes installation UUID plus documented App/workspace context, and all roles/SoD use random `actor_id`, not the header or email. |
| Browser and same-value recreation model | `RESOLVED_FOR_P0` | A distinct host-only random browser credential is required in addition to the actor mapping. The plan accurately states that identical forwarded-value recreation cannot be detected; it requires unique-person-account policy, bounded expiry, review, offboarding, epoch revocation, and fresh approval for an unrecognized browser. Guaranteed detection makes P6 `UNSUPPORTED`, not falsely secure. |
| Dedicated action secret scope | `RESOLVED_FOR_P0` | The scope is per installation and contains only current/previous HMAC keys because App read access is scope-wide. Secret creation is separately planned and approved before App binding; value exposure, blind regeneration, rotation, retirement, and uninstall behavior are explicit. |
| Fixed role-administration Job | `RESOLVED_FOR_P0` | A named group receives only `CAN_MANAGE_RUN`; the fixed unscheduled Job runs as a separate service principal. Its exact warehouse, parent, table `SELECT`+`MODIFY`, secret-scope, and negative permissions are enumerated, as is the deployer's Service Principal User prerequisite. The only retained parameter is a nonsecret one-time locator. |
| Saved Direct plan binding | `RESOLVED_FOR_P0` | The sidecar covers the gaps in CLI saved-plan validation: exact CLI/checksum, engine, target/profile/host/workspace/principal, variables/resources/configuration, source/build, and semantic remote-state evidence. Immediate re-plan mismatch returns to approval. P3 contains explicit lineage, empty-initial-lineage, source-change, and remote-drift tests. |
| Explicit stopped lifecycle and App start | `RESOLVED_FOR_P0` | Every managed target uses `lifecycle.started: false`; under CLI 1.7.0 that leaves new Apps without compute and stops an existing running App during apply. App code/start then uses exactly `bundle run <app-resource-key>`; bare Bundle-aware `apps deploy` is prohibited. |
| Table creation and non-App per-table grants | `CHANGES_REQUIRED` | The plan assigns table creation, role-principal grants, and App bindings to one Direct plan, but only the last operation is a supported App binding. See `DBX-P0-010`. |

## Prior finding disposition

| Finding | Earlier disposition | Third re-review disposition |
|---|---|---|
| `DBX-P0-001` | Initial `CHANGES_REQUIRED`; resolved in the first and second re-reviews | `RESOLVED_FOR_P0`; no regression in the cross-Job Run Job topology or effective run-as tests. |
| `DBX-P0-002` | Initial `CHANGES_REQUIRED`; resolved in the first and second re-reviews | `RESOLVED_FOR_P0`; no regression in bounded reconciliation, degraded behavior, recovery latency, or exactly-once tests. |
| `DBX-P0-003` | Initial `CHANGES_REQUIRED`; partially resolved through the second re-review | `RESOLVED_FOR_P0`; shared App authorization is only the platform principal, while the human action policy and ledger are independent and Preview-free. |
| `DBX-P0-004` | Initial `CHANGES_REQUIRED`, reopened in the first re-review, resolved in the second | `RESOLVED_FOR_P0`; exact GA CLI/Direct, environment, Python, dbt, SQL channel, and typed workspace gates remain explicit. |
| `DBX-P0-005` | Initial `CHANGES_REQUIRED`; resolved in the first and second re-reviews | `RESOLVED_FOR_P0`; no regression in zero required public runtime egress or the separated signed/locked build-deploy boundary. |
| `DBX-P0-006` | Initial `CHANGES_REQUIRED`; resolved in the first and second re-reviews | `RESOLVED_FOR_P0`; no regression in scoped system enrichment or honest shared-warehouse cost confidence. |
| `DBX-P0-007` | Initial `CHANGES_REQUIRED`; resolved in the first and second re-reviews | `RESOLVED_FOR_P0`; no regression in named App groups, separate access/resource grants, or uninstall preservation. |
| `DBX-P0-008` | Added as `CHANGES_REQUIRED` in the first re-review; partially resolved in the second | `RESOLVED_FOR_P0`; actor enrollment, browser binding, same-value limitation, fixed role Job, exact privileges, and Preview-disabled tests now form one testable contract. |
| `DBX-P0-009` | Added as `CHANGES_REQUIRED` in the first re-review; partially resolved in the second | `RESOLVED_FOR_P0`; saved-plan/source/drift binding, explicit false lifecycle, and exact non-redeploying `bundle run` sequence are accepted. |
| `DBX-P0-010` | Not previously recorded | `NEW — CHANGES_REQUIRED`; the plan needs an executable and approved UC table/schema migration and non-App grant stage. |

## Finding

### DBX-P0-010: The Direct plan cannot create or fully grant the claimed Unity Catalog tables

- Classification: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: `docs/plans/product-plan.md`, **Target architecture**, **Runtime identity model**, **Bootstrap the product**, **Enable optional controlled actions**, P3, P6, P7, and P8; `docs/decisions/0001-private-app-bundle.md`, **Decision** and **Consequences**; `docs/plans/documentation-plan.md`; `docs/research/source-register.md`
- Evidence:
  - The official Bundle supported-resource table for CLI 1.7.0 includes Unity Catalog catalogs, schemas, and volumes, but not managed Delta tables or views. The read-only local `databricks bundle schema` result agrees: `resources` has no `tables` key.
  - An App `uc_securable` Bundle entry takes `securable_full_name` and a `TABLE` permission. The App resource prerequisites and table-resource page both require that the table already exist. The binding grants the App service principal; it cannot create the table or grant the role-administration/collector service principals.
  - The product plan says P6 “adds the secret scope/key, restricted action tables, role-administration Job, and selected observed-Job run grants together,” and says one `ACTION_BUNDLE_PLAN` generates the Direct plan for the restricted tables, role Job, App table grants, and observed-Job grants. The base bootstrap likewise has no stage that creates its normalized tables/views before collector and App grants are used.
  - Hiding DDL or `GRANT` statements in a Bundle pre-deploy script would not fix the reviewed-plan contract. CLI 1.7.0 executes that script before applying the saved Direct plan, while the script's SQL mutations are not Direct resources in the machine-readable plan. The plan also correctly prohibits relying on the experimental `job_runs` Bundle resource.
- User/system impact: A literal implementation fails when the App binding references a missing table, or it silently introduces manual SQL, an unreviewed pre-deploy mutation, a broad schema grant, or a principal with excess DDL authority. Any of those outcomes breaks the promised no-mutation-before-visible-plan, resumability, least-privilege, rollback, and uninstall contracts in a regulated installation.
- Required change:
  1. Choose and document one GA table/bootstrap path for both the base normalized schema and the optional P6 restricted schema. A customer-preprovisioned schema is acceptable only if every exact table, view, owner, and grant becomes a typed readiness prerequisite; otherwise add a product-owned migration path.
  2. For the preferred product-owned path, add explicit `DATA_PLAN`, `DATA_APPROVE`, `DATA_APPLY`, and `DATA_VERIFY` stages. Show deterministic versioned DDL and exact per-principal grants, bind approval to their digest plus workspace/principal/warehouse/schema state, and execute them through a fixed least-privilege identity after approval.
  3. Keep that mutation separate from the Direct resource plan. After the tables and non-App grants are verified, regenerate the Direct plan so App `uc_securable` bindings point only to existing tables. Do not claim the Direct diff contains SQL table creation or the role/collector principal grants.
  4. Define idempotency, transaction boundaries, partial multi-table recovery, concurrent installer exclusion, schema-version compatibility, upgrade ordering, rollback limits, and safe receipts without raw SQL or internal IDs in ordinary output.
  5. Keep base App/action routes unavailable until the required table schema, grants, bindings, and code version all match. A P6 partial operation must leave the read-only product intact and actions locked.
  6. Give the migration identity only the temporary DDL/grant authority required for the reviewed objects, remove temporary product-created authority in a recovery-safe final stage, preserve pre-existing customer grants, and include every table/grant in access review and uninstall evidence.
  7. Update the ADR, installer stages, source register caution, support/readiness matrix, documentation plan, P3/P6/P7/P8 exits, and generated-Bundle policy tests together. Explicitly prohibit mutation-bearing Bundle pre-deploy scripts in the saved-plan path unless a separate reviewed decision replaces the current approval model.
- Testable acceptance:
  1. A clean supported workspace produces a read-only Direct resource plan plus a separate deterministic table/grant plan before either mutation. No table, view, grant, or App binding exists before its recorded approval.
  2. Base and P6 fresh install, no-op, upgrade, interrupted partial apply, retry, rollback, and uninstall fixtures prove exact schema versions, grants, receipts, and stopped/locked states.
  3. App binding is attempted only after every referenced table exists; it fails closed if a table, owner, schema version, or expected role/collector grant is missing or drifted.
  4. Positive tests prove the collector, App, and role Job can perform only their listed operations. Removing warehouse `CAN_USE`, parent `USE`, table `SELECT`, table `MODIFY`, secret read, or Job permission independently produces the expected denial without substituting a broader grant.
  5. A failed or cancelled migration leaves no action endpoint enabled, no paid compute running, and a safe resumable or cleanup operation. Pre-existing customer objects and grants are unchanged.
  6. Static policy rejects table-creation claims in the Direct plan, required experimental `job_runs`, mutation-bearing pre-deploy scripts, schema-wide `MODIFY`, and App binding to an unverified table.

## Reviewed-file outcome

| File or set | Outcome | Databricks conclusion |
|---|---|---|
| `README.md`, `AGENTS.md`, `docs/index.md` | `PASS` | Product boundary, evidence rules, exact feature-status policy, and review process remain appropriate. |
| `docs/decisions/0001-private-app-bundle.md` | `CHANGES_REQUIRED` | Identity and lifecycle decisions are accepted, but the decision must distinguish Direct resources from the table/grant migration path in `DBX-P0-010`. |
| `docs/plans/product-plan.md` | `CHANGES_REQUIRED` | `DBX-P0-008` and `DBX-P0-009` are closed; the base/P6 table bootstrap and non-App grant order is not executable as written. |
| `docs/plans/review-process.md` | `PASS` | Independent frozen-input review, finding format, re-review, and P0-P10 gates remain sound. |
| `docs/plans/documentation-plan.md` | `CHANGES_REQUIRED` | Add the schema migration/grant plan, recovery, upgrade, rollback, and uninstall pages/sections required by `DBX-P0-010`; do not describe those mutations as Direct resources. |
| `docs/research/source-register.md` | `CHANGES_REQUIRED` | Existing sources are relevant, but the Bundle resource and App table rows must record that tables must preexist and that Direct has no managed Delta-table resource in CLI 1.7.0. |
| `docs/reviews/p0-planning-baseline/resolution.md` | `NOT_AN_APPROVAL_INPUT` | Its resolutions of `DBX-P0-001` through `DBX-P0-009` are accepted, but the ledger predates `DBX-P0-010`. |

## P0-P10 Databricks matrix

| Part | Outcome | Databricks conclusion and required evidence |
|---|---|---|
| P0 — Product contract | `CHANGES_REQUIRED` | Resolve `DBX-P0-010`, freeze a new author-input hash, and re-review the corrected bootstrap/grant sequence. All earlier Databricks findings are closed. |
| P1 — Capture library | `PASS_WITH_FOLLOW_UP` | No regression. Retain typed attempt identity, actual compatibility metadata, schema versions, and no live Databricks dependency. |
| P2 — Collector and reconciliation | `PASS_WITH_FOLLOW_UP` | No regression. Live proof still must assert both run-as principals, negative permissions, cancellation/timeout recovery, and one AttemptKey; collector writes require verified pre-existing tables from the corrected bootstrap. |
| P3 — Bundle installer | `CHANGES_REQUIRED` | Separate the saved Direct resource plan from deterministic table/view DDL and non-App table grants, then prove approval binding, ordering, resume, lifecycle, upgrade, rollback, and uninstall. |
| P4 — App read-only MVP | `PASS_WITH_FOLLOW_UP` | Curated-only reads, no broad system access, statelessness, cost confidence, and accessibility remain sound. The App starts only after its curated objects and bindings verify. |
| P5 — Job onboarding | `PASS_WITH_FOLLOW_UP` | No regression. Preserve five scanner states, source-controlled semantic-change review, Run Job topology, grants, and rollback visibility. |
| P6 — Controlled actions | `CHANGES_REQUIRED` | The actor/browser/role-Job authorization contract now passes, but P6 cannot install until restricted tables and role-principal grants have an explicit approved GA migration stage before App binding. |
| P7 — Security and operations | `CHANGES_REQUIRED` | Rotation/revocation and identity limits are sound. Upgrade, rollback, access review, and uninstall must include schema versions, temporary migration authority, per-table grants, partial migration recovery, and preservation of customer grants. |
| P8 — Bounded live proof | `PASS_WITH_FOLLOW_UP` | The cost/cleanup envelope remains sufficient. Add scoped evidence for the corrected table/grant plan and verify a failed migration leaves no App/warehouse compute running. |
| P9 — Optional intelligence | `PASS_WITH_FOLLOW_UP` | No regression. AI remains outside authorization, command construction, capture, schema migration, and validation. |
| P10 — Private alpha | `PASS_WITH_FOLLOW_UP` | Retain Preview-disabled, separated-role, clean-install, upgrade, and uninstall journeys. A non-author must complete the corrected data/bootstrap and Direct-plan sequence without SQL, IDs, paths, or YAML. |

## Final verdict

`CHANGES_REQUIRED`

The private Databricks App plus plain-YAML Direct Bundle remains the recommended starting architecture. Baseline 0.4 successfully resolves the actor/browser authorization and exact saved-plan/App-lifecycle findings, including the platform's same-value recreation limitation. P0 can return for a narrow fourth Databricks re-review after the author adds a source-backed, separately approved, idempotent table/view and non-App grant bootstrap before the Direct App-binding plan. No live cloud proof is required to close that planning defect; live qualification remains correctly assigned to P3, P6, P7, and P8.
