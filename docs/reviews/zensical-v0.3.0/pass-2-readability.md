# Pass 2: FastAPI-style readability

- Scope: first-time reader path, commands, examples, expected output, and glossary
- Verdict: `CHANGES_REQUIRED`, then resolved
- Review date: 2026-07-18

## Findings

1. The dbt-project onboarding guide used an undefined target placeholder and did
   not explain the seven required fields or its success receipt.
2. The lifecycle guide used workspace-wide inventory commands and did not prove
   the App state, reconciler schedule, or absence of product Jobs.
3. The recovery query omitted the reconciliation run ID referenced by the next
   step.
4. The home-page heading claimed coverage for every dbt run rather than every
   observed dbt run.
5. Several first-use terms were absent from the glossary, and two fixed platform
   compatibility values were unexplained.
6. The tutorial's final compute checkpoint did not give the reader a precise
   verification path.

## Resolution

- Replaced the onboarding placeholder with a structurally valid synthetic target,
  defined every field, documented generated files, and showed the exact receipt
  shape. The command was executed locally against `qualification_dbt` and returned
  `DBT_ONBOARDING_REVIEW_READY`.
- Replaced broad inventory checks with exact App and Job-name checks, expected
  values, active-run checks by Job ID, and retain-versus-delete evidence checks.
- Added `last_reconciliation_run_id` to the recovery query.
- Narrowed the home-page promise to observed runs.
- Added definitions for Bundle, Databricks App, normalized evidence, sealed
  project, serverless compute, service principal, and Unity Catalog Volume. Linked
  important first uses and explained Bundle engine `Direct` and environment client
  `5`.
- Linked the tutorial to the scoped final-state verification and explained the SQL
  warehouse auto-stop interval.

## Re-review result

`PASS`: the primary path now uses short sections, runnable examples, visible
results, plain definitions, and progressive disclosure without hiding operational
decisions.

Pass 3 later found that the standalone onboarding example was an internal entry
point rather than the supported operator route. It was replaced with the attended
`dbtobsb bootstrap` flow; the readability requirements were retained there.
