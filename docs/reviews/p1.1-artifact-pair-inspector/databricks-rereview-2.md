# Final Azure Databricks platform and security regression re-review: P1.1 artifact-pair inspector

- Commit/diff: `bedfaa9d9e803c168c2481d5e4f18264a1f40e01` against previously reviewed `e5969edd822ea5ccb31171f6c74e0ba690fd2294`
- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform and security reviewer
- Verdict: `CHANGES_REQUIRED`
- Prior re-review: [`databricks-rereview.md`](databricks-rereview.md), verdict `PASS_WITH_FOLLOW_UP` at `e5969edd822ea5ccb31171f6c74e0ba690fd2294`
- Cloud activity: None. This regression re-review made no Azure, Databricks authentication, App, Jobs, SQL, warehouse, cluster, serverless-compute, or Unity Catalog call and did not create, start, stop, modify, or delete a cloud resource.

## Scope and source basis

This review covers the exact immutable post-`e596` change. It inspected the closed Python report constructors, shared issue registry, generated JSON Schema, inspector integration, tests, two changed public references, and the changed evidence text. No platform implementation, Bundle resource, Databricks App, Job, collector, archive retriever, or Unity Catalog path changed.

The Databricks interpretation remains based on the first-party sources recorded in the prior review, including [dbt in Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/how-to/use-dbt-in-workflows), [Jobs API limits](https://learn.microsoft.com/en-us/azure/databricks/resources/limits), [Jobs permissions and result visibility](https://learn.microsoft.com/en-us/azure/databricks/jobs/privileges), and [Unity Catalog Volume files](https://learn.microsoft.com/en-us/azure/databricks/volumes/volume-files). No new platform semantic claim was introduced by this commit.

## Regression assessment

| Boundary | Outcome | Evidence |
| --- | --- | --- |
| `DBX-P1.1-001` installed-resource boundary | `REMAINS_RESOLVED` | The API still opens no caller path and reads only the installed checksum-pinned manifest-v12 and run-results-v6 schemas. An isolated installed-wheel audit observed exactly those two schema opens and zero socket events. |
| `DBX-P1.1-002` compute evidence scope | `REMAINS_RESOLVED` | The evidence retains the timestamp `2026-07-15T21:54:20+03:00`, zero active Lakeflow Job runs, the profile-visibility qualification, the point-in-time limitation, and the explicit statement that it is not an inventory of every billable service. This review did not refresh that historical observation or claim current workspace idleness. |
| Customer-local and runtime egress | `PASS` | Production changes add only local static contract validation and schema generation. No Azure, Databricks, network, telemetry, subprocess, environment, SQL, Bundle, or Unity Catalog client/path was added. Dependency installation remains a separate disclosed boundary. |
| Evidence confidentiality | `PASS` | The generated report schema remains closed to four top-level fields. Its 26 issue variants contain only the six static allowlisted issue fields; no observed value is interpolated. The new exception and CLI fallback are static and expose no artifact fragment, identifier, path, or exception detail. |
| Bounded evidence handling and report integrity | `FAIL` | A schema-valid, bounded pair with two ordinary evidence defects can now escape the documented `PAIR_INVALID` path as a constructor exception and CLI internal error. See `DBX-P1.1-003`. |
| CI and supply chain | `PASS` | `.github/`, `capture/pyproject.toml`, `capture/uv.lock`, `scripts/check_capture.sh`, `databricks.yml`, and the App are unchanged from `e596`. The existing read-only permissions, full action SHAs, uv pin, disabled cache, locked runtime-only sync, timeout, and no artifact upload remain intact. |
| P1.1 versus P2 boundary | `PASS` | This commit changes only local report construction. It still does not claim archive retrieval, structured-log parsing, AttemptKey correlation, live-runtime qualification, capture completeness, or `CONFIRMED_ABSENT`. The prior P2 artifact-link, rate-limit, reconciliation, archive-layout, closed-file, result-visibility, and Unity Catalog authority gates remain later work. |

## Finding

### DBX-P1.1-003: Canonical report enforcement turns valid multi-defect evidence into an internal error

- Severity: Medium
- Affected behavior: `capture/src/dbtobsb_capture/inspector.py:389-395`, `capture/src/dbtobsb_capture/inspector.py:482-488`, `capture/src/dbtobsb_capture/contracts.py:170-173`, and `docs/developers/reference/python-api.md:39`.
- Re-review outcome: `OPEN — CHANGES_REQUIRED`

The new `ArtifactPairReport` constructor correctly rejects issue tuples that do not follow `ISSUE_PRECEDENCE`. The inspector's `_invalid()` adapter does not establish that invariant: it deduplicates codes in encounter order and truncates them, then constructs the report directly.

That encounter order is not always registry order. For example, the inspector appends `DBT_TIMING_INVALID` for a bad top-level elapsed time before it appends `DBT_RESULTS_DUPLICATE_ID`, while the shared registry places duplicate-ID before timing. A probe started from the checked-in valid-success fixture, set `elapsed_time` to `-1`, and duplicated its one result. Both mutated documents still passed the vendored dbt schemas with zero errors. The public inspector then returned:

```text
manifest_schema_errors=0
run_results_schema_errors=0
exception=ValueError
message=issues must follow the closed v1 precedence
```

The same payload passed through the CLI control flow produced:

```text
exit=4
stdout=''
stderr='DBTOBSB_INTERNAL_ERROR\n'
```

The documented contract says expected evidence failures return `PAIR_INVALID` and do not raise. The stable CLI contract assigns invalid evidence exit `10`, not internal-error exit `4`. This input is below the size and nesting limits and is schema-valid; duplicate results and impossible timing are both explicitly modeled evidence failures. The new constructor therefore exposes an integration defect between two individually reasonable controls.

The failure does not leak evidence and cannot start Databricks compute or create runtime egress. It does, however, convert corrupt or adversarial dbt evidence into a product-internal failure, suppress the two specific recovery actions, and create an avoidable observability gap. That is a current P1.1 correctness and availability defect, so it blocks acceptance under the review policy.

Required change:

1. In the inspector's report-construction boundary, deduplicate all issue codes, sort them with the shared `ISSUE_PRECEDENCE` registry, and only then apply the 20-issue cap.
2. Add a public-API regression using a schema-valid pair with duplicate result IDs plus invalid timing. Require `PAIR_INVALID`, canonical issue order `DBT_RESULTS_DUPLICATE_ID` before `DBT_TIMING_INVALID`, safe static text, and successful validation against the bundled report schema.
3. Add the equivalent installed-entry-point regression and require exit `10`, not exit `4`.
4. Cover differently ordered per-result defects or otherwise prove that every reachable multi-issue inspector report is canonical before construction; rerun the full gate.

- Resolution commit: Pending.
- Validation evidence: Pending the targeted API and installed-CLI regressions plus the full local gate.

## Controls that did not regress

The post-`e596` schema work materially improves the public-construction boundary. It rejects invented states and object types, non-tuples, more than 20 issues, duplicates, wrong issue text, and noncanonical public issue order. The generated JSON Schema keeps state/summary cardinality closed, defines every static issue variant, rejects duplicate issues, and prevents a later-precedence primary issue when an earlier one is present. Those controls should remain; the required correction belongs at the inspector-to-constructor integration boundary.

The installed-wheel runtime probe returned:

```text
PAIR_VALID
installed_schema_opens=manifest-v12.json,run-results-v6.json
socket_events=0
```

No new production import can open a network connection or call Azure/Databricks. Raw artifacts remain outside returned reports; fixtures remain synthetic with `runtime_evidence=false` and `runtime_attestation=false`; canary and adversarial-source tests still pass. The changed evidence file updates test/link counts only and preserves its honest compute and runtime-qualification limits.

The prior non-blocking P2 gates also remain correctly deferred: short-lived task artifact links and raw output must not be persisted; Jobs output calls need bounded rate-aware reconciliation; `CONFIRMED_ABSENT` needs stable staged evidence; `ALL_DONE` is not exactly-once delivery; archive/custom path layout and closed-file Volume handling require qualification; and Jobs result visibility constrains raw evidence. None excuses the current local-constructor regression.

## Local and read-only validation

All checks used exact commit `bedfaa9d9e803c168c2481d5e4f18264a1f40e01`. No Databricks or Azure command was run.

```text
scripts/check_capture.sh
85 passed in 2.46s
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

git diff --check e5969edd822ea5ccb31171f6c74e0ba690fd2294..bedfaa9d9e803c168c2481d5e4f18264a1f40e01
passed

targeted schema-valid multi-defect API probe
failed contract: ValueError instead of PAIR_INVALID

targeted CLI control-flow probe
failed contract: exit 4 DBTOBSB_INTERNAL_ERROR instead of exit 10
```

The green 85-test gate is genuine but lacks the multi-defect integration case above. The local gate used available CPython 3.12.13; this review did not download or claim exact local reproduction of the workflow's declared CPython 3.12.3.

## Conclusion

The prior filesystem/resource boundary and compute-scope findings remain resolved, and no customer-local, runtime-egress, evidence-confidentiality, cloud-mutation, CI-permission, supply-chain, or P1.1/P2-scope regression was found. `DBX-P1.1-003` is nevertheless a present P1.1 correctness and bounded-evidence-handling defect. Fix it at a new immutable commit and request another Azure Databricks platform/security re-review; the verdict for `bedfaa9d9e803c168c2481d5e4f18264a1f40e01` is `CHANGES_REQUIRED`.
