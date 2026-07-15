# Third dbt Core re-review: P0 planning baseline 0.4

- Reviewed input: frozen pre-commit author file set defined in `resolution.md`
- Re-review input SHA-256: `8504d49ed1397e218a5760885673c87458d4ecd16d60936191ea0a2d89f48c98`
- Date: 2026-07-15
- Reviewer role: independent dbt Core and `dbt-databricks` specialist
- Verdict: `PASS`
- Open dbt findings: none
- Blockers: none
- Cloud mutation: none

## Executive verdict

Baseline 0.4 is ready for P0 acceptance from the dbt specialist perspective. It resolves the two conditions reopened by the second re-review without weakening the already resolved warning, artifact, data-model, privacy, or AI boundaries:

1. The scanner now models simultaneous non-empty project and deprecated profile flag mappings as Core's configuration error, treats configured current/legacy aliases as a deliberate stricter conflict, and defines separate exact `deps` and `build` templates. Both ordinals explicitly disable anonymous usage and artifact-ingest upload, and neither accepts CLI vars.
2. Primary-file cardinality is now total. Each file is validated independently; one standalone-valid manifest is an incomplete `PARTIAL` capture, run-results without its manifest is invalid, neither file requires same-primary-build start evidence for `PARTIAL`, and a `deps` event cannot supply that evidence.
3. The exact `dbt-common==1.37.5` wheel hash, expected `log_version=3`, seven ordered log states, quarantine rules, and complete dependency-lock requirement remain intact.

No new dbt regression was found. The implementation and live evidence named for P1, P2, P3, P4, P5, P7, P8, and P10 remain mandatory at those part gates; their absence during P0 planning is not a contract defect and does not qualify this verdict.

This is the dbt specialist approval of the planning contract, not a claim that the candidate runtime has already passed its future golden suite or live Databricks qualification. Repository-level P0 completion still depends on the other independent re-reviews, resolution recording, and the commit/push gate in the plan.

## Immutable input verification

The reviewed author scope is `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path. I independently hashed every scoped file and then hashed the sorted digest list. The result is:

```text
8504d49ed1397e218a5760885673c87458d4ecd16d60936191ea0a2d89f48c98
```

The repository still has no commit. The file-set digest is therefore the immutable review identity. Review reports and `resolution.md` are outside the author-input hash. I changed no author-owned file.

## Current source and local contract checks

Web research, the official dbt documentation, tagged first-party source, release APIs, the artifact schemas, and the published wheel metadata were refreshed on 2026-07-15. Core 1.11.12 remains the latest stable Core release; 1.12.0rc3 is a prerelease. `dbt-databricks` 1.12.2 remains the latest stable adapter release.

Primary evidence checked:

- [dbt Core 1.11.12 release](https://github.com/dbt-labs/dbt-core/releases/tag/v1.11.12) and [Python/dependency metadata](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/pyproject.toml)
- [`dbt-databricks` 1.12.2 release](https://github.com/databricks/dbt-databricks/releases/tag/v1.12.2) and [exact Core/common constraints](https://github.com/databricks/dbt-databricks/blob/v1.12.2/pyproject.toml)
- [Core 1.11.12 project/profile flag loading](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/config/project.py), [option declarations and aliases](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/params.py), [flag resolution](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/flags.py), and [command decorators](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/main.py)
- [dbt warning configuration](https://docs.getdbt.com/reference/global-configs/warnings), [global flags](https://docs.getdbt.com/reference/global-configs/about-global-configs), [JSON artifacts](https://docs.getdbt.com/reference/global-configs/json-artifacts), [logs](https://docs.getdbt.com/reference/global-configs/logs), and [usage statistics](https://docs.getdbt.com/reference/global-configs/usage-stats)
- [manifest v12 schema](https://schemas.getdbt.com/dbt/manifest/v12.json), [run-results v6 schema](https://schemas.getdbt.com/dbt/run-results/v6.json), and [Core 1.11.12 BuildTask collections](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/task/build.py)
- [Core 1.11.12 `MainReportVersion` emission](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/core/dbt/cli/requires.py), [dbt events/logging](https://docs.getdbt.com/reference/events-logging), and [`dbt-common` 1.37.5](https://pypi.org/project/dbt-common/1.37.5/)

Read-only local checks against an isolated Core 1.11.12 environment corroborated the tagged source:

- `deps` accepts the governed global warning, logging, usage, artifact-upload, and vars options, but has no selector or target-path option; `build` accepts selector and target path.
- The hidden `--log-file-max-bytes` global option is accepted by both command parsers.
- Simultaneous non-empty project `flags` and profile `config` fails during Core configuration before normal value resolution.
- The exact installed `dbt-common` version was 1.37.5, its source declares `LOG_VERSION = 3`, and a JSON-logging initialization emitted the expected `MainReportVersion` event.
- The PyPI wheel digest independently reproduced `432e3f2f9ca61eace65d4d1cb99a715c3ffc343b7190a692c39f126eedf0c077`.

These were local parser/source probes only. They did not start Databricks compute or mutate Azure, Databricks, dbt Cloud, or another remote system.

## Focused finding dispositions

| Finding | Third re-review disposition | Baseline 0.4 evidence | Conclusion |
|---|---|---|---|
| `DBT-P0-002` | `RESOLVED` | Product plan lines 171-209 and fixture line 436 | Project/profile coexistence is a stable `DBT_PROJECT_PROFILE_FLAGS_CONFLICT`; configured current/legacy aliases are a stable `DBT_FLAG_ALIAS_CONFLICT`; conflict inspection occurs before Core alias propagation. Exact shared flags apply to both ordinals, while only `build` receives selector and target path. Both commands disable anonymous usage and artifact-ingest upload, and additional output/egress/path/vars flags fail closed. |
| `DBT-P0-003` | `RESOLVED` | Product plan lines 253-293 and fixture line 436 | Standalone validation precedes pair validation. Manifest-only is the sole missing-counterpart exception and creates no result rows; run-results-only is invalid; same-build start evidence makes neither-file input partial; no such evidence makes it not produced; unavailable retrieval wins first; a `deps` event is excluded. Every supported input reaches exactly one state. |
| `DBT-P0-004` | `RESOLVED — NO REGRESSION` | Product plan lines 154-167, 261-271, and 432-436 | Core, adapter, common, Python, environment, expected log version, and wheel digest are exact candidate inputs. The full Python 3.12/Linux graph remains a required hash lock. The seven log states are ordered and total, damaged/unknown diagnostics are quarantined without parsing `msg`, and a valid artifact pair remains independently valid. |

The previously resolved `DBT-P0-001`, `DBT-P0-005`, `DBT-P0-006`, `DBT-P0-007`, and `DBT-P0-008` contracts did not regress.

## Exact planning-contract verification

| Contract area | Verdict | Third re-review conclusion |
|---|---|---|
| Candidate compatibility | `PASS` | Core 1.11.12 fits adapter 1.12.2's exact `<1.11.13` bound. Python 3.12.3 is inside the published 3.10-3.13 intersection. Core 1.12, Core 2.0, Python 3.14, other serverless environments, and dependency changes remain unsupported until requalified. |
| Complete dependency lock | `PASS` | The common wheel/version/hash is exact, while the plan explicitly states that this is not the complete lock. Producing the full Python 3.12/Linux and Node hash locks is correctly assigned to P3 before support is claimed. |
| Project/profile configuration | `PASS` | Two non-empty mappings are a configuration conflict regardless of CLI overrides, matching tagged `read_project_flags`; the plan no longer presents them as a precedence chain. |
| Environment aliases | `PASS` | The scanner checks configured current and legacy aliases before Core's internal alias propagation. Rejecting simultaneous configured aliases even when equal is a deterministic, stricter regulated-product policy and avoids ambiguous configuration ownership. |
| Exact command sequence | `PASS` | Only optional `deps` followed by one named-selector `build` is `READY`; all other command classes have explicit dispositions and `source freshness` remains a separate deferred evidence type. |
| Exact `deps` argv | `PASS` | It receives warning promotion, JSON writing, JSON/info file logs, usage opt-out, artifact-upload opt-out, ordinal-local log path, and the exact rotation size. It receives no selector or target path and requires no execution artifact. |
| Exact `build` argv | `PASS` | It receives the same shared policy plus one approved selector and an ordinal-local target path. No free-form selector, flags, command fragments, vars, upload, or paths enter through the App, Job parameters, or AI. |
| Warning/empty execution | `PASS` | Both named warning events are promoted. Explicit `warn_error`, conflicting warning sources, and ephemeral-only/empty result arrays fail closed and cannot become Observable. |
| Usage and artifact upload | `PASS` | Both ordinals explicitly use `--no-send-anonymous-usage-stats` and `--no-upload-to-artifacts-ingest-api`; `DO_NOT_TRACK` truth values and configured aliases are included in scanner resolution. |
| Primary artifact pair | `PASS` | Exact manifest v12/run-results v6 schemas, Core version, adapter type where available, `args.which`, invocation/ordinal binding, non-empty unique results, and exact BuildTask collection resolution are all required. Unsupported equality keys are correctly excluded. |
| Incomplete primary artifacts | `PASS` | Manifest-only can be partial inventory without node rows; run-results-only cannot be trusted without inventory and is invalid; neither-file cases are split by same-build start evidence. |
| Capture-state precedence | `PASS` | Retrieval is first classified as retrieved, confirmed absent, or unavailable. The ordered capture predicates are exclusive, conservative for indeterminate access, and preserve an outer attempt for pre-dbt failure. |
| Structured-log states | `PASS` | `UNAVAILABLE`, `NOT_INITIALIZED`, `TRUNCATED`, `MALFORMED`, `MISSING`, `UNKNOWN_VERSION`, and `VALID` distinguish retrieval, pre-logger failure, rotation loss, structural contradiction, missing A001 after logger start, unknown version, and qualified parsing. The actual version is retained when present; the state carries explicit absence/damage semantics otherwise. |
| Inventory/result semantics | `PASS` | Manifest resources remain inventory. Only a valid run-result row creates execution state; unmatched inventory is `NO_RESULT_RECORDED`, and Lakeflow, invocation, node/test, collector, and capture outcomes remain separate. |
| Regulated evidence boundary | `PASS` | Curated fields are allowlisted; raw SQL/code/messages/vars/events are excluded; secret scrubbing is only defense in depth; diagnostic evidence is separately restricted and bounded. |
| Documentation contract | `PASS` | D2 has explicit homes for supported commands/artifacts, resolved flags/paths, command templates/conflicts, artifact/log fields, capture states, support matrix, egress, and recovery. Subject-accuracy review occurs before Diataxis/readability passes. |

## P0-P10 dbt planning-contract matrix

The verdicts below assess whether each part has a sufficient dbt contract and future acceptance gate. They do not claim the later implementation evidence already exists.

| Part | Planning-contract verdict | Required evidence at the named part gate |
|---|---|---|
| P0 — Product contract | `PASS` | Record all third re-reviews and resolution, then satisfy the repository commit/push gate. No additional dbt contract edit is required. |
| P1 — Capture library | `PASS` | Implement full schema validation, standalone/pair invariants, every artifact/log/capture fixture in line 436, field allowlists, and parser qualification. |
| P2 — Collector and reconciliation | `PASS` | Prove closed-file bounds, independent per-ordinal log state, quarantine, total capture precedence, idempotent AttemptKey writes, and reconciliation stability. |
| P3 — Bundle installer | `PASS` | Produce reproducible full hash locks and exact accepted build-only/deps-plus-build argv; reject unsupported/conflicting scanner inputs before mutation. |
| P4 — App read-only MVP | `PASS` | UI/query fixtures must preserve inventory versus result and Job/invocation/node/test/collector/capture distinctions without raw evidence or `msg`. |
| P5 — Job onboarding | `PASS` | Scanner fixtures must prove deterministic state/code/patch for conflicts, aliases, `DO_NOT_TRACK`, flags, paths, upload, commands, selector, and vars. |
| P6 — Controlled actions | `PASS` | Preserve the pre-bound immutable command/selector contract; no person or AI can supply a dbt command, selector, vars, flags, or paths. |
| P7 — Security and operations | `PASS` | Complete field classification, raw-evidence denial/deletion, adversarial string, retention, and egress tests; do not treat dbt masking as DLP. |
| P8 — Bounded live proof | `PASS` | Within the approved cost envelope, prove exact runtime/dependency/schema/log evidence, all required capture paths, one real selector, and final stopped/clean inventory. |
| P9 — Optional intelligence | `PASS` | Run the core install/capture/operation suite with AI disabled; any Genie/MCP path remains advisory and calls the deterministic validator. |
| P10 — Private alpha | `PASS` | Classify every partner Job against the closed matrix and complete repeatable install/upgrade/uninstall evidence without implicitly expanding support. |

## File-set result

| File | Verdict | dbt result |
|---|---|---|
| `README.md` | `PASS` | Artifact-first, customer-local, deterministic, and restricted-diagnostic principles remain correct. |
| `AGENTS.md` | `PASS` | Arbitrary dbt input, active Volume logging, unsafe evidence, floating dependencies, and AI enforcement remain prohibited. |
| `docs/index.md` | `PASS` | Routes readers to the normative plan, ADR, reviews, and source register. |
| `docs/decisions/0001-private-app-bundle.md` | `PASS` | The App does not execute dbt; the observed Job owns execution and the deterministic collector remains outside the App. |
| `docs/plans/product-plan.md` | `PASS` | The two previously reopened ambiguities are now exact and fixture-backed; no dbt contract regression remains. |
| `docs/plans/review-process.md` | `PASS` | Independent immutable review, finding lifecycle, and dbt responsibilities across P0-P10 are adequate. |
| `docs/plans/documentation-plan.md` | `PASS` | The D2 information architecture and six-pass review sequence cover the final flag, artifact, capture, logging, security, and recovery contracts. |
| `docs/research/source-register.md` | `PASS` | Current official docs, exact tagged Core/adapter sources, schemas, wheel/hash evidence, release watch items, and refresh triggers support the decisions. |
| `docs/reviews/p0-planning-baseline/resolution.md` | `PASS` | The baseline 0.4 rows accurately describe `DBT-P0-002`, `DBT-P0-003`, `DBT-P0-004`, and the later implementation evidence. |

## Final disposition

- `DBT-P0-002`: resolved.
- `DBT-P0-003`: resolved.
- `DBT-P0-004`: resolved with no regression.
- Previously resolved dbt findings: no regression.
- New dbt findings: none.
- dbt specialist re-review verdict for frozen baseline 0.4: `PASS`.
