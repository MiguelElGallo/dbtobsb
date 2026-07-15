# P1.1 final documentation consistency closure re-review

## Review record

| Field | Value |
| --- | --- |
| Reviewed commit | `2367a05d4e9ddb763cc52a3b7090c4099a639631` |
| Commit tree | `a3ef222f0300903f6cee4bef57db64d9a3d5b49d` |
| Commit parent | `08de2ddb3429bb675b6587de4c225bbf93102a1f` |
| Commit subject | `fix: make p1.1 invocation recovery overwrite-safe` |
| Blocking audit | `documentation-final.md`, reviewed commit `2b76abbd565271b30f37fdb1e3f00d76185e8dc4` |
| Review date | 2026-07-15 |
| Review role | Independent focused documentation closure reviewer |
| Verdict | **PASS** |

`DOCFINAL-P1.1-001` is closed. The authoritative P1.1 table now routes directly to all six specialist reports named by the finding, every displayed verdict equals the verdict in its target report, and the follow-up paragraph distinguishes accepted source documentation from later runtime, distribution, rendered-site, and publication gates. All 21 P1.1 reports present at the blocking audit remain byte-identical; three newer finding records are additive. The current reader journey and executable documentation checks also pass without regression.

This is a one-finding re-review. It does not adjudicate or resolve findings in the separately added `documentation-dbt.md` or `documentation-usability.md` reports, and its `PASS` must not be used as their resolution.

## Exact scope

### Closure set

The closure set is this exact path-ordered eight-file list:

1. `docs/reviews/README.md`
2. `docs/reviews/p1.1-artifact-pair-inspector/databricks-rereview-3.md`
3. `docs/reviews/p1.1-artifact-pair-inspector/dbt-core-rereview-3.md`
4. `docs/reviews/p1.1-artifact-pair-inspector/documentation-final.md`
5. `docs/reviews/p1.1-artifact-pair-inspector/documentation-ia-rereview-2.md`
6. `docs/reviews/p1.1-artifact-pair-inspector/documentation-security-rereview-2.md`
7. `docs/reviews/p1.1-artifact-pair-inspector/documentation-style-rereview-2.md`
8. `docs/reviews/p1.1-artifact-pair-inspector/usability-rereview-3.md`

History preservation was compared against every file under `docs/reviews/p1.1-artifact-pair-inspector/` in the blocking audit commit `2b76abb…`. That immutable baseline contains 21 reports.

### Reader-journey no-regression set

The reader set is this exact path-ordered 11-file list:

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
11. `docs/index.md`

### Executable corroboration

The validation set is:

1. `capture/tests/test_documentation.py`
2. `scripts/check_capture.sh`
3. `scripts/check_markdown_links.py`

No cloud, Databricks authentication, dbt execution, or paid compute was used. No reviewed source was edited.

## Immutable hashes

Each aggregate is SHA-256 over the literal path-ordered `shasum -a 256` record stream for its exact set above.

| Frozen input | SHA-256 |
| --- | --- |
| Eight-file closure aggregate | `235b2df6e2462f1e7dd74218777c1f71690ea3b081301f6365462756c32ae1b1` |
| 11-file reader-journey aggregate | `903dc23ae61ca87e4750fc2df5cb3baf82e7798d26d9825296e3e0891b05f9b0` |
| Three-file validation aggregate | `f28a1c57b8c451dc518e69e84b1d3c62a2977da3dead138b7a13b1ad8715ec72` |

Closure-file hashes are:

| File | SHA-256 |
| --- | --- |
| `docs/reviews/README.md` | `ec7e73009e88274a38c140add8eb49e81b74be23c5350a39578a70a784d8780c` |
| `databricks-rereview-3.md` | `03acccf94d1f57e4f634979ea0f1de3b70297cbd9802f40a9070badd66c3a18d` |
| `dbt-core-rereview-3.md` | `5bb97bbf6a08207fb4462c1de590e4fa7c9e0fd40bcba7f28e9926f3f2ac0180` |
| `documentation-final.md` | `5b147240e90c6a1660e5ee2c9fe80a2efdd3dcaf05e510b5e955f6a89411e2e6` |
| `documentation-ia-rereview-2.md` | `0ac0ef4e9e29bbc4ca6f3005d630b836934e28ab85cdc159cf2712b668cd7c44` |
| `documentation-security-rereview-2.md` | `914af86b68d7cf578f7f8a532c35fdeca2b74e23b733d295d8c850bbdbd6454a` |
| `documentation-style-rereview-2.md` | `d0d531b5724ef641279730280745b7a8a75a4fe50bb145f502f0af88e45d5791` |
| `usability-rereview-3.md` | `6605d63b92605f9a7940a17234794468c3d03d1e8052fb475e18682f68fb0317` |

Validation-file hashes are:

| File | SHA-256 |
| --- | --- |
| `capture/tests/test_documentation.py` | `34a514f751fd83df0afd045ae73b6bbc0af151dcb27523fb22a9f08f534a9683` |
| `scripts/check_capture.sh` | `92656cda84b66dd76338cec050c35e632ae50de015bda89e474d28a74854b911` |
| `scripts/check_markdown_links.py` | `aa904ffdd5540d2604b840c42d8d04660c03c57e0d1f818355fc524dbd40b0c0` |

## Checks executed

All checks ran in a detached worktree at the exact reviewed commit with dedicated uv cache and environment paths.

| Check | Result |
| --- | --- |
| Exact commit/tree/parent verification | Passed |
| P1.1 authority-table parser | Six rows; six target files; six exact index/report verdict matches; zero missing or mismatched targets |
| Review-history comparison to `2b76abb…` | 21 baseline reports preserved byte-for-byte; three reports added; zero existing files modified, deleted, renamed, or type-changed |
| Recursive landing-route graph | All eight implemented developer pages reachable; zero unreachable pages |
| `python3 scripts/check_markdown_links.py` | 124 tracked Markdown files, 200 local links, 55 fragments, zero errors |
| `scripts/check_capture.sh` | Passed; ended in `DBTOBSB_CAPTURE_CHECK_PASSED` |
| Capture test suite | 96 passed |
| Focused documentation tests | Six of six passed |
| Ruff check and format, plus ty | Passed |
| Schema and fixture regeneration | Passed without diff |
| Seven-package runtime-only path, API example, wheel, and installed CLI | Passed |
| `bash -n scripts/check_capture.sh` and `shellcheck scripts/check_capture.sh` | Passed |
| Reader heading hierarchy | 11 files checked; one H1 per file and zero skipped levels |
| Reader terminology scan | Zero `PII` or expanded-PII uses |
| `git diff --check 2b76abb…2367a05…` | Passed |
| Detached reviewed worktree after all checks | Clean; zero tracked diff |

The first combined focused-test invocation supplied unsupported optional flags to the link checker after all six documentation tests had passed. That invocation exited on argument parsing. The repository-owned link checker was then rerun with its supported command shown above and passed with the exact recorded counts; the full gate independently invoked the same supported path and passed.

## DOCFINAL-P1.1-001 closure

### Six authority routes and verdicts — PASS

| Review lens | Direct target from `docs/reviews/README.md` | Index verdict | Target-report verdict |
| --- | --- | --- | --- |
| Databricks platform/security | `databricks-rereview-3.md` | `PASS_WITH_FOLLOW_UP` | `PASS_WITH_FOLLOW_UP` |
| dbt Core/artifact contract | `dbt-core-rereview-3.md` | `PASS_WITH_FOLLOW_UP` | `PASS_WITH_FOLLOW_UP` |
| Usability/onboarding | `usability-rereview-3.md` | `PASS_WITH_FOLLOW_UP` | `PASS_WITH_FOLLOW_UP` |
| Diátaxis information architecture | `documentation-ia-rereview-2.md` | `PASS_WITH_FOLLOW_UP` | `PASS_WITH_FOLLOW_UP` |
| Security/compliance documentation | `documentation-security-rereview-2.md` | `PASS` | `PASS` |
| FastAPI-style writing | `documentation-style-rereview-2.md` | `PASS` | `PASS` |

Every target is a direct Markdown-source link in the P1.1 table. An accountable reader no longer has to enumerate the directory or infer which of the earlier failed reports was superseded.

### Failed-history preservation — PASS

The comparison commit contains the 21 P1.1 reports that existed when the blocking audit was written. None changed or disappeared. The current tree contains 24 reports because `documentation-dbt.md`, `documentation-final.md`, and `documentation-usability.md` were added. Fifteen current files contain retained `CHANGES_REQUIRED` evidence. The source fix therefore improves discoverability without rewriting or hiding a failed pass.

### Source closure versus later gates — PASS

The index says that the latest source-level architecture, security, and writing reports are accepted. That matches the three report verdicts and dispositions. It places actual Databricks runtime and archive qualification, complete Linux dependency-lock/distribution qualification, distributed help, rendered-site behavior, and publication safety in later gates. Those deferrals are present in the authoritative specialist reports. The paragraph also preserves the crucial limit: they do not permit P1.1 to claim a complete capture or a qualified production runtime.

This wording does not convert a deferred rendered or product gate into source acceptance, and it does not weaken the repository rule for `PASS_WITH_FOLLOW_UP`.

## Reader-journey no-regression assessment

The three landing routes still lead through the developer index to all seven leaf pages. The tutorial remains a guided fixture journey; the how-tos remain recovery and raw-custody tasks; the references remain machine and Python contracts; and the explanations retain the validity/outcome/capture and custody mental models.

The reader changes after the blocking audit improve rather than blur those routes:

- invocation recovery now tells readers to collect both closed artifacts from one completed pinned `dbt build` before another command can overwrite the target;
- the reference now exposes the exact BuildTask result compatibility and `status_counts` semantics used by implementation;
- raw-artifact handling uses the same locked, no-sync command as the tutorial and the executable documentation test;
- `PAIR_VALID` explicitly excludes provenance, authenticity, custody, archive, and capture-completeness claims; and
- the exact invalid-invocation output, issue registry, API contract, command snippets, and sensitive-input routes are bound by the six passing documentation tests.

Local-link, heading, terminology, runtime, installed-wheel, and exact documentation-contract checks all pass. No mode, navigation, terminology, current-versus-future, or custody regression was found in this focused re-review.

## Rendered-site-only checks explicitly deferred

These checks still require a built publication artifact and are not source failures in this closure verdict:

1. rendered breadcrumbs, current audience/mode context, and search routing;
2. generated anchors, static help fragments, and copy-button fidelity;
3. responsive tables, long code/JSON wrapping, reflow, and contrast;
4. keyboard order, focus, skip navigation, heading navigation, and representative screen-reader output; and
5. publication-safety inspection of generated HTML, search indexes, metadata, source maps, and downloadable artifacts.

## Verdict

**PASS**

`DOCFINAL-P1.1-001` is resolved at exact commit `2367a05d4e9ddb763cc52a3b7090c4099a639631`. All six required authority routes are present and exact, failed history is preserved, later gates remain accurately bounded, and the reader journey has not regressed. No new finding was opened in this one-finding scope.
