# Final Diataxis re-review: P0 planning baseline 0.20

- Planning author SHA-256: `e6a8d55f2b155916d52ac0c6aa6ce87941a3d8672f6dc4a0bfdb692a3fb7fd44`
- Evidence SHA-256: `670f54bdcef70e458adad590e959004e08f9aa5319855104299f5813c9419ed3`
- Run-record-template SHA-256: `6c61dc5091358cae2b5a531c6017bb012a4d0fc869edfd22fcaa2369bf5dca69`
- Review date: 2026-07-15
- Verdict: **PASS_WITH_FOLLOW_UP**
- Highest severity: **Low**, inherited D0 transition gate
- New findings: none
- Blocking findings: none
- Cloud/authentication activity: none

## Executive verdict

The baseline 0.20 security changes introduce no Diataxis or routing blocker. The current P0 how-to remains concise and task-oriented, and the new authentication information appears exactly where the operator needs it:

- secure-storage behavior is in the prerequisite step before mutation;
- the development-only token exception and its production contrast appear immediately before the run command;
- the evidence record preserves the historical credential-storage limitation without rewriting the old run; and
- the copy-only template now says plainly that approval is a human procedural gate the wrapper cannot inspect.

The prior Low finding for the transitional README/planning-index entry layer remains correctly deferred to D0. No rendered product-documentation site is claimed.

## Immutable inputs

```text
e6a8d55f2b155916d52ac0c6aa6ce87941a3d8672f6dc4a0bfdb692a3fb7fd44  planning author aggregate
670f54bdcef70e458adad590e959004e08f9aa5319855104299f5813c9419ed3  docs/evidence/p0-live-smoke-2026-07-15.md
6c61dc5091358cae2b5a531c6017bb012a4d0fc869edfd22fcaa2369bf5dca69  docs/templates/p0-smoke-run-record.md
```

This report is outside all three inputs.

## Focused Diataxis assessment

| Content | Reader need and placement | Result |
| --- | --- | --- |
| **What works now** | Establishes current capability and explicit exclusions before any procedure. | **Pass** — P0 cannot be mistaken for the product. |
| Workspace/tools step | Adds secure-storage and dedicated-workspace prerequisites before mutation. | **Pass** — safety belongs in the how-to at the decision point. |
| Private cost record step | Says the wrapper cannot inspect the external record and assigns authorization to operator/approver. | **Pass** — procedural versus mechanical enforcement is unambiguous. |
| Run-once step | Explains the token exception, safeguards, and production prohibition immediately before execution. | **Pass** — consequence is visible without sending the reader to reference material. |
| Expected health body | Remains adjacent to the action and says readiness is not evaluated. | **Pass** — checkpoint is concrete and scoped. |
| Final readback | Keeps verification and residual stopped-object consequence after execution. | **Pass** — task closes with observable evidence. |
| Evidence record | Separates cost and credential-storage process findings from the observed technical run. | **Pass** — dated evidence/reference, not an instruction or retroactive success claim. |
| Run-record template | Blank, synthetic-approved, and rejected forms support one how-to step. | **Pass** — task asset, not a competing tutorial or product feature. |
| Product plan | Gives the production bootstrap rule and removal gate for the P0 exception. | **Pass** — future contract is explicit and not injected into the current command. |

The wording is repeated only where reader context changes: operational warning in README, historical qualification in evidence, normative future contract in the product plan, and source caution in the register. This is purposeful cross-document reinforcement rather than mode confusion.

## Current task sequence

The route remains coherent:

1. understand the process-liveness-only scope;
2. verify dedicated workspace, exact tools, OAuth profile, and secure storage;
3. run local checks;
4. complete the external private approval and cost record;
5. understand cost, cleanup, token, and production-boundary consequences;
6. execute once;
7. compare the exact health response; and
8. retain the separate final stopped/zero-compute readback.

This is a real-work how-to. The future fixture tutorial remains separately planned as a safe, linear learning experience.

## Inherited Low D0 follow-up

The immediately preceding IA review's transitional-entry finding remains open and non-blocking:

- README still combines repository explanation with the sole current how-to.
- `docs/index.md` remains a planning-artifact list plus a route to that how-to.
- D0 still owns the status-first home, four Diataxis overview landing pages, audience/task routes, page registry, feature-state labels, and extraction of executable guidance into dedicated how-to pages.

With one executable P0 task this remains proportionate. It must be completed before the repository presents a full product-documentation site.

## Rendered-site and link decision

No accepted site configuration or `docs/tutorials`, `docs/how-to`, `docs/reference`, or `docs/explanation` directory exists. Rendered navigation, search, accessibility, responsive layout, and publication-artifact checks therefore remain correctly deferred until D0/D1 pages exist.

Current local entry targets were checked. README, index, evidence, template, plans, decision, source register, review index, and `AGENTS.md` exist; both index and evidence resolve to the current `README.md#run-the-p0-smoke` anchor.

## Diataxis sources

- [Diataxis overview](https://diataxis.fr/)
- [Tutorial versus how-to](https://diataxis.fr/tutorials-how-to/)
- [Reference guidance](https://diataxis.fr/reference/)
- [Complex hierarchies](https://diataxis.fr/complex-hierarchies/)

## New findings

None.

## Final disposition

**PASS_WITH_FOLLOW_UP** for planning `e6a8d55…`, evidence `670f54bd…`, and template `6c61dc50…`.

The security delta is placed correctly, preserves the P0-versus-production distinction, and creates no new IA blocker. The inherited Low D0 transition gate remains the only follow-up.
