# Databricks platform/security eleventh re-review: P0 planning baseline

- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform/security reviewer
- Immutable author input SHA-256: `93343ae870073dbe4518765b8949edc29d0a992255b36854b0e62c631f78392b`
- Baseline: 0.12
- Verdict: `CHANGES_REQUIRED`
- Cloud mutation: none

## Immutable input verification

I read every frozen author file: `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, globally sorted. I also read the tenth Databricks, dbt Core, and usability re-reviews before reaching this independent platform/security conclusion.

I recomputed the requested digest by sorting the author paths, hashing each file with SHA-256, concatenating those path-ordered hash records, and hashing that stream. The result was exactly:

```text
93343ae870073dbe4518765b8949edc29d0a992255b36854b0e62c631f78392b
```

The hash still matched immediately before this report was written. No author file or earlier review was changed. This report is the only file written. I made no Azure, Databricks, authentication, account-console, SQL, warehouse, App, Job, or Unity Catalog call.

## Executive assessment

Baseline 0.12 correctly resolves the two deployment-protocol defects from the tenth review:

- `DBX-P0-022` is resolved. The stage Direct plan is generated, approved, and applied first. Deployment reconciliation and stop then establish current Direct and remote state. Only afterward is the executable final-binding plan generated and separately approved. First install, upgrade, rollback, interruption, stale serial, remote drift, partial Apply, P6 extension, and uninstall all use fresh planning rather than a lineage/serial bypass.
- `DBX-P0-023` is resolved. The wrapper fully paginates and canonicalizes the deployment inventory before and after the one permitted pinned `bundle run` invocation; acknowledges both the prior-deployment start and the runner's possible internal POST reissue; stops on success, error, timeout, or lost response; and accepts only exactly one new terminal successful matching `SNAPSHOT`, with no pending or unexplained deployment. A human never selects an internal deployment ID.
- The implementation-level component cardinality, client-signature non-authority, latest-generation reduction, and same-statement P6 gate requested by `DBX-P0-024` are substantially improved. One physical row is now one logical event, the whole component set is a typed nested array, the status view is installation-wide, and optional signatures are explicitly excluded from positive trust.

The recommended architecture therefore remains a private Databricks App deployed through a plain-YAML Direct Bundle, with customer-local Unity Catalog data and an attended fixed Statement Execution control plane. Apps and Direct are GA, the CLI is pinned, and the required path still avoids Preview identity APIs.

P0 nevertheless remains blocked by three related defects in the newly frozen runtime-trust contract:

1. The contract does not unambiguously represent and validate both the pre-start and post-start machine observations or the one permitted lifecycle-state transition between them.
2. Early roster reuse can derive a positive current generation from an orphaned, invalidated, unaccepted, or transitively reused candidate anchor; the direct pointer can also extend the evidence clock despite the prose prohibition.
3. The claimed frozen physical schema and canonical identifiers remain incomplete, and `current_timestamp()` is described as a commit timestamp even though Databricks defines it at query-evaluation start.

These are positive-authorization defects, not documentation polish: `runtime_trust_status_v` controls every trusted label and P6 conditional DML. All three must be resolved before implementation begins.

## Current primary evidence checked

All platform claims below were checked against current official Microsoft/Databricks documentation or the exact first-party CLI source pinned by the plan.

### Sequential Direct plans and deployment reconciliation

- [Bundle direct deployment engine](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/direct) documents Direct's separate local/remote state and saved plan/apply workflow. [Databricks CLI v1.3.0](https://github.com/databricks/cli/releases/tag/v1.3.0) records Direct as GA/default for new deployments; the baseline pins [CLI v1.7.0](https://github.com/databricks/cli/releases/tag/v1.7.0).
- In pinned CLI 1.7.0, [`ValidatePlanAgainstState`](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/direct/bundle_plan.go#L42-L57) enforces the saved plan's lineage and serial, and the pinned [`bundle deploy --plan` path](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/cmd/bundle/utils/process.go#L240-L265) invokes that validation. Baseline 0.12 now plans in the required sequence and never disables this guard.
- The pinned [`bundle run` App runner](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/run/app.go#L48-L95) can start the prior last active deployment before deploying. Its [deployment helper](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/bundle/appdeploy/app.go#L80-L112) can reissue the deploy request after an error. Baseline 0.12 now treats an invocation as potentially multiple submissions and reconciles remote results instead of retrying the wrapper.
- The [Apps CLI reference](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/reference/apps-commands) documents App get/start/stop and deployment list/get operations. The pinned [`list-deployments` implementation](https://github.com/databricks/cli/blob/2f68ee4951ef96fa9d99e40c8ebadccf08412d58/cmd/workspace/apps/apps.go#L1288-L1365) exposes iterator-backed pagination. Baseline 0.12 explicitly consumes every page and checks active/pending state before and after the command.
- [Manage Databricks Apps using Declarative Automation Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial) distinguishes resource deployment from `bundle run` code deployment. [Get started with Databricks Apps](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/get-started) exposes the deployment ID, immutable deployment artifact, mode, and terminal state needed by the selected reconciliation policy.

### Delta event authority and time semantics

- [ACID guarantees on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/acid) and [Delta `MERGE INTO`](https://learn.microsoft.com/en-us/azure/databricks/delta/merge) support one managed Delta table and one atomic conditional event insert. This remains the right GA storage boundary.
- [Constraints on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/tables/constraints) confirms that primary and foreign keys are informational. The wrapper and status view, rather than a declared key, must therefore reject duplicates, conflicts, and invalid chains.
- [`current_timestamp()`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/functions/current_timestamp) returns the timestamp at the start of query evaluation. It is server-derived and suitable as a conservative statement-time anchor, but it is not a Delta commit timestamp and must not be named or described as one.
- [RFC 8785 JSON Canonicalization Scheme](https://www.rfc-editor.org/rfc/rfc8785) defines deterministic JSON serialization. It does not supply the product's domain labels, object property names, field inclusion rules, or digest dependency graph; those remain part of the dbtobsb contract.

## Ranked findings

| Rank | Finding | Severity | P0 effect |
|---:|---|---|---|
| 1 | `DBX-P0-025` - the frozen ledger does not unambiguously retain and validate both machine observations | High | Blocks P0; `CHANGES_REQUIRED` |
| 2 | `DBX-P0-026` - early roster-anchor reuse is not closed over an independently valid source attestation | High | Blocks P0; `CHANGES_REQUIRED` |
| 3 | `DBX-P0-027` - the physical schema, canonical ID objects, and server-time name are not actually frozen | High | Blocks P0; `CHANGES_REQUIRED` |

### DBX-P0-025: the frozen ledger does not unambiguously retain and validate both machine observations

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: `TRUST_CANDIDATE`, `SNAPSHOT_ACCEPTED`, `runtime_trust_status_v`, accepted/stale labeling, P6 authorization, refresh, upgrade/rollback, and evidence/audit documentation.
- Evidence:
  1. The physical schema has only one event-scoped `machine_observation_digest` column.
  2. `TRUST_CANDIDATE` requires a complete **pre-start** machine observation while the App and selected deployment are stopped.
  3. `SNAPSHOT_ACCEPTED` says it repeats every deployment/inventory/graph/roster/component value and “adds” the matching **post-start** machine observation after the App is active. It does not say whether its single machine field replaces the candidate value, is a composite of both values, or repeats one value while an unnamed field holds the other.
  4. A single field per event can be valid only if event-specific semantics are explicit: candidate row = pre-start digest, acceptance row = post-start digest, and the status view joins both rows. That mapping is not present in the schema/nullability table or status-view reduction.
  5. The complete machine observations cannot simply be required equal. The candidate must prove `STOPPED`; the acceptance must prove `ACTIVE`. Only their stable graph projection—deployment ID, code/artifact/configuration, bindings, ACLs, grants, component set, and deployment inventory—must remain equal while lifecycle state makes one defined transition.
  6. The status view says it checks matching graph fields and exposes “both evidence times,” but it does not name both machine digests, define their lifecycle roles, or reject missing, swapped, overwritten, or wrong-state observations. “Both evidence times” elsewhere means roster and accepted-machine evidence, leaving the pre-start observation contract implicit.
- User/system impact:
  - Two implementers can build incompatible accepted-state views from the same rows.
  - An acceptance can overwrite or omit the stopped-state proof, compare two full observations incorrectly, or authorize a graph that changed between stop and start.
  - P6 can receive a fresh accepted status without one executable rule proving both observations and the exact permitted state transition.
- Required acceptance condition:
  1. Choose and freeze one representation. Either add explicitly typed `pre_start_machine_observation_digest` and `post_start_machine_observation_digest` fields with per-event nullability, or state that the candidate and acceptance instances of `machine_observation_digest` have those exact distinct roles and expose them under phase-specific aliases in the view.
  2. Freeze the canonical machine-observation object and separate its stable graph projection from lifecycle facts. Candidate requires `STOPPED`; acceptance requires `ACTIVE`; selected deployment is identical; pending count remains zero; and every stable projection field compares equal.
  3. Make acceptance and `runtime_trust_status_v` require exactly one of each phase observation through the exact candidate/acceptance predecessor chain. Missing, duplicate, swapped, wrong-state, or stable-projection mismatch must derive `RUNTIME_TRUST_UNVERIFIED`.
  4. Include both phase digests and their server statement-time anchors in the appropriate payload/candidate/acceptance/snapshot identities without a digest cycle. State which times are exposed and which time bounds validity.
  5. Add SQL/golden fixtures for missing pre/post evidence, reversed phases, `ACTIVE` before candidate, `STOPPED` after start, changed deployment/configuration/binding/grant, pending deployment, duplicate rows, exact retry, and the valid `STOPPED` to `ACTIVE` path.

### DBX-P0-026: early roster-anchor reuse is not closed over an independently valid source attestation

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: early unchanged refresh, roster evidence expiry, source-generation invalidation, current-view reduction, P6, recovery, and audit display.
- Evidence:
  1. A new roster comparison is anchored by a candidate that points to itself. An early refresh may instead point to “one prior unexpired candidate anchor” with equal account/workspace, service-principal set, rosters, reviewer, and components.
  2. The reuse rule does not require that source candidate to be self-anchored, to belong to exactly one complete accepted generation, or to have zero invalidations, unknown events, duplicate/conflicting rows, or broken predecessor links. The source can therefore be orphaned, never accepted, or later invalidated even though a candidate is explicitly “never positive trust.”
  3. The accepted-row rule rejects a missing, duplicate, expired, or mismatched anchor, while the current view requires zero invalidations only for the globally latest generation. Neither rule validates the complete source generation behind a reused prior anchor.
  4. The schema has only the direct `roster_anchor_event_id` pointer. If generation B reused generation A's original roster evidence and generation C points to B's candidate, the accepted-row formula uses B's later `server_commit_at`, not A's original evidence time. This transitively extends expiry despite the text saying reuse cannot change the earlier server time.
  5. A later invalidation or conflict in the source generation is not named as a dynamic reason for the current accepted generation to become unverified.
- User/system impact:
  - A non-positive or invalid source event can supply the roster half of a new positive runtime-trust decision.
  - Chained refreshes can extend a 24-hour roster review without another native account-console comparison.
  - The UI and P6 can remain accepted after the source evidence on which they depend is invalidated or made ambiguous.
- Required acceptance condition:
  1. Select one explicit authority model. The conservative model is to permit reuse only from the original self-anchored candidate of exactly one historically valid registration/candidate/acceptance chain with zero invalidations, unknown operations, duplicates, conflicts, or broken links. If roster evidence is intended to remain independently valid even when the machine generation fails, define a separate `ROSTER_ATTESTED` event and its own exact writer, chain, invalidation, and status rules instead of deriving authority from a non-positive candidate.
  2. Always reference the original self-anchored roster event; prohibit a pointer to an intermediate reuse candidate. Compute expiry from that original server statement-time value so refresh can never move it forward.
  3. Make the latest status view validate the complete referenced source attestation every time. A source invalidation, duplicate, payload conflict, unknown operation, deletion, or broken link must immediately make the dependent current generation unverified.
  4. Include the original anchor ID and digest in current acceptance/snapshot identity and expose its age without exposing raw roster identity.
  5. Add fixtures for orphan, incomplete, unaccepted, invalidated-before-reuse, invalidated-after-acceptance, duplicate/conflicting, transitive, expired, deleted, and tampered source anchors plus one valid unchanged reuse.

### DBX-P0-027: the physical schema, canonical ID objects, and server-time name are not actually frozen

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: P1/P3 table DDL and writer, all event IDs/readback, current-view SQL, P2/P4 labels, P6 conditional DML, recovery, interoperability, and fixtures.
- Evidence:
  1. The “physical schema and nullability are frozen” table gives six named deployment columns followed by prose: “plus source/build/artifact/configuration/App-resource/ACL/Job-run-as/UC-grant/group-root/expected-roster/observed-roster digests.” Those fields have no exact column names, SQL types, or declared nullability.
  2. Event-specific nullability remains prose such as “may omit,” “retains only facts already known,” and “every field.” There is no exhaustive four-event column matrix. `state` and `reason` are non-null for every row but have no closed values or per-operation meaning.
  3. `candidate_digest` and `acceptance_digest` are stored and used by later IDs but their input objects are undefined.
  4. The identifier paragraph names RFC 8785 and broad field groups but not the exact domain-separation constants, JSON property names/types, array objects, absent-versus-null rules, or versioned dependency order. “Every client-bound field” does not explicitly exclude the digest being calculated or derived `event_id`, `ledger_row_id`, `snapshot_id`, `candidate_digest`, and `acceptance_digest`, leaving a circular or implementation-dependent payload definition.
  5. `snapshot_id` depends on `acceptance_digest`, which is itself undefined. Two compliant-looking implementations can therefore disagree on IDs, exact retries, conflicts, and accepted snapshot identity.
  6. `server_commit_at` is populated by statement-scoped `current_timestamp()` and repeatedly described as the event's server commit. Official Databricks SQL semantics define that function at the **start of query evaluation**, not at Delta commit. The value is server-derived and conservative for expiry, but the current name and claim are false.
  7. The status-view and P6 prose is a useful semantic sketch, but without the complete fields, phase-specific observation roles, roster-source validation, and exact identifier construction, it is not yet one executable fail-closed reduction.
- User/system impact:
  - Python, SQL, App, and documentation implementations can produce different IDs and disagree whether a retry conflicts or no-ops.
  - A malformed event can exploit null/omission differences or an unclosed state/reason value and be interpreted differently by the writer and view.
  - Audit output labels a query-start value as a commit timestamp, which overstates what the platform proves.
  - P6's authorization statement cannot be fixture-tested against one canonical accepted row until the schema and view projection are exact.
- Required acceptance condition:
  1. Publish the exhaustive managed-table DDL: every column's exact name, SQL type, nested type, and base nullability, plus a per-operation required/null/allowed-value matrix. Close `operation`, `state`, `reason`, deployment mode, counts, component keys, and lifecycle values.
  2. Publish versioned canonical object definitions for `event_id`, `payload_digest`, `ledger_row_id`, `candidate_digest`, `acceptance_digest`, `snapshot_id`, deployment-set digests, machine observations, roster observations, and component observations. Define literal domain labels, property names/types, null/absent handling, sorting, inclusions/exclusions, and a non-circular dependency graph.
  3. Rename `server_commit_at` to an accurate term such as `server_recorded_at` or `statement_evaluated_at`, and state that one server `current_timestamp()` expression is fixed at query-evaluation start and may precede the Delta commit. If an actual commit timestamp is required, qualify a separate GA mechanism rather than relabeling this function.
  4. Freeze reference SQL or an equivalent complete relational specification for `runtime_trust_status_v`, including both machine phases, roster-source validity, all duplicate/conflict checks, latest-generation selection, invalidation precedence, expiry, and exact output types.
  5. Freeze the P6 same-statement predicate against named view columns: exact installation, generation, snapshot, state, validity, and exactly one `CONTROLLED_ACTIONS` component/digest. Absence, duplicate summary, null, stale evaluation, and view error must prevent DML.
  6. Add shared golden canonicalization vectors and Delta fixtures consumed by every implementation language, including null/absent, Unicode, array order, same-event/different-payload, cross-version, duplicate, and timestamp-boundary cases.

## Focused disposition of tenth-review findings

### DBX-P0-022

`RESOLVED_FOR_P0`

The executable plans are now sequential. A non-executable pre-stage intent is clearly distinguished from the saved final plan. The fresh final plan receives its own approval after stage Apply, deployment reconciliation, and stop; it binds current lineage/serial and unchanged source/build/configuration/deployment; drift or partial failure returns to recovery and re-planning. This is propagated through first install, upgrade, rollback, P6, recovery, tests, ADR, review process, and documentation.

### DBX-P0-023

`RESOLVED_FOR_P0`

The wrapper no longer equates one invocation with one POST. It consumes the complete before and after inventories, includes active/pending state, acknowledges the old-code interval and pinned helper reissue, never retries the wrapper, stops on every exit, accepts exactly one matching terminal `SNAPSHOT`, and fails closed on zero/multiple/pending/mismatched/unexplained outcomes. This is the correct containment and reconciliation policy for the pinned runner.

### DBX-P0-024

`PARTIALLY_RESOLVED; RESIDUAL_SUPERSEDED_BY_DBX-P0-025_THROUGH_027`

Baseline 0.12 resolves the former row/component cardinality ambiguity, signature-authority ambiguity, and high-level latest-generation/P6 structure. The remaining implementation blockers are now narrower and concrete: dual machine-observation semantics, roster-source eligibility and non-extension, exhaustive columns/nullability, canonical digest objects, accurate server-time semantics, and the resulting exact view/P6 specification. Those residuals are tracked as 025-027 rather than leaving 024 as an undifferentiated finding.

## Prior-finding disposition

| Finding | Eleventh re-review disposition |
|---|---|
| `DBX-P0-001` through `DBX-P0-008` | `RESOLVED_FOR_P0`; no regression found in identity separation, bounded reconciliation, App/action authorization, prerequisites, egress, optional enrichment, App permission/resource separation, or P6 identity/DML boundaries. |
| `DBX-P0-009` | `RESOLVED_FOR_P0`; the stale-plan regression identified as 022 is fixed by sequential post-stage final planning. |
| `DBX-P0-010` through `DBX-P0-019` | `RESOLVED_FOR_P0`; no regression found in deployment/data-plane separation, recoverable fixed DML, targeted grants, migration identity, pending/composite truth, warehouse/Query History recovery, exact runtime DML, whole-group roots, or direct-versus-effective warehouse authority. |
| `DBX-P0-020` | `RESOLVED_FOR_CORE_ORDERING`; intended code is staged before candidate, final bindings are applied while stopped, direct start precedes the post-start observation, and only acceptance unlocks. Findings 025-027 concern the proof representation, not this order. |
| `DBX-P0-021` | `RESOLVED_IN_SUBSTANCE; EXACT_CONTRACT_OPEN`; the durable customer-local carrier, access, expiry, lifecycle, restart, retention, and uninstall path remain present. Exact positive-state semantics are blocked by 025-027. |
| `DBX-P0-022` | `RESOLVED_FOR_P0`; sequential fresh final planning is complete. |
| `DBX-P0-023` | `RESOLVED_FOR_P0`; complete deployment-set reconciliation is complete. |
| `DBX-P0-024` | `PARTIALLY_RESOLVED`; component/cardinality, signature non-authority, and high-level reduction are fixed; remaining exact-contract defects are superseded by 025-027. |
| `DBX-P0-F01` | `RESOLVED_FOR_P0`; current DML, inheritance, ownership/`MANAGE`, visibility, pagination, and whole-group roots remain explicit. |
| `DBX-P0-F02` | `RESOLVED_FOR_P0`; optional enrichment remains separate, pair-scoped, disabled by default, and removable. |

## Author-file outcome

| Author file or set | Outcome | Databricks conclusion |
|---|---|---|
| `README.md` | `CHANGES_REQUIRED` | The architecture and deployment summary are correct, but “server commit times” is inaccurate and the whole-generation trust claim depends on exact dual-observation and roster-anchor rules. |
| `AGENTS.md` | `CHANGES_REQUIRED` | Deployment invariants are now strong; the ledger invariant still overstates frozen canonical IDs/server commit semantics and does not close the two evidence paths. |
| `docs/index.md` | `PASS` | The index introduces no independent platform/security contradiction. |
| `docs/decisions/0001-private-app-bundle.md` | `CHANGES_REQUIRED` | Preserve the chosen architecture and lifecycle. Correct the time claim and freeze machine-phase and reusable-roster authority before the ADR is implementable. |
| `docs/plans/product-plan.md` | `CHANGES_REQUIRED` | Primary location of 025-027: singular phase-ambiguous machine field, under-qualified reusable candidate anchor, prose-only columns/nullability, undefined digests, and query-start time named as commit. |
| `docs/plans/review-process.md` | `CHANGES_REQUIRED` | Add explicit gates for the two machine phases/stable projection, original roster-source chain/non-extension, exhaustive event matrix, canonical object vectors, and accurate Databricks time semantics. |
| `docs/plans/documentation-plan.md` | `CHANGES_REQUIRED` | The planned captures must teach and display the exact pre/post machine proof and original roster anchor; replace commit-time wording and define the failure/recovery states for source-anchor invalidation. |
| `docs/research/source-register.md` | `CHANGES_REQUIRED` | It now records the saved-plan/runner mitigations well. Add the official `current_timestamp()` semantics and stop saying the schema's broad digest fields are already exact until names/types/nullability and canonical objects are frozen. |

## P0-P10 Databricks coverage matrix

These are planning outcomes; they do not claim implementation or live evidence exists.

| Part | Planning outcome | Databricks conclusion and required next evidence |
|---|---|---|
| P0 - Product contract | `CHANGES_REQUIRED` | Resolve 025-027 and re-review a new immutable author set. The private App plus Direct Bundle remains the recommended architecture. |
| P1 - Capture library | `CHANGES_REQUIRED` | Baseline 0.12 explicitly assigns the physical schema to P1/P3; implement only after exact columns, per-event nullability, canonical objects, and golden vectors are frozen. |
| P2 - Collector and reconciliation | `CHANGES_REQUIRED` | Three-table/no-DDL boundaries remain sound, but snapshot/state stamps depend on one deterministic status view and exact component/phase identity. |
| P3 - Bundle installer | `CHANGES_REQUIRED` | Sequential Direct planning and deployment reconciliation now pass. The installer still needs an executable event writer/readback/view contract with accurate server-time semantics and closed roster reuse. |
| P4 - Read-only App MVP | `CHANGES_REQUIRED` | Setup-only safe boot and view-only reads remain sound. Every-page accepted/stale/unverified display must derive from the corrected dual-observation and roster-source rules. |
| P5 - Existing-job onboarding | `PASS` | Scanner, proposed patch, owner approval, and rollback classification are not changed by these findings. Evidence cannot be labeled trusted until P3/P4 pass. |
| P6 - Controlled actions | `CHANGES_REQUIRED` | The semantic same-statement gate is directionally correct, but it must join exact view columns produced from both machine phases and an independently valid original roster anchor. |
| P7 - Security and operations | `CHANGES_REQUIRED` | Document original-anchor invalidation/recovery, precise query-start time meaning, digest/version migration, retained-ledger compatibility, and administrator-root limits. |
| P8 - Bounded live proof | `CHANGES_REQUIRED` | Deployment lifecycle fixtures are now well planned. Add the phase-swap/stable-graph, orphan/invalidated/transitive roster, canonical-ID, schema-nullability, and statement-time boundary cases from 025-027. |
| P9 - Optional intelligence | `PASS` | Genie/AI remains optional and outside capture, deployment, data seal, authorization, and runtime-trust authority. No Preview AI feature is required for the base path. |
| P10 - Private alpha | `CHANGES_REQUIRED` | Non-author installs/upgrades cannot be accepted until independent implementations produce identical event IDs/view state and the evidence chain cannot reuse or lose authority ambiguously. |

## Explicit verdict

`CHANGES_REQUIRED`

Baseline 0.12 preserves the recommended Azure Databricks product architecture and now has a credible first-install, upgrade, rollback, recovery, P6, and deployment-reconciliation protocol around pinned CLI 1.7.0. `DBX-P0-022` and `DBX-P0-023` are resolved. No new required Preview dependency was found.

The remaining work is one bounded trust-contract revision: represent and validate both pre-start and post-start machine observations with the exact permitted lifecycle transition; make roster reuse depend on one original, independently valid, non-extendable source attestation; and publish exhaustive DDL/nullability, canonical digest objects, accurate server statement-time semantics, reference view reduction, and the exact P6 predicate. Propagate those decisions through the ADR, source register, review process, documentation plan, and fixtures, then request another independent Databricks platform/security review.
