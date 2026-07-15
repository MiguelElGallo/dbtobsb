# Pair validity, dbt outcome, and capture state

Three different questions can describe the same dbt run. Treating them as one status creates false success and false completeness.

| Question | P1.1 evidence | Example answer |
| --- | --- | --- |
| Do these two files form a trusted pair? | Full schema and semantic checks across `manifest.json` and `run_results.json`. | `PAIR_VALID` |
| What did dbt record for its resources? | Native statuses in a valid `run_results.json`. | one `error` |
| Did dbtobsb capture all required attempt evidence? | Later Databricks attempt, archive retrieval, artifacts, and structured-log evidence. | not evaluated by P1.1 |

A pair can therefore be valid while dbt failed. The `valid_dbt_failure` fixture is intentional: it produces `PAIR_VALID` with `error=1`. The inspector preserves native dbt status instead of rewriting evidence validity as job success.

Conversely, a successful Databricks task cannot make a malformed or mismatched pair valid. Outer Lakeflow state answers whether and how an attempt ran; it does not repair artifact identity or schema violations.

## Why P1.1 does not say `COMPLETE`

The future capture-state engine also needs to know whether the native archive was retrievable, whether required artifacts were present, how early failures and cancellation were represented, and what structured logs prove. P1.1 receives none of that context. Calling a pair `COMPLETE` would overstate the evidence.

Use `PAIR_VALID` and `PAIR_INVALID` only for this local contract. Use native status counts only for dbt outcomes. Introduce capture-state labels only after the later collector supplies and validates the outer evidence.

## Security benefit

This separation allows ordinary output to stay allowlisted. P1.1 can answer the pair question without reproducing raw SQL, messages, environment values, paths, relations, project names, resource IDs, or invocation IDs. Restricted raw evidence remains outside the ordinary report.

To learn with fixtures, use [Inspect an artifact pair](../tutorials/inspect-an-artifact-pair.md). To recover from a failure, use [Diagnose an invalid artifact pair](../how-to/diagnose-an-invalid-artifact-pair.md). Before substituting real files, follow [Handle raw dbt artifacts safely](../how-to/handle-raw-dbt-artifacts-safely.md). For the custody model, read [Why safe reports do not make raw artifacts safe](raw-artifact-custody.md).
