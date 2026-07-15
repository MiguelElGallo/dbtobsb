# P1.1 FastAPI-style documentation review

## Review record

| Field | Value |
| --- | --- |
| Reviewed commit | `1900cd01254837010d7d93bb0cd69cf0b98eb1b5` |
| Review date | 2026-07-15 |
| Review role | Independent technical-writing specialist |
| Style benchmark | Current FastAPI documentation traits; no FastAPI theme or wording was copied |
| Verdict | **CHANGES_REQUIRED** |

This is a source-document verdict. Three documentation defects remain in the reviewed commit. The runnable paths, output examples, security boundaries, and tutorial-to-recovery flow are otherwise strong and passed their executable controls.

## Scope

The review covered these files and contracts at the immutable commit above:

- `README.md`, specifically the P1.1 route;
- `capture/README.md`;
- `docs/index.md`;
- every Markdown file under `docs/developers/`;
- `docs/evidence/p1.1-local-artifact-pair-2026-07-15.md`;
- the implemented P1.1 boundary in `docs/plans/product-plan.md`;
- the P1.1 information architecture and page contract in `docs/plans/documentation-plan.md`; and
- the public API, issue registry, input limits, and allowed-status vocabulary in `capture/src/dbtobsb_capture/`.

The review evaluated outcome-first structure, progressive disclosure, copy-ready commands and API code, exact expected responses, plain language, type and contract precision, error-to-recovery proximity, descriptive links, terminology consistency, and explicit product boundaries.

## External benchmark

The comparison used only current official FastAPI documentation:

- [FastAPI First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/) presents a complete minimal program before explaining its parts, supplies a copy-ready run command, and places the exact response beside the action that produces it.
- [FastAPI Handling Errors](https://fastapi.tiangolo.com/tutorial/handling-errors/) keeps the error cause, code, response, and recovery context together and explicitly warns against leaking sensitive exception details.
- [FastAPI Response Model](https://fastapi.tiangolo.com/tutorial/response-model/) gives complete typed examples and then explains validation, filtering, schema, and security consequences.
- [FastAPI Learn](https://fastapi.tiangolo.com/learn/) separates tutorial, advanced guide, and reference material so readers can choose a task path without reading the whole site.

These traits were used as a clarity benchmark. FastAPI-specific product concepts, visual design, and prose were not treated as requirements.

## Executable review

All concrete P1.1 commands and output examples in scope were exercised from a detached worktree at the reviewed commit. Schematic commands containing `PATH` or caller-owned path placeholders were exercised with the checked-in sanitized fixtures. The compact Python fragment was exercised after defining its two documented caller-provided byte values.

| Control | Result |
| --- | --- |
| Fresh `uv sync --project capture --locked --no-dev` in a dedicated cache and environment | Passed; installed the seven locked runtime packages |
| Valid-pair CLI command | Exit `0`; empty stderr; output exactly matched the tutorial |
| Valid evidence containing a dbt failure | Exit `0`; empty stderr; compact JSON exactly matched the tutorial |
| Invalid invocation pair | Exit `10`; empty stderr; output exactly matched the tutorial |
| Checked-in Python API example | Exit `0`; empty stderr; both documented lines matched exactly |
| Python reference fragment with caller-provided fixture bytes | Executed and returned `PAIR_VALID` |
| Input-read failure | Exit `3`; empty stdout; the four stderr lines matched the CLI reference exactly |
| How-to and CLI placeholder forms with fixture paths substituted | Executed with the documented structure |
| `scripts/check_capture.sh` | Passed: 90 tests, Ruff check and format, ty, regeneration, runtime-only example, API example, wheel and installed CLI, Bash syntax, and ShellCheck |
| Scoped local-link check | Passed: 36 local links resolved; the checked local heading target exists |
| Worktree cleanliness after execution | Passed |

The executable controls prove that the present commands and literal responses are accurate. They do not remove the reference and copy-readiness defects below.

## Required findings

### DOCSTYLE-P1.1-001 — The Python API example is not copy-ready on the page

**Severity:** Medium

**Affected source:** `docs/developers/reference/python-api.md:5-33`

The page calls a checked-in script and accurately shows its exact output, but it neither displays nor links directly to that script. The only Python code visible on the page uses `manifest_bytes` and `run_results_bytes` without defining them. A reader can run the repository's prepared example, but cannot copy and adapt a complete API call from this page without leaving the documented path, locating source, and inferring the file-loading and safe-serialization steps.

This falls short of the reviewed page's claim that the route is copy-ready and of the benchmark established by FastAPI First Steps: show the complete minimal program, then the run command and exact response. It is also materially different from a deliberately schematic function signature because the heading promises a first inspection.

**Required change:** Put one complete, minimal Python example on the page—or include it from the single tested source—covering fixture or caller-path byte loading, `inspect_artifact_pair`, `PairState`, and deterministic safe serialization. Keep the exact output immediately after it. Make the displayed snippet executable in a documentation check so the page and checked-in example cannot drift. Retain the compact function signature below as reference material.

**Resolution:** Pending.

**Re-review:** Confirm that a reader can copy the displayed program into a file and reproduce the documented output without discovering an unlinked implementation file.

### DOCSTYLE-P1.1-002 — The Python contract reference omits enforced limits and allowed values

**Severity:** Medium

**Affected source:** `docs/developers/reference/python-api.md:39-66`

The page describes the public types by purpose but does not fully specify their public field types or cardinality. It also omits two enforced API input limits—128 MiB per byte argument and a maximum JSON nesting depth of 256—and does not enumerate the closed native-status vocabulary: `error`, `fail`, `no-op`, `partial success`, `pass`, `skipped`, `success`, and `warn`.

The CLI page documents its 128 MiB file boundary, but the Python API accepts bytes directly and enforces the same size limit. Python integrators should not have to inspect implementation constants or induce errors to learn the accepted envelope. The omission also conflicts with the repository's own documentation contract in `docs/plans/documentation-plan.md:281`, which requires reference pages to define types, allowed values, defaults, compatibility, security classification, and examples.

**Required change:** Add a compact public-contract table that states the function input constraints and failure behavior, public attribute types and optionality/cardinality, the complete allowed status vocabulary, and the 20-issue limit already described in prose. State the 256 nesting boundary and 128 MiB limit beside the corresponding Python inputs and link their stable issue codes to recovery guidance. Prefer a generated or test-checked source for closed vocabularies and constants.

**Resolution:** Pending.

**Re-review:** Compare the rendered reference against exported signatures, public dataclass fields, registry values, and inspector constants; then exercise boundary examples or their contract tests.

### DOCSTYLE-P1.1-003 — Stable report issue codes are separated from meaning and recovery

**Severity:** Medium

**Affected source:** `docs/developers/reference/cli-report-and-exit-codes.md:51-62`; related recovery route `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md`

The issue registry lists stable codes by validation stage, but it does not give the meaning, retry or recollection classification, primary next action, or a direct recovery link for each code or coherent code family. Runtime issue objects carry safe static `impact` and `next_action` text, and the how-to offers a useful family table, but an integrator reading the contract cannot determine automation or support behavior without manufacturing each failure or inspecting source and schema files.

The exit-`3` section is the positive counterexample: its code, exact output, impact, next action, and recovery route are adjacent. The report issue registry should offer equivalent navigability without turning the reference into a procedure. This is required both by the FastAPI error-documentation benchmark and by `docs/plans/documentation-plan.md:281`, which says stable-code references catalogue meaning and retryability and link to symptom-specific recovery tasks.

**Required change:** Expand the registry, directly or through grouped rows, with code, plain-language meaning or impact, retry/recollect/unsupported classification, primary recovery action, and a descriptive link to the matching how-to section. Generate or validate these fields against the closed issue registry so static security-safe text and precedence cannot drift.

**Resolution:** Pending.

**Re-review:** Verify every published report issue code has one unambiguous interpretation and recovery route, and that the table still matches the machine contract exactly.

## File-specific assessment and positive controls

| Source | Assessment |
| --- | --- |
| `README.md` P1.1 | Pass. Leads with the offline inspection outcome, distinguishes offline execution from the initial dependency download, gives a short successful command path, and routes details through descriptive links. It does not claim that a disconnected installation artifact ships in P1.1. |
| `capture/README.md` | Pass. Briefly states the library boundary and sends each reader to the appropriate tutorial, how-to, reference, explanation, or evidence page. |
| `docs/index.md` | Pass for the documented P1.1 route. It links the implemented inspection path without pretending that the planned product site already exists. The planning-heavy home is explicitly deferred to D0. |
| `docs/developers/index.md` | Pass. Starts with reader outcomes, separates learn/fix/integrate/understand routes, and makes fixture and production-evidence boundaries visible before navigation. |
| `docs/developers/tutorials/inspect-an-artifact-pair.md` | Pass. Gives the result first, reveals prerequisites before commands, provides exact success, dbt-failure, and invalid-pair responses, and closes with a three-question mental model. All concrete commands and literal output matched execution. |
| `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md` | Pass. Begins with the symptom, maps primary issue families to actions, and places exit-`3` and exit-`4` recovery beside their failure modes. Placeholder paths are clearly schematic. |
| `docs/developers/reference/python-api.md` | Changes required by DOCSTYLE-P1.1-001 and DOCSTYLE-P1.1-002. Its deterministic behavior, non-I/O boundary, safe serialization, supported pair, and evidence-validity-versus-job-success distinction are otherwise unusually clear. |
| `docs/developers/reference/cli-report-and-exit-codes.md` | Changes required by DOCSTYLE-P1.1-003. CLI syntax, output channels, exact exit behavior, safe read boundary, closed JSON shape, and versioning rule are precise. |
| `docs/developers/explanation/artifact-pair-validity.md` | Pass. Uses a concise comparison table to prevent the central category error: valid evidence is not necessarily a successful dbt run, and local inspection is not capture completeness. |
| `docs/evidence/p1.1-local-artifact-pair-2026-07-15.md` | Pass. Leads with outcomes, labels sanitized synthetic evidence, and distinguishes source-tree, installed-wheel, security, determinism, and negative controls. Its dense test-inventory paragraph is a later scanability improvement, not a correctness blocker. |
| P1.1 product and documentation plans | Pass as governing contract text. The implemented boundary, audience route, publication evidence, and Diataxis page rules are explicit; findings 002 and 003 arise because the current reference pages do not yet satisfy those rules. |

Terminology is consistent across the route: `manifest.json`, `run_results.json`, artifact pair, pair validity, dbt result status, capture completeness, `PAIR_VALID`, and `PAIR_INVALID` retain distinct meanings. The material repeatedly and correctly avoids claims of production capture, dbt success, Databricks observation, or disconnected installation.

## Later-site gates

These items should be verified when D0 introduces the rendered documentation site. They do not change this source-document verdict:

1. Verify task navigation, search synonyms, heading anchors, responsive tables and JSON blocks, keyboard focus, and code-copy behavior in the actual renderer.
2. Replace repository-relative runtime help with a stable distributed help URL or packaged offline route before customers install the CLI outside a source checkout.
3. Run publication-safety checks against the rendered artifact, including search indexes, source maps, generated metadata, and downloadable files—not only Markdown sources.
4. Confirm long issue and evidence tables remain scannable on narrow screens and that grouped rows preserve accessible headers.
5. Re-run every displayed snippet from its rendered copy surface so include directives or formatting cannot alter executable text.

## Verdict

**CHANGES_REQUIRED**

The P1.1 documentation already has a strong tutorial, accurate literal outputs, nearby error recovery for CLI failures, explicit regulated-data boundaries, and a coherent Diataxis route. It is not ready to pass the requested FastAPI-style source review until the Python page contains a self-contained tested example, its public contract documents enforced limits and allowed values, and the stable issue registry connects each error family to meaning and recovery. Re-review can be limited to those three changes plus their executable and contract-drift controls.
