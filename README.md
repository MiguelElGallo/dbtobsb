# dbtobsb

Customer-local observability for dbt Core jobs running on Databricks.

This private repository contains a reviewed product plan and an early implementation. The target product is a private Databricks App delivered through a Databricks Declarative Automation Bundle. Required data, compute, identity, audit, and retention stay inside the customer's Databricks environment; no external telemetry platform is required.

## What works now

P0 is a deliberately narrow FastAPI App smoke. It proves that the locked source can be packaged, deployed, started, called, logged, and stopped through Databricks. It does **not** run dbt, ingest artifacts, read product data, or prove product readiness.

The first paid-workspace run passed the health/log/stop checks. Its [sanitized evidence record](docs/evidence/p0-live-smoke-2026-07-15.md) preserves both the technical result and the original cost-approval process finding. Later compute-size and dedicated-workspace guardrails have passed local tests but were not used to justify another paid run.

P1.1 can validate one pinned artifact pair locally. It does not retrieve Databricks archives, classify capture states, parse structured logs, write observability tables, or run dbt. Its three synthetic, sanitized fixtures make pair validity, native dbt outcome, and future capture state visibly separate.

## Inspect one artifact pair locally

P1.1 runs offline and requires Python 3.12 plus [uv](https://docs.astral.sh/uv/). Install the locked development environment and inspect the successful fixture:

```bash
uv sync --project capture --locked
uv run --project capture dbtobsb-capture inspect-artifact-pair \
  --manifest capture/tests/fixtures/artifact_pair/valid_success/manifest.json \
  --run-results capture/tests/fixtures/artifact_pair/valid_success/run_results.json \
  --no-color
```

The first line is `PAIR_VALID`. That means only that the two files satisfy the pinned P1.1 contract. Follow the [developer tutorial](docs/developers/tutorials/inspect-an-artifact-pair.md) for the valid-failure and invalid-pair examples, or use the [CLI report and exit-code reference](docs/developers/reference/cli-report-and-exit-codes.md) for automation.

## Run the P0 smoke

### 1. Check the supported workspace and tools

P0 supports only a dedicated smoke workspace in which the OAuth user has approved complete inventory visibility. Before mutation, the wrapper requires:

- no App other than an optional existing `dbtobsb-smoke` that is `STOPPED`, unbound, and `MEDIUM`;
- zero visible SQL warehouses;
- zero visible clusters;
- Databricks CLI exactly `1.7.0`, plus `jq` and `curl`; and
- a named OAuth user-to-machine (U2M) profile for the exact intended host and user.

The wrapper checks this observable inventory and exits before Bundle validation or deployment when it is not clean. It also sets `DATABRICKS_AUTH_STORAGE=secure` and rejects an inherited non-secure value; an existing plaintext-only profile therefore cannot satisfy authentication. A shared or partially visible workspace is unsupported for this P0 route. Never stop or delete unrelated resources to make the check pass.

Run the local gates first:

```bash
uv sync --project app --locked --extra dev
uv run --project app --extra dev pytest
uv run --project app --extra dev ruff check app/dbtobsb_app app/tests
uv run --project app --extra dev ruff format --check app/dbtobsb_app app/tests
uv run --project app --extra dev ty check app/dbtobsb_app app/tests
bash -n scripts/smoke_databricks_app.sh
shellcheck scripts/smoke_databricks_app.sh
```

### 2. Approve the private cost record

Copy the [P0 private run-record template](docs/templates/p0-smoke-run-record.md) into the policy-approved private system. Do not fill it in or commit real workspace/user data here. This is an attended procedural gate: the wrapper cannot inspect that external record, so the operator and approver must not authorize execution while any required field is missing or `approval_state` is not `APPROVED`.

The current P0 assumptions are:

| Control | P0 value |
| --- | --- |
| App size | `MEDIUM`; the wrapper refuses another live size |
| Published rate | `0.5 DBU/hour` ([official compute-size reference](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/compute-size)) |
| Cancellation deadline | 10 minutes after wrapper invocation |
| Planned usage through cancellation | At most `0.084 DBU` (`0.5 × 10 / 60`, rounded up) |
| Successful-stop exposure | Cleanup waits up to 20 more minutes; the conservative 30-minute window is `0.25 DBU` |
| Hard cost ceiling | None; a failed stop can incur cost until `STOPPED` is observed |
| Schedule | None |
| Cleanup owner | One named person stays at the terminal for the entire run |
| Required final state | One stopped P0 App; zero warehouses and clusters |

Running Apps incur compute cost; stopped Apps do not ([official App-status reference](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts#app-status)). The `0.084 DBU` value is a planned budget, not a guaranteed maximum. If policy requires a mechanically enforced hard monetary ceiling, do not run this smoke.

Start a separate 10-minute timer immediately before the command. If it fires, press `Ctrl-C`. Cleanup attempts the stop for up to 20 minutes. If `STOPPED` is not verified, cost may continue: run the copy-ready recovery commands printed by the wrapper and escalate immediately.

### 3. Run once

Never pass a token or client secret to the wrapper. To call the token-protected App health URL, this development-only P0 wrapper obtains one short-lived U2M access token with `databricks auth token`, keeps it in memory, sends it to `curl` through standard input with user/global curl configuration disabled, and clears it. It never prints, persists, logs, or places the token in an argument. This narrow smoke exception is not the future regulated production bootstrap contract, which prohibits token-output commands.

```bash
DBTOBSB_DATABRICKS_PROFILE='<oauth-profile>' \
DBTOBSB_EXPECTED_HOST='https://<workspace-host>' \
DBTOBSB_EXPECTED_USER='<signed-in-user>' \
scripts/smoke_databricks_app.sh
```

The wrapper validates the exact CLI, host, user, authentication type, dedicated-workspace inventory, stopped `MEDIUM` size, and absence of App bindings. It deploys stopped, starts once, calls `/api/health`, finds the structured stdout event, then always attempts and verifies stop.

The successful health body is exactly:

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

### 4. Retain the separate final readback

After the wrapper exits, the cleanup owner runs and retains:

```bash
databricks apps list -p '<oauth-profile>' -o json \
  | jq -e --arg app 'dbtobsb-smoke' \
    'length == 1
     and .[0].name == $app
     and .[0].compute_status.state == "STOPPED"
     and .[0].compute_size == "MEDIUM"
     and ((.resources // []) | length == 0)'
databricks warehouses list -p '<oauth-profile>' -o json | jq -e 'length == 0'
databricks clusters list -p '<oauth-profile>' -o json | jq -e 'length == 0'
```

All three commands must exit `0`. Any other result is a failed cleanup proof, not a prompt to alter unrelated resources. The stopped App object and uploaded Bundle files can remain; they do not represent running App compute.

## Product direction

The product plan keeps these user-visible principles:

- customer-local data, compute, identity, audit, and retention;
- deterministic, artifact-first evidence from `manifest.json` and `run_results.json`;
- least-privilege runtime identities and customer-owned Unity Catalog objects;
- restricted diagnostics rather than raw logs in the ordinary UI;
- explicit cost, recovery, retention, and uninstall consequences; and
- optional AI assistance that is never required for capture, validation, or operation.

Detailed migration, trust, deployment, controlled-action, and dbt contracts live in the planning documents rather than in this getting-started path:

- [Product and delivery plan](docs/plans/product-plan.md)
- [Architecture decision: private App plus Bundle](docs/decisions/0001-private-app-bundle.md)
- [Documentation plan](docs/plans/documentation-plan.md)
- [Review process](docs/plans/review-process.md)
- [Research source register](docs/research/source-register.md)
- [Review records](docs/reviews/README.md)
- [Documentation index](docs/index.md)

## Current baseline

Planning baseline: **0.20**. Implemented product slice: **P1.1 candidate**. Every independently deliverable slice requires Databricks, dbt Core, and usability reviews. Documentation additionally requires Diataxis, FastAPI-style, security/compliance, and usability/accessibility passes. The exact working agreement is in [AGENTS.md](AGENTS.md).
