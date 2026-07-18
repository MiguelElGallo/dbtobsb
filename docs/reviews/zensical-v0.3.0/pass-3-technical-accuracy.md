# Pass 3: Databricks and dbt technical accuracy

- Scope: commands, lifecycle, compute, dbt project handling, and evidence claims
- Verdict: `CHANGES_REQUIRED`, then resolved in two focused re-reviews
- Review date: 2026-07-18

## Findings

1. The first onboarding guide exposed an internal target-document command. The
   supported launcher derives those values from authenticated preflight.
2. The source project was said to require `profiles.yml`, although the installer
   excludes it and generates the runtime profile.
3. App compute was documented only for explicit start, then as one installation
   start. Installation actually performs two bounded App deployment checks.
4. Project replacement incorrectly included `stop` as a route to fresh install.
5. The home-page node list omitted snapshots and other accepted result types.

## Resolution

- Routed project onboarding only through attended `dbtobsb bootstrap`; marked the
  standalone generator as an internal entry point.
- Documented the generated, credential-free profile and removed the source-profile
  requirement.
- Documented both bounded App deployment checks and the stop verification after
  each one.
- Required uninstall under retention policy, then a new empty evidence schema, for
  project replacement. Clarified that stop alone preserves the installation.
- Changed the result description to every accepted dbt result node and named common
  types, including snapshots.

## Re-review result

`PASS`: commands, approvals, exact App and Job names, compute transitions, dbt
project rules, supported versions, and lifecycle boundaries match the v0.3.0
implementation and support contract.
