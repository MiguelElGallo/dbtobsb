# Compute and cost

dbtobsb uses three kinds of Databricks compute. They start and stop differently.

| Compute | When it runs | How it stops |
| --- | --- | --- |
| Serverless Lakeflow Jobs | Installation, dbt builds, collection, and manual reconciliation | Stops when each run becomes terminal. |
| Databricks App compute | During one bounded attended-installation check, and after an administrator runs `dbtobsb start` | Installation stops and verifies the App before granting viewer access. After a later start, run `dbtobsb stop`; closing the browser is not enough. |
| SQL warehouse | During the dbt target query and when the App loads data | Uses the customer warehouse's configured auto-stop policy, unless an authorized operator stops that exact warehouse. |

## Stopped by default

Installation starts and stops the App during one bounded deployment check, grants
the approved viewer group through the targeted App permission API while compute
remains stopped, and leaves it stopped with the reconciler schedule paused. The
App does not query data on page load. A viewer must select **Load observability**,
which can start the bound SQL warehouse.

## Shared customer resources

The installer uses an existing SQL warehouse. It does not create a disposable
warehouse for ordinary operation. Cleanup must therefore preserve the customer's
resource and its configuration.

Do not stop, resize, or delete a shared warehouse merely to make a test inventory
empty. Stop the exact resource only when customer policy and your authority allow
it.

## Safe finish

Every live exercise should end by checking:

- all product Job runs are terminal;
- the App is stopped;
- the reconciler schedule is paused;
- no classic cluster was created; and
- the selected warehouse is stopped or following its approved auto-stop policy.
