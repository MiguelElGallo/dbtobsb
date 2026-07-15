# P0 live Databricks App smoke evidence

**Run date:** 2026-07-15  
**Cloud:** Azure Databricks  
**Scope:** One private Databricks App process-liveness smoke  
**Result:** Technical PASS with cost-control and credential-storage process findings  
**Live-tested implementation hash:** `eff855524237e36909b282b5c030207b0478606e7f2b44a810082012d33f6a5c`

This record is intentionally sanitized. It contains no workspace URL, workspace or account identifier, user identity, App identifier, service-principal identifier, OAuth token, or raw customer log.

## Safety preflight

- Databricks CLI was exactly `1.7.0`.
- A named Databricks OAuth U2M profile matched both the intended canonical workspace host and the same current user observed through Azure CLI authentication.
- The wrapper rejected ambient token and client-secret authentication.
- The starting inventory was zero Apps, zero SQL warehouses, and zero clusters.
- `databricks bundle validate` passed.
- `databricks bundle plan` proposed exactly one App create, zero changes, and zero deletes.
- The Bundle declared `lifecycle.started: false` and no App resource bindings.

## Cost-control process finding

The run did **not** have the product plan's complete numeric cost envelope recorded before execution. In particular, the pre-run record omitted a maximum elapsed interval, expected DBUs, cancellation deadline, and named cleanup owner. This is a process nonconformance; a final zero-running state does not retroactively resolve it.

The observed remote object-create-to-final-`STOPPED` window was 2 minutes 52 seconds on `MEDIUM` App compute. At the current published `0.5 DBU/hour` rate, that whole window gives a conservative post-run upper bound below `0.024 DBU`; the actual billable `ACTIVE` interval was a subset of the window. This is a derived bound, not an invoice or a substitute for later billing-table reconciliation. The final stopped state prevents further App compute cost.

Baseline 0.20 resolves the runbook defect for subsequent runs by placing the operator cancellation deadline, planned DBUs through that deadline, successful-stop exposure bound, unbounded stop-failure warning, cleanup ownership, residual-object disclosure, private record template, and exact dedicated-workspace final inventory before the executable command. Later wrapper guards fail before mutation on unrelated visible Apps, warehouses, or clusters. Those guards passed local tests; no second paid run was performed merely to erase this historical finding.

## Credential-storage process finding

The live-tested wrapper required a named OAuth U2M profile but did not force or attest `DATABRICKS_AUTH_STORAGE=secure`. The run therefore does not prove that the profile avoided plaintext fallback, even though no token or profile material was captured in this evidence. Baseline 0.20 makes the current wrapper set secure storage explicitly and reject an inherited non-secure value; fake-CLI tests fail if secure storage is not present. This local correction does not retroactively upgrade the live evidence.

The P0 health call uses a short-lived access token obtained from the named U2M profile. The wrapper holds it in memory, supplies the authorization header to `curl` through standard input with ambient curl configuration disabled, and clears it; it is not logged, persisted, or passed in an argument. This development-only smoke exception is distinct from the future regulated production bootstrap, which prohibits token-output commands.

## Observed run

1. The Bundle uploaded the locked FastAPI source and created the App.
2. The first live readback observed App compute `STOPPED` with zero resource bindings.
3. The wrapper invoked the App Bundle resource once.
4. The App reached `ACTIVE` at its Databricks Apps URL with zero resource bindings.
5. Authenticated `GET /api/health` returned exactly:

   ```json
   {
     "status": "alive",
     "check": "process_liveness",
     "readiness": "not_evaluated",
     "phase": "p0_smoke",
     "service": "dbtobsb",
     "version": "0.1.0"
   }
   ```

6. Databricks App stdout contained the required structured `health_check` event.
7. The exit cleanup issued the bounded App stop and read back `STOPPED`.

The endpoint proves only that the packaged App process ran and served its reviewed HTTP contract. It does not prove dbt execution, artifact capture, product-data access, dependency readiness, or product readiness.

## Separate post-run state readback

After the wrapper exited successfully, another read-only CLI call—using the same operator and credential context, not an independent human attestation—observed:

| Check | Final observation |
| --- | --- |
| App object | Present and `STOPPED` |
| Non-stopped Apps | `0` |
| App resource bindings | `0` |
| Pending App deployment | None reported |
| SQL warehouses | `0` |
| Clusters | `0` |

The stopped App object and uploaded Bundle files remain as reproducible evidence. No App compute, SQL warehouse, or cluster was left running.

## Reproduction

Use the [P0 smoke instructions](../../README.md#run-the-p0-smoke). Supply a local profile, canonical host, and exact expected user at runtime; do not copy any real values into this repository or a review record.
