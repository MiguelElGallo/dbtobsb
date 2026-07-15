# P1.1 artifact-pair inspector final resolution

- Date: 2026-07-15
- Reviewed source commit: `cff8bbcd808ff7e13a7ead182543a2564cd04ff6`
- P1.1 disposition: **accepted as the offline-after-installation local artifact-pair inspection slice**
- Production disposition: **not a live Databricks collector, complete capture, qualified production runtime, disconnected distribution, or Marketplace release**

## Frozen inputs

| Input | Scope | SHA-256 |
| --- | --- | --- |
| Capture implementation and gates | 48 tracked files under `capture/`, `.github/workflows/capture.yml`, `scripts/check_capture.sh`, and `scripts/check_markdown_links.py`, path-sorted | `eed53519381de61685832eaf61e713eec0f8ad0b45a37fccd3e0b563a12024ce` |
| P1.1 developer documentation | 14 path-sorted files: repository/package/documentation entry points, all `docs/developers/` pages, P1.1 evidence, Decision 0002, and the documentation plan | `3731146dfe3890192c74f23fc39e207b0df714433369afb2973a63f9c32ae6f6` |
| Latest authoritative reviews | Nine reports listed in the verdict table below, in table order | `d8225ab1886dcff00a5f791dc718381ec23e638f2705e0ebd0d37730b61c5625` |

Each aggregate is SHA-256 over the literal `shasum -a 256` records for the stated path order. The resolution and review index are outside those frozen inputs and receive a separate final audit.

## Final review verdicts

| Review lens | Latest report | Verdict |
| --- | --- | --- |
| Databricks platform/security | [databricks-rereview-4.md](databricks-rereview-4.md) | `PASS_WITH_FOLLOW_UP` |
| dbt Core/artifact contract | [dbt-core-rereview-4.md](dbt-core-rereview-4.md) | `PASS_WITH_FOLLOW_UP` |
| Product usability/onboarding | [usability-rereview-4.md](usability-rereview-4.md) | `PASS_WITH_FOLLOW_UP` |
| Diátaxis information architecture | [documentation-ia-rereview-2.md](documentation-ia-rereview-2.md) | `PASS_WITH_FOLLOW_UP` |
| Security/compliance documentation | [documentation-security-rereview-2.md](documentation-security-rereview-2.md) | `PASS` |
| FastAPI-style writing | [documentation-style-rereview-2.md](documentation-style-rereview-2.md) | `PASS` |
| dbt subject-matter documentation | [documentation-dbt-rereview.md](documentation-dbt-rereview.md) | `PASS` |
| Documentation usability/accessibility | [documentation-usability-rereview-2.md](documentation-usability-rereview-2.md) | `PASS_WITH_FOLLOW_UP` |
| Final reader-journey consistency | [documentation-final-rereview.md](documentation-final-rereview.md) | `PASS` |

There is no open P1.1 blocker. Every `PASS_WITH_FOLLOW_UP` item names a later runtime, distribution, rendered-site, accessibility, or release gate rather than a defect in this local slice.

## Accepted product contract

P1.1 accepts keyword-only `manifest: bytes` and `run_results: bytes`, validates the complete pinned dbt Core 1.11.12 manifest-v12 and run-results-v6 schemas for a manifest whose `adapter_type` is `databricks`, and applies the exact dbt Core `BuildTask` collection/resource plus `RunStatus`/`TestStatus` matrix. A valid report preserves native executed-result status counts; it does not reinterpret them as dbt success, Lakeflow task state, or capture completeness.

The CLI accepts closed regular files up to 128 MiB, fails safely for paths, links, pipes, devices, and oversized input, and emits only allowlisted output. The API and CLI use no Databricks, dbt, network, environment, clock, or subprocess runtime dependency during inspection. Raw input bytes, SQL, messages, adapter responses, paths, relations, project/resource/invocation identity, and other artifact content are excluded from ordinary reports.

Invocation pairing requires equal parseable invocation identities and overwrite-safe collection of both closed artifacts from one completed pinned build. Directory co-location is not a pairing key. Decision 0002 records the pre-release v1 correction; the generated schema, fixture/generator, API/CLI output, documentation, and tests are synchronized.

## Quality evidence

The accepted source passed:

- 96 tests, including six executable documentation contracts and the complete collection/status/schema/constructor/CLI/adversarial suite;
- Ruff lint and formatting plus `ty` static type checking;
- byte-identical report-schema and fixture regeneration;
- a seven-package runtime-only environment, exact Python example, wheel build, and isolated installed console-entry-point run;
- Bash syntax and ShellCheck;
- deterministic Markdown path/fragment validation; and
- independent mutation, GFM rendering, safe-output, input-shape, raw-canary, and zero-socket/process probes recorded in the latest reports.

The runtime-only locked dependency export had no known vulnerability in the recorded `pip-audit==2.10.0` check. GitHub Actions uses read-only contents permission, exact action SHAs, CPython 3.12.3, uv 0.11.28, a ten-minute timeout, and no artifact upload.

## Material finding cycles closed

- Full schema/resource/status coverage, strict input parsing, bounded files/nesting/issues, deterministic primary precedence, closed constructors/schema, installed-resource proof, and nonblocking unsafe-file handling closed the product review findings.
- The developer route now separates tutorial, recovery/handling how-tos, API/CLI reference, and pair/custody explanations; exact programs, outputs, limits, fields, issue classifications/actions/anchors, and compatibility semantics are executable documentation contracts.
- Raw artifacts are treated as potentially Personal Data-bearing and sensitive. Caller custody, support boundaries, retention/deletion/legal hold, transient processing, and workstation-local versus future Databricks-local meaning are explicit.
- Invocation recovery no longer relies on a reused target directory or calls a pair trusted. Static text and generated contracts changed together under the accepted pre-release decision.
- GFM table structure and visible union types, runnable uv command shape, reproducible immutable link evidence, complete review-index reachability, and final reader-journey consistency all passed focused re-review.

## Retained nonblocking gates

- Real Azure Databricks archive retrieval and layout for success, dbt failure, early failure, cancellation, timeout, retry, and repair.
- AttemptKey, archive hash, structured logs, native Job evidence, stable absence, trust observation, and full capture-state implementation.
- Complete Python 3.12/Linux and disconnected-distribution qualification before any air-gapped installation claim.
- Rendered documentation-site navigation, search, browser, keyboard, responsive layout, contrast, screen-reader, assistive-technology, WCAG, and publication-safety validation.
- Compatibility qualification for any dbt Core/adapter/schema/resource/status row beyond the pinned candidate.

These gates block later product claims. They do not block the reviewed offline local inspector.
