# v0.3.0 release acceptance ledger

- Status: `PASS` — local and live Azure release gates complete
- Review model: [Continuous domain ownership](../../plans/review-process.md)
- Final contract: [v0.3.0 supported-release contract](../../releases/v0.3.0-support-contract.md)
- Contract-freeze evidence: [evidence packet](contract-freeze-evidence.md)
- Final live evidence: [2026-07-17 Azure acceptance](../../evidence/v0.3.0-live-acceptance-2026-07-17.md)
- Marketplace: Excluded

This is the single current ledger. It consolidates overlapping Databricks, dbt Core, and usability observations into product outcomes. A symptom is not tracked again under each perspective.

## Current outcomes

| ID | Outcome | Current owner | Domain checks | Contract freeze | Local release candidate | Live Azure proof |
|---|---|---|---|---|---|---|
| `CF-001` | Installation authority and customer state | Databricks | `DBX-02`, `DBX-03`, `DBX-04`, `DBX-05`, `DBX-08`; `UX-01` | Name the sole combined-role launcher, exact human/identity and schema-owner requirements, bootstrap/dbt/App compute topology, complete object/grant graph, retained authority, idempotency boundary, native-registry status, independence limitation, and regulated-use claim. | Launcher rejects every unsupported mode before calls or mutation; exact object/grant render and mandatory App bindings agree; fresh/rerun/partial/drift cases are deterministic. | Actor, schema owner, warehouses, objects, grants, and App bindings match the contract; capability probes stay inside the privilege graph; prior resource state is restored. |
| `CF-002` | Normative dbt runtime and non-demo onboarding | dbt Core | `DBT-01`, `DBT-02`, `DBT-03`, `DBT-04`, `DBT-07`, `DBT-09`; `UX-04` | Bind the full runtime, schemas, command, AttemptKey paths, output/custody, and drift rules to one machine-readable support manifest. Freeze workspace-project, profile/target, selector, source closure, packages/lock, patch, and re-onboarding policy. | Manifest, generator, parser, and resolved environment agree; a non-demo fixture produces a byte-stable patch/policy; unsupported mutations fail before execution. | Released tuple and nested archive members match the policy; one real project is onboarded without entered SQL, IDs, flags, paths, `vars`, or environment overrides. |
| `CF-003` | Lifecycle, safe defaults, and cost completion | Usability | `UX-02`, `UX-03`, `UX-06`, `UX-07`; `DBX-05`, `DBX-06`, `DBX-09` | Freeze install, resume, stop, retain-uninstall, and delete-uninstall outcomes: approval, state changes, data/grants, compute, safe default, irreversible consequences, receipt, and one indeterminate next action. Resolve the successful-install App state. | Table-driven tests cover every lifecycle row and injected interruption; an ambiguous mutation is reconciled rather than resent; destructive deletion requires separate approval. | Rehearse both uninstall modes; no operation reports success before statements/runs are terminal and App, schedule, and warehouses match their promised post-state; unrelated prior-running resources are preserved. |
| `CF-004` | First useful evidence and qualification matrix | dbt Core | `DBT-05`, `DBT-06`, `DBT-08`; `UX-03`, `UX-05`, `UX-06` | Freeze separate dbt, pair/capture, node, collection, trust, and next-action results. Freeze cost-before-query and explicit Load behavior. Separate local golden cases from the live release proof. | Fixtures cover success, dbt failure, early/partial evidence, retry/repair, missed collection, replay, reconciliation, trust hold, and empty state; no evidence query occurs before Load. | One immutable RC proves two deterministic complete runs, one selected failure or partial case, missed collection plus reconciliation, distinct histories, queryable rows, and matching App results. |

## Domain decisions

| Domain | Contract-freeze state | Current decision scope |
|---|---|---|
| Databricks platform | `PASS` | Installation, identity, App bindings, Jobs, lifecycle, and zero-compute inventory match the final contract |
| dbt Core | `PASS` | Runtime, artifact pair, failure, reconciliation, and real-project onboarding outcomes match the final contract |
| Usability | `PASS` | Install, start, stop, retain, delete, first-value, cost notice, and zero-guess selection journeys passed |

`DBX-01` remains `PASS`; this contract review did not change the already reviewed native Statement Execution submission interface. v0.3.0 now explicitly excludes that foundation registry from its launcher.

### Closed root finding

| Finding | Fact owner | Boundary order | Resolution evidence |
|---|---|---|---|
| `CF-002-PROFILE-HOST` | Databricks | Databricks -> dbt Core -> usability | `PASS` in all three domains at contract-set `c19ade791e9dcd8a204f5e17a1c3b95e0781910e0fb91721f7e9902e5364ddf8`: installer-rendered canonical workspace hostname, injected token only, valid exact dbt profile, and zero operator connection fields. |

The earlier Databricks and usability observations were two effects of this one
root cause, not separate blockers. The Databricks owner froze the supported
platform mechanism, dbt Core validated the resulting profile, and usability
validated the final operator journey. No other contract criterion was reopened.

## Deferred product scope

- Marketplace, separated duties, compliance certification, automatic legal retention, upgrade, and rollback remain explicitly outside v0.3.0.
- A future artifact or contract change must pass the same local and live gates again.

## Closure rule

All four outcomes are closed for the final manifest digest. A future change reopens only the affected outcome and any crossed boundary.
