# Azure Databricks fifteenth re-review: planning baseline 0.17

- Date: 2026-07-15
- Reviewer: Independent Azure Databricks platform reviewer
- Planning author-set SHA-256: `83be89fd59fe16c023c7e4b7fb6f336d6ab27d44c7c0ebf03a7d862a2a43ce97`
- Live-evidence SHA-256: `6d1a6e133ce98b01e976a12ea8837733dd0cd1198dddb5ad3225ff0b04f8073a`
- Verdict: `PASS_WITH_FOLLOW_UP`
- Cloud activity: None. This review made no Azure, Databricks, authentication, SQL, App, Job, warehouse, cluster, or Unity Catalog call.

## Immutable input verification

Before the author set advanced, I read the frozen baseline 0.17 inputs: `README.md`, `AGENTS.md`, `docs/index.md`, and every Markdown file under `docs/decisions`, `docs/plans`, and `docs/research`, globally sorted by path. I reproduced the requested aggregate path-and-content digest exactly:

```text
83be89fd59fe16c023c7e4b7fb6f336d6ab27d44c7c0ebf03a7d862a2a43ce97
```

I separately reproduced the sanitized live-smoke evidence digest exactly:

```text
6d1a6e133ce98b01e976a12ea8837733dd0cd1198dddb5ad3225ff0b04f8073a
```

This report preserves the review of those immutable inputs even though baseline 0.18 subsequently superseded them. No author, evidence, or implementation file was changed by this reviewer.

## Executive assessment

Baseline 0.17 had no remaining Azure Databricks architecture or platform blocker. The private App plus Direct Bundle direction remained appropriate, the required path stayed customer-local and GA-first, and no external telemetry dependency was introduced.

The two prior P6 blockers remained resolved:

- `DBX-P0-030` was resolved. The normative fence contract used one managed Delta `CREATE TABLE` with explicit `DEFAULT COLLATION UTF8_BINARY`, a separate `Serializable` property operation, eleven separate `ALTER TABLE ... ADD CONSTRAINT` operations, complete partial-state readback/recovery, and the singleton insert last. It no longer used unsupported inline Delta `CHECK` clauses.
- `DBX-P0-031` was resolved. The Jobs projection preferred current `status`, used deprecated `state` only when current status was wholly absent, treated legacy `TERMINATED`, `SKIPPED`, and `INTERNAL_ERROR` as terminal, retained exact safe enums, and kept conflict, unknown, denied, deleted, malformed, and pagination-incomplete evidence indeterminate.

The live record was sanitized and appropriately narrow. It disclosed the missing pre-run numeric cost record as a historical process nonconformance, did not retroactively call the run compliant, separated technical liveness from product readiness, identified the same-operator post-run readback as non-independent, and stated that the stopped App object and Bundle files remained. Its observed 2 minute 52 second object-create-to-`STOPPED` window at 0.5 DBU/hour gives the stated conservative post-run bound below 0.024 DBU.

Two cost-documentation follow-ups remained. Neither invalidated the completed, stopped live run or the platform architecture, but both needed correction before another paid smoke.

## Current primary sources checked

- [Databricks Apps key concepts](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/key-concepts#app-status) currently states that a running App is billed and accessible, while a stopped App is inaccessible and incurs no cost. It does not say a stop request itself ends billing.
- [Databricks Apps compute sizes](https://learn.microsoft.com/en-us/azure/databricks/dev-tools/databricks-apps/compute-size) currently publishes `Medium` as the default, up to 2 vCPUs and 6 GB, at `0.5 DBU/hour`; `Large` is `1 DBU/hour`.
- [Azure Databricks `CREATE TABLE [USING]`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-syntax-ddl-create-table-using) directs Delta `CHECK` constraints to `ALTER TABLE` and supports explicit table default collation.
- [`ALTER TABLE ... ADD CONSTRAINT`](https://learn.microsoft.com/en-us/azure/databricks/sql/language-manual/sql-ref-syntax-ddl-alter-table-add-constraint) provides the enforced Delta `CHECK` operation used by the ordered fence envelope.
- The pinned first-party [`RunLifeCycleState`](https://github.com/databricks/databricks-sdk-go/blob/bad015296869703de251d189b8a43ea4e6df8bfb/service/jobs/model.go#L4129-L4177) includes legacy `INTERNAL_ERROR` among terminal lifecycle states.

## Findings

### DBX-P0-032: cost and compute-size sources were not registered at the exact supporting anchors

- Severity: Low
- Verdict effect: Non-blocking follow-up
- Affected input: baseline 0.17 `docs/research/source-register.md`, former App-state-and-cost row
- Evidence: The row linked to `key-concepts#app-state` while its stopped-App cost claim is documented under `#app-status`. The same source register did not contain the compute-size page that supports the new `MEDIUM` and `0.5 DBU/hour` claim, although `README.md` linked that page directly.
- User/system impact: A reviewer following the registered anchor landed on persistence semantics rather than the cost statement, and the time-sensitive numeric rate was not represented in the dated primary-source inventory.
- Required change: Split status/cost from persistence, point the cost row to `#app-status`, and add the official compute-size source with its current rate, default-size fact, live readback requirement, and refresh trigger.
- Disposition: Resolved in baseline 0.18 and verified by the sixteenth re-review.

### DBX-P0-033: 0.084 DBU was labeled as a conservative maximum without the stop tail

- Severity: Medium
- Verdict effect: Non-blocking for the completed P0 proof; correction required before another paid smoke
- Affected inputs: baseline 0.17 `README.md`, P0 cost envelope; cost-discipline language in `docs/plans/product-plan.md`; explanatory sentence in the live evidence
- Evidence: The arithmetic `0.5 × 10 / 60 = 0.0833...`, rounded up to `0.084 DBU`, was correct for ten minutes. The label was not. The wrapper relied on an attended external ten-minute timer, then allowed `databricks apps stop --timeout 20m`. Current platform documentation guarantees no App-compute cost after `STOPPED`; it does not make the cancellation or stop request a cost-cessation point. A delayed or failed stop can therefore exceed 0.084 DBU.
- User/system impact: An operator could read a planned cancellation budget as a mechanically enforced cost ceiling and underestimate exposure during stop or control-plane failure.
- Required change: Label 0.084 DBU as planned usage through the operator cancellation request, disclose the successful-stop observation window and its conservative exposure, say explicitly that there is no hard ceiling if stop fails, require cost escalation until `STOPPED`, and declare the smoke unsupported where policy requires a mechanical ceiling.
- Disposition: Resolved in baseline 0.18 and verified by the sixteenth re-review.

## Evidence assessment

The evidence itself remained acceptable with the follow-up above:

- no host, workspace/account ID, user, App/SP ID, token, signed URL, raw log, or customer payload was retained;
- the exact health response was non-sensitive and claimed process liveness only;
- the one wrapper invocation was not described as proof of one internal deployment POST;
- final App, warehouse, and cluster state was reported separately from the successful endpoint response;
- the historical cost-control deficiency remained visible instead of being erased by a second paid run; and
- the computed post-run bound was explicitly a derived estimate rather than an invoice or billing-table attribution.

## Verdict

`PASS_WITH_FOLLOW_UP`

Baseline 0.17 had no platform blocker and kept `DBX-P0-030` and `DBX-P0-031` resolved. The source-register precision and cost-ceiling wording needed the two bounded follow-ups above before reuse. Both were subsequently resolved without changing the platform architecture or rerunning paid compute.
