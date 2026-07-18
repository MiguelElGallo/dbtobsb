# Pass 3: how-to implementation review

- Scope: how-to claims traced to installer, collector, contracts, tests, and release
  evidence
- Initial verdict: `CHANGES_REQUIRED`
- Review date: 2026-07-18

## Findings

1. The two required source YAML files and generated `profiles.yml` were described
   correctly but not demonstrated.
2. The documented location could be read as allowing a project at the repository
   root. That would expose `.git` and `.github` to the source scan and fail.
3. Profile and selector name rules, prohibited project keys, hidden-file and
   symbolic-link rejection, and dependency-lock rules were undocumented.
4. Recovery omitted the no-row and older-than-24-hours branches; SQL investigations
   were unbounded; lifecycle checks used undeclared `jq`.

## Resolution

- Required an isolated child directory and showed its exact minimum tree.
- Added the accepted-input reference with required, generated, ignored, and rejected
  inputs, name patterns, file limits, and dependency rules.
- Added the fixed 24-hour recovery boundary, seven-day query windows, 100-row result
  limits, and the `jq` prerequisite.
- Ran all 15 installer onboarding tests against the same contract; they passed.

## Re-review target

The final validation must run the strict Zensical build, local-link check, targeted
onboarding tests, and publication-safety checks before publication.
