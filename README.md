# dbtobsb

Customer-local observability for dbt Core jobs running on Databricks.

This repository contains the supported v0.3 release: a privately installed Databricks App and three Lakeflow Jobs deployed through a Databricks Declarative Automation Bundle. Required data, compute, identity, audit, and retention stay inside the customer's Azure Databricks workspace; no external telemetry platform is required. Databricks Marketplace is out of scope for this release.

## What works now

The sealed observed Job runs the pinned dbt Core project without a shell, uploads only `manifest.json`, `run_results.json`, and bounded structured logs to a managed staging Volume, and verifies every uploaded byte. The distinct collector service principal builds and preserves a deterministic archive, validates the artifact pair, and publishes allowlisted fields to three evidence tables behind three read-only health views. The exact raw archive remains in a separate managed Volume.

Object creation is intentionally split from collection. An authorized administrator may run the fixed, versioned `BOOTSTRAP_ALLOWED` entry point against an intentionally selected production catalog; it creates or verifies the product schema objects idempotently. The ordinary `RUNTIME_DML_ONLY` collector entry point performs only fixed writes to those existing objects. It cannot be switched into bootstrap mode with a runtime flag.

Start with the [plain-language documentation](docs/site/index.md). It separates
tutorials, how-to guides, reference, and explanation. The full machine contract and
governance boundary remain in the
[v0.3 supported-release contract](docs/releases/v0.3.0-support-contract.md). The App
is read-only and stopped by default; explicitly starting it can incur App compute
cost.

The latest sanitized execution proof is [v0.3.0 stable Azure Databricks acceptance](docs/evidence/v0.3.0-stable-acceptance-2026-07-18.md). It links the exhaustive beta matrix to the independently rebuilt and exercised stable artifacts.

## Ask an agent to install and run it

This repository includes an
[install-and-run skill](.agents/skills/install-and-run-dbtobsb/SKILL.md) for agents
that support repository skills. From a fresh clone, ask:

```text
Use $install-and-run-dbtobsb to install dbtobsb, run the weather example,
prove that its model result and structured logs were captured, and stop compute.
```

Before changing anything, the agent lists the available Azure Databricks choices
and asks you to confirm the profile, project, service principals, group, warehouse,
catalog, schemas, allowed data-object changes, compute deadline, warehouse stop
policy, and final retained state. It pauses again at the installer's exact preview.

The successful result is one terminal dbt Job with at least one successful model,
complete and valid artifact evidence, valid nonempty structured logs, published
health rows, the App stopped, the reconciler paused, no active product run, and the
selected warehouse stopped. The agent does not expose raw logs or captured data in
its receipt.

## Release status

The private `v0.3.0` support contract is final for the qualified `0.3.0` artifacts. Marketplace distribution is not included. Regulated use requires customer governance approval; dbtobsb is not certified or attested against a regulatory framework.

| Release component | Version |
| --- | --- |
| Git release/tag | `v0.3.0` |
| Evidence object manifest | `dbtobsb.evidence.v1.0.0-rc.11` |
| Python packages | `0.3.0` plus content-addressed final wheel versions |
| Support contract | `dbtobsb.support.v1` |
| App | `0.3.0`, read-only and stopped by default |

P1.1 remains available as an offline strict artifact-pair inspector. Its synthetic fixtures make pair validity, native dbt outcome, and capture state visibly separate.

## Inspect one artifact pair locally

P1.1 inspection is offline after installation and requires Python 3.12 plus [uv](https://docs.astral.sh/uv/). On a clean machine, the first sync can download Python packages from the configured index; regulated environments must use an approved registry, mirror, or populated cache. A disconnected installation artifact is not shipped yet.

> **Sensitive input boundary:** Real `manifest.json` and `run_results.json` files can contain Personal Data, secrets, SQL, messages, paths, topology, and identities. Use policy-approved local storage and least-privilege access; do not commit, upload, paste, or attach raw artifacts to an ordinary support ticket. Inspection does not delete or govern caller-owned files. Follow [Handle raw dbt artifacts safely](docs/developers/how-to/handle-raw-dbt-artifacts-safely.md) before replacing the synthetic fixture paths below.

Install runtime dependencies only, then inspect the successful fixture without synchronizing or contacting an index again:

```bash
uv sync --project capture --locked --no-dev
uv run --project capture --no-sync dbtobsb-capture inspect-artifact-pair \
  --manifest capture/tests/fixtures/artifact_pair/valid_success/manifest.json \
  --run-results capture/tests/fixtures/artifact_pair/valid_success/run_results.json \
  --no-color
```

The first line is `PAIR_VALID`. That means only that the two files satisfy the pinned
P1.1 contract. Follow the
[artifact tutorial](docs/site/tutorials/inspect-artifacts-locally.md) for the
valid-failure and invalid-pair examples.

## Build the documentation locally

The reader documentation uses Zensical `0.0.51`. The same strict build is published
to GitHub Pages from `main`.

```console
scripts/check_docs.sh
```

The command performs a strict local build into the ignored `site/` directory and
checks every local Markdown link.

## Run the legacy App-shell development smoke

This section validates only the earlier empty App shell in a dedicated disposable workspace. It is not the v0.3 installation or acceptance route.

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

Planning baseline: **0.20**. Implemented product slice: **supported private v0.3 release**. Release acceptance uses automated local gates, adversarial contract tests, clean bootstrap, two live Azure Databricks end-to-end attempts, controlled failure and reconciliation cases, SQL/App result comparison, both uninstall modes, and a zero-running-compute cleanup audit. The exact working agreement is in [AGENTS.md](AGENTS.md).

## License

dbtobsb is available under the [MIT License](LICENSE).
