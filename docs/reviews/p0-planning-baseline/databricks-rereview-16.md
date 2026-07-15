# Azure Databricks sixteenth re-review: planning baseline 0.18

- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform reviewer
- Planning author-set SHA-256: `64ccac49c9cb91656a609fa432b32dc4c9ba451134f5577a722051806e23f8d9`
- Live-evidence SHA-256: `90d18fdf3412e324f0250a40024a5e95467ecff34096d53462974067d7129e74`
- Verdict: `PASS`
- Cloud activity: None. This focused re-review made no Azure, Databricks, authentication, SQL, App, Job, warehouse, cluster, or Unity Catalog call.

## Immutable input verification

I recomputed the globally sorted author path-and-content digest for `README.md`, `AGENTS.md`, `docs/index.md`, and all Markdown under `docs/decisions`, `docs/plans`, and `docs/research`. It matched exactly:

```text
64ccac49c9cb91656a609fa432b32dc4c9ba451134f5577a722051806e23f8d9
```

I separately recomputed the sanitized evidence digest. It matched exactly:

```text
90d18fdf3412e324f0250a40024a5e95467ecff34096d53462974067d7129e74
```

No author, evidence, or implementation file was edited by this reviewer. This report is outside the frozen author set.

## Focused resolution review

### DBX-P0-032 is resolved

The source register now separates three exact platform facts:

1. `App status and cost` links to `key-concepts#app-status` and accurately states that running Apps incur compute cost while stopped Apps are inaccessible and do not incur App-compute cost.
2. `App state persistence` links separately to `#app-state` and limits that row to ephemeral memory/local files and persistent Databricks storage.
3. `App compute size` links to the official compute-size page and records `MEDIUM` as the default at `0.5 DBU/hour`, `LARGE` at `1 DBU/hour`, plus the requirement to read back the approved live size and refresh the time-sensitive rate.

The anchors now land on the sections that directly support each claim. The current official pages corroborate every value.

### DBX-P0-033 is resolved

The P0 runbook now distinguishes all relevant cost facts instead of presenting one false ceiling:

- a ten-minute **operator cancellation deadline**;
- planned usage through that request of at most `0.084 DBU` at the published Medium rate;
- a successful-stop observation exposure of up to 30 elapsed minutes, conservatively `0.25 DBU` if the App were billable for that entire window;
- an explicit statement that no hard ceiling exists when stop fails and cost can continue until `STOPPED` is observed; and
- an explicit prohibition when policy requires a mechanically enforced hard cost ceiling.

The product-plan cost discipline uses the same semantics: cancellation is not cost cessation, failed stop remains running/unverified with continuing cost, and every live test records the cancellation deadline, planned DBUs, stop exposure, cleanup owner, and final inventory command.

The updated evidence preserves the completed run's historical process finding. It says baseline 0.18 fixes the future runbook, does not claim the original pre-run control retroactively existed, and correctly avoids a second paid run merely to erase the finding.

## Prior platform findings

| Finding | Baseline 0.18 disposition |
|---|---|
| `DBX-P0-030` - unsupported inline fence checks | `RESOLVED`; exact create, property, eleven separate add-constraint operations, full readback/recovery, and singleton-last sequence remain unchanged. |
| `DBX-P0-031` - omitted terminal legacy `INTERNAL_ERROR` | `RESOLVED`; current-first/legacy-fallback projection, terminal failure handling, conflict/unknown denial, and final inventory remain unchanged. |
| `DBX-P0-032` - incorrect/missing cost source registration | `RESOLVED`; exact status, state, and compute-size sources are now separate and current. |
| `DBX-P0-033` - 0.084 DBU mislabeled as a maximum | `RESOLVED`; planned budget, successful-stop exposure, unbounded failure tail, and policy prohibition are explicit. |

No regression was found in the private App/Direct Bundle boundary, customer-local storage/compute model, optional-system-data isolation, App staging and stop protocol, runtime-trust design, or P6 fence/Jobs terminality contracts.

## Live-evidence assessment

The evidence remains sanitized and does not overclaim:

- it contains no workspace URL, account/workspace/user/App/SP identifier, credential, signed URL, raw log, or customer payload;
- it identifies one technical process-liveness smoke, not dbt, capture, dependency, authorization, or product readiness;
- it records zero starting Apps, warehouses, and clusters and a one-App-create Bundle plan without pretending the later readback was independently attested;
- it retains the missing pre-run cost record as a process nonconformance;
- its 2 minute 52 second whole-window calculation at 0.5 DBU/hour is correctly below 0.024 DBU and is explicitly a derived upper bound rather than an invoice;
- it reports the stopped App object and uploaded Bundle files as residual non-running objects; and
- it reports final `STOPPED`, zero non-stopped Apps, zero bindings, no pending deployment reported, and zero warehouses/clusters without expanding that evidence into a broader platform claim.

## Sources checked

- [Databricks Apps status and state](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts#app-status)
- [Databricks Apps compute sizes](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/compute-size)
- [Azure Databricks `CREATE TABLE [USING]`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-syntax-ddl-create-table-using)
- [`ALTER TABLE ... ADD CONSTRAINT`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-syntax-ddl-alter-table-add-constraint)
- [Pinned first-party Jobs lifecycle enum](https://github.com/databricks/databricks-sdk-go/blob/bad015296869703de251d189b8a43ea4e6df8bfb/service/jobs/model.go#L4129-L4177)

## Verdict

`PASS`

Baseline 0.18 accurately represents current Azure Databricks App status, compute size, DBU rate, and stop-cost semantics. Both new follow-ups are resolved, prior P6 platform findings remain resolved, the live evidence is honest and sanitized, and no Azure Databricks platform blocker remains.
