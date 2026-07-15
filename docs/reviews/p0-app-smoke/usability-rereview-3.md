# P0 Databricks App smoke: third usability and accessibility re-review

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
| `app/tests/test_main.py` | `cc1bad1b858316df50d830ad7c928101583bc8e3fe32f8cb9bda76108bdc9c70` |
| `app/uv.lock` | `b7145c88938dcf34b2d88a2f18d54f362a7ca94f6709727ee2cc25801b05be5d` |
| `databricks.yml` | `d0f53887622010c27974fd9a1cf5ba708cedc404694e86361df825d417435b45` |
| `scripts/smoke_databricks_app.sh` | `66ecca40b34d6178ae174b3b99b690796185309b35e4299b2487a4fb509f96fe` |

The globally sorted path-and-content aggregate reproduced exactly:

```text
0ad64adf3071944adddf501120713bb07c0e19d43e360a901d17dbe6bf7fa437
```

This report is outside the implementation digest. No implementation, planning, template, or evidence file was edited by this reviewer.

## Executive verdict

The frozen implementation passes the bounded P0 usability and accessibility gate. The focused change adds a dedicated-workspace inventory preflight after identity verification and before any Bundle validation or deployment. It fails safely when an unrelated App is visible and does not stop, delete, validate, deploy, or run anything on that path.

All twelve tests pass. The new test proves the user-visible property that matters most: an unsupported workspace returns a specific nonzero result before mutation. Static review confirms the same fail-before-mutation branch for a visible SQL warehouse or cluster.

No prior liveness/readiness, credential, compute-size, binding, cleanup, recovery-copy, OpenAPI, external-asset, terminal-accessibility, or Personal Data control regressed.

## Dedicated-workspace preflight

### Ordering — Pass

The wrapper first checks required tools, exact CLI version, and the named OAuth U2M profile's host/user boundary. It then reads the visible App, warehouse, and cluster inventories. Bundle validation occurs only after all inventory predicates succeed; deployment and start occur later still.

This order gives the operator a useful early answer while avoiding a workspace mutation when the route is unsupported.

### Supported inventory — Pass

The App predicate permits only:

- no App; or
- one existing App named `dbtobsb-smoke` that is `STOPPED`, `MEDIUM`, and has zero resource bindings.

It rejects an unrelated App, duplicate smoke Apps, a non-stopped smoke App, a non-`MEDIUM` smoke App, or any binding. Warehouses and clusters must each be empty. Missing or malformed inventory cannot satisfy the `jq -e` predicates and therefore fails closed.

The wrapper does not pretend these list calls establish account-global visibility. The user-facing prerequisite separately requires approved complete visibility for this dedicated workspace.

### Failure copy and consequence — Pass

The two messages are short and actionable:

- `P0 requires no unrelated Apps and only an optional stopped, unbound MEDIUM dbtobsb-smoke App.`
- `P0 requires a dedicated smoke workspace with zero visible SQL warehouses and clusters.`

They expose no host, user, profile, token, URL, resource ID, or raw inventory JSON. Exit code `2` distinguishes precondition failure from a failed liveness check. Because mutation has not been armed, the wrapper correctly does not issue an App stop on this path; it never touches an unrelated resource.

### Twelfth test — Pass

`test_smoke_wrapper_rejects_unrelated_workspace_before_mutation` injects one unrelated App and proves:

1. exit code is `2`;
2. the dedicated-App message is present;
3. Bundle validation is not called;
4. Bundle deployment is not called;
5. Bundle run is not called; and
6. App stop is not called.

The test checks executable behavior through the fake CLI call log rather than asserting only a constant or helper return value. The warehouse/cluster predicate is direct and was inspected; adding separate branch tests for those two equivalent list failures would strengthen future regression coverage but is not an open usability finding.

## Prior finding disposition

| Finding | Disposition at `0ad64adf…` |
| --- | --- |
| `UX-SMOKE-001` — public documentation assets | **RESOLVED — NO REGRESSION.** `/docs` and `/redoc` remain disabled; the raw customer-local OpenAPI JSON has no public browser-asset dependency. |
| `UX-SMOKE-002` — liveness mistaken for readiness | **RESOLVED — NO REGRESSION.** Health, index, log, schema, descriptions, and tests retain `alive`, `process_liveness`, `not_evaluated`, and `p0_smoke`. |
| `UX-SMOKE-003` — OpenAPI routing and ergonomics | **RESOLVED — NO REGRESSION.** `/api/openapi.json`, stable operation IDs, summaries, response descriptions, tags, field descriptions, and examples remain exact. |
| `UX-SMOKE-FU-001` — visible final cost state and recovery commands | **RESOLVED — NO REGRESSION.** Verified cleanup prints `STOP VERIFIED`; failed or unverified cleanup warns that cost may continue and prints shell-escaped stop/state commands. |
| Focused `MEDIUM` compute-size check | **PASS — NO REGRESSION.** Both stopped and active readbacks require `MEDIUM`; the existing negative test proves no start and verified stop after a mismatch. |
| Dedicated-workspace preflight | **PASS.** The new inventory guard and twelfth test fail before mutation and preserve unrelated resources. |

## End-to-end operator safety regression scan

### Identity and secrets — Pass

- Required profile, expected host, and expected user inputs fail immediately when absent.
- Shell tracing and ambient token/client-secret authentication are refused before mutation.
- The exact CLI version and OAuth U2M authentication type are checked.
- The bearer token enters `curl` through standard input rather than its process arguments and is unset afterward.
- `curl` ignores user configuration and permits only HTTPS with TLS 1.2 or newer.
- Tests continue to prove the token is absent from arguments, stdout, and stderr.

### Cost and lifecycle — Pass

- The Bundle declares one unbound App stopped by default.
- Inventory rejection occurs before deploy/start and incurs no App-compute start from this wrapper.
- After deployment, the wrapper requires stopped, unbound `MEDIUM` state before the single start.
- After start, it requires active `MEDIUM` state, the expected URL shape, and still-zero bindings.
- Cleanup is armed before deployment, attempts idempotent stop on every later exit path, and treats a stop request as insufficient until `STOPPED` is read back.
- Cleanup uncertainty cannot produce success and includes continuing-cost language plus copy-ready recovery commands.

### Liveness and product boundary — Pass

The App remains a small FastAPI process-liveness surface. It has no dbt dependency, subprocess execution, product binding, SQL warehouse, Job, cluster, secret, Volume, model-serving resource, artifact parser, or customer-data response. The endpoint and OpenAPI contract explicitly deny product/dependency readiness. Starting/stopping App compute is never mapped to a dbt outcome.

### Terminal and API accessibility — Pass for the shipped P0 surface

The terminal path uses linear plain text, stable condition prefixes, no color-only meaning, no cursor control, no animation, and no interactive prompt. JSON responses are small and machine-readable. Interactive HTML documentation remains absent, so no unreviewed keyboard/focus/zoom/reflow or external-asset surface was introduced.

Future HTML UI, interactive documentation, dbt capture, product binding, installer, or Marketplace work requires its own complete-process usability and accessibility review.

## Twelve-test and local quality gate

The complete local sequence passed:

```text
uv sync --project app --locked --extra dev
Resolved 31 packages
Checked 30 packages

uv run --project app --extra dev pytest
collected 12 items
12 passed in 3.52s

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

The wrapper tests use temporary fake `databricks` and `curl` executables. No authentication or network call occurs.

## Final disposition

**`PASS`.** The P0 implementation at `0ad64adf3071944adddf501120713bb07c0e19d43e360a901d17dbe6bf7fa437` is understandable, fail-closed, secret-safe, stopped-by-default, unbound, `MEDIUM`-only, and limited to process liveness. Its dedicated-workspace guard rejects unrelated visible resources before any Bundle action, and all twelve tests plus static gates pass. Approval does not extend to future dbt execution/capture, product bindings, an HTML UI, the P3 installer, or Marketplace distribution.
