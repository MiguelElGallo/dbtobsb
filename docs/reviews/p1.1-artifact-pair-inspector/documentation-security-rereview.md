# Security/compliance documentation re-review: P1.1 raw artifact custody

- Date: 2026-07-15
- Reviewer: independent regulated-industry security/compliance documentation reviewer
- Immutable reviewed commit: `3665590ea9d9cfd65fc695b9c6cf0a18493fc077`
- Prior report: `documentation-security.md`
- Prior finding: `DOCSEC-P1.1-001`
- Prior verdict: **CHANGES_REQUIRED**
- Re-review verdict: **PASS**
- Cloud/authentication activity: none
- Rendered-site/WCAG validation: deferred because no documentation site or rendered publication artifact exists

## Executive verdict

`DOCSEC-P1.1-001` is resolved at the exact reviewed commit. A warning now
precedes real-artifact use in the repository README, tutorial, recovery how-to,
CLI reference, and Python reference. The new dedicated custody explanation
identifies the raw fields and sensitivity classes, distinguishes safe report
output from sensitive input custody, defines the CLI/API/persistence/transfer/
deletion boundary, assigns originals and copies to the caller's approved
lifecycle, restricts the ordinary support payload, and gives an explicit
separately approved exception for raw evidence.

The text also distinguishes workstation-local P1.1 inspection from the future
Databricks-local product. It does not claim that local inspection proves archive
collection, retention implementation, runtime qualification, air-gapped first
installation, or regulatory certification. No current source-documentation
security/compliance defect remains in this reviewed closure slice.

## Immutable scope and hashes

The worktree was clean and `HEAD` matched the immutable commit before checks.
No reviewed source or prior report was edited. This re-review report is outside
the frozen input.

The resolution source set, in aggregate order, is:

1. `README.md`
2. `capture/README.md`
3. `capture/examples/inspect_valid_fixture.py`
4. `capture/tests/test_documentation.py`
5. `docs/index.md`
6. `docs/developers/index.md`
7. `docs/developers/tutorials/inspect-an-artifact-pair.md`
8. `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md`
9. `docs/developers/reference/cli-report-and-exit-codes.md`
10. `docs/developers/reference/python-api.md`
11. `docs/developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md`
12. `docs/developers/explanation/raw-artifact-custody.md`
13. `docs/evidence/p1.1-local-artifact-pair-2026-07-15.md`

The implementation claim-check set, in aggregate order, is:

1. `capture/src/dbtobsb_capture/cli.py`
2. `capture/src/dbtobsb_capture/inspector.py`
3. `capture/src/dbtobsb_capture/contracts.py`
4. `capture/src/dbtobsb_capture/schemas/artifact-pair-report-v1.json`
5. `capture/src/dbtobsb_capture/schemas/manifest-v12.json`
6. `capture/src/dbtobsb_capture/schemas/run-results-v6.json`
7. `capture/pyproject.toml`
8. `capture/uv.lock`
9. `scripts/check_capture.sh`
10. `.github/workflows/capture.yml`

Each aggregate is SHA-256 over the literal `shasum -a 256` output for its
listed files in the listed order:

| Input | SHA-256 |
| --- | --- |
| Resolution source set | `1f4ec97b3a0f64b1243b93f362f6d684159cb0634e2cbebb30ca5d70a83b20a5` |
| Implementation claim-check set | `78371c621ba03fd0ab8ac49d65eb0a068fed8e596410df0ed772df72ed777078` |
| New raw-custody explanation | `8cddedf3f54c543831a017e453311458ffbe5f8723d38e9c59a8bc65392e2784` |
| Preserved prior security report | `77358a7d058059886b4108ecdd0b71e79fa5901b7519df3af9408b4c0c1f6684` |
| Vendored Core 1.11.12 manifest v12 schema | `b290bb419026be3fa361ead7f0d8e3bb0eb6bca8c3a3fb7971f5d252fd0825b3` |
| Vendored run-results v6 schema | `1783bda55656bde624ed67640375640a2919a8608e2505e3a02c04cd139e2cdf` |

## Finding closure

| Required closure | Evidence at `3665590ea9d9cfd65fc695b9c6cf0a18493fc077` | Result |
| --- | --- | --- |
| Warn before real-artifact use | README places the warning before its fixture command. The tutorial identifies its inputs as synthetic before installation and commands. The how-to warns before its real-path form. Both references repeat the boundary and link to the full custody explanation. | **Resolved** |
| Name raw sensitivity precisely | Reader text names Personal Data, credentials or other secrets, proprietary/raw/compiled SQL, adapter responses, messages, environment/configuration values, database/relation topology, local paths, and invocation/user/project/resource identities. | **Resolved** |
| Require approved custody and least privilege | The warning and custody page require policy-approved local storage, least-privilege access, applicable encryption, access logging, endpoint controls, and approved transfer restrictions. Raw files/fragments must not be committed, uploaded, pasted into chat, or attached to an ordinary support ticket. | **Resolved** |
| State exact inspector limits | The CLI is documented as opening two caller-supplied regular files and reading their bytes within the limit. The API receives caller bytes and opens no caller path. Inspection uses installed schemas, has no runtime network/dbt/Databricks call, and returns no raw bytes. It creates no persistent file copy or external transfer and does not delete, encrypt, relocate, govern, or make caller files compliant. | **Resolved** |
| Assign the complete caller lifecycle | Originals, extracts, copies, and backups remain under the customer's classification, encryption, access, retention, legal-hold, and deletion decisions. The inspector does not delete them or turn inspection into lifecycle enforcement. | **Resolved** |
| Bound ordinary and exceptional support | The ordinary payload is limited to product version, safe command shape, exit/static issue code, and the allowlisted report. Exceptional raw evidence requires a separately approved process with a named authorized recipient, approved transfer method, explicit access boundary, and retention/deletion decision. The docs explicitly say P1.1 has no evidence-upload endpoint. | **Resolved** |
| Separate the two meanings of local | The dedicated explanation says P1.1 runs on the operator's execution host and does not prove that workstation, backup, or support controls satisfy the future product boundary. It separately describes the target product as Databricks-local and leaves collector storage, runtime retention/deletion, archive retrieval, and uninstall to later reviewed parts. | **Resolved** |
| Ground the field/version boundary in first-party sources | The custody page links the official dbt artifact, manifest, and run-results references plus the repository source-register section. The pinned local schemas are byte-bound to the exact Core 1.11.12 tag and expose the documented sensitive fields. | **Resolved** |

## Code-to-document boundary verification

The implementation supports the documented external data-flow boundary:

- CLI `_read_regular_file` opens read-only, rejects non-regular/oversize inputs,
  reads into process memory, and closes the descriptor. It has no write path.
- `inspect_artifact_pair` accepts bytes, checks size/depth, decodes and parses
  them transiently in process memory, validates them against installed schemas,
  and returns only the closed report types.
- The report includes only schema/version/adapter/command/status counts or
  static issues. It retains no artifact bytes, SQL, messages, paths, topology,
  environment values, or resource/project/invocation identity.
- The capture package contains no runtime network, upload, dbt, Databricks,
  environment, clock, or subprocess access in this inspection path and does not
  delete caller files.

The custody table's “does not copy” statement is read in its labelled
persistence-and-transfer sense: no durable file copy or external transfer is
created. Parsing necessarily creates transient in-process representations. The
documentation does not claim secure memory zeroization, confidential-computing
isolation, or freedom from ordinary process-memory residency, and this review
does not infer any such control.

## Authoritative source recheck

The three current dbt Labs artifact pages and the two exact tagged GitHub schema
links returned HTTP 200 on 2026-07-15:

- [dbt artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts)
- [manifest.json](https://docs.getdbt.com/reference/artifacts/manifest-json)
- [run_results.json](https://docs.getdbt.com/reference/artifacts/run-results-json)
- [Core 1.11.12 manifest v12 schema](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/manifest/v12.json)
- [Core 1.11.12 run-results v6 schema](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/run-results/v6.json)

The current artifact overview identifies custom environment metadata,
invocation identity, project name, and user identity. The manifest reference
describes the complete project resource/configuration inventory and paths. The
run-results reference identifies command arguments, unique IDs, database
messages, adapter responses, compiled code, and relation names. Those sources
directly support the resolved sensitivity warning; they do not make every
artifact value Personal Data or a secret, so the docs correctly use “can
contain” rather than a categorical classification.

## Local checks

The exact commit passed:

```text
scripts/check_capture.sh
94 tests passed
Ruff check and format: passed
ty: passed
report-schema and fixture regeneration: passed
runtime-only install and checked-in example: passed
wheel build and isolated installed CLI: passed
DBTOBSB_CAPTURE_CHECK_PASSED

uv lock --check --project capture
passed

Bash syntax and ShellCheck for scripts/check_capture.sh
passed

independent tracked-Markdown occurrence scan
113 Markdown files; 133 local link occurrences;
41 fragment-bearing occurrences; 0 missing targets

selected first-party dbt source check
5 URLs; 5 returned HTTP 200

git diff --check for the resolution commit
passed
```

The four added executable documentation tests passed. They bind the displayed
Python program to the checked-in example, bind public limits/statuses to code,
bind every CLI issue row to the static registry and recovery route, and require
the sensitive-input/custody terms on every real-artifact route.

## Publication and secret safety

A scoped tracked-source scan found no likely live Databricks workspace host,
local `/Users` or `/Volumes` path, email address, long live-style account ID,
access token, private key, or credential assignment in the resolution source
set. No expected report or reader route contains a `CANARY_*` value. The raw
fixtures retain deliberate synthetic canaries and `example.invalid` identities
only in their fixture/generator/test boundary; the complete capture gate again
proved report non-disclosure.

All checked source links and fragments resolve. No MkDocs, Zensical,
Docusaurus, Jekyll, or equivalent site configuration and no rendered site
artifact exists. Therefore browser navigation, generated metadata/search
indexes, screenshot/OCR content, responsive behavior, keyboard/focus/contrast,
screen-reader output, and WCAG conformance remain explicitly untested. This is
a source-publication safety check, not a public-release or rendered-site
attestation. Reachable Git history, ignored files, CI logs/artifacts, and future
generated publication files still require their release gate.

## Retained later gates

The following remain outside this source-doc closure and are not represented as
completed controls:

1. a checksum-bound disconnected installation artifact before any air-gapped
   first-installation promise;
2. independently sanitized real Azure Databricks success, dbt failure,
   early-failure, cancellation, timeout, retry, and repair qualification;
3. implemented collector/archive/derived-row/backup/uninstall retention and
   deletion controls; and
4. a complete rendered documentation site followed by publication-safety,
   browser, accessibility, and WCAG 2.2 validation.

## Verdict

**PASS**

`DOCSEC-P1.1-001` is closed at immutable commit
`3665590ea9d9cfd65fc695b9c6cf0a18493fc077`. The reviewed documentation now
defines the raw-input sensitivity, caller custody/lifecycle, inspector
persistence/transfer/deletion limits, support exception, workstation-local
scope, future Databricks-local boundary, and authoritative dbt provenance
needed for this P1.1 regulated-industry documentation slice.
