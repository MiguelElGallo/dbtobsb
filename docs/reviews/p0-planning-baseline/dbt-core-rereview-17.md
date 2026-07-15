# Seventeenth dbt Core re-review: final P0 planning baseline 0.20

- Planning author SHA-256: `e6a8d55f2b155916d52ac0c6aa6ce87941a3d8672f6dc4a0bfdb692a3fb7fd44`
- Separate evidence SHA-256: `670f54bdcef70e458adad590e959004e08f9aa5319855104299f5813c9419ed3`
- Separate run-record-template SHA-256: `6c61dc5091358cae2b5a531c6017bb012a4d0fc869edfd22fcaa2369bf5dca69`
- Review date: 2026-07-15
- Reviewer lens: dbt Core boundary and P0-versus-production authentication exception
- Planning verdict: **PASS**
- Evidence verdict: **PASS**
- Template verdict: **PASS**
- Findings: none
- Cloud/authentication activity: none

## Executive verdict

Baseline 0.20 passes the focused dbt Core re-review. The security delta creates no dbt execution, configuration, artifact, log, identity, capture, or outcome coupling.

The development-only P0 App smoke uses `databricks auth token` solely to make one authenticated HTTP liveness request. README, evidence, product plan, and source register all label that behavior as a narrow P0 exception. The future regulated `dbtobsb bootstrap` contract explicitly rejects token-output commands and requires the exception to be removed or replaced before its gate. Nothing in the exception can become a dbt command, Job input, selector, vars mapping, target/log path, artifact field, structured event, AttemptKey component, capture predicate, or native outcome.

The existing dbt capture contract remains unchanged and passes regression review. `DBT-P0-001` through `DBT-P0-008` remain resolved.

## Immutable scope

The planning aggregate covers `README.md`, `AGENTS.md`, `docs/index.md`, and all Markdown files under `docs/decisions`, `docs/plans`, and `docs/research`. The sorted path-plus-content procedure reproduced:

```text
e6a8d55f2b155916d52ac0c6aa6ce87941a3d8672f6dc4a0bfdb692a3fb7fd44  -
```

Evidence and the copy-only private template were verified separately:

```text
670f54bdcef70e458adad590e959004e08f9aa5319855104299f5813c9419ed3  docs/evidence/p0-live-smoke-2026-07-15.md
6c61dc5091358cae2b5a531c6017bb012a4d0fc869edfd22fcaa2369bf5dca69  docs/templates/p0-smoke-run-record.md
```

This report is outside all three frozen inputs.

## P0 token exception versus production contract

| Contract point | Baseline 0.20 evidence | dbt verdict |
| --- | --- | --- |
| P0 scope | README calls the wrapper development-only and the endpoint process-liveness-only. | **Pass** — not a dbt run or product readiness claim. |
| Token purpose | One short-lived U2M token authenticates only `GET /api/health`. | **Pass** — no dbt command or evidence path receives it. |
| Token handling | Token stays in a shell variable, reaches curl configuration through standard input, is absent from argv/output/logs, and is cleared. | **Pass** — no token becomes a dbt flag, environment value, artifact, or event. |
| P0 secure storage | The wrapper forces `DATABRICKS_AUTH_STORAGE=secure`, rejects inherited non-secure storage, and still rejects ambient token/client-secret variables. | **Pass** — authentication storage is an App-smoke prerequisite, not dbt configuration. |
| Production bootstrap | Product plan rejects `auth token`, deprecated `auth env`, sensitive auth output, plaintext storage, ambient credential variables, and profile transfer. | **Pass** — the P0 exception cannot silently become production behavior. |
| Removal gate | The plan requires the exception to be removed or replaced before regulated production bootstrap acceptance. | **Pass** — no grandfathered token-output dependency. |
| Historical evidence | The live evidence records that its old wrapper did not force secure storage and does not retroactively upgrade that run. | **Pass** — historical App evidence remains honest and dbt-neutral. |
| Private run record | Template now states that approval is an attended procedural gate the wrapper cannot inspect. | **Pass** — approval fields do not enter dbt execution or capture. |

## dbt-contract regression check

| Contract | Result |
| --- | --- |
| Candidate pair | **Pass** — `dbt-databricks==1.12.2`, `dbt-core==1.11.12`, `dbt-common==1.37.5`, Python 3.12.3, manifest v12, run-results v6, and structured-log version 3 remain candidate pins requiring fixtures. |
| Command surface | **Pass** — optional governed `deps` plus exactly one named-selector `build`; other commands remain classified and unsupported as primaries. |
| Resolved flags and paths | **Pass** — configuration conflicts fail deterministically; command ordinals retain closed flags and independent immutable log/target boundaries. |
| Artifact and result semantics | **Pass** — invocation identity, exact schema/version/command/adapter checks, non-empty unique results, exact result-ID resolution, and inventory-versus-execution separation remain intact. |
| Structured logs | **Pass** — seven ordered states remain total; human `msg` remains display-only. |
| Capture precedence | **Pass** — archive, primary-pair, partial, and not-produced states remain ordered and independent of App/auth/cost/trust state. |
| Attempt and trust | **Pass** — token/auth fields do not enter AttemptKey, hashes, artifact validity, collector provenance, capture, or native Lakeflow/dbt/node outcomes. |
| Privacy and egress | **Pass** — raw SQL/code, relations, args/vars, arbitrary metadata/events, sensitive environment values, and raw logs remain outside ordinary tables; dbt telemetry/upload remain disabled. |

## Current primary sources

- [Azure Databricks CLI authentication](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/authentication) documents U2M short-lived tokens, OS-native secure storage, plaintext fallback, and environment-variable precedence.
- [Databricks CLI auth commands](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/reference/auth-commands) documents that `auth token` returns an OAuth access token from the U2M cache.
- [curl configuration](https://curl.se/docs/manpage.html#-K) documents that `--config -` reads options from standard input and that `--disable` prevents loading the default curl configuration.
- [Manifest JSON](https://docs.getdbt.com/reference/artifacts/manifest-json), [run-results JSON](https://docs.getdbt.com/reference/artifacts/run-results-json), and [events/logging](https://docs.getdbt.com/reference/events-logging) continue to distinguish dbt inventory, executed results, invocation identity, structured fields, and unstable human messages from an App HTTP liveness call.

## Findings

None.

## Final disposition

- Planning baseline `e6a8d55…`: **PASS**.
- Evidence `670f54bd…`: **PASS**.
- Template `6c61dc50…`: **PASS**.
- New dbt findings or blockers: none.
- No cloud, authentication, dbt, SQL, or paid-compute action was performed.

