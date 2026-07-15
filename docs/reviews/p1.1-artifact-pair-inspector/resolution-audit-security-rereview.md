# Security and truthful-claims re-review: P1.1 final resolution

## Audit record

| Field | Value |
| --- | --- |
| Audited commit | `19368bd44ae6e182f647907825ceedec4e782fcc` |
| Audited tree | `19fd085e834eb191924ad221866d1e392f9180e2` |
| Immediate parent | `b0e5b06d3895b77f356ff05c36d1ca22847f2b1e` |
| Frozen source named by the resolution | `cff8bbcd808ff7e13a7ead182543a2564cd04ff6` |
| Audit date | 2026-07-16 |
| Audit scope | Focused closure check for `RESSEC-P1.1-001` |
| Verdict | **PASS** |
| Cloud activity | None. No Azure or Databricks authentication, API, App, Job, warehouse, cluster, serverless-compute, Unity Catalog, or other cloud call was made. No paid compute was started. |

## Executive verdict

`RESSEC-P1.1-001` is closed at exact commit `19368bd`. The corrected accepted-product-contract sentence now separates the two authorities accurately:

- the manifest compatibility condition is `adapter_type=databricks`; and
- the supported collections, resource types, and native status families come from pinned dbt Core 1.11.12 `BuildTask`, `RunStatus`, and `TestStatus` semantics.

The resolution no longer calls that contract a Databricks `build` resource/status matrix. Its statement remains consistent with the authoritative dbt review, which records dbt Core 1.11.12, manifest v12, run-results v6, adapter `databricks`, and command `build` as distinct parts of the compatibility row.

The correction introduces no scope or truthful-claims regression. P1.1 remains only the offline-after-installation local artifact-pair inspection slice. The resolution still expressly declines claims of a live Databricks collector, complete capture, qualified production runtime, disconnected distribution, or Marketplace release. It also continues to say that native result counts are not dbt success, Lakeflow task state, or capture completeness.

## Exact scope and hashes

Commit `19368bd` changes exactly one tracked file:

`docs/reviews/p1.1-artifact-pair-inspector/resolution.md`

The diff changes only the attribution sentence in the accepted product contract. Exact SHA-256 values at the audited commit are:

| File | SHA-256 |
| --- | --- |
| `docs/reviews/p1.1-artifact-pair-inspector/resolution.md` | `930528d8d7009e9787d824b4b45941a37e005da88cf24729ae222f1aa6b277b4` |
| `docs/reviews/p1.1-artifact-pair-inspector/dbt-core-rereview-4.md` | `316efb6850d7759a2fdfa4a1d61cf164b0d79778899770dcb103746cec4d703c` |
| `docs/reviews/p1.1-artifact-pair-inspector/resolution-audit-security.md` | `d8f1b797e3e17fcd6351bce22c9ac0cd512c19c396c410f61d34a4203832b6f4` |
| `docs/reviews/README.md` | `275e28fc30017f155305257cf621be85afc843522d44520dcb397f13b8d483ba` |

The three frozen aggregate hashes correctly remain:

| Frozen input | SHA-256 |
| --- | --- |
| Capture implementation and gates | `eed53519381de61685832eaf61e713eec0f8ad0b45a37fccd3e0b563a12024ce` |
| P1.1 developer documentation | `3731146dfe3890192c74f23fc39e207b0df714433369afb2973a63f9c32ae6f6` |
| Latest authoritative reviews | `d8225ab1886dcff00a5f791dc718381ec23e638f2705e0ebd0d37730b61c5625` |

Those aggregate hashes need not change. The resolution explicitly places itself and the review index outside the frozen inputs, and the commit modifies only the resolution. The frozen-input table and its boundary statement are byte-identical to the parent. The resolution's own file hash changed, as expected, and is recorded separately above.

## Focused checks

The following local, no-cloud checks passed against exact commit `19368bd`:

- `git diff-tree --no-commit-id --name-status -r 19368bd` showed only the resolution modification.
- The parent-to-commit diff showed a one-sentence replacement and no other content change.
- The replacement contains the separate `adapter_type=databricks` condition and exact dbt Core `BuildTask` plus `RunStatus`/`TestStatus` attribution.
- The superseded phrase `exact Databricks build resource/status matrix` is absent.
- The authoritative `dbt-core-rereview-4.md` at the audited commit confirms the pinned `BuildTask.RUNNER_MAP`, `RunStatus`, `TestStatus`, adapter, command, and schema semantics.
- The production nonclaim sentence remains present without modification.
- The frozen-input boundary remains present, and its table plus boundary statement are byte-identical to the parent.
- `git diff --check 19368bd^ 19368bd` passed.

No source, runtime, package, Bundle, or cloud object was edited or exercised in this re-review.

## Finding disposition

| Finding | Previous state | Re-review result |
| --- | --- | --- |
| `RESSEC-P1.1-001`: resource/status semantics were attributed to Databricks rather than dbt Core | `CHANGES_REQUIRED` | **Closed.** Attribution is accurate, authority boundaries are explicit, and no adjacent claim regressed. |

## Final verdict

**PASS.** The exact correction requested by `RESSEC-P1.1-001` is complete at `19368bd44ae6e182f647907825ceedec4e782fcc`. No new finding was identified in the focused scope.
