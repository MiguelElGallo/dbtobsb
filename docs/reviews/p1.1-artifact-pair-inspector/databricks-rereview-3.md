# Azure Databricks platform and security closure re-review: P1.1 artifact-pair inspector

- Commit/diff: `75b7d41316216a3b18a3c56ff0c98f133f7aab89` against finding commit `bedfaa9d9e803c168c2481d5e4f18264a1f40e01`
- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform and security reviewer
- Verdict: `PASS_WITH_FOLLOW_UP`
- Prior finding: `DBX-P1.1-003` in [`databricks-rereview-2.md`](databricks-rereview-2.md)
- Cloud activity: None. This closure review made no Azure, Databricks authentication, App, Jobs, SQL, warehouse, cluster, serverless-compute, or Unity Catalog call and did not create, start, stop, modify, or delete a cloud resource.

## Scope and source basis

This is a focused immutable-commit closure review. The only production change after `bedfaa9` is local issue canonicalization inside the artifact-pair inspector. The remaining changes are targeted tests, the historical evidence test-count update, and the three preceding independent re-review records. No Bundle, App, Job, collector, archive retrieval, Unity Catalog, deployment, CI workflow, dependency, or public report-schema implementation changed.

The Azure Databricks source basis remains the first-party set recorded in the preceding reviews, including [dbt in Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/how-to/use-dbt-in-workflows), [Jobs API limits](https://learn.microsoft.com/en-us/azure/databricks/resources/limits), [Jobs permissions and result visibility](https://learn.microsoft.com/en-us/azure/databricks/jobs/privileges), and [Unity Catalog Volume files](https://learn.microsoft.com/en-us/azure/databricks/volumes/volume-files). This commit introduces no new platform semantic claim.

## Finding resolution

### DBX-P1.1-003: Resolved — mixed invalid evidence is canonical through API and CLI

- Original severity: Medium
- Resolution commit: `75b7d41316216a3b18a3c56ff0c98f133f7aab89`
- Re-review outcome: `RESOLVED`

The inspector now derives `_ISSUE_RANK` from the one shared `ISSUE_PRECEDENCE` registry. `_invalid()` deduplicates all encountered codes, sorts the unique set by that rank, applies the 20-issue cap after sorting, and only then constructs `ArtifactPairReport`. This establishes the constructor's canonical-order invariant instead of asking encounter order to happen to match it.

The committed tests exercise the corrected boundary at three levels:

1. A schema-valid duplicate-result-ID plus invalid-timing pair must return the ordered issues `DBT_RESULTS_DUPLICATE_ID`, then `DBT_TIMING_INVALID`, and validate against the bundled report schema.
2. A mixed parse case must return `DBT_RUN_RESULTS_JSON_INVALID`, then `DBT_MANIFEST_JSON_DUPLICATE_KEY`.
3. Every pair from the 26-code registry is supplied to the internal report factory in reverse order with a duplicate; every result must be deduplicated and canonical.

The installed-command tests cover both mixed cases with a two-second bound, require exit `10`, empty stderr, `PAIR_INVALID`, exact canonical issue codes, and no canary disclosure.

An independent closure probe built the reviewed wheel, installed it with the seven locked runtime packages into an isolated environment, and tested both the public API and that environment's real `dbtobsb-capture` entry point. The semantic input remained valid against both vendored dbt schemas:

```text
manifest_schema_errors=0
run_results_schema_errors=0
api_semantic=PAIR_INVALID:DBT_RESULTS_DUPLICATE_ID,DBT_TIMING_INVALID
cli_exit=10 codes=DBT_RESULTS_DUPLICATE_ID,DBT_TIMING_INVALID
```

The parse-mixed path also closed end to end:

```text
api_parse=PAIR_INVALID:DBT_RUN_RESULTS_JSON_INVALID,DBT_MANIFEST_JSON_DUPLICATE_KEY
cli_exit=10 codes=DBT_RUN_RESULTS_JSON_INVALID,DBT_MANIFEST_JSON_DUPLICATE_KEY
```

Both API reports and both CLI reports validated against `dbtobsb.artifact-pair-report.v1`. Each issue had exactly the six static fields `code`, `component`, `field`, `observed_category`, `impact`, and `next_action`; output contained no `CANARY_` value. The former `ValueError` and CLI exit-4 path were not reached.

## Regression assessment

| Boundary | Outcome | Evidence |
| --- | --- | --- |
| `DBX-P1.1-001` installed-resource boundary | `REMAINS_RESOLVED` | No caller path is opened by the API. A fresh installed-wheel audit observed only `manifest-v12.json` and `run-results-v6.json` under installed package resources and zero socket events. |
| `DBX-P1.1-002` compute-evidence scope | `REMAINS_RESOLVED` | The historical record still limits its `2026-07-15T21:54:20+03:00` inventory to listed classes visible to the profile, includes zero active Lakeflow Job runs, and disclaims every-service coverage. This review did not refresh it or claim current workspace idleness. |
| Customer-local and runtime egress | `PASS` | The production diff adds only a constant local rank map and local sorting. No Azure, Databricks, network, telemetry, subprocess, environment, SQL, Bundle, or Unity Catalog path was added. The installed API audit recorded `socket_events=0`. |
| Evidence and Personal Data safety | `PASS` | Reports remain closed and static. Raw artifacts, SQL, messages, adapter responses, variables, paths, environment values, project/relation names, resource IDs, and invocation IDs are neither retained nor emitted. The mixed-failure probes passed exact-shape, canary, and report-schema checks. |
| Bounded input handling | `PASS` | The failing schema-valid multi-defect case now returns ordinary invalid evidence. Pairwise canonicalization covers every registry pair; CLI tests retain their two-second timeout. Existing 128 MiB, depth, nonblocking-file, FIFO, device, symlink, and static-error controls remain unchanged and green. |
| CI and supply chain | `PASS` | `.github/`, `capture/pyproject.toml`, `capture/uv.lock`, `scripts/check_capture.sh`, `databricks.yml`, and the App are unchanged. Existing read-only workflow permission, full action SHAs, uv pin, cache disablement, locked runtime-only sync, timeout, and no artifact upload remain intact. |
| P1.1 versus P2 scope | `PASS` | The change does not retrieve archives, parse structured logs, correlate AttemptKey, attest live runtime, classify capture completeness, or emit `CONFIRMED_ABSENT`. Later collector and release gates remain explicitly later work. |

## Customer-local and no-compute evidence

The isolated installed-wheel runtime audit returned:

```text
installed_schema_opens=manifest-v12.json,run-results-v6.json
socket_events=0
safe_static_issue_shape=passed
```

The production package still has no Azure or Databricks SDK, network client, telemetry SDK, SQL client, environment lookup, or subprocess launcher. The public API's only internal reads are the two checksum-pinned schemas. Dependency build/install egress remains separately disclosed and was not reclassified as product-runtime egress.

The evidence record changed only its verified test count and coverage description, from 85 to 90 tests. Its fixtures remain synthetic with `runtime_evidence=false` and `runtime_attestation=false`. Its compute paragraph remains point-in-time, profile-visible, and narrower than all Azure or Databricks billing. No cloud command was used to re-observe or mutate that state in this review.

## Non-blocking later gates

The prior P2 and release follow-ups remain owned by their later parts: do not persist short-lived task artifact links or raw output; apply bounded rate-aware Jobs reconciliation; require stable staged proof before `CONFIRMED_ABSENT`; do not treat `ALL_DONE` as exactly-once delivery; qualify archive/custom paths and closed-file Volume handling; enforce Jobs result-visibility limits for raw evidence; preserve the disclosed Unity Catalog `MODIFY` authority boundary; and qualify the final Linux/disconnected provenance and SBOM distribution path.

Owners: P2 collector owner for collector/retrieval controls and release-packaging owner for distributable supply-chain controls. These are not present P1.1 defects.

## Local and read-only validation

All checks used exact commit `75b7d41316216a3b18a3c56ff0c98f133f7aab89`. No Databricks or Azure command was run.

```text
scripts/check_capture.sh
90 passed in 3.17s
Ruff lint: passed
Ruff format: passed
ty: passed
fixture byte-identical regeneration: passed
seven-package runtime-only locked environment: passed
wheel build and isolated installed console entry point: passed
DBTOBSB_CAPTURE_CHECK_PASSED

bash -n scripts/check_capture.sh
passed

shellcheck scripts/check_capture.sh
passed

git diff --check bedfaa9d9e803c168c2481d5e4f18264a1f40e01..75b7d41316216a3b18a3c56ff0c98f133f7aab89
passed

independent isolated-wheel API and CLI closure probe
semantic mixed: passed
parse mixed: passed
canonical issue order: passed
report-schema validation: passed
safe static issue shape and canary exclusion: passed
runtime socket audit: passed with zero events
```

The local gate and isolated probe used available CPython 3.12.13. The workflow still declares CPython 3.12.3; this review did not download or claim exact local reproduction of that CI interpreter.

## Conclusion

`DBX-P1.1-003` is resolved end to end at the reviewed immutable commit. The two earlier Databricks findings remain resolved, and no current P1.1 egress, cloud/compute mutation, evidence or Personal Data safety, bounded-input, CI/supply-chain, compute-scope, or P1.1/P2-boundary defect was identified. The verdict is `PASS_WITH_FOLLOW_UP` only for the explicitly deferred P2 collector and later release-packaging gates above.
