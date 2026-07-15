# Final Diataxis information-architecture re-review: P0 planning baseline 0.19

- Review role: independent documentation information-architecture specialist
- Review method: focused Diataxis architecture and task-routing re-review
- Review date: 2026-07-15
- Planning author aggregate: `703ae3cc1a86bee5d641c7fa478fbb49bdd88cd193f2aec36e61e9b00078eb5f`
- Evidence SHA-256: `d4904dc48dd8d803d258e58845da929418d5f11dbb55a805aa919c9fbb71c0c2`
- Run-record-template SHA-256: `172ae9825e5e7383526fd2879fe4deb29df3a24ac972c63fd37559484f4d310b`
- Verdict: **PASS_WITH_FOLLOW_UP**
- Highest severity: **Low**, inherited deferred D0 gate
- New findings: none
- Blocking findings: none
- Cloud/authentication activity: none

## Executive verdict

The baseline 0.19 restructuring introduces no documentation-architecture blocker. It improves the current P0 route materially:

- README leads with **What works now**, not the future product design.
- The only executable task is one numbered **Run the P0 smoke** how-to.
- The cost record is linked at the exact step where the reader must copy and approve it.
- Current health output and final cleanup proof are embedded in the operational sequence.
- Future observability behavior is moved below the procedure into **Product direction** and linked to the detailed plans.
- Evidence and index links resolve to the renamed current README anchor.

The prior Low finding from `documentation-ia-final.md` remains accurately deferred to D0: the repository still has a transitional README plus planning index rather than the final four-mode product-documentation site. That is a planned gate, not a current P0 blocker. No product-documentation site or rendered-site pass is claimed.

## Immutable inputs

The planning author aggregate was reproduced from `README.md`, `AGENTS.md`, `docs/index.md`, and all Markdown files under `docs/decisions`, `docs/plans`, and `docs/research`:

```text
703ae3cc1a86bee5d641c7fa478fbb49bdd88cd193f2aec36e61e9b00078eb5f  -
```

The evidence and copy-only run-record template remain separate inputs:

```text
d4904dc48dd8d803d258e58845da929418d5f11dbb55a805aa919c9fbb71c0c2  docs/evidence/p0-live-smoke-2026-07-15.md
172ae9825e5e7383526fd2879fe4deb29df3a24ac972c63fd37559484f4d310b  docs/templates/p0-smoke-run-record.md
```

This report is outside all three frozen inputs.

## Diataxis criteria refreshed

The review applied these current principles:

- Documentation should serve four distinct needs: tutorial, how-to, reference, and explanation ([Diataxis overview](https://diataxis.fr/)).
- Tutorials are controlled learning experiences; how-to guides direct a competent reader's real work ([tutorial and how-to distinction](https://diataxis.fr/tutorials-how-to/)).
- Reference describes machinery neutrally and links to procedures rather than absorbing them ([reference guidance](https://diataxis.fr/reference/)).
- Larger sets can place the four modes inside an audience/task hierarchy, with overview landing pages instead of bare file lists ([complex hierarchies](https://diataxis.fr/complex-hierarchies/)).

## Focused restructuring assessment

| Surface | Baseline 0.19 function | Result |
| --- | --- | --- |
| README introduction | Brief product positioning plus explicit “early implementation” wording | **Pass** — establishes purpose without claiming implementation completeness. |
| **What works now** | Two short paragraphs state exact P0 capability, exclusions, historical proof, and later local-only guards | **Pass** — current/future and live/local evidence are distinct. |
| **Run the P0 smoke** | Four numbered task stages: readiness, private approval, one run, final readback | **Pass** — one real-work how-to with consequence before mutation and verification after it. |
| **Product direction** | Six principles plus links to detailed planning artifacts | **Pass** — concise explanation/roadmap context after the current task, not mixed into its steps. |
| `docs/index.md` | Planning-artifact list plus direct route to the smoke | **Pass for P0** — accurately labels current scope and warns that dbt execution/ingestion are later. |
| Evidence record | Dated sanitized record of what happened, what did not happen, and the historical process finding | **Pass** — evidence/reference record, not a procedure or readiness claim. |
| Run-record template | Copy-only task support artifact with blank, synthetic-approved, and rejected examples | **Pass** — linked from the approval step and not presented as a tutorial, product feature, or public record. |
| Documentation plan | Future four modes inside audience/task navigation, with page registry and implementation stages | **Pass at plan level** — reader needs, ownership, prerequisites, publication state, and evidence are explicit. |

## Current P0 task sequence

The restructured route presents consequential information in the correct order:

1. **Scope** — the reader sees that this is App liveness only.
2. **Environment gate** — only a dedicated, completely visible smoke workspace is supported.
3. **Local validation** — all non-cloud checks precede remote action.
4. **Private approval** — the copy-only record, accountable cleanup owner, inventory, timestamps, DBU assumptions, no-hard-ceiling acknowledgement, and required final state precede execution.
5. **Consequence** — billing, timer, failed-stop exposure, escalation, and residual stopped objects are visible before the command.
6. **One mutation** — exact environment inputs and one wrapper command are provided.
7. **Expected result** — the exact health body appears immediately after the action description.
8. **Independent final readback** — App state/size/bindings plus zero warehouses/clusters must all pass; unrelated resources are never treated as cleanup targets.

This is correctly a how-to for an operator at work. The future tutorial remains a separate controlled, fixture-based, choice-free learning path in the documentation plan.

## Run-record-template placement

The template is appropriately subordinate to the how-to rather than promoted as a competing entry route. Its IA strengths are:

- “copy-only” and “private record system” appear before the data structure;
- real identities, hosts, IDs, and internal URLs are prohibited in the repository;
- the blank form shows the required shape;
- the synthetic approved example demonstrates completion without a live identifier;
- the rejected example makes a failed authorization state recognizable; and
- `cleanup_owner_reference` is explicitly private and appears in blank, approved, and rejected examples.

The template records an input/checkpoint for the smoke procedure. It neither teaches the overall product nor describes future dbt machinery, so no new tutorial/reference conflation is introduced.

## Inherited Low follow-up: transitional entry layer

- Prior record: `documentation-ia-final.md`, finding `DOC-IA-P0-001`
- Severity: **Low**
- Current state: **Open and correctly deferred to D0**
- Current-part blocker: **No**

README still combines repository explanation with the sole operational how-to, and `docs/index.md` is still a flat planning index. With one executable task, this is clear and proportionate. It must not become the permanent structure as product tasks accumulate.

The existing D0 acceptance contract remains sufficient:

1. replace the planning index with a status-first product home;
2. create tutorial, how-to, reference, and explanation overview landing pages;
3. group navigation by audience-recognizable task/concern;
4. move executable smoke guidance to a dedicated how-to and leave README as a repository route;
5. carry `base`, `optional installed capability`, and `future/not available` state in the page registry and visible routes; and
6. re-review every affected route after a move, split, rename, or optionality change.

Baseline 0.19 does not claim to have completed D0, so this open gate does not require a P0 change.

## Rendered-site decision

The repository has no accepted documentation-site configuration and no `docs/tutorials`, `docs/how-to`, `docs/reference`, or `docs/explanation` directories. The documentation plan explicitly says the current index is a planning index until D0 and permits planning review before pages exist.

Therefore the following remain not-yet-executable gates rather than passes or defects:

- rendered navigation and responsive layout;
- search across the four modes;
- rendered code, fragment, and complete-site link checks;
- alt text, contrast, keyboard, screen-reader, zoom, and reflow checks; and
- generated-site and CI-artifact publication-safety review.

The current local entry links were checked: all referenced files exist, `README.md#run-the-p0-smoke` exists, and both `docs/index.md` and the evidence record use that corrected anchor.

## New findings

None.

## Final disposition

**PASS_WITH_FOLLOW_UP** for planning aggregate `703ae3…`, evidence `d4904d…`, and template `172ae9…`.

The baseline 0.19 restructuring is clearer, routes the only current task correctly, and preserves an honest current-versus-future boundary. The inherited Low D0 transition remains open by design; it is not a P0 blocker. Any later content change or D0 site implementation requires a new hash-bound IA and rendered-site review.
