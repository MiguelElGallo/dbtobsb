# Diátaxis information-architecture review: P1.1 artifact-pair inspector

- Reviewed commit: `1900cd01254837010d7d93bb0cd69cf0b98eb1b5`
- Review date: 2026-07-15
- Review mode: immutable source-level Markdown and reader-route inspection
- Verdict: **CHANGES_REQUIRED**
- Highest severity: **Medium**
- Blocking findings: **2**
- Cloud, Databricks, authentication, and paid-compute activity: **none**

## Executive verdict

P1.1 has a coherent small-scale Diátaxis route: the developer landing page groups one controlled tutorial, one recovery how-to, two contract references, and one explanation by reader need. The tutorial teaches through three synthetic fixtures; the recovery guide stays focused on a real invalid-pair problem; the CLI reference is a neutral catalogue; and the explanation develops the essential three-fact mental model. Root and package entry points make the implemented P1.1 capability visible without presenting P0 or future collection work as part of it.

Two source-level architecture defects prevent acceptance. The Python API reference embeds a first-use task procedure, contrary to both current official Diátaxis reference guidance and the repository's explicit page contract. In addition, the tutorial and recovery how-to do not link readers to the existing explanation at the point where each task repeats the pair-validity/dbt-outcome/capture-state boundary. Those are current source defects, not rendered-site unknowns, so this review cannot use `PASS_WITH_FOLLOW_UP`.

## Immutable scope

The exact review scope is the following 14-file set. The SHA-256 after each path was recomputed from the reviewed commit:

```text
e26ef1011555fa855b81b92b3a741c3a3e88942cacf993d1e26f29423dfb97d4  README.md
b30aff40deabd3d22a7a74f562f8ca187f71f23e8e1cfb23e214b31d68e4e562  capture/README.md
2109941e8f55bf5e3da8139eee62008874ef6fbc3f3b4f3010edb0af1dde9056  docs/developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md
7f6005d64fefb1180b76ac16cb116c3ac545e4bab1ffda32119ac89d403c81ca  docs/developers/how-to/diagnose-an-invalid-artifact-pair.md
877bbbcd3a5c21d68b33579ba1d0d759902895d271a334ed8b677055c43d4e70  docs/developers/index.md
64f68c7ef456447df1106c296ab6e09cfc3789c95db1b6cd3a348e172a31995b  docs/developers/reference/cli-report-and-exit-codes.md
c9b3d40a31aa3ae06bf23fa6823b8f0f58baf6155a50dfad5a7fb6d3960fddb5  docs/developers/reference/python-api.md
64ca585df20b777a057384bd947b9ecf0aa0e3ca60576d4da303efe467397fc3  docs/developers/tutorials/inspect-an-artifact-pair.md
cd8acc4b2893df2e24ef57a4297fb0c27c9784dae93b9e032fd1959072a7665a  docs/evidence/p1.1-local-artifact-pair-2026-07-15.md
e40557c77af24554c6c063e9981d7f446b56856b16abf6bc5b7e5e287c8e4ebc  docs/index.md
80a528d311747ce0c950c1de1c67bbb35215835b9a77152d9b20c26142f13e62  docs/plans/documentation-plan.md
00e410370497edc3b55bfb2ee9491eeb91512dca64b81d44543c0f04c72076eb  docs/plans/product-plan.md
4189c82644fdbc93dc11faf1f652831ffab5e54ffd320e2c28af1b788283f95b  docs/research/source-register.md
af0f8b9cc8b717689f9b9c2ba2217db6df56c7f355508e1e2198b3b9cb3cb382  docs/reviews/README.md
```

The SHA-256 of that path-sorted `shasum -a 256` record stream is:

```text
635ab0f71c574e9a9a7efcb80f6bdf7c2e8c5a69dadbaaf5db0409c85ec58333
```

This report is outside the reviewed input and aggregate.

## Review basis

The assessment used the current official guidance available on the review date:

- [Diátaxis overview](https://diataxis.fr/) — documentation is organised around four distinct user needs.
- [The compass](https://diataxis.fr/compass/) — action/cognition and acquisition/application classify content by the need it serves.
- [Tutorials](https://diataxis.fr/tutorials/) — a tutorial is a controlled, learning-oriented experience with concrete action, early visible results, minimal explanation, and no distracting alternatives.
- [How-to guides](https://diataxis.fr/how-to-guides/) — a how-to serves an already-competent reader's real-world goal or problem and keeps attention on action.
- [Reference](https://diataxis.fr/reference/) — reference describes the machinery neutrally, austerely, and authoritatively; it can describe correct usage but should link to task and learning material rather than absorb it.
- [Explanation](https://diataxis.fr/explanation/) — explanation broadens understanding, connects facts, supplies context, and answers the conceptual “why”.
- [Complex hierarchies](https://diataxis.fr/complex-hierarchies/) — audience-first structure is valid when modes remain distinct, landing pages provide real overviews, and routes stay logical for users.

The repository-specific acceptance contract is [Documentation plan](../../plans/documentation-plan.md), especially its P1.1 route, D1P evidence row, page contract, and separate review-pass requirements. The [research source register](../../research/source-register.md#documentation-and-usability) correctly treats Diátaxis as information architecture rather than prose style.

## Reader-route and mode assessment

| Surface | Reader need and mode | Assessment |
| --- | --- | --- |
| [Current public inspection tutorial](../../site/tutorials/inspect-artifacts-locally.md) | Current capability and immediate first route | **Pass.** The public route now explains the task without internal milestone language. |
| [Documentation index](../../index.md) | Transitional planning index plus current execution routes | **Pass for P1.1, with the inherited D0 gate retained.** It explicitly links developer documentation and gives P1.1 its own outcome heading; it does not claim to be the finished product-doc home. |
| [Capture README](../../../capture/README.md) | Package-local orientation | **Pass.** It states the one operation and its boundaries, then routes first to the tutorial and next to lookup material. |
| [Developer landing page](../../developers/index.md) | Developer/integrator audience landing | **Pass.** “Start with an outcome”, “Look up a contract”, and “Understand the boundaries” route by need rather than by repository machinery. Four additional empty mode landing pages would add fragmentation to this five-page slice. |
| [Inspect an artifact pair](../../developers/tutorials/inspect-an-artifact-pair.md) | Action plus acquisition: tutorial | **Pass in its learning sequence; fail in closing navigation.** The three fixed fixture journeys are concrete, repeatable, choice-free, visibly successful, and explicitly synthetic. Finding `DIA-P1.1-002` covers the missing explanation route. |
| [Diagnose an invalid artifact pair](../../developers/how-to/diagnose-an-invalid-artifact-pair.md) | Action plus application: how-to | **Pass in task shape; fail in closing navigation.** It begins from a real failure, branches by issue family, gives one primary recovery path, and ends with verification. Finding `DIA-P1.1-002` covers the missing conceptual route. |
| [Python API](../../developers/reference/python-api.md) | Intended cognition plus application: reference | **Fail.** Its contract sections are sound, but “Run a first inspection” is an embedded first-use task. See `DIA-P1.1-001`. |
| [CLI, report, and exit codes](../../developers/reference/cli-report-and-exit-codes.md) | Cognition plus application: reference | **Pass.** It mirrors the CLI/report machinery, states complete stable values, and keeps recovery in the linked how-to/help route. |
| [Pair validity, dbt outcome, and capture state](../../developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md) | Cognition plus acquisition: explanation | **Pass.** It connects three independently meaningful facts, explains why `COMPLETE` is unavailable, and derives the security benefit without becoming a procedure. |
| [P1.1 evidence](../../evidence/p1.1-local-artifact-pair-2026-07-15.md) | Dated evidence/reference | **Pass.** It records reproducibility, compatibility context, quality evidence, cloud boundary, and remaining qualification gates without becoming onboarding guidance or production proof. |
| Product plan/source register/review index | Normative future contract, research provenance, and audit route | **Pass.** Future archive, collector, runtime, and rendered-site work remains visibly future; none is injected as a current P1.1 capability. |

## Blocking findings

### DIA-P1.1-001 — The Python API reference embeds a first-use task procedure

- Severity: **Medium**
- Status: **Blocking**
- Source: [Python API — Run a first inspection](../../developers/reference/python-api.md#run-a-first-inspection)

The section tells the reader to complete a runtime sync, run a repository command, inspect a checked-in example, and compare exact output. That content informs action for skill acquisition: by the Diátaxis compass it is tutorial-shaped, not reference-shaped. The remainder of the page is appropriately organised around the function, public types, supported pair, and result interpretation, but the opening procedure makes the page serve two incompatible reader needs.

This also directly violates the repository's [page contract](../../plans/documentation-plan.md#page-contract): reference pages may include examples, but they “do not embed procedures”. Keeping the procedure here duplicates the first-use route and creates a future drift point between installation/onboarding instructions and the API contract.

Required resolution:

1. Remove the setup/run/check-output procedure from the reference page or move that runnable journey to an action-oriented page.
2. Keep a concise, descriptive API example beside the function signature if useful; organise it around the API element rather than a reader task.
3. Link from the reference to the tutorial for installation and first use.
4. Preserve the checked-in example's test/evidence coverage without using that coverage to justify mixed documentation modes.

Acceptance is a new frozen input in which the Python API page can be consulted as a neutral contract, with the runnable first-use journey owned by tutorial/how-to material and no duplicated setup sequence.

### DIA-P1.1-002 — Task pages do not route to the existing explanation

- Severity: **Medium**
- Status: **Blocking**
- Sources: [tutorial conclusion](../../developers/tutorials/inspect-an-artifact-pair.md#what-you-have-proved), [how-to confirmation](../../developers/how-to/diagnose-an-invalid-artifact-pair.md#confirm-the-recovery), and [existing explanation](../../developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md)

Both task pages repeat the crucial boundary between pair validity, native dbt outcome, and future capture completeness. The tutorial's final navigation links only to the how-to and CLI reference. The how-to links the code registry but ends without any related explanation link. A reader entering either route directly therefore receives a compressed conceptual warning but no path to the dedicated mental model already written for that purpose.

Official guidance recommends minimising explanation inside tutorials/how-tos and linking to the relevant explanation. The repository's page contract likewise requires related reference and explanation links where applicable. The topic is plainly applicable here: it is the slice's central safety and interpretation boundary.

Required resolution:

1. Add an explicit related link from the tutorial to the pair/outcome/capture explanation.
2. Add an explicit related link from the recovery how-to to that explanation and retain the CLI reference route.
3. Keep procedural recovery in the how-to and conceptual discussion in the explanation; do not solve the missing route by expanding the inline conceptual passages.
4. Consider a concise related-task/lookup block on the explanation so source Markdown remains navigable before a rendered-site breadcrumb layer exists.

Acceptance is a new frozen route in which a reader can move from learning or recovery to the deeper mental model without returning manually to the developer index.

## Positive controls

- The tutorial uses one predetermined sequence and three controlled fixtures. It produces visible, exact results early and repeatedly and offers no production or paid-compute branch.
- The how-to assumes the reader has an actual failed inspection and organises recovery around that human problem, not around an exhaustive walk through internal functions.
- The CLI reference is neutral and sufficiently exhaustive for the P1.1 surface: command shape, flags, all exits, machine report, safety limits, issue registry, and versioning rule are available for lookup.
- The explanation builds a genuine mental model: valid evidence can contain a dbt failure, successful outer execution cannot repair invalid evidence, and capture completeness requires evidence P1.1 never receives.
- `PAIR_VALID` is never presented as dbt success, Databricks archive retrieval, a complete capture, or production qualification. Synthetic/sanitized and `runtime_evidence=false` boundaries are consistent across entry pages, tutorial, explanation, evidence, and plans.
- P0 and future product planning do not overwrite the P1.1 route. The README presents P1.1 before the P0 smoke, package documentation routes directly to it, and future collector/runtime claims remain in planning and remaining-gate sections.
- The developer landing page is an appropriate audience-first hierarchy for a five-page slice. It preserves all four modes without forcing readers through redundant single-item mode landing pages.

## Mechanical source checks

A read-only source check covered all 112 repository Markdown files for relative targets/fragments and the 14 scoped files for heading structure:

```text
markdown_files_checked=112
local_links_checked=69
scoped_local_links_checked=51
scoped_files_heading_checked=14
heading_errors=0
link_errors=0
```

Each scoped file has exactly one H1, no skipped ATX heading level, and no broken checked local target or Markdown heading fragment. The static exit-3 help target `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md#recover-an-input-read-error` also resolves. `git diff --check` passed before this report was added.

These mechanical results do not cancel either semantic navigation/mode finding.

## Later rendered-site gates

The following are real later gates, not reasons to defer the two current source fixes:

1. Build and inspect the accepted documentation site with audience landing, mode context, breadcrumbs, previous/next or related links, and visible P1.1 versus future feature-state labels.
2. Verify that search routes `PAIR_INVALID`, exits `3` and `10`, issue codes, “artifact pair”, “dbt failure”, and “capture state” to the correct page type rather than to planning records first.
3. Check keyboard order, focus visibility, skip navigation, heading navigation, link purpose, table semantics, contrast, reflow, and screen-reader output across the complete routes.
4. Verify copy controls and wrapping for shell, JSON, and text output on narrow viewports without changing bytes or hiding exit/output distinctions.
5. Exercise every rendered local link and fragment, including generated breadcrumbs and the static CLI help route.
6. Run publication-safety checks over source, built HTML, search indexes, metadata, and artifacts before any broader distribution.

The transitional `docs/index.md` planning list and full D0 site hierarchy remain a named follow-up. They do not block this small source route by themselves because the README, capture README, and developer landing expose P1.1 directly; they must be replaced and re-reviewed before a finished product-documentation site is claimed.

## Final disposition

**CHANGES_REQUIRED** for commit `1900cd01254837010d7d93bb0cd69cf0b98eb1b5` and aggregate `635ab0f71c574e9a9a7efcb80f6bdf7c2e8c5a69dadbaaf5db0409c85ec58333`.

The P1.1 content set has the right four-mode skeleton and a strong central mental model, but the Python reference must stop owning a first-use procedure and the two action routes must link to the existing explanation. Freeze those source changes and perform an independent Diátaxis re-review; rendered-site validation remains a separate later gate.
