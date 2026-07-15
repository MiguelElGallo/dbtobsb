# Azure Databricks platform and security re-review: P1.1 artifact-pair inspector

- Commit/diff: `e5969edd822ea5ccb31171f6c74e0ba690fd2294` against the originally reviewed `054527a6721c36af6a9e99218120b39920bd0fed`
- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform and security reviewer
- Verdict: `PASS_WITH_FOLLOW_UP`
- Cloud activity: None. This re-review made no Azure, Databricks authentication, App, Jobs, SQL, warehouse, cluster, serverless-compute, or Unity Catalog call and did not mutate, start, stop, or delete any cloud resource.

## Scope and sources

This is an immutable-commit re-review of the two findings in `databricks-review.md`. Local tests and source inspection were repeated at the exact commit above. The timestamped cloud inventory in the committed evidence was reviewed as historical evidence but was not refreshed or independently reproduced, because this re-review was explicitly local and no-cloud.

The platform interpretation continues to use these first-party references:

- [Use dbt transformations in Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/how-to/use-dbt-in-workflows)
- [Configure task dependencies](https://learn.microsoft.com/en-us/azure/databricks/jobs/run-if)
- [Troubleshoot and repair job failures](https://learn.microsoft.com/en-us/azure/databricks/jobs/repair-job-failures)
- [Azure Databricks resource and Jobs API limits](https://learn.microsoft.com/en-us/azure/databricks/resources/limits)
- [Manage identities, permissions, and privileges for Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/privileges)
- [Work with files in Unity Catalog volumes](https://learn.microsoft.com/en-us/azure/databricks/volumes/volume-files)
- [Azure Databricks `ALTER TABLE` permissions](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-syntax-ddl-alter-table#required-permissions)
- [Databricks Apps key concepts](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts)
- [Pinned first-party Jobs run model](https://github.com/databricks/databricks-sdk-go/blob/bad015296869703de251d189b8a43ea4e6df8bfb/service/jobs/model.go#L3406-L3432), [repair history](https://github.com/databricks/databricks-sdk-go/blob/bad015296869703de251d189b8a43ea4e6df8bfb/service/jobs/model.go#L4435-L4474), and [dbt artifact-link headers](https://github.com/databricks/databricks-sdk-go/blob/bad015296869703de251d189b8a43ea4e6df8bfb/service/jobs/model.go#L251-L259)
- [Pinned first-party CLI Jobs output-retention contract](https://github.com/databricks/cli/blob/09b5514a57ebe905755eec9eb27b2566c65f269b/cmd/workspace/jobs/jobs.go#L943-L970)

No change in this commit modifies `databricks.yml`, the Databricks App, the P0 live-smoke wrapper, or a cloud resource definition. P1.1 remains a portable local slice rather than a claim of live dbt-on-Databricks qualification.

## Finding resolutions

### DBX-P1.1-001: Resolved — installed schema-resource boundary is now truthful and tested

- Original severity: Medium
- Resolution commit: `e5969edd822ea5ccb31171f6c74e0ba690fd2294`
- Re-review outcome: `RESOLVED`

The public and code contracts no longer claim that a fresh inspection performs no filesystem access. They now state the narrower, accurate boundary: `inspect_artifact_pair()` opens no caller-supplied path and reads only the two installed, checksum-pinned schema resources. They separately exclude network, environment, clock, subprocess, dbt, and Databricks access. The CLI's reads of two caller-selected, closed regular files remain a separate input-adapter responsibility.

The selected boundary is enforced in three complementary ways:

1. `test_fresh_inspection_reads_only_installed_checksum_pinned_schema_resources` clears the validator cache, audits the package-resource accessor, performs a valid inspection, and proves exactly two accesses anchored to `dbtobsb_capture`.
2. The vendored-schema test verifies the exact manifest-v12 and run-results-v6 SHA-256 constants before validation.
3. The full gate builds a wheel, installs it in an isolated environment, and invokes the installed console entry point. An additional local audit-hook probe against that installed wheel observed only `manifest-v12.json` and `run-results-v6.json` under the installed package's `schemas/` directory, with hashes matching the constants, and zero socket events.

The independent installed-wheel probe returned:

```text
PAIR_VALID
installed_schema_opens=manifest-v12.json,run-results-v6.json
socket_events=0
```

This closes the original ambiguity without weakening the customer-local boundary. Dependency acquisition remains explicitly classified as build/install egress: a regulated deployment must use an approved index, mirror, or populated cache. The product does not yet claim to ship a disconnected wheelhouse.

### DBX-P1.1-002: Resolved — compute evidence is timestamped, scoped, and includes active Jobs

- Original severity: Medium
- Resolution commit: `e5969edd822ea5ccb31171f6c74e0ba690fd2294`
- Re-review outcome: `RESOLVED`

The evidence no longer infers a workspace-wide absence of paid compute from Apps, warehouses, and classic clusters. It records a read-only inventory at `2026-07-15T21:54:20+03:00` through the existing secure OAuth profile: one stopped `dbtobsb-smoke` App, zero running Apps, zero SQL warehouses, zero classic clusters, and zero active Lakeflow Job runs. The active-Job check covers the previously omitted path by which serverless Job tasks can be running.

The record expressly limits this to a point-in-time observation of the listed compute classes visible to that profile and says it is not evidence about every possible Azure or Databricks billable service. It separately makes the stronger source-backed statement that P1.1 created, started, changed, or deleted no App, Job, warehouse, cluster, serverless compute, Unity Catalog object, or Azure resource and that the inspector makes no runtime network call.

This re-review did not refresh the historical inventory, so it does not claim that the workspace is idle now. The corrected point-in-time wording and inclusion of active Lakeflow runs satisfy the original finding without requiring a new paid run.

## Platform, data, and regulated-runtime assessment

The P1.1 production package has no Azure or Databricks SDK, network client, telemetry SDK, environment lookup, subprocess launcher, SQL client, Bundle mutation, or Unity Catalog mutation. Inspection is local after installation, returns a deterministic allowlisted report, and neither persists nor returns raw artifact bytes. The checked-in fixtures are synthetic and explicitly set `runtime_evidence=false` and `runtime_attestation=false`; they do not masquerade as customer or live Databricks evidence.

The fixture generator accepts only the reviewed, checksum-pinned synthetic source projection, validates its expected resource inventory, and rejects changed origin metadata or injected free text before producing output. Canary tests cover non-disclosure of SQL, messages, paths, identifiers, tokens, environment values, project/relation identity, and other non-allowlisted input. This supports the intended regulated boundary: customer data and normalized observability evidence remain customer-local, while no external telemetry platform or product-runtime egress is introduced.

The distinction between zero product-runtime egress and possible dependency-installation egress is now consistent across the plan, package README, tutorial, API reference, and workflow terminology. A first `uv sync` may require an approved package source; subsequent documented inspection commands use `--no-sync`.

## CI and supply-chain assessment

The capture workflow uses `pull_request` rather than `pull_request_target`, grants only `contents: read`, pins both GitHub Actions to full commit SHAs, pins uv `0.11.28`, disables the uv cache, declares CPython `3.12.3`, limits the job to ten minutes, and uploads no fixture, report, wheel, or test artifact. It contains no Databricks credential, authentication, or cloud call.

Runtime dependencies are exact in `pyproject.toml`, the lock contains distribution hashes, and the gate creates a seven-package runtime-only environment with `uv sync --locked --no-dev`. The isolated wheel install is a packaging smoke test; it does not replace the locked runtime path. The committed evidence records a manual `pip-audit==2.10.0` result, but this re-review did not reproduce that external-tool run and does not treat it as a current vulnerability attestation.

Two release-hardening items remain intentionally outside P1.1 acceptance: a fully qualified Python 3.12/Linux dependency graph and a disconnected, provenance-bearing wheelhouse/SBOM path. They are follow-ups, not evidence of runtime egress in the inspector.

## Non-blocking later-gate follow-ups

These items remain acceptance gates for the P2 collector or later release packaging. None is a defect in the P1.1 local inspector.

1. Fetch each task's output promptly; treat the pre-signed artifact link as short-lived, and never persist that URL or raw inline log output.
2. Budget, back off, and reconcile against the workspace-shared `runs/get-output` and `runs/output` quota of 20 requests per second.
3. Keep capture state `UNAVAILABLE` until a staged stable response proves archive absence; do not translate an expired/missing link, 403, transport error, or human-readable failure into `CONFIRMED_ABSENT`.
4. Treat `ALL_DONE` as a best-effort dependency trigger, not exactly-once delivery. The bounded reconciler must cover collector-never-started, cancellation, excluded/disabled tasks, retry, repair, and response-loss paths.
5. Qualify the exact native archive layout and custom target/log-path inclusion before freezing the Azure staging contract. Copy only policy-approved closed files to a Unity Catalog Volume; do not stream an active append-style log there.
6. Apply the Jobs result-visibility boundary to raw evidence. Ordinary product views must remain normalized and allowlisted, and secrets must never be printed to driver stdout/stderr as a redaction strategy.
7. Preserve the disclosed Unity Catalog authority boundary: table `MODIFY` includes schema-altering operations. Fixed DML-only code and lack of schema-level create grants reduce risk but do not turn `MODIFY` into a platform-enforced DML-only privilege.
8. Before distributable release, qualify the exact Linux lock and provide the approved disconnected-install/provenance/SBOM path promised by the release plan.

Owners: P2 collector owner for items 1–7; release-packaging owner for item 8. Targets: P2 bounded staging review and the later distributable-release gate, respectively.

## Local and read-only validation

All checks used exact commit `e5969edd822ea5ccb31171f6c74e0ba690fd2294`. No cloud command was run.

```text
scripts/check_capture.sh
81 passed in 2.44s
Ruff lint: passed
Ruff format: passed
ty: passed
fixture regeneration and byte-identical comparison: passed
seven-package runtime-only locked environment: passed
wheel build and isolated installed console entry point: passed
DBTOBSB_CAPTURE_CHECK_PASSED

bash -n scripts/check_capture.sh
passed

shellcheck scripts/check_capture.sh
passed

git diff --check 054527a6721c36af6a9e99218120b39920bd0fed..e5969edd822ea5ccb31171f6c74e0ba690fd2294
passed
```

The local full gate used the available CPython 3.12.13. The workflow declares CPython 3.12.3, but this re-review did not download that interpreter or claim an exact local reproduction of the CI runtime.

## Conclusion

Both blocking findings from the original Azure Databricks platform and security review are resolved at the reviewed immutable commit. No current P1.1 platform, regulated-data-boundary, compute-mutation, runtime-egress, or CI-permission blocker was identified. The verdict is `PASS_WITH_FOLLOW_UP` solely for the explicitly owned P2 retrieval/reconciliation/visibility gates and later release-supply-chain qualification above.
