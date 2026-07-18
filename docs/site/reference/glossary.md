# Glossary

## Artifact pair

The `manifest.json` and `run_results.json` files presented as one dbt invocation.
A valid pair has matching parseable invocation IDs and satisfies the pinned
contract. That check does not prove origin, unchanged custody, or absence of later
modification.

## Bundle

A reviewed set of files that describes the Databricks resources to deploy. This
release uses a Databricks Asset Bundle and applies it through the installer.

## Capture

The process of acquiring, preserving, validating, and normalizing dbt evidence.

## Collector

The separate Job that reads staged evidence, preserves an exact archive, validates
the files, and writes normalized rows.

## Databricks App

The read-only web interface included with dbtobsb. Its serverless compute is
separate from dbt Job compute and the SQL warehouse used to read evidence.

## Databricks Free Edition

The current official name for Databricks' no-cost personal-use offering. It
replaced Community Edition in 2025. It is not the customer-subscription Azure
workspace offering qualified by dbtobsb. Databricks does not document a separate
current product called “Personal Edition.”

## Evidence schema

The existing customer-owned Unity Catalog schema chosen for dbtobsb objects.

## Normalized evidence

Small, consistent rows derived from validated dbt artifacts. They make runs and
node results queryable without exposing every field from the raw files.

## Health view

One of the three curated SQL views intended for normal readers and the App.

## Observed Job

The installed Lakeflow Job that runs the sealed dbt project and stages approved
artifacts and logs.

## Pair state

Whether a dbt manifest and run-results file satisfy the supported schemas and
belong to one invocation.

## Raw archive

The exact bounded archive stored in `dbtobsb_raw` before parsing. It is restricted
because it can contain sensitive operational data.

## Sealed project

The reviewed copy of a dbt project used by the observed Job. dbtobsb records its
file hashes, selector, target, command, and dependency versions so an unreviewed
change is rejected.

## Serverless compute

Databricks-managed compute that starts for a Job or App without a customer-managed
cluster. It can still incur usage while active.

## Service principal

A non-human Databricks identity used to run a Job with fixed permissions. dbtobsb
uses separate service principals for the observed Job and collection Jobs.

## Reconciler

The paused-by-default Job that discovers supported attempts with missing evidence
and retries collection within fixed limits.

## Retrieval state

Whether the collector obtained the fixed staged files and built an archive.

## Trusted root

A person or identity with enough authority to change code, Jobs, permissions, or
evidence. The product records this boundary instead of claiming those actors are
technically unable to alter evidence.

## Unity Catalog Volume

A governed file-storage location inside Unity Catalog. dbtobsb uses restricted
Volumes for staged files and exact raw archives.
