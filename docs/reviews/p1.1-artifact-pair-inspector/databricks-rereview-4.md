# Final Azure Databricks platform and security re-review: P1.1 overwrite-safe contract

## Review record

| Field | Value |
| --- | --- |
| Reviewed commit | `cff8bbcd808ff7e13a7ead182543a2564cd04ff6` |
| Reviewed tree | `a3802ab9b14a1dc3b7f18f90255eee349fdeecbb` |
| Immediate parent | `8711aa803016b5d732553756c5e71542e0a928bf` |
| Prior Databricks closure baseline | `75b7d41316216a3b18a3c56ff0c98f133f7aab89` |
| Overwrite-safe source correction | `2367a05d4e9ddb763cc52a3b7090c4099a639631` |
| Correction parent | `08de2ddb3429bb675b6587de4c225bbf93102a1f` |
| Review date | 2026-07-15 |
| Review role | Independent Azure Databricks platform and regulated-product security reviewer |
| Verdict | **PASS_WITH_FOLLOW_UP** |
| New current-part findings | None |
| Prior Databricks findings | `DBX-P1.1-001`, `DBX-P1.1-002`, and `DBX-P1.1-003` remain resolved |
| Workspace and cloud activity | None. No Azure or Databricks authentication, CLI, workspace API, App, Jobs, SQL, warehouse, cluster, serverless-compute, Unity Catalog, or resource mutation call was made. No paid compute was started. Public documentation was read over the web. |

## Executive verdict

The P1.1 artifact-pair inspector remains a bounded, offline-after-installation,
operator-host-local slice. The production package still has no Azure or
Databricks SDK, network or telemetry client, SQL client, environment lookup, or
subprocess launcher. Its public API opens no caller path, reads only two
installed checksum-pinned schemas, and returns a closed allowlisted report. The
CLI adds bounded reads of two caller-selected closed regular files and uses
static, evidence-safe errors.

The corrected invocation guidance is materially safer than the superseded
directory-based text. It requires two closed artifacts from one completed
pinned `dbt build` invocation, collected before another dbt command can
overwrite the target. It does not use directory co-location as identity and
does not say that a valid pair is authentic, unmodified, in custody, complete,
or tied to a verified Databricks task attempt.

The two changed issue variants agree byte-for-byte across the runtime registry,
generated JSON Schema, generated fixture, machine output, tutorial, CLI
reference, recovery guide, and executable documentation tests. An independent
probe confirmed parity for all 26 issue variants, safe fixture output, and zero
socket or process audit events. The complete local gate passed with 96 tests.

No prior Databricks blocker regressed. Native archive retrieval, task-attempt
correlation, `AttemptKey`, structured logs, live Azure Databricks runtime
qualification, customer-Databricks-local custody, and capture-state claims
remain explicitly outside P1.1. Those follow-ups explain the
`PASS_WITH_FOLLOW_UP` verdict; they are not current-part defects.

## Current first-party source basis

The platform and dbt boundary was rechecked on 2026-07-15 against current
first-party documentation:

- [Use dbt transformations in Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/how-to/use-dbt-in-workflows),
  updated 2026-07-06, distinguishes the dbt Core process and generated SQL from
  Lakeflow orchestration and compute. It documents automatic artifact
  archiving, inline logs, a packaged-artifact download link, truncation state,
  and retrieval by the individual dbt task run ID rather than a multi-task
  parent run ID.
- [dbt task for jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/tasks/dbt),
  updated 2026-06-29, documents the native dbt task, its Run-as credential
  injection, compute and warehouse permissions, and the recommendation to pin
  `dbt-databricks` for reproducible development and production behavior.
- [Manage identities, permissions, and privileges for Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/privileges),
  updated 2026-04-09, documents that `CAN VIEW` exposes job run results and
  warns that secrets written to driver stdout or stderr are not automatically
  redacted. This supports keeping raw logs and artifacts outside ordinary
  reports and support payloads.
- [dbt JSON artifacts](https://docs.getdbt.com/reference/global-configs/json-artifacts)
  documents that JSON artifacts default to `target/`, that the target path can
  be overridden per invocation, and that a later operation can overwrite
  earlier artifacts.
- [dbt logs](https://docs.getdbt.com/reference/global-configs/logs) documents
  separate console and file logs and invocation-level `--target-path` and
  `--log-path` overrides. P1.1 does not parse or collect those logs.

These sources do not establish the layout of every native archive entry,
custom-path inclusion, a stable absence response, or durable task-attempt
correlation. This review therefore does not convert those future qualification
items into P1.1 claims.

## Exact immutable scope and hashes

The primary review set below is path ordered. Each value is the SHA-256 of the
exact blob at `cff8bbc`, obtained through `git show`. The aggregate is the
SHA-256 of the displayed newline-terminated `<sha256>  <path>` rows in this
order.

| Path | SHA-256 |
| --- | --- |
| `README.md` | `0be609fbbb0239d7dbb1142dcd630fa94f0a7b13ba9af7940b65f08d9d48c5cf` |
| `capture/README.md` | `d664454aa140415fc822398a217d62bb57cffc41c647fee46da98213fa0e6e19` |
| `capture/scripts/generate_artifact_pair_fixtures.py` | `3a55f3869616f8db19b8771081efe0b329d88bc080f648f471da3ac908a59de3` |
| `capture/scripts/generate_report_schema.py` | `a3b0a877110617e10d27d11893b34e65633279b77fd1cd7b547c10c396e44ad9` |
| `capture/src/dbtobsb_capture/cli.py` | `d05d272ead702943221a4e337c4708af21db7c07607b734c8ed30b18f70bc4f1` |
| `capture/src/dbtobsb_capture/contracts.py` | `6f312022cfbf58b4a11232963e06e406e81da9c8ba42f55c331529f5a257b5f9` |
| `capture/src/dbtobsb_capture/inspector.py` | `d80955b8575ff12d5daf2d6d26bf3e4b49f79a2d0beb910ef5aed961db7ffdaf` |
| `capture/src/dbtobsb_capture/registry.py` | `561f7a81bcb0fe7a9d1d2a8364228d39f88f758a83c34889c7e4480f60d5c1a6` |
| `capture/src/dbtobsb_capture/schemas.py` | `d9a03b0c53e3346031520abef9b22094733402d64bbed1337665623621965029` |
| `capture/src/dbtobsb_capture/schemas/artifact-pair-report-v1.json` | `a57bd0c63cfb846ea4282e686ff859892465b501eff6ae132b8650503d2eddc0` |
| `capture/tests/fixtures/artifact_pair/invalid_invocation_mismatch/expected-report.json` | `05cadb8737782e4eb35af90bfff48dfd41db86de12bca95cc7702651c677ee9c` |
| `capture/tests/test_artifact_pair.py` | `203f4a7ba9f445330c9a9807fc19b15cec125a7d4241b80fe4d9380005cd795b` |
| `capture/tests/test_cli.py` | `b8f620560cc16ec77935c306ac4ef10b40a29ed16bb6864ba94c9ad2e4bcb29d` |
| `capture/tests/test_documentation.py` | `8dab5bf14843fef5ae4bc86a2335ae3912fe18c9ba88175302fdff0b7e160b99` |
| `docs/decisions/0002-correct-p1.1-invocation-recovery-text.md` | `946d6ca04d362d5a25606f0306114b2776d2479376ab300899ca4bc0019614d1` |
| `docs/developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md` | `0ce8f5dc9fe7e426fbcd65b2b09b8bdf30b5230f29cb288c14836d423c88fda1` |
| `docs/developers/explanation/raw-artifact-custody.md` | `653d6befeb6791974362e5ceb29cedd14980cf92b01a92f4eb2981e1c822b990` |
| `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md` | `e2befb7ad8648db1cfd71ec9e4f9eba4a44a78a2c67fb2cb7233fece097c4531` |
| `docs/developers/how-to/handle-raw-dbt-artifacts-safely.md` | `539ac1e3e1c208b52d6e486a1c87b788e73b92f1f4b7d4e5d30724022908e920` |
| `docs/developers/index.md` | `8867bd6d28b38d7c22bfe1bb2c2affead9b737f64311b8c7d2c519544d6c0ceb` |
| `docs/developers/reference/cli-report-and-exit-codes.md` | `bb4c28a5c50988e4ddc17e90c462b3d86de145ecec8d1c06e78f19ed97c30323` |
| `docs/developers/reference/python-api.md` | `7c5e2ca891124cfb9b60f6184983fb97a963ec26339c1decce4e40dba14e9c82` |
| `docs/developers/tutorials/inspect-an-artifact-pair.md` | `35b778b40eda2880b837a2d5c5d517c55ac9593e41d6aacf3815f76ba5c6a12d` |
| `docs/evidence/p1.1-local-artifact-pair-2026-07-15.md` | `84fcc96227afab551e07c0ed7194d13e8fa299e7210bebb132ef5b875b076eab` |
| `docs/index.md` | `555ea21e8de979ad539024e0856275b9741cd377253a5285fa2779ee12288849` |
| `docs/plans/product-plan.md` | `00e410370497edc3b55bfb2ee9491eeb91512dca64b81d44543c0f04c72076eb` |

Primary review-set aggregate:
`c2dc8aff91a44285ad9d2803f20f31815c6e9ac2f23eac2e3ac85a86738f4122`.

The unchanged validation set was also bound to the exact commit:

| Path | SHA-256 |
| --- | --- |
| `.github/workflows/capture.yml` | `53fae7a7b79d7d7c52ea89737bc764a461a1faff523a303f7f4e547b1a1f94dc` |
| `capture/pyproject.toml` | `69f1367bf81be14cf166626251e734854655871c95dd1624015c11a10e2a8935` |
| `capture/uv.lock` | `fb09543bcd8cbca30786135e5879465181efd8d0e6e92b452d1bfffcba68b461` |
| `scripts/check_capture.sh` | `92656cda84b66dd76338cec050c35e632ae50de015bda89e474d28a74854b911` |
| `scripts/check_markdown_links.py` | `aa904ffdd5540d2604b840c42d8d04660c03c57e0d1f818355fc524dbd40b0c0` |

Validation-set aggregate:
`29b73d05f314bd41e41f198c444b1749aec58cf524a8d1f6a71dcdac13556cbe`.

The four prior Databricks reports were treated as immutable finding history.
Their path-ordered aggregate is
`3d82ca83a95daef59a9ed56eecff6330a74682ea0839e83e86be25c7f09c3ae9`.

## Platform and security assessment

| Boundary | Outcome | Evidence |
| --- | --- | --- |
| Operator-host-local inspection | `PASS` | The API receives caller bytes, opens no caller path, reads only installed schema resources, and has no external-service client. The CLI reads only the two selected regular files. |
| No Databricks call or compute | `PASS` | No SDK/client/resource path exists in the package. The audit observed zero socket and process events. No authenticated platform call or paid compute was used in this review. |
| Raw-data and Personal Data boundary | `PASS` | Raw bytes are parsed transiently but never retained in the report. SQL, messages, adapter responses, variables, paths, environment values, relation/project/resource/invocation identities, and fixture canaries remain excluded. |
| Safe static errors | `PASS` | All issue fields come from the closed registry. CLI read/internal failures suppress paths, exceptions, and evidence fragments. The changed invocation issues contain no observed value. |
| Databricks versus dbt semantics | `PASS` | `PAIR_VALID` is internal dbt artifact-pair validity; native dbt status counts are separate; outer Lakeflow task state and capture completeness are not inferred. |
| Overwrite-safe recovery | `PASS` | Recovery requires one completed pinned build, an empty attempt-specific target path, closed artifacts, and collection before another command. Directory co-location is not the pairing key. |
| Generated contract parity | `PASS` | All 26 runtime issue templates equal their generated Schema constants; fixtures and displayed output agree; every closed issue validates under the report schema. |
| Future archive, attempt, and runtime claims | `PASS` | Archive retrieval/layout, custom paths, `AttemptKey`, structured logs, runtime qualification, and capture state are explicitly deferred. |
| Customer-local product claim | `PASS` | Documentation distinguishes the current workstation/operator-host-local slice from the future Databricks-local customer product. It does not use this local test as custody attestation. |
| Decision 0002 pre-release treatment | `PASS` | The accepted decision governs this static-text correction before release; generated and executable contracts were regenerated and checked; required specialist closure now exists; no contrary release evidence was found. |

## Overwrite-safe invocation contract

The two invocation variants now use this one static action:

```text
Collect both closed artifacts from one completed pinned dbt build invocation before another dbt command runs.
```

The mismatch impact is:

```text
The files do not have the same dbt invocation identity.
```

This language has four security properties:

1. It does not interpolate either invocation ID, a path, or any artifact value.
2. It says identity differs rather than claiming an untrusted, forged, or
   platform-invalid Databricks run.
3. It accounts for dbt's reused-target overwrite behavior and tells the operator
   to collect after the producing invocation closes and before another command.
4. It preserves the implemented equality invariant: two parseable
   `metadata.invocation_id` values must match. A common directory is neither
   necessary nor sufficient pairing evidence.

The recovery guide additionally asks for an empty attempt-specific target path.
That is an operator procedure for obtaining a clean candidate pair, not a claim
that P1.1 creates a Databricks attempt root, retrieves the native archive, or
authenticates provenance. `PAIR_VALID` remains limited to the pinned schemas and
implemented cross-file invariants.

## Raw evidence and customer-local boundary

The safe report does not declassify its inputs. Real dbt artifacts can carry
Personal Data, SQL, credentials, messages, local paths, database and relation
topology, project/resource/invocation identities, and operational metadata.
P1.1 provides no upload endpoint and performs no durable raw-artifact copy,
retention, deletion, or legal-hold action.

The current custody boundary is stated precisely:

- the Python API receives caller-owned bytes;
- the CLI opens two caller-selected closed regular files with bounded,
  nonblocking, no-follow handling;
- the report retains only allowlisted state, schema/version/adapter/command,
  native status counts, and static issue text; and
- originals, temporary copies, backups, support handling, retention, deletion,
  and legal hold remain customer responsibilities.

This implementation runs on the approved operator host. That is customer-local
processing in the ordinary ownership sense, but it is not yet the target
product's Databricks-local custody architecture. The documentation explicitly
keeps archive retrieval, collector storage, runtime retention, deletion, and
uninstall for later reviewed parts.

## Databricks and dbt facts remain separate

Current Databricks documentation describes a native dbt task as a dbt Core
process orchestrated by Lakeflow Jobs and backed by selected compute and a SQL
warehouse. It separately exposes outer task metadata, inline logs, truncation,
and an archived-artifact link through task-run output.

P1.1 consumes none of those platform surfaces. It inspects only `manifest.json`
and `run_results.json` bytes supplied by the caller. Consequently:

- `adapter_type=databricks` is a dbt manifest fact, not proof of a live
  Databricks task;
- `status_counts` preserves native dbt resource outcomes, not Lakeflow state;
- a successful Lakeflow task cannot repair an invalid artifact pair;
- a valid pair can contain a native dbt `error`, `fail`, or `warn`; and
- neither result establishes `COMPLETE`, `CONFIRMED_ABSENT`, or any future
  capture-state label.

This distinction is necessary for a regulated observability product: outer
platform state, artifact-pair validity, native dbt outcome, and capture
completeness are four separately evidenced facts.

## Prior Databricks blocker regression check

### `DBX-P1.1-001` remains resolved

The API still opens no caller-supplied path and reads only
`manifest-v12.json` and `run-results-v6.json` from the installed package. The
fresh-validator test passed, and the independent audit observed zero socket and
process events. The public docs retain the same honest installed-resource
qualification; no absolute no-filesystem claim returned.

### `DBX-P1.1-002` remains resolved

The historical evidence still scopes its inventory to
`2026-07-15T21:54:20+03:00`, the listed classes visible to that profile, and a
point-in-time observation. It includes zero active Lakeflow Job runs and
expressly disclaims coverage of every billable Azure or Databricks service.
This review did not refresh that historical inventory and does not claim that
the workspace is idle now. The stronger current statement is source based:
P1.1 and this review created, started, changed, or deleted no platform resource.

### `DBX-P1.1-003` remains resolved

Inspector issue canonicalization still deduplicates and sorts through the
shared precedence registry before applying the 20-issue cap and constructing a
report. The changed invocation strings do not touch this control. Mixed-invalid
API and installed-CLI regressions, every issue-pair ordering case, and closed
Schema/Python parity all passed in the complete gate.

No new Databricks platform or security finding was identified.

## Decision 0002 and pre-release scope

[Decision 0002](../../decisions/0002-correct-p1.1-invocation-recovery-text.md)
is accepted and narrowly scoped to the two static invocation issue variants in
`dbtobsb.artifact-pair-report.v1`. It records that the candidate had not been
distributed, released, or accepted by an external consumer and requires
regeneration, byte checks, executable gates, immutable review history, and dbt,
usability, and security re-review before release.

The local repository has no tag, tracked wheel, release/publish workflow, or
PyPI upload configuration. That establishes absence of the ordinary repository
release surfaces; it cannot independently prove the absence of every private
out-of-band copy. Decision 0002 remains the accountable record for the stronger
external-consumer statement, and no contradictory repository evidence was
found.

The post-correction requirements are now represented by:

- the dbt documentation closure review at correction commit `2367a05`, verdict
  `PASS`;
- the final source usability closure at `8711aa8`, verdict
  `PASS_WITH_FOLLOW_UP`, with both source findings closed; and
- this post-correction Azure Databricks platform/security review at `cff8bbc`,
  which rechecks static-text safety, raw-data non-disclosure, local egress,
  generated-contract parity, and future-platform non-claims.

The earlier custody-focused security documentation review remains valid for
its reviewed source set, but it is not being misrepresented as the
post-correction security evidence. This report supplies that final security
regression check. Any equivalent text change after release still requires a new
contract-version decision and consumer migration analysis.

## Explicitly deferred gates

The following remain later product or release gates, not P1.1 capabilities:

1. qualify real Azure Databricks native archives for success, dbt failure,
   early failure, cancellation, timeout, retry, and repair;
2. freeze native archive retrieval and layout, custom target/log-path
   inclusion, link lifetime handling, and a stable absence response before
   `CONFIRMED_ABSENT` exists;
3. implement task-attempt and `AttemptKey` correlation, structured-log parsing,
   customer-evidence hashes, durable reconciliation, and capture-state logic;
4. qualify the exact Python 3.12/Linux dependency lock in the actual
   Databricks execution image and the disconnected/mirrored distribution path;
5. implement and review Databricks-local raw-evidence storage, access,
   retention, deletion, legal hold, export, and uninstall; and
6. preserve Jobs result-visibility and raw-log confidentiality controls when a
   collector is introduced.

Owners remain the later collector/runtime, security, and release-packaging
parts. None may be inferred from this local report.

## Local and read-only validation

All runtime and repository checks used exact commit
`cff8bbcd808ff7e13a7ead182543a2564cd04ff6`. No Databricks or Azure command was
run.

```text
focused boundary suite
9 passed

independent static-contract and runtime audit
issue_variants=26
generated_schema_parity=passed
fixture_snapshot_parity=passed
safe_static_invocation_text=passed
raw_canary_exclusion=passed
socket_events=0
process_events=0

scripts/check_capture.sh
96 passed in 5.12s
tracked_markdown_files=128
local_links=212
fragments=59
errors=0
Ruff lint: passed
Ruff format: passed
ty: passed
fixture byte-identical regeneration: passed
seven-package runtime-only locked install: passed
wheel build and isolated installed CLI: passed
DBTOBSB_CAPTURE_CHECK_PASSED

uv lock --check --project capture
passed

bash -n scripts/check_capture.sh
passed

shellcheck scripts/check_capture.sh
passed

git diff --check 08de2dd...cff8bbc
passed

platform/resource/dependency no-diff check from 75b7d41 to cff8bbc
databricks.yml, app/, .github/, capture dependency files, CLI,
contracts, registry, and installed-schema loader: unchanged
```

The full local gate used available CPython 3.12.13. It does not qualify the
planned CPython 3.12.3 Databricks runtime. Temporary environments and the wheel
were created under the gate's temporary directory and removed by its cleanup
trap.

## Verdict

**PASS_WITH_FOLLOW_UP**

The overwrite-safe invocation correction is static, evidence-safe, generated
and documented consistently, and properly limited to dbt artifact-pair
identity. The offline/operator-host-local boundary, no-platform-call behavior,
raw-data non-disclosure, Databricks-versus-dbt distinction, and all three prior
Databricks finding closures remain intact at exact commit `cff8bbc`. Decision
0002 is acceptable for this pre-release v1 correction, and its final
post-correction platform/security review requirement is satisfied here.

Only the explicitly deferred collector, native-archive, task-attempt,
Databricks-runtime, Databricks-local custody, and release-packaging gates remain.
