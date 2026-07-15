# Final usability regression re-review: P1.1 artifact-pair inspector

- Commit/diff: `bedfaa9d9e803c168c2481d5e4f18264a1f40e01`
- Date: 2026-07-15
- Reviewer: independent usability, onboarding, and text-interface specialist
- Verdict: **PASS_WITH_FOLLOW_UP**
- Cloud/authentication activity: none

## Executive verdict

The post-`e5969edd822ea5ccb31171f6c74e0ba690fd2294` constructor, schema,
registry, and reference-documentation changes introduce no usability regression.
At exact commit `bedfaa9d9e803c168c2481d5e4f18264a1f40e01`, a non-author still reaches
first value through the seven-package runtime-only path, receives the exact
documented recovery messages and API output, and can interpret valid, invalid,
and native dbt outcomes without confusing them with capture completeness.

The new primary-issue precedence is understandable at each reader level. The
how-to tells an operator to use the first code and its one next action. The CLI
reference defines `issues[0]` as primary and describes the closed registry. The
Python reference adds the stricter constructor rule without changing the
ordinary inspection journey. A deliberate two-issue pair confirmed that text
shows the correct primary action while JSON retains both issues in canonical
order.

`UX-P1.1-001`, `UX-P1.1-002`, and `UX-P1.1-003` remain resolved. No current
P1.1 usability defect was found. The existing rendered-documentation,
distribution, and real-runtime follow-ups remain later-gate work and do not
block acceptance of this part.

## Scope and acceptance criteria

This independent regression checked:

- the exact immutable commit and its diff from the prior accepted candidate;
- installation-egress versus offline-after-installation wording;
- the runtime-only first-success tutorial and its time-to-value;
- valid dbt failure, invalid-pair, input-read, and return-to-valid journeys;
- the checked-in Python API example and exact output;
- missing, symlink, FIFO, device, and over-limit exit-3 behavior;
- deterministic text and JSON in redirected non-TTY/no-color conditions;
- linear text semantics, stable exits, safe usage, and recovery labels;
- multi-issue ordering, primary selection, JSON retention, and constructor
  rejection of reversed precedence;
- developer navigation and local link targets;
- the three-question pair/dbt/capture mental model and synthetic-fixture
  honesty; and
- the complete local capture quality gate.

The work ran in a detached worktree at
`bedfaa9d9e803c168c2481d5e4f18264a1f40e01`. It did not edit reviewed files,
run dbt, authenticate to Azure or Databricks, or start cloud or paid compute.

## Task evidence

### Runtime-only first success and boundaries

From a new dedicated uv cache and environment, the documented setup installed
exactly seven runtime packages with:

```text
uv sync --project capture --locked --no-dev
Prepared 7 packages
Installed 7 packages
```

The first inspection then ran under `UV_OFFLINE=1`, `TERM=dumb`, `NO_COLOR=1`,
and `--no-sync`. It exited `0` with the unchanged exact text:

```text
PAIR_VALID
The files satisfy the pinned artifact-pair contract.
dbt_version: 1.11.12
adapter_type: databricks
command: build
result_count: 1
status_counts: success=1
next_action: Evaluate outer run and archive evidence before claiming capture state.
```

Setup plus first value took approximately two seconds on this machine, well
inside the ten-minute target. README and tutorial wording remain explicit that
initial package preparation can use an approved index, mirror, or populated
cache; only inspection after installation is called offline; and no
disconnected wheelhouse is shipped.

The valid-dbt-failure fixture still exited `0` with `PAIR_VALID` and `error=1`.
The invocation-mismatch fixture exited `10` with one clear impact and next
action, then the valid pair returned exit `0`; the three-command exercise took
approximately two seconds. This remains comfortably inside the five-minute
recovery target without presenting the machine-local timing as a universal
performance promise.

The final tutorial checkpoint still asks three separate questions:

1. whether the pair is valid;
2. what native outcomes dbt recorded; and
3. whether dbtobsb capture is complete, which P1.1 explicitly cannot answer.

The fixtures and evidence remain labeled synthetic and sanitized, with
`runtime_evidence=false`; no local output is presented as real Azure Databricks
runtime evidence.

### Exact exit recovery

Missing, symbolic-link, FIFO, `/dev/null` device, and
128-MiB-plus-one-byte regular-file inputs were exercised separately. All five
cases returned exit `3` immediately, produced zero stdout bytes, and emitted
byte-identical stderr with SHA-256
`5aaabc86350569e379d5976a7efe5dd0bf5f026c4d675d024d0243284b1a7a9d`:

```text
DBTOBSB_INPUT_READ_ERROR
impact: One or both inputs could not be read as closed regular files within 128 MiB.
next_action: Provide existing, closed, non-symlink regular files no larger than 128 MiB.
help: docs/developers/how-to/diagnose-an-invalid-artifact-pair.md#recover-an-input-read-error
```

No path, exception, or artifact content was disclosed. The local help heading
exists, the developer index routes exit-3 readers to the guide, and the guide
continues to exclude pipes, devices, and symbolic links explicitly.

### Python example and report readability

The checked-in API command ran under `UV_OFFLINE=1` and `--no-sync`, exited `0`,
wrote no stderr, and produced the same exact two documented lines: `PAIR_VALID`
plus the sorted compact safe JSON report with `success=1`. File reading remains
outside `inspect_artifact_pair`; the example still supplies all byte loading,
API invocation, state reading, and deterministic serialization needed for first
success.

Two redirected runs of both text and JSON under `TERM=dumb`, `NO_COLOR=1`,
`CI=1`, `UV_OFFLINE=1`, and `--no-sync` were byte-identical. Their hashes remain
the same as the prior accepted candidate:

```text
text  6dc2e98d982f1f57be246b224b7b1406d06e1a19794dee7145ef3e1c1c6f67b1
json  a5a39e26af3a99d759a6687cb24e91f29d4b81b86c570d1cd64b4fbc60e0707a
```

No checked stream contained ANSI escapes. Output meaning remains independent of
color, cursor position, animation, a spinner, or interaction. The state and
`code`, `impact`, `next_action`, and `help` labels form a linear reading order.
Missing required arguments still return safe exit `2`, usage, and
`DBTOBSB_CLI_USAGE_ERROR` without rejected argument values.

### Primary-precedence clarity

A copy of the successful run-results fixture was changed to contain both a
different valid invocation ID and an unsupported `run` command. Inspection
returned these two issue codes in this order:

```text
DBT_INVOCATION_ID_MISMATCH
DBT_COMMAND_UNSUPPORTED
```

JSON retained both static issues. Text returned only
`DBT_INVOCATION_ID_MISMATCH` with its recollection action, matching the how-to's
instruction to read the first code and next action. `report.primary_issue`
returned that same first issue. Passing the reversed issue tuple to the public
report constructor raised the safe, deterministic error:

```text
ValueError: issues must follow the closed v1 precedence
```

The documentation keeps three useful layers separate:

- the how-to gives the operator one action without exposing constructor rules;
- the CLI reference states that invalid reports contain one to 20 unique static
  issues, that `issues[0]` is primary, and that codes and primary selection are
  a versioned contract; and
- the Python reference explains that returned issues are canonically ordered
  and that public constructors reject wrong types, duplicates, oversized issue
  sets, and noncanonical precedence before an object exists.

This is sufficient to interpret and automate the report without treating array
order as incidental. The added constructor/schema detail stays in reference
material and does not interrupt the choice-free tutorial or recovery guide.

### Navigation and complete gate

A reader route through README, capture README, documentation index, tutorial,
how-to, CLI/API reference, and explanation resolved 36 relative links with zero
missing targets. The input-read help anchor exists. The detached source
worktree remained clean after validation.

The exact commit passed:

```text
scripts/check_capture.sh
85 tests passed
Ruff check and format: passed
ty: passed
report-schema and fixture regeneration: passed
seven-package runtime-only quickstart: passed
checked-in Python API example: passed
wheel build and isolated installed command: passed
DBTOBSB_CAPTURE_CHECK_PASSED
bash -n and ShellCheck for scripts/check_capture.sh: passed
```

The added tests cover Python/JSON constructor parity, unique and bounded issue
sets, canonical full-tuple precedence, rejected reversed primary precedence,
and unchanged deterministic output.

## Original finding status

### UX-P1.1-001: Offline wording and runtime-only setup

- Resolution commit: `e5969edd822ea5ccb31171f6c74e0ba690fd2294`.
- Regression result at `bedfaa9d9e803c168c2481d5e4f18264a1f40e01`:
  **RESOLVED**. The honest download boundary, seven-package `--no-dev` setup,
  and offline `--no-sync` inspection all remain intact and passed.

### UX-P1.1-002: Actionable safe exit-3 recovery

- Resolution commit: `e5969edd822ea5ccb31171f6c74e0ba690fd2294`.
- Regression result at `bedfaa9d9e803c168c2481d5e4f18264a1f40e01`:
  **RESOLVED**. All five input shapes retained the exact safe actionable message,
  stable exit, nonblocking behavior, and valid help route.

### UX-P1.1-003: Runnable Python API first success

- Resolution commit: `e5969edd822ea5ccb31171f6c74e0ba690fd2294`.
- Regression result at `bedfaa9d9e803c168c2481d5e4f18264a1f40e01`:
  **RESOLVED**. The checked-in example and exact documented output remain
  runnable through the runtime-only offline-after-installation path.

## Positive controls preserved

- `PAIR_VALID` remains pair evidence, not a dbt-success or capture-completeness
  label.
- Valid native failures remain visible without relabeling the pair invalid.
- Primary issue selection is deterministic and gives exactly one immediate
  recovery action in text, while JSON preserves the bounded static issue set.
- Reports remain allowlisted and omit raw SQL, messages, paths, environment
  values, relation/project/resource/invocation identities, and artifact text.
- CLI exits, required named flags, abbreviation rejection, non-TTY behavior,
  no-color semantics, and safe internal/usage errors remain unchanged.
- The keyword-only API still opens no caller path, retains no raw bytes, and
  performs no network, Databricks, dbt, environment, clock, or subprocess
  access.
- No Databricks App, Job, SQL warehouse, cluster, serverless environment, Unity
  Catalog object, Azure resource, authentication flow, or paid compute was
  accessed or started.

## Later-gate follow-ups

The prior nonblocking follow-ups remain correctly outside P1.1:

1. **D1/D1P, documentation owner:** validate the rendered journey, accepted
   distributed help destination, search, responsive layout, keyboard use,
   representative screen reader, and WCAG 2.2 AA process.
2. **P10/D8, distribution/install owner:** ship and test a checksum-bound
   disconnected source only if the later product promises disconnected first
   installation; until then retain the explicit non-claim.
3. **Later P1/P8, capture owner:** qualify independently sanitized real Azure
   Databricks success, failure, cancellation, timeout, retry, and repair
   evidence before runtime or capture-completeness claims.

## Resolution and re-review

- Resolution: The constructor/schema hardening in
  `bedfaa9d9e803c168c2481d5e4f18264a1f40e01` preserves all accepted onboarding
  and text-interface behavior from `e5969edd822ea5ccb31171f6c74e0ba690fd2294`.
- Validation: Complete non-author fixture journey, five exit-3 shapes, API
  example, two-issue precedence probe, deterministic non-TTY/no-color output,
  navigation, 85 tests, Ruff, `ty`, regeneration, runtime-only install,
  wheel/installed command, Bash syntax, and ShellCheck all passed.
- Current defects: none.
- Re-review verdict: **PASS_WITH_FOLLOW_UP**. The immutable P1.1 part is safe to
  accept; only the named later-gate work remains.
