# P0 smoke private run-record template

This is a copy-only template. Never fill it with a real identity, workspace host, account/workspace/App ID, or internal approval-system URL in this repository. Copy it into the organization's policy-approved private record system; that system owns access, retention, approver identity, and audit policy.

This record is an attended procedural gate; the wrapper cannot read the external private system. The operator and approver must not authorize the wrapper while a required field is blank or `approval_state` is not `APPROVED`.

## Blank record

```yaml
record_version: 1
approval_state: PENDING # required: APPROVED
approval_reference: "" # private-system reference; never copy it back here
approved_at_utc: ""
approver_role: ""
cleanup_owner_role: ""
cleanup_owner_reference: "" # private accountable-person reference; never copy it back here
workspace_alias: "" # nonsecret internal alias, not a host or workspace ID
inventory_visibility_confirmed_complete: false
starting_inventory:
  unrelated_apps: null # required: 0
  sql_warehouses: null # required: 0
  clusters: null # required: 0
app_compute_size: MEDIUM
published_dbu_per_hour: 0.5
source_refreshed_at_utc: ""
wrapper_start_at_utc: ""
cancellation_deadline_at_utc: "" # start + 10 minutes
planned_dbu_through_cancellation: 0.084
successful_stop_timeout_minutes: 20
successful_stop_exposure_dbu: 0.25
hard_cost_ceiling: NONE
hard_ceiling_risk_accepted: false # required: true, or do not run
schedule_state: NONE
cleanup_result: NOT_RUN # required after run: STOPPED_VERIFIED or FAILED_ESCALATED
final_readback_retained: false
evidence_reference: "" # private-system reference
notes: ""
```

## Synthetic approved example

This example is fictional and contains no deployable credential or live identifier.

```yaml
record_version: 1
approval_state: APPROVED
approval_reference: "change-record-example-001"
approved_at_utc: "2030-01-02T09:50:00Z"
approver_role: "personal-workspace owner"
cleanup_owner_role: "smoke operator"
cleanup_owner_reference: "operator-example-a"
workspace_alias: "dedicated-smoke-example"
inventory_visibility_confirmed_complete: true
starting_inventory:
  unrelated_apps: 0
  sql_warehouses: 0
  clusters: 0
app_compute_size: MEDIUM
published_dbu_per_hour: 0.5
source_refreshed_at_utc: "2030-01-02T09:45:00Z"
wrapper_start_at_utc: "2030-01-02T10:00:00Z"
cancellation_deadline_at_utc: "2030-01-02T10:10:00Z"
planned_dbu_through_cancellation: 0.084
successful_stop_timeout_minutes: 20
successful_stop_exposure_dbu: 0.25
hard_cost_ceiling: NONE
hard_ceiling_risk_accepted: true
schedule_state: NONE
cleanup_result: STOPPED_VERIFIED
final_readback_retained: true
evidence_reference: "evidence-record-example-001"
notes: "Technical smoke only; no dbt execution or product readiness claim."
```

## Rejected example

This record cannot authorize a run because the cleanup owner, visibility proof, timestamps, risk acceptance, and approval are incomplete.

```yaml
approval_state: PENDING
cleanup_owner_role: ""
cleanup_owner_reference: ""
inventory_visibility_confirmed_complete: false
wrapper_start_at_utc: ""
cancellation_deadline_at_utc: ""
hard_ceiling_risk_accepted: false
cleanup_result: NOT_RUN
```
