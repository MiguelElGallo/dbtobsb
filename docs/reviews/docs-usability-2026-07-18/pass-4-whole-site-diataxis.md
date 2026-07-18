# Pass 4: whole-site Diátaxis review

- Scope: `docs/site`, Zensical navigation, reader journeys, and cross-links
- Initial verdict: `CHANGES_REQUIRED`
- Final verdict: `PASS`
- Review date: 2026-07-18

## Findings

1. The project-preparation guide linked a complete qualification directory that
   contained a local `profiles.yml`, reintroducing the three-source-file ambiguity.
2. Recovery did not name its SQL access, warehouse, placeholder, and Job-manager
   prerequisites before the first command.
3. The first-run tutorial did not identify the exact synthetic project behind its
   captured counts.

## Resolution

- Added and linked a clean `examples/customer_weather` project containing only the
  two source YAML files and one model.
- Added a recovery prerequisite section before the first action.
- Linked the tutorial to the exact qualification project, tied the recorded counts
  to it, and labeled its profile as local-only and ignored during installation.

## Re-review result

`PASS`: preparation, installation, first run, investigation, recovery, and
lifecycle tasks form a complete route. Exact file rules remain in Reference, while
task choices and actions remain in How-to guides.
