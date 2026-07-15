# Security and compliance documentation review: planning baseline 0.19

- Date: 2026-07-15
- Reviewer: Independent security/compliance documentation reviewer
- Planning author-set SHA-256: `703ae3cc1a86bee5d641c7fa478fbb49bdd88cd193f2aec36e61e9b00078eb5f`
- Live-evidence SHA-256: `d4904dc48dd8d803d258e58845da929418d5f11dbb55a805aa919c9fbb71c0c2`
- Private run-record template SHA-256: `172ae9825e5e7383526fd2879fe4deb29df3a24ac972c63fd37559484f4d310b`
- Eight-file implementation SHA-256 used for claim checking: `0ad64adf3071944adddf501120713bb07c0e19d43e360a901d17dbe6bf7fa437`
- Verdict: `CHANGES_REQUIRED`
- Highest severity: Medium
- Cloud activity: None. This source review made no Azure, Databricks authentication, App, Job, SQL, warehouse, cluster, or Unity Catalog call.
- Rendered-site security/accessibility validation: Deferred because no documentation site exists.

## Immutable review input

Before the shared working tree advanced, I reproduced all four requested hashes. This report is bound only to those baseline 0.19 inputs. It does not approve a later author, evidence, template, or implementation state.

I reviewed `README.md`, `AGENTS.md`, `docs/index.md`, the ADR, all planning files, the source register, the sanitized live-smoke evidence, the private run-record template, and the then-latest final Diataxis and FastAPI-style reports. I inspected the frozen implementation only where necessary to verify documentation claims about credential and token handling.

No author, evidence, template, or implementation file was edited by this reviewer. This report is outside the frozen input sets.

## Executive assessment

Baseline 0.19 has a strong regulated-industry design posture. It consistently uses **Personal Data**, classifies pseudonymous identity records correctly, keeps raw dbt artifacts/logs out of ordinary views, declares least-privilege runtime write sets, makes optional broad system-table access separate and disabled, discloses administrator and group roots, and avoids presenting point-in-time evidence as continuous or administrator-resistant assurance.

The P0 evidence and examples are sanitized and the cost/readiness claims are unusually honest. However, the runnable P0 authentication path does not yet satisfy the secure-storage posture that the same baseline declares, and the source register falsely states that dbtobsb never calls a sensitive token-output command. The external approval record is also described as if it blocks the wrapper without saying that P0 enforcement is procedural. Those documentation/security inconsistencies must be corrected before this baseline is accepted.

## Controls that pass

### Personal Data and diagnostic classification

- Reader-facing and planning text uses `Personal Data`; the only appearances of `PII` are contributor instructions saying not to use that term.
- Pseudonymous actor/device/governance records remain classified as Personal Data.
- Raw SQL, compiled SQL, arbitrary metadata, messages, structured-log payloads, environment values, raw forwarded identity, and full dbt artifacts are excluded from ordinary UI/analytical views.
- Restricted raw evidence is optional or failure-only, separately permissioned, bounded, and subject to customer retention policy.
- Signed archive URLs are never retained, and forwarded identity/browser secrets are request-local.

### Customer-local and least-privilege boundary

- No external telemetry, provider control plane, licensing service, or AI dependency is required.
- Product runtime has zero required public-internet egress; build/deployment egress is separately disclosed and still awaiting its P3 decision.
- dbt anonymous usage and artifact-ingest upload are explicitly disabled for every supported command ordinal.
- Runtime App, collector, role-administration, observed-job, and optional-enrichment identities have separately enumerated write sets and denials.
- Optional system enrichment is absent from the base install and discloses regional/account-global source scope before enablement.
- Direct schema grants, hidden SQL hooks, privileged migration Jobs, and implicit customer-schema adoption are prohibited.

### Readiness, trust, and cost honesty

- P0 is repeatedly limited to process liveness; it does not claim dbt execution, artifact capture, dependency readiness, product-data access, or product readiness.
- Point-in-time trust, administrator-attested roster evidence, group roots, App/Job managers, self-grant capability, and compromised-admin/App limitations are disclosed without false tamper-resistance language.
- The ten-minute cancellation budget, `0.084 DBU` planned exposure, `0.25 DBU` successful-stop window, lack of a hard ceiling after failed stop, and possible continuing cost are distinct facts.
- The original live run's incomplete cost approval remains a historical process nonconformance rather than being rewritten as compliant.

### Evidence and example safety

The requested source files contained no known live workspace host/ID, account ID, user identity, email, service-principal/App ID, signed URL, token, private key, raw customer log, or customer payload. Credential-pattern scans found no PAT, OAuth/JWT value, bearer literal, or private-key block. Long numeric literals were hashes, standards vectors, or deliberately bounded schema values rather than live identifiers.

The run-record example is explicitly synthetic and uses unmistakable example aliases and future timestamps. The README uses placeholders rather than real profile, host, or user values. The evidence is bound to the implementation that actually ran, identifies later guards as local-only, and says its separate readback reused the same operator/credential context rather than claiming independent attestation.

This scan covered the requested source inputs. It is not a substitute for the separately planned repository-history, source-image metadata/OCR, rendered-site, CI-log, and publication-artifact scan.

## Findings

### DOC-SEC-P0-001: runnable P0 does not require OS-native secure OAuth storage

- Severity: **Medium**
- Affected inputs: `README.md`, `scripts/smoke_databricks_app.sh`, `docs/research/source-register.md`, `docs/plans/product-plan.md`

The source register correctly says the regulated attended baseline must force `DATABRICKS_AUTH_STORAGE=secure`, because ordinary CLI login can silently fall back to plaintext storage when the native backend is unavailable. The target installer contract likewise rejects plaintext storage.

The runnable P0 path requires only an OAuth U2M profile and checks authentication type, host, and user. It neither forces secure storage nor rejects an inherited plaintext setting. A valid U2M profile backed by the CLI's plaintext cache can therefore pass the documented preflight.

This does not mean the P0 script prints the token: its access-token handling is otherwise careful. The risk is the longer-lived OAuth cache on the workstation, which is precisely the regulated boundary the planning documents say must fail closed.

Required resolution:

1. Force explicit secure storage before every P0 CLI call and reject an inherited non-secure value.
2. Confirm the effective storage backend through non-sensitive authentication description and reject plaintext or unknown state.
3. State the supported native secure stores and that the actor-owned cached credential remains customer-controlled endpoint state outside the repository.
4. Add a local negative test proving plaintext/non-secure input fails before inventory, Bundle validation, deployment, token output, or cleanup arming.
5. Preserve the operator-owned profile; do not create, overwrite, copy, log out, or delete it.

Current official documentation confirms that CLI 1.0+ defaults to native secure storage but can silently persist `auth_storage = plaintext` unless secure mode is explicit. See [CLI token storage](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/authentication#token-storage) and [stored-credentials troubleshooting](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/troubleshooting#stored-credentials-error).

### DOC-SEC-P0-002: “never calls sensitive token-output commands” contradicts P0

- Severity: **Medium**
- Affected inputs: `docs/research/source-register.md`, `README.md`, `scripts/smoke_databricks_app.sh`

The source register says dbtobsb “never calls sensitive token-output commands.” The frozen P0 wrapper calls `databricks auth token` and extracts `.access_token` so it can invoke the App health endpoint.

The implementation materially reduces exposure: tracing is refused, the token is captured only after safe App readback, supplied to curl through stdin configuration rather than argv, cleared before parsing and again in cleanup, and tested absent from argv/stdout/stderr. Nevertheless, the command does output a bearer token to the wrapper. A regulated reader relying on the categorical source-register statement could incorrectly approve an environment whose policy prohibits that operation.

Required resolution:

1. Scope the production-installer prohibition accurately and document the bounded P0 exception and its exact safeguards.
2. State that P0 is unsupported where policy prohibits materializing an OAuth access token in the wrapper process.
3. Keep the token out of argv, environment exports, files, logs, evidence, exceptions, and screenshots; retain the current tracing/curl/cleanup tests.
4. Before product release, either use a supported credential-delegation path that does not expose token output or retain the exception through explicit security approval.

The official [`auth token` command reference](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/reference/auth-commands#databricks-auth-token) confirms that the command emits an OAuth access token from the local U2M cache.

### DOC-SEC-P0-003: private approval is procedural but not labeled as such

- Severity: **Low**
- Affected inputs: `README.md`, `docs/templates/p0-smoke-run-record.md`, `scripts/smoke_databricks_app.sh`

The README says the run is blocked while a required private-record field is missing, and the template says the wrapper is not authorized to run. The record intentionally lives in an external policy-approved private system, but the P0 wrapper takes no record path/reference and cannot inspect that system.

An attended procedural gate is acceptable for this bounded P0 test. The problem is that the executable route does not explicitly distinguish that human/governance control from wrapper-enforced checks. In a regulated runbook, “blocked” must not imply a machine gate that does not exist.

Required resolution:

1. Say directly that P0 cannot query the private approval system and that the operator/approver must enforce and retain this gate before invocation.
2. List which controls are wrapper-enforced versus externally attested.
3. Keep the real approval reference, approver identity, cleanup-owner reference, host/ID, and evidence reference only in the policy-approved private system.
4. Forbid tokens, secrets, signed URLs, raw logs/SQL, or arbitrary customer evidence in the free-form record notes.

## Prior documentation-review context

The final Diataxis report reviewed an older 0.17 input and correctly retained the D0 transition from the repository README/index to four rendered documentation modes. The final FastAPI-style report also bound only 0.17 and found the then-supported non-empty-workspace path, reversed README disclosure, missing run-record template, and incomplete cost-source registration.

The current 0.19 source resolves those four old content defects: it supports only a dedicated/complete-visibility workspace, puts the runnable route first, provides the private template, and registers precise cost sources. Those older reports do not, however, approve 0.19, and they do not resolve the security findings above.

## Rendered-site disposition

Source Markdown was checked for headings, descriptive links, fenced examples, text-only status language, and unsafe literals. Full rendered-site validation is accurately deferred: there is no implemented product documentation site, theme, navigation/search layer, screenshot set, or publication artifact to test.

No WCAG, rendered-navigation, contrast, responsive-layout, metadata/OCR, Git-history, or publication-safety pass is claimed here. Those remain mandatory when D0/D1 produces a site and real captures.

## Verdict

`CHANGES_REQUIRED`

Baseline 0.19 has no leaked live identifier or credential and its broader data, least-privilege, egress, readiness, evidence, retention, and cost posture is strong. It cannot receive final security/compliance documentation approval while a plaintext-backed OAuth profile can pass the runnable P0 path and the source register denies a token-output behavior the implementation performs. The procedural approval boundary must also be labeled explicitly. Re-review all four bound inputs after those corrections.
