# Security and truthful-claims audit: P1.1 final resolution and review index

## Audit record

| Field | Value |
| --- | --- |
| Audited commit | `74a9cdf8e2b9da44015a134fffc6b13d66395453` |
| Audited tree | `106aa4421db895ae45623aefb72f24b7bab1ac14` |
| Immediate parent | `a00d6abde507210948b5fb7eaf566448e4ad6bc7` |
| Frozen source named by the resolution | `cff8bbcd808ff7e13a7ead182543a2564cd04ff6` |
| Audit date | 2026-07-16 |
| Audit role | Independent Databricks platform, security/compliance, and truthful-claims auditor |
| Verdict | **CHANGES_REQUIRED** |
| Current findings | One resolution wording finding; no implementation, raw-data, egress, compute, review-index, or deferred-gate regression |
| Cloud activity | None. No Azure or Databricks authentication, CLI, workspace API, App, Job, SQL, warehouse, cluster, serverless-compute, Unity Catalog, or cloud mutation call was made. No paid compute was started. |

## Executive verdict

The final resolution and review index correctly bind the accepted P1.1 slice to
the immutable source at `cff8bbc`. Their recorded implementation,
documentation, and latest-review aggregates reproduce exactly. Both verdict
tables point to the same nine reports with the same verdicts, and each target's
current verdict matches the table. All five `PASS_WITH_FOLLOW_UP` reports name
later nonblocking gates rather than unresolved defects in the local inspector.

The accepted scope is otherwise stated honestly. P1.1 is an
offline-after-installation local artifact-pair inspector, not a Databricks
collector, complete capture, qualified production runtime, disconnected
distribution, or Marketplace release. Runtime archive retrieval, `AttemptKey`,
structured logs, native Job evidence, full capture-state logic, the complete
Python 3.12/Linux distribution, and rendered/browser/keyboard/screen-reader/WCAG
publication validation remain explicitly gated.

The no-compute, local-inspection, and raw-evidence boundaries also remain
truthful. The production package has no Databricks or dbt runtime call, network
client, environment lookup, clock, or subprocess dependency during inspection.
Ordinary output remains allowlisted, while caller custody, Personal Data,
support, retention, deletion, legal hold, and workstation-local versus future
Databricks-local distinctions remain explicit.

One current authoritative sentence is inaccurate, however. The resolution
calls the resource/status compatibility contract an exact “Databricks `build`
matrix.” The frozen implementation and the latest dbt review establish that
matrix from dbt Core 1.11.12 `BuildTask.RUNNER_MAP`, `RunStatus`, and
`TestStatus`; `adapter_type=databricks` and `command=build` are separate pair
invariants. The wording collapses the dbt-versus-Databricks distinction that
the rest of the accepted contract carefully preserves.

Because this defect is in the current final resolution rather than a later
product gate, `PASS_WITH_FOLLOW_UP` would be inappropriate under the review
index's own rule. The underlying P1.1 implementation remains accepted from the
already completed specialist reviews, but this final resolution/index audit is
`CHANGES_REQUIRED` until the sentence is corrected and re-reviewed at a new
immutable commit.

## Exact audited scope and hashes

The two audited files are outside the resolution's frozen inputs by design.
Their SHA-256 values at exact commit `74a9cdf` are:

| Audited file | SHA-256 |
| --- | --- |
| `docs/reviews/README.md` | `275e28fc30017f155305257cf621be85afc843522d44520dcb397f13b8d483ba` |
| `docs/reviews/p1.1-artifact-pair-inspector/resolution.md` | `8cef3ae575ee7985eb369dc17cd19dd1ef69553f1a1c3956a80b5d2136e2f308` |

The path-ordered two-file `shasum -a 256` record-stream aggregate is
`9f04e43e6bd982a7e97e12df3af3710ba4cdc6c81b15231eb565fcab6d525a0e`.

The three frozen aggregates recorded in the resolution were independently
reproduced from its named source commit:

| Frozen input | Count and order | Recorded and reproduced SHA-256 |
| --- | --- | --- |
| Capture implementation and gates | 48 total path-sorted files: 45 under `capture/` plus the capture workflow and two gate scripts | `eed53519381de61685832eaf61e713eec0f8ad0b45a37fccd3e0b563a12024ce` |
| P1.1 developer documentation | 14 path-sorted entry, developer, evidence, decision, and documentation-plan files | `3731146dfe3890192c74f23fc39e207b0df714433369afb2973a63f9c32ae6f6` |
| Latest authoritative reviews | Nine reports in the resolution-table order | `d8225ab1886dcff00a5f791dc718381ec23e638f2705e0ebd0d37730b61c5625` |

The nine latest report blobs are:

| Latest report | SHA-256 |
| --- | --- |
| `databricks-rereview-4.md` | `b5d89552394b5e5ad047d32017e47bb9d930f1f835e9f58974a910ceede5d024` |
| `dbt-core-rereview-4.md` | `316efb6850d7759a2fdfa4a1d61cf164b0d79778899770dcb103746cec4d703c` |
| `usability-rereview-4.md` | `8e13be26f5d5caa2708c88f6e9650ff823ab92dac7de5401127488cdbec388e4` |
| `documentation-ia-rereview-2.md` | `0ac0ef4e9e29bbc4ca6f3005d630b836934e28ab85cdc159cf2712b668cd7c44` |
| `documentation-security-rereview-2.md` | `914af86b68d7cf578f7f8a532c35fdeca2b74e23b733d295d8c850bbdbd6454a` |
| `documentation-style-rereview-2.md` | `d0d531b5724ef641279730280745b7a8a75a4fe50bb145f502f0af88e45d5791` |
| `documentation-dbt-rereview.md` | `b824d7721e442678b9843832cb87bdbd6c3e186fec1a976310a76678a9480745` |
| `documentation-usability-rereview-2.md` | `b2326a65d2d2babe8b49e55fd43950b28c420c07d7eed755b09f7cb854cf1a3d` |
| `documentation-final-rereview.md` | `e09e54fda8185b44fd327a4256fd040fce8b3fc1d479766da484e7d27dd6150e` |

Decision 0002 has SHA-256
`946d6ca04d362d5a25606f0306114b2776d2479376ab300899ca4bc0019614d1`.
The validation scripts remain bound by SHA-256
`92656cda84b66dd76338cec050c35e632ae50de015bda89e474d28a74854b911`
for `scripts/check_capture.sh` and
`aa904ffdd5540d2604b840c42d8d04660c03c57e0d1f818355fc524dbd40b0c0`
for `scripts/check_markdown_links.py`.

## Resolution and index consistency

### Frozen inputs and latest-report table

The resolution's three aggregate records are reproducible, including the
stated path order. The 48-file count is the total across 45 `capture/` files,
`.github/workflows/capture.yml`, `scripts/check_capture.sh`, and
`scripts/check_markdown_links.py`; it is not an unsupported claim that all 48
live below `capture/`.

The resolution and index each contain nine P1.1 verdict rows. Their target
filenames and verdicts agree in order:

| Review lens | Target | Verified current verdict |
| --- | --- | --- |
| Databricks platform/security | `databricks-rereview-4.md` | `PASS_WITH_FOLLOW_UP` |
| dbt Core/artifact contract | `dbt-core-rereview-4.md` | `PASS_WITH_FOLLOW_UP` |
| Product usability/onboarding | `usability-rereview-4.md` | `PASS_WITH_FOLLOW_UP` |
| Diátaxis information architecture | `documentation-ia-rereview-2.md` | `PASS_WITH_FOLLOW_UP` |
| Security/compliance documentation | `documentation-security-rereview-2.md` | `PASS` |
| FastAPI-style writing | `documentation-style-rereview-2.md` | `PASS` |
| dbt subject-matter documentation | `documentation-dbt-rereview.md` | `PASS` |
| Documentation usability/accessibility | `documentation-usability-rereview-2.md` | `PASS_WITH_FOLLOW_UP` |
| Final reader-journey consistency | `documentation-final-rereview.md` | `PASS` |

The index shortens “Product usability/onboarding” to
“Usability/onboarding,” but the link and verdict are identical and the target's
scope is unambiguous. This is not a finding.

Earlier `CHANGES_REQUIRED` reports remain in the directory as immutable failed
history. The index does not rewrite them or present them as current. The final
resolution's statement that there is no open P1.1 blocker is supported by all
nine current target verdicts and dispositions, subject only to the new
resolution wording finding in this audit.

### `PASS_WITH_FOLLOW_UP` use

There are five current `PASS_WITH_FOLLOW_UP` targets. Each states that no
current source or P1.1 part defect remains and assigns its follow-ups to a later
gate:

- Databricks runtime, archive, task-attempt, Databricks-local custody, and
  release packaging;
- dbt runtime, compatibility, capture/correlation, and release readiness;
- product distribution, rendered documentation, and real Databricks journeys;
- rendered-site information architecture, search, accessibility, and
  publication; and
- complete-site browser, assistive-technology, and WCAG validation.

That usage satisfies the index rule that `PASS_WITH_FOLLOW_UP` is acceptable
only when the item does not block the reviewed slice. None of those later gates
may be used to waive a current defect in the resolution itself, which is why
this audit uses `CHANGES_REQUIRED`.

## Accepted scope versus production nonclaims

The resolution begins with the correct two-part disposition:

- accepted: the offline-after-installation local artifact-pair inspection
  slice; and
- not accepted: a live Databricks collector, complete capture, qualified
  production runtime, disconnected distribution, or Marketplace release.

The review index repeats the critical restriction: later gates do not permit
P1.1 to claim complete capture or a qualified production runtime. This is
consistent with the frozen README, developer entry point, evidence record, and
specialist reviews.

The local inspector does not retrieve a native archive, run dbt, authenticate a
Databricks attempt, parse structured logs, write observability tables,
correlate an `AttemptKey`, hash customer evidence, or classify full capture
state. The synthetic fixtures and local parse remain compatibility and contract
evidence, not Azure Databricks runtime evidence.

## Offline, no-compute, and raw-data boundaries

### Offline-after-installation

The accepted wording is “offline after installation,” not “disconnected first
installation.” The initial locked dependency installation can require the
customer-approved index, mirror, or populated cache. A disconnected wheelhouse
and complete Linux distribution remain later qualification gates. The
resolution preserves that distinction and does not turn the successful local
runtime-only installation into an air-gapped distribution claim.

### No platform call or paid compute

Inspection itself has no Databricks or dbt call, network, environment, clock,
or subprocess runtime dependency. The API reads only installed checksum-pinned
schemas; the CLI additionally reads two caller-selected local regular files.
The current resolution/index commit changes only Markdown and adds no Bundle,
App, Job, warehouse, cluster, serverless, Unity Catalog, Azure, or telemetry
path.

This audit used local files, temporary local environments, and repository
gates only. It did not authenticate to a workspace or start paid compute. The
historical workspace inventory remains a point-in-time evidence record and is
not reused as a claim that the workspace is idle now.

### Raw evidence and Personal Data

The resolution correctly states that ordinary reports exclude raw bytes, SQL,
messages, adapter responses, paths, relations, project/resource/invocation
identity, and other non-allowlisted artifact content. It also preserves the
stronger custody caveat: real raw artifacts can contain Personal Data, secrets,
SQL, identifiers, paths, topology, and operational metadata.

The caller remains responsible for approved storage, access, support transfer,
retention, deletion, backups, and legal hold. Local no-network processing does
not prove that a workstation or its backups satisfy the future Databricks-local
product custody model. No declassification or deletion attestation is implied.

## Decision 0002

Decision 0002 is still `accepted` and narrowly governs the two static
invocation issue variants before the first release. It records the
repository-controlled pre-release premise, requires generated schema and
fixture byte checks plus API/CLI/constructor gates, and requires dbt, usability,
and security re-review before release. An equivalent post-release text change
requires a new contract-version decision and consumer migration analysis.

The current report set satisfies those specialist review routes:

- `dbt-core-rereview-4.md` rechecks the correction at `cff8bbc`;
- `usability-rereview-4.md` rechecks the user journey at `cff8bbc`; and
- `databricks-rereview-4.md` supplies the post-correction platform/security
  review at `cff8bbc`.

The static registry, generated report schema, generated fixture, expected
output, references, tutorial, and executable tests remain synchronized. The
decision does not authorize a platform-semantic misstatement in the final
resolution, so it does not resolve the finding below.

## Retained nonblocking gates

The resolution and index retain all material later gates required by the
latest reports:

1. real Azure Databricks archive retrieval and layout for success, dbt failure,
   early failure, cancellation, timeout, retry, and repair;
2. `AttemptKey`, archive hashes, structured logs, native Job evidence, stable
   absence, trust observation, reconciliation, and full capture-state logic;
3. the complete Python 3.12/Linux lock and disconnected distribution before an
   air-gapped installation claim;
4. rendered-site navigation, search, generated anchors, browser behavior,
   keyboard/focus order, responsive layout and reflow, contrast, representative
   screen-reader and assistive-technology behavior, WCAG process, and
   publication safety; and
5. a fresh compatibility qualification for any dbt Core, adapter, schema,
   resource, or status row beyond the pinned candidate.

These remain nonblocking only for the reviewed local inspector. They block the
corresponding later production, runtime, distribution, accessibility, and
publication claims.

## Finding

### `RESSEC-P1.1-001`: The final resolution attributes dbt Core `BuildTask` semantics to Databricks

- Severity: **Medium**
- Affected file: `docs/reviews/p1.1-artifact-pair-inspector/resolution.md:36`
- Status: **OPEN — CHANGES_REQUIRED**

The final resolution says that P1.1:

> applies the exact Databricks `build` resource/status matrix

There is no reviewed Databricks platform `build` resource/status matrix behind
this contract. The immutable dbt review binds the supported collections and
status families to dbt Core 1.11.12 `BuildTask.RUNNER_MAP`, `RunStatus`, and
`TestStatus`. The Python reference names the table “BuildTask result
compatibility.” The inspector separately requires
`manifest.metadata.adapter_type == "databricks"` and
`run_results.args.which == "build"`.

Those are related but distinct facts:

| Fact | Owner and meaning |
| --- | --- |
| Resource collections and valid status families | dbt Core 1.11.12 `BuildTask` and result schemas |
| `adapter_type=databricks` | dbt manifest evidence for the qualified adapter path |
| `command=build` | dbt run-results evidence for the supported primary command |
| Lakeflow task state, archive, and run identity | Future Databricks platform evidence, not P1.1 input |

The current wording makes a dbt Core compatibility rule appear to be a
Databricks platform contract. In an authoritative final resolution, that can
misdirect support ownership, future compatibility qualification, and regulated
evidence interpretation. It also weakens the otherwise explicit separation of
pair validity, native dbt outcome, Lakeflow state, and capture completeness.

The error does not create runtime egress, expose raw data, start compute, or
invalidate the frozen implementation. It is nevertheless a present factual
defect in the audited final resolution and cannot be deferred.

Required change:

Replace the attribution with wording that keeps the invariants separate. For
example:

```text
P1.1 accepts keyword-only manifest: bytes and run_results: bytes, validates the
complete pinned dbt Core 1.11.12 manifest-v12 and run-results-v6 schemas, and
applies that version's exact BuildTask resource/status matrix. The separate
supported-pair invariants require manifest adapter_type=databricks and
run-results command=build.
```

Preserve the following sentence that distinguishes native executed-result
status counts from dbt success, Lakeflow task state, and capture completeness.
Then create a new immutable commit and repeat this focused resolution/index
audit. No production-code or cloud change is required.

## Local validation

All checks used exact commit
`74a9cdf8e2b9da44015a134fffc6b13d66395453`. The audit report itself was not an
input to the checks.

```text
frozen implementation/gate aggregate
count=48
recorded SHA-256 reproduced

frozen developer-documentation aggregate
count=14
recorded SHA-256 reproduced

latest-review aggregate
count=9
recorded SHA-256 reproduced

resolution/index/target parser
resolution_rows=9
index_rows=9
target_verdict_matches=9
pass_with_follow_up_targets=5
later_gate_nonblocking_language=passed
production_nonclaims=passed
decision_0002_requirements=passed

scripts/check_capture.sh
96 passed in 5.09s
tracked_markdown_files=132
local_links=227
fragments=59
errors=0
Ruff lint and format: passed
ty: passed
schema and fixture byte regeneration: passed
seven-package runtime-only install: passed
wheel build and isolated installed CLI: passed
DBTOBSB_CAPTURE_CHECK_PASSED

uv lock --check --project capture
passed

bash -n scripts/check_capture.sh
passed

shellcheck scripts/check_capture.sh
passed

git diff --check a00d6ab...74a9cdf
passed

git diff --check cff8bbc...74a9cdf
passed
```

The local gate used available CPython 3.12.13. It does not qualify the planned
Databricks CPython 3.12.3 runtime; the resolution correctly retains that runtime
qualification as later work.

## Verdict

**CHANGES_REQUIRED**

The final resolution and review index correctly bind their frozen inputs,
latest reports, accepted offline local scope, no-compute and raw-data
boundaries, Decision 0002 treatment, `PASS_WITH_FOLLOW_UP` policy, and later
runtime/distribution/rendered/accessibility gates. No underlying P1.1 product
blocker regressed.

`RESSEC-P1.1-001` remains a current truthful-claims defect in the final
resolution: dbt Core `BuildTask` resource/status semantics are mislabeled as a
Databricks matrix. Correct that one sentence at a new immutable commit and
request a focused re-review. Until then, this final resolution/index audit
cannot pass.
