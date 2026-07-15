# Focused usability re-review: P0 App `MEDIUM` cost enforcement

- Date: 2026-07-15
- Reviewer: usability, onboarding, and accessibility specialist
- Verdict: **PASS**
- Cloud/authentication activity: none

## Frozen implementation input

Only these eight files were reviewed:

| File | SHA-256 |
| --- | --- |
| `app/app.yaml` | `e08b266f4e0be736a260a53a5b2d22ebeae5a9c83f9479c916f0fc753111334c` |
| `app/dbtobsb_app/__init__.py` | `4849b6ba1eb8a5a2c83293ff7be232ab01b66a9fdc0ee9c913b9bc8bf5d72bba` |
| `app/dbtobsb_app/main.py` | `63514752f4f3e4e4ccc3e4623b3bff13c8b999c64b6e720f0ba41beac48b90ab` |
| `app/pyproject.toml` | `90653dc48d2e01a81f66ec32735385be176e7df55a1d38c40821cee9b3e9c1fd` |
| `app/tests/test_main.py` | `99dca0acc2e0d7b02b830f5a1b34d9eb8e0f6ef350e68a5aa4f56d6ef24a8d80` |
| `app/uv.lock` | `b7145c88938dcf34b2d88a2f18d54f362a7ca94f6709727ee2cc25801b05be5d` |
| `databricks.yml` | `d0f53887622010c27974fd9a1cf5ba708cedc404694e86361df825d417435b45` |
| `scripts/smoke_databricks_app.sh` | `745437b32254d5cdb2e90fd030523e33b9319381b897046cc6c22a0a671af65d` |

The globally sorted path-and-content proof is:

```text
3dfdce3c354b858a252904190ccbca7689d10fe883a818910c897acb9dcd3866
```

Reproduction command, run from the repository root:

```sh
printf '%s\n' \
  databricks.yml \
  app/app.yaml \
  app/pyproject.toml \
  app/uv.lock \
  app/dbtobsb_app/__init__.py \
  app/dbtobsb_app/main.py \
  app/tests/test_main.py \
  scripts/smoke_databricks_app.sh |
  LC_ALL=C sort |
  while IFS= read -r file; do shasum -a 256 "$file"; done |
  shasum -a 256
```

The supplied hash reproduced exactly before and after review. No implementation file was edited by this reviewer.

## Focused verdict

The wrapper now enforces the cost-envelope size before it can invoke the App Bundle resource. The implementation is understandable, fail-closed, secret-safe, and consistent with the README's `MEDIUM`/`0.5 DBU/hour` envelope.

The new negative test proves that an observed `LARGE` deployment:

1. returns a nonzero result;
2. produces a specific `Expected stopped MEDIUM deployment` error;
3. never reaches `bundle run dbtobsb_smoke`;
4. still invokes the idempotent App stop; and
5. finishes the simulated remote state as `STOPPED`.

No usability, accessibility, recovery-copy, liveness/readiness, credential-handling, or cost-state regression was found.

## Enforcement review

### Pre-start check — Pass

`scripts/smoke_databricks_app.sh` fixes `EXPECTED_COMPUTE_SIZE='MEDIUM'`. After deployment, while cleanup is already armed, it reads both `.compute_status.state` and `.compute_size` from the live App representation.

The wrapper continues only if the App is both:

- `STOPPED`; and
- exactly `MEDIUM`.

Any missing, malformed, differently cased, unknown, or larger value fails the equality check. The error includes the expected size and safe observed state/size but no host, user, profile, token, App URL, workspace identifier, or raw JSON.

The cleanup trap remains active on this rejection path. The wrapper attempts the idempotent stop and verifies final `STOPPED` before returning, so refusal does not silently leave a drifted App running.

### Post-start recheck — Pass

After the one approved start, the wrapper again requires:

- state `ACTIVE`;
- compute size `MEDIUM`; and
- the expected HTTPS Databricks Apps URL shape.

This does not replace the pre-start gate; it detects a state/size change between observations and enters the same cleanup path. The user-facing error reports state and size without exposing the URL.

### Negative regression test — Pass

`test_smoke_wrapper_rejects_unapproved_compute_size_and_stops` injects `LARGE` through the fake live App response. It asserts the precise consequence most important to an operator: start never happens and stop still does.

The test is stronger than an isolated constant assertion because it exercises the executable wrapper, fake CLI call log, exit status, error text, and final state together.

## Usability and accessibility regression scan

### Operator comprehension — Pass

- `MEDIUM` is named in both the approved runbook envelope and runtime rejection.
- The error distinguishes expected versus observed values.
- Rejection occurs before the billable start action.
- The command fails rather than silently substituting a cheaper or more expensive size.
- Cleanup success retains the explicit `STOP VERIFIED: App compute state is STOPPED.` terminal message.
- Cleanup uncertainty retains prominent continuing-cost language and copy-ready recovery commands.

### Terminal accessibility — Pass

The new message is linear plain text, begins with the expected condition, includes the observed state, and does not depend on color, cursor movement, animation, or an interactive prompt. It remains understandable to screen-reader users and in copied support output.

### Secret and Personal Data safety — Pass

The new fields are non-sensitive compute state/size enums. Existing protections remain unchanged:

- shell tracing and ambient token/client-secret authentication are refused;
- exact OAuth U2M host and user context are verified before mutation;
- the token never enters process arguments or output;
- `curl` remains restricted to HTTPS/TLS with user configuration disabled; and
- tests continue to prove the token is absent from arguments, stdout, and stderr.

### Liveness and documentation surfaces — No regression

- `/api/health` remains explicitly process liveness with readiness `not_evaluated`.
- `/api/openapi.json` retains stable operation IDs, summaries, response descriptions, tags, and examples.
- `/docs` and `/redoc` remain disabled, so no public CDN-backed documentation UI reappears.
- The App remains unbound and stopped by default.

## Scope boundary

This review approves the executable `MEDIUM` state check and its local regression proof. The ten-minute timer/cancellation deadline is an explicit attended runbook control; this report does not mislabel it as an internally enforced wrapper timeout. The focused task did not authorize or require a second paid live run.

The official [Azure Databricks App compute-size reference](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/compute-size) currently lists `Medium` at `0.5 DBU` per hour and as the default size when none is specified. The wrapper nevertheless validates the remote value rather than trusting that default.

## Validation performed

```text
uv sync --project app --locked --extra dev
Resolved 31 packages
Checked 30 packages

uv run --project app --extra dev pytest
11 passed in 3.50s

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

No Databricks, Azure, authentication, or other cloud call was made.

## Final disposition

**`PASS`.**

The P0 App smoke implementation at hash `3dfdce3c354b858a252904190ccbca7689d10fe883a818910c897acb9dcd3866` enforces the reviewed live size before start and fails safely with clear operator-facing evidence when the remote size is not `MEDIUM`. The eleventh test protects the no-start/stop/verified-final-state behavior without weakening any previously approved usability or accessibility control.
