# P1.1 FastAPI-style documentation re-review

## Review record

| Field | Value |
| --- | --- |
| Reviewed commit | `3665590ea9d9cfd65fc695b9c6cf0a18493fc077` |
| Commit tree | `602cf8ea8a4c45fe37b1c663a9f360b815fe2f99` |
| Commit parent | `94b9922ffbe78b7b5261cb8f6a14746b0b358456` |
| Commit subject | `docs: close p1.1 documentation findings` |
| Review date | 2026-07-15 |
| Review role | Independent technical-writing specialist |
| Prior report | `docs/reviews/p1.1-artifact-pair-inspector/documentation-style.md` |
| Verdict | **CHANGES_REQUIRED** |

The reader-facing content requested by DOCSTYLE-P1.1-001, DOCSTYLE-P1.1-002, and DOCSTYLE-P1.1-003 is present and accurate at this commit. The verdict remains changes required because the new executable documentation gates do not bind all of that content to its implementation or to valid recovery anchors. Mutation probes demonstrated that stale limits, stale expected output, an unsafe retry classification, and a broken recovery anchor can pass the named documentation tests.

## Exact scope

This re-review was limited to closure of the three prior findings and their executable anti-drift controls:

- `docs/reviews/p1.1-artifact-pair-inspector/documentation-style.md`;
- `docs/developers/tutorials/inspect-an-artifact-pair.md`;
- `docs/developers/reference/python-api.md`;
- `docs/developers/reference/cli-report-and-exit-codes.md`;
- `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md`;
- `capture/examples/inspect_valid_fixture.py`;
- `capture/tests/test_documentation.py`;
- `capture/src/dbtobsb_capture/contracts.py`;
- `capture/src/dbtobsb_capture/registry.py`;
- the public limits and issue templates in `capture/src/dbtobsb_capture/inspector.py`; and
- the documentation-test execution path in `scripts/check_capture.sh`.

The new raw-custody material was considered only where the affected pages link to it. Unrelated P1.1 behavior, other prior reviews, rendered-site behavior, and any cloud or paid-compute path were outside this bounded re-review. Reviewed source was not edited.

## Reviewed file hashes

All hashes are SHA-256 values read from the detached worktree at the exact commit.

| File | SHA-256 |
| --- | --- |
| `docs/reviews/p1.1-artifact-pair-inspector/documentation-style.md` | `77fcec23cdbfcd04a955d92f6ad39308afd77d4cd6d28d3f8b6d24b49841ba1c` |
| `docs/developers/tutorials/inspect-an-artifact-pair.md` | `e7f400f158584d8a35e1f02db1b7cc78b508bfd7eb13b1c36bea1e3fea011aae` |
| `docs/developers/reference/python-api.md` | `a935c761200df30b5ce0384f1834cc0edb6bf8836e24dd0fb91dd2ca23626b82` |
| `docs/developers/reference/cli-report-and-exit-codes.md` | `345f8421a519f96de5c66a0d8b8b752836ed241e3a1f3c29167624032de2be2d` |
| `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md` | `c73dc413e185d6fda992df7679806be9bf6a576bd57f2e709f1fa3c996b910da` |
| `capture/examples/inspect_valid_fixture.py` | `9ec9e35e7362cbe2907483e344c2979bd886b9586b03d35b465d93e533ec5099` |
| `capture/tests/test_documentation.py` | `32f97d5a80af2a4531e2b686e6643708eec9a5d2174b58d6b5f8e4d02c174438` |
| `capture/src/dbtobsb_capture/contracts.py` | `6f312022cfbf58b4a11232963e06e406e81da9c8ba42f55c331529f5a257b5f9` |
| `capture/src/dbtobsb_capture/registry.py` | `561f7a81bcb0fe7a9d1d2a8364228d39f88f758a83c34889c7e4480f60d5c1a6` |
| `capture/src/dbtobsb_capture/inspector.py` | `eccae1da909abeba0638f78a5001e6fb059481b74fe8fff8e4e2f1aac37208be` |
| `scripts/check_capture.sh` | `51d16177f3e517f2342df108ba6886aec6e7a4ea1d65e147ced70e7c1e1f91cd` |

## Current FastAPI benchmark

The re-review used the current official documentation as a style and maintenance benchmark, not as a theme or product template:

- [FastAPI First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/) gives the complete minimal program first, then the run action and observable response.
- The [official First Steps source](https://github.com/fastapi/fastapi/blob/master/docs/en/docs/tutorial/first-steps.md) includes its program from the separate checked-in [`docs_src` example](https://github.com/fastapi/fastapi/blob/master/docs_src/first_steps/tutorial001_py310.py), keeping displayed code tied to an executable source rather than maintaining two independent copies.
- [FastAPI Response Model](https://fastapi.tiangolo.com/tutorial/response-model/) puts exact type declarations beside validation, output-shape, and security consequences.
- [FastAPI Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/) places the error cause and exact resulting response together, then warns against exposing internal exception details.
- [FastAPI Learn](https://fastapi.tiangolo.com/learn/) keeps tutorial, advanced guide, and reference routes distinct.

Commit `3665590` now follows these reader-facing conventions: a complete example appears on the page, the exact response is adjacent, the public contract is table-led, and each issue row connects meaning to action and recovery. The remaining problem is maintenance integrity, not reader-facing organization.

## Check evidence

All commands ran in a detached worktree at the reviewed commit with dedicated uv cache and development environment paths.

| Check | Result |
| --- | --- |
| `scripts/check_capture.sh` | Passed; 94 tests, schema regeneration, Ruff check and format, ty, fixture regeneration, seven-package runtime-only path, API example, built wheel, and installed CLI ended in `DBTOBSB_CAPTURE_CHECK_PASSED` |
| `bash -n scripts/check_capture.sh` and `shellcheck scripts/check_capture.sh` | Passed |
| `pytest capture/tests/test_documentation.py -vv` | Passed all four documentation tests |
| Python fence extracted from `python-api.md` and executed through `python -` | Passed and matched the adjacent two-line output exactly |
| Public signature and dataclass-field probe | Matched the displayed keyword-only bytes signature and all documented public field types |
| Limit and vocabulary probe | `134217728` bytes, depth `256`, at most `20` issues, and exactly `error, fail, no-op, partial success, pass, skipped, success, warn` |
| Issue-registry shape | 26 rows, matching the 26-code precedence registry |
| Current recovery targets | All four referenced how-to headings exist |
| Detached worktree after checks | No reviewed-source changes |

The green suite establishes current correctness. The following in-memory mutation probes evaluated whether the new tests would also fail on documentation drift; they did not modify the worktree.

| Mutation probe | Observed result |
| --- | --- |
| Change implementation size/depth constants in memory to 64 MiB and 128, then call `test_python_reference_binds_closed_public_contract()` | Test still passed while the page still said 128 MiB and 256 |
| Change only the documented exact output's first line to `STALE_OUTPUT`, then call `test_displayed_python_example_matches_checked_in_program()` | Test still passed |
| Change the first issue classification to `Retry automatically` and its link to `#missing-recovery`, then call `test_issue_registry_binds_precedence_and_recovery_routes()` | Test still passed |

## Finding-by-finding closure

### DOCSTYLE-P1.1-001 — Partially closed

**Reader-facing closure: pass.** `docs/developers/reference/python-api.md:31-65` now shows a complete program on the page, links the checked-in source descriptively, reads fixture bytes explicitly, calls the API, safely serializes the allowlisted dictionary, and places exact output immediately after the code. `docs/developers/tutorials/inspect-an-artifact-pair.md:81-96` supplies the copy-ready run command. Extracting and running the displayed fence reproduced the documented output exactly.

**Code anti-drift closure: pass.** `capture/tests/test_documentation.py:27-33` proves that the displayed program is byte-for-byte equal to the checked-in executable example, and `scripts/check_capture.sh:37-49` executes that example on the runtime-only environment.

**Exact-response anti-drift closure: fail.** Neither test extracts the adjacent expected output and compares it with runtime stdout. The script gate checks only the first state and `pair_state` inside parseable JSON. The in-memory `STALE_OUTPUT` mutation therefore passed the documentation test.

**Required change:** Mark the expected output as a single extractable block and compare the displayed program's complete stdout with it in `test_documentation.py`. Keep the existing source-equality assertion. A semantic JSON assertion may be retained in addition to, not instead of, the exact-output assertion because the page says the output is exact.

### DOCSTYLE-P1.1-002 — Partially closed

**Reader-facing closure: pass.** `docs/developers/reference/python-api.md:7-29` now states the exact signature, 134,217,728-byte/128-MiB limit for each input, 256-level depth, failure behavior, closed status vocabulary, and one-to-20 invalid-issue cardinality. Lines 67-79 accurately describe public field types, optionality, tuple cardinality, computed fields, ordering, and invariants. Independent reflection matched the page to `contracts.py`, `registry.py`, and `inspector.py`.

**Vocabulary/cardinality anti-drift closure: pass.** `capture/tests/test_documentation.py:36-43` derives native statuses and the 20-issue maximum from the implementation registry.

**Limits/types anti-drift closure: fail.** The same test asserts literal strings `128 MiB` and `256`; it does not derive them from `MAX_PRIMARY_ARTIFACT_BYTES` or `MAX_JSON_NESTING_DEPTH`. It does not inspect the function signature or public dataclass fields. Changing the live constants in memory left the test green, proving that the named “binds closed public contract” check does not bind those exact limits.

**Required change:** Derive the decimal-byte/MiB and depth strings from the exported or inspector constants, then assert the exact table cells. Bind the displayed signature and public field/type/cardinality rows through `inspect.signature`, `dataclasses.fields`, and the relevant properties or generate those rows from one checked source. Add a mutation test or equivalent negative control showing that a limit or type change makes the documentation gate fail.

### DOCSTYLE-P1.1-003 — Partially closed

**Reader-facing closure: pass.** `docs/developers/reference/cli-report-and-exit-codes.md:55-92` now contains all 26 stable codes in precedence order. Every row supplies an exact safe impact, an understandable retry/recollect/unsupported classification, the exact primary action, and a descriptive recovery link. `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md:20-49` provides the four linked recovery sections. All current targets exist.

**Machine-contract anti-drift closure: pass.** `capture/tests/test_documentation.py:46-61` binds code membership/order to `ISSUE_PRECEDENCE` and binds every impact and primary action to the static issue template.

**Classification/recovery anti-drift closure: fail.** The test accepts any nonempty classification and only checks that a recovery cell contains the expected path prefix. It does not validate the allowed classification or per-code mapping and does not resolve the target heading. The in-memory `Retry automatically` plus `#missing-recovery` mutation passed.

**Required change:** Define and test the exact per-code classification mapping or generate that column from one reviewed documentation registry. Resolve each relative recovery link and assert that its fragment identifies a real heading. Add negative controls for an invented classification and a missing anchor.

## Verdict

**CHANGES_REQUIRED**

The three pages are now clear, accurate, and materially aligned with the current FastAPI documentation traits. No new reader-facing content defect was found. Re-review fails only because the requested executable anti-drift protection is incomplete in each closure path. A focused follow-up can retain the present prose and tables, strengthen the three documentation tests above, rerun `scripts/check_capture.sh`, and re-execute the mutation probes.
