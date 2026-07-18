# Pass 4: Security and regulated-use safety

- Scope: permissions, sensitive-data boundaries, retention, deletion, and claims
- Verdict: `CHANGES_REQUIRED`, then resolved
- Review date: 2026-07-18

## Findings

1. The internal caller-supplied onboarding route bypassed supported bootstrap
   discovery and approval.
2. Piped uninstall acknowledgements let destructive prompts be prequeued.
3. The access table omitted workspace-file authority, observed-to-collector run
   authority, and the resulting trusted-root consequence.
4. The customer-local statement omitted the workstation installer and its sensitive
   state file.
5. Pair validity wording implied origin and custody assurance that the inspector
   cannot provide.

## Resolution

- Kept connection and destination choices inside attended bootstrap.
- Made retain and delete acknowledgements interactive, with the legal-hold and
  export warning read before the second delete phrase.
- Added the deployed workspace and Job grants and identified the managing group as
  a code and deployment trusted root.
- Narrowed the locality claim to captured evidence and runtime compute. Documented
  local state contents, owner-only custody, resume behavior, and uninstall cleanup.
- Explained that pair validity checks matching invocation IDs and schema, not
  origin, non-modification, or custody.

## Re-review result

`PASS`: no unsupported compliance claim, unsafe destructive shortcut, Personal
Data wording problem, leaked real identifier, or unresolved least-privilege
omission remains in the reader site.
