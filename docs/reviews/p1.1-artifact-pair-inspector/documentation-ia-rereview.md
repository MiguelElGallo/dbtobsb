# Diátaxis information-architecture re-review: P1.1 artifact-pair inspector

- Reviewed commit: `3665590ea9d9cfd65fc695b9c6cf0a18493fc077`
- Prior review: [documentation-ia.md](documentation-ia.md), verdict `CHANGES_REQUIRED`
- Review date: 2026-07-15
- Review mode: independent immutable source-level Markdown and reader-route re-review
- Verdict: **CHANGES_REQUIRED**
- Prior blocking findings closed: **2 of 2**
- New blocking findings: **2**
- Highest severity: **Medium**
- Cloud, Databricks, authentication, and paid-compute activity: **none**

## Executive verdict

Commit `3665590…` closes both prior Diátaxis findings. The runnable Python first-use journey now belongs to the tutorial, while the Python reference is organised around the function, public types, supported values, and report contract. The tutorial and invalid-pair how-to now link to the pair/outcome/capture explanation, and that explanation provides useful return routes.

The re-review nevertheless finds two new source/evidence blockers. The newly added raw-artifact-custody page is routed as explanation but is titled and substantially written as a real-work handling guide; it is also absent from the documentation plan's implemented P1.1 inventory and mandatory page-registry row. Separately, the immutable evidence record's Markdown-link totals cannot be reproduced from the exact commit and do not name a narrower counting convention or executable check. These are current source defects, not rendered-site unknowns, so the verdict remains `CHANGES_REQUIRED`.

## Immutable scope and hashes

The source-route aggregate covers this exact path-sorted 15-file set. Each SHA-256 was recomputed from the reviewed commit:

```text
eafc7289df2792ad6085a073b1ea457c4053c4f88160a3f85d27c3cddcf7a8f9  README.md
5c1578037f99f3738dacb2f549652555b3e50a1ea6634cbd6e26d773aff00cbc  capture/README.md
df0b1e4e2f9aed986085535dc03f9bb7db98d759939acdd2650e60b6a2824cf9  docs/developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md
8cddedf3f54c543831a017e453311458ffbe5f8723d38e9c59a8bc65392e2784  docs/developers/explanation/raw-artifact-custody.md
c73dc413e185d6fda992df7679806be9bf6a576bd57f2e709f1fa3c996b910da  docs/developers/how-to/diagnose-an-invalid-artifact-pair.md
7b3f4c09b1bcba4061e1a067406862594d5819cbe57251a5d425b99c151b4182  docs/developers/index.md
345f8421a519f96de5c66a0d8b8b752836ed241e3a1f3c29167624032de2be2d  docs/developers/reference/cli-report-and-exit-codes.md
a935c761200df30b5ce0384f1834cc0edb6bf8836e24dd0fb91dd2ca23626b82  docs/developers/reference/python-api.md
e7f400f158584d8a35e1f02db1b7cc78b508bfd7eb13b1c36bea1e3fea011aae  docs/developers/tutorials/inspect-an-artifact-pair.md
ae84d27f2394a9a3657ea19d2c3c390b7109458d9131444b34e9396610081a29  docs/evidence/p1.1-local-artifact-pair-2026-07-15.md
f0216648de8a09a665381f1cd0af948409cc124022b77dc3aa8f9774f2e71ee3  docs/index.md
80a528d311747ce0c950c1de1c67bbb35215835b9a77152d9b20c26142f13e62  docs/plans/documentation-plan.md
00e410370497edc3b55bfb2ee9491eeb91512dca64b81d44543c0f04c72076eb  docs/plans/product-plan.md
4189c82644fdbc93dc11faf1f652831ffab5e54ffd320e2c28af1b788283f95b  docs/research/source-register.md
af0f8b9cc8b717689f9b9c2ba2217db6df56c7f355508e1e2198b3b9cb3cb382  docs/reviews/README.md
```

The SHA-256 of that path-sorted `shasum -a 256` record stream is:

```text
8181f069ee5fe50c6f259ac4a1632263eedbe5df5aea89202c9f607696e01fa5
```

The prior immutable finding record and executable corroborating inputs were hashed separately:

```text
8f8543fd99bd04f4bb2688ad3c3b221c84452103767ffa64c7185f65b335520a  docs/reviews/p1.1-artifact-pair-inspector/documentation-ia.md
32f97d5a80af2a4531e2b686e6643708eec9a5d2174b58d6b5f8e4d02c174438  capture/tests/test_documentation.py
9ec9e35e7362cbe2907483e344c2979bd886b9586b03d35b465d93e533ec5099  capture/examples/inspect_valid_fixture.py
51d16177f3e517f2342df108ba6886aec6e7a4ea1d65e147ced70e7c1e1f91cd  scripts/check_capture.sh
```

This re-review report is outside every reviewed input and aggregate.

## Current review basis

Official guidance was refreshed on the review date:

- [The Diátaxis compass](https://diataxis.fr/compass/) classifies practical action for application of skill as how-to, and understanding-oriented cognition for acquisition as explanation.
- [How-to guides](https://diataxis.fr/how-to-guides/) address a real-world goal or problem with an executable, logically ordered solution.
- [Reference](https://diataxis.fr/reference/) neutrally describes product machinery; concise usage examples are explicitly appropriate when they illustrate rather than instruct.
- [Explanation](https://diataxis.fr/explanation/) develops context and connections at a distance from immediate work; it warns that allowing instruction to creep in both weakens explanation and removes instruction from its correct location.
- [Complex hierarchies](https://diataxis.fr/complex-hierarchies/) permit audience-first organisation, but require user-needs logic and content that does not muddle forms or purposes.

Repository-specific acceptance comes from the [documentation plan](../../plans/documentation-plan.md), especially the implemented P1.1 inventory, navigation/page-traceability contract, D1P registry row, page contract, and separate architecture review pass. Its rule is explicit: explanation does not masquerade as procedure, and no page enters drafting without a matching registry row and page-specific prerequisites/evidence.

## Resolution of prior findings

### DIA-P1.1-001 — Closed

The prior finding required the setup/run/check-output procedure to leave the Python reference, a concise descriptive API example to remain permissible, and first use to be linked to action-oriented material.

The new source satisfies every condition:

1. [Tutorial step 4](../../developers/tutorials/inspect-an-artifact-pair.md#4-use-the-python-api) now owns the shell command, guided first result, exact output, and observation.
2. [Python API](../../developers/reference/python-api.md) opens with the function contract and is structured by function, example, public types, input boundary, supported pair, and result interpretation.
3. Its opening sentence links installation/first result to the tutorial.
4. The remaining `Example` is descriptive and located beside the API contract. Official reference guidance explicitly permits succinct usage examples, and the repository page contract permits examples.
5. `test_displayed_python_example_matches_checked_in_program` prevents the illustrative code from drifting from the checked-in program.

The retained compatibility anchor `<a id="run-a-first-inspection"></a>` does not restore a task section or affect the page's current mode.

**Resolution: CLOSED.**

### DIA-P1.1-002 — Closed

The prior finding required both action routes to lead to the existing explanation without moving conceptual discussion into the task pages.

The new source satisfies every condition:

1. The [tutorial conclusion](../../developers/tutorials/inspect-an-artifact-pair.md#what-you-have-proved) links to why pair validity, dbt outcome, and capture state are separate.
2. The [how-to confirmation](../../developers/how-to/diagnose-an-invalid-artifact-pair.md#confirm-the-recovery) links to the same explanation while retaining its CLI reference route.
3. The [explanation](../../developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md) now links back to the tutorial and recovery guide.
4. The detailed mental model remains in explanation; the action pages retain only the short interpretation needed to use their results safely.

**Resolution: CLOSED.**

## Current route assessment

| Surface | Intended reader need | Result |
| --- | --- | --- |
| [Repository README](../../../README.md#inspect-one-artifact-pair-locally) | Immediate current-capability route | **Pass.** P1.1 scope, sensitive-input boundary, fixture command, and non-claims remain before the much larger P0 path. |
| [Documentation index](../../index.md) | Transitional planning index plus P1.1 route | **Pass with inherited D0 gate.** It points directly to the tutorial and input boundary without claiming to be the finished site. |
| [Capture README](../../../capture/README.md) | Package-local orientation | **Pass.** It leads with the tutorial, then lookup material, and warns before real-file substitution. |
| [Developer landing](../../developers/index.md) | Developer/integrator audience route | **Fail for the new custody entry.** Existing tutorial/how-to/reference/explanation grouping remains concise, but “Handle raw dbt artifacts safely” is placed under “Understand the boundaries” despite promising and containing a handling task. |
| [Artifact-pair tutorial](../../developers/tutorials/inspect-an-artifact-pair.md) | Action plus acquisition | **Pass.** Four controlled fixture/API results remain deterministic, safe, concrete, and choice-free; conceptual and lookup transitions are explicit. |
| [Invalid-pair how-to](../../developers/how-to/diagnose-an-invalid-artifact-pair.md) | Action plus application | **Pass.** It begins from an actual failure, routes by issue family, gives actionable recovery, verifies the result, and links to reference/explanation. |
| [Python API](../../developers/reference/python-api.md) | Cognition plus application | **Pass.** The machinery-led contract is neutral, complete for the public surface, and illustrated without an embedded shell task. |
| [CLI/report reference](../../developers/reference/cli-report-and-exit-codes.md) | Cognition plus application | **Pass.** The expanded issue registry mirrors stable machinery and sends recovery to symptom-specific how-to anchors. |
| [Pair/outcome/capture explanation](../../developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md) | Cognition plus acquisition | **Pass.** It develops the three-fact mental model and now has useful cross-mode routes. |
| [Raw-artifact custody](../../developers/explanation/raw-artifact-custody.md) | Mixed: conceptual boundary plus real-work handling | **Fail.** See `DIA-P1.1-003`. |
| [P1.1 evidence](../../evidence/p1.1-local-artifact-pair-2026-07-15.md) | Dated immutable evidence | **Fail only for the unreproducible Markdown totals.** Runtime, fixture, quality, and non-claim boundaries remain appropriately evidence-oriented. See `DIA-P1.1-004`. |
| Plans/source register/review record | Normative contract, provenance, and audit | **Fail for route registration.** The new custody page is absent from the implemented inventory and D1P registry. Future Databricks collection remains correctly separate. |

## New blocking findings

### DIA-P1.1-003 — Raw-artifact custody is action-led but routed as unregistered explanation

- Severity: **Medium**
- Status: **Blocking**
- Sources: [raw-artifact-custody.md](../../developers/explanation/raw-artifact-custody.md), [developer landing](../../developers/index.md#understand-the-boundaries), and [documentation plan](../../plans/documentation-plan.md#information-architecture)

The page's title, “Handle raw dbt artifacts safely”, promises a real-work outcome. Its “Apply the caller's evidence lifecycle” section directs the reader to select approved storage/access controls, govern extracts and backups, prohibit ordinary-ticket transfer, apply retention/legal-hold decisions, and use an exceptional restricted-evidence process. By the compass, this informs action in application of skill and is how-to material.

The same page also contains genuine explanation: why inputs remain sensitive despite a safe output, what P1.1 does and does not do, and why workstation-local inspection is not the future Databricks-local custody model. Keeping both needs under `explanation/` makes the page serve two modes, while the developer landing labels the action-titled page as an understanding route. This is precisely the instruction creep that current Diátaxis explanation guidance and the repository's page contract reject.

The route is also unregistered. The documentation plan's implemented P1.1 inventory names only the pair/outcome/capture explanation, and the D1P page-family row omits raw custody. That conflicts with the same plan's rule that no page enters drafting without a row covering audience, dependency, stage/owner, publication state, prerequisites/next pages, synonyms/codes, and evidence.

Required resolution:

1. Choose and state the primary reader need.
2. If the goal is real-file handling, move/reshape the action material as a how-to with a concrete outcome, audience/environment, prerequisites, ordered controls, verification, lifecycle/cleanup consequence, and related reference/explanation links.
3. Keep the conceptual “why sensitive” and local-versus-Databricks custody model in a separately named explanation, or reframe this page entirely as that explanation and move imperative handling elsewhere.
4. Update the developer landing and every inbound/outbound link to reflect the selected mode.
5. Register every retained/new page in the implemented P1.1 inventory and D1P registry with the mandatory traceability/evidence fields.
6. Freeze and independently re-review the resulting route.

Acceptance is not satisfied by changing only the directory or title; the reader need, content shape, navigation, and plan registry must agree.

### DIA-P1.1-004 — The immutable Markdown-link evidence is not reproducible

- Severity: **Low**
- Status: **Blocking to documentation-evidence acceptance**
- Source: [P1.1 evidence — Quality evidence](../../evidence/p1.1-local-artifact-pair-2026-07-15.md#quality-evidence)

The evidence record says a documentation check resolved 120 local Markdown links, including 28 fragment targets, across 113 Markdown files. An independent scan of the exact tracked Markdown set at `3665590…` confirms 113 files but finds 133 local link occurrences and 41 fragment occurrences. All 133 targets resolve, so this is not a broken-link defect; it is an undefined or stale immutable evidence total.

The independent method:

- enumerated exactly `git ls-files '*.md'`;
- ignored fenced code blocks;
- counted each relative Markdown link occurrence, excluding `http`, `https`, `mailto`, and `tel`;
- resolved paths relative to the source file;
- validated fragments against ATX-generated anchors and explicit HTML `id` anchors; and
- checked for repository escape and missing targets.

No checked-in link-inventory test or script was found. `capture/tests/test_documentation.py` verifies the Python example, public API values, issue registry/recovery routes, and sensitive-input wording, but not the claimed whole-repository Markdown totals.

Required resolution:

1. Correct the evidence totals, or state the exact narrower scope/counting convention that reproducibly yields `120` and `28`.
2. Check in or name the deterministic command/test that produced the totals so later reports can reproduce the same result.
3. Keep the distinction between “targets resolved” and a raw occurrence count explicit.
4. Freeze and re-run the documentation evidence before re-review.

## Positive controls and checks

The full repository-owned capture gate passed on the exact commit without Databricks or paid compute:

```text
scripts/check_capture.sh
94 tests passed
Ruff lint: passed
Ruff format: passed
ty: passed
fixture regeneration/diff: passed
runtime-only installation and API example: passed
wheel build and isolated installed CLI: passed
DBTOBSB_CAPTURE_CHECK_PASSED
```

The independent source check produced:

```text
tracked_markdown_files_checked=113
local_links_checked=133
fragment_links_checked=41
scoped_files_heading_checked=15
heading_errors=0
link_errors=0
```

Every scoped document has one H1 and no skipped ATX heading level. The old compatibility anchor and all new issue-registry recovery fragments resolve. `git diff --check` passed and the reviewed worktree was clean before this report was created.

The content-level boundaries also remain strong: fixtures are visibly synthetic/sanitized; a valid pair is never called dbt success or capture completeness; a local workstation inspection is not presented as Databricks runtime/custody proof; P0 and future collector work do not obscure the current P1.1 route; and reference examples remain allowlisted rather than raw-evidence examples.

## Genuinely deferred rendered-site gates

These gates remain deferred until the source findings are resolved and an accepted site exists:

1. Verify rendered audience/mode context, breadcrumbs, previous/next and related links, and visible P1.1-versus-future feature status.
2. Verify that search terms such as `PAIR_INVALID`, exit `3`, issue codes, “raw artifacts”, “retention”, “support payload”, “customer-local”, and “capture state” route to the correct page type after custody content is reclassified.
3. Exercise generated links/fragments and confirm the static CLI help route in the built artifact.
4. Test keyboard order, focus visibility, skip navigation, heading navigation, link purpose, table semantics, code-copy fidelity, contrast, reflow, and screen-reader output across complete routes.
5. Run publication-safety checks over source, rendered HTML, search indexes, metadata, and build artifacts.

The transitional `docs/index.md` and full D0 product hierarchy remain the inherited later gate. After all documentation re-reviews land, the review index must publish the accepted latest reports while preserving this and the prior immutable findings. None of these later tasks can waive `DIA-P1.1-003` or `DIA-P1.1-004`.

## Final disposition

**CHANGES_REQUIRED** for commit `3665590ea9d9cfd65fc695b9c6cf0a18493fc077` and source-route aggregate `8181f069ee5fe50c6f259ac4a1632263eedbe5df5aea89202c9f607696e01fa5`.

`DIA-P1.1-001` and `DIA-P1.1-002` are closed. Acceptance now requires a mode-correct and registered raw-custody route plus reproducible immutable Markdown-link evidence. Rendered-site validation remains a separate later gate.
