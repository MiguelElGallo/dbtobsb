# Focused security/compliance documentation re-review: baseline 0.20

- Date: 2026-07-15
- Reviewer: Independent security/compliance documentation reviewer
- Planning author-set SHA-256: `e6a8d55f2b155916d52ac0c6aa6ce87941a3d8672f6dc4a0bfdb692a3fb7fd44`
- Live-evidence SHA-256: `670f54bdcef70e458adad590e959004e08f9aa5319855104299f5813c9419ed3`
- Private run-record template SHA-256: `6c61dc5091358cae2b5a531c6017bb012a4d0fc869edfd22fcaa2369bf5dca69`
- Eight-file implementation SHA-256 used for claim checking: `8b1865cd05ba5abbeef6634d80e01778affe5b03ee76cbdfe919be3d84355101`
- Prior verdict: `CHANGES_REQUIRED`
- Verdict: `PASS`
- Cloud activity: None. This re-review made no Azure, Databricks authentication, App, Job, SQL, warehouse, cluster, or Unity Catalog call.
- Rendered-site security/accessibility validation: Deferred because no documentation site exists.

## Immutable input verification

I recomputed all four requested hashes and matched them exactly. No author, evidence, template, or implementation file was edited by this reviewer. This report is outside every frozen input set.

## Finding resolution

| Prior finding | Resolution in baseline 0.20 | Result |
|---|---|---|
| `DOC-SEC-P0-001` - runnable P0 did not require native secure OAuth storage | The wrapper rejects any inherited non-empty value other than `secure`, then exports `DATABRICKS_AUTH_STORAGE=secure` before the first CLI call. Because the environment setting takes precedence over profile settings, a plaintext-only cache cannot authenticate through this path. The fake CLI rejects every invocation that does not receive secure mode. README states the boundary. | `RESOLVED` |
| `DOC-SEC-P0-002` - categorical token-output claim contradicted P0 | README, evidence, and source register now describe the development-only `databricks auth token` exception and distinguish it from the future production-bootstrap prohibition. They state the in-memory/stdin/no-argv/no-log/clear safeguards and avoid claiming that the P0 command is absent. | `RESOLVED` |
| `DOC-SEC-P0-003` - external approval looked mechanically enforced | README and the template now say explicitly that the private record is an attended procedural gate, the wrapper cannot read the external system, and the operator/approver must withhold authorization until the record is complete and `APPROVED`. | `RESOLVED` |

## Security/compliance assessment

The secure-storage change is fail-closed and correctly ordered. It runs before tool/version checks, authentication, inventory, Bundle validation, cleanup arming, or token output. A local negative invocation with inherited `DATABRICKS_AUTH_STORAGE=plaintext` returned exit `2` with no CLI call. The normal fake-CLI suite also proves that every wrapper-created CLI process sees `secure`.

Official Databricks documentation confirms both relevant semantics: CLI login can silently fall back to plaintext when secure storage is not explicit, and the environment storage setting overrides profile configuration. See [CLI token storage](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/authentication#token-storage) and [stored-credentials troubleshooting](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/troubleshooting#stored-credentials-error).

The token exception is now auditably narrow. It does not normalize token-output commands as a production pattern or conceal their use. The implementation still rejects shell tracing and ambient token/client-secret auth; retrieves the access token only after active/Medium/unbound readback; supplies it to curl through stdin configuration with curlrc disabled; clears it before response parsing and in cleanup; and tests that the token is absent from argv, stdout, and stderr. A policy that prohibits this development exception can decline the P0 smoke without weakening the production contract.

The updated historical evidence is honest: the already completed paid run did not attest secure token storage, and later local corrections do not retroactively upgrade that evidence. It continues to preserve the original cost-control finding and the exact implementation hash that actually ran.

The final source set continues to use Personal Data terminology correctly, classify pseudonymous identity records, exclude raw diagnostics from ordinary views, separate optional broad system access, disclose administrator/group/App/Job roots, and keep cost/readiness claims narrow. The private template remains synthetic and contains no deployable value.

## Identifier and credential scan

The final README, working agreement, index, ADR/plans/source register, evidence, and template contain none of the known live workspace/user/repository identifiers supplied outside this repository. No runtime Databricks host, email, account/workspace/App/service-principal ID, token, bearer literal, signed URL, private key, raw customer log, or customer payload was found.

This is a source-input scan, not the future rendered/publication pass. Git history, CI logs/artifacts, screenshot metadata/OCR, generated HTML, and publication reachability remain subject to the planned independent release scan.

## Local verification

```text
uv sync --project app --locked --extra dev
Resolved 31 packages; checked 30 packages

uv run --project app --extra dev pytest
12 passed in 3.56s

ruff check / format check / ty check
passed

bash -n / shellcheck
passed

inherited plaintext-storage negative probe
exit 2 before any CLI call
```

## Rendered-site disposition

Source Markdown passes this security/compliance review. No complete documentation site, screenshot set, theme, search/navigation implementation, or publication artifact exists, so rendered accessibility, metadata/OCR, link behavior, reachable-history, and artifact-safety validation are accurately deferred. No WCAG or rendered-publication claim is made.

## Verdict

`PASS`

All three baseline 0.19 security/compliance findings are resolved in the exact 0.20 inputs. The runnable P0 path now forces the documented secure-store boundary, the token-output exception is explicit and bounded, the private approval record is honestly procedural, the historical evidence remains non-retroactive, and no live identifier or credential is present.
