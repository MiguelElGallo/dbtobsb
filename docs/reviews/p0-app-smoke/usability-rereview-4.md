# P0 Databricks App smoke: fourth usability and accessibility re-review

- Date: 2026-07-15
- Reviewer: usability, onboarding, and accessibility specialist
- Verdict: **PASS**
- Findings: none
- Cloud/authentication activity: none

## Frozen implementation input

Only the following eight implementation files were reviewed:

| File | SHA-256 |
| --- | --- |
| `app/app.yaml` | `e08b266f4e0be736a260a53a5b2d22ebeae5a9c83f9479c916f0fc753111334c` |
| `app/dbtobsb_app/__init__.py` | `4849b6ba1eb8a5a2c83293ff7be232ab01b66a9fdc0ee9c913b9bc8bf5d72bba` |
| `app/dbtobsb_app/main.py` | `63514752f4f3e4e4ccc3e4623b3bff13c8b999c64b6e720f0ba41beac48b90ab` |
| `app/pyproject.toml` | `90653dc48d2e01a81f66ec32735385be176e7df55a1d38c40821cee9b3e9c1fd` |
| `app/tests/test_main.py` | `2bb3445533c8ad80ddca87dc4628960202bd00a9790b096091850bca31b18066` |
| `app/uv.lock` | `b7145c88938dcf34b2d88a2f18d54f362a7ca94f6709727ee2cc25801b05be5d` |
| `databricks.yml` | `d0f53887622010c27974fd9a1cf5ba708cedc404694e86361df825d417435b45` |
| `scripts/smoke_databricks_app.sh` | `3f4f6c2a52bc42396e5d5f43ec5c598cb58f6939695d97893d720f8b8a37cb27` |

The globally sorted path-and-content aggregate reproduced exactly:

```text
8b1865cd05ba5abbeef6634d80e01778affe5b03ee76cbdfe919be3d84355101
```

This report is outside the implementation digest. No implementation, planning, template, or evidence file was edited by this reviewer.

## Executive verdict

The focused security delta passes the P0 implementation usability gate. The wrapper now rejects inherited non-secure authentication storage and forces `DATABRICKS_AUTH_STORAGE=secure` before its first Databricks CLI call. The fake CLI refuses every invocation unless that environment is present, so all executable wrapper paths covered by the twelve-test suite prove the setting is propagated.

The existing token handling remains bounded and accurately documented: the operator cannot supply an ambient token/client secret; the wrapper retrieves a short-lived U2M token only after identity, inventory, stopped-size, binding, and active-App checks; the token reaches `curl` through standard input rather than argv; shell tracing and user/global curl configuration are disabled; and the value is cleared.

No liveness/readiness, workspace-inventory, compute-size, resource-binding, cleanup, recovery-copy, OpenAPI, terminal-accessibility, or secret-output regression was found.

## Secure authentication storage

### Early rejection — Pass

The new check occurs before the wrapper installs traps, searches for tools, invokes the CLI, inspects inventory, validates the Bundle, deploys, or starts compute. If `DATABRICKS_AUTH_STORAGE` is inherited with any nonempty value other than exact `secure`, it returns exit `2` and prints:

```text
Refusing non-secure Databricks authentication storage.
```

The message is short, names the failed condition, exposes no configuration path or credential, and cannot be mistaken for a prompt to continue with plaintext. A local synthetic probe with `DATABRICKS_AUTH_STORAGE=plaintext` reproduced that exact result with no stdout and no external command call.

### Forced secure mode — Pass

When the variable is absent or already `secure`, the wrapper exports exact `secure` before `databricks --version` and every later CLI call. Environment-variable precedence therefore prevents an `auth_storage=plaintext` profile setting from silently selecting plaintext for this run. If the native store is unavailable or cannot supply the profile token, authentication fails before inventory or mutation.

Current official behavior and the reason for this guard are documented in [Databricks CLI authentication](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/authentication#token-storage) and [Databricks CLI troubleshooting](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/troubleshooting#stored-credentials-error).

### Fake-CLI proof — Pass

The fake `databricks` executable begins every invocation with:

```sh
if [ "${DATABRICKS_AUTH_STORAGE:-}" != secure ]; then
  printf '%s\n' 'secure auth storage was not forced' >&2
  exit 18
fi
```

All twelve tests pass through this guard. This covers CLI version, authentication description, inventories, Bundle lifecycle, App reads/logs/stop, and the P0 token request on their exercised paths. The proof is stronger than a source-string assertion because an omitted export would make the wrapper tests fail at their first fake CLI call.

The explicit inherited-nonsecure branch was additionally executed locally. A dedicated unit case for that one-line branch would improve regression localization but is not an open usability finding because its observable behavior was directly verified and the script passed shell analysis.

## P0-only token handling — Pass

The token path remains guarded in the correct order:

1. reject shell tracing and ambient `DATABRICKS_TOKEN`/client-secret input;
2. force secure U2M storage and confirm the named profile, exact host, authentication type, and expected user;
3. reject unsupported workspace inventory;
4. deploy stopped and verify `STOPPED`, `MEDIUM`, and zero bindings;
5. start once and verify `ACTIVE`, `MEDIUM`, expected URL shape, and zero bindings;
6. request one short-lived token from the named profile for the authenticated health call;
7. pipe a curl configuration containing the bearer header over standard input with `curl --disable`; and
8. unset the shell variable immediately after the call.

Tests prove the synthetic token is absent from curl arguments, stdout, and stderr. The App response/log remains an allowlisted liveness event. This review approves that narrow P0 mechanism only; it does not approve token-output commands for the production bootstrap, product capture, or runtime.

## Procedural approval boundary — No implementation overclaim

The wrapper has no API or path for the policy-owned private approval record. That is now documented as an attended procedural gate owned by operator and approver, so the implementation is not credited with enforcement it does not provide. The script's technical preflights complement rather than replace that human control.

## Prior finding and regression disposition

| Area | Disposition at `8b1865cd…` |
| --- | --- |
| `UX-SMOKE-001` through `UX-SMOKE-003` | **RESOLVED — NO REGRESSION.** Interactive CDN-backed docs remain disabled; liveness/readiness semantics and `/api/openapi.json` metadata remain exact. |
| `UX-SMOKE-FU-001` | **RESOLVED — NO REGRESSION.** Verified stop and failed/unverified-stop recovery copy remain explicit and shell-escaped. |
| `MEDIUM` size and dedicated-workspace checks | **PASS — NO REGRESSION.** Unsupported state fails before start or before any Bundle mutation as applicable; unrelated resources are not stopped. |
| Secure-storage delta | **PASS.** Non-secure inheritance fails before all external calls; secure mode is forced for all exercised CLI paths. |
| P0 token exception | **PASS WITH P0 SCOPE ONLY.** In-memory health-call handling remains secret-safe; it is not production-bootstrap approval. |

## Accessibility-relevant assessment

The new error is linear plain text and does not depend on color, focus, animation, cursor movement, or an interactive prompt. It precedes any noisy platform output on the inherited-nonsecure path. The API remains structured JSON with no interactive HTML surface. Future installer guidance must add a reviewed recovery route for supported native stores and explicit unsupported workstation states; that work remains under the P3 gate rather than this expert-only P0 script.

## Twelve-test and static gate

The complete local sequence passed:

```text
uv sync --project app --locked --extra dev
Resolved 31 packages
Checked 30 packages

uv run --project app --extra dev pytest
collected 12 items
12 passed in 3.54s

uv run --project app --extra dev ruff check app/dbtobsb_app app/tests
All checks passed!

uv run --project app --extra dev ruff format --check app/dbtobsb_app app/tests
3 files already formatted

uv run --project app --extra dev ty check app/dbtobsb_app app/tests
All checks passed!

bash -n scripts/smoke_databricks_app.sh
# exit 0

shellcheck scripts/smoke_databricks_app.sh
# exit 0
```

The tests use local fake executables. No Databricks, Azure, authentication, App, Job, SQL, warehouse, cluster, Unity Catalog, or other cloud call was made, and no paid compute started.

## Final disposition

**`PASS`.** The implementation at `8b1865cd05ba5abbeef6634d80e01778affe5b03ee76cbdfe919be3d84355101` forces secure authentication storage before every CLI call, rejects inherited non-secure configuration before mutation, and preserves the bounded no-output P0 health-token handling. All twelve tests and static gates pass. Approval remains limited to the stopped-by-default, unbound, dedicated-workspace process-liveness smoke.
