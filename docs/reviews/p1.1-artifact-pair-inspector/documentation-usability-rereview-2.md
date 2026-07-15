# Documentation usability/accessibility re-review 2: P1.1 artifact-pair inspector

- Review date: 2026-07-15
- Reviewer: independent source-level documentation usability/accessibility reviewer
- Immutable reviewed commit: `8711aa803016b5d732553756c5e71542e0a928bf`
- Reviewed tree: `d37f4dc0aba63b489530b94849019383b46b49c5`
- Immediate parent: `c671b7ec8273dd5ed4937ac78ecadafbb2379f9a`
- Prior finding record: [documentation-usability.md](documentation-usability.md)
- Prior re-review: [documentation-usability-rereview.md](documentation-usability-rereview.md)
- Verdict: **PASS_WITH_FOLLOW_UP**
- Finding disposition: `DOCUX-P1.1-001` and `DOCUX-P1.1-002` **CLOSED**
- New source findings: none
- Cloud, Databricks, authentication, dbt, and paid-compute activity: none
- Full-site/browser/WCAG result: explicitly deferred; no documentation site or publication artifact exists

## Executive verdict

`DOCUX-P1.1-002` is fully closed at immutable commit
`8711aa803016b5d732553756c5e71542e0a928bf`. The marked public-types table now
uses the GFM-prescribed escaped pipe inside both inline code spans. Every source
row parses as exactly two cells, and GitHub's Markdown service renders both
Python unions as visible `| None` text with no displayed backslash or entity.

The regression test now matches the source contract instead of masking it. It
splits only on pipes not preceded by a backslash, normalizes the two escaped
display pipes for reflected-type comparison, and continues to bind every public
field to the actual Python annotations. The focused test and complete P1.1 gate
passed.

`DOCUX-P1.1-001` remains closed. Its raw-handling source is byte-identical to the
accepted prior re-review, and the same executable documentation test still
extracts the unique marked uv command, substitutes sanitized fixture paths,
runs it from the repository root, and requires successful safe JSON.

No current P1.1 Markdown-source usability or accessibility defect remains.
`PASS_WITH_FOLLOW_UP` records only the already deferred complete-site,
browser, assistive-technology, and WCAG validation. That later publication gate
does not weaken or reopen either source finding.

## Review basis and limits

The focused closure was evaluated against the exact acceptance evidence in the
two prior reports and the formal
[GitHub Flavored Markdown table rules](https://github.github.com/gfm/#tables-extension).
The specification's table example uses `` `\|` `` inside inline code and renders
it as `<code>|</code>`.

The GitHub Markdown API was used only as a narrow parser/render conformance probe
for the marked table. It is not a substitute for a built documentation site,
browser interaction, representative assistive technology, or a WCAG audit.

## Immutable scope and hashes

`HEAD` matched the reviewed commit and the worktree was clean before review and
validation. Reviewed bytes came from the named immutable revision. This report
is outside the frozen input, and no reviewed source or prior report was edited.

### Finding-closure set

| SHA-256 | Input |
| --- | --- |
| `40113deea018d4303a8655a64122b3b7ca4e58677710af859e1fcb32b53926dc` | `docs/reviews/p1.1-artifact-pair-inspector/documentation-usability.md` |
| `e876c6755b43bc08e5916f8565b8b541070051c07ab628ca75fd9fd9d6411423` | `docs/reviews/p1.1-artifact-pair-inspector/documentation-usability-rereview.md` |
| `7c5e2ca891124cfb9b60f6184983fb97a963ec26339c1decce4e40dba14e9c82` | `docs/developers/reference/python-api.md` |
| `539ac1e3e1c208b52d6e486a1c87b788e73b92f1f4b7d4e5d30724022908e920` | `docs/developers/how-to/handle-raw-dbt-artifacts-safely.md` |
| `8dab5bf14843fef5ae4bc86a2335ae3912fe18c9ba88175302fdff0b7e160b99` | `capture/tests/test_documentation.py` |

The SHA-256 over the literal path-ordered `shasum -a 256` record stream is:

```text
bb4044047840b5ea1c01c18b1906c110d74078d3b9e3a7cab9ed6767abdd9274
```

### Validation set

| SHA-256 | Input |
| --- | --- |
| `92656cda84b66dd76338cec050c35e632ae50de015bda89e474d28a74854b911` | `scripts/check_capture.sh` |
| `aa904ffdd5540d2604b840c42d8d04660c03c57e0d1f818355fc524dbd40b0c0` | `scripts/check_markdown_links.py` |
| `69f1367bf81be14cf166626251e734854655871c95dd1624015c11a10e2a8935` | `capture/pyproject.toml` |
| `fb09543bcd8cbca30786135e5879465181efd8d0e6e92b452d1bfffcba68b461` | `capture/uv.lock` |

The SHA-256 over this literal path-ordered record stream is:

```text
2741725958f78ba0eb8f7df7ca17dc37031e5efe6ca473f1b680b97db7f5f252
```

## DOCUX-P1.1-002 closure

### Source cell parsing

The `python-public-types` marker appears exactly once. Its seven table lines
consist of one header, one delimiter, and five body rows. Splitting on only
unescaped delimiters produced:

```text
markers=1/1
row_widths=[2, 2, 2, 2, 2, 2, 2]
escaped_display_pipes=2
entities=0
```

After normalizing the escaped display pipes, the marked source contains both
exact reflected annotations:

```text
summary: ArtifactPairSummary | None
primary_issue: ArtifactPairIssue | None
```

The row therefore preserves the intended two-column `Type` to
`Public fields and invariant` relationship without using an entity that becomes
literal code text.

### Conforming GFM/GitHub rendering

The exact marked section was sent to GitHub's Markdown renderer in GFM mode. The
observed result was:

```text
gfm_th=2
gfm_td=10
visible_union_tokens=2
visible_entity_tokens=0
visible_backslash_pipe_tokens=0
```

The relevant generated HTML contained:

```html
<code>summary: ArtifactPairSummary | None</code>
<code>primary_issue: ArtifactPairIssue | None</code>
```

This closes both parts of the finding: the row remains exactly two cells, and
the reader receives both real Python union operators without source escapes or
entities leaking into the visible contract.

### Regression-test binding

`test_python_reference_binds_closed_public_contract` now:

1. reads only the uniquely marked public-types section;
2. uses `re.split(r"(?<!\\)\|", line)[1:-1]` so only unescaped pipes are
   delimiters;
3. requires every marked table line to contain exactly two cells;
4. converts only the GFM display source `\|` to `|` for annotation comparison;
5. reflects the real public dataclass type hints; and
6. requires every field name and exact displayed type to appear in the
   normalized marked section.

The test no longer invents an entity conversion that GFM does not perform. A
missing escape would create an extra cell; a missing or incorrect union would
fail the reflected-type assertion.

**Disposition: CLOSED.**

## DOCUX-P1.1-001 regression check

The accepted raw-artifact how-to remains byte-identical to commit `2367a05…`,
with SHA-256
`539ac1e3e1c208b52d6e486a1c87b788e73b92f1f4b7d4e5d30724022908e920`.
It still:

- requires the repository root and the tutorial's locked runtime setup;
- uses `uv run --project capture --no-sync dbtobsb-capture` inside one marked
  Bash fence;
- retains approved path placeholders and all custody/lifecycle controls; and
- is extracted, substituted with sanitized fixtures, and executed by
  `test_recovery_and_raw_handling_commands_match_runtime`.

That focused executable test passed together with the public-types test and the
full suite.

**Disposition: REMAINS CLOSED.**

## Validation executed

Focused tests:

```text
uv run --project capture pytest -q \
  capture/tests/test_documentation.py::test_python_reference_binds_closed_public_contract \
  capture/tests/test_documentation.py::test_recovery_and_raw_handling_commands_match_runtime
2 passed
```

Full exact-commit gate:

```text
uv lock --check --project capture
passed

scripts/check_capture.sh
96 tests passed
tracked_markdown_files=127
local_links=210
fragments=59
errors=0
Ruff check and format: passed
ty: passed
report-schema and fixture regeneration: passed
runtime-only installation and checked-in API example: passed
wheel build and isolated installed CLI: passed
DBTOBSB_CAPTURE_CHECK_PASSED

scripts/check_markdown_links.py --revision 8711aa803016b5d732553756c5e71542e0a928bf
tracked_markdown_files=127
local_links=210
fragments=59
errors=0

bash -n scripts/check_capture.sh
passed

shellcheck scripts/check_capture.sh
passed

git diff --check c671b7e..8711aa8
passed
```

The reviewed commit changes only the marked Python reference row and its
regression parser. It introduces no heading, link, route, code-fence, warning,
or raw-handling change.

## Positive controls preserved

- The public type contract is complete, machine-bound, and visually accurate in
  GFM.
- The public-types table retains explicit headers and consistent row shape.
- The raw-handling command remains copy-ready in its stated uv environment.
- Real-input custody, support, retention, deletion, backup, and legal-hold
  warnings remain unchanged.
- Pair validity remains separate from dbt outcome and future capture state.
- Commands and outputs remain text-first and do not depend on color, animation,
  cursor position, or pointer input.

## Explicitly deferred full-site/browser/WCAG follow-up

No MkDocs, Zensical, Docusaurus, Sphinx, Jekyll, generated `site`, `_site`, or
equivalent publication artifact exists. This report therefore does not claim:

- complete-site navigation, landmarks, page metadata, search, or breadcrumbs;
- keyboard/focus/target-size behavior;
- contrast, zoom, text spacing, responsive reflow, or overflow behavior;
- representative screen-reader output for the complete page/site; or
- WCAG 2.2 A/AA conformance or regulated-customer accessibility acceptance.

Those remain a non-blocking later documentation-publication gate and require a
complete built artifact plus automated, keyboard, reflow, and representative
assistive-technology testing.

## Verdict

**PASS_WITH_FOLLOW_UP**

At immutable commit `8711aa803016b5d732553756c5e71542e0a928bf`,
`DOCUX-P1.1-002` is closed and `DOCUX-P1.1-001` remains closed. The P1.1 source
documentation is acceptable from this usability/accessibility lens. Only the
explicitly deferred complete-site, browser, assistive-technology, and WCAG gate
remains; no current source change is required.
