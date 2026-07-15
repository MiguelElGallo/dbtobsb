# Databricks platform/security thirteenth re-review: P0 planning baseline

- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform/security reviewer
- Immutable author input SHA-256: `3402e6cb5c96844be04a4d259fb8ca00d6fd60903e0f801fe2559c048334507a`
- Baseline: 0.14
- Verdict: `CHANGES_REQUIRED`
- Cloud mutation: none

## Immutable input verification

I read all eight frozen author files: `README.md`, `AGENTS.md`, `docs/index.md`, `docs/decisions/0001-private-app-bundle.md`, `docs/plans/documentation-plan.md`, `docs/plans/product-plan.md`, `docs/plans/review-process.md`, and `docs/research/source-register.md`.

I recomputed the author digest with the requested global path ordering and per-file SHA-256 records:

```sh
{
  printf '%s\n' README.md AGENTS.md docs/index.md
  find docs/decisions docs/plans docs/research -type f -name '*.md'
} | LC_ALL=C sort | while IFS= read -r file; do
  shasum -a 256 "$file"
done | shasum -a 256
```

The result was exactly:

```text
3402e6cb5c96844be04a4d259fb8ca00d6fd60903e0f801fe2559c048334507a
```

The hash still matched immediately before this report was written. No author file or earlier review was changed. This report is the only file written. I made no Azure, Databricks, authentication, account-console, SQL, warehouse, App, Job, or Unity Catalog call.

## Executive assessment

Baseline 0.14 resolves both blockers from the twelfth Databricks re-review and preserves the recommended product architecture:

- `DBX-P0-028` is resolved in substance. Optional P6 now uses one unpartitioned `Serializable` Delta fence row. Claim, drain, phase, takeover, release, reopen, and retirement all conditionally write that same row. The claim commit is the admission linearization point; the drain commit prevents later dbtobsb admissions; an earlier admission remains visible and must be reconciled to terminal/no-request before the matching drain can become `CLOSED`. Trust and lifecycle mutation are prohibited before that closed state. The contract does not require Preview multi-table transactions and does not call Delta plus Jobs atomic. It explicitly excludes schedules, direct callers, and compromised App/administrator roots from the fence promise.
- Collector provenance is now honest. Its tuple records the status-view snapshot and query-evaluation time observed by the first AttemptKey-root write, not trust at the evidence-table commit. Later trust change does not rewrite the dbt evidence, AttemptKey, capture classification, or native outcome.
- `DBX-P0-029` is resolved. SQL integer columns remain numeric, while every non-null integral property in canonical JSON is a range-checked unsigned decimal string. The contract closes lexical form, field ranges, cross-language vectors, owner-inserted out-of-domain behavior, and retained-version migration.
- `DBX-P0-025`, `DBX-P0-026`, and the remaining `DBX-P0-027` schema/canonical/time/view requirements remain resolved. No regression was found in phase-specific machine evidence, original roster self-anchor/source-chain validation, latest-generation reduction, query-start timestamps, component cardinality, or signature non-authority.

The P6 concept is therefore now a credible GA per-table concurrency design. P0 cannot yet be accepted because the newly frozen exact platform contract contains two executable/recovery defects:

1. The normative fence `CREATE TABLE` statement puts eleven `CHECK` constraints inside `CREATE TABLE`. Current Azure Databricks SQL does not support defining a Delta `CHECK` constraint there; it requires `ALTER TABLE ... ADD CONSTRAINT` after creation. The exact DDL and the claimed tests cannot run as written.
2. The terminal-run contract recognizes only `TERMINATED` and `SKIPPED`. The first-party Jobs model also defines `INTERNAL_ERROR` as a terminal lifecycle state. The current text would leave a safely failed run, its fence, maintenance, and uninstall permanently unresolved even though Get Run returned documented terminal evidence.

Both are bounded corrections. They do not change the private App plus Direct Bundle decision or weaken the same-row fence. They must nevertheless be fixed before P3/P6 implementation because this baseline deliberately calls the fence DDL and state machine exact and normative.

## Current primary evidence checked

### Same-table isolation and transaction boundary

- [Azure Databricks isolation levels](https://learn.microsoft.com/en-us/azure/databricks/optimizations/isolation/isolation-levels) states that `Serializable` is the strongest table isolation, orders committed reads/writes for a given table, keeps ordinary reads snapshot-based, and rejects a concurrent write whose read cannot fit the table history. It also notes that a conditional write which reads its target has `MERGE`-like concurrency behavior. This supports the same-row claim/drain CAS, not an atomic trust-table-plus-fence-plus-Jobs transaction.
- [Azure Databricks ACID guarantees](https://learn.microsoft.com/en-us/azure/databricks/lakehouse/acid) describes per-table transactional commits and optimistic conflict handling. [The multi-table transaction tutorial](https://learn.microsoft.com/en-us/azure/databricks/transactions/tutorial) marks managed-Delta multi-table writes as Public Preview. Baseline 0.14 correctly excludes that feature.

### Executable Delta constraint syntax

- [Azure Databricks `CREATE TABLE [USING]`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-syntax-ddl-create-table-using) limits `table_constraint` in `CREATE TABLE` to informational key constraints and says twice that a Delta `CHECK` constraint must be added with `ALTER TABLE`.
- [The `CONSTRAINT` clause](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-syntax-ddl-create-table-constraint) likewise says that `CREATE TABLE` supports informational primary/foreign/unique constraints and that a Delta `CHECK` constraint is added only after table creation.
- [`ALTER TABLE ... ADD CONSTRAINT`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-syntax-ddl-alter-table-add-constraint) documents an enforced Delta `CHECK`, verifies existing data, requires a deterministic Boolean expression, and requires `UTF8_BINARY` default collation when the check uses strings.

### Jobs idempotency, cancellation, and terminal states

- [Azure Databricks Jobs CLI commands](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/reference/jobs-commands) documents the Run Now idempotency token, asynchronous cancellation, and polling to terminal state.
- The current first-party generated Jobs model says that a duplicate Run Now token returns the existing run, a deleted matching run returns an error, retries with the same token launch exactly one run, and the token is at most 64 characters: [`RunNow.IdempotencyToken`](https://github.com/databricks/databricks-sdk-go/blob/bad015296869703de251d189b8a43ea4e6df8bfb/service/jobs/model.go#L4280-L4294). Baseline 0.14's 64-hex deterministic token and held deleted-run outcome match that contract.
- The same first-party model defines `TERMINATED`, `SKIPPED`, and `INTERNAL_ERROR` as terminal legacy lifecycle states: [`RunLifeCycleState`](https://github.com/databricks/databricks-sdk-go/blob/bad015296869703de251d189b8a43ea4e6df8bfb/service/jobs/model.go#L4129-L4177). The generated waiter returns success for `TERMINATED`/`SKIPPED` but halts with an error for terminal `INTERNAL_ERROR`: [`WaitGetRunJobTerminatedOrSkipped`](https://github.com/databricks/databricks-sdk-go/blob/bad015296869703de251d189b8a43ea4e6df8bfb/service/jobs/api.go#L269-L298). Product code must classify that error as a documented terminal failure, not as an indefinitely nonterminal or unknown run.

### Canonical integer interoperability and server time

- [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785) and [RFC 7493 section 2.2](https://www.rfc-editor.org/rfc/rfc7493#section-2.2) support the selected decimal-string representation for exact values above the binary64 interoperable integer range.
- [`current_timestamp`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/functions/current_timestamp) remains a query-evaluation-start timestamp. Baseline 0.14 preserves that meaning and never relabels it as commit time.

## Ranked findings

| Rank | Finding | Severity | P0 effect |
|---:|---|---|---|
| 1 | `DBX-P0-030` - the normative fence DDL uses unsupported inline `CHECK` syntax | High | Blocks P0; `CHANGES_REQUIRED` |
| 2 | `DBX-P0-031` - the Jobs terminal-state contract omits terminal `INTERNAL_ERROR` | Medium | Blocks P0's exact P6/recovery contract; `CHANGES_REQUIRED` |

### DBX-P0-030: the normative fence DDL uses unsupported inline `CHECK` syntax

- Verdict: `CHANGES_REQUIRED`
- Severity: high
- Affected contract: P6 data envelope, exact fence DDL, constraint/nullability verification, initial singleton creation, recovery after partial DDL, P3/P6/P8 executable fixtures, source register, review gates, and fence reference documentation.
- Evidence:
  1. `docs/plans/product-plan.md` calls the displayed `CREATE TABLE runtime_authorization_fence (...)` normative and puts `fence_key`, `fence_contract`, all range checks, the state check, the phase check, and the drain-reason check inside its table specification.
  2. The plan says the attended data envelope creates this exact table and that local/staging tests execute the exact DDL.
  3. Current Azure Databricks `CREATE TABLE [USING]` does not admit `CHECK` as a `table_constraint`. Its table and column constraint clauses are informational keys, and the official page explicitly directs users to `ALTER TABLE` for `CHECK`.
  4. Current `ADD CONSTRAINT` supports and enforces the intended Delta checks, but it is a separate mutation. It validates existing data and requires `UTF8_BINARY` default collation for string expressions.
  5. The current single statement therefore cannot be treated as executable evidence. A parser failure occurs before the singleton or fence protocol exists; silently dropping the checks would also contradict the normative DDL and test gates.
- User/system impact:
  - P6 installation fails during the approved data envelope after the user has accepted mutations and bounded warehouse cost.
  - If implementation omits the unsupported clauses to make creation succeed, the installed table no longer matches the approved contract and malformed state/range values lose platform enforcement.
  - Recovery cannot deterministically distinguish table-created, property-set, constraints-added, and singleton-initialized states because the current plan models them as one creation operation.
- Required acceptance condition:
  1. Replace the normative statement with an executable ordered envelope: create the managed Delta table without inline checks; set and verify `Serializable`; establish or verify `UTF8_BINARY` default collation; add each named `CHECK` through one marked `ALTER TABLE ... ADD CONSTRAINT`; verify every constraint and table property; then initialize and read back exactly one `CLOSED`/`INSTALL` row.
  2. Keep the project's one-operation-per-Statement-Execution-request rule. Give every create/property/constraint/initial-row step its own operation ID, semantic pre/post-state, Query History marker, idempotent resume rule, and drift classification.
  3. Define exact recovery for each partial state: missing table, exact empty table, missing subset of exact constraints, conflicting same-name constraint, non-empty table before constraints, wrong collation/property, and exact already-initialized singleton. Never accept an unknown or weaker constraint definition by name alone.
  4. Preserve the same DDL columns, checks, unpartitioned layout, owner/grants, and `Serializable` semantics unless a separately reviewed contract change explains the difference.
  5. Add generated-SQL/static parser fixtures and one bounded Databricks SQL staging execution that prove the frozen sequence runs on the supported Current-channel installer warehouse, survives process death after every statement, and leaves exactly the intended table/property/constraints/row/grants with no active statement or temporary authority.
  6. Propagate the sequence and recovery states through `AGENTS.md`, the ADR consequences where relevant, product/review/documentation plans, source register, P3/P6/P7/P8 gates, and the future fence reference/how-to pages.

### DBX-P0-031: the Jobs terminal-state contract omits terminal `INTERNAL_ERROR`

- Verdict: `CHANGES_REQUIRED`
- Severity: medium
- Affected contract: P6 action phase, cancel-or-wait policy, Get Run reconciliation, terminal action ledger, `DRAINING` to `CLOSED`, maintenance/uninstall availability, cost wording, P6/P7/P8/P10 tests, and operator documentation.
- Evidence:
  1. `docs/plans/product-plan.md` states that `ACTION_CLAIMED` remains occupied until Get Run proves only `TERMINATED` or `SKIPPED`, or the product proves a no-request/rejected outcome.
  2. Current first-party Jobs types explicitly define legacy `INTERNAL_ERROR` as terminal. It represents a Jobs-service exceptional failure and is not the same as an unknown response, deleted run, prolonged outage, `BLOCKED`, or `WAITING_FOR_RETRY`.
  3. The generated Databricks waiter treats `INTERNAL_ERROR` as a halting error rather than one of its two success target states. A caller that merely maps waiter error to `ACTION_DISPATCH_INDETERMINATE` will therefore miss the returned documented terminal classification.
  4. Baseline 0.14 correctly keeps a deleted token-associated run or unavailable Get Run indeterminate, but it gives no exact path from a visible `INTERNAL_ERROR` to terminal action-ledger evidence and fence closure.
- User/system impact:
  - A native run that has definitively failed terminally can leave controlled actions, refresh, upgrade, stop, rollback, and uninstall locked forever.
  - The UI can mislabel a known terminal platform failure as an unknown action outcome and continue warning that a run may execute when the platform has already classified it terminal.
  - Operators may be tempted to bypass the no-force-open rule because the documented recovery path has no legal completion.
- Required acceptance condition:
  1. Freeze the exact Get Run compatibility projection. Prefer the current `status.state`/termination-details representation when present; define the permitted legacy fallback; fail closed if both representations conflict or an unknown value appears.
  2. Classify every documented terminal lifecycle outcome. For the legacy projection this includes `TERMINATED`, `SKIPPED`, and `INTERNAL_ERROR`. Preserve success/failure/cancel/skipped/internal-error result semantics separately from the fact that the lifecycle is terminal.
  3. For `INTERNAL_ERROR`, write and verify an explicit terminal-failure action-ledger milestone. If current compute/run inventory is still needed to prove no execution or cost remains, require that additional observation before `DRAINING` becomes `CLOSED`; do not call the run nonterminal merely because a convenience waiter returned an error.
  4. Keep deleted-run, denied, malformed, contradictory, and unavailable states held and escalated. Unknown future lifecycle values must fail closed rather than being inferred terminal.
  5. Add fake-API and bounded staging cases for `INTERNAL_ERROR` before and after cancel, current-versus-legacy fields, conflicting fields, unknown fields, task/run pagination where used, deleted run, and a final inventory. Assert one terminal ledger outcome, no duplicate Run Now, truthful cost state, and deterministic close/no-close behavior.
  6. Propagate the terminal table through the source register, product/review/documentation plans, P6/P7/P8/P10 gates, operation codes, UI labels, and action recovery documentation.

## Focused disposition of prior findings 025-029

### DBX-P0-025

`RESOLVED_FOR_P0`

The physical ledger, matrix, canonical objects, view, tests, App lifecycle, and documentation retain separate pre-start `STOPPED` and post-start `ACTIVE` observations. Only the lifecycle-free stable graph remains equal, and missing/reversed/swapped/overwritten phases fail closed.

### DBX-P0-026

`RESOLVED_FOR_P0`

Roster reuse targets only the original self-anchored candidate behind one complete accepted, uninvalidated, conflict-free source chain. The latest view revalidates that source on every read, later source invalidation/tamper invalidates dependents, and reuse never advances the original roster clock.

### DBX-P0-027

`RESOLVED_FOR_P0`

The ledger has exhaustive DDL and a complete four-event required/null matrix, closed enums, literal canonical domains, an acyclic identifier dependency order, accurate query-start time naming, an exact status projection/reduction, and cardinality rules. The unsupported inline checks in finding 030 are new fence-table executable syntax, not a regression in the runtime-trust-ledger schema contract.

### DBX-P0-028

`RESOLVED_FOR_P0`

The same-row fence resolves the earlier cross-table authorization race for honest product writers:

- Claim and drain both read and conditionally write the exact singleton target row under `Serializable` isolation.
- If claim commits first, drain observes/reconciles that admitted action and trust/lifecycle waits for `CLOSED`.
- If drain commits first, a stale claimant cannot successfully commit the expected `OPEN` row/version; no later dbtobsb admission is authorized.
- The trust summary is a source snapshot, but the fence commit—not that read—is the admission point, and every trust/lifecycle writer must win the same-row drain before changing another table or App state.
- Run Now remains an external idempotent side effect. `DRAINING` explicitly permits an earlier request/run to appear and requires same-token reconciliation plus cancel-or-wait before closure.
- The contract claims neither multi-table atomicity nor protection from schedules, direct callers, App code/managers, the verifier, owners, or administrators.

Finding 030 concerns how the fence table and its checks are installed. Finding 031 concerns one documented terminal Jobs result. Neither reopens the same-row ordering model itself.

### DBX-P0-029

`RESOLVED_FOR_P0`

Every canonical SQL integer is now a quoted unsigned ASCII decimal with an exact field range. JSON numbers, signs, leading zero, whitespace, Unicode digits, fractions, exponent, null-for-required, and overflow are rejected. Boundary vectors span binary64 and signed-`BIGINT` limits across Python, generated SQL, and JavaScript/reference JCS, and later versions cannot reinterpret retained rows.

## Prior-finding disposition

| Finding | Thirteenth re-review disposition |
|---|---|
| `DBX-P0-001` through `DBX-P0-008` | `RESOLVED_FOR_P0`; no regression found in identity separation, bounded reconciliation, App/action authorization, prerequisites, egress, optional enrichment, App permission/resource separation, or P6 identity/DML boundaries. |
| `DBX-P0-009` through `DBX-P0-019` | `RESOLVED_FOR_P0`; no regression found in saved-plan validation, deployment/data-plane separation, recoverable fixed mutations, targeted grants, migration identity, pending/composite truth, warehouse/Query History recovery, exact runtime DML, whole-group roots, or direct-versus-effective warehouse authority. |
| `DBX-P0-020` | `RESOLVED_FOR_CORE_ORDERING`; stage/reconcile/stop/fresh-final-plan/candidate/start/accept remains correctly ordered. |
| `DBX-P0-021` | `RESOLVED_IN_SUBSTANCE`; durable trust carrier, restart, retention, refresh, and uninstall are present. Exact P6 install/recovery remains blocked only by 030-031. |
| `DBX-P0-022` | `RESOLVED_FOR_P0`; final planning remains sequential and fresh after stage reconciliation and stop. |
| `DBX-P0-023` | `RESOLVED_FOR_P0`; deployment inventories are fully paginated and reconciled without user-selected IDs. |
| `DBX-P0-024` | `RESOLVED_FOR_P0`; row/component cardinality, signature non-authority, latest-generation reduction, and exact summary/component admission predicate remain frozen. |
| `DBX-P0-025` | `RESOLVED_FOR_P0`; exact dual machine phases and stable projection remain present. |
| `DBX-P0-026` | `RESOLVED_FOR_P0`; original roster source-chain authority and non-extension remain present. |
| `DBX-P0-027` | `RESOLVED_FOR_P0`; exhaustive ledger schema/matrix/canonical/time/view contract remains present. |
| `DBX-P0-028` | `RESOLVED_FOR_P0`; the same-row Serializable claim/drain and closed-before-mutation protocol now matches the stated GA boundary. |
| `DBX-P0-029` | `RESOLVED_FOR_P0`; canonical integral values use exact decimal strings and cross-language boundary fixtures. |
| `DBX-P0-F01` | `RESOLVED_FOR_P0`; current DML, inheritance, ownership/`MANAGE`, visibility, pagination, and whole-group roots remain explicit. |
| `DBX-P0-F02` | `RESOLVED_FOR_P0`; optional enrichment remains separate, pair-scoped, disabled by default, and removable. |

## Author-file outcome

| Author file | Outcome | Databricks conclusion |
|---|---|---|
| `README.md` | `PASS` | The product boundary, observation-time collector label, same-row fence promise, external-caller/App-compromise boundary, and cost discipline are accurate at overview level. |
| `AGENTS.md` | `CHANGES_REQUIRED` | Core invariants are strong, but the instruction to implement the exact fence contract inherits invalid creation syntax and an incomplete terminal-run projection. |
| `docs/index.md` | `PASS` | The planning index introduces no platform contradiction. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | The architecture and fence boundary remain sound; the two findings are implementation-contract corrections, not an ADR reversal. |
| `docs/plans/product-plan.md` | `CHANGES_REQUIRED` | Primary location of unsupported inline `CHECK` clauses and the terminal set limited to `TERMINATED`/`SKIPPED`. |
| `docs/plans/review-process.md` | `CHANGES_REQUIRED` | Add executable create/property/add-constraint/recovery review and exact current/legacy terminal-state classification. |
| `docs/plans/documentation-plan.md` | `CHANGES_REQUIRED` | Fence reference/how-tos and D6 evidence must teach the actual multi-statement DDL recovery sequence and known-terminal-versus-indeterminate Jobs outcomes. |
| `docs/research/source-register.md` | `CHANGES_REQUIRED` | Add the official `CREATE TABLE`/`ADD CONSTRAINT` boundary, collation requirement, and first-party terminal-state model; keep the existing isolation/idempotency entries. |

## P0-P10 Databricks coverage matrix

These are planning outcomes; they do not claim implementation or live evidence exists.

| Part | Planning outcome | Databricks conclusion and required next evidence |
|---|---|---|
| P0 - Product contract | `CHANGES_REQUIRED` | Resolve 030-031 and freeze/re-review a new globally sorted author set. The private App plus Direct Bundle and same-row fence remain recommended. |
| P1 - Capture library | `PASS` | Capture schemas, artifacts, canonical trust integers, and local fixtures are sufficiently planned; fence DDL/run terminality do not alter dbt capture identity. |
| P2 - Collector and reconciliation | `PASS` | The exact three-table/no-DDL writer boundary and observation-time AttemptKey-root trust tuple correctly reflect per-table snapshot semantics. |
| P3 - Bundle installer | `CHANGES_REQUIRED` | Base staged/final Direct and attended migration design passes, but the P3 fence fixture/enable envelope must use executable create/add-constraint/property/initial-row operations with partial-state recovery. |
| P4 - Read-only App MVP | `PASS` | Stateless, curated-only, setup-only, trust-age, current-versus-observed, and optional-enrichment boundaries remain credible. |
| P5 - Existing-job onboarding | `PASS` | Scanner, patch review, unsupported/access/check distinctions, and customer-Job non-mutation are unaffected. |
| P6 - Controlled actions | `CHANGES_REQUIRED` | Same-row authorization ordering passes conceptually. Execute the actual constrained table sequence and close the full documented Jobs terminal set before implementation acceptance. |
| P7 - Security and operations | `CHANGES_REQUIRED` | Runbooks need partial constraint-install recovery and a legal no-force-open path from terminal `INTERNAL_ERROR` to final ledger/closed state. |
| P8 - Bounded live proof | `CHANGES_REQUIRED` | Add process-death tests around every table/property/constraint/initial-row operation and Jobs `INTERNAL_ERROR`/current-versus-legacy/unknown-state cases. |
| P9 - Optional intelligence | `PASS` | AI remains optional and outside capture, trust, fence, deployment, and authorization. |
| P10 - Private alpha | `CHANGES_REQUIRED` | A P6-enabled alpha cannot claim repeatable install/lifecycle until 030-031 pass; read-only base journeys remain properly scoped. |

## Explicit verdict

`CHANGES_REQUIRED`

Baseline 0.14 successfully repairs the two substantive platform/security defects from baseline 0.13. The collector now makes only an observation-time provenance claim, the P6 claim/drain fence has the correct same-row GA linearization and quiescence boundary, and canonical 64-bit integers are interoperable across SQL, Python, and JavaScript. No required Preview multi-table, identity, App-user-authorization, or external telemetry dependency was introduced.

Before P0 can pass, make the exact fence installation executable by separating Delta table creation from enforced `ALTER TABLE ... ADD CONSTRAINT` operations with collation/property/readback/recovery, and include documented terminal `INTERNAL_ERROR` in the Jobs reconciliation contract without confusing terminal failure with successful outcome or with unknown dispatch. Then request another independent Databricks platform/security re-review of the new frozen author hash.
