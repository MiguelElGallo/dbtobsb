# Documentation usability/accessibility re-review: P1.1 artifact-pair inspector

- Review date: 2026-07-15
- Reviewer: independent source-level documentation usability/accessibility reviewer
- Immutable reviewed commit: `2367a05d4e9ddb763cc52a3b7090c4099a639631`
- Reviewed tree: `a3ef222f0300903f6cee4bef57db64d9a3d5b49d`
- Immediate parent: `08de2ddb3429bb675b6587de4c225bbf93102a1f`
- Prior finding record: [documentation-usability.md](documentation-usability.md)
- Verdict: **CHANGES_REQUIRED**
- Finding disposition: `DOCUX-P1.1-001` **CLOSED**; `DOCUX-P1.1-002` **OPEN**
- New finding IDs: none
- Cloud, Databricks, authentication, dbt, and paid-compute activity: none
- Rendered-site/browser/WCAG result: explicitly deferred; no site configuration or publication artifact exists

## Executive verdict

Commit `2367a05d4e9ddb763cc52a3b7090c4099a639631` fully closes the
copy/paste environment finding. The raw-artifact page now names the repository
root and the tutorial's locked runtime setup, places the exact command inside a
unique marker, and invokes the executable through
`uv run --project capture --no-sync`. Independent extraction and execution of
that marked command with sanitized fixture substitutions returned exit `0`,
empty stderr, and the expected allowlisted `PAIR_VALID` JSON. The new regression
test extracts and executes the same marked command rather than a duplicate.

The table finding is only partially resolved. The Python public-types table now
has two source cells per row, so the original extra-cell truncation is gone.
However, the two union operators were changed to `&#124;` inside inline code.
The formal GitHub Flavored Markdown (GFM) specification says entity and numeric
character references are literal text in code spans. A narrow render through
GitHub's own Markdown API consequently produced
`ArtifactPairSummary &amp;#124; None` in HTML, which displays
`ArtifactPairSummary &#124; None`, not the documented Python type
`ArtifactPairSummary | None`.

The new test does not detect this. It checks raw `|`-separated source width and
then manually replaces `&#124;` with `|` before comparing reflected types. That
replacement does not occur in GFM code spans; it makes the test pass by applying
a transformation the reader does not receive. The same raw `split("|")` check
would reject the GFM-prescribed `` `\|` `` representation that renders the
correct operator.

Because one current public API contract remains inaccurate in the native GFM
source rendering model, `DOCUX-P1.1-002` remains open and the verdict stays
`CHANGES_REQUIRED`. All repository gates pass, the command finding is closed,
and no additional source-level route, heading, link, fence, or table-width
regression was found.

This narrow GFM parser probe is not a documentation-site render, browser test,
assistive-technology test, or WCAG audit. Those later gates remain explicitly
deferred.

## Review basis and limits

The re-review uses the acceptance conditions in the prior finding record and
the repository [review process](../../plans/review-process.md) and
[documentation plan](../../plans/documentation-plan.md). Accessibility source
implications were checked against:

- the formal [GFM tables specification](https://github.github.com/gfm/#tables-extension),
  whose table example escapes a pipe inside an inline code span as `` `\|` ``
  and renders `<code>|</code>`;
- the GFM [entity and numeric character reference rules](https://github.github.com/gfm/#entity-and-numeric-character-references),
  which state that references are not recognized in code spans and show that
  they render as literal text there;
- W3C [Info and Relationships](https://www.w3.org/WAI/WCAG22/Understanding/info-and-relationships.html)
  and [Headings and Labels](https://www.w3.org/WAI/WCAG22/Understanding/headings-and-labels)
  guidance for source structure and descriptive organization; and
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) only as the eventual rendered-web
  target, not as a conformance result for Markdown source.

The review did not re-decide dbt artifact semantics or the pre-release report
contract correction in Decision 0002. It checked their reader-facing
accessibility/usability effects and ran the full P1.1 gate.

## Immutable scope and hashes

`HEAD` matched the immutable reviewed commit and the worktree was clean before
review and validation. Reviewed content was read from the named revision. This
report is outside the frozen input; no reviewed source or earlier report was
edited.

### Reader-route set

The regression route covers the same four entry surfaces and seven registered
leaf pages as the initial review:

| SHA-256 | Reviewed source |
| --- | --- |
| `0be609fbbb0239d7dbb1142dcd630fa94f0a7b13ba9af7940b65f08d9d48c5cf` | `README.md` |
| `d664454aa140415fc822398a217d62bb57cffc41c647fee46da98213fa0e6e19` | `capture/README.md` |
| `555ea21e8de979ad539024e0856275b9741cd377253a5285fa2779ee12288849` | `docs/index.md` |
| `8867bd6d28b38d7c22bfe1bb2c2affead9b737f64311b8c7d2c519544d6c0ceb` | `docs/developers/index.md` |
| `35b778b40eda2880b837a2d5c5d517c55ac9593e41d6aacf3815f76ba5c6a12d` | `docs/developers/tutorials/inspect-an-artifact-pair.md` |
| `e2befb7ad8648db1cfd71ec9e4f9eba4a44a78a2c67fb2cb7233fece097c4531` | `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md` |
| `539ac1e3e1c208b52d6e486a1c87b788e73b92f1f4b7d4e5d30724022908e920` | `docs/developers/how-to/handle-raw-dbt-artifacts-safely.md` |
| `bb4c28a5c50988e4ddc17e90c462b3d86de145ecec8d1c06e78f19ed97c30323` | `docs/developers/reference/cli-report-and-exit-codes.md` |
| `14f83e19b7520a80287a1c728a76ee04fdb103df084b9fe1b705e71b5a0d02aa` | `docs/developers/reference/python-api.md` |
| `0ce8f5dc9fe7e426fbcd65b2b09b8bdf30b5230f29cb288c14836d423c88fda1` | `docs/developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md` |
| `653d6befeb6791974362e5ceb29cedd14980cf92b01a92f4eb2981e1c822b990` | `docs/developers/explanation/raw-artifact-custody.md` |

The SHA-256 of the literal path-ordered `shasum -a 256` record stream is:

```text
96c70f59849ef6aac7cd92519d920a304c92a1b446842a4bf93c2ad9d8fe8565
```

### Executable corroboration set

| SHA-256 | Validation input |
| --- | --- |
| `34a514f751fd83df0afd045ae73b6bbc0af151dcb27523fb22a9f08f534a9683` | `capture/tests/test_documentation.py` |
| `9ec9e35e7362cbe2907483e344c2979bd886b9586b03d35b465d93e533ec5099` | `capture/examples/inspect_valid_fixture.py` |
| `92656cda84b66dd76338cec050c35e632ae50de015bda89e474d28a74854b911` | `scripts/check_capture.sh` |
| `aa904ffdd5540d2604b840c42d8d04660c03c57e0d1f818355fc524dbd40b0c0` | `scripts/check_markdown_links.py` |
| `69f1367bf81be14cf166626251e734854655871c95dd1624015c11a10e2a8935` | `capture/pyproject.toml` |
| `fb09543bcd8cbca30786135e5879465181efd8d0e6e92b452d1bfffcba68b461` | `capture/uv.lock` |

The SHA-256 of this literal path-ordered record stream is:

```text
8c015e1feb9769192383b66aa42d37db18debb2b139663f92131a02ae408221c
```

### Finding and governance set

| SHA-256 | Supporting input |
| --- | --- |
| `40113deea018d4303a8655a64122b3b7ca4e58677710af859e1fcb32b53926dc` | `docs/reviews/p1.1-artifact-pair-inspector/documentation-usability.md` |
| `946d6ca04d362d5a25606f0306114b2776d2479376ab300899ca4bc0019614d1` | `docs/decisions/0002-correct-p1.1-invocation-recovery-text.md` |
| `84fcc96227afab551e07c0ed7194d13e8fa299e7210bebb132ef5b875b076eab` | `docs/evidence/p1.1-local-artifact-pair-2026-07-15.md` |
| `ec7e73009e88274a38c140add8eb49e81b74be23c5350a39578a70a784d8780c` | `docs/reviews/README.md` |
| `d293175884cb5d1cb1916609cf490aac8189856535317b9061eb8267c0941a0d` | `docs/plans/review-process.md` |
| `b753b2d568e246bceefefe806d1ebd5bb47eadf8e7a32d95a557f03471e0623e` | `docs/plans/documentation-plan.md` |

The SHA-256 of this literal path-ordered record stream is:

```text
ed1f73ae42a92f5a7dbcf34693d0d81ea090e6a1380dc456fc2ea56d220fdc04
```

## Finding closure

### DOCUX-P1.1-001: Closed

The exact acceptance conditions are now satisfied:

1. `Before you begin` requires the repository root and the P1.1 runtime created
   by the tutorial's locked
   `uv sync --project capture --locked --no-dev` command.
2. The marked procedure uses
   `uv run --project capture --no-sync dbtobsb-capture`, retaining the approved
   path placeholders, JSON output, no-color behavior, and all custody controls.
3. The command is bounded by one `raw-handling-command` marker pair. The test
   extracts the marked Bash fence, uses shell-compatible argument parsing,
   replaces only the two policy placeholders with the sanitized successful
   fixture, executes from the repository root, and requires exit `0`, empty
   stderr, and `PAIR_VALID` JSON.
4. Independent extraction and execution repeated that exact path with
   `UV_OFFLINE=1`, `TERM=dumb`, and `NO_COLOR=1` after the documented runtime
   preparation:

```text
marked_sections=1
argv_prefix=uv run --project capture --no-sync dbtobsb-capture inspect-artifact-pair
exit=0
stderr_bytes=0
stdout_sha256=a5a39e26af3a99d759a6687cb24e91f29d4b81b86c570d1cd64b4fbc60e0707a
pair_state=PAIR_VALID
```

5. The focused
   `test_recovery_and_raw_handling_commands_match_runtime` check and the entire
   capture suite passed.

The reader no longer needs to guess activation or a different installation
method. The policy-owned path remains a visible placeholder, so the fix does not
weaken the handling boundary.

**Disposition: CLOSED.**

### DOCUX-P1.1-002: Remains open

The source-width part is improved:

- the marked `python-public-types` table has one header row, one delimiter row,
  and five body rows;
- every row now has exactly two unescaped raw `|`-separated cells; and
- a GitHub GFM render produced two `<th>` elements and ten `<td>` elements, so
  the original four-cell/truncation behavior is gone.

The displayed type contract is still wrong. The `ArtifactPairReport` row uses:

```text
`summary: ArtifactPairSummary &#124; None`
`primary_issue: ArtifactPairIssue &#124; None`
```

GFM treats character references inside code spans as literal text. GitHub's own
Markdown API rendered the marked section with:

```html
<code>summary: ArtifactPairSummary &amp;#124; None</code>
<code>primary_issue: ArtifactPairIssue &amp;#124; None</code>
```

The observed parser summary was:

```text
gfm_th=2
gfm_td=10
visible_entity_tokens=2
visible_union_tokens=0
```

Therefore a reader sees `&#124;`, not the Python union operator. This is not only
a browser-theme concern: it is the deterministic inline-code result specified by
GFM and reproduced by the repository host's Markdown service.

The new test at `capture/tests/test_documentation.py:156-195` binds the wrong
representation:

1. `line.strip("|").split("|")` proves only raw two-cell shape; it is not a
   GFM-aware separator parser and would count a correct escaped `\|` as another
   cell.
2. `public_types_source.replace("&#124;", "|")` creates the correct annotation
   only inside the test. GFM explicitly does not perform that replacement in a
   code span.
3. The reflected-field assertions consequently pass against a synthetic string,
   not the content presented to the reader.

A control render using GFM's documented table-cell form,
`` `ArtifactPairSummary \| None` ``, produced the correct visible code text
`ArtifactPairSummary | None` while preserving two cells.

Required closure:

1. use GFM's escaped-pipe representation inside both code spans, or move the
   union-bearing types to a structure that preserves literal `|` without a table
   delimiter;
2. replace the manual entity conversion and raw `split("|")` assertion with a
   GFM-aware source/rendered-content check that proves both the two-cell shape
   and the two visible `| None` unions; and
3. rerun the focused documentation tests, immutable link check, structural
   scan, and complete capture gate.

The future documentation-site/browser/accessibility gate remains required, but
it cannot waive this current source-contract correction.

**Disposition: OPEN.**

## Source-level regression assessment

The exact 11-page reader route produced:

```text
files=11
h1=11
headings=62
links=99
tables=10
code_blocks=21
images=0
heading_errors=0
fence_errors=0
ambiguous_link_text=0
table_shape_errors=0
code_span_entity_tokens=2
```

Other than the two literal entity tokens described by the retained finding:

- each page has exactly one H1 and no skipped ATX heading level;
- headings remain descriptive and task-oriented;
- all fenced blocks are closed and language-labeled;
- link text names its target purpose, and all local files/fragments resolve;
- warning meaning remains present in text rather than color or iconography;
- the new BuildTask compatibility table has a clear three-column header and
  consistent body shape;
- the diagnosis page adds a direct compatibility-matrix link without obscuring
  the primary recovery action; and
- the corrected invocation wording distinguishes contract validity from origin,
  authenticity, custody, and capture completeness.

The additional compatibility detail raises reference-page density but remains
under a descriptive heading and is reached from recovery only when relevant. No
new source-level cognitive-load or route blocker was found.

## Validation executed

Focused closure checks passed:

```text
uv run --project capture pytest -q \
  capture/tests/test_documentation.py::test_recovery_and_raw_handling_commands_match_runtime \
  capture/tests/test_documentation.py::test_python_reference_binds_closed_public_contract
2 passed

marked raw-handling command with synthetic substitutions
exit=0
stderr_bytes=0
stdout_sha256=a5a39e26af3a99d759a6687cb24e91f29d4b81b86c570d1cd64b4fbc60e0707a

GitHub GFM parse of marked public-types section
gfm_th=2
gfm_td=10
visible_entity_tokens=2
visible_union_tokens=0
```

The complete exact-commit gate also passed:

```text
uv lock --check --project capture
passed

scripts/check_capture.sh
96 tests passed
tracked_markdown_files=124
local_links=200
fragments=55
errors=0
Ruff check and format: passed
ty: passed
report-schema and fixture regeneration: passed
runtime-only installation and checked-in API example: passed
wheel build and isolated installed CLI: passed
DBTOBSB_CAPTURE_CHECK_PASSED

scripts/check_markdown_links.py --revision 2367a05d4e9ddb763cc52a3b7090c4099a639631
tracked_markdown_files=124
local_links=200
fragments=55
errors=0

bash -n scripts/check_capture.sh
passed

shellcheck scripts/check_capture.sh
passed

git diff --check 08de2dd..2367a05
passed
```

The green suite demonstrates that the new table test is present, but it does not
override the direct GFM/specification evidence that the test's entity
normalization differs from reader output.

No MkDocs, Zensical, Docusaurus, Sphinx, Jekyll, generated `site`, `_site`, or
equivalent publication artifact was found.

## Positive controls preserved

- Real-artifact handling still begins with accountable ownership, approved
  host/storage, least privilege, lifecycle decisions, and a stop condition.
- The command fix retains `--no-sync`, policy placeholders, safe JSON, and the
  no-upload/no-governance boundary.
- Tutorial, recovery, API, CLI, and explanations continue to distinguish pair
  validity, native dbt outcome, and future capture completeness.
- The updated mismatch output gives one deterministic impact and overwrite-safe
  action without exposing a path, raw identifier, or artifact content.
- Ordinary support remains limited to allowlisted context and the restricted
  exception remains explicit.
- Text, examples, and output do not depend on color, animation, pointer input,
  or cursor position.
- No scoped page contains an image, so there is no current missing-alt-text
  source defect.

## Explicitly deferred rendered-site, browser, and WCAG gates

The GitHub Markdown API call above was a narrow conformance probe for the exact
GFM cell/parser behavior named by `DOCUX-P1.1-002`. It is not evidence for a
future documentation site's theme, navigation, interaction, or accessibility.

Because no documentation site exists, this review does not determine or claim:

1. semantic landmarks, page language/title, breadcrumbs, skip links, search,
   previous/next routes, or generated help;
2. keyboard order, focus visibility, target size, code-copy behavior, or table
   overflow controls;
3. contrast, text spacing, zoom, 320-CSS-pixel reflow, clipping, or responsive
   layout of the long issue and compatibility tables or compact JSON;
4. assistive-technology output for headings, links, blockquote warnings, tables,
   code, or CLI output; or
5. WCAG 2.2 A/AA conformance, regulated-customer accessibility acceptance, or
   publication readiness.

Those checks remain required against a complete built artifact using automated
analysis plus keyboard, high-zoom/reflow, and representative screen-reader
review.

## Required acceptance evidence

Before another re-review, provide one immutable commit proving:

1. both optional public fields visibly contain the Python `| None` union in a
   conforming GFM render while the row remains exactly two cells;
2. the regression test validates GFM-aware cell separation and presented code
   text without manually inventing an entity conversion;
3. `DOCUX-P1.1-001`'s marked command, prerequisite, synthetic-substitution test,
   and custody controls remain unchanged or equivalently strong;
4. the 11-page heading/link/fence/table scan contains no source errors or
   literal entity token in the two type spans; and
5. the focused tests, immutable links, Ruff, formatting, `ty`, generation,
   runtime-only, wheel, installed CLI, Bash, and ShellCheck gates remain green.

## Verdict

**CHANGES_REQUIRED**

`DOCUX-P1.1-001` is closed at immutable commit
`2367a05d4e9ddb763cc52a3b7090c4099a639631`. `DOCUX-P1.1-002` remains open:
the table structure is now two columns, but its code spans present the entity
source rather than Python's union operator, and the new test masks that mismatch.
The current source contract must be corrected before acceptance. Rendered-site,
browser, assistive-technology, and WCAG validation remains a separate future
gate and is not claimed here.
