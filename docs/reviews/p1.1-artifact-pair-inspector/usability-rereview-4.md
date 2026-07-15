# Final product usability and onboarding re-review: P1.1 artifact-pair inspector

## Review record

| Field | Value |
| --- | --- |
| Reviewed commit | `cff8bbcd808ff7e13a7ead182543a2564cd04ff6` |
| Commit tree | `a3802ab9b14a1dc3b7f18f90255eee349fdeecbb` |
| Commit parent | `8711aa803016b5d732553756c5e71542e0a928bf` |
| Commit subject | `docs: record p1.1 usability closure` |
| Prior product review | `usability-rereview-3.md`, commit `75b7d41316216a3b18a3c56ff0c98f133f7aab89` |
| Review date | 2026-07-15 |
| Review role | Independent product usability, onboarding, and text-interface reviewer |
| Verdict | **PASS_WITH_FOLLOW_UP** |

P1.1 remains usable as an unreleased private candidate. A new user can install only the locked runtime, complete the CLI and Python first-success journeys, distinguish pair validity from dbt outcome and future capture state, follow safe deterministic recovery, and discover the exact compatibility boundary. The corrected invocation action is more operationally useful and is identical across runtime, generated schema, fixture, tutorial, and reference. The raw-handling command and GFM public-type contract are copy-ready and reader-correct.

`UX-P1.1-001`, `UX-P1.1-002`, and `UX-P1.1-003` remain resolved. The source-level `DOCUX-P1.1-001` and `DOCUX-P1.1-002` controls also remain closed. No current P1.1 usability or onboarding defect was found. `PASS_WITH_FOLLOW_UP` records only the later rendered-site, distribution, and real-Databricks qualification gates; it does not request a source change in this slice.

## Exact scope

### Reader and decision set

The reader set is this exact path-ordered 12-file list:

1. `README.md`
2. `capture/README.md`
3. `docs/decisions/0002-correct-p1.1-invocation-recovery-text.md`
4. `docs/developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md`
5. `docs/developers/explanation/raw-artifact-custody.md`
6. `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md`
7. `docs/developers/how-to/handle-raw-dbt-artifacts-safely.md`
8. `docs/developers/index.md`
9. `docs/developers/reference/cli-report-and-exit-codes.md`
10. `docs/developers/reference/python-api.md`
11. `docs/developers/tutorials/inspect-an-artifact-pair.md`
12. `docs/index.md`

### Runtime and machine-contract set

The runtime set is this exact path-ordered 10-file list:

1. `capture/examples/inspect_valid_fixture.py`
2. `capture/pyproject.toml`
3. `capture/src/dbtobsb_capture/__init__.py`
4. `capture/src/dbtobsb_capture/cli.py`
5. `capture/src/dbtobsb_capture/contracts.py`
6. `capture/src/dbtobsb_capture/inspector.py`
7. `capture/src/dbtobsb_capture/registry.py`
8. `capture/src/dbtobsb_capture/schemas/artifact-pair-report-v1.json`
9. `capture/tests/fixtures/artifact_pair/invalid_invocation_mismatch/expected-report.json`
10. `capture/uv.lock`

### Prior-review set

The review set is:

1. `docs/reviews/p1.1-artifact-pair-inspector/documentation-usability-rereview-2.md`
2. `docs/reviews/p1.1-artifact-pair-inspector/usability-rereview-2.md`
3. `docs/reviews/p1.1-artifact-pair-inspector/usability-rereview-3.md`
4. `docs/reviews/p1.1-artifact-pair-inspector/usability-rereview.md`
5. `docs/reviews/p1.1-artifact-pair-inspector/usability-review.md`

### Executable corroboration

The validation set is:

1. `capture/tests/test_cli.py`
2. `capture/tests/test_documentation.py`
3. `scripts/check_capture.sh`
4. `scripts/check_markdown_links.py`

The review used a detached worktree at the exact commit and dedicated uv cache and environment paths. No reviewed source or prior report was edited. It made no Azure, Databricks, dbt, warehouse, cluster, serverless, or paid-compute call. Read-only GitHub repository/release and Markdown-rendering queries plus a read-only PyPI package lookup were used only to corroborate pre-release and GFM claims; they created no external object.

## Immutable hashes

Each aggregate is SHA-256 over the literal path-ordered `shasum -a 256` record stream for its exact set above.

| Frozen input | SHA-256 |
| --- | --- |
| 12-file reader and decision aggregate | `038658c97a53febffe5cfef43f5c704be01fa4336611d6c378a630d8e5daf4c1` |
| 10-file runtime and machine-contract aggregate | `5b8fea9b977b25d86ae6825bd88aeb837bae652412d3bf408ec79e19d5007bd6` |
| Five-file prior-review aggregate | `6c37c5a6380f1a442007ee111df1a10cc1e52710c279a4b4ca0cbe27f6c311e1` |
| Four-file validation aggregate | `3e7090a86603f3cee2c856e38b6b72ab0ae5217770a4b38f07c1d4b27a14c369` |

Critical individual hashes are:

| File | SHA-256 |
| --- | --- |
| `docs/decisions/0002-correct-p1.1-invocation-recovery-text.md` | `946d6ca04d362d5a25606f0306114b2776d2479376ab300899ca4bc0019614d1` |
| `docs/developers/tutorials/inspect-an-artifact-pair.md` | `35b778b40eda2880b837a2d5c5d517c55ac9593e41d6aacf3815f76ba5c6a12d` |
| `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md` | `e2befb7ad8648db1cfd71ec9e4f9eba4a44a78a2c67fb2cb7233fece097c4531` |
| `docs/developers/how-to/handle-raw-dbt-artifacts-safely.md` | `539ac1e3e1c208b52d6e486a1c87b788e73b92f1f4b7d4e5d30724022908e920` |
| `docs/developers/reference/cli-report-and-exit-codes.md` | `bb4c28a5c50988e4ddc17e90c462b3d86de145ecec8d1c06e78f19ed97c30323` |
| `docs/developers/reference/python-api.md` | `7c5e2ca891124cfb9b60f6184983fb97a963ec26339c1decce4e40dba14e9c82` |
| `capture/examples/inspect_valid_fixture.py` | `9ec9e35e7362cbe2907483e344c2979bd886b9586b03d35b465d93e533ec5099` |
| `capture/src/dbtobsb_capture/inspector.py` | `d80955b8575ff12d5daf2d6d26bf3e4b49f79a2d0beb910ef5aed961db7ffdaf` |
| `capture/src/dbtobsb_capture/schemas/artifact-pair-report-v1.json` | `a57bd0c63cfb846ea4282e686ff859892465b501eff6ae132b8650503d2eddc0` |
| Invocation-mismatch `expected-report.json` | `05cadb8737782e4eb35af90bfff48dfd41db86de12bca95cc7702651c677ee9c` |
| `usability-rereview-3.md` | `6605d63b92605f9a7940a17234794468c3d03d1e8052fb475e18682f68fb0317` |
| `documentation-usability-rereview-2.md` | `b2326a65d2d2babe8b49e55fd43950b28c420c07d7eed755b09f7cb854cf1a3d` |
| `capture/tests/test_cli.py` | `b8f620560cc16ec77935c306ac4ef10b40a29ed16bb6864ba94c9ad2e4bcb29d` |
| `capture/tests/test_documentation.py` | `8dab5bf14843fef5ae4bc86a2335ae3912fe18c9ba88175302fdff0b7e160b99` |
| `scripts/check_capture.sh` | `92656cda84b66dd76338cec050c35e632ae50de015bda89e474d28a74854b911` |
| `scripts/check_markdown_links.py` | `aa904ffdd5540d2604b840c42d8d04660c03c57e0d1f818355fc524dbd40b0c0` |

## Checks executed

| Check | Result |
| --- | --- |
| `scripts/check_capture.sh` | Passed; ended in `DBTOBSB_CAPTURE_CHECK_PASSED` |
| Complete capture suite | 96 passed |
| Focused documentation plus CLI suites | 20 passed |
| Immutable Markdown link check | 128 tracked Markdown files, 212 local links, 59 fragments, zero errors |
| Ruff check and format, plus ty | Passed |
| Schema and fixture regeneration | Passed without diff |
| Runtime-only install | Exactly seven packages installed |
| Checked-in API example, wheel, and isolated installed CLI | Passed |
| `bash -n scripts/check_capture.sh` and `shellcheck scripts/check_capture.sh` | Passed |
| Landing-route graph | All eight implemented developer pages reachable; Decision 0002 reachable |
| Heading hierarchy | 12 scoped reader files; one H1 each; zero skipped levels |
| Active old invocation wording scan | Zero uses in runtime, tests, fixtures, reader docs, root README, or capture README |
| Local GFM source-contract probe | Seven two-cell rows, two escaped display pipes, two normalized unions, zero entities |
| GitHub GFM rendering probe | Two headers, 10 body cells, two visible union tokens, zero visible entities or backslash-pipe tokens |
| Accepted raw/GFM source continuity from `8711aa8…` | Passed; source and regression test byte-identical |
| `git diff --check 75b7d41…cff8bbc…` | Passed |
| Detached worktree after validation | Clean; zero tracked diff |

## Public task-completion evidence

### Locked installation and copy-ready uv commands — PASS

The root README and tutorial disclose that the first locked sync can contact the configured package source, require an approved registry, mirror, or cache in a regulated environment, and do not promise a disconnected wheelhouse. The executed runtime-only path installed exactly seven packages:

```text
uv sync --project capture --locked --no-dev
```

All subsequent public journeys ran with `uv run --project capture --no-sync` under `UV_OFFLINE=1`, `TERM=dumb`, `NO_COLOR=1`, and `CI=1`. The marked raw-handling command was extracted, its approved-path placeholders were replaced by sanitized fixture paths, and the literal uv command returned safe valid JSON. The diagnosis command uses explicit placeholders rather than presenting a synthetic path as real evidence. No copy-ready command silently adds development dependencies or synchronizes at inspection time.

### CLI and API first value — PASS

The exact public journeys produced these channel and determinism results:

| Journey | Exit | Primary channel SHA-256 | Other channel | Repeat result |
| --- | ---: | --- | --- | --- |
| Valid text | `0` | stdout `6dc2e98d982f1f57be246b224b7b1406d06e1a19794dee7145ef3e1c1c6f67b1` | empty stderr | byte-identical |
| Valid JSON | `0` | stdout `a5a39e26af3a99d759a6687cb24e91f29d4b81b86c570d1cd64b4fbc60e0707a` | empty stderr | byte-identical |
| Valid pair with native dbt error | `0` | stdout `f632c1bde08347d59673749108c0f888e2984ac10eaae0bfc47cf3ee7a501c46` | empty stderr | byte-identical |
| Invalid invocation pair | `10` | stdout `a7cecf8ca0556b92c1077a7b36660fb0de6a0e6111a5babd6dac474efbd584e8` | empty stderr | byte-identical |
| Checked-in Python example | `0` | stdout `f53fd7c0ec2308b1239d6c4edf0f4fa057035c21da9ad58358ed651053519aae` | empty stderr | byte-identical |

Every checked stream was ANSI-free. The direct Python API returned `PAIR_INVALID`, the same primary invocation code, impact, and action as the CLI. A non-byte call raised the static `TypeError` `manifest and run_results must be bytes` without echoing the supplied canary. CLI and API users therefore receive the same task model and can complete both first-success and expected-invalid paths without an internal-error detour.

### Overwrite-safe invocation recovery — PASS

The CLI now emits exactly:

```text
PAIR_INVALID
code: DBT_INVOCATION_ID_MISMATCH
impact: The files do not have the same dbt invocation identity.
next_action: Collect both closed artifacts from one completed pinned dbt build invocation before another dbt command runs.
```

The action is concrete, bounded, and accurate. The diagnosis how-to adds the operational detail that the approved pinned `dbt build` receives an empty attempt-specific target path, both files are collected after the invocation closes them, and collection happens before a later command can reuse or overwrite the path. It explicitly says that equal parseable `metadata.invocation_id` values are the pairing key and directory co-location is not.

The same impact/action tuple appears in the runtime registry, generated v1 schema, expected fixture report, tutorial, and CLI issue registry. The old “trusted pair” and “same target directory” formulations have zero active-source occurrences. Historical reviews retain them only as immutable audit evidence, not as a competing current instruction.

### Safe failures and deterministic text — PASS

Missing, symlink, FIFO, device, and 128-MiB-plus-one-byte regular-file inputs all returned exit `3` within the probe timeout, zero stdout, and the same safe stderr SHA-256:

```text
5aaabc86350569e379d5976a7efe5dd0bf5f026c4d675d024d0243284b1a7a9d
```

The error provides impact, a concrete correction, and a valid local help fragment while exposing no path, exception, or canary. An abbreviated option returned exit `2`, empty stdout, `DBTOBSB_CLI_USAGE_ERROR` on stderr, and no supplied canary. Focused tests also preserve static internal-error behavior, deep-nesting invalid inspection, canonical mixed-invalid reports, nonblocking FIFO/device handling, named-option enforcement, and no-color behavior.

Meaning is linear text and does not depend on a TTY, color, cursor position, animation, spinner, or interaction. JSON retains all bounded canonical issues; text exposes the one primary action a human should take first.

### GFM and compatibility discoverability — PASS

The public-types table uses GFM-prescribed escaped pipes inside the two union code spans. A local delimiter-aware parse produced seven two-cell rows. GitHub's GFM renderer produced two headers and 10 body cells, with visible `ArtifactPairSummary | None` and `ArtifactPairIssue | None` code and no visible entity or backslash. The reflection test binds those displayed types to the public Python annotations.

The Python reference gives the complete BuildTask collection/resource/status matrix and unsupported-result rules under a descriptive heading. Both the diagnosis page and CLI issue registry link directly to that exact fragment. The developer index exposes the Python reference, and the immutable link checker validates every route and anchor. Compatibility detail is available at the decision point without burdening the tutorial's first-success path.

## Prior finding status

### UX-P1.1-001 — REMAINS RESOLVED

The clean runtime path still installs seven locked runtime packages only. Installation egress is disclosed before the command, regulated-source requirements are explicit, a disconnected wheelhouse is not promised, and inspections use offline `--no-sync` execution.

### UX-P1.1-002 — REMAINS RESOLVED

All five unsafe or unreadable input shapes retain exit `3`, immediate nonblocking completion, identical static actionable stderr, a valid help route, and no path or exception disclosure.

### UX-P1.1-003 — REMAINS RESOLVED

The checked-in Python example remains identical to the displayed example, runs in the documented runtime, emits the exact two documented lines, and links onward to the complete API contract.

### DOCUX-P1.1-001 and DOCUX-P1.1-002 — REMAIN CLOSED

The raw-artifact command remains executable after its stated prerequisite and sanitized path substitution. The GFM table remains structurally two-column and visibly presents both true Python union operators. The focused regression tests and current GitHub GFM rendering corroborate both closures.

## Decision 0002 migration assessment

Decision 0002 creates no migration ambiguity for this candidate:

- the repository labels P1.1 a candidate and the decision explicitly records that it has not been distributed, released, or accepted by an external consumer;
- the GitHub repository was observed as `PRIVATE`, with zero GitHub releases, zero local tags, zero tags containing this commit, and zero live remote branch heads at the reviewed commit;
- the PyPI JSON endpoint for `dbtobsb-capture` returned `404` at review time;
- all repository-controlled forms of the static v1 invocation text agree, and regeneration passes; and
- the decision explicitly requires a new contract-version decision and consumer migration analysis for an equivalent post-release text change.

Retaining `dbtobsb.artifact-pair-report.v1` is therefore a pre-release correction to one unpublished candidate contract, not a silent change between two supported public v1 variants. The installed distribution version `0.1.0` is candidate metadata, not evidence of an external release. No user must choose between old and new current recovery behavior.

## Current-versus-future boundary

The journey consistently says that P1.1 validates one local pinned pair and is offline only after installation. It does not retrieve archives, run dbt, prove a Databricks attempt, parse structured logs, write observability tables, authenticate provenance, govern caller files, or assign capture completeness. `PAIR_VALID` is expressly limited to pinned schema and internal cross-file invariants; a valid pair can still contain a native dbt error.

The workstation-local custody page states that local no-network processing is not proof of the target Databricks-local product boundary. The fixtures remain synthetic and sanitized. Compatibility rows are local contract support, not real-runtime qualification. No current feature is described as a future collector, archive, capture-state, or production-runtime capability.

## Explicit later-gate follow-ups

These remain later product gates and do not block this source-level P1.1 usability verdict:

1. **Documentation publication:** build the complete site, then test rendered navigation, distributed help, generated anchors, copy controls, responsive reflow, keyboard/focus order, representative screen-reader output, contrast, and the WCAG 2.2 AA process.
2. **Distribution:** provide and test a checksum-bound disconnected installation source only if the released product promises disconnected first installation; the current approved registry/mirror/cache boundary remains honest.
3. **Real runtime:** independently qualify sanitized Azure Databricks success, failure, cancellation, timeout, retry, and repair journeys before making production-runtime or capture-completeness claims.

## Verdict

**PASS_WITH_FOLLOW_UP**

At exact commit `cff8bbcd808ff7e13a7ead182543a2564cd04ff6`, all prior P1.1 product usability blockers remain resolved, both source-level documentation usability closures remain intact, Decision 0002 is unambiguous for the unreleased private candidate, and no new current-part defect was found. Only the explicitly later rendered-site, distribution, and real-runtime gates remain.
