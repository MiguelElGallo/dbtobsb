# Security/compliance documentation re-review 2: P1.1 custody page split

- Date: 2026-07-15
- Reviewer: independent regulated-industry security/compliance documentation reviewer
- Immutable reviewed commit: `7ce722cddfed42f1e96741bb07b6cd8762127f22`
- Prior finding: `DOCSEC-P1.1-001`
- Prior closure report: `documentation-security-rereview.md`
- Prior closure commit: `3665590ea9d9cfd65fc695b9c6cf0a18493fc077`
- Re-review verdict: **PASS**
- Cloud/authentication activity: none
- Rendered-site/WCAG validation: deferred because no documentation site or rendered publication artifact exists

## Executive verdict

`DOCSEC-P1.1-001` remains fully closed after the custody content split. The new
how-to owns the ordered real-work controls: approved owner/host/storage,
least-privilege access, all-copy handling, ordinary and exceptional support,
retention, legal hold, deletion consequence, and a closing checklist. The
renamed explanation owns the conceptual model: raw-field sensitivity, exact
CLI/API data flow, transient in-process parsing, safe output versus
declassification, caller custody, and workstation-local versus future
Databricks-local scope.

Warnings and API/CLI references route readers to the action page before real
files are substituted, while the action page and explanation link to each other
and to the machine contract. The implemented P1.1 page registry now gives both
pages an audience, dependency, accountable owners, prerequisites, next routes,
search terms, and required evidence. No control from the accepted closure was
lost or weakened, and no new source-documentation security/compliance defect was
found.

## Immutable scope and hashes

The worktree was clean and `HEAD` matched
`7ce722cddfed42f1e96741bb07b6cd8762127f22` before review and validation. No
reviewed source or prior report was edited. This report is outside the frozen
input.

The split source set, in aggregate order, is:

1. `README.md`
2. `capture/README.md`
3. `docs/index.md`
4. `docs/developers/index.md`
5. `docs/developers/tutorials/inspect-an-artifact-pair.md`
6. `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md`
7. `docs/developers/how-to/handle-raw-dbt-artifacts-safely.md`
8. `docs/developers/reference/cli-report-and-exit-codes.md`
9. `docs/developers/reference/python-api.md`
10. `docs/developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md`
11. `docs/developers/explanation/raw-artifact-custody.md`
12. `docs/evidence/p1.1-local-artifact-pair-2026-07-15.md`
13. `docs/plans/documentation-plan.md`

The API/CLI data-flow set, in aggregate order, is:

1. `capture/src/dbtobsb_capture/cli.py`
2. `capture/src/dbtobsb_capture/inspector.py`
3. `capture/src/dbtobsb_capture/contracts.py`
4. `capture/src/dbtobsb_capture/schemas/artifact-pair-report-v1.json`
5. `capture/src/dbtobsb_capture/schemas/manifest-v12.json`
6. `capture/src/dbtobsb_capture/schemas/run-results-v6.json`

The validation set, in aggregate order, is:

1. `capture/tests/test_documentation.py`
2. `scripts/check_capture.sh`
3. `scripts/check_markdown_links.py`
4. `capture/pyproject.toml`
5. `capture/uv.lock`
6. `.github/workflows/capture.yml`

Each aggregate is SHA-256 over the literal `shasum -a 256` output for its
listed files in the listed order:

| Input | SHA-256 |
| --- | --- |
| Split source set | `06c829fea2af06119d6282ebb0b1f0e515bdaf174c303cb7e2dc94bda23bf769` |
| API/CLI data-flow set | `a4278015ee3a379303d6464844c4c08a95ddb3537f9a6bf6612eedf398b19ef2` |
| Validation set | `5e4f8b0f494ce35f0e81db6bcee0a0aa852f606059261d1a747bf8ddf30883e4` |
| Action-oriented raw-artifact how-to | `59f10d13d45d85a13eb4d903bfc76e245621f09d13348b2c8b1676af46fedd46` |
| Conceptual raw-custody explanation | `653d6befeb6791974362e5ceb29cedd14980cf92b01a92f4eb2981e1c822b990` |
| Documentation plan and page registry | `b753b2d568e246bceefefe806d1ebd5bb47eadf8e7a32d95a557f03471e0623e` |
| Preserved first security re-review | `6c9fb696eb2d5d6d599834581e27340585d01ebf6960d30e433b485b1c42e5a5` |
| Preserved original security review | `77358a7d058059886b4108ecdd0b71e79fa5901b7519df3af9408b4c0c1f6684` |
| Vendored Core 1.11.12 manifest v12 schema | `b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3` |
| Vendored run-results v6 schema | `1783bda55656bde624ed67640375640a2919a8608e2505e3a02c04cd139e2cdf` |

## Closure continuity after the split

| Required boundary | Split-page evidence | Result |
| --- | --- | --- |
| Warning before real input | README, capture README, documentation index, tutorial, invalid-pair how-to, CLI reference, and Python reference all route to the handling how-to before or beside real-artifact use. Reader warnings still name Personal Data, secrets, SQL, messages, paths, topology, and identities. | **Preserved** |
| Approved custody and least privilege | The action how-to requires an accountable data/security owner, a policy-approved execution host and storage location, least-privilege access, an approved evidence lifecycle, and an approved installed dependency source. If the boundary or owner is unclear, the reader must stop before reading the files. | **Preserved and strengthened** |
| Every raw copy remains governed | Originals, extracts, temporary copies, and backups must stay within approved storage with required encryption, access logging, endpoint controls, and transfer restrictions. Raw files or fragments must not enter source control, chat, an ordinary ticket, or an unapproved transfer. | **Preserved** |
| Exact CLI/API data flow | The explanation says the CLI opens and reads the two caller files, the API receives caller bytes and opens no path, schemas are installed and checksum-pinned, raw input receives transient in-process parsing, the report retains no raw bytes, and no durable raw-file copy or external transfer is created. Caller files are not deleted, encrypted, relocated, governed, or made compliant. | **Preserved and clarified** |
| Safe report is not declassification | The explanation now says explicitly that the allowlisted report is a separate lower-data output, not a declassification decision for the raw evidence. Caller-side encryption, access, backup, retention, deletion, and legal hold remain independent controls. | **Strengthened** |
| Ordinary support payload | Both the action how-to and invalid-pair how-to limit ordinary support to product version, safe command shape, exit/static issue code, and the allowlisted report. The action page explicitly excludes local paths, raw fragments, SQL, messages, identifiers, and other artifact content. | **Preserved and clarified** |
| Exceptional restricted evidence | An accountable support owner must require the exception; a separately approved process must name the authorized recipient, approved transfer method, access boundary, and retention/deletion decision before transfer. P1.1 still has no evidence-upload endpoint. | **Preserved** |
| Retention, deletion, and legal hold | The action page applies the approved retention/legal-hold decision to originals, extracts, temporary copies, and backups. Deletion occurs only when the approved schedule permits and no hold applies. It explicitly says P1.1 neither performs nor attests deletion and requires outcomes to be recorded through the customer's control process. | **Preserved and strengthened** |
| Workstation-local versus Databricks-local | The explanation states that no-network processing is local to the operator host but does not prove workstation, backup, or support compliance. The target remains data and compute inside the customer's Databricks environment; collector/archive storage, runtime retention/deletion, uninstall, and related controls remain later reviewed work. | **Preserved** |
| Authoritative dbt provenance | The conceptual explanation retains the official dbt artifact, manifest, and run-results references and the project source-register anchor. Exact tagged schemas remain vendored and checksum-pinned. | **Preserved** |
| Page registry and ownership | The implemented P1.1 registry includes separate rows for the action how-to and conceptual explanation. Each row binds audience/dependency, D1P owners, prerequisite/next routes, search terms, and evidence. The family row requires input-custody/support/lifecycle controls and an explicit non-claim of Databricks-local custody. | **Added and passed** |

## Mode separation and navigation assessment

The content split does not fragment the security contract:

- the **how-to** begins with an operational outcome, prerequisites, a stop
  condition, four ordered steps, verification, and related conceptual/reference
  routes;
- the **explanation** answers why a safe report does not make raw evidence safe,
  separates inspection from custody, and explains the two meanings of local;
- entry-point warnings link to the action page, the action page links to the
  explanation and references, and the explanation links back to the action
  page; and
- the developer index presents the handling task under outcomes and the custody
  model under boundaries, so a regulated reader can find either need directly.

No control is available only through an unrelated review record or planning
page. The page registry is governance evidence and not a substitute for the
reader-facing warnings and task, which are present.

## API/CLI implementation check

The underlying data-flow implementation did not change from the accepted first
re-review and still supports the split wording:

- CLI input is read-only, bounded, regular-file-only, and descriptor-closing;
- the API accepts bytes, performs bounded transient decoding/parsing and schema
  validation in process memory, and opens no caller path;
- ordinary output is the closed allowlisted report or static safe error text;
- the inspection path contains no raw-artifact write, upload, runtime network,
  dbt, Databricks, environment, clock, or subprocess operation; and
- no caller-file deletion or deletion attestation is implemented.

The direct API/CLI pages still use the concise phrase “does not persist, copy,
upload, delete, or govern.” Their linked how-to and explanation now remove the
only plausible ambiguity: the guarantee is no durable raw-artifact copy or
external transfer, while transient in-process parsing necessarily occurs. No
memory-zeroization, confidential-computing, or absence-of-process-residency
claim is made or inferred.

## Authoritative source recheck

The LLM-oriented dbt URLs were unavailable through the documentation fetcher,
so the re-review failed safe to the current official HTML pages and exact
first-party tagged schemas. All five selected URLs returned HTTP 200 on
2026-07-15:

- [dbt artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts)
- [manifest.json](https://docs.getdbt.com/reference/artifacts/manifest-json)
- [run_results.json](https://docs.getdbt.com/reference/artifacts/run-results-json)
- [Core 1.11.12 manifest v12 schema](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/manifest/v12.json)
- [Core 1.11.12 run-results v6 schema](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/run-results/v6.json)

The current official pages continue to support the sensitivity language:
artifacts carry environment and invocation metadata; manifest contains project
inventory, configuration, paths, and compiled context; run-results contains
command arguments, unique IDs, messages, adapter responses, compiled code, and
relation names. “Can contain” remains the accurate wording; the docs do not
categorically classify every field as Personal Data or a secret.

## Local validation

The exact reviewed commit passed:

```text
uv lock --check --project capture
passed

scripts/check_markdown_links.py --revision 7ce722cddfed42f1e96741bb07b6cd8762127f22
tracked_markdown_files=117
local_links=160
fragments=48
errors=0

scripts/check_markdown_links.py --revision 80d0c0a6dd0e139ec4b8e040c36f99983931b06f
tracked_markdown_files=117
local_links=160
fragments=48
errors=0

scripts/check_capture.sh
94 tests passed
revision-bound Markdown link check: passed
Ruff check and format: passed
ty: passed
report-schema and fixture regeneration: passed
runtime-only install and checked-in example: passed
wheel build and isolated installed CLI: passed
DBTOBSB_CAPTURE_CHECK_PASSED

Bash syntax and ShellCheck for scripts/check_capture.sh
passed

git diff --check 3665590..7ce722c
passed
```

The strengthened documentation tests bind the API signature, public fields,
limits, statuses, example and output, every issue classification/action/recovery
fragment, real-artifact warning routes, required action-page controls, and the
conceptual transient-parsing/declassification/Databricks-local boundaries.

The new link checker reads blobs from the named immutable Git revision, excludes
fenced code and external schemes, rejects repository escapes and missing files,
and validates ATX and explicit-ID fragments. The evidence record binds its
published `117`/`160`/`48` result to source revision
`80d0c0a6dd0e139ec4b8e040c36f99983931b06f`; the same result reproduced at the
final reviewed commit.

## Publication and secret safety

A scoped tracked-source scan found no likely live Databricks host, local
`/Users` or `/Volumes` path, email address, access token, private key,
credential assignment, or live-style workspace/account identifier in the split
source set. Reader routes and expected reports contain no `CANARY_*` value. The
how-to's `/approved/path/...` command is an explicit policy-bound placeholder,
not a captured local path or deployable identifier.

No MkDocs, Zensical, Docusaurus, Jekyll, or equivalent site configuration and
no rendered site artifact exists. Source paths and fragments pass, but browser
navigation, generated search/metadata, screenshot/OCR content, responsive
layout, keyboard/focus/contrast, screen-reader behavior, and WCAG conformance
remain untested. This report makes no rendered-site, accessibility, public
release, or WCAG claim. Reachable history, ignored files, CI logs/artifacts, and
future generated publication files remain part of the later release gate.

## Retained later gates

The split correctly leaves these controls outside P1.1 rather than presenting
them as complete:

1. disconnected first-installation distribution;
2. real Azure Databricks runtime and archive qualification;
3. implemented product collector/archive/derived-row/backup/uninstall
   retention and deletion; and
4. a complete rendered documentation site followed by publication,
   accessibility, and WCAG 2.2 validation.

## Verdict

**PASS**

`DOCSEC-P1.1-001` remains closed at immutable commit
`7ce722cddfed42f1e96741bb07b6cd8762127f22`. The action-oriented how-to,
conceptual explanation, entry warnings, API/CLI boundary, support and lifecycle
rules, two-local-scopes distinction, authoritative sources, and implemented page
registry form a complete and internally consistent regulated-industry source
documentation contract for this P1.1 slice.
