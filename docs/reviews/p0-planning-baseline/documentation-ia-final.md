# Final documentation information-architecture review: P0 planning baseline 0.17

- Review role: independent documentation information-architecture specialist
- Review method: Diataxis architecture and user-journey review
- Review date: 2026-07-15
- Planning author aggregate: `83be89fd59fe16c023c7e4b7fb6f336d6ab27d44c7c0ebf03a7d862a2a43ce97`
- Evidence SHA-256: `6d1a6e133ce98b01e976a12ea8837733dd0cd1198dddb5ad3225ff0b04f8073a`
- Verdict: **PASS_WITH_FOLLOW_UP**
- Highest severity: **Low**
- Blocking findings: **None**

## Review integrity

The two requested hashes were reproduced before this review began. The files were then read in full at that immutable state.

The shared working tree advanced concurrently before this report was written. At report time, the same hash procedure produced planning aggregate `64ccac49c9cb91656a609fa432b32dc4c9ba451134f5577a722051806e23f8d9` and evidence hash `90d18fdf3412e324f0250a40024a5e95467ecff34096d53462974067d7129e74`. This verdict therefore applies only to the two hashes in the review metadata. It does not approve the later working-tree content.

## Executive verdict

The reviewed P0 baseline is safe to accept as a **planning baseline with one deliberately narrow executable smoke procedure**.

The documents do three important things correctly:

1. They distinguish the implemented App process-liveness smoke from the future dbt observability product.
2. They specify a credible future Diataxis architecture instead of presenting the planning-file list as the finished product documentation.
3. They place the live smoke's prerequisites, cost consequence, stop deadline, checkpoints, recovery, and cleanup around the mutation in the order an operator needs them.

The remaining follow-up is architectural rather than corrective: once product documentation pages exist, the transitional README/planning index must be replaced by the planned mode landing pages and audience/task routes. The current baseline already assigns that work to D0. It is not a P0 blocker because the repository does not claim that a complete user documentation site exists.

## Sources and review criteria

The review used the following Diataxis principles:

- Documentation should serve four distinct needs: tutorial, how-to, reference, and explanation ([Diataxis overview](https://diataxis.fr/)).
- A tutorial is a controlled learning experience; a how-to directs a competent reader's real work ([tutorial and how-to distinction](https://diataxis.fr/tutorials-how-to/)).
- Reference should describe the product machinery neutrally and link to procedures rather than absorb them ([reference guidance](https://diataxis.fr/reference/)).
- A larger documentation set can place the four modes inside a deeper hierarchy, but each section needs an overview landing page rather than only a file list ([complex hierarchies](https://diataxis.fr/complex-hierarchies/)).

## Scope reviewed

| File | Current function in the P0 baseline | Diataxis treatment |
| --- | --- | --- |
| `README.md` | Repository landing page, product-positioning summary, and the only executable P0 procedure | Deliberately transitional mixture of explanation and one how-to |
| `docs/index.md` | Planning index and route to the P0 smoke | Transitional entry point, not the future documentation home |
| `docs/evidence/p0-live-smoke-2026-07-15.md` | Dated, sanitized record of what was actually exercised and observed | Evidence/reference record, not a procedure |
| `docs/plans/documentation-plan.md` | Normative information-architecture, page, review, and publication plan | Planning specification; defines future mode separation |
| `docs/plans/product-plan.md` | Normative staged product contract | Product planning/reference artifact, not end-user guidance |
| `docs/plans/review-process.md` | Review roles, gates, cadence, and record format | Contributor/process reference |
| `docs/decisions/0001-private-app-bundle.md` | Accepted architecture decision and consequences | Decision explanation |
| `docs/research/source-register.md` | Primary-source register and applicability notes | Contributor reference |
| `AGENTS.md` | Contributor guardrails | Contributor-only control; correctly absent from user navigation |

## Criteria results

| Criterion | Result | Assessment |
| --- | --- | --- |
| Tutorial/how-to/reference/explanation separation | **Pass at plan level; follow-up at site level** | The documentation plan defines all four modes and their reader needs. The planned tutorial is safe, linear, fixture-based, choice-free, and cleanup-bound. Real operational work is routed to how-to guides. Reference is explicitly neutral. Explanation pages are contextual. The mode directories and pages do not exist yet and are not claimed to exist. |
| Routing from the current index | **Pass for P0** | `docs/index.md` states the current scope, links to the planning contract and evidence, and routes the only runnable task to the README's P0 section. It warns that dbt execution and artifact ingestion are later work. |
| Implemented smoke versus future product | **Pass** | README, index, evidence, product plan, and ADR consistently limit the implementation claim to App process liveness. They do not claim dbt execution, artifact capture, product-data reads, or product readiness. |
| Prerequisites and consequences | **Pass** | The live prerequisites appear before the command. The cost envelope, operator deadline, residual stopped objects/files, and the possibility of continued cost after a failed stop are disclosed before mutation. |
| Checkpoints, recovery, and cleanup | **Pass** | The command is surrounded by pre-run identity/host controls, bounded run behavior, health/event verification, an exit-trap stop, an explicit post-run state readback, and a safe exception for workspaces containing unrelated compute. |
| Rendered full-site validation | **Pass as explicitly deferred** | No product documentation site, four mode landing pages, or accepted publishing stack exists at this baseline. The plan and review process explicitly allow D0 planning review before pages render and require re-review plus rendered checks once pages exist. No rendered-site pass is falsely claimed. |
| Contributor-rule contradictions | **Pass** | `AGENTS.md` requires separate IA, readability, security, accessibility, and rendered validation when pages exist. That agrees with the plans and does not expose contributor material as user documentation. |

## P0 operator journey

The only current operational journey is sequenced correctly:

1. **Scope first** — the reader is told that the smoke proves process liveness only.
2. **Local checks** — tests, lint, type checking, and shell validation precede any remote mutation.
3. **Live prerequisites** — exact CLI/tool and OAuth-profile expectations are stated.
4. **Cost decision before execution** — compute size, published rate, planned DBU exposure, cancellation deadline, cleanup owner, and required final state are visible before the command.
5. **Consequence before execution** — the reader knows that running compute is billable, a failed stop can continue to cost money, and stopped objects/files remain.
6. **One bounded mutation** — the wrapper validates identity and target, deploys stopped, starts once, checks health and its event, and enters cleanup on every exit path.
7. **Independent state readback** — the cleanup owner checks App, warehouse, and cluster state after the wrapper exits.
8. **Safe shared-workspace branch** — readers with unrelated resources are told to use a reviewed paginated before/after inventory and never stop or delete unrelated compute.

This is a how-to for a competent operator doing real work, not a tutorial. The future tutorial is correctly planned as a separate controlled fixture experience.

## Finding DOC-IA-P0-001: transitional entry layer will not scale

- Severity: **Low**
- Status: **Follow-up required at D0**
- Affected files: `README.md`, `docs/index.md`, `docs/plans/documentation-plan.md`

### Evidence

The current index is a short list of planning artifacts plus a route to the README. The README combines repository/product explanation, planning links, and the sole live how-to. That is understandable with one implemented task, and both files disclose their transitional status.

The documentation plan already says that D0 will replace this planning index deliberately with a product home, four overview landing pages, grouped navigation, audience/task routes, a glossary, and a page registry.

### User impact

There is no material P0 ambiguity because only one executable task exists. If additional runnable pages were added without the D0 structure, readers would have to infer:

- whether they are learning, operating, looking up facts, or seeking context;
- which material is available now versus planned;
- which route applies to their role and environment; and
- whether a planning contract is an executable procedure.

### Required follow-up

At D0:

1. Replace the planning list with a status-first product home.
2. Create tutorial, how-to, reference, and explanation overview landing pages.
3. Group routes by audience-recognizable task or concern, not merely by file type.
4. Move the operational smoke into its own how-to page; let README describe the repository and link to that page.
5. Label pages or routes as **Available now**, **Planned**, **Optional**, or **Future/not available** where applicable.
6. Re-run navigation and mode review after every move, split, rename, or optionality change.

### Acceptance evidence

- The home and four overview pages exist.
- The page registry records audience, mode, dependency, stage, owner, prerequisites, publication state, search terms/codes, and evidence.
- Every current executable task is reachable from an audience/task route.
- Planning-only or unavailable routes cannot be mistaken for runnable product features.
- Local navigation and fragment links pass.
- The selected site renderer successfully builds the actual pages before the rendered-site review is signed.

## Deferred gates that are not findings

The following checks are not executable against this P0 planning baseline and must not be recorded as passes yet:

- rendered navigation, responsive layout, and theme behavior;
- rendered code-block and anchor behavior;
- documentation search across the four modes;
- complete-site link checking;
- alt-text and contrast review;
- WCAG 2.2 AA testing of complete documentation journeys; and
- publication-safety inspection of the generated site and CI artifact.

This deferral is accurate. The repository has no accepted documentation-site implementation to render, and the plans explicitly trigger these checks after the relevant pages exist. D0 owns the architecture transition; the first complete rendered journey is then subject to the universal rendered-site pass at its implementation stage.

## Final disposition

**PASS_WITH_FOLLOW_UP** for planning aggregate `83be89fd59fe16c023c7e4b7fb6f336d6ab27d44c7c0ebf03a7d862a2a43ce97` and evidence SHA-256 `6d1a6e133ce98b01e976a12ea8837733dd0cd1198dddb5ad3225ff0b04f8073a`.

No documentation architecture defect blocks P0 acceptance. Finding `DOC-IA-P0-001` must remain owned by D0 and must be closed before the repository presents itself as a complete product documentation site. The later working-tree hashes recorded under **Review integrity** require a separate review.
