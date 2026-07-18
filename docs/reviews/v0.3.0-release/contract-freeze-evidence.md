# v0.3.0 contract-freeze evidence packet

> Historical contract-freeze snapshot. Implementation and live qualification later completed; use the [final acceptance ledger](acceptance-ledger.md) and [2026-07-18 stable Azure acceptance](../../evidence/v0.3.0-stable-acceptance-2026-07-18.md) for release status.

- Evidence state: Contract freeze passed
- Contract-set digest: `c19ade791e9dcd8a204f5e17a1c3b95e0781910e0fb91721f7e9902e5364ddf8`
- Machine-contract digest: `ed061a89e5012cf076e17af60d86a4728799639168e818107df2287a0979c640`
- Cloud mutation: None

## Review outcomes

Review only these four shared outcomes and their named rubric checks:

| Outcome | Checks | Frozen decision |
|---|---|---|
| `CF-001` installation authority and customer state | `DBX-02`, `DBX-03`, `DBX-04`, `DBX-05`, `DBX-08`, `UX-01` | One combined administrator and one temporary serverless Spark bootstrap Job; eight exact objects; thirteen exact product grants; no v0.3 runtime-trust ledger or native-registry execution |
| `CF-002` dbt runtime and onboarding | `DBT-01`, `DBT-02`, `DBT-03`, `DBT-04`, `DBT-07`, `DBT-09`, `UX-04` | Full pinned distribution/output/schema contract plus `dbtobsb.dbt-policy.v1` for one immutable `WORKSPACE` customer-project snapshot |
| `CF-003` lifecycle and cost | `UX-02`, `UX-03`, `UX-06`, `UX-07`, `DBX-05`, `DBX-06`, `DBX-09` | Six commands/actions with Stop as the safe default; install ends stopped; every success requires terminal inventory and prior-state restoration |
| `CF-004` first useful evidence | `DBT-05`, `DBT-06`, `DBT-08`, `UX-03`, `UX-05`, `UX-06` | No landing query; explicit Load; separate Lakeflow/retrieval/pair/dbt/node/collection outcomes; local fixtures separated from live Azure proof |

## Frozen files

The contract-set digest is the SHA-256 of the ordered per-file SHA-256 lines for:

1. `contracts/src/dbtobsb_contracts/support-manifest-v1.json`
2. `contracts/src/dbtobsb_contracts/support.py`
3. `contracts/tests/test_support.py`
4. `contracts/tests/test_release_contract.py`
5. `docs/releases/v0.3.0-support-contract.md`
6. `docs/plans/product-plan.md`
7. `docs/plans/documentation-plan.md`
8. `docs/decisions/0001-private-app-bundle.md`

The three long-form planning files are in scope only for their new v0.3.0 authority notices. Their later separated-duty, runtime-trust, controlled-action, enrichment, upgrade, and rollback design is explicitly not a v0.3.0 promise.

## Validation evidence

| Command | Result |
|---|---|
| `./scripts/check_contracts.sh` | PASS: 105 tests, fixed Bundle contract, Ruff, Ty, wheel build/install/import |
| `uv run --project installer pytest -q installer/tests/test_operation_registry.py` | PASS: 8 cross-language registry tests after support-digest propagation |
| `(cd native && go test -race ./bridge)` | PASS |
| `uv run --project contracts pytest -q contracts/tests/test_support.py contracts/tests/test_release_contract.py contracts/tests/test_commands.py` | PASS: 37 tests |

The strict manifest loader rejects extensions and weakened values, pins its canonical digest, deep-freezes nested data, and makes the manifest normative. The release-contract parity tests derive their assertions from that manifest.

## Primary-source checks

- Azure Databricks Jobs run as their creator by default, and a Bundle can set a run identity explicitly: [Lakeflow Jobs privileges](https://learn.microsoft.com/en-us/azure/databricks/jobs/privileges), [Bundle run identity](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/run-as).
- Serverless Jobs support Python-wheel and dbt tasks: [serverless Jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/run-serverless-jobs), [Python-wheel tasks](https://learn.microsoft.com/en-us/azure/databricks/jobs/tasks/python-wheel).
- App table bindings automatically add required parent usage plus selected table privilege, and removal attempts to revoke them: [Databricks App table resources](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/tables).
- A stopped App does not incur App-compute cost; a running App does: [Databricks Apps concepts](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts).
- dbt recommends committing `package-lock.yml` for repeatable `dbt deps`: [dbt deps](https://docs.getdbt.com/reference/commands/deps).
- A Databricks dbt Job injects `DBT_ACCESS_TOKEN` for its run-as principal. The current custom-profile example renders the Server Hostname and HTTP Path as literal values, and a custom `profiles_directory` is mutually exclusive with task `warehouse_id`: [Azure Databricks dbt task](https://learn.microsoft.com/en-us/azure/databricks/jobs/tasks/dbt), [custom-profile workflow](https://learn.microsoft.com/en-us/azure/databricks/jobs/how-to/use-dbt-in-workflows#advanced-run-dbt-with-a-custom-profile), [Bundle dbt task fields](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/bundles/job-task-types).
- dbt Core profiles name a profile, default target, and adapter-specific output; the Databricks adapter profile binds host, HTTP path, catalog, and schema: [dbt Databricks setup](https://docs.getdbt.com/docs/local/connect-data-platform/databricks-setup).

## Known implementation gaps assigned to later gates

These do not create additional contract-freeze findings unless they contradict the frozen promise:

- No production `dbtobsb bootstrap/start/stop/uninstall` orchestrator exists yet.
- The Bundle has no temporary bootstrap Job and remains fixed-demo-only.
- Collector and App code still require the uninstalled runtime-trust view; v0.3 implementation must remove that dependency and its registry projection fields.
- Generic `dbtobsb.dbt-policy.v1` onboarding, generated patch, and source attestation are not implemented.
- Product grants, concrete App lifecycle adapter, retain/delete uninstall, interruption matrix, reproducible RC, and live Azure proof remain pending.
- The machine release state remains `CANDIDATE` until all later gates pass.

## Reviewer response

Each owner reviews only their domain column against this packet. Report one root outcome per finding, assign implementation or live evidence to its later gate, and do not reopen unchanged `DBX-01`.
