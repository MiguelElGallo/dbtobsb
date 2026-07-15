# Documentation usability/accessibility review: P1.1 artifact-pair inspector

- Review date: 2026-07-15
- Reviewer: independent source-level documentation usability/accessibility reviewer
- Immutable reviewed commit: `2b76abbd565271b30f37fdb1e3f00d76185e8dc4`
- Reviewed tree: `24d4fb122ee6a167bf2ae529034ee17013b30024`
- Immediate parent: `7ce722cddfed42f1e96741bb07b6cd8762127f22`
- Verdict: **CHANGES_REQUIRED**
- Findings: `DOCUX-P1.1-001` and `DOCUX-P1.1-002`
- Cloud, Databricks, authentication, dbt, and paid-compute activity: none
- Rendered-site/browser/WCAG result: explicitly deferred; no site configuration or rendered artifact exists

## Executive verdict

The P1.1 source documentation has a strong reader model. Its entry routes expose
the current local capability before the older P0 smoke, the developer landing
separates outcomes from lookup and explanation, the tutorial reaches first value
with synthetic data, and failure recovery is deterministic and safe. Headings,
links, lists, callout text, and fenced examples are generally linear and
meaningful without color or interaction.

Two current source defects prevent acceptance:

1. the raw-artifact handling how-to presents a bare `dbtobsb-capture` command,
   but the only reader-facing runtime preparation installs the executable in
   the uv project environment and every runnable inspection elsewhere uses
   `uv run --project capture --no-sync`; and
2. the Python API public-types table contains two unescaped `|` characters in
   inline union types. Under GitHub Flavored Markdown (GFM), that two-column row
   parses as four cells and excess cells are ignored, truncating the rendered
   `ArtifactPairReport` contract and breaking its intended header relationship.

These are source-level copy/paste and information-structure problems in the
current P1.1 part, not future-site preferences. The repository gates pass but do
not detect either defect. The appropriate verdict under the repository review
process is therefore `CHANGES_REQUIRED`.

No browser, generated HTML, responsive viewport, keyboard, focus, contrast,
screen-reader, or WCAG conformance claim is made. Those checks remain mandatory
after a documentation renderer and publication artifact exist.

## Review basis and limits

Repository acceptance was evaluated against:

- [Review process](../../plans/review-process.md), especially the dedicated
  documentation usability/accessibility pass, actionable-error requirement,
  and verdict definitions;
- [Documentation plan](../../plans/documentation-plan.md), especially the P1.1
  page registry, reader roles, prerequisites, search terms, and required
  evidence;
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/), as the current W3C web-content
  accessibility recommendation;
- W3C guidance for [Info and Relationships](https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships.html),
  [Headings and Labels](https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels),
  [Link Purpose (In Context)](https://www.w3.org/WAI/WCAG22/Understanding/link-purpose-in-context.html),
  and [Reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html); and
- the formal [GitHub Flavored Markdown table specification](https://github.github.com/gfm/#tables-extension),
  which requires a literal pipe in a table cell to be escaped, including inside
  an inline span, and defines excess body cells as ignored.

W3C's success criteria apply to rendered web content and require a combination
of automated and human evaluation. This review uses them only to identify
source implications that can be determined from Markdown. It does not convert a
source review into a WCAG audit.

## Immutable scope and hashes

`HEAD` matched the immutable commit and the worktree was clean before review and
validation. Reviewed bytes were read from the named Git revision. This report is
outside the frozen input, and no reviewed source or prior report was edited.

The reader-route set covers the four P1.1 entry surfaces and all seven registered
leaf pages, in the order below:

| SHA-256 | Reviewed source |
| --- | --- |
| `0be609fbbb0239d7dbb1142dcd630fa94f0a7b13ba9af7940b65f08d9d48c5cf` | `README.md` |
| `d664454aa140415fc822398a217d62bb57cffc41c647fee46da98213fa0e6e19` | `capture/README.md` |
| `2b6fece0e8ca96e2407e14f1bd8e5df90dbad39495feaefbd74914541bbc7fe2` | `docs/index.md` |
| `8867bd6d28b38d7c22bfe1bb2c2affead9b737f64311b8c7d2c519544d6c0ceb` | `docs/developers/index.md` |
| `4a005dacbbdb3d89f1c97d21b1ad9e5f98eb148f622fa7e0dfa53d52f2d79296` | `docs/developers/tutorials/inspect-an-artifact-pair.md` |
| `196ae6032b6ea8e2fe19b84cdb6ae9e2bdb15f90af41e0202e02ed033ca2eae8` | `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md` |
| `59f10d13d45d85a13eb4d903bfc76e245621f09d13348b2c8b1676af46fedd46` | `docs/developers/how-to/handle-raw-dbt-artifacts-safely.md` |
| `462117759f5eb09588f843e91c603a1e7ef8ef405d99d71423fe3229582a8aab` | `docs/developers/reference/cli-report-and-exit-codes.md` |
| `d6163c7b4ae07db5bb6b033f20c527a48f9912b7a4b382b80ad39807cdac1dc2` | `docs/developers/reference/python-api.md` |
| `3221cd5c38a3b5d9fdace49cb19a07efdc945fec9d3a0af1bfebbe0c5911e48e` | `docs/developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md` |
| `653d6befeb6791974362e5ceb29cedd14980cf92b01a92f4eb2981e1c822b990` | `docs/developers/explanation/raw-artifact-custody.md` |

The SHA-256 of the literal path-ordered `shasum -a 256` record stream for the
reader set is:

```text
8c88e29fc0a9f237de972ee70d006b328ad6d3faef3ce355a3c74b034bf593c4
```

The executable corroboration set is:

| SHA-256 | Validation input |
| --- | --- |
| `3653fe330b9dd660f959803c98337053980c9ea24cd30be904025f01ff90b8f9` | `capture/tests/test_documentation.py` |
| `9ec9e35e7362cbe2907483e344c2979bd886b9586b03d35b465d93e533ec5099` | `capture/examples/inspect_valid_fixture.py` |
| `92656cda84b66dd76338cec050c35e632ae50de015bda89e474d28a74854b911` | `scripts/check_capture.sh` |
| `aa904ffdd5540d2604b840c42d8d04660c03c57e0d1f818355fc524dbd40b0c0` | `scripts/check_markdown_links.py` |
| `69f1367bf81be14cf166626251e734854655871c95dd1624015c11a10e2a8935` | `capture/pyproject.toml` |
| `fb09543bcd8cbca30786135e5879465181efd8d0e6e92b452d1bfffcba68b461` | `capture/uv.lock` |

Its path-ordered record-stream SHA-256 is:

```text
8dbea64125cd9430b0e984cb83a51956042c730ffcf666df9f0e93a1c9f71897
```

The governance inputs have these exact hashes:

```text
d293175884cb5d1cb1916609cf490aac8189856535317b9061eb8267c0941a0d  docs/plans/review-process.md
b753b2d568e246bceefefe806d1ebd5bb47eadf8e7a32d95a557f03471e0623e  docs/plans/documentation-plan.md
```

## Reader-route assessment

| Surface | Reader need | Source result |
| --- | --- | --- |
| Repository README | Discover current capability and reach first value | **Pass.** P1.1 appears before the longer P0 smoke, states its non-goals, warns before real input, and gives the runtime-only setup plus synthetic first-success command. |
| Capture README | Orient a package consumer | **Pass.** It states one operation, the offline-after-installation boundary, the two status non-claims, and routes to tutorial, references, and raw handling. |
| Documentation index | Choose planning, P0, or P1.1 | **Pass.** The dedicated artifact-pair section links directly to the tutorial and raw-input task without presenting P1.1 as live Databricks capture. |
| Developer landing | Choose task, lookup, or explanation | **Pass.** Descriptive link text and three short groups separate outcomes, machine contracts, and mental models. |
| Tutorial | Reach first value and learn the three outcomes | **Pass.** Reader, repository-root environment, Python/uv prerequisites, dependency-egress boundary, synthetic fixtures, commands, exact outputs, exits, and next routes are visible in order. |
| Invalid-pair how-to | Recover from exit `10` or `3` | **Pass.** Entry conditions, primary action, eight concise issue families, detailed recovery anchors, rerun verification, and safe support escalation are explicit. |
| Raw-artifact how-to | Inspect real evidence within approved custody | **Changes required.** Role, policy prerequisites, stop condition, lifecycle, and support controls are strong, but its runnable command is outside the only documented runtime environment. See `DOCUX-P1.1-001`. |
| Python API reference | Look up callable, types, limits, output, and interpretation | **Changes required.** The copy-ready example and contract are strong, but the public-report row is malformed under GFM. See `DOCUX-P1.1-002`. |
| CLI/report reference | Look up flags, exits, safe report, and issues | **Pass at source.** Stable named flags, exact output, descriptive recovery links, and a complete issue registry support keyboard-independent text use. The long five-column registry still requires rendered reflow and screen-reader testing. |
| Pair-state explanation | Avoid false success/completeness | **Pass.** One three-row comparison and short sections preserve the three-question model and hand action back to task pages. |
| Raw-custody explanation | Understand safe output versus sensitive input | **Pass.** The two meanings of local and the CLI/API custody boundaries are concise and link back to the action page. |

## Source-level accessibility and usability results

### Structure, headings, and serial reading

The 11 reader pages contain 11 H1 headings and 61 headings total. Every page has
exactly one H1, no ATX level is skipped, and headings describe the topic or
reader action. Ordered task headings remain meaningful when read without visual
styling. Lists and paragraphs preserve the relevant relationships in text.

The warning callouts do not depend on color, icon shape, or position: their
labels say `Sensitive input boundary` or `Before using real files`, and the same
warning content remains understandable as plain serial text. Whether a future
renderer exposes them as an appropriate note/alert structure cannot be inferred
from blockquote Markdown and remains deferred.

### Links and navigation

The reader set contains 95 inline Markdown links. The source scan found zero
generic labels such as `here`, `click here`, `more`, `read more`, `this`, or
`link`. Destination purpose is named either by the page/task title or by the
same sentence. The revision-aware repository checker found zero missing files,
repository escapes, or invalid fragments across all tracked Markdown.

These results support source-level link purpose and route continuity. They do
not prove rendered focus order, focus visibility, target size, breadcrumb
behavior, generated previous/next links, or search behavior.

### Code and command safety

The reader set contains 21 fenced code blocks. Every fence is closed and has a
language label (`bash`, `text`, `json`, or `python`). Commands and outputs use
separate blocks; no meaning depends on syntax color. Synthetic examples use
checked-in paths. Recovery placeholders are visibly quoted, and the input-read
path does not echo a local path.

The tutorial's CLI and Python commands execute exactly as published. The
raw-artifact how-to is the exception: its bare executable is not available after
the documented uv project preparation unless the reader guesses an activation
or different installation step. See `DOCUX-P1.1-001`.

### Tables and cognitive load

The reader set contains nine GFM-style tables. Header labels are non-empty, and
tables are used for relationships rather than visual layout. The pair-state,
exit, machine-report, custody, and concise recovery-family tables reduce
cognitive load. The full 26-row issue registry is kept in reference while the
how-to provides eight recovery families, which is appropriate progressive
disclosure.

Eight tables have consistent source cell counts. The Python public-types table
has one malformed row because type-union pipes were not escaped. See
`DOCUX-P1.1-002`. The long issue registry and wide inline JSON/code examples
must still be tested for reflow, horizontal scrolling, zoom, table-header
associations, and screen-reader navigation in the eventual renderer.

### Failure recovery and mental model

The published journey provides stable exits, exact safe text, one primary issue,
one next action, and a real help fragment. Exit `0` is explicitly limited to
pair validity, native dbt outcomes are read separately, and capture completeness
is left unevaluated. Recovery says recollect or rerun rather than edit evidence
to make it pass. Ordinary support context is allowlisted and the exceptional
raw-evidence route is explicit.

This is strong cognitive and error-recovery design. The two findings do not
weaken the machine behavior; they prevent the source documentation itself from
being accepted as a fully runnable and reliably structured route.

## Validation executed

The exact reviewed commit passed the repository-owned gates:

```text
uv lock --check --project capture
passed

scripts/check_capture.sh
94 tests passed
tracked_markdown_files=120
local_links=188
fragments=53
errors=0
Ruff check and format: passed
ty: passed
report-schema and fixture regeneration: passed
runtime-only installation and checked-in API example: passed
wheel build and isolated installed CLI: passed
DBTOBSB_CAPTURE_CHECK_PASSED

scripts/check_markdown_links.py --revision 2b76abbd565271b30f37fdb1e3f00d76185e8dc4
tracked_markdown_files=120
local_links=188
fragments=53
errors=0

bash -n scripts/check_capture.sh
passed

shellcheck scripts/check_capture.sh
passed

git diff --check
passed before this report was created
```

The exact documented local journeys were also executed with `UV_OFFLINE=1`,
`TERM=dumb`, `NO_COLOR=1`, and `--no-sync` after runtime preparation:

| Journey | Exit | Result |
| --- | ---: | --- |
| Valid-success CLI | `0` | Exact `PAIR_VALID`, `success=1`, and capture-state caution; stderr empty. |
| Valid dbt-failure JSON | `0` | Exact `PAIR_VALID` with `error=1`; stderr empty. |
| Invocation mismatch | `10` | Exact safe code, impact, and recollection action; stderr empty. |
| Checked-in Python API example | `0` | Exact displayed state and compact safe JSON; stderr empty. |
| Missing-input recovery | `3` | Exact static impact, next action, and valid help fragment; stdout empty. |

Observed output hashes were:

```text
6dc2e98d982f1f57be246b224b7b1406d06e1a19794dee7145ef3e1c1c6f67b1  valid-success text
f632c1bde08347d59673749108c0f888e2984ac10eaae0bfc47cf3ee7a501c46  valid dbt-failure JSON
24b8965cb09df9c64e2598204f5bd2421a10da3f7d2f5182a73f1fc1ff71211b  invocation-mismatch text
f53fd7c0ec2308b1239d6c4edf0f4fa057035c21da9ad58358ed651053519aae  Python example output
5aaabc86350569e379d5976a7efe5dd0bf5f026c4d675d024d0243284b1a7a9d  input-read stderr
```

An independent immutable-source structural scan produced:

```text
files=11
h1=11
headings=61
links=95
tables=9
code_blocks=21
images=0
heading_errors=0
fence_errors=0
ambiguous_link_text=0
table_shape_errors=1
docs/developers/reference/python-api.md:78: expected_cells=2 parsed_cells=4
```

The scan treats unescaped GFM pipes as cell separators, including inside inline
spans, as required by the GFM table grammar. The repository link checker cannot
detect that class of error.

No MkDocs, Zensical, Docusaurus, Sphinx, Jekyll, rendered `site`, `_site`, or
equivalent documentation publication artifact was found.

## Findings

### DOCUX-P1.1-001: The real-artifact procedure does not run in the documented environment

- Verdict and severity: **CHANGES_REQUIRED — medium**
- Affected source: `docs/developers/how-to/handle-raw-dbt-artifacts-safely.md`,
  especially the prerequisite at line 11 and command at lines 27–32; inbound
  routes from README, capture README, documentation index, tutorial, recovery
  how-to, API/CLI references, and pair-state explanation.
- Evidence: The repository and tutorial prepare the runtime with
  `uv sync --project capture --locked --no-dev` and invoke it with
  `uv run --project capture --no-sync dbtobsb-capture`. After that exact
  preparation, the executable resolves only inside
  `capture/.venv/bin`. From a normal non-activated shell,
  `command -v dbtobsb-capture` returned not found. Executing the how-to's bare
  command under a clean ordinary `PATH` returned exit `127` and
  `command not found` before inspecting either placeholder path.
- User impact: This is the page readers are told to follow before substituting
  real evidence. A reader who follows the documented setup must guess that the
  command needs an activated environment or a different installation method.
  That breaks copy/paste task completion at the most regulated transition in
  the journey and can send the reader back toward less-specific pages.
- Required change: Make the procedure use the already documented and tested
  repository-root form, for example
  `uv run --project capture --no-sync dbtobsb-capture ...`, and state the
  repository-root prerequisite; or document and test a complete installed-wheel
  activation/invocation path before the command. Keep the approved-path
  placeholder, `--no-sync`, policy prerequisites, and no-upload boundary.
  Add a documentation test that executes the displayed how-to command shape in
  the environment its prerequisite creates, with synthetic approved-path
  substitutes.
- Resolution: open at the reviewed commit.
- Re-review outcome: pending.

### DOCUX-P1.1-002: Unescaped type unions corrupt the public-types table

- Verdict and severity: **CHANGES_REQUIRED — medium**
- Affected source: `docs/developers/reference/python-api.md:75-81`, specifically
  the `ArtifactPairReport` row at line 78.
- Evidence: The table declares two columns, `Type` and
  `Public fields and invariant`. The row includes
  `` `summary: ArtifactPairSummary | None` `` and
  `` `primary_issue: ArtifactPairIssue | None` `` with literal, unescaped
  pipes. The GFM table specification says pipes delimit cells even inside inline
  spans unless escaped. The immutable-source scan therefore parses four cells
  where the header defines two. GFM ignores excess body cells, so the rendered
  second cell ends at the first union pipe and the remaining fields/invariants
  are not reliably presented under the intended header.
- Accessibility and user impact: The source visually suggests one complete
  type contract, while a conforming renderer can expose a truncated data row.
  That loses programmatic row/column relationships important to serial and
  assistive-technology reading, and hides public fields from an integrator
  using the rendered reference. It conflicts with the source implications of
  WCAG 1.3.1 and the page's lookup purpose.
- Required change: Escape both union pipes as `\|` in the table source so GFM
  renders literal code pipes, or move the union-bearing contract out of the
  pipe table into a structure that cannot be split. Add a source/GFM table-shape
  check so every body row has the declared column count and literal cell pipes
  are escaped. Then verify the generated semantic table with the future
  renderer; that later visual/assistive-technology check does not replace the
  current source fix.
- Resolution: open at the reviewed commit.
- Re-review outcome: pending.

## Positive controls to preserve

- The first P1.1 action is visible before the much longer P0 path.
- Every real-file entry route warns before example substitution and uses
  descriptive task text rather than a generic warning link.
- The tutorial identifies role-independent prerequisites, repository-root
  context, installation egress, offline-after-installation behavior, synthetic
  fixtures, exact output, and next steps before the reader must infer them.
- Pair validity, dbt outcome, and capture state remain three explicit questions;
  neither exit `0` nor `PAIR_VALID` is called job success or complete capture.
- Invalid and input-read output is linear, deterministic, static, path-free,
  noninteractive, and independent of color, animation, or cursor position.
- The diagnosis how-to reduces 26 issue codes to eight recovery families and
  leaves the exhaustive registry in reference.
- Link labels name their target purpose, headings name the section task/topic,
  and all fenced blocks have a source language.
- The raw-handling page correctly names the accountable owner, approved host and
  storage, least privilege, stop condition, all-copy scope, support boundary,
  retention, deletion, backup, and legal hold.
- No scoped page contains an image, so there is no current missing-alt-text
  source defect. Future images or screenshots require separate alt-text and
  publication-safety review.

## Explicitly deferred rendered-site and WCAG gates

Because no documentation renderer, site configuration, generated HTML, or
publication artifact exists, this review cannot determine or claim:

1. semantic HTML heading, landmark, list, callout, table, and code structure;
2. page titles, language metadata, breadcrumbs, skip navigation, focus order,
   focus visibility, target size, or consistent navigation/help;
3. keyboard operation of navigation, search, anchors, table overflow, and any
   future copy-code control;
4. contrast, color independence in the actual theme, text spacing, zoom,
   320-CSS-pixel reflow, responsive table/code behavior, or content clipping;
5. accessible names, states, live regions, generated search results, or link
   behavior in the final application shell;
6. representative VoiceOver/NVDA/JAWS reading of headings, links, callouts,
   five-column issue registry, code, and output; or
7. WCAG 2.2 A/AA conformance, accessibility-statement accuracy, or regulated
   customer acceptance.

After a renderer exists, test those behaviors against the built artifact with
automated checks plus keyboard, high-zoom/reflow, and representative
screen-reader review. Pay particular attention to the long issue table, compact
JSON lines, shell continuations, blockquote warnings, and source-to-rendered
heading/fragment fidelity.

## Required acceptance evidence

Before re-review, provide one immutable commit that proves:

1. the raw-artifact how-to command runs in its stated reader environment without
   an undocumented activation or installation step;
2. the Python public-types row has two GFM cells and retains both optional-field
   unions under the `Public fields and invariant` header;
3. a regression check rejects unescaped table-cell pipes or mismatched table
   widths in the P1.1 reader set;
4. the complete revision-bound link check, documentation tests, tutorial/API
   journeys, Ruff, format, `ty`, regeneration, runtime-only setup, wheel, and
   isolated installed CLI gates remain green; and
5. all positive controls and explicit future rendered-site/WCAG deferrals remain
   intact.

## Verdict

**CHANGES_REQUIRED**

Commit `2b76abbd565271b30f37fdb1e3f00d76185e8dc4` provides a clear and largely
accessible source journey, but `DOCUX-P1.1-001` blocks copy/paste completion of
the real-artifact task and `DOCUX-P1.1-002` corrupts a public API table under the
repository's native GFM rendering model. Both belong to the current source part
and must be resolved before documentation acceptance. Browser, rendered-site,
and WCAG validation remains a separate later gate and is not claimed here.
