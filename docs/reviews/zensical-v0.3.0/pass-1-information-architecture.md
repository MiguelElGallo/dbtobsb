# Pass 1: Diátaxis information architecture

- Scope: `docs/site`, reader entry points, and Zensical navigation
- Verdict: `CHANGES_REQUIRED`, then resolved
- Review date: 2026-07-18

## Findings

1. The former home page was a repository inventory rather than a reader entry
   point.
2. Production installation was labeled as a tutorial even though it requires real
   resource and governance decisions.
3. Historical v0.2 pages and internal review evidence competed with the supported
   route.
4. Audience-first operator and developer trees hid the four documentation modes.
5. The evidence reference omitted `dbt_collection_health`.
6. The explanation set did not provide an end-to-end product model.

## Resolution

- Added a reader-only `docs/site` tree and made it the Zensical `docs_dir`.
- Made Tutorials, How-to guides, Reference, and Explanation the four top-level
  sections.
- Moved installation to How-to guides and created a choice-free first-run tutorial.
- Kept plans, decisions, dated evidence, and historical pages outside site
  navigation and search.
- Reduced the old home, operator, and developer entry pages to compatibility
  pointers.
- Added complete coverage for all three health views and short explanation pages
  for capture flow, outcome separation, separate collector authority, customer-local
  data, and compute.

## Re-review result

`PASS`: each navigated page has one dominant Diátaxis purpose, current v0.3 tasks
are reachable from Home, and no historical or future capability appears in customer
navigation.
