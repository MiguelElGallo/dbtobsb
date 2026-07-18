# Why data stays in Databricks

dbt artifacts are useful because they contain detailed operational context. The
same detail can include sensitive information: SQL, messages, relation names,
paths, variables, workspace structure, and Personal Data.

dbtobsb keeps its required evidence path inside the customer's Azure Databricks
workspace:

- staging files use a managed Unity Catalog Volume;
- exact archives use a separate restricted managed Volume;
- normalized evidence uses managed Delta tables;
- operators use SQL views; and
- the App runs in Databricks and receives read-only bindings to those views.

No external telemetry platform is required.

## Normalized views reduce exposure

The collector copies only reviewed fields into the evidence tables. Normal readers
do not see compiled SQL, raw messages, environment values, archive locations, or
full artifacts.

This is data minimization, not automatic declassification. Operational IDs and dbt
resource names can still be sensitive, and administrators with broad Databricks
authority remain trusted.

## The customer keeps governance responsibility

Customer-local storage lets the customer apply its own access, retention, backup,
legal-hold, export, and deletion policies. `v0.3.0` does not automate or certify
those controls.
