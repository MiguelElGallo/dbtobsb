# Pass 2: how-to FastAPI-style review

- Scope: every how-to command, input, output, failure branch, and point-of-need link
- Initial verdict: `CHANGES_REQUIRED`
- Review date: 2026-07-18

## Findings

1. A first-time administrator had to invent `dbt_project.yml` and `selectors.yml`.
2. Installation prerequisites named tools but did not show checks.
3. Package locking, installer errors, SQL execution context, empty results, recovery
   timing, uninstall receipts, and evidence-object verification required guesswork.
4. Several phrases described internal mechanisms where a direct outcome would be
   clearer.

## Resolution

- Added copyable YAML and SQL, a small project tree, a complete repository example,
  official references, and the expected installer preview.
- Added copyable local tool, release-tag, authentication, and identity checks.
- Named dependency files and their lock workflow; linked installer onboarding errors
  back to the source checks.
- Added a real sanitized healthy-row link, a computed recovery-lease field, both
  uninstall receipts, and one SQL query that verifies the nine product objects.
- Replaced avoidable terms such as “sealed” and “bindings” in task instructions.

## Re-review target

The whole-site clarity pass must confirm that a reader can move from project files
to installation, first run, investigation, recovery, and shutdown without an
undocumented input.
