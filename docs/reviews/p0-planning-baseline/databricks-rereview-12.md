# Databricks platform/security twelfth re-review: P0 planning baseline

- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform/security reviewer
- Immutable author input SHA-256: `2bde12f3f3eef01efecef33f483015cbcf2588234281666ba192a6d7534c81c7`
- Baseline: 0.13
- Verdict: `CHANGES_REQUIRED`
- Cloud mutation: none

## Immutable input verification

I read every frozen author file: `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, globally sorted. I also read the eleventh Databricks, dbt Core, and usability re-reviews before reaching this independent platform/security conclusion.

I recomputed the requested digest by globally sorting the author paths, hashing each file with SHA-256, concatenating those path-ordered hash records, and hashing that stream. The result was exactly:

```text
2bde12f3f3eef01efecef33f483015cbcf2588234281666ba192a6d7534c81c7
```

The hash still matched immediately before this report was written. No author file or earlier review was changed. This report is the only file written. I made no Azure, Databricks, authentication, account-console, SQL, warehouse, App, Job, or Unity Catalog call.

## Executive assessment

Baseline 0.13 closes almost all of the implementation-contract ambiguity from the eleventh review:

- `DBX-P0-025` is resolved. The DDL, event matrix, canonical machine-observation object, status reduction, and fixtures now retain distinct pre-start `STOPPED` and post-start `ACTIVE` observations, exclude lifecycle facts from the stable graph, require the same selected deployment, and reject missing, reversed, swapped, or graph-changing phases.
- `DBX-P0-026` is resolved. Reuse points directly to the original self-anchored roster observation, requires the immediately prior accepted generation to reference it, revalidates one complete accepted source chain on every query, fails after later invalidation/deletion/conflict/tamper, and never moves the original expiry clock.
- Most of `DBX-P0-027` is resolved. The baseline now supplies exhaustive DDL, a four-event required/null matrix, closed values, literal canonical objects, an acyclic dependency order, accurate query-start timing, an exact summary projection/reduction, and the P6 cardinality predicate.
- Deployment-bearing generations require exactly one new immutable deployment record, while `UNCHANGED_REFRESH` requires a zero-sized difference, equal inventories, no Bundle run, and an explicit stop/start of the already accepted deployment.

The recommended architecture therefore remains a private Databricks App deployed through a plain-YAML Direct Bundle, with customer-local Unity Catalog state, attended fixed Statement Execution, pinned CLI behavior, and no required Preview identity or external telemetry platform.

P0 is still not acceptable for implementation because two positive-authorization details remain open:

1. The claim that a new trust generation or invalidation locks P6 immediately is stronger than the GA Databricks transaction boundary actually used. The P6 statement reads the runtime-trust table/view but writes a different action table; a concurrent trust change need not conflict, and the subsequent Jobs API start is outside the SQL statement.
2. The canonical contract maps unrestricted SQL `BIGINT` values to RFC 8785 JSON numbers. JCS/I-JSON cannot guarantee exact cross-language interchange for every 64-bit integer, so Python, SQL, and JavaScript can derive different authoritative identifiers from an otherwise accepted row.

The first is a high-severity authorization race. The second is a medium-severity deterministic-identity defect. Both are bounded planning fixes, but both must be frozen before P1/P3/P6 implementation begins.

## Current primary evidence checked

All platform claims below were checked against current official Microsoft/Databricks documentation or first-party standards/source.

### App and Direct architecture

- [Bundle direct deployment engine](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/direct) documents Direct's local/remote state and saved plan/apply flow. [Manage Databricks Apps using Declarative Automation Bundles](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/apps-tutorial) distinguishes resource deployment from App code deployment. The frozen sequential stage/reconcile/stop/fresh-final-plan protocol remains the right containment for the pinned runner.
- [App state and cost](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts#app-state), [App resources](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/resources), and [App authorization](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/auth) support the stateless App, dedicated principal, explicit binding, stop/cleanup, and GA shared-principal boundaries selected by the baseline.

### Transaction and isolation boundary

- [ACID guarantees on Azure Databricks](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/acid) states that, by default, each SQL statement is one atomic transaction against one table; reads use snapshot isolation; and reads from multiple tables do not interrupt concurrent transactions that modify those tables.
- [Delta isolation levels](https://learn.microsoft.com/en-us/azure/databricks/optimizations/isolation/isolation-levels) states that concurrent-operation isolation applies to a given table and that reads always use snapshot isolation. Setting the action table to `Serializable` does not by itself turn a separately read trust table or a later platform API call into the same transaction.
- [Transactions](https://learn.microsoft.com/en-us/azure/databricks/transactions/) and [catalog commits](https://learn.microsoft.com/en-us/azure/databricks/tables/features/catalog-commits) document multi-statement/multi-table managed Delta transactions. For Unity Catalog managed Delta, this facility is Public Preview as of this review and therefore cannot silently become a required fix in this GA-only regulated baseline.

### Canonical number interoperability

- [RFC 8785 section 3.1 and Appendix B](https://www.rfc-editor.org/rfc/rfc8785.html) require JCS number data to be expressible as IEEE 754 double precision, recommend strings for longer integers, and identify `-9007199254740991` through `9007199254740991` as the interoperable exact-integer range.
- [RFC 7493 section 2.2](https://www.rfc-editor.org/rfc/rfc7493.html) says a receiver cannot be expected to preserve an integer with absolute value greater than `9007199254740991` exactly and specifically recommends string encoding for exact 64-bit integer interchange.

## Ranked findings

| Rank | Finding | Severity | P0 effect |
|---:|---|---|---|
| 1 | `DBX-P0-028` - GA per-table isolation cannot provide the claimed immediate runtime-trust fence | High | Blocks P0; `CHANGES_REQUIRED` |
| 2 | `DBX-P0-029` - unrestricted `BIGINT` JSON numbers make authoritative IDs non-interoperable | Medium | Blocks P0; `CHANGES_REQUIRED` |

### DBX-P0-028: GA per-table isolation cannot provide the claimed immediate runtime-trust fence

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: `runtime_trust_status_v`, P2 accepted/stale stamping, P6 prepare/approve/run, `action_ledger`, observed-Job start, refresh, invalidation, upgrade, rollback, stop, recovery, P7 operations, and P8 race fixtures.
- Evidence:
  1. The baseline correctly keeps `runtime_trust_ledger` customer-security-owned and denies every runtime principal control-ledger writes. The P6 App can write only `pending_identity_requests` and `action_ledger` and can run selected Jobs.
  2. The P6 gate is one conditional DML statement whose source is `runtime_trust_status_v` and whose write target is an action table. These are different managed Delta tables.
  3. The plan says that any new generation or invalidation prevents DML, that a newer registration locks P6 immediately, and that upgrade/rollback first registers a generation to lock actions.
  4. Under the selected GA default, the action-table statement reads a snapshot of the trust source and atomically commits only its action-table target. A concurrent trust committer can append `MANIFEST_REGISTERED` or `SNAPSHOT_INVALIDATED` after the P6 source snapshot was read without writing the P6 target. There is no same-table write conflict that forces P6 to re-read the new trust generation.
  5. A concrete permitted ordering is: P6 reads accepted generation N; the verifier commits generation N+1 or an invalidation; P6 commits its action row from the older source snapshot. The statement has satisfied its written predicate even though the product now claims the action is locked.
  6. Starting the approved observed Job through the platform occurs after action DML and is not part of any Delta transaction. Even if action admission is assigned a SQL linearization point, a trust change, App stop, response loss, or process failure can occur between the action commit and Jobs start.
  7. The same source/target race can let a bounded collector commit an `ACCEPTED` or `STALE`-stamped evidence row after the summary it read has been superseded. That is less dangerous than P6, but its exact point-in-time meaning also needs to be stated.
- User/system impact:
  - A production controlled action can be admitted or started after the UI/operator believes a new generation or invalidation has locked actions.
  - Upgrade, rollback, refresh, and emergency invalidation can proceed while a previously admitted action is still between ledger commit and native Job start.
  - Audit order can overstate causality: the trust ledger shows a lock before an action-table commit or Job start that was actually authorized from an older read snapshot.
- Required acceptance condition:
  1. Freeze the authorization linearization point and the promise it provides. If the intended contract is point-in-time admission, state explicitly that an action which read an accepted snapshot before the lock may commit or start afterward; replace every “immediate lock” claim with the exact boundary, and identify that admitted/in-flight action in status and audit output.
  2. If the product requires the current strict lock, define a GA-only fence/quiescence protocol that covers both action DML and the later Jobs start. Before registration, invalidation, refresh, upgrade, rollback, stop, or uninstall assumes actions are locked, close new ingress, reconcile every action operation and native Job-start request, drain or explicitly resolve in-flight work, and prove the bounded executor is quiescent. Define the safe recovery action for response loss and a run that cannot be cancelled.
  3. Do not treat a second status read immediately before Jobs start as sufficient by itself: another trust change can occur after that read. Pair any recheck with the accepted linearization semantics or the reviewed fence/quiescence mechanism.
  4. Do not silently repair this with catalog-commit multi-table transactions. They are Public Preview for managed Delta and still cannot atomically include a Jobs API call. Any future use requires an explicit feature-status, compute/table-eligibility, security, rollback, cost, and customer-policy decision.
  5. Define collector stamping under the same concurrency model: name the snapshot and evaluation point represented by a row and never imply that a later commit means trust was still current at commit time.
  6. Add deterministic barrier tests for a new registration and invalidation: before the status-view snapshot, after the view snapshot but before action-table commit, after action commit but before Jobs request, during lost Jobs response, during App stop, and after executor crash. Assert the documented action row, native run, cancellation/reconciliation, status, and audit outcome for each ordering.
  7. Propagate the chosen semantics through the ADR, `AGENTS.md`, product/review/documentation plans, source register, P2, P6, P7, P8, and P10 acceptance gates.

### DBX-P0-029: unrestricted `BIGINT` JSON numbers make authoritative IDs non-interoperable

- Verdict: `CHANGES_REQUIRED`
- Severity: medium
- Affected contract: event ID, candidate/acceptance/payload/snapshot/server-record/row IDs, exact retry/conflict handling, DDL validation, view validation, Python/SQL/JavaScript implementations, golden vectors, retained-ledger upgrades, and P1/P3/P8/P10.
- Evidence:
  1. The DDL declares `generation`, `prior_generation`, and `direct_state_serial` as `BIGINT`. The canonical contract says “SQL integers are JSON integers.”
  2. The baseline constrains `generation >= 1` and says “both counts” are non-negative, but it supplies no JCS safe-integer upper bound for the `BIGINT` fields and does not unambiguously close every count/serial field's sign and range.
  3. `generation` participates in `event-id.v1`; `direct_state_serial` participates in `stable-graph.v1`; and later canonical objects transitively depend on those digests. These are authorization identities, not display-only values.
  4. A Databricks `BIGINT` can hold values through `9223372036854775807`. RFC 8785 canonicalization follows ECMAScript/IEEE 754 number serialization, for which exact integer interchange is not assured above `9007199254740991`.
  5. For example, `9007199254740992` is representable but `9007199254740993` rounds to the same binary64 value. A Python integer serializer or SQL string construction that preserves the latter decimal digits can disagree with a conforming JavaScript/JCS implementation that rounds before serialization.
- User/system impact:
  - Two implementations can compute different `event_id`, `payload_digest`, or `snapshot_id` for the same SQL row.
  - A valid retry can be rejected as a conflict, or two distinct integer inputs can collapse to one canonical number in one implementation but not another.
  - A later implementation language or retained-ledger migration can make previously accepted trust unreadable or derive a different current state.
- Required acceptance condition:
  1. Choose one versioned representation for every numeric property in every canonical object. Either constrain the SQL/writer/view domain to exact interoperable integers no greater than `9007199254740991` in magnitude, or encode potentially 64-bit values as canonical decimal JSON strings.
  2. If strings are selected, freeze sign, zero, leading-zero, whitespace, and minimum/maximum lexical rules and state whether the SQL column remains numeric. If numbers are selected, enforce the bound before hashing and again in the status view so an owner-inserted out-of-domain row cannot authorize.
  3. Enumerate the sign/range rule for `generation`, `prior_generation`, `direct_state_serial`, `expected_component_count`, `new_deployment_count`, both pending-deployment counts, and every future numeric canonical property. Replace the ambiguous “both counts” wording.
  4. Add common Python, generated-SQL, and JavaScript/reference-JCS golden vectors for `0`, `1`, `9007199254740991`, `9007199254740992`, `9007199254740993`, and `9223372036854775807`, plus rejected negative, leading-zero, fractional, exponent, null, and overflow inputs according to the chosen domain.
  5. State the retained-ledger/version-migration rule if the representation changes in a later contract version; never reinterpret an old canonical integer under new encoding rules.
  6. Add the RFC 8785/I-JSON numeric limit to the source register and the Databricks/dbt implementation review gates.

## Focused disposition of eleventh-review findings

### DBX-P0-025

`RESOLVED_FOR_P0`

Baseline 0.13 now has phase-specific DDL fields, per-event nullability, canonical `machine-observation.v1`, a lifecycle-free stable graph, exact `STOPPED` to `ACTIVE` rules, both active/pending observations, both phase times/digests in the accepted identity, reference-view reduction, and negative fixtures. No phase overwrite or ambiguity remains in the frozen planning contract.

### DBX-P0-026

`RESOLVED_FOR_P0`

Reuse now references only the original self-anchor, never an intermediate candidate. The immediately prior accepted row must reference that original. The original belongs to exactly one complete accepted, uninvalidated, conflict-free source chain, and the current view dynamically revalidates it. Original time bounds expiry; later invalidation, deletion, conflict, or tamper makes dependent trust unverified.

### DBX-P0-027

`PARTIALLY_RESOLVED; NUMERIC_INTEROPERABILITY_RESIDUAL_SUPERSEDED_BY_DBX-P0-029`

The exhaustive DDL and four-event matrix, closed enums, literal canonical object properties, explicit exclusions, non-circular dependency graph, query-start timestamp name/meaning, exact status output/reduction, and P6 row/component cardinality predicate are now frozen. The remaining canonicalization defect is narrow: unrestricted SQL `BIGINT` values are still mapped to JSON numbers outside the RFC 8785/I-JSON exact-interchange range. Finding 029 owns that residual.

## Prior-finding disposition

| Finding | Twelfth re-review disposition |
|---|---|
| `DBX-P0-001` through `DBX-P0-008` | `RESOLVED_FOR_P0`; no regression found in identity separation, bounded reconciliation, App/action authorization roles, prerequisites, egress, optional enrichment, App permission/resource separation, or P6 identity/DML boundaries. |
| `DBX-P0-009` through `DBX-P0-019` | `RESOLVED_FOR_P0`; no regression found in saved-plan validation, deployment/data-plane separation, recoverable fixed DML, targeted grants, migration identity, pending/composite truth, warehouse/Query History recovery, exact runtime DML, whole-group roots, or direct-versus-effective warehouse authority. |
| `DBX-P0-020` | `RESOLVED_FOR_CORE_ORDERING`; stage, reconcile/stop, fresh final plan, pre-start candidate, direct start, post-start observation, and acceptance remain correctly ordered. Finding 028 concerns concurrent action admission, not this deployment sequence. |
| `DBX-P0-021` | `RESOLVED_IN_SUBSTANCE; AUTHORIZATION_FENCE_OPEN`; durable carrier, access, expiry, restart, retention, refresh, and uninstall remain present. Exact P6/in-flight semantics are blocked by 028. |
| `DBX-P0-022` | `RESOLVED_FOR_P0`; final planning remains sequential and fresh after stage reconciliation/stop. |
| `DBX-P0-023` | `RESOLVED_FOR_P0`; complete deployment-set pagination and reconciliation remain explicit. |
| `DBX-P0-024` | `RESOLVED_FOR_P0`; row/component cardinality, signature non-authority, latest-generation reduction, and the literal P6 summary/component predicate are frozen. The new 028 issue is transaction concurrency around that predicate, not a recurrence of 024. |
| `DBX-P0-025` | `RESOLVED_FOR_P0`; distinct pre/post observations and the one stable-graph lifecycle transition are exact. |
| `DBX-P0-026` | `RESOLVED_FOR_P0`; original-anchor eligibility, non-extension, and dynamic source-chain revalidation are exact. |
| `DBX-P0-027` | `PARTIALLY_RESOLVED`; DDL/matrix/dependency/time/view work passes; numeric interoperability is superseded by 029. |
| `DBX-P0-F01` | `RESOLVED_FOR_P0`; current DML, inheritance, ownership/`MANAGE`, visibility, pagination, and whole-group roots remain explicit. |
| `DBX-P0-F02` | `RESOLVED_FOR_P0`; optional enrichment remains separate, pair-scoped, disabled by default, and removable. |

## Author-file outcome

| Author file or set | Outcome | Databricks conclusion |
|---|---|---|
| `README.md` | `CHANGES_REQUIRED` | Architecture and evidence summary remain sound, but the claim of canonical whole-generation authority needs the numeric domain correction. |
| `AGENTS.md` | `CHANGES_REQUIRED` | Its same-statement P6 invariant overstates a cross-table GA fence, and its RFC 8785 rule lacks exact integer bounds/encoding. |
| `docs/index.md` | `PASS` | The index introduces no independent platform/security contradiction. |
| `docs/decisions/0001-private-app-bundle.md` | `CHANGES_REQUIRED` | Preserve the architecture and lifecycle. Freeze point-in-time versus strict action-lock semantics and canonical integer representation. |
| `docs/plans/product-plan.md` | `CHANGES_REQUIRED` | Primary location of 028 and 029: immediate-lock/new-generation claims exceed the cross-table transaction, and unrestricted `BIGINT` values feed authoritative JCS identities. |
| `docs/plans/review-process.md` | `CHANGES_REQUIRED` | Add cross-table barrier/Jobs-start race review and RFC 8785 integer-domain interoperability to the P2/P3/P6/P8 gates. |
| `docs/plans/documentation-plan.md` | `CHANGES_REQUIRED` | Teach the chosen action linearization/in-flight behavior and show admitted/running/reconciled outcomes during refresh, invalidation, upgrade, and stop. Add canonical numeric compatibility to reference/capture review. |
| `docs/research/source-register.md` | `CHANGES_REQUIRED` | Add per-table snapshot-isolation/multi-table Public Preview scope and the RFC 8785/I-JSON safe-integer/string rule; the current ACID and RFC rows do not cover either residual. |

## P0-P10 Databricks coverage matrix

These are planning outcomes; they do not claim implementation or live evidence exists.

| Part | Planning outcome | Databricks conclusion and required next evidence |
|---|---|---|
| P0 - Product contract | `CHANGES_REQUIRED` | Resolve 028-029 and re-review a new immutable author set. The private App plus Direct Bundle remains the recommended architecture. |
| P1 - Capture library | `CHANGES_REQUIRED` | Freeze the exact numeric JSON domain and cross-language vectors before implementing canonical IDs or validators. |
| P2 - Collector and reconciliation | `CHANGES_REQUIRED` | Define what trust snapshot/evaluation point an evidence-row stamp represents when the trust ledger changes concurrently with a different target-table write. |
| P3 - Bundle installer | `CHANGES_REQUIRED` | Deployment sequencing, DDL shape, phases, roster source, and view reduction now pass. Add integer enforcement and the lifecycle-wide action quiescence/fence required by the chosen P6 semantics. |
| P4 - Read-only App MVP | `CHANGES_REQUIRED` | Read-only bindings and fail-closed view use remain sound, but displayed snapshot identity must use the corrected canonical contract and must not imply commit-current truth. |
| P5 - Existing-job onboarding | `PASS` | Scanner, proposed patch, owner approval, and rollback classification are not changed by these findings. |
| P6 - Controlled actions | `CHANGES_REQUIRED` | The row/cardinality predicate is exact, but cross-table snapshot isolation and the later Jobs call do not provide the claimed immediate lock. Freeze admission/in-flight semantics or a GA fence and barrier-test it. |
| P7 - Security and operations | `CHANGES_REQUIRED` | Document in-flight action visibility, drain/cancel/reconcile behavior, response loss, emergency invalidation limits, and retained canonical-ID compatibility. |
| P8 - Bounded live proof | `CHANGES_REQUIRED` | Add controlled barriers around view read, action commit, trust commit, Jobs request/response, stop, and crash; add safe-integer/overflow vectors across Python, SQL, and JavaScript. |
| P9 - Optional intelligence | `PASS` | Genie/AI remains optional and outside capture, deployment, data seal, authorization, and runtime-trust authority. No Preview AI feature is required. |
| P10 - Private alpha | `CHANGES_REQUIRED` | Do not accept a non-author install until the concurrency matrix matches documented action outcomes and independent implementations derive identical IDs at every accepted numeric boundary. |

## Explicit verdict

`CHANGES_REQUIRED`

Baseline 0.13 retains the recommended Azure Databricks architecture and makes a substantial, credible repair to the runtime-trust ledger. `DBX-P0-025` and `DBX-P0-026` are resolved. The exhaustive schema, event matrix, phase/lifecycle model, deployment-difference rules, original-source validation, query-start timing, status view, and literal digest dependency graph requested by `DBX-P0-027` now pass. No new required Preview identity, telemetry, or external service dependency was found.

Two bounded corrections remain. First, define an honest GA authorization boundary for cross-table P6 admission and the later Jobs start; either accept and disclose point-in-time/in-flight behavior or freeze a lifecycle-wide GA quiescence/fence protocol, then test every concurrent ordering. Second, constrain every canonical JSON number to the RFC 8785/I-JSON exact range or encode 64-bit values as versioned canonical decimal strings with shared boundary vectors. Propagate both decisions through the ADR, working agreement, product/review/documentation plans, source register, and P0-P10 gates, then request another independent Databricks platform/security review.
