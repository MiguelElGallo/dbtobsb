# Sixteenth dbt Core re-review: final P0 planning baseline 0.19

- Reviewed input: frozen author-owned planning file set
- Frozen author-input SHA-256: `703ae3cc1a86bee5d641c7fa478fbb49bdd88cd193f2aec36e61e9b00078eb5f`
- Separate evidence SHA-256: `d4904dc48dd8d803d258e58845da929418d5f11dbb55a805aa919c9fbb71c0c2`
- Separate run-record-template SHA-256: `172ae9825e5e7383526fd2879fe4deb29df3a24ac972c63fd37559484f4d310b`
- Review date: 2026-07-15
- Reviewer lens: dbt Core and dbt-databricks contract correctness
- Planning verdict: **PASS**
- Evidence dbt-boundary verdict: **PASS**
- Template dbt-boundary verdict: **PASS**
- Findings: none
- Cloud/authentication activity: none

## Executive verdict

Final baseline 0.19 passes the dbt Core re-review. The lean entry path now leads with what is implemented, gives one bounded App-smoke procedure, and moves detailed future-product contracts behind an explicitly labeled **Product direction** section. It never represents App liveness, App stdout, stopped compute, cost approval, or inventory cleanup as a dbt run or capture result.

The future dbt contract remains closed and internally consistent: one qualified runtime pair, optional `deps` plus one named-selector `build`, per-attempt and per-ordinal paths, exact artifact and structured-log validation, total capture precedence, immutable native outcomes, and strict data minimization. The final evidence and run-record template are operational P0 inputs only; neither contributes a dbt command, artifact, event, identity, status, or readiness signal.

`DBT-P0-001` through `DBT-P0-008` remain resolved with no regression. No new dbt finding is opened.

## Immutable scope and hash proof

The planning aggregate was reproduced from this exact path set:

- `AGENTS.md`
- `README.md`
- `docs/decisions/0001-private-app-bundle.md`
- `docs/index.md`
- `docs/plans/documentation-plan.md`
- `docs/plans/product-plan.md`
- `docs/plans/review-process.md`
- `docs/research/source-register.md`

The sorted path-plus-content procedure was:

```sh
{
  printf '%s\n' README.md AGENTS.md docs/index.md
  rg --files docs/decisions docs/plans docs/research -g '*.md'
} | LC_ALL=C sort -u > /tmp/dbtobsb-baseline-019-files.txt

while IFS= read -r file; do
  shasum -a 256 "$file"
done < /tmp/dbtobsb-baseline-019-files.txt | shasum -a 256
```

Result:

```text
703ae3cc1a86bee5d641c7fa478fbb49bdd88cd193f2aec36e61e9b00078eb5f  -
```

The evidence and copy-only run-record template were intentionally outside that aggregate and were verified separately:

```text
d4904dc48dd8d803d258e58845da929418d5f11dbb55a805aa919c9fbb71c0c2  docs/evidence/p0-live-smoke-2026-07-15.md
172ae9825e5e7383526fd2879fe4deb29df3a24ac972c63fd37559484f4d310b  docs/templates/p0-smoke-run-record.md
```

This report is outside all three frozen inputs.

## Lean README and current-versus-future boundary

| Entry-point claim | Result | dbt interpretation |
| --- | --- | --- |
| Repository purpose | **Pass** | “Customer-local observability” is product direction, not a claim that P0 already observes dbt. |
| **What works now** | **Pass** | P0 is explicitly a FastAPI App smoke and explicitly does not run dbt, ingest artifacts, read product data, or prove product readiness. |
| Historical live evidence | **Pass** | The README says the first paid run proved health/log/stop only and says later guards were local-tested rather than used to justify another paid run. |
| P0 procedure | **Pass** | Tool, OAuth, inventory, cost, start, health, App-log, stop, and final-readback facts stay in the App/platform domain. |
| Health response | **Pass** | `process_liveness` plus `readiness: not_evaluated` cannot be interpreted as dbt, dependency, capture, or product readiness. |
| **Product direction** | **Pass** | Artifact-first evidence, restricted diagnostics, runtime identities, and optional AI are introduced after the current procedure and linked to the planning contract. |
| Baseline label | **Pass** | The page identifies planning baseline 0.19 and requires later independently reviewed slices; it does not call P0 the product. |

`docs/index.md` repeats the same boundary: the current endpoint proves only App process liveness, and dbt execution/artifact ingestion begin later.

## Resolved dbt-contract regression check

| Contract | Baseline 0.19 result |
| --- | --- |
| Candidate runtime | **Pass** — `dbt-databricks==1.12.2`, `dbt-core==1.11.12`, `dbt-common==1.37.5`, Python 3.12.3, structured-log version 3, and the exact wheel digest remain candidate pins, not an unqualified support claim. |
| Dependency qualification | **Pass** — the complete Python/Linux and Node graphs still require hash locks and golden-capture qualification; compatible-looking minor versions are not inferred to work. |
| Command surface | **Pass** — optional governed `dbt deps` followed by exactly one named-selector-scoped `dbt build` remains the only supported sequence. Other commands are classified explicitly rather than accepted from artifact presence. |
| Zero execution | **Pass** — both zero-selection warnings are promoted, configuration conflicts fail scanning, and an empty results array independently becomes `DBT_EMPTY_EXECUTION`; none can become observable. |
| Resolved flags and paths | **Pass** — project/profile and current/legacy alias conflicts are deterministic; both ordinals receive closed privacy/logging flags; `deps` receives neither selector nor target path; each build attempt has an immutable target and ordinal-local log path. |
| Primary artifact pair | **Pass** — exactly manifest v12 plus run-results v6, matching parseable invocation UUID, Core 1.11.12, `args.which=build`, manifest adapter type `databricks`, non-empty unique results, and trusted attempt/ordinal context remain mandatory. |
| Result resolution | **Pass** — result IDs resolve exactly once through the supported BuildTask collections. Manifest inventory stays distinct from executed results and unmatched inventory remains `NO_RESULT_RECORDED`. |
| Structured logs | **Pass** — the ordered states remain `UNAVAILABLE`, `NOT_INITIALIZED`, `TRUNCATED`, `MALFORMED`, `MISSING`, `UNKNOWN_VERSION`, and `VALID`; human `msg` is never parsed as a machine protocol. |
| Capture precedence | **Pass** — `ARCHIVE_UNAVAILABLE`, `INVALID_CAPTURE_CONTRACT`, `COMPLETE`, `PARTIAL`, and `NOT_PRODUCED` remain total, ordered, and separate from App/cost/trust state. A `deps` event never proves build start. |
| Attempt identity and trust | **Pass** — the full Lakeflow AttemptKey plus command ordinal remains authoritative. Collector-observed trust is frozen as observation-time provenance and cannot alter identity, hashes, artifact validity, capture precedence, or native outcomes. |
| Privacy and egress | **Pass** — raw/compiled SQL, relation names, CLI args/vars, messages, arbitrary metadata/events, custom environment values, and sensitive paths remain excluded from ordinary product tables. Anonymous usage and artifact-ingest upload are explicitly disabled. |
| Optional controls and AI | **Pass** — action/fence/token/trust/deployment inputs and all AI assistance remain outside dbt argv, environment, selectors, vars, paths, artifacts, events, authorization, and deterministic validation. |

## Final evidence assessment

The evidence hash `d4904d…` records one App process-liveness run. Its corrected reproduction link resolves to the current `README.md#run-the-p0-smoke` anchor. The record explicitly says:

- no dbt execution was proved;
- no artifact capture was proved;
- no product data was accessed;
- no dependency or product readiness was proved;
- zero warehouses and clusters were left running; and
- the App event is a fixed `health_check` stdout event, not a dbt structured event.

The historical cost-process nonconformance and conservative DBU calculation remain operational evidence. They do not modify dbt invocation or result semantics.

## Final run-record-template assessment

The template hash `172ae9…` is a private approval/cleanup record for the App smoke. Its fields cover approval, accountable cleanup-owner reference, dedicated-workspace inventory, App size/rate, timestamps, stop exposure, risk acceptance, cleanup result, and evidence reference.

The blank, synthetic-approved, and rejected examples all preserve the same boundary. The synthetic note says “Technical smoke only; no dbt execution or product readiness claim.” No field can become a dbt command, selector, flag, vars mapping, target/log path, invocation ID, artifact fact, structured event, native status, or capture predicate. The new `cleanup_owner_reference` stays in the private record system and is unrelated to dbt identity.

## Current primary-source refresh

The current first-party sources support the frozen candidate contract:

- [dbt Core 1.11.12](https://github.com/dbt-labs/dbt-core/releases/tag/v1.11.12) is an actual July 2026 release, not a roadmap version.
- [dbt-databricks 1.12.2](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.2) explicitly raises its dbt Core upper bound to include 1.11.12 while remaining below 1.11.13.
- [Manifest documentation](https://docs.getdbt.com/reference/artifacts/manifest-json) maps Core 1.11 to manifest v12 and states that the manifest represents project inventory, including resources not executed.
- [Run-results documentation](https://docs.getdbt.com/reference/artifacts/run-results-json) identifies v6 as current, says only executed nodes appear, and documents `args.which` and result `unique_id`.
- [Events and logs](https://docs.getdbt.com/reference/events-logging) documents invocation identity and log version as structured fields and explicitly says human `msg` is not intended for machine consumption.

These sources validate the plan's candidate inputs; they do not replace its required fixture and staging qualification.

## Findings

None.

## Cloud and mutation statement

This review used local repository reads, local hash checks, and current public first-party dbt sources. It made no Azure or Databricks authentication call, ran no dbt or SQL, started no compute, and changed no author, evidence, template, or cloud resource.

## Final disposition

- Planning baseline `703ae3…`: **PASS**.
- Separate evidence `d4904d…` dbt boundary: **PASS**.
- Separate template `172ae9…` dbt boundary: **PASS**.
- `DBT-P0-001` through `DBT-P0-008`: resolved with no regression.
- New dbt findings or P0 blockers: none.

