# Focused usability regression re-review: P1.1 mixed-invalid reports

- Commit/diff: `75b7d41316216a3b18a3c56ff0c98f133f7aab89`
- Date: 2026-07-15
- Reviewer: independent usability, onboarding, and text-interface specialist
- Verdict: **PASS_WITH_FOLLOW_UP**
- Cloud/authentication activity: none

## Executive verdict

The mixed-invalid canonicalization fix works through both the Python API and the
actual CLI. At exact commit `75b7d41316216a3b18a3c56ff0c98f133f7aab89`,
mixed evidence defects produce a deterministic, actionable `PAIR_INVALID`
report and exit `10`; they no longer fall into the generic internal-error exit
`4`. Text exposes the earliest primary issue and one safe recovery action, while
JSON retains the complete bounded issue set in canonical order.

The focused change introduces no onboarding or text-interface regression.
Runtime-only installation, offline-after-installation inspection, the successful
and valid-dbt-error fixtures, invocation-mismatch recovery, checked-in Python
example, exit-3 recovery, deterministic non-TTY/no-color output, documentation
navigation, and the pair/dbt/capture mental model all remain intact.

`UX-P1.1-001`, `UX-P1.1-002`, and `UX-P1.1-003` remain resolved. No current
P1.1 usability defect was found. The prior rendered-documentation,
distribution, and real-runtime follow-ups remain later-gate work only.

## Scope and method

The review used a detached worktree at the exact immutable commit and inspected
the focused diff from `bedfaa9d9e803c168c2481d5e4f18264a1f40e01`. It then
executed:

- clean runtime-only setup and first success;
- mixed parse failures through text and JSON CLI modes;
- mixed semantic failures through text and JSON CLI modes and the Python API;
- repeated mixed-invalid and valid reports under non-TTY/no-color conditions;
- the valid-dbt-error, invocation-mismatch, and checked-in API journeys;
- all five established exit-3 file-shape probes;
- local developer-route link validation; and
- the complete capture quality gate.

No reviewed implementation, documentation, evidence, fixture, or prior review
was edited. The review did not run dbt, authenticate to Azure or Databricks, or
access cloud or paid compute.

## Mixed-invalid acceptance evidence

### Mixed parse failures

The manifest contained a duplicate `metadata` key while run-results contained
invalid JSON. Both CLI output modes returned exit `10` with empty stderr. JSON
reported:

```text
PAIR_INVALID
DBT_RUN_RESULTS_JSON_INVALID
DBT_MANIFEST_JSON_DUPLICATE_KEY
```

Text presented the canonical primary issue and a specific recovery action:

```text
PAIR_INVALID
code: DBT_RUN_RESULTS_JSON_INVALID
impact: The run-results file is not one unambiguous UTF-8 JSON document.
next_action: Collect run_results.json again from the pinned dbt build target directory.
```

The reader receives an actionable invalid-evidence result without a path,
exception, artifact fragment, or generic internal-error detour.

### Mixed semantic failures

The successful run-results fixture was changed to have both negative elapsed
time and a duplicated result ID. Both CLI modes again returned exit `10`, empty
stderr, `PAIR_INVALID`, and canonical codes:

```text
DBT_RESULTS_DUPLICATE_ID
DBT_TIMING_INVALID
```

Text selected the same primary issue as JSON and supplied one safe next action:

```text
PAIR_INVALID
code: DBT_RESULTS_DUPLICATE_ID
impact: One dbt resource appears more than once in the execution results.
next_action: Collect a fresh unmodified artifact pair from the pinned dbt build.
```

Direct API inspection returned the same state, issue order,
`primary_issue.code`, and next action. Two repeated redirected JSON CLI runs
were byte-identical, with SHA-256
`223f34f1f20643674b33e5cd9b0f5a22544ea33bcccd64341ba25c3d3609c0f4`.
No checked mixed-invalid stream contained ANSI output.

This behavior matches the documentation contract: `issues[0]` is the primary
recovery path, text gives one immediate action, and machine consumers retain the
remaining static issues. The implementation now deduplicates, sorts against the
shared precedence registry, and only then applies the 20-issue bound and public
constructor.

## Preserved onboarding and recovery controls

### Runtime-only and offline-after-installation journey

From a new dedicated uv cache and environment, the documented command prepared
and installed exactly seven runtime packages:

```text
uv sync --project capture --locked --no-dev
Prepared 7 packages
Installed 7 packages
```

The first inspection ran with `UV_OFFLINE=1`, `TERM=dumb`, `NO_COLOR=1`, and
`--no-sync`, returned exit `0`, and emitted the exact documented
`PAIR_VALID`/`success=1` text. Setup plus first value took approximately one
second on this machine. The documentation still states before setup that
initial package preparation may use an approved index, mirror, or cache, and
that no disconnected wheelhouse is shipped.

### Valid error, mismatch, and API example

- The valid-dbt-error fixture returned exit `0`, `PAIR_VALID`, and `error=1`.
- The invocation-mismatch fixture returned exit `10`,
  `DBT_INVOCATION_ID_MISMATCH`, its impact, and one recollection action.
- The checked-in Python example returned exit `0`, no stderr, and the exact two
  documented `PAIR_VALID` plus compact-JSON lines.
- These three checks completed in approximately two seconds.

The first-value text and JSON remain byte-identical to the previously accepted
candidate:

```text
text  6dc2e98d982f1f57be246b224b7b1406d06e1a19794dee7145ef3e1c1c6f67b1
json  a5a39e26af3a99d759a6687cb24e91f29d4b81b86c570d1cd64b4fbc60e0707a
```

Their repeated redirected runs under `TERM=dumb`, `NO_COLOR=1`, `CI=1`, and
`UV_OFFLINE=1` were byte-identical, wrote no stderr, and contained no ANSI
escape. Meaning remains independent of interaction, cursor position, timing,
animation, spinner state, or color.

### Exact exit-3 behavior

Missing, symbolic-link, FIFO, `/dev/null` device, and
128-MiB-plus-one-byte regular-file inputs all returned exit `3` immediately,
with zero stdout and byte-identical stderr SHA-256
`5aaabc86350569e379d5976a7efe5dd0bf5f026c4d675d024d0243284b1a7a9d`:

```text
DBTOBSB_INPUT_READ_ERROR
impact: One or both inputs could not be read as closed regular files within 128 MiB.
next_action: Provide existing, closed, non-symlink regular files no larger than 128 MiB.
help: docs/developers/how-to/diagnose-an-invalid-artifact-pair.md#recover-an-input-read-error
```

No supplied path or exception text was exposed. The help heading and developer
navigation remain valid.

### Mental model and navigation

The tutorial still separates:

1. pair validity;
2. native dbt outcomes; and
3. future capture completeness, which P1.1 cannot establish.

Fixtures remain explicitly synthetic and sanitized with
`runtime_evidence=false`. A reader-route check across README, capture README,
documentation index, tutorial, how-to, CLI/API reference, and explanation
resolved 36 relative links with zero missing targets.

## Quality-gate evidence

The exact commit passed:

```text
scripts/check_capture.sh
90 tests passed
Ruff check and format: passed
ty: passed
report-schema and fixture regeneration: passed
seven-package runtime-only quickstart: passed
checked-in Python API example: passed
wheel build and isolated installed command: passed
DBTOBSB_CAPTURE_CHECK_PASSED
bash -n and ShellCheck for scripts/check_capture.sh: passed
```

The added regressions cover every pair from the closed issue precedence,
duplicate/bounded canonicalization, mixed parse failures, mixed semantic
failures, API output, and installed CLI exit/report behavior. The detached
source worktree remained clean after validation.

## Original finding status

### UX-P1.1-001: Offline wording and runtime-only setup

- Resolution commit: `e5969edd822ea5ccb31171f6c74e0ba690fd2294`.
- Result at `75b7d41316216a3b18a3c56ff0c98f133f7aab89`:
  **RESOLVED**. Seven-package setup, honest installation-egress wording, and
  offline `--no-sync` inspection all passed unchanged.

### UX-P1.1-002: Actionable safe exit-3 recovery

- Resolution commit: `e5969edd822ea5ccb31171f6c74e0ba690fd2294`.
- Result at `75b7d41316216a3b18a3c56ff0c98f133f7aab89`:
  **RESOLVED**. All five file shapes retained their exact safe message, exit,
  nonblocking behavior, and help route.

### UX-P1.1-003: Runnable Python API first success

- Resolution commit: `e5969edd822ea5ccb31171f6c74e0ba690fd2294`.
- Result at `75b7d41316216a3b18a3c56ff0c98f133f7aab89`:
  **RESOLVED**. The runtime-only example and exact output remain runnable.

## Positive controls preserved

- Mixed evidence defects now remain evidence-validation results rather than
  surfacing as an internal tool failure.
- Primary issue and next action are deterministic; JSON retains all bounded,
  unique static issues in canonical order.
- `PAIR_VALID` still does not imply native dbt success or complete capture.
- Reports and errors remain allowlisted and exclude raw SQL, messages, paths,
  environment values, project/resource/invocation identity, and artifact text.
- Stable exits, named flags, abbreviation rejection, linear text labels,
  non-TTY behavior, and no-color semantics remain intact.
- The keyword-only API opens no caller path, retains no raw bytes, and performs
  no network, Databricks, dbt, environment, clock, or subprocess access.
- No Databricks App, Job, SQL warehouse, cluster, serverless environment, Unity
  Catalog object, Azure resource, authentication flow, or paid compute was
  accessed or started.

## Later-gate follow-ups

The prior nonblocking follow-ups remain outside P1.1:

1. **D1/D1P, documentation owner:** rendered navigation, distributed help,
   responsive layout, keyboard, representative screen-reader, and WCAG 2.2 AA
   process validation.
2. **P10/D8, distribution/install owner:** a checksum-bound disconnected source
   only if later distribution promises disconnected first installation.
3. **Later P1/P8, capture owner:** independently sanitized real Azure
   Databricks success, failure, cancellation, timeout, retry, and repair
   qualification before runtime or capture-completeness claims.

## Resolution and re-review

- Resolution: `75b7d41316216a3b18a3c56ff0c98f133f7aab89` canonicalizes every
  invalid-report issue set before constructing the closed report.
- Validation: Mixed parse and semantic API/CLI probes, prior onboarding and
  recovery journeys, repeated deterministic non-TTY/no-color output,
  navigation, 90 tests, Ruff, `ty`, regeneration, runtime-only setup, API
  example, wheel/installed command, Bash syntax, and ShellCheck all passed.
- Current defects: none.
- Re-review verdict: **PASS_WITH_FOLLOW_UP**. P1.1 is safe to accept; only the
  previously named later-gate work remains.
