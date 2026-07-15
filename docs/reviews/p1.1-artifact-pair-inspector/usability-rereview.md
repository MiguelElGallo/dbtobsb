# Usability re-review: P1.1 artifact-pair inspector

- Commit/diff: `e5969edd822ea5ccb31171f6c74e0ba690fd2294`
- Date: 2026-07-15
- Reviewer: independent usability, onboarding, and text-interface specialist
- Verdict: **PASS_WITH_FOLLOW_UP**
- Cloud/authentication activity: none

## Executive verdict

Commit `e5969edd822ea5ccb31171f6c74e0ba690fd2294` resolves all three usability
findings from the review of `054527a6721c36af6a9e99218120b39920bd0fed`.
A non-author can now distinguish installation egress from offline inspection,
install only the seven runtime packages, use `--no-sync` with an already prepared
environment, recover safely from every tested exit-3 file shape, and run a
checked-in Python API example with exact expected output.

The complete first-value journey and both recovery journeys remained far below
their ten- and five-minute targets on this machine. Text and JSON stayed
deterministic in a redirected non-TTY under `TERM=dumb`, `NO_COLOR=1`, and
`UV_OFFLINE=1`; no output used ANSI state, animation, cursor rewriting, or
color-only meaning. The three-question model remains explicit: pair validity,
native dbt outcome, and future capture completeness are separate facts.

No current P1.1 usability defect remains. The follow-ups below belong to the
already planned rendered-documentation, distribution, and real-runtime gates;
they do not block acceptance of this local inspector part.

## Sources and scope checked

- Initial [usability review](usability-review.md), including findings
  `UX-P1.1-001` through `UX-P1.1-003` and their acceptance evidence.
- Repository [review process](../../plans/review-process.md), especially the
  P1 actionable-error focus and verdict rules.
- Repository [P1.1 implemented boundary](../../plans/product-plan.md#p11-implemented-boundary).
- Repository [documentation page registry](../../plans/documentation-plan.md#navigation-and-page-traceability-contract)
  and D1/D1P rendered-documentation boundary.
- Revised repository, capture-package, developer tutorial, recovery guide,
  CLI/API reference, example, evidence, tests, and local capture gate at the
  exact immutable commit above.

The review used a detached isolated worktree at the exact commit. It did not
inspect another re-review, alter reviewed implementation or documentation, run
dbt, authenticate to Databricks or Azure, or start paid compute.

## Acceptance criteria rechecked

- Honest, visible separation between dependency-installation egress and
  offline-after-installation inspection.
- Runtime-only installation through `--no-dev`, followed by `--no-sync` for
  every reader-facing inspection.
- First successful CLI inspection in less than ten minutes after the stated
  prerequisites.
- Invalid-pair and input-read recovery in less than five minutes.
- One safe exit-3 message and recovery route for missing, symbolic-link, FIFO,
  device, and over-limit inputs.
- Checked-in, copy-ready Python API first success with exact output.
- Deterministic text and JSON in a non-TTY and with no color or animation.
- Linear, labeled text semantics suitable for assistive-technology reading.
- Clear developer navigation and locally valid Markdown links.
- Continued fixture honesty and separation of pair validity, native dbt result,
  and capture completeness.
- Reproducible tests, lint, type, wheel, and installed-command evidence.

## Non-author task evidence

### First value and offline-after-installation boundary

From an empty dedicated uv cache and a separate environment, the documented
runtime preparation completed successfully:

```text
uv sync --project capture --locked --no-dev
Prepared 7 packages
Installed 7 packages
```

The installed set was `attrs`, `dbtobsb-capture`, `jsonschema`,
`jsonschema-specifications`, `referencing`, `rpds-py`, and
`typing-extensions`; no pytest, Hypothesis, Ruff, or `ty` package entered the
runtime environment.

The documented successful inspection was then run with `--no-sync` and
`UV_OFFLINE=1`. It exited `0`, emitted the exact documented `PAIR_VALID` report,
and setup plus first value completed in approximately one second on this
machine. Repeating that inspection with a newly empty uv cache, the prepared
environment, `UV_OFFLINE=1`, and `--no-sync` also returned `PAIR_VALID` without
stderr. This verifies the claimed offline behavior after installation rather
than calling the initial dependency bootstrap offline.

The README, package README, tutorial, developer index, product boundary, and
workflow label now use the same honest distinction. They state before the first
command that a clean sync can download packages; regulated users must configure
an approved registry, mirror, or populated cache; and a disconnected wheelhouse
is not shipped. A user without an approved source is told to stop before
installation.

### Tutorial and recovery timing

All three documented fixture commands were run with `UV_OFFLINE=1` and
`--no-sync`:

| Journey | Exit | Observed result |
| --- | ---: | --- |
| Valid success | `0` | Exact `PAIR_VALID`, `success=1`, and capture-state caution. |
| Valid dbt failure | `0` | Exact compact JSON with `PAIR_VALID` and `error=1`. |
| Invocation mismatch | `10` | Exact `DBT_INVOCATION_ID_MISMATCH`, impact, and one next action. |

Moving from the invalid fixture back to the packaged valid pair took
approximately two seconds. A separate missing-input exit `3` followed by the
documented valid inputs returned to `PAIR_VALID` in less than one second. These
machine-local measurements satisfy the under-five-minute recovery target while
remaining evidence, not a universal performance guarantee.

### Exit-3 text and file-shape behavior

Missing, symbolic-link, FIFO, `/dev/null` device, and 128-MiB-plus-one-byte
regular-file cases were executed independently. Every case:

- returned exit `3` without blocking;
- wrote zero bytes to stdout;
- emitted the same stderr bytes, SHA-256
  `5aaabc86350569e379d5976a7efe5dd0bf5f026c4d675d024d0243284b1a7a9d`;
- omitted the supplied path, exception, and artifact content; and
- pointed to a real local heading in the revised recovery guide.

The exact message was:

```text
DBTOBSB_INPUT_READ_ERROR
impact: One or both inputs could not be read as closed regular files within 128 MiB.
next_action: Provide existing, closed, non-symlink regular files no larger than 128 MiB.
help: docs/developers/how-to/diagnose-an-invalid-artifact-pair.md#recover-an-input-read-error
```

The developer index now routes exit `3` users to that guide, its entry condition
names `DBTOBSB_INPUT_READ_ERROR`, and the guide explicitly excludes pipes,
devices, and symbolic links. Tests bind the exact static message and place
two-second timeouts around FIFO, device, and sparse-over-limit installed-command
cases.

### Python API first success

The documented command:

```text
uv run --project capture --no-sync python capture/examples/inspect_valid_fixture.py
```

ran with `UV_OFFLINE=1`, exited `0` in approximately one second, wrote no
stderr, and emitted the exact two documented lines: `PAIR_VALID` followed by
the compact, sorted safe report for `success=1`. The checked-in script defines
the fixture byte loading, keyword-only API call, `PairState` rendering, and
deterministic `to_dict()` serialization; the reader no longer has to invent
undefined byte variables. The capture gate executes this same script in its
fresh runtime-only environment, and golden report tests bind the serialized
content.

### Determinism, text accessibility, navigation, and quality gates

Two redirected runs of both text and JSON under `TERM=dumb`, `NO_COLOR=1`,
`CI=1`, `UV_OFFLINE=1`, and `--no-sync` were byte-identical. All normal stderr
streams were empty, and no checked stream contained an ANSI escape. The output
is a linear sequence with explicit state, `code`, `impact`, `next_action`, and
`help` labels; it requires no prompt, pointer, timing, cursor position, color,
or spinner to interpret. Missing required arguments still returned safe exit
`2` with usage and `DBTOBSB_CLI_USAGE_ERROR`, without echoing the rejected
argument.

A local navigation check resolved 36 relative links across the repository
README, capture README, documentation index, and complete developer route with
zero missing targets. The help anchor exists. Tutorial, how-to, API/CLI
reference, and explanation remain distinct and reachable from the developer
index.

The immutable commit also passed:

```text
scripts/check_capture.sh
81 tests passed
Ruff check and format: passed
ty: passed
fixture and report-schema regeneration: passed
seven-package runtime-only quickstart: passed
checked-in Python API example: passed
wheel build and isolated installed console entry point: passed
DBTOBSB_CAPTURE_CHECK_PASSED
bash -n and ShellCheck for scripts/check_capture.sh: passed
```

The detached source worktree remained clean after the checks.

## Finding-by-finding resolution

### UX-P1.1-001: Offline wording and runtime-only setup

- Original severity: high.
- Resolution commit: `e5969edd822ea5ccb31171f6c74e0ba690fd2294`.
- Resolution: The reader sees the possible initial package download and
  approved-source requirement before running it. Every quickstart inspection
  now uses a seven-package `--no-dev` environment and `--no-sync`; the workflow
  no longer labels dependency bootstrap as an offline gate. The disconnected
  wheelhouse is explicitly absent rather than implied.
- Validation: Empty-cache runtime setup installed exactly seven packages;
  `UV_OFFLINE=1 --no-sync` inspections passed from the prepared environment,
  including after replacing the uv cache with an empty one. The full gate
  independently builds a fresh seven-package runtime environment and runs the
  same quickstart.
- Re-review outcome: **RESOLVED**. No current P1.1 change required.

### UX-P1.1-002: Actionable safe exit-3 recovery

- Original severity: medium.
- Resolution commit: `e5969edd822ea5ccb31171f6c74e0ba690fd2294`.
- Resolution: Exit `3` now gives a static impact, one static next action, and a
  stable local help route without disclosing which path failed. Developer
  navigation and the how-to entry condition include this error explicitly.
  Nonblocking file opening prevents FIFO/device hangs.
- Validation: Missing, symlink, FIFO, device, and over-limit probes all returned
  the byte-identical documented message immediately with no stdout or leakage;
  correction to the valid pair took less than one second. Exact stderr and
  timeout-bounded installed-command tests passed.
- Re-review outcome: **RESOLVED**. No current P1.1 change required.

### UX-P1.1-003: Runnable Python API first success

- Original severity: medium.
- Resolution commit: `e5969edd822ea5ccb31171f6c74e0ba690fd2294`.
- Resolution: `capture/examples/inspect_valid_fixture.py` is a complete,
  checked-in example; the API reference gives a copy-ready command and exact
  output. File reading remains outside the inspector API.
- Validation: The documented command passed offline after installation with
  the exact two-line output, and the full capture gate executed it in the
  runtime-only environment against golden serialized report content.
- Re-review outcome: **RESOLVED**. No current P1.1 change required.

## Positive controls preserved

- `PAIR_VALID` still does not imply native dbt success or complete capture. The
  valid-error fixture and three explicit tutorial questions prove the
  distinction.
- All three fixtures remain labeled synthetic and sanitized, and their
  provenance states `runtime_evidence=false`; no local result is presented as a
  real Databricks capture or qualified compatibility row.
- Reports remain deterministic, closed, bounded, and allowlisted. No raw SQL,
  result message, path, environment value, project/resource/invocation identity,
  or artifact fragment appears in ordinary output.
- CLI meanings do not depend on color, motion, a TTY, or interaction. Named
  flags and stable exits remain intact, and abbreviated flags remain rejected.
- The Python API remains keyword-only and does not open caller paths, retain raw
  bytes, or access the network, Databricks, dbt, environment, clock, or a
  subprocess.
- No Databricks App, Job, SQL warehouse, cluster, serverless environment, Unity
  Catalog object, Azure resource, authentication flow, or paid compute was
  accessed or started for this re-review.

## Later-gate follow-ups

These are outside P1.1's implemented boundary and do not weaken this verdict:

1. **D1/D1P rendered documentation — documentation owner.** Render the complete
   developer journey, replace or supplement the repository-relative CLI help
   route with the accepted stable documentation destination for distributed
   installs, and run the planned search, responsive-layout, keyboard,
   representative screen-reader, and WCAG 2.2 AA process checks.
2. **P10/D8 distribution qualification — distribution/install owner.** If the
   product later promises a disconnected first installation, ship and test a
   checksum-bound wheelhouse or equivalent approved source. Until then retain
   the present explicit non-claim and approved-index/mirror/cache prerequisite.
3. **Later P1/P8 runtime qualification — capture owner.** Replace synthetic-only
   learning evidence with independently sanitized real Azure Databricks success,
   failure, cancellation, timeout, retry, and repair captures before making
   runtime or capture-completeness claims.

## Resolution and re-review

- Resolution: Commit `e5969edd822ea5ccb31171f6c74e0ba690fd2294`
  closes `UX-P1.1-001`, `UX-P1.1-002`, and `UX-P1.1-003`.
- Validation: Non-author journeys, exact error/file-shape probes, API example,
  offline-after-installation checks, deterministic non-TTY checks, navigation,
  81 tests, Ruff, `ty`, schema/fixture regeneration, runtime-only install,
  wheel/installed-command smoke, Bash syntax, and ShellCheck all passed.
- Current defects: none.
- Re-review verdict: **PASS_WITH_FOLLOW_UP**. P1.1 is safe to accept; the three
  follow-ups above are owned by later gates and are not current-part blockers.
