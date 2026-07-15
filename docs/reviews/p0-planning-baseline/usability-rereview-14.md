# Usability and onboarding re-review: planning baseline 0.16

- Date: 2026-07-15
- Reviewer: usability, onboarding, and accessibility specialist
- Verdict: **CHANGES_REQUIRED**
- Cloud/authentication activity: none

## Frozen review input

The planning author set is exactly:

| Author file | SHA-256 |
| --- | --- |
| `AGENTS.md` | `b98568650936e701e988f743f6d2b8409f81f9483be7220a2194523b634408e3` |
| `README.md` | `c7c36c8ab2557bb242a1accc2e110796c4c176a764430c2f9e6ae33dd6ece185` |
| `docs/decisions/0001-private-app-bundle.md` | `38ebb5537fd41f6261fcce2ae4e996af3e41e23d84e0d0995d38bbc43c89aa47` |
| `docs/index.md` | `d0de65579c3ad3d7e56b272eed9611db758bdb95c0573066114ea72573bed792` |
| `docs/plans/documentation-plan.md` | `7ddc57ed11ae8e087eb47d9f43e8aebc466886174833d9e1c7a191e5c6e410d4` |
| `docs/plans/product-plan.md` | `fd254b8e9b2d50dc3028d05a6ca879845b68965e77a7ebbe71a811ac84083737` |
| `docs/plans/review-process.md` | `d6e2c685ea71223a798c0d1b0f42ae6ecfa4870bec4a16d325d871ba7ac38734` |
| `docs/research/source-register.md` | `0256e0b6c8e91c49b94f1fae3015a397d6b8c78954b4b9f7c796d143a0c69afc` |

The globally sorted path-and-content aggregate is:

```text
3d463e4e578ac5c24b0f0723b9830448559494f765713ac3caba4c5d4f480b9a
```

Reproduction command, run from the repository root:

```sh
author_files=$(
  printf '%s\n' README.md AGENTS.md docs/index.md
  find docs/decisions docs/plans docs/research -type f -name '*.md' -print |
    LC_ALL=C sort
)
printf '%s\n' "$author_files" |
  LC_ALL=C sort |
  while IFS= read -r file; do shasum -a 256 "$file"; done |
  shasum -a 256
```

The live-smoke evidence was inspected separately and was not folded into the planning-author aggregate:

| Evidence file | SHA-256 |
| --- | --- |
| `docs/evidence/p0-live-smoke-2026-07-15.md` | `9d46184b907c15038ecec919a4707075ad59404a035bc7628b4be5166e747326` |

Both supplied hashes reproduced exactly during the frozen 0.16 review. The shared author and evidence files advanced to a later candidate after the findings were delivered; this report intentionally preserves the 0.16 input and verdict. No author, evidence, or implementation file was edited by this reviewer.

## Executive verdict

Baseline 0.16 retains the coherent product journey, actor boundaries, accessibility contract, and hard P3 supported-workstation gate approved at the preceding planning review. The new README and live-smoke record are concise, discoverable, secret-safe, and unusually honest about the narrow result: P0 proved App process liveness only and left one stopped App object plus uploaded Bundle files.

The baseline cannot receive final usability approval yet because the executable live-smoke runbook and its evidence do not satisfy the planning baseline's own pre-run cost-envelope contract. The plan requires App size, DBU/hour, maximum elapsed intervals, expected DBUs, schedule state, cancellation deadline, stop/cleanup owner, final inventory command, and stopped-App charge meaning before a live test starts. The README presents the mutating command first and only describes cleanup and residue afterward. The evidence proves the final stopped state but does not record the approved bound or distinguish the billable `ACTIVE` interval from the final no-running-compute state.

This is a Medium documentation and operator-safety defect, not a failure of the wrapper's stop behavior. Final `STOPPED` evidence answers “what is running now”; it does not answer “what cost and maximum duration did the operator approve before starting.”

One additional Low wording issue remains: **Independent final inventory** is ambiguous in a product whose independence flags are security-significant. The record proves a separate read-only check after the wrapper; it does not state that a different human, credential, or organizationally independent reviewer performed it.

## Verification performed

### README command verification

The README's complete local verification sequence was executed exactly as written:

```text
uv sync --project app --locked --extra dev
Resolved 31 packages
Checked 30 packages

uv run --project app --extra dev pytest
10 passed in 3.47s

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

No live-smoke command, Databricks command, Azure command, authentication check, or other cloud operation was executed by this review.

### Secret and Personal Data inspection

The live evidence contains no workspace URL, account/workspace identifier, user name or email, OAuth token, bearer header, client secret, signed URL, raw customer log, or raw platform response. The README uses visibly synthetic placeholders and explicitly tells the operator never to pass a token/client secret and never to copy runtime values into the repository or review record.

The authenticated health example is an allowlisted six-field response. It contains no workspace, actor, resource, path, artifact, or customer-data value.

### Source-level accessibility inspection

- Heading levels are ordered and descriptive.
- Links use task- or document-oriented labels rather than bare URLs.
- Shell and JSON examples declare their language.
- The final-inventory table has explicit column headers.
- Meaning does not depend on color, position, animation, or an image.
- The runbook is non-interactive and does not create a memorization, transcription, pointer, or timing task.
- The health response uses stable machine-readable fields in addition to prose.

This is a source-level Markdown review. It does not claim rendered-site WCAG conformance; the baseline correctly reserves complete rendered-page/process testing for later documentation and UI stages.

## `UX-P0-F03` hard P3 gate

**Disposition: `OPEN_NONBLOCKING_P0_HARD_P3_GATE — NO REGRESSION`.**

The gate remains explicit and cannot be mistaken for a current support claim:

- `docs/decisions/0001-private-app-bundle.md:82` says the exact supported OS/architecture remains a P3 release gate and rejects same-login and improvised cross-workstation separation.
- `docs/decisions/0001-private-app-bundle.md:88` labels the toolchain a candidate and permits a support claim only after fixtures and staging validation pass.
- `docs/plans/product-plan.md:842-856` requires non-author clean-account/workstation tasks, zero safety-critical errors, explicit supported/unsupported topology comprehension, and owners/target parts for every lower-severity finding.
- `docs/plans/product-plan.md:912` makes the private-alpha installer OS/architecture matrix a **Before P3 release** decision backed by signed asset names, checksum commands, combined and separated clean-workstation evidence, secure-profile behavior, spool ACL/atomicity/session release, and explicit unsupported-topology messages.

The README claims only that the reviewed P0 App shell can be packaged and smoke-tested. It does not claim that the future signed product installer, either complete actor mode, or any production workstation matrix is supported. The sanitized P0 evidence therefore does not close `UX-P0-F03`.

P3 must still publish and test before any installer/platform combination is described as supported:

- exact supported operating-system versions and architectures;
- signed wrapper and embedded dependency asset names, signatures, checksums, and verification workflow;
- native secure-store behavior and non-mutating unsupported outcomes;
- one-account combined operation;
- two-account separated operation, system spool ACL/atomicity/session-release/restart/removal behavior;
- explicit rejection of same-account separation, separate-workstation transfer, a third reviewer, and a non-account-admin verifier; and
- real non-author stage/final approvals, recovery, cleanup, uninstall, and zero-residue evidence.

## New README and evidence assessment

### Clarity and onboarding — Pass with cost-order correction required

The onboarding route is easy to find from both `README.md` and `docs/index.md`. It gives local checks, exact live prerequisites, a single command, expected verification behavior, the allowed residual stopped object, and a direct link to sanitized evidence.

The P0 limitation is repeated consistently:

- it is App process liveness, not product readiness;
- it does not run dbt;
- it does not ingest artifacts or read product data; and
- the evidence does not prove dependency readiness or observability.

The safety/cost consequence must move before the executable command and become complete enough to satisfy the cost contract described below.

### Cost and final-state honesty — Changes required

The final-state statements are internally consistent and useful:

- the App was observed `ACTIVE` only for the smoke interval;
- cleanup read back `STOPPED`;
- a separate read-only inventory found zero non-stopped Apps, zero bindings, zero warehouses, zero clusters, and no pending deployment;
- the stopped App object and uploaded Bundle files remain; and
- neither document claims that the App object was deleted.

What is missing is the other half of cost truth: the approved paid interval before start and the cost already eligible to be billed while the App was `ACTIVE`. Neither a final zero-running inventory nor a stopped object proves zero incurred cost.

### Secret-safe copy — Pass

The README contains only placeholders for profile, host, and expected user, prohibits token/client-secret use, and points to a wrapper that validates the selected identity boundary. The evidence deliberately omits every real value. No command invites a token, raw platform identifier, SQL, log, or artifact to be pasted into Markdown.

### Contradiction scan — One material contradiction

Baseline/version labels are coherent at 0.16. The ADR, product plan, documentation plan, contributor agreement, index, README, and evidence agree on the App/Bundle starting point, customer-local boundary, P0 liveness-only result, no dbt/artifact readiness, stopped residual App object, and future P3 installer gate.

The material contradiction is between `docs/plans/product-plan.md:866-870` and `README.md:52-61` plus the evidence record:

- the plan requires a specific cost envelope before each live test and before first `bundle run`;
- the runbook omits that envelope and places its partial consequence statement after the command; and
- the evidence proves cleanup but cannot prove that the required bound was disclosed and approved before start.

The plan's prohibition on cloud use during planning/static validation is not contradicted by this review. The repository distinguishes the planning author set from the separately recorded P0 implementation smoke, and this re-review made no cloud call.

## Findings

### `UX-P0-F07` — Live runbook and evidence omit the required pre-run cost envelope

- Severity: **Medium**
- Status: **OPEN — CHANGES_REQUIRED**
- Evidence:
  - `docs/plans/product-plan.md:866` requires App size, DBU/hour, maximum stage/safe-boot intervals, stop owner, and the stopped-App no-App-compute-charge fact before first `bundle run`.
  - `docs/plans/product-plan.md:868` requires maximum elapsed minutes, expected App/warehouse DBUs, warehouse auto-stop, schedule state, cancellation deadline, cleanup owner, and final inventory command before each live test.
  - `AGENTS.md:70` requires every live test to declare its cost boundary and end with stopped/absent inventory.
  - `README.md:52-59` gives prerequisites and the immediately executable live command without that envelope.
  - `README.md:61` gives only the start/stop/residual-object consequence after the command.
  - `docs/evidence/p0-live-smoke-2026-07-15.md:22-40` records `ACTIVE` and later `STOPPED`, but not the approved maximum, App size/rate, expected DBUs, cancellation deadline, cleanup owner, or elapsed active interval.
- User impact: an operator can start personally funded App compute without first seeing or approving an upper bound and accountable cleanup path. A later `STOPPED` observation can then be misread as “no cost” rather than “no continuing App-compute cost.”
- Required change:
  1. Put a short mutation/residue/cost panel immediately before the live command.
  2. State that the command creates or updates a private App, briefly starts billable App compute, and may retain one stopped App object and uploaded Bundle files.
  3. State App size and DBU/hour, or explicitly label either value unavailable and explain how the operator must obtain/approve it before continuing.
  4. Give the maximum elapsed and active-compute interval, expected App DBUs separately from currency, cancellation/stop deadline, cleanup owner, schedule state, and exact final-inventory action.
  5. State that successful completion requires verified `STOPPED`, while failed/unverified cleanup may continue to incur cost and requires the printed recovery commands.
  6. Amend the dated evidence with the bound that was actually approved, measured elapsed/active interval if available, and an explicit statement that the `ACTIVE` interval was billable or cost-eligible even though the final state was stopped. If a value was not captured, say `not recorded`; do not reconstruct false precision.
- Owner and target: documentation owner plus P0 smoke owner; close before the next live reproduction is offered as a runbook or the evidence is used as proof of the baseline cost contract.

### `UX-P0-F08` — “Independent final inventory” overstates unspecified independence

- Severity: **Low**
- Status: **OPEN**
- Evidence: `docs/evidence/p0-live-smoke-2026-07-15.md:44-46` calls the section **Independent final inventory**, then establishes only that a separate read-only inventory ran after the wrapper. It does not identify a different human, credential, OS account, reviewer, or organizational boundary.
- User impact: a regulated reader may interpret “independent” as independent-human or independent-credential assurance, conflicting with the plan's strict use of independence flags and non-independent administrator attestations.
- Required change: rename the section **Separate post-run inventory** or state explicitly “independent of the wrapper process; not an independent-human review.” If a different actor actually performed it, record the non-sensitive actor-role boundary without adding identity data.
- Owner and target: evidence/documentation owner; resolve with `UX-P0-F07` before the record is reused as audit or customer evidence.

## Author-file outcome

| Author file or set | Outcome | Usability conclusion |
| --- | --- | --- |
| `README.md` | `CHANGES_REQUIRED` | Clear and runnable, but the mutating command precedes and omits the required cost envelope. |
| `AGENTS.md` | `PASS` | The live-test cost, cleanup, source, and review rules remain explicit. |
| `docs/index.md` | `PASS` | Provides a short, coherent route to the runbook and evidence without overstating P0 readiness. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | Keeps the paid-runtime consequence and hard supported-workstation P3 gate explicit. |
| `docs/plans/product-plan.md` | `PASS` | The cost contract and P3 support gate are clear; the new runbook, not the plan, fails to implement one of those documentation requirements. |
| `docs/plans/review-process.md` | `PASS` | Preserves independent specialist and documentation review gates. |
| `docs/plans/documentation-plan.md` | `PASS` | Diataxis structure, progressive disclosure, accessibility, real-evidence, and secret-safe capture requirements remain coherent. |
| `docs/research/source-register.md` | `PASS` | Retains the primary platform, dbt, Diataxis, accessibility, security, and usability sources and their cautions. |
| Separate P0 live evidence | `CHANGES_REQUIRED` | Scope and final state are clear and sanitized; cost-envelope provenance and independence wording need correction. |

## Final disposition

**`CHANGES_REQUIRED`.**

Baseline 0.16 remains a strong and testable planning contract, and `UX-P0-F03` remains the correct hard P3 release gate. The new P0 smoke documentation proves an important bounded implementation milestone without claiming dbt or product readiness. It is not yet consistent with the baseline's own live-test cost discipline, and its independence wording is too broad for a regulated evidence record.

Close `UX-P0-F07` and `UX-P0-F08`, freeze a new author/evidence hash, rerun the README's local checks, and request a focused usability re-review. No cloud resource was created, started, stopped, queried, changed, or deleted by this review.
