# Why collection uses a separate Job

The observed Job and collector Job run as different service principals. This gives
each identity a smaller job.

The observed principal needs to run dbt and write the fixed staging files. It does
not need to read or change normalized evidence.

The collector principal needs to read staging, preserve raw archives, and publish
normalized rows. It does not need to own the dbt target schema or run the customer's
models.

## Collection still runs after a dbt failure

The collector edge uses Databricks' `ALL_DONE` rule. A dbt failure can therefore
leave useful manifest, run-results, or partial evidence for investigation.

Running collection inside the dbt command would make it easier for an early failure
to skip evidence handling. A separate task also lets the product show the dbt
outcome and collection outcome independently.

## Separation reduces access; it does not remove trust

People who can change either Job, deploy its code, manage the service principal, or
administer the workspace remain trusted roots. The separate identities reduce
ordinary runtime access, but they are not protection against a compromised
administrator.
