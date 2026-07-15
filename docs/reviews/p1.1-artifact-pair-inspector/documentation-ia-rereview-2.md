# Diátaxis information-architecture re-review 2: P1.1 artifact-pair inspector

- Reviewed commit: `7ce722cddfed42f1e96741bb07b6cd8762127f22`
- Documentation source revision named by the evidence: `80d0c0a6dd0e139ec4b8e040c36f99983931b06f`
- Prior reviews: [documentation-ia.md](documentation-ia.md) and [documentation-ia-rereview.md](documentation-ia-rereview.md)
- Review date: 2026-07-15
- Review mode: independent immutable source-level Markdown, traceability, and reader-route closure re-review
- Verdict: **PASS_WITH_FOLLOW_UP**
- Finding disposition: `DIA-P1.1-001` through `DIA-P1.1-004` **CLOSED**
- New blocking findings: **0**
- Cloud, Databricks, authentication, and paid-compute activity: **none**

## Executive verdict

Commit `7ce722c…` closes both findings from the preceding re-review while preserving closure of the two original findings. Real-file custody is now a mode-correct pair: [Handle raw dbt artifacts safely](../../developers/how-to/handle-raw-dbt-artifacts-safely.md) owns the executable task, and [Why safe reports do not make raw artifacts safe](../../developers/explanation/raw-artifact-custody.md) owns the conceptual model. The developer landing, inbound links, four-mode inventory, D1P family row, and seven-row implemented-page registry all agree with that split.

The immutable link evidence is also reproducible. Its exact command resolves the named source revision rather than the mutable worktree and produces the recorded `117` Markdown blobs, `160` local-link occurrences, `48` fragment-bearing occurrences, and zero errors. The checker at the evidence source revision has the same SHA-256 as the checker in the reviewed commit and is part of the repository-owned capture gate.

No source-level information-architecture or documentation-evidence blocker remains in this closure slice. `PASS_WITH_FOLLOW_UP` records only the already-deferred rendered-site, search, accessibility, and publication checks; it does not weaken any source acceptance condition.

## Immutable scope and hashes

The worktree was clean and `HEAD` matched the reviewed commit before this report was created. The reviewed commit has tree `48704123d3b873a4bddf57ed173fba3b1ad9376e` and immediate parent `80d0c0a6dd0e139ec4b8e040c36f99983931b06f`. That parent is the documentation source revision named in the evidence; the reviewed commit changes only the evidence sentence that binds the count to that revision.

The source-route aggregate covers this exact path-sorted 16-file set. Each SHA-256 was recomputed from the reviewed commit:

```text
0be609fbbb0239d7dbb1142dcd630fa94f0a7b13ba9af7940b65f08d9d48c5cf  README.md
d664454aa140415fc822398a217d62bb57cffc41c647fee46da98213fa0e6e19  capture/README.md
3221cd5c38a3b5d9fdace49cb19a07efdc945fec9d3a0af1bfebbe0c5911e48e  docs/developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md
653d6befeb6791974362e5ceb29cedd14980cf92b01a92f4eb2981e1c822b990  docs/developers/explanation/raw-artifact-custody.md
196ae6032b6ea8e2fe19b84cdb6ae9e2bdb15f90af41e0202e02ed033ca2eae8  docs/developers/how-to/diagnose-an-invalid-artifact-pair.md
59f10d13d45d85a13eb4d903bfc76e245621f09d13348b2c8b1676af46fedd46  docs/developers/how-to/handle-raw-dbt-artifacts-safely.md
8867bd6d28b38d7c22bfe1bb2c2affead9b737f64311b8c7d2c519544d6c0ceb  docs/developers/index.md
462117759f5eb09588f843e91c603a1e7ef8ef405d99d71423fe3229582a8aab  docs/developers/reference/cli-report-and-exit-codes.md
d6163c7b4ae07db5bb6b033f20c527a48f9912b7a4b382b80ad39807cdac1dc2  docs/developers/reference/python-api.md
4a005dacbbdb3d89f1c97d21b1ad9e5f98eb148f622fa7e0dfa53d52f2d79296  docs/developers/tutorials/inspect-an-artifact-pair.md
670dc2b74185492ea1de9e06fc0d64ee7c1fb3bef3b402ceeee3e4496e1125e9  docs/evidence/p1.1-local-artifact-pair-2026-07-15.md
2b6fece0e8ca96e2407e14f1bd8e5df90dbad39495feaefbd74914541bbc7fe2  docs/index.md
b753b2d568e246bceefefe806d1ebd5bb47eadf8e7a32d95a557f03471e0623e  docs/plans/documentation-plan.md
00e410370497edc3b55bfb2ee9491eeb91512dca64b81d44543c0f04c72076eb  docs/plans/product-plan.md
4189c82644fdbc93dc11faf1f652831ffab5e54ffd320e2c28af1b788283f95b  docs/research/source-register.md
af0f8b9cc8b717689f9b9c2ba2217db6df56c7f355508e1e2198b3b9cb3cb382  docs/reviews/README.md
```

The SHA-256 of that path-sorted `shasum -a 256` record stream is:

```text
4bd4ae3e459fba0e6694042d20b73bc17a1a23abe558e3e9e885c3ef6f2828f8
```

The immutable prior finding records and executable corroborating inputs were hashed separately:

```text
8f8543fd99bd04f4bb2688ad3c3b221c84452103767ffa64c7185f65b335520a  docs/reviews/p1.1-artifact-pair-inspector/documentation-ia.md
f5858d59a5b89ad0fb6d132e7872eba7edf9556244442699d1fdff7bd3ba0583  docs/reviews/p1.1-artifact-pair-inspector/documentation-ia-rereview.md
3653fe330b9dd660f959803c98337053980c9ea24cd30be904025f01ff90b8f9  capture/tests/test_documentation.py
9ec9e35e7362cbe2907483e344c2979bd886b9586b03d35b465d93e533ec5099  capture/examples/inspect_valid_fixture.py
92656cda84b66dd76338cec050c35e632ae50de015bda89e474d28a74854b911  scripts/check_capture.sh
aa904ffdd5540d2604b840c42d8d04660c03c57e0d1f818355fc524dbd40b0c0  scripts/check_markdown_links.py
```

This report is outside every reviewed input and aggregate. It does not replace or modify either prior immutable finding record.

## Current review basis

Official guidance was refreshed on the review date:

- [The Diátaxis compass](https://diataxis.fr/compass/) classifies action in application of skill as how-to and understanding-oriented cognition as explanation.
- [How-to guides](https://diataxis.fr/how-to-guides/) solve a real-world goal with an executable, logically ordered procedure.
- [Reference](https://diataxis.fr/reference/) neutrally describes product machinery; a concise illustrative example is compatible with reference.
- [Explanation](https://diataxis.fr/explanation/) develops context and connections away from immediate work and warns against instruction creep.
- [Complex hierarchies](https://diataxis.fr/complex-hierarchies/) permit an audience/task hierarchy when the modes and reader purposes remain distinct.

Repository-specific acceptance comes from the [documentation plan](../../plans/documentation-plan.md), particularly the implemented P1.1 four-mode inventory, navigation/page-traceability contract, D1P family row, implemented P1.1 page registry, page contract, and independent architecture review pass.

## Finding closure

### DIA-P1.1-001 — Remains closed

The original finding required the runnable Python first-use procedure to leave reference while preserving a concise descriptive API example and an explicit route to first use.

The current source preserves that resolution:

1. [Tutorial step 4](../../developers/tutorials/inspect-an-artifact-pair.md#4-use-the-python-api) owns the shell command, guided first result, exact output, and interpretation.
2. [Python API](../../developers/reference/python-api.md) opens with the function contract and is organised by function, example, public types, supported pair, and result interpretation.
3. Its opening sentence sends installation and a guided first result to the tutorial.
4. The remaining example is concise, descriptive, and adjacent to the API contract rather than presented as a setup/run procedure.
5. `test_displayed_python_example_and_output_match_execution` binds the displayed source and output to the checked-in executable example.

**Resolution: CLOSED.**

### DIA-P1.1-002 — Remains closed

The original navigation finding required both action routes to reach the pair/outcome/capture explanation without moving the mental model into the task pages.

The current source preserves that resolution:

1. The [tutorial conclusion](../../developers/tutorials/inspect-an-artifact-pair.md#what-you-have-proved) links to the explanation.
2. The [invalid-pair verification](../../developers/how-to/diagnose-an-invalid-artifact-pair.md#confirm-the-recovery) links to the same explanation and retains the CLI lookup route.
3. [Pair validity, dbt outcome, and capture state](../../developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md) returns to the tutorial, recovery how-to, raw-handling how-to, custody explanation, and CLI reference according to reader need.
4. The action pages retain only the interpretation needed to complete or verify their task; the detailed three-fact model remains in explanation.

**Resolution: CLOSED.**

### DIA-P1.1-003 — Closed

The preceding re-review required action-led raw handling to become a registered how-to, conceptual custody to remain explanation, and navigation plus traceability to agree with the split.

Every acceptance condition is now met:

1. [Handle raw dbt artifacts safely](../../developers/how-to/handle-raw-dbt-artifacts-safely.md) states a concrete local-inspection outcome, policy-approved local environment, accountable owner, access and lifecycle prerequisites, and a stop condition before reading a file.
2. Its ordered procedure covers approved copies, local inspection, ordinary versus exceptional support evidence, retention/deletion/legal hold, verification, and closure. It ends with the related explanation, recovery how-to, and machine reference.
3. [Why safe reports do not make raw artifacts safe](../../developers/explanation/raw-artifact-custody.md) is now cognition-led. It explains retained operational context, inspection versus custody, and workstation-local versus future Databricks-local scope. The old handling procedure is absent; its final sentence is cross-mode navigation, not an embedded task.
4. The [developer landing](../../developers/index.md) puts the handling task under “Start with an outcome” and the custody model under “Understand the boundaries”. README, package README, tutorial, recovery how-to, API reference, CLI reference, and pair-state explanation route real-file action to the how-to.
5. The documentation plan's implemented four-mode inventory and D1P family row name both the raw-handling how-to and raw-custody explanation.
6. The implemented P1.1 registry has one row for every leaf page in that inventory: one tutorial, two how-tos, two references, and two explanations. The developer index remains the route landing rather than an unregistered leaf.

The registry supplies the mandatory traceability contract without hidden fields:

| Mandatory field | Where it is satisfied |
| --- | --- |
| Audience and product dependency | Per-page “Audience and dependency” cells, plus the inherited offline-capture-library dependency. |
| Documentation stage and accountable owner | Per-page “Stage and accountable owner” cells; all seven are D1P with the relevant capture, dbt, or security owner. |
| Prerequisite and next pages | Per-page “Prerequisite and next route” cells. |
| Publication state | The registry preamble explicitly makes every implemented P1.1 page `base`. |
| Search synonyms and stable codes | Per-page search cells include reader language and applicable API, pair, issue, or exit-code terms. |
| Required evidence | Per-page evidence cells name runnable output, fixtures, contract tests, security review, data-flow checks, and non-claims as applicable. |

**Resolution: CLOSED.**

### DIA-P1.1-004 — Closed

The preceding evidence finding required exact reproducible totals, a deterministic checked-in command, a defined counting convention, and a clear distinction between occurrence counts and invalid targets.

The [quality-evidence record](../../evidence/p1.1-local-artifact-pair-2026-07-15.md#quality-evidence) now names all of those inputs. The exact recorded command was run without modification:

```bash
uv run --project capture python scripts/check_markdown_links.py --revision 80d0c0a6dd0e139ec4b8e040c36f99983931b06f
```

It reproduced the evidence exactly:

```text
tracked_markdown_files=117
local_links=160
fragments=48
errors=0
```

The source binding is independently checkable:

- `80d0c0a6dd0e139ec4b8e040c36f99983931b06f` resolves as a Git commit and is the immediate parent of the reviewed evidence-only commit.
- The SHA-256 of `scripts/check_markdown_links.py` at that source revision is `aa904ffdd5540d2604b840c42d8d04660c03c57e0d1f818355fc524dbd40b0c0`; the reviewed commit contains identical checker bytes.
- The checker enumerates Markdown blobs with `git ls-tree` and reads them with `git show`, so uncommitted files and later tracked-worktree drift cannot change the named-revision result.
- It ignores fenced code and external `http`, `https`, `mailto`, and `tel` targets, counts duplicate inline-link occurrences separately, counts fragment-bearing occurrences separately, and validates repository containment, target existence, ATX anchors, explicit IDs, and duplicate-heading suffixes.
- Running the same checker against the exact reviewed commit also produced `117`, `160`, `48`, and zero errors.
- [check_capture.sh](../../../scripts/check_capture.sh) runs the checked-in checker as part of the normal repository gate.

The evidence describes counts as occurrences and separately reports zero invalid targets; it no longer presents an unexplained total as a resolved-target inventory.

**Resolution: CLOSED.**

## Current route assessment

| Surface | Intended reader need | Result |
| --- | --- | --- |
| [Repository README](../../../README.md#inspect-one-artifact-pair-locally), [documentation index](../../index.md), and [capture README](../../../capture/README.md) | Immediate current-capability route | **Pass.** They lead to the tutorial and raw-handling task while retaining synthetic-fixture and current-capability non-claims. |
| [Developer landing](../../developers/index.md) | Developer/integrator routing | **Pass.** Outcome, lookup, and understanding routes are visibly separated, including both halves of the raw-artifact split. |
| [Artifact-pair tutorial](../../developers/tutorials/inspect-an-artifact-pair.md) | Action plus acquisition | **Pass.** First use, three fixture journeys, exact results, and cross-mode next routes remain coherent. |
| [Invalid-pair how-to](../../developers/how-to/diagnose-an-invalid-artifact-pair.md) | Action plus application | **Pass.** Recovery stays task-led and verification reaches explanation/reference. |
| [Raw-artifact handling how-to](../../developers/how-to/handle-raw-dbt-artifacts-safely.md) | Action plus application | **Pass.** The real-work outcome, prerequisites, ordered controls, verification, lifecycle consequence, and related routes are complete. |
| [Python API](../../developers/reference/python-api.md) and [CLI/report reference](../../developers/reference/cli-report-and-exit-codes.md) | Cognition plus application | **Pass.** Machinery and stable contracts remain lookup-led; action routes leave reference. |
| [Pair-state explanation](../../developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md) and [raw-custody explanation](../../developers/explanation/raw-artifact-custody.md) | Cognition plus acquisition | **Pass.** Each develops one mental model and hands action to the correct how-to. |
| [Documentation plan](../../plans/documentation-plan.md) | Route, ownership, and evidence contract | **Pass.** Inventory, family row, seven leaf rows, inherited publication/dependency state, and mandatory per-page fields agree. |
| [P1.1 evidence](../../evidence/p1.1-local-artifact-pair-2026-07-15.md) | Dated immutable evidence | **Pass.** Source revision, executable checker, occurrence semantics, exact counts, and zero-error result are reproducible. |

## Positive controls and checks

The repository-owned gate passed on the exact reviewed commit without Databricks or paid compute:

```text
scripts/check_capture.sh
94 tests passed
tracked_markdown_files=117
local_links=160
fragments=48
errors=0
Ruff lint: passed
Ruff format: passed
ty: passed
fixture regeneration/diff: passed
runtime-only installation and API example: passed
wheel build and isolated installed CLI: passed
DBTOBSB_CAPTURE_CHECK_PASSED
```

An independent heading check over the 16 scoped source documents produced:

```text
scoped_files_heading_checked=16
heading_errors=0
```

Each scoped document has exactly one H1 and no skipped ATX heading level. `git diff --check` passed before this report was created. The source continues to label fixtures synthetic and sanitized, keep pair validity separate from dbt outcome and capture completeness, distinguish workstation-local inspection from future Databricks-local custody, and avoid treating a safe report as a declassification decision.

## Genuinely deferred rendered-site follow-up

These are later publication gates, not source blockers for findings `001`–`004`:

1. Verify rendered breadcrumbs, audience/mode context, related links, and visible P1.1-versus-future feature status.
2. Verify search routing for `PAIR_INVALID`, exit `3`, issue codes, raw artifacts, retention, support payload, customer-local, and capture state.
3. Exercise generated links/fragments and static CLI help links in the built artifact.
4. Test keyboard order, focus, skip navigation, heading navigation, link purpose, tables, code-copy fidelity, contrast, reflow, and screen-reader output.
5. Run publication-safety checks over source, rendered HTML, search indexes, metadata, and build artifacts.
6. Publish this accepted latest report from the review index while preserving both prior immutable finding records.

## Final disposition

**PASS_WITH_FOLLOW_UP** for commit `7ce722cddfed42f1e96741bb07b6cd8762127f22` and source-route aggregate `4bd4ae3e459fba0e6694042d20b73bc17a1a23abe558e3e9e885c3ef6f2828f8`.

`DIA-P1.1-001` and `DIA-P1.1-002` remain closed. `DIA-P1.1-003` and `DIA-P1.1-004` are now closed. Only the explicitly deferred rendered/publication gates remain.
