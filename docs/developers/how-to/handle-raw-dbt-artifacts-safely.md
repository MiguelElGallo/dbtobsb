# Handle raw dbt artifacts safely

Use this guide before substituting real `manifest.json` or `run_results.json` files for the synthetic P1.1 fixtures. The outcome is a local inspection whose inputs, copies, support evidence, retention, and deletion remain inside the customer's approved controls.

## Before you begin

You need:

- an accountable data or security owner for the evidence;
- a policy-approved local execution host and storage location;
- least-privilege access for the people performing the inspection;
- the applicable classification, retention, deletion, backup, and legal-hold decision; and
- the repository root and a P1.1 runtime created by the tutorial's locked `uv sync --project capture --locked --no-dev` command from the customer-approved registry, mirror, or cache.

Raw artifacts can contain Personal Data, credentials or other secrets, SQL, messages, paths, database and relation topology, project/resource/invocation identities, and operational metadata. P1.1 has no evidence-upload endpoint.

## 1. Place every copy under approved controls

Keep originals, extracts, temporary copies, and backups only in the approved storage boundary. Apply required encryption, access logging, endpoint controls, and transfer restrictions. Do not commit, upload, paste into chat, or attach a raw artifact or fragment to an ordinary support ticket.

If the approved boundary or accountable owner is unclear, stop before reading the files.

## 2. Inspect the pair locally

Run the inspector on two existing, closed, non-symlink regular files no larger than 128 MiB each:

<!-- BEGIN: raw-handling-command -->

```bash
uv run --project capture --no-sync dbtobsb-capture inspect-artifact-pair \
  --manifest /approved/path/manifest.json \
  --run-results /approved/path/run_results.json \
  --json \
  --no-color
```

<!-- END: raw-handling-command -->

The CLI reads caller-owned inputs and creates no durable raw-artifact copy or external transfer. It does not delete, encrypt, relocate, govern, or make the caller's files compliant. The JSON report contains only allowlisted pair facts or static issue text; keep the raw inputs governed independently.

## 3. Limit support evidence

Use only the product version, safe command shape, exit or static issue code, and allowlisted report as the ordinary support payload. Do not include a local path, raw JSON fragment, SQL, message, identifier, or other artifact content.

If an accountable support owner exceptionally requires raw evidence, use a separately approved restricted-evidence process. It must name the authorized recipient, approved transfer method, access boundary, and retention/deletion decision before any transfer.

## 4. Complete the evidence lifecycle

Apply the approved retention or legal-hold decision to originals, extracts, temporary copies, and backups. Delete caller-owned evidence only when the approved schedule permits deletion and no legal hold applies. P1.1 does not perform or attest that deletion.

## Verify and close the handling task

Confirm that:

- every raw copy remains in approved storage with least-privilege access;
- no raw content entered source control, chat, an ordinary ticket, or an unapproved transfer;
- any support payload contains only the allowlisted report and safe context;
- any exceptional raw-evidence process has its named recipient and lifecycle decision; and
- retention, deletion, backup, and legal-hold outcomes are recorded through the customer's normal control process.

For why these controls remain necessary, read [Why safe reports do not make raw artifacts safe](../explanation/raw-artifact-custody.md). For inspection failures, use [Diagnose an invalid artifact pair](diagnose-an-invalid-artifact-pair.md). For the exact machine boundary, use [CLI, report, and exit codes](../reference/cli-report-and-exit-codes.md).
