#!/usr/bin/env bash

set -Eeuo pipefail

if [[ $- == *x* ]]; then
  printf '%s\n' 'Refusing to run with shell tracing enabled; it could expose an OAuth token.' >&2
  exit 2
fi

readonly REQUIRED_CLI_VERSION='Databricks CLI v1.9.0'
readonly APP_NAME='dbtobsb-smoke'
readonly APP_RESOURCE_KEY='dbtobsb_smoke'
readonly BUNDLE_TARGET='smoke'
readonly EXPECTED_COMPUTE_SIZE='MEDIUM'
readonly PROFILE="${DBTOBSB_DATABRICKS_PROFILE:?Set DBTOBSB_DATABRICKS_PROFILE to an OAuth U2M profile.}"
readonly EXPECTED_HOST="${DBTOBSB_EXPECTED_HOST:?Set DBTOBSB_EXPECTED_HOST to the exact workspace URL.}"
readonly EXPECTED_USER="${DBTOBSB_EXPECTED_USER:?Set DBTOBSB_EXPECTED_USER to the exact signed-in user.}"
readonly STOP_VERIFY_ATTEMPTS="${DBTOBSB_STOP_VERIFY_ATTEMPTS:-10}"

if [[ ! $STOP_VERIFY_ATTEMPTS =~ ^[1-9][0-9]*$ ]]; then
  printf '%s\n' 'DBTOBSB_STOP_VERIFY_ATTEMPTS must be a positive integer.' >&2
  exit 2
fi

if [[ -n ${DATABRICKS_TOKEN:-} || -n ${DATABRICKS_CLIENT_SECRET:-} ]]; then
  printf '%s\n' 'Refusing ambient token or client-secret authentication; use the named OAuth U2M profile.' >&2
  exit 2
fi
if [[ -n ${DATABRICKS_AUTH_STORAGE:-} && $DATABRICKS_AUTH_STORAGE != 'secure' ]]; then
  printf '%s\n' 'Refusing non-secure Databricks authentication storage.' >&2
  exit 2
fi
export DATABRICKS_AUTH_STORAGE='secure'

unset DATABRICKS_HOST DATABRICKS_AUTH_TYPE DATABRICKS_CONFIG_PROFILE

may_need_stop=0
access_token=''

app_json() {
  databricks apps get "$APP_NAME" -t "$BUNDLE_TARGET" -p "$PROFILE" -o json
}

print_manual_recovery() {
  printf 'Manual stop: databricks apps stop %q -t %q -p %q --timeout 20m\n' \
    "$APP_NAME" "$BUNDLE_TARGET" "$PROFILE" >&2
  printf 'Verify state: databricks apps get %q -t %q -p %q -o json | jq -er %q\n' \
    "$APP_NAME" "$BUNDLE_TARGET" "$PROFILE" '.compute_status.state' >&2
}

cleanup() {
  local original_status=$?
  local cleanup_failed=0
  local observed_state='UNKNOWN'
  local state_json=''
  trap - EXIT INT TERM
  set +e
  unset access_token

  if (( may_need_stop )); then
    # Once deployment might have created or drifted the App, always attempt the
    # idempotent stop. A failed status read must never suppress the stop command.
    if ! databricks apps stop "$APP_NAME" -t "$BUNDLE_TARGET" -p "$PROFILE" --timeout 20m; then
      cleanup_failed=1
      printf '%s\n' 'STOP FAILED: Databricks App compute may still be billable.' >&2
    else
      for (( attempt = 1; attempt <= STOP_VERIFY_ATTEMPTS; attempt++ )); do
        if state_json="$(app_json 2>/dev/null)" && \
            observed_state="$(jq -er '.compute_status.state' <<<"$state_json" 2>/dev/null)"; then
          if [[ $observed_state == 'STOPPED' ]]; then
            break
          fi
        fi
        observed_state='UNKNOWN'
        if (( attempt < STOP_VERIFY_ATTEMPTS )); then
          sleep 2
        fi
      done
      unset state_json
      if [[ $observed_state == 'STOPPED' ]]; then
        printf '%s\n' 'STOP VERIFIED: App compute state is STOPPED.'
      else
        cleanup_failed=1
        printf '%s\n' 'STOP UNVERIFIED: final App compute state could not be confirmed; cost may continue.' >&2
      fi
    fi
    if (( cleanup_failed != 0 )); then
      print_manual_recovery
    fi
  fi

  if (( original_status == 0 && cleanup_failed != 0 )); then
    original_status=1
  fi
  exit "$original_status"
}

trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

for command_name in databricks jq curl; do
  command -v "$command_name" >/dev/null || {
    printf 'Missing required command: %s\n' "$command_name" >&2
    exit 2
  }
done

actual_cli_version="$(databricks --version)"
if [[ $actual_cli_version != "$REQUIRED_CLI_VERSION" ]]; then
  printf 'Expected %s, got %s.\n' "$REQUIRED_CLI_VERSION" "$actual_cli_version" >&2
  exit 2
fi

auth_json="$(databricks auth describe -p "$PROFILE" -o json)"
auth_type="$(jq -er '.details.auth_type' <<<"$auth_json")"
profile_host="$(jq -er '.details.host' <<<"$auth_json")"
profile_user="$(jq -er '.username' <<<"$auth_json")"
unset auth_json
if [[ $auth_type != 'databricks-cli' || $profile_host != "$EXPECTED_HOST" || \
    $profile_user != "$EXPECTED_USER" ]]; then
  printf '%s\n' 'The named profile is not OAuth U2M for the exact expected workspace host and user.' >&2
  exit 2
fi

apps_inventory="$(databricks apps list -p "$PROFILE" -o json)"
warehouses_inventory="$(databricks warehouses list -p "$PROFILE" -o json)"
clusters_inventory="$(databricks clusters list -p "$PROFILE" -o json)"
if ! jq -e --arg app "$APP_NAME" --arg size "$EXPECTED_COMPUTE_SIZE" '
    ([.[] | select(.name != $app)] | length == 0)
    and ([.[] | select(.name == $app)] | length <= 1)
    and all(.[] | select(.name == $app);
      .compute_status.state == "STOPPED"
      and .compute_size == $size
      and ((.resources // []) | length == 0))
  ' <<<"$apps_inventory" >/dev/null; then
  printf '%s\n' 'P0 requires no unrelated Apps and only an optional stopped, unbound MEDIUM dbtobsb-smoke App.' >&2
  exit 2
fi
if ! jq -e 'length == 0' <<<"$warehouses_inventory" >/dev/null || \
    ! jq -e 'length == 0' <<<"$clusters_inventory" >/dev/null; then
  printf '%s\n' 'P0 requires a dedicated smoke workspace with zero visible SQL warehouses and clusters.' >&2
  exit 2
fi
unset apps_inventory warehouses_inventory clusters_inventory
printf '%s\n' 'DEDICATED WORKSPACE VERIFIED: no unrelated App, warehouse, or cluster is visible.'

databricks bundle validate -t "$BUNDLE_TARGET" -p "$PROFILE" -o json >/dev/null

# The deployed declaration is stopped by default, but cleanup starts before deployment
# so a remote drift or partial response cannot silently leave compute active.
may_need_stop=1
databricks bundle deploy -t "$BUNDLE_TARGET" -p "$PROFILE" \
  --select "apps.$APP_RESOURCE_KEY" --auto-approve
deployed_json="$(app_json)"
deployed_state="$(jq -er '.compute_status.state' <<<"$deployed_json")"
deployed_compute_size="$(jq -er '.compute_size' <<<"$deployed_json")"
if [[ $deployed_state != 'STOPPED' || $deployed_compute_size != "$EXPECTED_COMPUTE_SIZE" ]]; then
  printf 'Expected stopped %s deployment, observed state=%s size=%s.\n' \
    "$EXPECTED_COMPUTE_SIZE" "$deployed_state" "$deployed_compute_size" >&2
  exit 1
fi
if ! jq -e '(.resources // []) | length == 0' <<<"$deployed_json" >/dev/null; then
  printf '%s\n' 'The deployed P0 App has live resource bindings; refusing to start it.' >&2
  exit 1
fi
unset deployed_json

databricks bundle run "$APP_RESOURCE_KEY" -t "$BUNDLE_TARGET" -p "$PROFILE"
running_json="$(app_json)"
running_state="$(jq -er '.compute_status.state' <<<"$running_json")"
running_compute_size="$(jq -er '.compute_size' <<<"$running_json")"
app_url="$(jq -er '.url' <<<"$running_json")"
if [[ $running_state != 'ACTIVE' || $running_compute_size != "$EXPECTED_COMPUTE_SIZE" || \
    $app_url != https://*.databricksapps.com ]]; then
  printf 'App did not reach expected ACTIVE/%s state and URL (state=%s size=%s).\n' \
    "$EXPECTED_COMPUTE_SIZE" "$running_state" "$running_compute_size" >&2
  exit 1
fi
if ! jq -e '(.resources // []) | length == 0' <<<"$running_json" >/dev/null; then
  printf '%s\n' 'The running P0 App has live resource bindings; stopping immediately.' >&2
  exit 1
fi
unset running_json

access_token="$(databricks auth token "$PROFILE" -o json | jq -er '.access_token')"
health_response="$({
  printf 'url = "%s/api/health"\n' "$app_url"
  printf 'header = "Authorization: Bearer %s"\n' "$access_token"
  printf '%s\n' 'fail-with-body' 'silent' 'show-error'
} | curl --disable --proto '=https' --tlsv1.2 --config -)"
unset access_token

jq -e '
  . == {
    "status": "alive",
    "check": "process_liveness",
    "readiness": "not_evaluated",
    "phase": "p0_smoke",
    "service": "dbtobsb",
    "version": "0.1.0"
  }
' <<<"$health_response" >/dev/null

health_log_found=0
for _ in 1 2 3 4 5 6 7 8 9 10; do
  if databricks apps logs "$APP_NAME" -t "$BUNDLE_TARGET" -p "$PROFILE" \
      --source APP --search health_check --tail-lines 200 2>/dev/null \
      | grep -Fq '"event":"health_check"'; then
    health_log_found=1
    break
  fi
  sleep 2
done
if (( health_log_found == 0 )); then
  printf '%s\n' 'The health response succeeded, but its required stdout event was not observable.' >&2
  exit 1
fi

printf '%s\n' "$health_response"
printf '%s\n' 'Smoke verified; stopping App compute now.'
