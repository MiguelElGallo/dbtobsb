# P1.1 artifact-pair inspector usability and onboarding review

- Commit/diff: `054527a6721c36af6a9e99218120b39920bd0fed`
- Date: 2026-07-15
- Reviewer: independent usability, onboarding, and text-interface specialist
- Verdict: **CHANGES_REQUIRED**
- Cloud/authentication activity: none

## Executive verdict

The P1.1 interaction model is strong. A non-author can follow one short local journey,
the three fixtures honestly distinguish pair validity from native dbt outcome and future
capture state, successful and invalid reports are deterministic and evidence-safe, and
the CLI behaves correctly in a non-TTY without color or spinner state. The complete
local quality gate passed, including the installed-wheel console entry point.

The part is not yet ready for acceptance because three current onboarding defects remain:

1. the quickstart calls the whole journey offline even though a clean `uv sync` can require
   package-index and Python downloads and currently installs the development group;
2. the common input-read failure emits only an opaque code and is not routed to recovery by
   the guide that actually describes it; and
3. the advertised Python API has no copy-ready first-success example or expected output.

These are current P1.1 defects, not later product gates, so the appropriate verdict under
the repository review process is `CHANGES_REQUIRED`.

## Sources checked

- Repository [review process](../../plans/review-process.md), especially the P1 focus on
  actionable validation errors and the required finding/verdict rules.
- Repository [P1.1 product boundary](../../plans/product-plan.md#p11-implemented-boundary).
- Repository [D1P documentation contract](../../plans/documentation-plan.md#navigation-and-page-traceability-contract).
- [uv CLI reference](https://docs.astral.sh/uv/reference/cli/) — `--offline` uses only
  locally cached or locally available data, and `--no-dev` excludes the development group.
- [uv dependency groups](https://docs.astral.sh/uv/concepts/projects/dependencies/#development-dependencies)
  — the `dev` group is included by default by `uv sync` and `uv run`.
- [Python Packaging entry-point specification](https://packaging.python.org/en/latest/specifications/entry-points/)
  — installed `console_scripts` provide the supported command wrapper.
- [dbt artifact reference](https://docs.getdbt.com/reference/artifacts/dbt-artifacts),
  [manifest reference](https://docs.getdbt.com/reference/artifacts/manifest-json), and
  [run-results reference](https://docs.getdbt.com/reference/artifacts/run-results-json) for
  the user-visible evidence distinctions and sensitive-field boundary.

## Acceptance criteria reviewed

- One safe, clear developer journey with no Databricks credentials, paid compute, SQL,
  profile, internal ID, or user-selected dbt command.
- First successful inspection in less than ten minutes after stated prerequisites.
- Invalid-pair diagnosis and return to a known valid pair in less than five minutes.
- Usable Python API, CLI, report, exits, and recovery messages.
- Deterministic text and JSON in a non-TTY, under `NO_COLOR`, with no ANSI sequence,
  spinner, cursor rewrite, or color-only meaning.
- Safe normal output, exception handling, representations, and issue text.
- Honest synthetic-fixture provenance and no live-runtime claim.
- Correct three-question mental model: pair validity, native dbt outcome, and capture state.
- Developer navigation from repository index to tutorial, how-to, reference, and explanation.
- Reproducible local test, lint, type, wheel, and installed-command evidence.

## Review execution and observed results

The commit was checked out detached in an isolated worktree. Its source worktree remained
clean. The documented tutorial was followed from the repository root without inspecting
implementation details first.

| Step | Exit | Observed result |
| --- | ---: | --- |
| `uv sync --project capture --locked` | `0` | Created the environment and installed 16 packages, including the default development group. |
| Valid-success fixture | `0` | Exact documented `PAIR_VALID`, `success=1`, and capture-state caution. |
| Valid-dbt-failure fixture with `--json` | `0` | Exact documented deterministic JSON with `PAIR_VALID` and `error=1`. |
| Invocation-mismatch fixture | `10` | Exact documented code, impact, and one next action. |

The setup plus all three tutorial inspections completed in approximately 24 seconds on
this machine with an already populated uv cache. This satisfies the local under-ten-minute
first-success target but does not prove a clean offline setup; finding `UX-P1.1-001`
addresses that distinction.

A second invalid-to-valid exercise completed in 15 seconds. The mismatch message made the
three relevant facts clear and the packaged valid pair returned exit `0`. The separate
input-read path did not provide comparable recovery guidance; see `UX-P1.1-002`.

The following additional checks passed:

```text
scripts/check_capture.sh
55 passed
Ruff check: passed
Ruff format: passed
ty: passed
wheel build and isolated console-entry-point inspection: passed
DBTOBSB_CAPTURE_CHECK_PASSED
```

Direct non-TTY runs under `NO_COLOR=1` and `TERM=dumb`, with and without `--no-color`,
contained no ANSI sequence and preserved the same meaning. Repeated JSON output was
byte-identical. A manual API probe using the checked-in successful fixture also returned
`PAIR_VALID`; the implementation works, but that runnable probe is absent from the reader
journey.

No Databricks App, Job, SQL warehouse, cluster, serverless environment, Unity Catalog
object, Azure resource, authentication flow, or paid compute was accessed or started.

## Findings

### UX-P1.1-001: The documented offline journey can require undeclared downloads and unnecessary development packages

- Verdict and severity: **CHANGES_REQUIRED — high**
- Affected behavior: `README.md` lines 15-20,
  `docs/developers/tutorials/inspect-an-artifact-pair.md` lines 3-13, the default
  `uv sync`/`uv run` command form, and the “offline capture gates” workflow label.
- Evidence: The tutorial says the entire journey is offline and the README says P1.1 runs
  offline immediately before `uv sync --project capture --locked`. uv officially defines
  offline mode as using only cached or locally available data and includes the `dev` group
  by default. With a fresh empty cache and separate environment, the reviewed project command
  with `--offline` failed before first value because a locked development package was not
  locally available. The documented normal sync installed 16 packages, including
  Hypothesis, pytest, Ruff, and `ty`. A runtime-only probe using `--no-dev` installed seven
  packages and successfully produced the same `PAIR_VALID` output.
- User/system impact: A reader in the stated regulated environment can reasonably treat
  “the entire journey is offline” as a zero-egress assurance. On a clean workstation it can
  instead contact a Python/package registry or fail without a recovery route. Installing
  test and lint tooling for a read-only inspection also widens the first-use dependency and
  download surface without providing user value.
- Required change: State precisely that artifact inspection is offline after installation,
  while initial Python/package preparation may require an approved registry, mirror, or
  populated cache. Use and test a runtime-only quickstart such as `uv sync ... --no-dev`
  and the matching `uv run ... --no-dev`. Before the first action, disclose possible Python
  and package downloads and give one approved-network/mirror/cache recovery route. If P1.1
  intends to promise a truly disconnected first install, provide and test the checksum-bound
  local wheel/dependency source and use `--offline`; otherwise explicitly say that route is
  not yet shipped. Rename any gate whose “offline” label includes dependency bootstrap, or
  define the label narrowly enough that it cannot be read as a no-network assertion.
- Resolution: Open at the reviewed commit.
- Re-review outcome: Pending.

### UX-P1.1-002: Exit 3 is safe but not actionable at the point of failure

- Verdict and severity: **CHANGES_REQUIRED — medium**
- Affected behavior: `capture/src/dbtobsb_capture/cli.py` lines 111-116,
  `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md` lines 3 and 20-37, and
  developer-index recovery navigation.
- Evidence: A missing input, symbolic link, non-regular file, or over-limit file returns
  exit `3` and exactly `DBTOBSB_INPUT_READ_ERROR` on stderr. This correctly exposes neither
  the supplied path nor an exception, but it gives no impact, safe next action, or
  documentation route. The only guide that explains exit `3` opens by saying it applies to
  `PAIR_INVALID` or exit `10`; exit `3` produces neither. The CLI reference contains the
  necessary facts, but the failing user is not directed there.
- User/system impact: A path typo or unsupported file shape is one of the most likely
  first-use errors. The user cannot tell from the command whether to recollect, close,
  resize, or replace the file and must discover a differently scoped guide. The current
  surface therefore does not demonstrate the requested under-five-minute recovery for this
  common branch, despite the P1 review focus on actionable errors.
- Required change: Preserve the non-disclosure behavior but add one static impact and one
  static recovery action, plus a stable documentation code/route, to the exit-3 text. Update
  the how-to entry condition and developer index so an input-read user is explicitly routed
  there. Add exact stderr tests for missing, symbolic-link, non-regular, and over-limit cases,
  continuing to assert that canary paths and exception text are absent. Do not expose the
  rejected path or require the user to repair artifact content manually.
- Resolution: Open at the reviewed commit.
- Re-review outcome: Pending.

### UX-P1.1-003: The public Python API has no runnable first-success journey

- Verdict and severity: **CHANGES_REQUIRED — medium**
- Affected behavior: `docs/developers/reference/python-api.md` lines 5-20 and the
  CLI-only developer tutorial.
- Evidence: The API reference shows `inspect_artifact_pair(manifest=manifest_bytes,
  run_results=run_results_bytes)`, but neither variable is defined, there is no copy-ready
  command using the checked-in fixtures, and no exact API result or serialization example
  is shown. The CLI tutorial is complete, but a library integrator must invent byte loading,
  report inspection, and JSON rendering before reaching the documented API outcome.
- User/system impact: The repository advertises both a Python API and a developer/integrator
  route. A CLI user succeeds without guessing; an API consumer does not receive equivalent
  first-value evidence or a tested example. This leaves a supported surface outside the
  under-ten-minute onboarding proof.
- Required change: Add one tested, copy-ready Python API example using the sanitized
  successful fixture. Keep file reading outside `inspect_artifact_pair`, print the exact
  `PairState`, demonstrate safe `to_dict()` serialization, and show the expected output.
  Include an invalid-report example or link directly to its recovery contract. Test the
  published snippet or provide a checked-in example script invoked by documentation CI.
- Resolution: Open at the reviewed commit.
- Re-review outcome: Pending.

## Positive controls to preserve

- `PAIR_VALID` never means dbt success or capture completeness. The valid-error fixture and
  final three-question tutorial checkpoint make this unusually clear.
- The fixture set is explicitly synthetic and sanitized, `runtime_evidence=false` is
  checksum-bound in provenance, and the evidence record does not call a local parse a live
  Databricks qualification.
- Text output is linear, concise, screen-reader-friendly, and independent of color,
  animation, cursor position, or interaction.
- JSON is compact, key-sorted, versioned, deterministic, and bounded. Valid summaries and
  invalid issues are mutually exclusive.
- Validation issues contain static code/category/impact/action fields without observed
  values. Raw SQL, messages, environment values, paths, relation names, project/resource
  identifiers, and invocation identifiers remain absent from report, text, JSON, exception,
  and ordinary representation tests.
- The CLI refuses abbreviated flags, accepts named inputs, uses stable exits, rejects unsafe
  local file shapes, and sanitizes usage, input, and internal failures.
- The pure keyword-only API retains no raw bytes and performs no filesystem, environment,
  clock, subprocess, dbt, Databricks, or network access.
- Navigation from `docs/index.md` to `docs/developers/index.md` exposes tutorial, recovery,
  reference, and explanation destinations with descriptive link text.

## Required acceptance evidence

Before re-review, provide one new immutable commit proving:

1. corrected installation/network wording in README, tutorial, workflow labels, and any
   evidence that calls dependency bootstrap offline;
2. a tested runtime-only quickstart, plus an honest tested disconnected or approved-mirror
   route and its failure recovery;
3. exact safe, actionable exit-3 output and navigation, with no path or exception leakage;
4. a tested copy-ready Python API example with exact output;
5. unchanged deterministic reports, exits, canary exclusions, non-TTY/no-color behavior,
   fixture provenance, all 55 or successor tests, Ruff, `ty`, wheel smoke, and local link
   validation; and
6. a repeated non-author journey recording first success under ten minutes and both
   invalid-pair and input-read recovery under five minutes.

## Resolution and re-review

- Resolution: No resolution is present in commit
  `054527a6721c36af6a9e99218120b39920bd0fed`.
- Validation: The positive controls and local gates above pass, but findings
  `UX-P1.1-001` through `UX-P1.1-003` remain open.
- Re-review verdict: **CHANGES_REQUIRED**.
