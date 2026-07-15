# Azure Databricks eighteenth re-review: planning baseline 0.20

- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform reviewer
- Planning author-set SHA-256: `e6a8d55f2b155916d52ac0c6aa6ce87941a3d8672f6dc4a0bfdb692a3fb7fd44`
- Live-evidence SHA-256: `670f54bdcef70e458adad590e959004e08f9aa5319855104299f5813c9419ed3`
- Private run-record template SHA-256: `6c61dc5091358cae2b5a531c6017bb012a4d0fc869edfd22fcaa2369bf5dca69`
- Verdict: `PASS`
- Cloud activity: None. This review made no Azure, Databricks authentication, App, Job, SQL, warehouse, cluster, or Unity Catalog call.

## Immutable input verification

I recomputed the globally sorted author path-and-content digest and the separate evidence/template digests. All matched the requested values exactly. No frozen input was edited by this reviewer.

## Focused platform assessment

Baseline 0.20 closes the authentication-documentation gap without changing the product architecture:

- The P0 wrapper's explicit `DATABRICKS_AUTH_STORAGE=secure` setting matches current CLI behavior and takes precedence over a profile's plaintext setting.
- A non-secure inherited value is rejected before any CLI, inventory, Bundle, token, or cleanup action.
- OAuth U2M, explicit profile, canonical host, exact current user, rejected ambient token/client-secret auth, and operator-owned profile preservation remain the attended boundary.
- The source register no longer says all dbtobsb paths avoid token output. It accurately isolates the P0 health-call exception from the future production bootstrap, which still prohibits it.
- The private approval record is correctly described as an attended external governance gate rather than a Databricks API or shell-enforced control.

Current official CLI documentation states that U2M tokens default to native secure storage but may silently fall back to plaintext unless secure mode is explicit. It also documents `auth token` as emitting an OAuth access token. The revised planning claims now match both behaviors.

The evidence remains non-retroactive. It records that the live-tested implementation did not force or attest secure storage, retains that earlier implementation hash, and does not present the new local guard as live-tested. It also preserves the cost-approval nonconformance and same-operator final readback limitation.

## No-regression review

| Platform boundary | Baseline 0.20 result |
|---|---|
| Dedicated P0 workspace | Still requires complete caller visibility, no unrelated visible App, zero visible warehouses/clusters, and exact final inventory. |
| App lifecycle and cost | Stopped-by-default, Medium-only, unbound smoke; planned/cancellation/successful-stop/unbounded-failure costs remain distinct and correctly sourced. |
| Customer-local regulated architecture | No required external telemetry/control plane; optional system enrichment and Preview telemetry remain separate/disabled. |
| Direct Bundle boundary | No schema grants, UC DDL/DML, hidden migration hook, privileged migration Job/SP, or implicit App start was introduced. |
| Least privilege and trusted roots | Runtime write sets, customer-owned objects, administrator/group/App/Job roots, and unsupported administrator-resistant custody remain explicit. |
| P6 fence (`DBX-P0-030`) | Separate managed-table create, `Serializable` property operation, eleven separate `ADD CONSTRAINT` operations, full recovery/readback, and singleton-last order remain intact. |
| Jobs terminality (`DBX-P0-031`) | Current-status-first/legacy-fallback handling still treats `INTERNAL_ERROR` as terminal failure and unknown/conflicting/incomplete evidence as indeterminate. |
| App sources/cost (`DBX-P0-032/033`) | Precise status/state/compute-size sources and honest planned-versus-hard-ceiling semantics remain intact. |

## Sources checked

- [Databricks CLI token storage](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/authentication#token-storage)
- [Databricks CLI stored-credentials behavior](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/troubleshooting#stored-credentials-error)
- [`databricks auth token`](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/reference/auth-commands#databricks-auth-token)
- [Azure Databricks App status](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts#app-status)
- [Azure Databricks App compute sizes](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/compute-size)
- [Azure Databricks `CREATE TABLE [USING]`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-syntax-ddl-create-table-using)
- [`ALTER TABLE ... ADD CONSTRAINT`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-syntax-ddl-alter-table-add-constraint)
- [Pinned first-party Jobs lifecycle enum](https://github.com/databricks/databricks-sdk-go/blob/bad015296869703de251d189b8a43ea4e6df8bfb/service/jobs/model.go#L4129-L4177)

## Verdict

`PASS`

The exact baseline 0.20 planning, evidence, and template inputs are approved. Authentication-storage and token-output claims now match current Databricks behavior, historical evidence remains honest, the external approval boundary is explicit, and no prior platform finding or architecture boundary regressed.
