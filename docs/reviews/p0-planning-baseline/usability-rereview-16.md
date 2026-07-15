# Final usability and onboarding re-review: planning baseline 0.19

- Date: 2026-07-15
- Reviewer: usability, onboarding, service-design, and accessibility specialist
- Verdict: **PASS_WITH_FOLLOW_UP**
- Open P0 usability blockers: none
- Open follow-up: `UX-P0-F03`, non-blocking for P0 and a hard P3 release gate
- Cloud/authentication activity: none

## Frozen review input

The reviewed planning-author set is exactly:

| Author file | SHA-256 |
| --- | --- |
| `AGENTS.md` | `b98568650936e701e988f743f6d2b8409f81f9483be7220a2194523b634408e3` |
| `README.md` | `0251659484a2727af01c7b4a799ad0e1efd01eeabdf01ed93164ba7050eb1224` |
| `docs/decisions/0001-private-app-bundle.md` | `7a1ca012882159f825a0d4aadb045fe365b35c4406f2b4b90ad4deb60202d231` |
| `docs/index.md` | `d90285d2236ab8734d4a67031ca8126097e37dacba74ee369d141d3904b332ca` |
| `docs/plans/documentation-plan.md` | `cdeb3c2dfa47f9990d61110328aa0229f3e2db59e2d1540fa5a184160a512cc9` |
| `docs/plans/product-plan.md` | `d2f0ea00f91d476b33ddd2fb52e452b94aa6d4335c2266487d44b0e7f4a413b6` |
| `docs/plans/review-process.md` | `d6e2c685ea71223a798c0d1b0f42ae6ecfa4870bec4a16d325d871ba7ac38734` |
| `docs/research/source-register.md` | `54bf6fedacd19282c5fbb7215e15cc939a2957a5bde4d97469895b303967876e` |

The globally sorted path-and-content aggregate reproduced exactly:

```text
703ae3cc1a86bee5d641c7fa478fbb49bdd88cd193f2aec36e61e9b00078eb5f
```

The following user-facing records were reviewed separately from the planning-author aggregate:

| Separate input | SHA-256 |
| --- | --- |
| `docs/evidence/p0-live-smoke-2026-07-15.md` | `d4904dc48dd8d803d258e58845da929418d5f11dbb55a805aa919c9fbb71c0c2` |
| `docs/templates/p0-smoke-run-record.md` | `172ae9825e5e7383526fd2879fe4deb29df3a24ac972c63fd37559484f4d310b` |

The supplied hashes reproduced before this report was written. This report is outside every frozen input and is the only file written by this review.

## Executive verdict

Baseline 0.19 passes the P0 planning usability gate. It resolves the final live-smoke documentation gaps without reopening any earlier product-journey finding:

- the P0 route now supports one clearly bounded environment—a dedicated smoke workspace with approved complete inventory visibility—instead of asking an operator to invent a safe procedure for a shared workspace;
- the wrapper inspects Apps, SQL warehouses, and clusters before Bundle validation or deployment and does not mutate an unrelated resource to make the precondition true;
- the private run-record template makes approval, accountable cleanup ownership, starting inventory, rate freshness, time/cost bounds, hard-ceiling risk, schedule state, cleanup result, and retained evidence explicit;
- the README shows the exact process-liveness response and exact final state assertions while continuing to deny dbt, artifact, product-data, and readiness claims; and
- the historical evidence retains its original approval-process finding and does not use later local guards or documentation improvements to rewrite the paid run as compliant.

No new Critical, High, Medium, or Low usability finding is opened. The verdict remains `PASS_WITH_FOLLOW_UP` only because the existing `UX-P0-F03` supported-workstation and signed-installer evidence gate correctly remains open until P3.

## P0 task-route assessment

### Entry and scope — Pass

The README now begins with the customer-local outcome, then immediately explains **What works now**. A first-time reader encounters the P0 limitation before any command: it is a FastAPI App packaging/liveness smoke and does not run dbt, ingest artifacts, read product data, or prove product readiness.

The numbered route is chronological and choice-free for its supported scope:

1. verify the dedicated workspace and local tools;
2. approve the private cost record;
3. run once; and
4. retain the final readback.

Deep migration, trust, deployment, controlled-action, and future dbt contracts are linked after this path instead of being prerequisites for finding it.

### Dedicated-workspace safety — Pass

The supported P0 topology is now explicit rather than inferred. The operator must have approved complete inventory visibility; only an optional existing stopped, unbound, `MEDIUM` `dbtobsb-smoke` App is permitted; visible warehouses and clusters must both be zero. A shared or partially visible workspace is unsupported.

The consequence is safe and understandable: failure means stop before Bundle validation/deployment, not “clean up” an unrelated resource. Both README and wrapper say never to stop or delete unrelated resources to make the check pass. The final readback then requires exactly one stopped, unbound `MEDIUM` P0 App and zero warehouses/clusters, with all three commands returning exit code `0`.

### Approval, cost, and cleanup — Pass

The cost consequence appears before the live command and separates facts that users commonly conflate:

- published `MEDIUM` rate: `0.5 DBU/hour`;
- ten-minute cancellation deadline and planned `0.084 DBU` through that request;
- up to twenty more minutes of cleanup observation and a conservative `0.25 DBU` thirty-minute exposure calculation;
- no hard ceiling if stop fails;
- no schedule;
- one accountable cleanup owner who remains at the terminal; and
- success only after exact `STOPPED` readback.

The private template is usable as a two-phase record. Its blank form names every required control, including a non-repository `cleanup_owner_reference`. The synthetic approved/completed example shows the expected shape without a live identity or deployable locator. The rejected example makes missing approval, ownership, visibility, timing, and risk acceptance visibly non-authorizing. Policy-owned access, retention, identity, and audit decisions remain outside this repository.

### Result and evidence language — Pass

The exact six-field JSON body uses `alive`, `process_liveness`, `not_evaluated`, and `p0_smoke`. The surrounding copy states precisely what that response does and does not establish. It cannot reasonably be read as dbt execution, capture success, dependency readiness, authorization readiness, or product readiness.

The evidence keeps three assertions separate:

1. one historical technical liveness/log/stop result;
2. one historical pre-run cost-control process nonconformance; and
3. later local-test evidence for the size and dedicated-workspace guards.

It also labels the separate final CLI readback as the same operator/credential context, not an independent-human attestation. The corrected reproduction link now lands on the current README task route.

## Prior finding disposition

| Finding | Baseline 0.19 disposition |
| --- | --- |
| `UX-P0-001` through `UX-P0-003` | **RESOLVED — NO REGRESSION.** One signed entry point, explicit actor modes, and distinct readiness outcomes remain intact. |
| `UX-P0-004` | **RESOLVED_AT_CONTRACT.** Complete-page/process WCAG 2.2 AA, keyboard, screen-reader, zoom/reflow, status, error, and non-color validation remain required before conformance is claimed. |
| `UX-P0-005` and `UX-P0-006` | **RESOLVED — NO REGRESSION.** Operation/Problem surfaces and representative-role task/time gates remain explicit. |
| `UX-P0-F01` and `UX-P0-F02` | **RESOLVED_AT_CONTRACT.** Bounded cost/cleanup evidence and distinct stop/remove/retain/delete consequences remain required. The P0 smoke now demonstrates the applicable runbook controls without pretending to satisfy future product-lifecycle evidence. |
| `UX-P0-007` through `UX-P0-013` | **RESOLVED — NO REGRESSION.** CLI scope, fixed attended mutation, two-account handoff, complete combined route, roster ownership, phase/time/source semantics, and capability-based recovery remain coherent. |
| `UX-P0-F03` | **OPEN_NONBLOCKING_P0_HARD_P3_GATE.** No production signed-installer asset or supported workstation matrix has been proven yet. |
| `UX-P0-F04` through `UX-P0-F06` | **RESOLVED_AT_CONTRACT — NO REGRESSION.** Scoped inventories, severity gates, and immutable action/approval summaries remain present. |
| `UX-P0-F07` | **RESOLVED.** The pre-command cost envelope now has precise cancellation, planned-usage, successful-stop, unbounded-failure, ownership, schedule, final-state, and private-record semantics. |
| `UX-P0-F08` | **RESOLVED.** The evidence says separate same-context readback and does not claim independent-human assurance. |

## `UX-P0-F03` hard P3 gate

**Disposition: `OPEN_NONBLOCKING_P0_HARD_P3_GATE — NO REGRESSION`.**

Baseline 0.19 continues to state that exact supported OS and architecture are P3 release facts, not P0 assumptions. It allows support claims only after fixtures and staging qualification and retains a **Before P3 release** decision for the installer OS/architecture matrix.

Before any installer/platform combination is described as supported, P3 must still publish and prove:

- exact operating-system versions and architectures;
- signed wrapper and embedded dependency asset names, signatures/checksums, and verification steps;
- native secure-store behavior and fail-before-mutation handling when it is unavailable;
- one-account combined operation with truthful non-independence flags;
- two-account separated operation on one supported workstation, including system-owned spool ACLs, atomicity, account/session release, restart/reboot resume, and removal;
- explicit rejection of same-account separation, separate-workstation transfer, a third reviewer, and a non-account-administrator verifier; and
- representative non-author install, recovery, upgrade, stop, retain/delete, uninstall, and zero-residue evidence with zero safety-critical errors.

The README and P0 evidence claim only an early stopped-by-default App smoke. They do not advertise a signed installer, production workstation, complete combined/separated installation, or Marketplace support. P0 therefore neither closes nor violates `UX-P0-F03`.

## Secret safety and source-level accessibility

- Executable examples contain placeholders rather than a real host, profile, user, token, or platform ID.
- The wrapper invocation prohibits tokens and client secrets.
- Real approval, operator, workspace, and evidence references are explicitly confined to a policy-approved private system.
- The template examples are synthetic and include no deployable credential or live locator.
- The evidence contains no workspace/account/user/App/service-principal identifier, credential, signed URL, raw customer log, or customer payload.
- The task uses ordered headings, descriptive links, labeled tables, fenced command/JSON examples, and plain-text success/failure semantics.
- Cancellation is keyboard-operable and named in text; no meaning relies on color, image, pointer movement, animation, or a memorized identifier.

This is source-level Markdown acceptance, not rendered-site WCAG conformance. Full rendered-page and complete-process checks remain correctly deferred until those surfaces exist.

## Local validation

The README's complete local sequence passed against the frozen implementation:

```text
uv sync --project app --locked --extra dev
Resolved 31 packages
Checked 30 packages

uv run --project app --extra dev pytest
12 passed in 3.52s

uv run --project app --extra dev ruff check app/dbtobsb_app app/tests
All checks passed!

uv run --project app --extra dev ruff format --check app/dbtobsb_app app/tests
3 files already formatted

uv run --project app --extra dev ty check app/dbtobsb_app app/tests
All checks passed!

bash -n scripts/smoke_databricks_app.sh
# exit 0

shellcheck scripts/smoke_databricks_app.sh
# exit 0
```

The tests use fake local executables for wrapper behavior. This review made no Azure, Databricks, authentication, App, Job, SQL, warehouse, cluster, Unity Catalog, or other cloud call and started no paid compute.

## Final disposition

**`PASS_WITH_FOLLOW_UP`.** Baseline 0.19 has no open P0 usability blocker and introduces no usability, onboarding, secret-handling, evidence-language, or source-accessibility regression. `UX-P0-F07` and `UX-P0-F08` remain resolved, and the new dedicated-workspace route plus private record remove the remaining operator-invention gaps. `UX-P0-F03` remains the sole usability follow-up and must close before a P3 installer/workstation combination is published as supported.
