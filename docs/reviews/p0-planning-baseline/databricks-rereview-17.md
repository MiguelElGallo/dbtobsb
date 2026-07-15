# Azure Databricks seventeenth re-review: planning baseline 0.19

- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform reviewer
- Planning author-set SHA-256: `703ae3cc1a86bee5d641c7fa478fbb49bdd88cd193f2aec36e61e9b00078eb5f`
- Live-evidence SHA-256: `d4904dc48dd8d803d258e58845da929418d5f11dbb55a805aa919c9fbb71c0c2`
- Private run-record template SHA-256: `172ae9825e5e7383526fd2879fe4deb29df3a24ac972c63fd37559484f4d310b`
- Verdict: `PASS`
- Cloud activity: None. This freeze review made no Azure, Databricks, authentication, SQL, App, Job, warehouse, cluster, or Unity Catalog call.

## Immutable input verification

I recomputed the globally sorted path-and-content digest for `README.md`, `AGENTS.md`, `docs/index.md`, and all Markdown under `docs/decisions`, `docs/plans`, and `docs/research`. It matched exactly:

```text
703ae3cc1a86bee5d641c7fa478fbb49bdd88cd193f2aec36e61e9b00078eb5f
```

I separately recomputed the two freeze artifacts. They matched exactly:

```text
d4904dc48dd8d803d258e58845da929418d5f11dbb55a805aa919c9fbb71c0c2  docs/evidence/p0-live-smoke-2026-07-15.md
172ae9825e5e7383526fd2879fe4deb29df3a24ac972c63fd37559484f4d310b  docs/templates/p0-smoke-run-record.md
```

The initially assigned evidence digest `38776974661df41496df8a4bc7ec6531fb9735f5a26f46d198a90d37cd2a9c8e` was superseded only by correcting its README reproduction anchor. The initially assigned template digest `ce03f3d979057e5a834f5839e6b8a50a519addcf3c7a99b9bdb595513797ad9e` was superseded by adding the required private accountable-person cleanup reference. This report binds only the final digests above.

No author, evidence, template, or implementation file was edited by this reviewer. This report is outside the frozen inputs.

## Baseline 0.19 freeze assessment

### Dedicated-workspace contract is explicit and fail-closed

The P0 route now supports only an attended, dedicated smoke workspace for which the OAuth U2M user has approved complete inventory visibility. Before mutation, the runbook and wrapper require:

- no visible App except an optional `dbtobsb-smoke` that is `STOPPED`, unbound, and `MEDIUM`;
- zero visible SQL warehouses and clusters;
- the exact CLI, profile, canonical host, authentication type, and user; and
- an approved private run record with the starting inventory and visibility assertion.

The documentation does not turn caller-visible inventory into an administrator-resistant platform claim. It explicitly rejects shared or partially visible workspaces and says never to stop or delete unrelated resources to make the preflight pass. The final readback is equally narrow: exactly one stopped, unbound, Medium P0 App and zero visible warehouses/clusters, with any other result treated as failed cleanup proof rather than permission to mutate unrelated objects.

This is an appropriate bounded contract for the attended P0 proof. A reusable P3 installer must bind ownership and visibility more strongly; that remains product hardening rather than a defect in the frozen dedicated-workspace route.

### Cost and source claims are current and arithmetically correct

Current official Azure Databricks documentation continues to state:

- a running App incurs App-compute cost;
- a stopped App is inaccessible and incurs no App-compute cost;
- `MEDIUM` is the default size at `0.5 DBU/hour`; and
- `LARGE` is published at `1 DBU/hour`.

Baseline 0.19 uses the exact status and compute-size sources and preserves the required distinction among:

1. the ten-minute operator cancellation deadline;
2. planned usage through that deadline of `0.084 DBU` (`0.5 * 10 / 60 = 0.08333...`, rounded upward);
3. the conservative successful-stop exposure of `0.25 DBU` across the planned 30-minute window; and
4. the unbounded tail when stop cannot be verified.

It does not call cancellation cost cessation, does not call `0.084 DBU` a hard ceiling, keeps DBUs separate from currency, and prohibits the smoke when policy requires a mechanically enforced hard monetary ceiling.

### Private run record closes the historical process gap

The final copy-only template records all inputs required before another paid run:

- approval state, private reference, approval time, and approver role;
- cleanup role plus a private accountable-person reference;
- workspace alias, complete-visibility assertion, and exact starting counts;
- App size, published DBU rate, and source-refresh time;
- wrapper start, cancellation deadline, planned DBUs, stop timeout, and successful-stop exposure;
- explicit `NONE` hard ceiling plus required risk acceptance;
- no schedule, cleanup result, retained final readback, and private evidence reference.

The template keeps real identities, hosts, IDs, and internal approval URLs out of the repository while still requiring the accountable cleanup person to be identifiable in the approved private system. Its approved example is plainly synthetic; its rejected example demonstrates that missing ownership, visibility, timing, risk acceptance, or approval cannot authorize a run.

The authorization record is an attended governance control, not a claim that this P0 shell script parses a private change-management system. The runbook states that dependency plainly.

### Live evidence remains honest

The sanitized evidence remains bound to the implementation that actually ran, `eff855524237e36909b282b5c030207b0478606e7f2b44a810082012d33f6a5c`. It does not claim that the later clean-workspace guard ran in Databricks and explicitly says those changes passed local tests only.

The record preserves the original missing cost envelope and named cleanup owner as a historical process nonconformance. Its 2 minute 52 second whole-window estimate at `0.5 DBU/hour` is correctly below `0.024 DBU` and is labeled a derived bound, not an invoice. It reports the stopped App and uploaded Bundle files as residual non-running objects, identifies the final readback as the same operator/credential context rather than independent attestation, and limits the result to App process liveness. The corrected reproduction link now resolves to the current README section.

No workspace URL, account/workspace/user/App/service-principal identifier, credential, signed URL, raw log, or customer payload is present.

## Prior Databricks findings and architecture

| Finding or boundary | Baseline 0.19 disposition |
|---|---|
| `DBX-P0-030` - unsupported inline fence checks | `RESOLVED`; managed Delta create with `UTF8_BINARY`, separate `Serializable` property operation, eleven separate `ALTER TABLE ... ADD CONSTRAINT` operations, full readback/recovery, and singleton insert last remain intact. |
| `DBX-P0-031` - missing legacy terminal `INTERNAL_ERROR` | `RESOLVED`; current `status` first, legacy `state` only when current status is absent, terminal failure handling, conflict/unknown denial, and final paginated inventory remain intact. |
| `DBX-P0-032` - incorrect or incomplete App-cost sourcing | `RESOLVED`; status, state persistence, and compute size remain separate, direct, current sources. |
| `DBX-P0-033` - planned DBUs presented as a maximum | `RESOLVED`; cancellation budget, successful-stop exposure, unbounded failed-stop tail, and policy prohibition remain distinct. |
| Customer-local regulated boundary | No regression; required data, evidence, compute, identity, audit, and retention remain in the customer's Databricks environment, with external telemetry absent and Preview telemetry optional/disabled. |
| Private App plus Direct Bundle | No regression; Marketplace remains a later packaging target, while the private App/Bundle route, stopped staging, explicit start, reconciliation, and customer-owned UC objects remain the planned product boundary. |

## Sources checked

- [Azure Databricks App status and state](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts#app-status)
- [Azure Databricks App compute sizes](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/compute-size)
- [Databricks CLI Apps commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/apps-commands)
- [Databricks CLI warehouses commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/warehouses-commands)
- [Databricks CLI clusters commands](https://docs.databricks.com/aws/en/dev-tools/cli/reference/clusters-commands)
- [Azure Databricks `CREATE TABLE [USING]`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-syntax-ddl-create-table-using)
- [`ALTER TABLE ... ADD CONSTRAINT`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-syntax-ddl-alter-table-add-constraint)
- [Pinned first-party Jobs lifecycle enum](https://github.com/databricks/databricks-sdk-go/blob/bad015296869703de251d189b8a43ea4e6df8bfb/service/jobs/model.go#L4129-L4177)

## Verdict

`PASS`

Baseline 0.19 is approved for freeze. The clean-workspace and private-approval contracts are explicit, the named cleanup owner is now durably referenceable, the current App cost/source claims and calculations are correct, the historical evidence remains honest, and no prior Databricks platform finding regressed.
