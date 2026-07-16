# Stop compute and remove the preview

Use this guide after a test or when you no longer need the private engineering preview.

The Bundle creates unscheduled Jobs and a stopped App resource. Those objects do not schedule work by themselves. A SQL warehouse used by the dbt task, an active Job run, a cluster, or a running App can incur compute cost.

## 1. Prove no Job run is active

```bash
databricks jobs list-runs -p '<profile>' --active-only -o json
```

The result must be an empty JSON list for the Jobs you own. In a shared workspace, filter by the three deployed Job IDs and never cancel an unrelated run.

If a dbtobsb run is active, cancel that run and wait until it reaches a terminal state before continuing:

```bash
databricks jobs cancel-run '<run-id>' -p '<profile>'
```

## 2. Stop the preview App

The P2 path does not need App compute. Check only the named preview App first:

```bash
databricks apps get dbtobsb-smoke -p '<profile>' -o json
```

If it is `ACTIVE`, starting, or otherwise not terminally stopped, request a stop and read it back:

```bash
databricks apps stop dbtobsb-smoke -p '<profile>'
databricks apps get dbtobsb-smoke -p '<profile>' -o json
```

If it is already `STOPPED`, do not issue an unnecessary stop; retain that readback. Otherwise wait for `compute_status.state` to become `STOPPED`. A stop request is not proof of a stopped App.

## 3. Remove only disposable compute you created

List warehouses and clusters:

```bash
databricks warehouses list -p '<profile>' -o json
databricks clusters list -p '<profile>' -o json
```

Delete a SQL warehouse only if it was created solely for this test and you have verified its ID and ownership:

```bash
databricks warehouses delete '<test-warehouse-id>' -p '<profile>'
```

Do not delete a customer's shared warehouse or cluster. Serverless Job compute ends with its run and has no persistent cluster for this Bundle to delete.

## 4. Remove the deployed Jobs and App shell

Destroy the Bundle target after active runs are terminal:

```bash
databricks bundle destroy -t smoke -p '<profile>' \
  --var 'warehouse_id=<warehouse-id>,evidence_catalog=<catalog>,evidence_schema=<evidence-schema>,demo_schema=<demo-schema>,raw_volume_name=dbtobsb_raw'
```

Review the displayed resources before confirming. This removes Bundle-managed resources. It does not delete the Unity Catalog evidence schema, tables, views, managed Volume, or the raw archives inside it.

## 5. Choose retain or delete for evidence

Retain evidence when audit, incident, legal-hold, or customer retention policy requires it. Revoke runtime write access and preserve the dedicated schema under customer ownership.

Delete evidence only when all of these are true:

- the schema is dedicated to dbtobsb;
- an authorized owner approved deletion;
- retention and legal-hold checks are complete;
- required exports are complete and verified; and
- the operator understands that deleting the managed Volume deletes the archived bytes.

The P2 preview deliberately does not automate this destructive decision. An authorized Unity Catalog owner may use a reviewed, fixed SQL statement such as:

```sql
DROP SCHEMA `<catalog>`.`<evidence-schema>` CASCADE;
```

Never drop a shared catalog. If the tutorial used a disposable catalog created solely for this proof, catalog deletion remains a separate customer-owner action after the schema inventory is confirmed empty.

## 6. Retain a sanitized final readback

Record only non-sensitive results:

- no active dbtobsb Job runs;
- test warehouse deleted or shared warehouse left unchanged;
- no preview cluster;
- App `STOPPED` or Bundle App removed; and
- evidence retained or deleted under an explicit decision.

Do not retain workspace IDs, user identities, signed artifact links, raw Volume paths, or raw dbt content in the ordinary release record.
