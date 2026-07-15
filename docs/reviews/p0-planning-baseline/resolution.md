# P0 baseline 0.20 final resolution

- Date: 2026-07-15
- P0 disposition: **accepted for the attended development smoke and continued product implementation**
- Production disposition: **not a production installer, dbt observability product, or Marketplace release**

## Frozen inputs

| Input | SHA-256 |
| --- | --- |
| Planning author set | `e6a8d55f2b155916d52ac0c6aa6ce87941a3d8672f6dc4a0bfdb692a3fb7fd44` |
| Sanitized live evidence | `670f54bdcef70e458adad590e959004e08f9aa5319855104299f5813c9419ed3` |
| Private run-record template | `6c61dc5091358cae2b5a531c6017bb012a4d0fc869edfd22fcaa2369bf5dca69` |
| P0 App implementation | `8b1865cd05ba5abbeef6634d80e01778affe5b03ee76cbdfe919be3d84355101` |

Planning author-set hash scope is `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, sorted by path and hashed with SHA-256. Evidence, template, implementation, and review records are bound separately.

## Final review verdicts

| Part | Databricks | dbt Core | Usability | Documentation specialists |
| --- | --- | --- | --- | --- |
| Planning baseline 0.20 | `PASS` | `PASS` | `PASS_WITH_FOLLOW_UP` | Diataxis `PASS_WITH_FOLLOW_UP`; FastAPI style `PASS`; security `PASS`; docs usability/accessibility `PASS_WITH_FOLLOW_UP` |
| P0 App implementation | `PASS_WITH_FOLLOW_UP` | `PASS` | `PASS` | HTTP/runbook surfaces included in the documentation passes |

There is no open P0 blocker. `PASS_WITH_FOLLOW_UP` items are later-gate work, listed below.

## Live evidence and current cloud state

The first paid-workspace smoke ran implementation hash `eff855524237e36909b282b5c030207b0478606e7f2b44a810082012d33f6a5c`. It reached the Databricks App URL, returned the exact process-liveness body, emitted the required structured stdout event, and verified final `STOPPED`. The sanitized evidence deliberately preserves two process gaps: no complete numeric cost record existed before that run, and secure credential storage was not explicitly forced or attested.

Baseline 0.20 does not rewrite that history. The current implementation adds locally tested `MEDIUM` size enforcement, a dedicated-workspace inventory gate, and forced secure auth storage. It has 12 passing tests plus Ruff, formatting, `ty`, Bash syntax, and ShellCheck. No second paid run was performed solely to manufacture cleaner evidence.

Separate read-only checks after the live run and after the guard changes observed one stopped, unbound `MEDIUM` P0 App, no pending deployment, zero non-stopped Apps, zero SQL warehouses, and zero clusters. The stopped App object and uploaded Bundle files remain; App compute is not running.

## Material finding cycles closed

- The Delta fence install now uses an explicit `UTF8_BINARY` create, a separate Serializable property statement, eleven separate `ADD CONSTRAINT` operations, full verification, and last-step singleton insert (`DBX-P0-030`).
- Jobs terminal projection prefers current status, treats legacy `INTERNAL_ERROR` as terminal failure, and fails closed on unknown/conflicting/incomplete evidence (`DBX-P0-031`).
- The P0 runbook now records planned cost through cancellation, successful-stop exposure, unbounded failed-stop risk, an accountable cleanup owner, and exact final inventory; it does not equate `STOPPED` at the end with compliant pre-approval (`UX-P0-F07/F08`, `DBX-P0-032/033`).
- The README now leads with the runnable current slice, supports only a dedicated clean workspace, provides exact final-state commands, and links a copyable approved/rejected private record template (`DOC-STYLE-P0-001` through `004`).
- Authentication now forces secure storage before any CLI call. The development-only in-memory `auth token` health-check exception is documented without weakening the future production prohibition, and the external approval record is accurately described as an attended procedural gate (documentation security findings).

## Retained nonblocking gates

- `UX-P0-F03` is a hard P3 release gate for the signed installer, supported OS/architecture and secure-store matrix, two-account topology, and representative non-author evidence.
- `DBX-SMOKE-F05` through `F07` remain P3/P8 work: pre-existing App ownership attestation, stronger digest/evidence binding, and stop/readback/signal hardening before reusable or unattended operation.
- `DOC-IA-P0-001` remains a Low D0 gate for the planned status-first home, four Diataxis landing pages, and audience/task routes.
- Rendered browser, keyboard, responsive-layout, contrast, and screen-reader validation is **deferred**, not passed, because no complete documentation site exists.

These items do not block the attended P0 development smoke. They block the later product stage named in each report.
