# Focused usability and onboarding re-review: planning baseline 0.20

- Date: 2026-07-15
- Reviewer: usability, onboarding, service-design, and accessibility specialist
- Verdict: **PASS_WITH_FOLLOW_UP**
- Open P0 usability blockers: none
- Open follow-up: `UX-P0-F03`, non-blocking for P0 and a hard P3 release gate
- Cloud/authentication activity: none

## Frozen review input

The reviewed planning-author set is exactly:

| Author file | SHA-256 |
| --- | --- |
| `AGENTS.md` | `b98568650936e701e988f743f6d2b8409f81f9483be7220a2194523b634408e3` |
| `README.md` | `c68c8931dd1f46d3b769380828b029f56f780823afc4049b5b262836b3876e76` |
| `docs/decisions/0001-private-app-bundle.md` | `83162e388b5084fb14ec450645a3294d005ee327040b2c0d806b4563e7c9de57` |
| `docs/index.md` | `d90285d2236ab8734d4a67031ca8126097e37dacba74ee369d141d3904b332ca` |
| `docs/plans/documentation-plan.md` | `c2e3eb96a76c601e9b3fbc0afd113722c74ea846ff1919334c983cd145873d14` |
| `docs/plans/product-plan.md` | `93dbe597df68d136635c85cfd5319db8469d2660bb25aaeb60257a55c1bf1aff` |
| `docs/plans/review-process.md` | `d6e2c685ea71223a798c0d1b0f42ae6ecfa4870bec4a16d325d871ba7ac38734` |
| `docs/research/source-register.md` | `2e251918e868c33d7a11b980708df73727b6b758581fbcbfb43bd0ea67961627` |

The globally sorted path-and-content aggregate reproduced exactly:

```text
e6a8d55f2b155916d52ac0c6aa6ce87941a3d8672f6dc4a0bfdb692a3fb7fd44
```

The separately reviewed user-facing records are:

| Separate input | SHA-256 |
| --- | --- |
| `docs/evidence/p0-live-smoke-2026-07-15.md` | `670f54bdcef70e458adad590e959004e08f9aa5319855104299f5813c9419ed3` |
| `docs/templates/p0-smoke-run-record.md` | `6c61dc5091358cae2b5a531c6017bb012a4d0fc869edfd22fcaa2369bf5dca69` |

All supplied hashes reproduced before this report was written. This report is outside the frozen inputs and is the only file written by this review.

## Focused verdict

Baseline 0.20 resolves the security-review wording gaps without reopening any P0 usability finding:

- the private record is accurately described as an attended procedural approval gate, not as a control the wrapper can inspect or enforce;
- secure authentication storage is a visible precondition before the live command, and plaintext-only or explicitly non-secure storage cannot satisfy the P0 route;
- the short-lived token-output command is disclosed before action as a narrow development-only P0 health-call exception with exact handling safeguards; and
- the dated evidence adds the missing credential-storage process finding while preserving the original cost-control finding and live-tested implementation hash.

No new Critical, High, Medium, or Low usability finding is opened. `UX-P0-F03` remains the only follow-up because the production signed installer and supported workstation matrix still require P3 evidence.

## Procedural approval gate — Pass

The README and private template now say the same thing: the record lives in a policy-approved external system that owns access, retention, approver identity, and audit policy; the P0 wrapper cannot read it; and the operator and approver must not authorize execution while a required field is blank or `approval_state` is not `APPROVED`.

This wording avoids a false technical-control claim. It also preserves a clear accountability chain:

- the approved record identifies the approver and accountable cleanup owner through private references;
- the starting inventory, source refresh, cancellation deadline, planned usage, successful-stop exposure, hard-ceiling acceptance, and schedule are explicit before execution; and
- cleanup result and retained evidence are completed after the run.

The blank, synthetic approved/completed, and rejected examples remain copyable and contain no live identity, host, workspace/App ID, credential, or internal-system URL.

## Secure-storage onboarding — Pass for bounded P0

The README tells the operator before the command that the wrapper sets `DATABRICKS_AUTH_STORAGE=secure`, rejects an inherited non-secure value, and cannot use a plaintext-only profile. The wrapper's focused implementation review confirms that the setting is established before every Databricks CLI call.

This matches current official Databricks behavior: OAuth U2M uses OS-native secure storage, while default login can fall back to plaintext when secure storage is unavailable unless secure mode is explicit. See [Databricks CLI authentication: token storage](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/authentication#token-storage) and [Databricks CLI troubleshooting: stored credentials](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/cli/troubleshooting#stored-credentials-error).

The P0 consequence is safe: inherited non-secure configuration receives a short refusal before tool lookup or mutation; an unavailable/unreadable secure store causes authentication to fail before inventory, validation, deploy, or start. The docs do not authorize following a CLI plaintext-fallback suggestion. A workstation without usable native secure storage is unsupported for this route.

P0 is an expert attended smoke, not the production installer. Guided secure login, unsupported-platform messaging, clean-account recovery, and exact supported OS/backend behavior remain correctly owned by `UX-P0-F03` at P3.

## P0-only token exception — Pass

The README no longer leaves an apparent contradiction between “never pass a token” and the implementation's authenticated App call. Immediately before the command it explains that:

- the operator never supplies a token or client secret;
- the wrapper obtains one short-lived U2M access token from the named profile;
- the value stays in memory;
- `curl` receives the authorization header through standard input with user/global configuration disabled;
- the token is not printed, persisted, logged, or placed in an argument; and
- the variable is cleared afterward.

The product plan and source register independently label this a development-only P0 exception. The regulated production bootstrap still prohibits token-output commands, and the plan requires this exception to be removed or replaced before that gate. The scope boundary is therefore explicit rather than implied.

## Historical evidence honesty — Pass

The evidence result is now **Technical PASS with cost-control and credential-storage process findings**. It states that the live-tested wrapper required U2M but did not force or attest secure storage, so the historical run cannot prove avoidance of plaintext fallback. It then distinguishes later local correction from historical fact: the current wrapper forces secure storage and the fake CLI tests it, but no second paid run was performed and the earlier evidence is not upgraded retroactively.

The same honesty remains for cost approval. The run lacked the complete pre-run numeric record; later runbook improvements and final `STOPPED` observation do not cure that process defect. The derived DBU figure remains a conservative bound rather than an invoice.

The P0 token use is described separately from both findings and accurately reflects the live health-call mechanism without claiming that no token ever existed.

## Prior finding disposition

| Finding set | Baseline 0.20 disposition |
| --- | --- |
| `UX-P0-001` through `UX-P0-013` | **RESOLVED / RESOLVED_AT_CONTRACT — NO REGRESSION**, except `UX-P0-F03` below. The product journey, actor modes, readiness states, accessibility contract, recovery, trust/fence distinctions, and no-guess operation remain coherent. |
| `UX-P0-F01`, `F02`, and `F04` through `F08` | **RESOLVED / RESOLVED_AT_CONTRACT — NO REGRESSION.** Cost/lifecycle consequences, scoped inventories, severity gates, action summaries, complete pre-run cost copy, and same-context evidence language remain explicit. |
| `UX-P0-F03` | **OPEN_NONBLOCKING_P0_HARD_P3_GATE.** Production signed assets, supported OS/architecture and secure-store matrix, combined/separated clean-workstation behavior, and representative non-author evidence remain future P3 work. |

## `UX-P0-F03` remains a hard P3 gate

Baseline 0.20 continues to prohibit a supported installer claim until P3 proves exact OS versions/architectures, signed assets/checksums, native secure-store behavior and safe failure, one-account combined operation, two-account separated operation and handoff ACL/session lifecycle, restart/reboot recovery, uninstall, explicit unsupported topologies, and representative non-author task success.

Neither README nor evidence claims that the P0 script is that installer. The new secure-storage guard is a current P0 safety improvement; it does not close or weaken the broader P3 gate.

## Source accessibility and secret safety

- Safety and authentication consequences appear before the live command.
- OAuth U2M and the P0-only exception are defined in plain language.
- Errors and state use linear text rather than color, animation, images, or pointer-only interaction.
- Commands use synthetic placeholders; real approval, actor, host, and evidence data stay in the private system.
- The evidence retains no token, profile material, host, user, account/workspace/App/service-principal ID, signed URL, or raw customer log.
- Liveness remains distinct from dbt, artifact, data, authorization, dependency, and product readiness.

This is source-level Markdown acceptance, not rendered-site WCAG conformance. Complete rendered-page/process validation remains deferred until those surfaces exist.

## Local validation

The frozen implementation passed the README's complete local sequence:

```text
uv sync --project app --locked --extra dev
Resolved 31 packages
Checked 30 packages

uv run --project app --extra dev pytest
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

An additional local no-cloud probe set `DATABRICKS_AUTH_STORAGE=plaintext`; the wrapper returned exit `2`, printed only `Refusing non-secure Databricks authentication storage.`, and made no command call.

No Databricks, Azure, authentication, App, Job, SQL, warehouse, cluster, Unity Catalog, or other cloud call was made, and no paid compute started.

## Final disposition

**`PASS_WITH_FOLLOW_UP`.** Baseline 0.20 has no open P0 usability blocker. Its approval control is honestly procedural, secure-storage failure is fail-before-mutation, the P0 token exception is narrow and explicit, and the historical evidence preserves both process defects. `UX-P0-F03` remains the sole usability follow-up and must close before a P3 installer/workstation combination is published as supported.
