# Azure Databricks platform and security review: P1.1 artifact-pair inspector

- Commit/diff: `054527a6721c36af6a9e99218120b39920bd0fed`
- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform and security reviewer
- Verdict: `CHANGES_REQUIRED`
- Cloud activity: None. This review made no Azure, Databricks authentication, App, Jobs, SQL, warehouse, cluster, serverless-compute, or Unity Catalog call and did not mutate or start any cloud resource.

## Sources checked

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

## Acceptance criteria reviewed

- P1.1 is one portable, local, independently testable slice and does not require Databricks, dbt, a warehouse, or paid compute at inspection time.
- The implementation and documentation do not claim Databricks archive retrieval, structured-log parsing, AttemptKey correlation, complete capture, or live-runtime qualification.
- Pair validity, native dbt outcome, Lakeflow outcome, and future capture state remain separate facts.
- Ordinary output is deterministic and allowlisted; raw artifacts, SQL, messages, environment values, paths, relation/resource identity, project identity, and invocation identity are not emitted.
- The required product path remains customer-local with no external telemetry platform and no inspector runtime egress.
- CI has a narrow permission and artifact boundary, and build/install egress is not confused with product-runtime egress.
- Cost and no-resource evidence is no broader than the inventory that supports it.
- P2 corrections preserve honest Azure Databricks semantics for task-run identity, archive absence, `ALL_DONE`, Unity Catalog `MODIFY`, and closed-file handling.

## Platform and security assessment

The inspected `capture/` package imports no Databricks or Azure client and contains no network client, subprocess launch, environment lookup, telemetry SDK, SQL, Bundle resource, or Unity Catalog mutation. The commit does not change `databricks.yml`, the App, or the P0 live-smoke wrapper. The P1.1 runtime therefore has no route to start Databricks compute or send evidence to an external telemetry service. The GitHub Actions job has `contents: read`, pins both actions by full commit SHA, disables the uv cache, has a ten-minute timeout, and uploads no fixture, report, wheel, or test artifact. Dependency and Python acquisition are still external build/install egress; the plan correctly keeps that separate from zero product-runtime egress.

The output boundary is also sound. A valid dbt error remains `PAIR_VALID` with native `error` status rather than becoming success, and no output claims `COMPLETE`. Synthetic fixtures carry explicit `runtime_evidence=false` provenance and canaries that the tests prove do not enter reports. The code does not retain raw artifact bytes in the returned report. This is appropriate for a regulated, customer-local path, subject to the first finding below.

The changed future-platform text is directionally correct:

- Native dbt task output must be fetched with the individual task run ID; inline logs can be truncated, and the artifact URL is temporary. P1.1 does not fetch or persist either.
- The new `(workspace_id, dbt_task_run_id)` uniqueness rule agrees with the first-party Jobs model: a run ID is unique across runs, each task has its own run ID, and repair history names the new task run IDs. Parent run, task key, attempt, repair, and original-attempt fields remain lineage and consistency evidence rather than alternative roots.
- `CONFIRMED_ABSENT` is correctly reserved until a stable staging response is qualified. Missing/expired links, access denial, transport failure, and human-readable errors remain unavailable rather than proven absent.
- `ALL_DONE` is a dependency condition, not durable exactly-once collection. The plan's separate reconciler and collector-never-started tests keep it from being the only recovery mechanism.
- The revised text no longer promises platform-enforced zero DDL authority. Azure Databricks documents that table `MODIFY` permits `ALTER COLUMN`, `ADD COLUMN`, `DROP COLUMN`, and table-property changes. Fixed DML-only collector code, lack of schema-level create grants, and disclosure of the collector/code-deployer/Job-manager trusted roots are the accurate boundary.
- Active append-style dbt logs stay task-local; any later Volume path receives only policy-approved closed files. No Volume is used in this part.

## Findings

### DBX-P1.1-001: The pure-API filesystem boundary is false

- Severity: Medium
- Affected files and behavior: `capture/src/dbtobsb_capture/inspector.py:349`, `capture/src/dbtobsb_capture/schemas.py:22`, `docs/plans/product-plan.md:526`, `docs/developers/reference/python-api.md:20`, and `capture/README.md:3`.
- Evidence: `inspect_artifact_pair()` says it runs without filesystem access and calls `validator_for()` at lines 376 and 379. On the first call for each schema, `validator_for()` executes `importlib.resources.files(...).joinpath(...).read_bytes()` at `schemas.py:32`. A fresh-process probe cleared the validator cache, replaced the package-resource accessor with a fixed sentinel, and a valid in-memory pair raised `PACKAGE_RESOURCE_READ_OBSERVED` from that exact line. The product plan and public API reference state that the function performs no filesystem access.
- User/system impact: The actual implementation is still local and customer-safe, but the frozen portable-architecture contract is wrong. A caller evaluating a read-denied, immutable, embedded, or specially packaged runtime could approve the API on the stated in-memory-only boundary and then receive an internal failure when the package schemas are read. In a regulated product, the declared evidence and dependency boundary must match the code.
- Required change: Choose and test one honest contract. Either (a) define checksum-pinned reads of installed package resources as an explicit internal dependency while preserving the stronger guarantee that the function never opens caller paths or performs network/Databricks access, and update every no-filesystem/pure claim, or (b) change packaging/loading so the function's documented no-filesystem behavior is true. Add a regression test that proves the selected boundary from a fresh validator state, then rerun the full gate.
- Resolution commit: Pending.
- Validation evidence: Pending a fresh-process boundary test plus the full P1.1 gate.
- Re-review outcome: Pending.

### DBX-P1.1-002: The no-paid-compute conclusion exceeds the recorded inventory

- Severity: Medium
- Affected file and behavior: `docs/evidence/p1.1-local-artifact-pair-2026-07-15.md:47`, cloud and cost evidence.
- Evidence: The record lists one stopped App, zero running Apps, zero SQL warehouses, and zero clusters, then concludes, “No paid compute was left running.” It records no active Lakeflow Job/task-run inventory. Azure Databricks documents that native dbt tasks can run on serverless Jobs compute by default; such active runs are not established absent by an App, warehouse, or cluster list. The sentence is therefore broader than the sanitized evidence preserved in this commit. This review did not make a cloud call and cannot retrospectively supply the missing evidence.
- User/system impact: The workspace is personally funded, and the repository's review process treats cost and cleanup truth as a safety boundary. An unsupported workspace-wide conclusion can hide ongoing serverless Job cost even though this P1.1 implementation itself starts no compute.
- Required change: Prefer the narrow, directly provable statement that P1.1 made no Databricks call and created or started no product/test resource. If the record intends a workspace-wide point-in-time claim, add timestamped sanitized evidence covering active Jobs/task runs and every compute class included by the claim, while distinguishing unrelated customer resources from P1.1-owned resources. Do not infer all paid compute from App, warehouse, and cluster inventory alone.
- Resolution commit: Pending.
- Validation evidence: Pending corrected wording or complete timestamped read-only inventory evidence. No new paid run is required.
- Re-review outcome: Pending.

## Non-blocking P2 gates

These items do not belong in P1.1 code, but they must be acceptance criteria for the P2 collector rather than inferred from this offline inspector:

1. Fetch task output promptly and never store the pre-signed artifact URL or raw inline log response. The first-party model describes artifact headers as valid for 30 minutes after the run finishes; Jobs output is not a durable evidence store.
2. Budget and back off `runs/get-output` against the fixed workspace quota of 20 requests per second shared with `runs/output`; reconciliation must not turn a missing capture into an API-rate-limit storm.
3. Preserve `UNAVAILABLE` until a staged, stable response proves absence. The public contract does not currently justify `CONFIRMED_ABSENT` from a missing link or error code.
4. Treat `ALL_DONE` as best-effort DAG triggering and keep bounded reconciliation authoritative for collector-never-started, cancellation, disabled/excluded-task, response-loss, retry, and repair cases.
5. Qualify the exact native archive layout and inclusion of generated target/log paths in Azure staging. Current public documentation promises packaged dbt outputs but does not freeze every tar entry or custom-path behavior.
6. Apply the Jobs result-visibility boundary to raw evidence. Users with Job result visibility can see run results, and secrets printed to driver stdout/stderr are not an acceptable redaction strategy; ordinary product views must continue to consume only normalized allowlisted fields.

Owner: P2 collector owner. Target: P2 implementation and bounded staging review.

## Local and read-only checks

All checks used commit `054527a6721c36af6a9e99218120b39920bd0fed`; the worktree was clean before this review record was added.

```text
git rev-parse HEAD
054527a6721c36af6a9e99218120b39920bd0fed

scripts/check_capture.sh
55 passed in 1.05s
Ruff lint: passed
Ruff format: passed
ty: passed
wheel build and installed console entry point: passed
DBTOBSB_CAPTURE_CHECK_PASSED

shellcheck scripts/check_capture.sh
passed

bash -n scripts/check_capture.sh
passed

git diff --check 054527a^ 054527a
passed
```

The local full gate used the available CPython 3.12.13. An exact 3.12.3 interpreter was not installed locally, so this review did not silently download one or claim to reproduce the workflow's exact Python runtime. The commit's CI declaration remains 3.12.3; its completed GitHub run, if any, was not used as evidence here.

The two required changes concern the truth of the public contract and cost evidence, not a detected Databricks mutation, telemetry route, raw-evidence leak, or failing local test. After both are resolved, re-run the local gates and request Databricks re-review of the new immutable commit.
