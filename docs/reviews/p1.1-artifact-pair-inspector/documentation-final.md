# P1.1 final documentation consistency and reader-journey audit

## Review record

| Field | Value |
| --- | --- |
| Reviewed commit | `2b76abbd565271b30f37fdb1e3f00d76185e8dc4` |
| Commit tree | `24d4fb122ee6a167bf2ae529034ee17013b30024` |
| Commit parent | `7ce722cddfed42f1e96741bb07b6cd8762127f22` |
| Commit subject | `docs: record p1.1 documentation closure reviews` |
| Review date | 2026-07-15 |
| Review role | Independent final cross-document peer reviewer |
| Verdict | **CHANGES_REQUIRED** |

The product-facing P1.1 documentation passes this audit: all landing routes reach the implemented journey, the Diátaxis modes stay distinct, exact outputs reproduce, terminology and current-versus-future boundaries agree, custody guidance is action-oriented and complete, and the six latest specialist verdicts do not contradict one another. One source-level traceability defect blocks final resolution: the repository's authoritative P1.1 review index omits the three documentation closure reports added by this commit.

## Exact scope

### Reader-route and contract source

The source-route set is this exact path-sorted 16-file list:

1. `README.md`
2. `capture/README.md`
3. `docs/developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md`
4. `docs/developers/explanation/raw-artifact-custody.md`
5. `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md`
6. `docs/developers/how-to/handle-raw-dbt-artifacts-safely.md`
7. `docs/developers/index.md`
8. `docs/developers/reference/cli-report-and-exit-codes.md`
9. `docs/developers/reference/python-api.md`
10. `docs/developers/tutorials/inspect-an-artifact-pair.md`
11. `docs/evidence/p1.1-local-artifact-pair-2026-07-15.md`
12. `docs/index.md`
13. `docs/plans/documentation-plan.md`
14. `docs/plans/product-plan.md`
15. `docs/research/source-register.md`
16. `docs/reviews/README.md`

### Latest specialist verdicts

The latest-review set is:

1. `docs/reviews/p1.1-artifact-pair-inspector/databricks-rereview-3.md`
2. `docs/reviews/p1.1-artifact-pair-inspector/dbt-core-rereview-3.md`
3. `docs/reviews/p1.1-artifact-pair-inspector/documentation-ia-rereview-2.md`
4. `docs/reviews/p1.1-artifact-pair-inspector/documentation-security-rereview-2.md`
5. `docs/reviews/p1.1-artifact-pair-inspector/documentation-style-rereview-2.md`
6. `docs/reviews/p1.1-artifact-pair-inspector/usability-rereview-3.md`

Earlier reports were retained as the immutable finding trail but were not re-adjudicated. Their resolution was checked through the latest report for each lens.

### Executable corroboration

The validation set is:

1. `capture/tests/test_documentation.py`
2. `scripts/check_capture.sh`
3. `scripts/check_markdown_links.py`

Relevant public implementation behavior was corroborated through the full capture gate and exact commands; no source file was edited. Cloud, Databricks authentication, dbt execution, and paid compute were outside this local documentation audit.

## Immutable hashes

Each aggregate is SHA-256 over the literal path-ordered `shasum -a 256` record stream for its exact set above.

| Frozen input | SHA-256 |
| --- | --- |
| 16-file source-route aggregate | `4bd4ae3e459fba0e6694042d20b73bc17a1a23abe558e3e9e885c3ef6f2828f8` |
| Six-file latest-review aggregate | `593ac94d6fae6e113c1a0a23db9c0e3243b1206a82965a660495b9191e0667b0` |
| Three-file validation aggregate | `3724d13ed0f1ef3021f3ecd9e3b89bfe111f5f746dc758f8c39051f04727f2c2` |

Critical individual hashes are:

| File | SHA-256 |
| --- | --- |
| `README.md` | `0be609fbbb0239d7dbb1142dcd630fa94f0a7b13ba9af7940b65f08d9d48c5cf` |
| `capture/README.md` | `d664454aa140415fc822398a217d62bb57cffc41c647fee46da98213fa0e6e19` |
| `docs/index.md` | `2b6fece0e8ca96e2407e14f1bd8e5df90dbad39495feaefbd74914541bbc7fe2` |
| `docs/developers/index.md` | `8867bd6d28b38d7c22bfe1bb2c2affead9b737f64311b8c7d2c519544d6c0ceb` |
| `docs/evidence/p1.1-local-artifact-pair-2026-07-15.md` | `670dc2b74185492ea1de9e06fc0d64ee7c1fb3bef3b402ceeee3e4496e1125e9` |
| `docs/reviews/README.md` | `af0f8b9cc8b717689f9b9c2ba2217db6df56c7f355508e1e2198b3b9cb3cb382` |
| `documentation-ia-rereview-2.md` | `0ac0ef4e9e29bbc4ca6f3005d630b836934e28ab85cdc159cf2712b668cd7c44` |
| `documentation-security-rereview-2.md` | `914af86b68d7cf578f7f8a532c35fdeca2b74e23b733d295d8c850bbdbd6454a` |
| `documentation-style-rereview-2.md` | `d0d531b5724ef641279730280745b7a8a75a4fe50bb145f502f0af88e45d5791` |
| `capture/tests/test_documentation.py` | `3653fe330b9dd660f959803c98337053980c9ea24cd30be904025f01ff90b8f9` |
| `scripts/check_capture.sh` | `92656cda84b66dd76338cec050c35e632ae50de015bda89e474d28a74854b911` |
| `scripts/check_markdown_links.py` | `aa904ffdd5540d2604b840c42d8d04660c03c57e0d1f818355fc524dbd40b0c0` |

## Checks executed

All checks ran in a detached worktree at the reviewed commit with dedicated uv cache and environment paths.

| Check | Result |
| --- | --- |
| `scripts/check_capture.sh` | Passed; ended in `DBTOBSB_CAPTURE_CHECK_PASSED` |
| Capture test suite | 94 passed |
| Documentation contract tests | Four of four passed |
| Current immutable link check at `2b76abb…` | 120 tracked Markdown files, 188 local links, 53 fragments, zero errors |
| Evidence-revision link replay at `80d0c0a…` | Reproduced the recorded 117 files, 160 local links, 48 fragments, zero errors |
| Ruff check and format, plus ty | Passed |
| Schema and fixture regeneration | Passed without diff |
| Seven-package runtime-only path, API example, wheel, and installed CLI | Passed |
| `bash -n scripts/check_capture.sh` and `shellcheck scripts/check_capture.sh` | Passed |
| Scoped heading hierarchy | 16 files checked; one H1 per file and zero skipped levels |
| Landing-route graph | All eight implemented developer pages reachable; zero unreachable pages |
| Terminology scan | Eight scoped `Personal Data` uses; zero `PII` or expanded-PII uses |
| Production-source continuity | `capture/src` unchanged since the latest Databricks/dbt/usability closure commit |
| Documentation-source continuity | Reader-route source unchanged since the exact evidence revision |
| Detached worktree diff after checks | Empty |

### Exact output replay

The following published journeys were executed with stdout, stderr, and exit status checked against the page text:

| Journey | Result |
| --- | --- |
| Tutorial valid-success pair | Exit `0`, empty stderr, exact text output |
| Tutorial valid pair with dbt error | Exit `0`, empty stderr, exact compact JSON |
| Tutorial invalid invocation pair | Exit `10`, empty stderr, exact text output |
| Tutorial/Python-reference API example | Exit `0`, empty stderr, exact two-line output |
| CLI input-read failure | Exit `3`, empty stdout, exact four-line stderr |

## Cross-document reader-journey assessment

### Landing routes — PASS

The root README leads with the present P0/P1.1 implementation boundary, gives a short P1.1 success path, and sends detail to the tutorial and CLI contract. `capture/README.md` identifies the package outcome and routes first use, integration, and real-input custody. `docs/index.md` separates the planning index from the implemented P1.1 path. `docs/developers/index.md` then exposes outcome, recovery, contract, and explanation routes in reader language. A recursive link-graph check reached all eight implemented developer pages from those landing roots.

### Tutorial, how-to, reference, and explanation boundaries — PASS

The tutorial teaches through three fixture outcomes plus the Python first success. The two how-tos solve real tasks: recover invalid evidence and handle real raw artifacts. The two references remain contract-led; the complete Python example is a concise reference aid with executable anti-drift protection. The explanations develop the pair/outcome/capture model and custody reasoning without replacing the procedures. The information architecture matches the seven-row implemented-page registry in the documentation plan.

### FastAPI-style clarity — PASS

This pass did not duplicate the specialist style review. It checked the same high-value reader traits across page boundaries: outcome first, complete runnable code before interpretation, exact response adjacent to action, error meaning beside recovery, explicit types and limits, and progressive links to deeper material. The prior FastAPI-style `PASS` remains supported by the exact-output and navigation replay.

### Terminology and machine text — PASS

`manifest.json`, `run_results.json`, pair validity, native dbt outcome, capture state, `PAIR_VALID`, `PAIR_INVALID`, and `status_counts` keep stable meanings. `Personal Data` is used consistently. Exact CLI/API output and exit-channel claims matched execution. No page converts pair validity into dbt success or capture completeness.

### Current versus future product claims — PASS

The pages consistently say that P1.1 is local and offline only after dependency installation. They disclose the approved-index/mirror/cache requirement and the absence of a disconnected wheelhouse. They do not claim archive retrieval, structured logs, AttemptKey correlation, Databricks runtime qualification, observability-table writes, or capture-state classification. The workstation-local custody explanation explicitly refuses to treat P1.1 as proof of the target Databricks-local product boundary.

### Raw-artifact custody journey — PASS

Warnings in the root README, tutorial, diagnosis how-to, Python reference, and CLI reference direct readers to the action-oriented raw-handling how-to before real-file substitution. That how-to covers owner, approved host/storage, least privilege, all copies and backups, support payload, restricted-evidence transfer, retention, legal hold, deletion, and verification. The custody explanation separately describes sensitivity, transient parsing, safe-output limits, caller ownership, and the workstation-versus-Databricks boundary. The routes are bidirectional and the machine references preserve the same data-flow claims.

### Evidence traceability — PASS except for the review index finding below

The evidence record names source revision `80d0c0a…`; replay at that revision reproduced its exact link counts. The reader-route source and validation inputs are unchanged from that revision, while the reviewed commit adds only the three accepted documentation closure reports to parent `7ce722c…`. The current immutable link check also passes with the expected higher counts caused by those three new reports.

## Latest-verdict consistency

| Lens | Latest report | Verdict | Consistency result |
| --- | --- | --- | --- |
| Databricks platform/security | `databricks-rereview-3.md` | `PASS_WITH_FOLLOW_UP` | Consistent; present P1.1 accepted, later runtime/collector/release gates retained |
| dbt Core/artifact contract | `dbt-core-rereview-3.md` | `PASS_WITH_FOLLOW_UP` | Consistent; present pair contract accepted, later runtime/compatibility qualification retained |
| Usability/onboarding | `usability-rereview-3.md` | `PASS_WITH_FOLLOW_UP` | Consistent; present journeys accepted, rendered/distribution/real-runtime gates retained |
| Diátaxis information architecture | `documentation-ia-rereview-2.md` | `PASS_WITH_FOLLOW_UP` | All four source findings closed; rendered/publication gates retained, including the still-unfulfilled source-index publication action |
| Security/compliance documentation | `documentation-security-rereview-2.md` | `PASS` | Consistent; custody split and regulated-industry source contract accepted |
| FastAPI-style writing | `documentation-style-rereview-2.md` | `PASS` | Consistent; all three style findings closed with executable anti-drift checks |

No latest specialist report contains a current product-source blocker, and none permits production-capture or runtime-qualification claims. `PASS` and `PASS_WITH_FOLLOW_UP` are used consistently with the repository's rule that later product/rendered gates do not block the reviewed P1.1 slice. This final audit has a broader pre-resolution traceability criterion, which exposes the source-index defect below without contradicting the narrower specialist verdicts.

## Required finding

### DOCFINAL-P1.1-001 — The authoritative P1.1 review index omits three latest closure reports

**Severity:** Medium

**Affected source:** `docs/reviews/README.md:3-13`; missing routes to the three `*-rereview-2.md` documentation reports added by commit `2b76abb…`

`docs/index.md` sends reviewers to `docs/reviews/README.md`, whose opening contract says the latest reports listed there are authoritative. The P1.1 table lists only Databricks, dbt Core, and usability. It does not list the latest Diátaxis IA (`PASS_WITH_FOLLOW_UP`), security/compliance (`PASS`), or FastAPI-style (`PASS`) reports. A graph traversal from the review index confirms that none of those three files is reachable. The IA closure report itself records “Publish this accepted latest report from the review index” as an outstanding publication action.

This is not a rendered-site-only limitation: the missing authority routes are absent from Markdown source. An accountable resolver following the documented entry point cannot discover half of the latest P1.1 peer-review lenses, distinguish their accepted closure from earlier `CHANGES_REQUIRED` reports, or assemble the complete verdict set for a final resolution.

**Required change:** Add three P1.1 rows to `docs/reviews/README.md` with the exact latest report paths and verdicts:

- Diátaxis information architecture → `documentation-ia-rereview-2.md` → `PASS_WITH_FOLLOW_UP`;
- Security/compliance documentation → `documentation-security-rereview-2.md` → `PASS`; and
- FastAPI-style writing → `documentation-style-rereview-2.md` → `PASS`.

Update the P1.1 follow-up paragraph so it accurately distinguishes present source closure from later rendered/publication, distribution, and runtime gates. Preserve every earlier report. Re-run the immutable link and review-index reachability checks, then re-review this single finding at a new exact commit before creating the resolution record.

**Resolution:** Pending.

**Re-review condition:** All six authoritative specialist reports are reachable from the P1.1 table, their displayed verdicts equal their report verdicts, and no earlier finding record is removed or rewritten.

## Rendered-site-only checks explicitly deferred

These checks cannot be completed from Markdown source and do not contribute to the `CHANGES_REQUIRED` verdict:

1. rendered breadcrumbs, current audience/mode context, and search routing;
2. generated anchor behavior and copy-button fidelity in the selected renderer;
3. responsive tables, long JSON/code wrapping, reflow, and contrast;
4. keyboard order, focus, skip navigation, heading navigation, and representative screen-reader output; and
5. publication-safety review of generated HTML, search indexes, metadata, source maps, and downloadable artifacts.

## Verdict

**CHANGES_REQUIRED**

The implemented P1.1 reader journey and its evidence are ready at source level, and all six latest specialist verdicts are substantively compatible. Final documentation resolution is not ready because the authoritative source index exposes only three of those six verdicts. Fix and re-review DOCFINAL-P1.1-001; do not reopen the already-passing product pages or defer this Markdown-source defect to rendered-site work.
