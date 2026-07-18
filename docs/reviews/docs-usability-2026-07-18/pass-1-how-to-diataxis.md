# Pass 1: how-to Diátaxis review

- Scope: every page in `docs/site/how-to-guides` and its navigation
- Initial verdict: `CHANGES_REQUIRED`
- Review date: 2026-07-18

## Findings

1. Installation required a dbt project but neither installation nor project
   preparation showed a directory tree or usable YAML.
2. Mentioning `profiles.yml` beside the two source files made the source and
   generated-runtime roles easy to confuse.
3. “Supported selector” was undefined at the point of action.
4. Navigation placed installation before its project-preparation prerequisite.
5. Query, recovery, and lifecycle guides hid permissions, empty-result branches,
   reference links, or the `jq` dependency.

## Resolution

- Made project preparation the first how-to and the canonical source for a minimal
  tree, both source YAML files, one model, dependencies, and the installer preview.
- Stated directly that the reader supplies two YAML files and dbtobsb generates
  `profiles.yml` in the installed snapshot.
- Added the exact selector purpose and naming rules, real repository examples, and
  official dbt references.
- Added task-specific execution context, expected healthy results, recovery
  branches, and final-state checks.
- Moved exact input limits into a dedicated reference page and linked it from the
  task flow.

## Re-review target

The whole-site Diátaxis pass must confirm that project preparation remains a task
guide while the complete accepted-input contract remains reference material.
