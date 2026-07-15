# FastAPI-style documentation review: planning baseline 0.17

- Date: 2026-07-15
- Reviewer: FastAPI-style technical documentation specialist
- Verdict: **CHANGES_REQUIRED**
- Review mode: read-only source review; no Databricks, Azure, authentication, or other cloud activity
- Rendered-site validation: **DEFERRED** because no complete documentation site exists yet

## Frozen review input

This review is bound only to the following immutable baseline 0.17 author set:

| Author file | SHA-256 |
| --- | --- |
| `AGENTS.md` | `b98568650936e701e988f743f6d2b8409f81f9483be7220a2194523b634408e3` |
| `README.md` | `4f7f20417e387dad15e8648e643630480012c0cacb71911dc00bc70e48bd6532` |
| `docs/decisions/0001-private-app-bundle.md` | `bd3a6067890b3640c2d59325db5de29397d69591fa65fcdfb938ca86381c8624` |
| `docs/index.md` | `d0de65579c3ad3d7e56b272eed9611db758bdb95c0573066114ea72573bed792` |
| `docs/plans/documentation-plan.md` | `7f5dd162708caea91d6b791baab3ce2e16e9f73ee49c982dd00b29aab102a1e1` |
| `docs/plans/product-plan.md` | `653f0d9aee35dad4ff6a3e5fd9ea2a577789115b916bcdbaa669e06d2a4edeb5` |
| `docs/plans/review-process.md` | `d6e2c685ea71223a798c0d1b0f42ae6ecfa4870bec4a16d325d871ba7ac38734` |
| `docs/research/source-register.md` | `0256e0b6c8e91c49b94f1fae3015a397d6b8c78954b4b9f7c796d143a0c69afc` |

The globally sorted path-and-content aggregate reproduced at review start as:

```text
83be89fd59fe16c023c7e4b7fb6f336d6ab27d44c7c0ebf03a7d862a2a43ce97
```

The separate evidence input was:

| Evidence file | SHA-256 |
| --- | --- |
| `docs/evidence/p0-live-smoke-2026-07-15.md` | `6d1a6e133ce98b01e976a12ea8837733dd0cd1198dddb5ad3225ff0b04f8073a` |

The shared workspace advanced to baseline 0.18 while this report was being completed. The live files therefore no longer reproduce these hashes. Every assessment below applies to the frozen 0.17 inputs only; it is not a review or approval of 0.18. This report is the only file written by this reviewer.

## Review method

The source review covered outcome-led writing, progressive disclosure, runnable examples, prerequisite and warning placement, returned-result semantics, readiness boundaries, terminology, links, and approachability under regulated-industry constraints.

The benchmark was the documentation behavior illustrated by [FastAPI's First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/): show the smallest useful example, tell the reader exactly how to run and inspect it, show the returned result, and introduce deeper machinery afterward. The information-type check used [Diataxis](https://diataxis.fr/): action-oriented instructions must stay distinct from explanation and reference. These are quality benchmarks, not requirements to copy FastAPI's visual design or weaken dbtobsb's controls.

## Executive assessment

Baseline 0.17 is unusually honest about its narrow outcome. It says immediately that dbtobsb is customer-local dbt Core observability, then states that P0 proves only App process liveness. It does not imply that dbt runs, artifacts are captured, product data is readable, or the product is ready. Cost, authentication, cancellation, cleanup, residual objects, and regulated-data warnings occur before the live command. The evidence page preserves the historical approval-process defect instead of rewriting it as a compliant run.

The documentation is not yet an acceptable no-guess runbook for every workspace it claims to cover. Its final verification commands are runnable only when the workspace has no unrelated compute. For a non-empty workspace, the reader is told to replace those commands with a reviewed, paginated inventory, but is given no procedure or canonical artifact to run. The README also makes a new reader traverse a long block of future implementation and trust machinery before reaching the current P0 task. Those two Medium findings require correction.

## What works well

- **Outcome and scope are explicit.** The opening sentence is concrete, and the P0 section repeatedly distinguishes process liveness from dbt execution, artifact ingestion, product-data access, and product readiness.
- **Warnings precede mutation.** Authentication requirements, the cost envelope, the ten-minute cancellation point, cleanup ownership, continuing-cost risk, and residual stopped objects all appear before the executable live command.
- **The command is secret-safe.** It uses visibly synthetic profile, host, and user placeholders and prohibits tokens and client secrets.
- **Response semantics are honest.** The evidence records the six-field liveness response and explicitly says it is not a dependency, product-data, dbt, or readiness check. The post-run readback is described as a separate observation in the same operator context, not an independent-human attestation.
- **The evidence is auditable without overselling it.** The original missing numeric approval envelope remains a process finding, the DBU estimate is labeled derived rather than invoiced, and no extra paid run was performed to manufacture cleaner history.
- **Source Markdown is structurally sound.** Headings, tables, fenced commands, descriptive links, and text-only state language are usable without relying on color or images.

## Findings

### DOC-STYLE-P0-001 — Non-empty-workspace verification is not runnable

- Severity: **Medium**
- Location: `README.md`, **P0 Databricks App smoke**, after the separate state-readback commands
- Quality affected: runnable examples, precise prerequisites, recovery and cleanup, regulated no-guess operation

The documented `jq` assertions prove the required result only in a workspace where the total number of warehouses and clusters is zero. The next paragraph allows an intentionally non-empty workspace but tells the operator to “replace” the commands with a “reviewed, paginated before/after inventory.” It does not provide that inventory command or script, the stable fields to compare, pagination behavior, capture timing, expected success result, record format, or a review/approval reference.

That is not merely missing background explanation. It transfers the design of a safety control to the person performing a paid live mutation. Two competent operators can create different inventories and reach different conclusions, while the surrounding documentation presents the route as exact and regulated.

Required resolution:

1. Either make a dedicated zero-unrelated-compute workspace an explicit P0 prerequisite and fail before mutation when it is not true; or provide one canonical, read-only, fully paginated before/after inventory procedure for the supported non-empty case.
2. Show the exact successful result, retained evidence, and failure/escalation result.
3. Identify resources by stable IDs and prove that no smoke-owned resource remains running without authorizing any stop or deletion of unrelated resources.
4. Link the procedure directly from the command path so an operator never has to invent it.

### DOC-STYLE-P0-002 — The README reverses progressive disclosure

- Severity: **Medium**
- Location: `README.md`, **Product principles** before **P0 Databricks App smoke**
- Quality affected: outcome-led onboarding, progressive disclosure, approachable style, information-type separation

The initial principles begin with useful product boundaries, then expand into dense future implementation detail: migration envelopes, Direct deployment behavior, Delta attestation states, effective DML and self-grant classification, trusted-root topology, P6 exceptions, stable deployment graphs, AttemptKey semantics, `UTF8_BINARY`, eleven constraints, and the Jobs terminal-state fallback.

These details matter in a regulated product, but this placement makes them prerequisites for discovering what can be run today. Several bullets combine architecture, security assumptions, algorithms, exceptions, and future-stage behavior in a single paragraph. They function as compressed reference/explanation content, not as scannable product principles. Terms such as `Direct`, DML, P6, AttemptKey, and U2M also appear without first-use definitions in the reader's current route.

Required resolution:

1. Keep a short opening set of user-visible principles: customer-local operation, deterministic artifact capture, least privilege, restricted diagnostics, explicit cost/cleanup, and honest capability boundaries.
2. Put a **What works now** or **Run the P0 smoke** route immediately after the outcome and boundary summary.
3. Move the detailed migration, trust, deployment, and controlled-action mechanics into the existing decision, plan, and future explanation/reference pages; link them with descriptive task- or concept-level labels.
4. Preserve every regulated constraint as a visible consequence or warning at the action it governs. Progressive disclosure must reorganize controls, not hide them.
5. Expand essential acronyms on first use—for example, “OAuth user-to-machine (U2M)”—and link stage names or specialist terms to a glossary or their canonical definition.

### DOC-STYLE-P0-003 — The approval record has no copyable contract

- Severity: **Low**
- Location: `README.md`, **Approve the cost envelope first**
- Quality affected: runnable example completeness, approval semantics, consistent regulated operation

The reader is told to copy the envelope into an “approved private run record” and complete it with an approver, cleanup owner, start time, and cancellation time. No template or canonical private-storage requirement is linked, no synthetic completed example shows the expected shape, and “approved” has no explicit pass/fail state. The cost table is useful input, but it is not itself a complete run record or post-run evidence index.

Required resolution:

- Provide a copyable, secret-safe template with required fields, approval state, timestamps, cost assumptions, cleanup result, and references to retained final-state evidence.
- State where policy—not this repository—must authorize storage, retention, and approver identity.
- Show one synthetic completed example and one rejected/incomplete example without real user or workspace identifiers.

### DOC-STYLE-P0-004 — Time-sensitive cost sources are not consistently registered

- Severity: **Low**
- Location: `README.md`, cost references; `docs/research/source-register.md`, Databricks Apps sources; `AGENTS.md`, source-recording policy
- Quality affected: link consistency, source governance, refreshability

The README directly links the current App compute-size table for the `MEDIUM` `0.5 DBU/hour` claim, but frozen baseline 0.17 does not record that source in the dated source register. Its App state/cost entry also points to the state subsection rather than the precise current App-status subsection used by the README. This conflicts with the repository policy that external sources and refresh expectations be recorded centrally.

Required resolution:

- Add the official App compute-size page as a dated, time-sensitive source with the exact claim and a pre-run refresh trigger.
- Point status and charging semantics to the precise App-status section.
- Keep the README action-level links, but make the source register the canonical freshness ledger rather than relying on inline discovery.

## Contradiction and claim scan

No material contradiction was found across the frozen 0.17 author set and evidence on these product claims:

- the target remains a private Databricks App delivered through a Bundle;
- data and compute stay in the customer's Databricks environment;
- no external telemetry platform is required;
- P0 is process-liveness evidence only;
- the stopped App object and uploaded Bundle files can remain;
- the original run's missing pre-approval envelope remains a process nonconformance;
- the derived DBU estimate is not presented as an invoice or currency cost; and
- same-credential readback is not called independent assurance.

The source-register mismatch in `DOC-STYLE-P0-004` is a documentation-governance inconsistency, not evidence that the linked rate or status claim was false at review time.

## Rendered-site and accessibility disposition

The Markdown/source review is complete. Heading order, tables, code fences, link labels, warning placement, and text-only state communication were reviewed at source level.

Rendered-site validation is explicitly deferred because baseline 0.17 contains a planning index and source Markdown, not a complete built documentation site. This review does not claim rendered navigation quality, responsive layout, keyboard behavior, screen-reader behavior, contrast conformance, or WCAG conformance. Those checks remain required when the planned site and complete pages exist.

## Final verdict

**`CHANGES_REQUIRED`.** No Critical or High issue was found, and the P0 scope/readiness language is commendably precise. Baseline 0.17 nevertheless has two Medium documentation defects: its supported non-empty-workspace cleanup proof is not executable without operator invention, and its primary onboarding page exposes specialist future mechanics before the current runnable path. Resolve `DOC-STYLE-P0-001` and `DOC-STYLE-P0-002`, then re-review the affected task route and terminology. The two Low findings can be closed in the same focused pass.
