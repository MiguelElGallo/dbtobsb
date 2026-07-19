# See what happened in every observed dbt run

![dbt Core observability in Databricks](images/databricks-app-logo.jpg){ width="640" loading="lazy" }

## Why dbtobsb exists

When you run dbt Core in Databricks, dbt creates a detailed log and result files.
They record what happened during that run, including whether each model and test
succeeded or failed.

Those files are useful when you investigate one job. On their own, however, they
do not give you an easy history that you can search across many jobs. Answering a
simple question such as "Which model failed yesterday?" can mean finding and
reading several separate files.

dbtobsb collects selected details from those files and stores them in Databricks
tables. It also creates read-only views that make the history safer and easier to
search. Instead of opening files one at a time, you can use SQL or the dbtobsb App
to see each run, the result of each model and test, how long it took, and whether
the record was collected. The original files stay in restricted storage, and
dbtobsb does not send logs or results to an external monitoring service.

dbtobsb gives operators one place to answer three questions:

1. Did the Databricks task finish?
2. Did dbt produce usable artifacts?
3. Did dbtobsb capture and publish the evidence?

These are separate questions. A failed dbt build can still leave complete evidence,
and a successful dbt build can still have missing evidence.

[Start the tutorial](tutorials/see-your-first-run.md){ .md-button .md-button--primary }
[View the source on GitHub](https://github.com/MiguelElGallo/dbtobsb){ .md-button }

!!! warning "Azure Databricks only"

    dbtobsb `v0.3.0` does not run on AWS Databricks, GCP Databricks, or
    **Databricks Free Edition**. Databricks does not use “Personal Edition” as the
    product name; personal-use signup creates a Free Edition workspace. Install
    only in a supported Azure Databricks workspace. See
    [Supported environment](reference/supported-environment.md).

!!! info "Private release"

    Version `0.3.0` is a private release. It is not distributed through Databricks
    Marketplace. The source repository and this documentation are public; customer
    installation and runtime evidence remain private to the customer's workspace.

## Choose what you need

### Learn the product

Start with [See your first observed dbt run](tutorials/see-your-first-run.md).
It takes you through one prepared dbt Job and shows the expected output at each
step.

### Complete a task

Use a [how-to guide](how-to-guides/index.md) when you already know the result you
need, such as adding a project, querying evidence, recovering a missed collection,
or removing the product.

### Look up exact facts

Use the [reference](reference/index.md) for supported versions, commands, tables,
views, statuses, permissions, and limits.

### Understand the design

Read the [explanation](explanation/index.md) to understand how capture works, why
dbt and capture outcomes stay separate, and why the product keeps data in the
customer's Databricks workspace.

## What dbtobsb stores

For each observed dbt task, dbtobsb keeps:

- the Databricks task outcome;
- a small summary of the dbt invocation;
- one result row for each accepted dbt result node, including models, seeds,
  snapshots, and tests;
- the state of artifact retrieval and validation; and
- the state of the collection process.

Raw artifacts and logs are restricted evidence. The App and normal SQL views expose
only a reviewed set of fields; they do not expose compiled SQL, raw log messages,
environment values, or secrets.

## Supported release

The supported path uses Azure Databricks—not Free Edition—dbt Core `1.11.12`,
dbt-databricks `1.12.2`, Python `3.12`, and Databricks CLI `1.7.0`.
See [Supported environment](reference/supported-environment.md) before installing.
