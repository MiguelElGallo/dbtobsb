# Focused usability and onboarding re-review: planning baseline 0.17

- Date: 2026-07-15
- Reviewer: usability, onboarding, and accessibility specialist
- Verdict: **PASS_WITH_FOLLOW_UP**
- Cloud/authentication activity: none

## Frozen review input

The planning author set is exactly:

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

The globally sorted path-and-content aggregate is:

```text
83be89fd59fe16c023c7e4b7fb6f336d6ab27d44c7c0ebf03a7d862a2a43ce97
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

The corrected live-smoke evidence was reviewed separately:

| Evidence file | SHA-256 |
| --- | --- |
| `docs/evidence/p0-live-smoke-2026-07-15.md` | `6d1a6e133ce98b01e976a12ea8837733dd0cd1198dddb5ad3225ff0b04f8073a` |

All supplied hashes reproduced exactly before and after the focused review. No author, evidence, or implementation file was edited by this reviewer.

## Current primary-source check

The two time-sensitive cost claims were verified against the linked official Azure Databricks documentation on 2026-07-15:

- [Configure compute resources for a Databricks app](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/compute-size) lists `Medium` at `0.5 DBU` per hour and says `Medium` is the default when no size is specified.
- [Key concepts in Databricks Apps: App status](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts#app-status) says running Apps incur compute charges and stopped Apps are inaccessible and do not incur costs.

The README's `0.084 DBU` ceiling is arithmetically conservative: `0.5 × 10 / 60 = 0.083333…`, rounded upward to three decimal places.

## Focused verdict

`UX-P0-F07` and `UX-P0-F08` are fully resolved. Baseline 0.17 now implements the cost and evidence language already required by its planning contract:

- the cost envelope appears before the executable command;
- the operator must copy it to an approved private run record and add approver, cleanup owner, start time, and cancellation time;
- `MEDIUM`, `0.5 DBU/hour`, ten minutes, and the conservative `0.084 DBU` ceiling are explicit;
- schedule state, cancellation action/deadline, cleanup owner, required final state, residual stopped object, and final readback commands are explicit;
- the evidence preserves the historic process nonconformance rather than retroactively claiming the original run was approved correctly;
- the post-run bound is labeled derived and conservative, not an invoice or billing reconciliation; and
- the final readback is accurately described as a separate CLI observation in the same operator/credential context, not independent-human assurance.

No new usability, onboarding, secret-handling, accessibility, or documentation-consistency finding is opened.

The verdict remains `PASS_WITH_FOLLOW_UP` only because `UX-P0-F03` is intentionally still open as a hard P3 release gate. It is not a P0 blocker and is not closed by this App smoke.

## `UX-P0-F07` resolution

**Disposition: `RESOLVED`.**

### Pre-command cost envelope

`README.md:54-70` places a titled **Approve the cost envelope first** section before the executable command and says not to execute until the record is privately approved and completed. The table covers every acceptance item from re-review 14:

| Required fact | Baseline 0.17 treatment |
| --- | --- |
| Mutation/residue | The text says a stopped App object and uploaded Bundle files remain after success. |
| App size | Fixed to `MEDIUM`; another live size is refused. |
| Published rate | `0.5 DBU/hour`, linked to the official size table. |
| Maximum interval | Ten minutes after wrapper invocation. |
| Conservative maximum | `0.084 DBU`, with the formula shown. |
| Schedule state | None; the Bundle creates no schedule. |
| Cancellation deadline | Recorded start time plus ten minutes. |
| Cancellation action | `Ctrl-C`, followed by cleanup verification/recovery. |
| Cleanup owner | Named person who remains at the terminal for the full run. |
| Required final state | App `STOPPED`; zero non-stopped Apps, warehouses, and clusters. |
| Continuing-cost meaning | Running is charged; stopped is inaccessible and has no App-compute cost. |

The safety consequence now precedes the action. A user cannot read naturally from prerequisites to the command without first passing the cost envelope.

### Separate final state proof

`README.md:81-90` requires the cleanup owner to retain a separate post-wrapper readback for Apps, warehouses, and clusters. It also handles a non-empty workspace honestly: replace total-zero checks with a reviewed, paginated before/after inventory and never stop or delete unrelated resources.

This separates three facts that were previously easy to conflate:

1. the maximum cost/duration approved before start;
2. the billable or cost-eligible interval that actually occurred; and
3. the final state that determines whether cost can continue.

### Historic evidence honesty

`docs/evidence/p0-live-smoke-2026-07-15.md:20-26` explicitly says the original run omitted the required numeric envelope and that later `STOPPED` evidence does not cure that process nonconformance. It records:

- a remote object-create-to-final-`STOPPED` window of 2 minutes 52 seconds;
- `MEDIUM` compute;
- a conservative upper bound below `0.024 DBU` at the current rate;
- that the actual billable `ACTIVE` interval was only a subset of that window;
- that this is derived, not an invoice or billing-table reconciliation; and
- that no second paid run was performed merely to manufacture compliant historical evidence.

The arithmetic is correct: `0.5 × 172 / 3600 = 0.023888… DBU`, which is below `0.024 DBU`.

The evidence result is now **Technical PASS with a cost-control process finding**, so it cannot be mistaken for a complete process pass.

## `UX-P0-F08` resolution

**Disposition: `RESOLVED`.**

The heading is now **Separate post-run state readback**, not **Independent final inventory**. The first sentence states that another read-only CLI call used the same operator and credential context and was not an independent-human attestation.

This wording aligns with the rest of the product contract, which treats independent observation, separate people, distinct OS accounts, and administrator-attested non-independent evidence as security-significant facts. The record no longer implies a person, credential, or organizational boundary it did not establish.

## Secret-safe and accessible onboarding disposition

### Secret and Personal Data handling — Pass

- The executable example contains only visibly synthetic placeholders.
- The README prohibits token and client-secret use.
- Real profile, host, user, approver, owner, and timestamps belong only in the approved private run record, not the repository.
- The evidence contains no real workspace URL, account/workspace ID, user identity, App ID, service-principal ID, token, signed URL, or raw customer log.
- The cost record uses DBUs, not an invented currency amount.
- The final readback commands contain no token, raw ID, or destructive action.

### Accessibility and task order — Pass at source level

- The safety heading and cost table occur before the action they govern.
- Table headers make each control/value pair explicit and linear.
- The cancellation action is available from the keyboard and has a text label.
- No state depends on color, animation, image, pointer gesture, or memory alone.
- Links have descriptive labels; code fences declare their language.
- Failure/recovery text uses direct consequence and action language.
- The user has one chronological route: approve, start timer, run, interrupt if required, observe wrapper stop verification, then perform the separate readback.

This is source-level Markdown acceptance, not a rendered-site WCAG conformance claim.

## Contradiction scan

No material contradiction remains across the frozen author set and evidence:

- baseline labels are consistently 0.17;
- P0 remains process-liveness evidence, not dbt execution, artifact ingestion, dependency readiness, or product readiness;
- running-cost and stopped-cost language matches the official App status documentation;
- the residual stopped object and uploaded Bundle files remain disclosed;
- the historical missing envelope is preserved as a finding rather than rewritten as compliant;
- the derived DBU estimate is distinct from billing reconciliation and currency; and
- same-context final readback is not mislabeled independent assurance.

## `UX-P0-F03` hard P3 gate

**Disposition: `OPEN_NONBLOCKING_P0_HARD_P3_GATE — NO REGRESSION`.**

The gate remains explicit:

- `docs/decisions/0001-private-app-bundle.md:82` says exact supported OS/architecture remains a P3 release gate.
- `docs/decisions/0001-private-app-bundle.md:88` permits a support claim only after fixtures and staging validation pass.
- `docs/plans/product-plan.md:842-856` retains clean-account/workstation non-author testing and the zero-safety-critical-error gate.
- `docs/plans/product-plan.md:912` keeps the installer OS/architecture matrix as a **Before P3 release** decision requiring signed assets/checksums, clean combined/separated operation, secure profile/storage behavior, spool controls, and explicit unsupported topology messages.

The P0 README and evidence claim only a reviewed App-shell smoke, not a supported signed installer or production workstation matrix. P3 must still close the complete acceptance list recorded in re-review 14 before any platform combination is described as supported.

## Validation performed

The README's local sequence passed on the frozen files:

```text
uv sync --project app --locked --extra dev
Resolved 31 packages
Checked 30 packages

uv run --project app --extra dev pytest
11 passed in 3.50s

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

No Databricks, Azure, authentication, or other cloud call was made.

## Final disposition

**`PASS_WITH_FOLLOW_UP`.**

Baseline 0.17 resolves `UX-P0-F07` and `UX-P0-F08` fully and introduces no new P0 usability or accessibility finding. The historic run remains honestly nonconforming on its pre-run process while retaining a technically successful, sanitized, bounded, and final-stopped result.

The only follow-up is the already-known `UX-P0-F03` hard P3 support gate. It remains correctly open and does not block P0 planning acceptance.
