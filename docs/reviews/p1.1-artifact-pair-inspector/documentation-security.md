# Security/compliance documentation review: P1.1 artifact-pair inspector

- Date: 2026-07-15
- Reviewer: independent regulated-industry security/compliance documentation reviewer
- Immutable reviewed commit: `1900cd01254837010d7d93bb0cd69cf0b98eb1b5`
- Verdict: **CHANGES_REQUIRED**
- Cloud/authentication activity: none
- Rendered-site/publication validation: deferred because no documentation site or rendered publication artifact exists

## Executive verdict

The P1.1 implementation and most of its documentation establish a strong
non-disclosure boundary for the normalized report: ordinary output is closed and
allowlisted, errors are static, caller paths and evidence fragments are not
echoed, inspection makes no runtime network call, and the fixtures are clearly
synthetic rather than Databricks runtime evidence.

The reader-facing documentation does not establish the corresponding custody
boundary for the **input** `manifest.json` and `run_results.json` files. The
first real-path procedure can be followed without first telling a regulated
operator that these raw dbt artifacts can contain Personal Data, secrets,
compiled or raw SQL, error text, adapter responses, environment metadata,
relation and project topology, local paths, and resource, user, project, or
invocation identifiers. It also does not say that the inspector leaves the
caller-owned source files in place or identify the required access, retention,
backup, deletion, and restricted-support handling boundary.

That omission can cause a reader to infer that a safe report makes the supplied
raw evidence safe to copy, retain, commit, or attach to an ordinary support
ticket. In a regulated-industry route this is a source-documentation security
defect, so P1.1 documentation cannot pass this review at the reviewed commit.

## Exact scope

The review covered these reader-facing and evidence inputs at the immutable
commit:

- `README.md` and `capture/README.md`;
- `docs/index.md` and `docs/developers/index.md`;
- `docs/developers/tutorials/inspect-an-artifact-pair.md`;
- `docs/developers/how-to/diagnose-an-invalid-artifact-pair.md`;
- `docs/developers/reference/cli-report-and-exit-codes.md`;
- `docs/developers/reference/python-api.md`;
- `docs/developers/explanation/pair-validity-vs-dbt-outcome-vs-capture-state.md`;
- `docs/evidence/p1.1-local-artifact-pair-2026-07-15.md`;
- the P1.1-relevant Jobs, telemetry, dependency, and dbt-artifact rows in
  `docs/research/source-register.md`;
- the P1.1 table and review rules in `docs/reviews/README.md`;
- `capture/examples/inspect_valid_fixture.py`, the three checked-in artifact
  pairs, their provenance and expected reports, the vendored dbt schemas, and
  `capture/src/dbtobsb_capture/schemas/artifact-pair-report-v1.json` where needed
  to verify documentation claims; and
- `capture/pyproject.toml`, `capture/uv.lock`, `scripts/check_capture.sh`, and
  `.github/workflows/capture.yml` where needed to verify checksum, dependency,
  local-gate, and CI claims.

No reviewed file or prior review report was edited by this reviewer. This new
report is outside the immutable reviewed commit.

## Authoritative sources checked

All selected external source links below returned HTTP 200 on 2026-07-15.

- dbt Labs: [dbt artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts),
  [manifest.json](https://docs.getdbt.com/reference/artifacts/manifest-json), and
  [run_results.json](https://docs.getdbt.com/reference/artifacts/run-results-json).
- Exact first-party dbt Core 1.11.12 contracts: [manifest v12](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/manifest/v12.json)
  and [run-results v6](https://github.com/dbt-labs/dbt-core/blob/v1.11.12/schemas/dbt/run-results/v6.json).
- Databricks: [run dbt transformations in Lakeflow Jobs](https://learn.microsoft.com/en-us/azure/databricks/jobs/how-to/use-dbt-in-workflows)
  and [Databricks App telemetry](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/observability),
  used only to check the future archive and optional-telemetry distinctions.
- OWASP: [Logging Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html),
  especially its exclusions for source code, access tokens, sensitive personal
  data, connection strings, and keys; restricted access and transmission; and
  retention/disposal treatment for copies, extracts, and backups.
- NIST: [SP 800-53 Release 5.2.0, including SI-12 Information Management and Retention](https://csrc.nist.gov/pubs/sp/800/53/upd2/final),
  used as the organization-defined retention and disposal baseline rather than
  as a product certification claim.
- W3C: [WCAG 2.2](https://www.w3.org/TR/WCAG22/), used only to define the later
  rendered-site gate; no conformance claim is made here.

The exact tagged schema fields independently confirm the input sensitivity
boundary. Manifest v12 permits, among other fields, `invocation_id`, `env`,
`project_name`, `user_id`, database/schema/relation names, paths,
`original_file_path`, `unique_id`, descriptions, metadata, unrendered config,
raw code, and compiled code. Run-results v6 permits `invocation_id`, `env`,
top-level arguments, adapter responses, messages, resource IDs, compiled code,
and relation names. The repository's synthetic canaries intentionally exercise
these same categories and prove only that they do not escape into the normalized
report.

## Blocking finding

### DOCSEC-P1.1-001 — Raw artifact confidentiality, custody, and support boundary is missing

- Severity: **Medium / blocking for regulated documentation acceptance**
- Affected routes: the local-inspection section in `README.md`; tutorial
  prerequisites; the real-path command and support paragraph in the invalid-pair
  how-to; the CLI and Python API references; and the security explanation.
- Evidence: those pages accurately describe safe output and avoid echoing a
  failed path, but none warns before a reader supplies real files that the raw
  inputs may contain Personal Data, credentials or other secrets, code, error
  details, environment/configuration values, paths, topology, and identities.
  The how-to says not to attach raw artifacts to an ordinary ticket only for
  exit `4`; it does not establish the general rule or an approved exceptional
  route. No page says the input files remain caller-owned and are neither
  deleted nor made policy-compliant by inspection.
- Impact: an operator can safely run the inspector yet mishandle the source
  evidence before or after inspection—for example by copying it to an unmanaged
  workstation directory, committing it, placing it in an uncontrolled backup,
  pasting a fragment into chat, or attaching it to a normal support case. The
  static report's confidentiality controls do not mitigate those copies.

Required resolution:

1. Put a prominent warning before the first route that accepts real artifacts,
   and repeat a concise boundary in both references: treat `manifest.json` and
   `run_results.json` as potentially sensitive and Personal Data-bearing. Do not
   commit, upload, paste, or attach them to an ordinary ticket. Use only
   policy-approved local storage and least-privilege access.
2. State the lifecycle precisely: the CLI reads the supplied files and the API
   receives caller-provided bytes; the inspector does not persist, copy, upload,
   or retain the raw bytes in its report, but it does not delete or govern the
   caller's original files or other copies. Customer policy must govern
   encryption, access logging where required, backup, retention, and deletion.
3. Make support handling general rather than exit-`4`-only. The normal support
   payload is limited to product version, safe command shape, exit/static code,
   and the allowlisted report. If raw evidence is exceptionally required, direct
   the reader to a separately approved restricted-evidence process with an
   authorized recipient, transfer method, access boundary, and retention/deletion
   decision; do not invent or imply an unimplemented upload endpoint.
4. Distinguish the scopes of “local”: P1.1 currently processes files on the
   operator's local execution host, while the target product is designed to keep
   runtime data and compute inside the customer's Databricks environment. Do not
   imply that this workstation-side candidate already proves the future
   Databricks-local data boundary.
5. Link the warning to the dbt artifact/schema sources and the project's source
   register so the field and version boundary remains auditable.

A new immutable documentation commit and independent re-review are required.

## Positive controls and claim assessment

- **Customer-local/no external telemetry:** the target-product statement is
  framed as direction, not completed P1.1 functionality. The current inspector
  makes no Databricks or runtime network call and requires no external telemetry
  platform. Optional Databricks App telemetry is explicitly disabled by default
  in the plan/source register. The missing workstation-input custody warning is
  the one material gap in this boundary.
- **Installation egress:** README and the tutorial correctly say
  “offline after installation,” disclose that the first locked sync can download
  packages, require an approved registry/mirror/cache in regulated environments,
  and state that no disconnected wheelhouse is shipped. There is no false
  air-gap claim.
- **Safe output and errors:** the generated report contract is closed and
  allowlisted. It excludes raw evidence and observed values; input-read and
  internal errors exclude paths, exceptions, and artifact fragments. The CLI
  regular-file/no-follow/128 MiB limits are documented accurately. These are
  output and parser-safety controls, not input-confidentiality controls.
- **Synthetic versus runtime evidence:** every reader route and the evidence
  record consistently identifies the three fixtures as synthetic and sanitized,
  with `runtime_evidence=false` and `runtime_attestation=false`. Pair validity,
  native dbt outcome, and future capture completeness remain separate.
- **Checksums, dependencies, and CI:** the two documented schema digests matched
  the vendored bytes. `uv lock --check` passed; the runtime dependencies are
  exact and locked with distribution hashes. The workflow uses read-only
  `contents`, full action commit SHAs, uv `0.11.28`, CPython `3.12.3`, a
  ten-minute timeout, disabled cache, and no artifact-upload step. The dated
  `pip-audit` result is presented as historical evidence, not a current or
  vulnerability-free certification.
- **Compute and runtime scope:** the evidence says P1.1 itself used no cloud or
  paid compute and carefully limits its dated inventory to the compute classes
  visible to one profile. It explicitly does not cover every billable service.
  This review made no fresh cloud call and therefore assesses the wording, not
  the continued truth of that point-in-time inventory.
- **Retention and completeness:** the docs do not claim that pair validation
  proves archive retrieval, structured-log capture, early-failure coverage, or
  a complete capture. Future signed-link, native archive, stable-absence, lock,
  and real-runtime qualification gates remain visible.
- **Qualification/certification:** P1.1 is consistently called a candidate;
  compatibility context is not described as a qualified production row, and no
  regulatory, NIST, OWASP, Databricks, dbt, or WCAG certification is claimed.

## Local verification and publication-safety scan

The exact reviewed commit produced:

```text
scripts/check_capture.sh
90 tests passed
Ruff check and format: passed
ty: passed
report-schema and fixture regeneration: passed
runtime-only install, checked-in example, wheel build, and isolated installed CLI: passed
DBTOBSB_CAPTURE_CHECK_PASSED

uv lock --check --project capture
passed

Markdown source scan
108 Markdown files; 69 local links; 0 missing local targets

selected authoritative source check
10 selected URLs; 10 returned HTTP 200
```

The gate also reproduced deterministic fixture generation and canary
non-disclosure. A tracked-source scan found no likely live Databricks host,
workspace/account/user identifier, access token, private key, or credential in
the reviewed P1.1 route. The email/path/secret-like values present in the
fixtures are conspicuously synthetic `CANARY_*` values or `example.invalid`
addresses and remain confined to fixture, generator, provenance, and test
contexts; the expected reports and reader output contain none of them.

This is a current-source check, not a public-release attestation. A future public
release still requires a reachable-history scan, ignored-file review, CI
log/artifact review, and inspection of generated publication files and metadata.

## Deferred later gates

1. **Documentation-site gate:** no MkDocs, Zensical, Docusaurus, Jekyll, or other
   site configuration and no rendered site artifact exists. Browser navigation,
   external-link behavior, responsive layout, keyboard use, focus, contrast,
   screen-reader behavior, generated metadata/OCR, and WCAG 2.2 conformance are
   explicitly deferred; source Markdown cannot satisfy that gate.
2. **Distribution gate:** qualify a checksum-bound disconnected installation
   artifact before promising offline first installation or air-gapped delivery.
3. **Runtime/capture gate:** use independently sanitized real Azure Databricks
   success, dbt failure, early-failure, cancellation, timeout, retry, and repair
   evidence before qualifying runtime support or capture completeness.
4. **Retention/product gate:** later collectors must define policy-driven
   customer-local retention/deletion, including archives, restricted evidence,
   derived rows, backups, and uninstall consequences; P1.1 pair validation does
   not prove those controls.

## Verdict

**CHANGES_REQUIRED**

`DOCSEC-P1.1-001` is a source-documentation security/compliance defect. The
implementation's safe-output boundary is strong, but the documentation must
make the raw-input custody, Personal Data/secrets, retention/deletion, support,
and workstation-versus-Databricks-local boundaries explicit before this slice
can be accepted for regulated use.
