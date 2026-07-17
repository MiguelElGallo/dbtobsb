"""Self-contained server-rendered read-only observability page."""

from __future__ import annotations

from datetime import datetime
from html import escape

from dbtobsb_app.models import (
    CollectionHealth,
    ErrorDetail,
    NodeHealth,
    RunHealth,
)


def _text(value: object | None) -> str:
    if value is None:
        return "—"
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _cell(value: object | None) -> str:
    if isinstance(value, datetime):
        rendered = escape(value.isoformat(), quote=True)
        return f'<td><time datetime="{rendered}">{rendered}</time></td>'
    return f"<td>{escape(_text(value), quote=True)}</td>"


def _row_header(value: object) -> str:
    return f'<th scope="row">{escape(_text(value), quote=True)}</th>'


def _yes_no_unknown(value: bool | None) -> str:
    if value is None:
        return "Unknown"
    return "Yes" if value else "No"


def _result_summary(run: RunHealth) -> str:
    actual = "not available" if run.result_count is None else str(run.result_count)
    return f"{actual} / {run.expected_node_count} expected"


def _document(content: str, *, title: str = "dbtobsb observability") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)}</title>
  <style>
    :root {{ color-scheme: light dark; --accent:#ff5f46; --panel:#18202b; --muted:#9aa8b8; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; font:15px/1.5 system-ui,sans-serif; background:#0d1117; color:#f4f7fa; }}
    main {{ width:min(1200px,calc(100% - 2rem)); margin:2rem auto 4rem; }}
    header {{ display:flex; justify-content:space-between; gap:1rem; align-items:end; }}
    h1,h2 {{ line-height:1.15; }} h1 {{ margin:.25rem 0; }} h2 {{ margin-top:2rem; }}
    .eyebrow {{ color:var(--accent); font-weight:700; letter-spacing:.08em;
      text-transform:uppercase; }}
    .muted {{ color:var(--muted); }}
    .panel {{ background:var(--panel); border-radius:12px; padding:1.25rem; }}
    .panel + .panel {{ margin-top:1rem; }}
    .table-wrap {{ overflow-x:auto; border-radius:12px; border:1px solid #344252; }}
    .table-wrap:focus-visible, a:focus-visible {{ outline:3px solid #ffd166; outline-offset:3px; }}
    table {{ border-collapse:collapse; width:100%; background:var(--panel); }}
    caption {{ padding:.75rem; text-align:left; color:var(--muted); }}
    th,td {{ padding:.65rem .75rem; border-bottom:1px solid #344252; text-align:left;
      white-space:nowrap; }}
    th {{ color:#cbd5df; font-size:.8rem; text-transform:uppercase; letter-spacing:.04em; }}
    tr:last-child td {{ border-bottom:0; }} a {{ color:#ff9d8d; }}
    .action {{ display:inline-block; margin-top:.75rem; padding:.65rem .9rem; border-radius:8px;
      background:var(--accent); color:#111; font-weight:700; text-decoration:none; }}
    .badge {{ display:inline-block; padding:.15rem .5rem; border-radius:999px;
      background:#243244; }}
    @media (prefers-color-scheme:light) {{
      :root {{ --panel:#fff; --muted:#52606d; }} body {{ background:#f4f6f8; color:#17212b; }}
      .table-wrap,th,td {{ border-color:#d6dde5; }} a {{ color:#a32d1c; }}
      .badge {{ background:#edf1f5; }}
    }}
  </style>
</head>
<body><main>{content}</main></body>
</html>"""


def _cost_notice() -> str:
    return """<section class="panel" aria-labelledby="compute-cost-heading">
  <h2 id="compute-cost-heading">Check compute and cost before loading data</h2>
  <p>The Databricks App is already running on <strong>App compute</strong>. Keeping the App
  running can accrue App-compute cost.</p>
  <p>Loading the observability page or either JSON data API sends read-only queries to the
  bound <strong>SQL warehouse</strong>. If that warehouse is stopped, the query can auto-start it
  and accrue separate SQL-warehouse cost.</p>
  <p><strong>dbtobsb neither changes nor currently knows</strong> the customer warehouse's
  auto-stop, size, or cost-center/tag settings. Before loading data, verify those settings on
  the warehouse in Databricks SQL Warehouses.</p>
  <p>Closing this page does not stop App compute or the SQL warehouse. Use the reviewed
  lifecycle runbook to stop them when they are no longer needed.</p>
</section>"""


def setup_page(required_bindings: tuple[str, ...], *, invalid: bool = False) -> str:
    """Explain the safe setup-only state without echoing resource values."""
    state = "Configuration needs attention" if invalid else "Finish App setup"
    names = required_bindings or (
        "DBTOBSB_WAREHOUSE_ID",
        "DBTOBSB_RUN_HEALTH_VIEW",
        "DBTOBSB_NODE_HEALTH_VIEW",
        "DBTOBSB_COLLECTION_HEALTH_VIEW",
    )
    items = "".join(f"<li><code>{escape(name)}</code></li>" for name in names)
    return _document(
        f"""<header><div><div class="eyebrow">Setup only</div><h1>{state}</h1></div></header>
<section class="panel" aria-labelledby="setup-heading">
  <h2 id="setup-heading">Connect customer-local resources</h2>
  <p>Bind one SQL warehouse with <strong>CAN USE</strong> and the three existing sanitized
  observability views with <strong>SELECT</strong>. The App does not create or modify data.</p>
  <p class="muted">Required installer-owned bindings:</p><ul>{items}</ul>
  <p>After the installer verifies and binds those resources, start the App again.</p>
</section>
{_cost_notice()}"""
    )


def landing_page() -> str:
    """Explain both compute products before the first warehouse query."""
    return _document(
        f"""<header><div><div class="eyebrow">Read only</div><h1>dbt observability</h1>
<div class="muted">Customer-local evidence in Databricks</div></div></header>
{_cost_notice()}
<section class="panel" aria-labelledby="load-heading">
  <h2 id="load-heading">Load recent evidence</h2>
  <p>This action reads the sanitized run, node, and collection health views. The JSON data APIs at
  <code>/api/v1/runs</code>, <code>/api/v1/nodes</code>, and <code>/api/v1/collection</code>
  have the same SQL-warehouse
  auto-start and cost behavior.</p>
  <a class="action" href="/observability">Load observability data</a>
</section>"""
    )


def collection_runbook_page() -> str:
    """Render the fixed, non-querying collection-recovery procedure."""
    return _document(
        """<header><div><div class="eyebrow">Operator runbook</div>
<h1>Reconcile missing dbt evidence</h1></div><nav><a href="/">Back to dbtobsb</a></nav></header>
<p class="muted">Condensed, non-querying triage for the fixed release workflow.</p>
<section class="panel" aria-labelledby="before-reconcile-heading">
  <h2 id="before-reconcile-heading">Before you run recovery</h2>
  <p>You must belong to the customer group installed as <code>job_manager_group_name</code>.
  The serverless Job has a fixed 15-minute timeout and incurs usage. Platform startup and billing
  records determine actual billable usage; the timeout is not a billed-duration ceiling.</p>
  <p>If another run is active, wait. If the schedule is not <strong>Paused</strong>, do not edit or
  run the Job; ask the Job manager to restore the reviewed deployment.</p>
</section>
<section class="panel" aria-labelledby="run-reconcile-heading">
  <h2 id="run-reconcile-heading">Run the fixed reconciliation</h2>
  <ol>
    <li>In Databricks Jobs &amp; Pipelines, open <code>dbtobsb-reconciler</code>.</li>
    <li>Confirm the schedule is <strong>Paused</strong> and no run is active.</li>
    <li>Select <strong>Run now</strong>. Add no parameters or overrides.</li>
    <li>Wait for a terminal result and inspect the one sanitized JSON event.</li>
    <li>Return to Collection health and match the Lakeflow Run ID to the
    <strong>Reconciliation run</strong> column.</li>
  </ol>
  <p>Success means the affected rows are <code>PUBLISHED</code> with issue <code>None</code>.
  Run the unchanged Job again for <code>DISCOVERED</code>, <code>RETRYABLE</code>, an expired
  20-minute <code>COLLECTING</code> lease, or <code>"backlog":true</code>. Stop after
  <code>TERMINAL_FAILURE</code>.</p>
</section>
<section class="panel" aria-labelledby="reconcile-escalation-heading">
  <h2 id="reconcile-escalation-heading">When to stop retrying</h2>
  <p><code>DBTOBSB_APP_QUERY_FAILED</code>: the data operator checks the dedicated App warehouse
  once and reloads once. If it persists, route the code to the
  <a href="/operators/how-to/reconcile-installation/">deployment/seal verifier</a>; do not repair
  App identity or bindings.</p>
  <p>Stop and preserve the static code when a row reaches <code>TERMINAL_FAILURE</code>, a
  parent/task bound is exceeded, or a binding, manifest, environment, command, target, source,
  or override code appears. <code>DBTOBSB_RECONCILIATION_BINDING_MISMATCH</code>,
  <code>DBTOBSB_RECONCILIATION_MANIFEST_MISMATCH</code>, and every deployment/configuration code
  belong to the <a href="/operators/how-to/reconcile-installation/">deployment/seal verifier</a>;
  collection lifecycle codes belong to the data operator.</p>
  <p>No code shown here authorizes entering a Job ID, path, SQL statement, selector, or
  destination value.</p>
</section>""",
        title="Reconcile missing dbt evidence · dbtobsb",
    )


def installation_runbook_page() -> str:
    """Render the safe, non-querying installation-recovery boundary."""
    return _document(
        """<header><div><div class="eyebrow">Installation triage</div>
<h1>Reconcile a dbtobsb installation</h1></div><nav><a href="/">Back to dbtobsb</a></nav></header>
<p class="muted">Condensed, non-querying triage. The signed installer owns the executable flow.</p>
<section class="panel" aria-labelledby="installation-stop-heading">
  <h2 id="installation-stop-heading">Keep runtime stopped</h2>
  <p>Do not repair App environment values, resource bindings, Job tasks, wheel paths, service
  principals, or Unity Catalog objects by hand. Keep the App stopped and do not run the observed,
  collector, or reconciler Jobs while the installed graph is unverified.</p>
</section>
<section class="panel" aria-labelledby="installation-recover-heading">
  <h2 id="installation-recover-heading">Route the code</h2>
  <ul>
    <li><code>DBTOBSB_CONFIGURATION_INVALID</code>, <code>DBTOBSB_APP_AUTH_INVALID</code>, and
    every <code>DBTOBSB_APP_*_VIEW_CONTRACT_MISMATCH</code>: deployment/seal verifier.</li>
    <li><code>DBTOBSB_RECONCILIATION_BINDING_MISMATCH</code>,
    <code>DBTOBSB_RECONCILIATION_MANIFEST_MISMATCH</code>, and
    <code>DBTOBSB_DEPLOYMENT_*</code>: deployment/seal verifier.</li>
    <li>Fixed data-envelope, Query History recovery, data verification, and exact temporary-grant
    revoke: UC operator in <code>SEPARATED_DUTIES</code>; the acknowledged single administrator in
    <code>COMBINED_ROLE</code>.</li>
  </ul>
  <h2 id="installation-recovery-steps-heading">Use the attended installer</h2>
  <ol>
    <li>Preserve only the static diagnostic code and a correlation value when the App emitted one.
    Do not copy raw
    exception text, SQL, logs, artifact paths, or Personal Data into a ticket.</li>
    <li>On the approved workstation, use the same signed dbtobsb release, immutable installation
    mode, actor-owned OAuth profile, customer-owned schema, dedicated installer warehouse, and
    named principals used for this installation.</li>
    <li>Run its canonical attended reconciliation entrypoint. The final launcher remains a release
    blocker; do not substitute the developer-only seal utility. Review the read-only inventory
    before any approval.</li>
    <li>In <code>SEPARATED_DUTIES</code>, the verifier hands fixed data recovery to the different UC
    operator and resumes only after supported return of control. In <code>COMBINED_ROLE</code>, the
    one actor acknowledges that the review is non-independent.</li>
    <li>Require terminal query history, exact object/seal readback, no temporary migration grant,
    a stopped App, and zero pending deployment before runtime is resumed.</li>
  </ol>
  <p>This page intentionally exposes no SQL, resource ID, path, profile, or free-form repair
  input. If the signed installer is unavailable, stop here and escalate to the deployment/seal
  verifier.</p>
</section>""",
        title="Reconcile a dbtobsb installation · dbtobsb",
    )


def _failure_panel(*, heading: str, failure: ErrorDetail) -> str:
    heading_ids = {
        "Recent runs": "recent-runs-failed-heading",
        "Recent nodes": "recent-nodes-failed-heading",
        "Collection health": "collection-health-failed-heading",
    }
    heading_id = heading_ids[heading]
    action_path = (
        "/operators/how-to/reconcile-collection/"
        if failure.responsible_actor == "data operator"
        else "/operators/how-to/reconcile-installation/"
    )
    return f"""<section class="panel" role="alert" aria-labelledby="{heading_id}">
  <h2 id="{heading_id}">{escape(heading)} unavailable</h2>
  <p>{escape(failure.message)}</p>
  <p><strong>Responsible actor:</strong> {escape(failure.responsible_actor)}.<br>
  <strong>Next action:</strong> <a href="{action_path}">{escape(failure.action)}</a></p>
  <p class="muted">Code: <code>{escape(failure.code)}</code> · Correlation:
  <code>{escape(failure.correlation_id)}</code></p>
</section>"""


def _status_help() -> str:
    return """<section class="panel" aria-labelledby="status-help-heading">
  <h2 id="status-help-heading">How to read this evidence</h2>
  <dl>
    <dt><strong>Lakeflow</strong></dt><dd>The Databricks task outcome.</dd>
    <dt><strong>Retrieval</strong></dt><dd>Whether dbt's closed output archive was available.</dd>
    <dt><strong>Capture</strong></dt>
    <dd>Whether both primary artifacts were complete and usable.</dd>
    <dt><strong>Issue</strong></dt>
    <dd>A static dbtobsb reason code. “None” means no capture issue.</dd>
    <dt><strong>Jobs logs truncated</strong></dt><dd>Yes, No, or Unknown from the Jobs API.</dd>
    <dt><strong>Build and deps logs</strong></dt><dd>VALID is healthy; MISSING, TRUNCATED,
    MALFORMED, UNKNOWN_VERSION, and invocation mismatch require evidence reconciliation.
    “Not run” means the optional deps command was not configured.</dd>
    <dt><strong>Artifact pair</strong></dt><dd>PAIR_VALID means manifest and run results agree.</dd>
    <dt><strong>Results</strong></dt>
    <dd>Accepted node results compared with the expected count.</dd>
    <dt><strong>Collection</strong></dt>
    <dd>DISCOVERED and COLLECTING are pending; RETRYABLE will be attempted again;
    TERMINAL_FAILURE requires operator reconciliation; PUBLISHED is visible in run health.</dd>
  </dl>
  <p>If collection is not healthy, the data operator follows the collection-reconciliation
  runbook. Installed binding or view-contract failures belong to the deployment/seal verifier.
  Operators do not enter Job IDs, paths, selectors, flags, or SQL.</p>
</section>"""


def dashboard_page(
    runs: tuple[RunHealth, ...],
    nodes: tuple[NodeHealth, ...],
    collection: tuple[CollectionHealth, ...],
    *,
    run_failure: ErrorDetail | None = None,
    node_failure: ErrorDetail | None = None,
    collection_failure: ErrorDetail | None = None,
) -> str:
    """Render only the public model allowlists with HTML escaping."""
    run_rows = "".join(
        "<tr>"
        + _row_header(run.observed_job_run_id)
        + _cell(run.observed_task_key)
        + _cell(run.task_start_time)
        + _cell(run.lakeflow_result_state)
        + _cell(run.retrieval_state)
        + _cell(run.capture_state)
        + _cell(run.issue_code or "None")
        + _cell(_yes_no_unknown(run.logs_truncated))
        + _cell(run.structured_log_state)
        + _cell(run.deps_structured_log_state if run.dbt_include_deps else "not run")
        + _cell(run.structured_log_expected_dbt_common_version)
        + _cell(run.pair_state or "Not available")
        + _cell(_result_summary(run))
        + _cell(run.elapsed_time)
        + "</tr>"
        for run in runs
    ) or (
        '<tr><td colspan="14">No collected runs yet. Run an onboarded dbt Job, '
        "verify its collector child succeeded, then refresh this page.</td></tr>"
    )
    node_rows = "".join(
        "<tr>"
        + _row_header(node.observed_job_run_id)
        + _cell(node.unique_id)
        + _cell(node.resource_type)
        + _cell(node.status)
        + _cell(node.execution_time)
        + _cell("Unknown" if node.failures is None else node.failures)
        + "</tr>"
        for node in nodes
    ) or (
        '<tr><td colspan="6">No accepted node results yet. Review the run capture state '
        "and issue code above.</td></tr>"
    )
    collection_rows = "".join(
        "<tr>"
        + _row_header(item.dbt_task_run_id)
        + _cell(item.collector_state)
        + _cell(item.collection_attempt_count)
        + _cell(item.collection_issue_code or "None")
        + _cell(item.first_discovered_at)
        + _cell(item.last_attempted_at)
        + _cell(item.published_at)
        + _cell(item.last_reconciliation_run_id)
        + "</tr>"
        for item in collection
    ) or (
        '<tr><td colspan="8">No collection records yet. This is not proof that the observed '
        "dbt Job has no runs; verify the fixed reconciler is installed and follow the collection "
        "runbook if a completed dbt attempt is missing.</td></tr>"
    )
    run_panel = (
        _failure_panel(heading="Recent runs", failure=run_failure)
        if run_failure is not None
        else f"""<h2 id="recent-runs-heading">Recent runs
<span class="badge">{len(runs)}</span></h2>
<div class="table-wrap" role="region" tabindex="0" aria-labelledby="recent-runs-heading"
  aria-describedby="recent-runs-caption"><table>
<caption id="recent-runs-caption">Run outcomes, evidence health, and accepted versus expected
node-result counts. Use arrow keys or horizontal scrolling when the table is wider than the
window.</caption><thead><tr>
<th scope="col">Job run</th><th scope="col">Task</th><th scope="col">Started</th>
<th scope="col">Lakeflow</th><th scope="col">Retrieval</th><th scope="col">Capture</th>
<th scope="col">Issue</th><th scope="col">Jobs logs truncated</th>
<th scope="col">Build logs</th>
<th scope="col">Deps logs</th><th scope="col">Expected dbt-common</th>
<th scope="col">Artifact pair</th>
<th scope="col">Results</th><th scope="col">Seconds</th>
</tr></thead><tbody>{run_rows}</tbody></table></div>"""
    )
    node_panel = (
        _failure_panel(heading="Recent nodes", failure=node_failure)
        if node_failure is not None
        else f"""<h2 id="recent-nodes-heading">Recent nodes
<span class="badge">{len(nodes)}</span></h2>
<div class="table-wrap" role="region" tabindex="0" aria-labelledby="recent-nodes-heading"
  aria-describedby="recent-nodes-caption"><table>
<caption id="recent-nodes-caption">Native dbt node outcomes from accepted artifact pairs.</caption>
<thead><tr>
<th scope="col">Job run</th><th scope="col">Node</th><th scope="col">Type</th>
<th scope="col">Status</th><th scope="col">Seconds</th><th scope="col">Failures</th></tr></thead>
<tbody>{node_rows}</tbody></table></div>"""
    )
    collection_panel = (
        _failure_panel(heading="Collection health", failure=collection_failure)
        if collection_failure is not None
        else f"""<h2 id="collection-health-heading">Collection health
<span class="badge">{len(collection)}</span></h2>
<div class="table-wrap" role="region" tabindex="0" aria-labelledby="collection-health-heading"
  aria-describedby="collection-health-caption"><table>
<caption id="collection-health-caption">Bounded collection attempts and reconciliation backlog.
The schedule is paused or running only as configured in Databricks Jobs; this view does not infer
the current schedule state.</caption>
<thead><tr>
<th scope="col">Task run</th><th scope="col">Collection</th><th scope="col">Attempts</th>
<th scope="col">Issue</th><th scope="col">Discovered</th><th scope="col">Last attempted</th>
<th scope="col">Published</th><th scope="col">Reconciliation run</th>
</tr></thead><tbody>{collection_rows}</tbody></table></div>"""
    )
    return _document(
        f"""<header><div><div class="eyebrow">dbt Core · Databricks</div><h1>Observability</h1>
<div class="muted">Customer-local evidence · read only</div></div>
<nav aria-label="Observability"><a href="/">Cost notice</a> ·
<a href="/observability">Refresh data</a></nav></header>
{_cost_notice()}
{collection_panel}
{run_panel}
{node_panel}
{_status_help()}
<p class="muted">JSON: <a href="/api/v1/collection">collection</a> ·
<a href="/api/v1/runs">runs</a> · <a href="/api/v1/nodes">nodes</a> ·
<a href="/api/readiness">readiness</a></p>"""
    )
