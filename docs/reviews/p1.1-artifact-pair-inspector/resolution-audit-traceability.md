# P1.1 final resolution and review-index traceability audit

- Audited commit: `74a9cdf8e2b9da44015a134fffc6b13d66395453`
- Audited tree: `106aa4421db895ae45623aefb72f24b7bab1ac14`
- Immediate parent: `a00d6abde507210948b5fb7eaf566448e4ad6bc7`
- Audited files: `docs/reviews/p1.1-artifact-pair-inspector/resolution.md` and `docs/reviews/README.md`
- Audit date: 2026-07-16
- Audit mode: immutable Git-blob traceability and recorded-evidence verification; no audited file, product source, cloud resource, or paid compute was changed
- Verdict: **PASS**

## Executive verdict

The final P1.1 resolution and review index are internally consistent and traceable at exact commit `74a9cdf8e2b9da44015a134fffc6b13d66395453`.

All three frozen aggregate hashes reproduce exactly from their stated scopes and ordering. The reviewed source commit exists, is an ancestor of the resolution, and its frozen implementation and documentation inputs are unchanged through the audited commit. Both authority tables contain the same nine reports in the same order with the same verdicts; every link resolves to a Git blob and every displayed verdict matches the target report's declared current verdict.

The retained `CHANGES_REQUIRED` text is visible history, not a hidden current verdict. The directory contains 15 superseded reports whose actual verdict was `CHANGES_REQUIRED` and three passing re-review records that quote earlier `CHANGES_REQUIRED` evidence. None of the nine authoritative rows currently resolves to `CHANGES_REQUIRED` or `BLOCKER`.

The resolution's quality claims are supported by the frozen evidence and latest reports. No unsupported claim or integrity break was found.

## Immutable audit identity

| Item | SHA-256 at `74a9cdf8e2b9da44015a134fffc6b13d66395453` |
| --- | --- |
| Final resolution | `8cef3ae575ee7985eb369dc17cd19dd1ef69553f1a1c3956a80b5d2136e2f308` |
| Review index | `275e28fc30017f155305257cf621be85afc843522d44520dcb397f13b8d483ba` |

The resolution commit changes only those two files relative to parent `a00d6abde507210948b5fb7eaf566448e4ad6bc7`: it adds the resolution and updates the index. The resolution and index are deliberately outside all three frozen aggregates, so this separate audit does not create a circular input.

## Frozen aggregate reproduction

Each aggregate was independently reconstructed from blobs at the audited commit. For every scoped path, the audit generated the literal record emitted by:

```text
shasum -a 256 <relative-path>
```

It then SHA-256 hashed the complete newline-delimited record stream without reformatting it.

| Frozen input | Exact order rule | Records | Recorded | Reproduced | Result |
| --- | --- | ---: | --- | --- | --- |
| Capture implementation and gates | All tracked files under `capture/`, plus `.github/workflows/capture.yml`, `scripts/check_capture.sh`, and `scripts/check_markdown_links.py`, sorted by path | 48 | `eed53519381de61685832eaf61e713eec0f8ad0b45a37fccd3e0b563a12024ce` | `eed53519381de61685832eaf61e713eec0f8ad0b45a37fccd3e0b563a12024ce` | **PASS** |
| P1.1 developer documentation | The 14 explicitly reconstructed files below, sorted by path | 14 | `3731146dfe3890192c74f23fc39e207b0df714433369afb2973a63f9c32ae6f6` | `3731146dfe3890192c74f23fc39e207b0df714433369afb2973a63f9c32ae6f6` | **PASS** |
| Latest authoritative reviews | The nine verdict-table reports below, in table order rather than path order | 9 | `d8225ab1886dcff00a5f791dc718381ec23e638f2705e0ebd0d37730b61c5625` | `d8225ab1886dcff00a5f791dc718381ec23e638f2705e0ebd0d37730b61c5625` | **PASS** |

The 48-file rule was reproduced with this immutable path enumeration:

```text
git ls-tree -r --name-only 74a9cdf8e2b9da44015a134fffc6b13d66395453 \
  -- capture .github/workflows/capture.yml \
  scripts/check_capture.sh scripts/check_markdown_links.py \
  | LC_ALL=C sort
```

The exact 14-file documentation order was:

```text
README.md
capture/README.md
docs/decisions/0002-correct-p1.1-invocation-recovery-text.md
docs/developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md
docs/developers/explanation/raw-artifact-custody.md
docs/developers/how-to/diagnose-an-invalid-artifact-pair.md
docs/developers/how-to/handle-raw-dbt-artifacts-safely.md
docs/developers/index.md
docs/developers/reference/cli-report-and-exit-codes.md
docs/developers/reference/python-api.md
docs/developers/tutorials/inspect-an-artifact-pair.md
docs/evidence/p1.1-local-artifact-pair-2026-07-15.md
docs/index.md
docs/plans/documentation-plan.md
```

This is exactly the resolution's three entry points, eight `docs/developers/` pages, Decision 0002, P1.1 evidence, and documentation plan.

## Reviewed source binding

The resolution names source commit `cff8bbcd808ff7e13a7ead182543a2564cd04ff6`. Git object verification produced:

```text
commit  cff8bbcd808ff7e13a7ead182543a2564cd04ff6
tree    a3802ab9b14a1dc3b7f18f90255eee349fdeecbb
parent  8711aa803016b5d732553756c5e71542e0a928bf
subject docs: record p1.1 usability closure
```

That commit exists and is an ancestor of `74a9cdf8e2b9da44015a134fffc6b13d66395453`. A path-restricted Git comparison confirms that every file in the 48-file implementation/gate scope and 14-file documentation scope is byte-identical between `cff8bbc…` and `74a9cdf…`.

Commit `a00d6abde507210948b5fb7eaf566448e4ad6bc7` then adds the three final product re-reviews without changing either source scope. All nine frozen review files are byte-identical between `a00d6ab…` and `74a9cdf…`. The final commit adds only the out-of-scope resolution and index.

## Nine-report link, verdict, and provenance audit

The following is the exact table order. “Reviewed source” records the immutable commit actually declared by the target report; specialist reports are not misrepresented as all having reviewed `cff8bbc…`.

| Review lens | Target report | Report SHA-256 | Reviewed source | Index verdict | Target verdict | Result |
| --- | --- | --- | --- | --- | --- | --- |
| Databricks platform/security | `databricks-rereview-4.md` | `b5d89552394b5e5ad047d32017e47bb9d930f1f835e9f58974a910ceede5d024` | `cff8bbcd808ff7e13a7ead182543a2564cd04ff6` | `PASS_WITH_FOLLOW_UP` | `PASS_WITH_FOLLOW_UP` | **PASS** |
| dbt Core/artifact contract | `dbt-core-rereview-4.md` | `316efb6850d7759a2fdfa4a1d61cf164b0d79778899770dcb103746cec4d703c` | `cff8bbcd808ff7e13a7ead182543a2564cd04ff6` | `PASS_WITH_FOLLOW_UP` | `PASS_WITH_FOLLOW_UP` | **PASS** |
| Product usability/onboarding | `usability-rereview-4.md` | `8e13be26f5d5caa2708c88f6e9650ff823ab92dac7de5401127488cdbec388e4` | `cff8bbcd808ff7e13a7ead182543a2564cd04ff6` | `PASS_WITH_FOLLOW_UP` | `PASS_WITH_FOLLOW_UP` | **PASS** |
| Diátaxis information architecture | `documentation-ia-rereview-2.md` | `0ac0ef4e9e29bbc4ca6f3005d630b836934e28ab85cdc159cf2712b668cd7c44` | `7ce722cddfed42f1e96741bb07b6cd8762127f22` | `PASS_WITH_FOLLOW_UP` | `PASS_WITH_FOLLOW_UP` | **PASS** |
| Security/compliance documentation | `documentation-security-rereview-2.md` | `914af86b68d7cf578f7f8a532c35fdeca2b74e23b733d295d8c850bbdbd6454a` | `7ce722cddfed42f1e96741bb07b6cd8762127f22` | `PASS` | `PASS` | **PASS** |
| FastAPI-style writing | `documentation-style-rereview-2.md` | `d0d531b5724ef641279730280745b7a8a75a4fe50bb145f502f0af88e45d5791` | `7ce722cddfed42f1e96741bb07b6cd8762127f22` | `PASS` | `PASS` | **PASS** |
| dbt subject-matter documentation | `documentation-dbt-rereview.md` | `b824d7721e442678b9843832cb87bdbd6c3e186fec1a976310a76678a9480745` | `2367a05d4e9ddb763cc52a3b7090c4099a639631` | `PASS` | `PASS` | **PASS** |
| Documentation usability/accessibility | `documentation-usability-rereview-2.md` | `b2326a65d2d2babe8b49e55fd43950b28c420c07d7eed755b09f7cb854cf1a3d` | `8711aa803016b5d732553756c5e71542e0a928bf` | `PASS_WITH_FOLLOW_UP` | `PASS_WITH_FOLLOW_UP` | **PASS** |
| Final reader-journey consistency | `documentation-final-rereview.md` | `e09e54fda8185b44fd327a4256fd040fce8b3fc1d479766da484e7d27dd6150e` | `2367a05d4e9ddb763cc52a3b7090c4099a639631` | `PASS` | `PASS` | **PASS** |

For every row:

- the relative link in `resolution.md` resolves from `docs/reviews/p1.1-artifact-pair-inspector/`;
- the relative link in `docs/reviews/README.md` resolves from `docs/reviews/`;
- both tables use the same report, order, and verdict; and
- the report blob declares the displayed verdict.

The earlier specialist source commits do not create an unrecorded gap. Changes after `7ce722c…` were the overwrite-safe invocation/dbt-compatibility correction reviewed at `2367a05…`, the GFM union rendering correction reviewed at `8711aa8…`, and additive review records. The final Databricks, dbt Core, and product-usability reports at `cff8bbc…` rechecked those changed machine, security, documentation, and onboarding surfaces with the complete gate. No developer page was removed, the documentation plan did not change, and the later changes strengthen rather than reverse the accepted IA, custody, or writing controls.

`documentation-final-rereview.md` validated the preceding six-row authority table at `2367a05…`; it does not claim to have audited the later nine-row index. The resolution expressly places its own index outside the frozen review aggregate and requires this separate final audit. The nine-row verification above closes that intended non-circular step.

## Hidden-failure audit

A directory-wide exact-token search at `74a9cdf…` found `CHANGES_REQUIRED` in 18 files:

- 15 superseded reports have an actual `CHANGES_REQUIRED` verdict; and
- three passing re-reviews quote or count that earlier failed history.

Within the nine authoritative reports, only two contain the token:

- `documentation-dbt-rereview.md` identifies its linked prior review as `CHANGES_REQUIRED` and then declares zero open findings and `PASS`; and
- `documentation-final-rereview.md` explicitly verifies preservation of failed history before declaring its finding closed and `PASS`.

The other seven authoritative reports contain no `CHANGES_REQUIRED` token. Each current report declares no current defect or blocker, closes its named findings, and limits any `PASS_WITH_FOLLOW_UP` to later runtime, distribution, rendered-site, accessibility, compatibility, or release work. The index retains the failed files and explains that they are immutable history. No current `CHANGES_REQUIRED` or `BLOCKER` is hidden.

## Resolution-claim evidence ledger

This was a traceability audit of recorded gates, not a new product-gate execution. Each resolution claim maps to immutable evidence as follows:

| Resolution claim | Recorded evidence checked | Result |
| --- | --- | --- |
| 96 tests, including six executable documentation contracts and the full schema/resource/status/constructor/CLI/adversarial suite | `dbt-core-rereview-4.md` records the six-test documentation selection, 56-test artifact selection, seven-test CLI selection, and complete 96-test gate; `databricks-rereview-4.md` and `usability-rereview-4.md` independently record the same complete total. | **PASS** |
| Ruff lint/format and `ty` | The three final product reports record all three checks as passed at `cff8bbc…`. | **PASS** |
| Byte-identical generated schema/fixture checks | `dbt-core-rereview-4.md`, `databricks-rereview-4.md`, and `usability-rereview-4.md` record regeneration without drift; the fixture and schema sources are in the reproduced implementation aggregate. | **PASS** |
| Seven-package runtime-only environment, exact Python example, wheel, and isolated installed CLI | `usability-rereview-4.md` records exactly seven packages plus byte-identical CLI/API output; the final dbt and Databricks reports record the runtime-only, example, wheel, and installed-entry-point gates. | **PASS** |
| Bash syntax and ShellCheck | All three final product reports record `bash -n scripts/check_capture.sh` and ShellCheck as passed. | **PASS** |
| Deterministic Markdown path and fragment validation | The current full-gate records agree on 128 tracked Markdown files, 212 local links, 59 fragments, and zero errors. | **PASS** |
| Mutation, GFM rendering, safe-output, unsafe-input, raw-canary, and zero-socket/process probes | The FastAPI-style report records required mutations; documentation-usability and product-usability reports record local and GitHub GFM checks; the final Databricks report records safe static output, raw-canary exclusion, `socket_events=0`, and `process_events=0`; product usability records bounded unsafe-input behavior. | **PASS** |
| Recorded dependency vulnerability check | Frozen evidence states that `pip-audit==2.10.0` reported no known vulnerabilities for the runtime-only locked export on 2026-07-15. The resolution correctly describes this as the recorded past check, not a current vulnerability-free certification. | **PASS** |
| GitHub Actions hardening | Frozen `.github/workflows/capture.yml` grants `contents: read`, uses two full action commit SHAs, sets `CAPTURE_PYTHON_VERSION=3.12.3`, pins uv `0.11.28`, sets a ten-minute timeout, disables the uv cache, and has no upload step. | **PASS** |

The reports also preserve the qualification boundary: the local gate used available CPython 3.12.13 and does not qualify the planned Python 3.12.3/Linux Databricks runtime. The resolution retains that runtime work as a later blocking gate for broader product claims.

## Findings

No traceability, integrity, hidden-verdict, broken-link, hash-scope, or recorded-evidence defect was found in the final P1.1 resolution or review index at `74a9cdf8e2b9da44015a134fffc6b13d66395453`.

## Final verdict

**PASS**

The final resolution binds the exact accepted source, documentation, evidence, and nine current review verdicts without rewriting failed history. Its three frozen aggregates reproduce, its two out-of-scope authority files have explicit immutable hashes, and its acceptance and retained-gate claims match the recorded evidence.
