# P2 native collector final resolution

- Date: 2026-07-16
- Intended tag: `v0.2.0-alpha.1`
- Authoring-set manifest: [author-set.sha256](author-set.sha256)
- Authoring-set SHA-256:
  `b09ac6b72039490080ce7f2ea1dcb00a604f3388f1c5b81215e979e590304898`
- Disposition: **accepted for the private personal/test, synthetic-data,
  combined-role engineering preview**
- Production disposition: **not production, regulated, Marketplace, or
  Databricks App readiness**

## Final verdicts

| Review lens | Report | Verdict |
| --- | --- | --- |
| Azure Databricks platform | [databricks.md](databricks.md) | `PASS` |
| dbt Core and artifacts | [dbt-core.md](dbt-core.md) | `PASS` |
| Product usability/onboarding | [usability.md](usability.md) | `PASS` |
| Diataxis information architecture | [documentation-ia.md](documentation-ia.md) | `PASS` |
| FastAPI-style writing | [documentation-style.md](documentation-style.md) | `PASS` |
| Documentation security/compliance | [documentation-security.md](documentation-security.md) | `PASS` |
| Documentation usability/accessibility | [documentation-usability.md](documentation-usability.md) | `PASS` |

All three product specialists independently recalculated the 64-file manifest.
The usability reviewer separately performed the three documentation passes.
No blocking finding remains.

## Accepted product contract

Databricks preserves the native dbt task archive. The collector correlates one
terminal dbt task attempt, preserves the exact bounded archive in a managed
Unity Catalog Volume, validates the exact primary artifact paths and pinned dbt
schemas, normalizes an allowlist, and publishes one attempt root, invocation,
and node results through typed Spark and fixed Delta operations.

Object creation is separate:

- `BOOTSTRAP_ALLOWED` is an explicit fixed, versioned, idempotent operation.
  An authorized administrator may intentionally use it to create or verify
  product objects in production.
- `RUNTIME_DML_ONLY` is ordinary collection. It has no runtime bootstrap
  switch and performs only the fixed persistent writes against existing
  evidence objects.

The invalid behavior is implicit DDL during ordinary collection, not production
object creation itself.

## Quality and live evidence

- capture `0.2.0a3`: 114 tests, Ruff, formatting, `ty`, and wheel build;
- collector `0.2.0a14`: 25 tests, Ruff, formatting, `ty`, and wheel build;
- App shell `0.1.0`: 13 tests, Ruff, formatting, and `ty`;
- Bundle validation with Databricks CLI `1.7.0`;
- Bash syntax, ShellCheck, fixture/schema parity, and Markdown link checks;
- final Azure bootstrap, dbt build, and collector Jobs all `SUCCESS`;
- final capture `COMPLETE`, pair `PAIR_VALID`, one invocation, nine nodes;
- identical replay kept the digest, timestamps, and row counts unchanged; and
- final inventory: zero active Job runs, warehouses, and clusters, with App
  compute `STOPPED`.

The retained Delta tables and raw Volume archives can incur storage charges.
Their retain-or-delete decision remains explicit and owner-controlled.

## Retained nonblocking gates

Before any broader claim, qualify dedicated identities and Job ACLs, sealed
source/destination parameters, complete bootstrap ownership/grant/property/view
verification, bootstrap-authority retirement, vendor-backed internal transport,
custom-profile behavior, native failed and partial live captures, retention and
legal hold, SBOM/signing, upgrades and rollback, Marketplace packaging,
rendered-site accessibility, and regulated production operation.

## Git and release binding

The private release tag `v0.2.0-alpha.1` must point to the merged `main`
commit containing this resolution and the exact authoring manifest. The release
process verifies the tag target, GitHub checks, repository privacy, and final
zero-running-compute inventory before publication. Review records themselves
are outside the frozen authoring set; they record independent verdicts over it.
