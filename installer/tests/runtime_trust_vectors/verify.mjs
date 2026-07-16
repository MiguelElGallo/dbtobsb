import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const MAX_BIGINT = 9223372036854775807n;
const DEFAULT_VECTOR_PATH = resolve(
  dirname(fileURLToPath(import.meta.url)),
  "vectors-v1.json",
);
const DOMAIN_ORDER = [
  "dbtobsb.runtime-trust.deployment-set.v1",
  "dbtobsb.runtime-trust.component-observation.v1",
  "dbtobsb.runtime-trust.roster-observation.v1",
  "dbtobsb.runtime-trust.stable-graph.v1",
  "dbtobsb.runtime-trust.machine-observation.v1",
  "dbtobsb.runtime-trust.event-id.v1",
  "dbtobsb.runtime-trust.candidate-digest.v1",
  "dbtobsb.runtime-trust.acceptance-digest.v1",
  "dbtobsb.runtime-trust.payload-digest.v1",
  "dbtobsb.runtime-trust.snapshot-id.v1",
  "dbtobsb.runtime-trust.server-record.v1",
  "dbtobsb.runtime-trust.ledger-row-id.v1",
];
const SCHEMAS = new Map([
  [DOMAIN_ORDER[0], "account_digest app_digest deployments workspace_digest".split(" ")],
  [
    DOMAIN_ORDER[1],
    "authority_digest binding_digest component_key contract_digest dml_allowlist_digest runtime_principal_digest runtime_resource_digest".split(
      " ",
    ),
  ],
  [
    DOMAIN_ORDER[2],
    "account_digest expected_component_count expected_components expected_roster_digest observed_components observed_roster_digest roster_reviewer_fingerprint service_principal_set_digest workspace_digest".split(
      " ",
    ),
  ],
  [
    DOMAIN_ORDER[3],
    "account_digest acl_digest app_digest app_resource_digest artifact_digest build_digest configuration_digest deployment_id deployment_mode deployment_set_after_digest direct_lineage_digest direct_plan_digest direct_state_serial expected_component_count expected_components expected_roster_digest group_root_digest installation_digest job_run_as_digest manifest_digest observed_components observed_roster_digest resource_selection_digest service_principal_set_digest source_digest uc_grant_digest workspace_digest".split(
      " ",
    ),
  ],
  [
    DOMAIN_ORDER[4],
    "account_digest active_deployment_id deployment_id deployment_mode deployment_set_after_digest installation_digest lifecycle_state machine_observer_fingerprint manifest_digest pending_deployment_count phase stable_graph_digest workspace_digest".split(
      " ",
    ),
  ],
  [
    DOMAIN_ORDER[5],
    "contract_version generation installation_digest operation predecessor_event_id".split(" "),
  ],
  [
    DOMAIN_ORDER[6],
    "account_digest deployment_id deployment_mode deployment_set_after_digest deployment_set_before_digest event_id expected_component_count expected_components installation_digest machine_observer_fingerprint manifest_digest new_deployment_count observed_components pre_start_machine_observation_digest predecessor_event_id roster_anchor_digest roster_anchor_event_id roster_observation_digest roster_reviewer_fingerprint stable_graph_digest workspace_digest".split(
      " ",
    ),
  ],
  [
    DOMAIN_ORDER[7],
    "account_digest candidate_digest candidate_event_id candidate_statement_evaluated_at deployment_id deployment_mode deployment_set_after_digest deployment_set_before_digest event_id expected_component_count expected_components installation_digest machine_observer_fingerprint manifest_digest new_deployment_count observed_components post_start_machine_observation_digest pre_start_machine_observation_digest roster_anchor_digest roster_anchor_event_id roster_reviewer_fingerprint roster_statement_evaluated_at stable_graph_digest workspace_digest".split(
      " ",
    ),
  ],
  [
    DOMAIN_ORDER[8],
    "acceptance_digest account_digest acl_digest app_digest app_resource_digest artifact_digest build_digest candidate_digest candidate_event_id configuration_digest contract_version deployment_id deployment_mode deployment_set_after_digest deployment_set_before_digest direct_lineage_digest direct_plan_digest direct_state_serial event_id expected_component_count expected_components expected_roster_digest generation group_root_digest installation_digest job_run_as_digest machine_observer_fingerprint manifest_digest new_deployment_count observed_components observed_roster_digest operation post_start_active_deployment_id post_start_lifecycle_state post_start_machine_observation_digest post_start_pending_deployment_count pre_start_active_deployment_id pre_start_lifecycle_state pre_start_machine_observation_digest pre_start_pending_deployment_count predecessor_event_id prior_generation prior_snapshot_id reason resource_selection_digest roster_anchor_digest roster_anchor_event_id roster_observation_digest roster_reviewer_fingerprint service_principal_set_digest source_digest stable_graph_digest state target_event_id target_snapshot_id uc_grant_digest workspace_digest".split(
      " ",
    ),
  ],
  [
    DOMAIN_ORDER[9],
    "acceptance_digest acceptance_statement_evaluated_at candidate_digest candidate_event_id candidate_statement_evaluated_at deployment_id deployment_mode deployment_set_after_digest deployment_set_before_digest event_id expected_component_count expected_components generation installation_digest new_deployment_count observed_components payload_digest post_start_machine_observation_digest pre_start_machine_observation_digest roster_anchor_digest roster_anchor_event_id roster_statement_evaluated_at stable_graph_digest valid_until".split(
      " ",
    ),
  ],
  [
    DOMAIN_ORDER[10],
    "event_id payload_digest snapshot_id statement_evaluated_at valid_until".split(" "),
  ],
  [DOMAIN_ORDER[11], "event_id server_record_digest".split(" ")],
]);
const PAYLOAD_REQUIRED_COMMON = new Set(
  "event_id installation_digest workspace_digest account_digest generation operation state reason contract_version manifest_digest expected_component_count expected_components".split(
    " ",
  ),
);

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

function exactObject(value, fields, label) {
  assert(
    value !== null &&
      typeof value === "object" &&
      !Array.isArray(value) &&
      Object.getPrototypeOf(value) === Object.prototype,
    `${label}: expected object`,
  );
  assert(
    JSON.stringify(Object.keys(value).sort()) === JSON.stringify([...fields].sort()),
    `${label}: field set differs`,
  );
}

function oneOf(value, allowed, label) {
  assert(typeof value === "string" && allowed.includes(value), `${label}: enum invalid`);
}

function digest(value, label) {
  assert(typeof value === "string" && /^[0-9a-f]{64}$/.test(value), `${label}: digest invalid`);
}

function nullableDigest(value, label) {
  if (value !== null) digest(value, label);
}

function deploymentId(value, label) {
  assert(
    typeof value === "string" && /^[0-9a-f]{32}$/.test(value),
    `${label}: deployment ID invalid`,
  );
}

function parseCanonicalDecimal(value, label = "decimal") {
  assert(typeof value === "string", `${label}: decimal must be a string`);
  assert(/^(0|[1-9][0-9]*)$/.test(value), `${label}: decimal is not canonical`);
  const parsed = BigInt(value);
  assert(parsed <= MAX_BIGINT, `${label}: decimal exceeds BIGINT`);
  return parsed;
}

function parseCanonicalTimestamp(value, label = "timestamp") {
  assert(typeof value === "string", `${label}: timestamp must be a string`);
  const match = value.match(
    /^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):([0-9]{2})\.([0-9]{6})Z$/,
  );
  assert(match !== null, `${label}: timestamp shape invalid`);
  const fields = match.slice(1, 7).map(Number);
  const [year, month, day, hour, minute, second] = fields;
  const parsed = new Date(0);
  parsed.setUTCFullYear(year, month - 1, day);
  parsed.setUTCHours(hour, minute, second, 0);
  assert(
    parsed.getUTCFullYear() === year &&
      parsed.getUTCMonth() === month - 1 &&
      parsed.getUTCDate() === day &&
      parsed.getUTCHours() === hour &&
      parsed.getUTCMinutes() === minute &&
      parsed.getUTCSeconds() === second,
    `${label}: timestamp calendar value invalid`,
  );
  return value;
}

function expectedComponent(value, label) {
  exactObject(value, ["component_key", "contract_digest"], label);
  oneOf(
    value.component_key,
    ["BASE_OBSERVABILITY", "SYSTEM_ENRICHMENT", "CONTROLLED_ACTIONS"],
    `${label}.component_key`,
  );
  digest(value.contract_digest, `${label}.contract_digest`);
}

function observedComponent(value, label) {
  exactObject(value, ["component_key", "contract_digest", "observation_digest"], label);
  expectedComponent(
    { component_key: value.component_key, contract_digest: value.contract_digest },
    label,
  );
  digest(value.observation_digest, `${label}.observation_digest`);
}

function componentArrays(data, label) {
  assert(Array.isArray(data.expected_components), `${label}: expected components invalid`);
  const count = Number(parseCanonicalDecimal(data.expected_component_count, label));
  assert(count >= 1 && count <= 3, `${label}: component count out of range`);
  const expectedKeys = data.expected_components.map((value) => value.component_key);
  assert(data.expected_components.length === count, `${label}: expected component count differs`);
  assert(
    JSON.stringify(expectedKeys) === JSON.stringify([...new Set(expectedKeys)].sort()),
    `${label}: expected component keys must be sorted and unique`,
  );
  data.expected_components.forEach((value, index) =>
    expectedComponent(value, `${label}.expected_components[${index}]`),
  );
  if (data.observed_components === null) {
    assert(
      data.operation === "MANIFEST_REGISTERED" || data.operation === "SNAPSHOT_INVALIDATED",
      `${label}: observed components may be null only without observations`,
    );
    return;
  }
  assert(Array.isArray(data.observed_components), `${label}: observed components invalid`);
  assert(data.observed_components.length === count, `${label}: observed component count differs`);
  const observedKeys = data.observed_components.map((value) => value.component_key);
  assert(
    JSON.stringify(observedKeys) === JSON.stringify([...new Set(observedKeys)].sort()),
    `${label}: observed component keys must be sorted and unique`,
  );
  data.observed_components.forEach((value, index) => {
    observedComponent(value, `${label}.observed_components[${index}]`);
    assert(
      value.component_key === data.expected_components[index].component_key &&
        value.contract_digest === data.expected_components[index].contract_digest,
      `${label}: observed component does not bind expected component`,
    );
  });
}

function deploymentRecord(value, label) {
  exactObject(
    value,
    [
      "deployment_id",
      "status",
      "mode",
      "source_digest",
      "artifact_digest",
      "configuration_digest",
    ],
    label,
  );
  deploymentId(value.deployment_id, `${label}.deployment_id`);
  oneOf(value.status, ["SUCCEEDED", "FAILED", "CANCELLED", "IN_PROGRESS"], label);
  oneOf(value.mode, ["SNAPSHOT", "AUTO_SYNC"], label);
  nullableDigest(value.source_digest, `${label}.source_digest`);
  nullableDigest(value.artifact_digest, `${label}.artifact_digest`);
  nullableDigest(value.configuration_digest, `${label}.configuration_digest`);
}

function validateField(name, value, label) {
  if (["prior_generation"].includes(name)) {
    if (value !== null) parseCanonicalDecimal(value, label);
  } else if (["prior_snapshot_id", "target_event_id", "target_snapshot_id"].includes(name)) {
    nullableDigest(value, label);
  } else if (name.endsWith("_digest") || name.endsWith("_fingerprint")) {
    digest(value, label);
  } else if (name === "snapshot_id") {
    digest(value, label);
  } else if (name.endsWith("event_id")) {
    digest(value, label);
  } else if (name === "deployment_id" || name.endsWith("active_deployment_id")) {
    deploymentId(value, label);
  } else if (
    name.endsWith("_count") ||
    name === "generation" ||
    name === "direct_state_serial"
  ) {
    parseCanonicalDecimal(value, label);
  } else if (name.endsWith("_at") || name === "valid_until") {
    parseCanonicalTimestamp(value, label);
  } else if (name === "component_key") {
    oneOf(value, ["BASE_OBSERVABILITY", "SYSTEM_ENRICHMENT", "CONTROLLED_ACTIONS"], label);
  } else if (name === "deployment_mode" || name === "mode") {
    oneOf(value, ["SNAPSHOT", "AUTO_SYNC"], label);
  } else if (name === "operation" || name === "state") {
    oneOf(
      value,
      ["MANIFEST_REGISTERED", "TRUST_CANDIDATE", "SNAPSHOT_ACCEPTED", "SNAPSHOT_INVALIDATED"],
      label,
    );
  } else if (name === "phase") {
    oneOf(value, ["PRE_START", "POST_START"], label);
  } else if (name.endsWith("lifecycle_state")) {
    oneOf(value, ["STOPPED", "ACTIVE"], label);
  } else if (name === "reason") {
    oneOf(
      value,
      [
        "INSTALL",
        "UPGRADE",
        "ROLLBACK",
        "CHANGED_REFRESH",
        "UNCHANGED_REFRESH",
        "PRE_START_OBSERVED",
        "POST_START_MATCHED",
        "DEPLOYMENT_RECONCILIATION_FAILED",
        "FINAL_PLAN_DRIFT",
        "PRE_START_MISMATCH",
        "ROSTER_REVIEW_FAILED",
        "START_MISMATCH",
        "POST_START_MISMATCH",
        "TRUST_WRITE_INDETERMINATE",
        "OPERATOR_ABORTED",
      ],
      label,
    );
  } else if (name === "contract_version") {
    assert(value === "dbtobsb.runtime-trust.v1", `${label}: contract version invalid`);
  } else if (name === "expected_components" || name === "observed_components") {
    return;
  } else {
    throw new Error(`${label}: unvalidated schema field`);
  }
}

function validateDomain(domain, data) {
  const fields = SCHEMAS.get(domain);
  assert(fields !== undefined, `${domain}: unknown domain`);
  exactObject(data, fields, domain);
  if (domain === DOMAIN_ORDER[0]) {
    assert(Array.isArray(data.deployments), `${domain}: deployments invalid`);
    data.deployments.forEach((value, index) =>
      deploymentRecord(value, `${domain}.deployments[${index}]`),
    );
    const deploymentIds = data.deployments.map((value) => value.deployment_id);
    assert(
      JSON.stringify(deploymentIds) === JSON.stringify([...new Set(deploymentIds)].sort()),
      `${domain}: deployment IDs must be sorted and unique`,
    );
  }
  for (const [name, value] of Object.entries(data)) {
    if (name === "deployments") continue;
    if (value === null && domain === DOMAIN_ORDER[8]) {
      assert(!PAYLOAD_REQUIRED_COMMON.has(name), `${domain}.${name}: required value is null`);
      continue;
    }
    validateField(name, value, `${domain}.${name}`);
  }
  if (fields.includes("expected_components")) componentArrays(data, domain);
  if (domain === DOMAIN_ORDER[2]) {
    assert(
      data.expected_roster_digest === data.observed_roster_digest,
      `${domain}: roster digests differ`,
    );
  }
  if (domain === DOMAIN_ORDER[3]) {
    assert(data.direct_state_serial === MAX_BIGINT.toString(), `${domain}: max BIGINT case missing`);
  }
  if (domain === DOMAIN_ORDER[4]) {
    assert(
      (data.phase === "PRE_START" && data.lifecycle_state === "STOPPED") ||
        (data.phase === "POST_START" && data.lifecycle_state === "ACTIVE"),
      `${domain}: phase and lifecycle differ`,
    );
  }
  if (domain === DOMAIN_ORDER[9]) {
    assert(
      data.roster_statement_evaluated_at <= data.candidate_statement_evaluated_at &&
        data.candidate_statement_evaluated_at <= data.acceptance_statement_evaluated_at &&
        data.acceptance_statement_evaluated_at < data.valid_until,
      `${domain}: timestamp chronology invalid`,
    );
  }
}

function validateCanonicalValue(value) {
  if (value === null) return;
  if (typeof value === "string") {
    for (const character of value) {
      assert(character.codePointAt(0) <= 0x7f, "canonical string must be ASCII");
    }
    return;
  }
  if (Array.isArray(value)) {
    value.forEach(validateCanonicalValue);
    return;
  }
  if (typeof value === "object" && Object.getPrototypeOf(value) === Object.prototype) {
    Object.entries(value).forEach(([key, item]) => {
      validateCanonicalValue(key);
      validateCanonicalValue(item);
    });
    return;
  }
  throw new Error("canonical type is outside the v1 restricted universe");
}

function canonicalJson(value) {
  validateCanonicalValue(value);
  if (value === null || typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
  return `{${Object.keys(value)
    .sort()
    .map((key) => `${JSON.stringify(key)}:${canonicalJson(value[key])}`)
    .join(",")}}`;
}

function canonicalObject(domain, data) {
  validateDomain(domain, data);
  return canonicalJson({ data, domain });
}

function sha256(value) {
  return createHash("sha256").update(value, "ascii").digest("hex");
}

const vectorPath = process.argv[2] ? resolve(process.argv[2]) : DEFAULT_VECTOR_PATH;
const vectors = JSON.parse(readFileSync(vectorPath, "utf8"));
exactObject(
  vectors,
  [
    "contract_version",
    "domain_count",
    "domains",
    "decimal_valid",
    "decimal_invalid",
    "canonical_invalid",
    "timestamp_valid",
    "timestamp_invalid",
    "semantic_invalid",
    "event_conflicts",
    "version_separation",
    "sql",
  ],
  "contract",
);
assert(
  vectors.contract_version === "dbtobsb.runtime-trust.semantic-golden-v1",
  "unknown vector contract",
);
assert(vectors.domain_count === 12, "domain count must be 12");
assert(vectors.domains.length === 12, "exactly 12 domain vectors required");
assert(
  JSON.stringify(vectors.domains.map((vector) => vector.domain)) === JSON.stringify(DOMAIN_ORDER),
  "domain literal coverage or order differs",
);
for (const vector of vectors.domains) {
  const canonical = canonicalObject(vector.domain, vector.data);
  assert(canonical === vector.canonical, `${vector.name}: canonical bytes differ`);
  assert(sha256(canonical) === vector.sha256, `${vector.name}: digest differs`);
}
const byDomain = new Map(vectors.domains.map((vector) => [vector.domain, vector.data]));
assert(
  byDomain.get(DOMAIN_ORDER[8]).prior_generation === null &&
    byDomain.get(DOMAIN_ORDER[8]).prior_snapshot_id === null &&
    byDomain.get(DOMAIN_ORDER[8]).target_event_id === null &&
    byDomain.get(DOMAIN_ORDER[8]).target_snapshot_id === null,
  "payload domain must preserve meaningful nulls",
);
assert(
  Array.isArray(byDomain.get(DOMAIN_ORDER[3]).expected_components) &&
    Array.isArray(byDomain.get(DOMAIN_ORDER[3]).observed_components),
  "stable graph domain must preserve component arrays",
);
assert(
  byDomain.get(DOMAIN_ORDER[10]).statement_evaluated_at ===
    "2026-07-16T10:05:00.654321Z",
  "server record must preserve exact UTC microseconds",
);
const expectedDecimals = [
  "0",
  "1",
  "2147483647",
  "9007199254740991",
  "9007199254740992",
  "9007199254740993",
  "9223372036854775807",
];
assert(
  JSON.stringify(vectors.decimal_valid) === JSON.stringify(expectedDecimals),
  "decimal acceptance boundaries differ",
);
vectors.decimal_valid.forEach((value) => parseCanonicalDecimal(value));

const expectedDecimalRejects = [
  "negative",
  "leading-zero",
  "plus-sign",
  "fractional",
  "exponent",
  "empty",
  "leading-whitespace",
  "trailing-whitespace",
  "unicode-digit",
  "json-number",
  "null-required",
  "overflow",
];
assert(
  JSON.stringify(vectors.decimal_invalid.map((vector) => vector.name)) ===
    JSON.stringify(expectedDecimalRejects),
  "decimal rejection matrix differs",
);
for (const vector of vectors.decimal_invalid) {
  let rejected = false;
  try {
    parseCanonicalDecimal(vector.value);
  } catch {
    rejected = true;
  }
  assert(rejected, `${vector.name}: malformed decimal was accepted`);
}

for (const vector of vectors.canonical_invalid) {
  let rejected = false;
  try {
    canonicalJson(vector.value);
  } catch {
    rejected = true;
  }
  assert(rejected, `${vector.name}: malformed canonical value was accepted`);
}

vectors.timestamp_valid.forEach((value) => parseCanonicalTimestamp(value));
for (const vector of vectors.timestamp_invalid) {
  let rejected = false;
  try {
    parseCanonicalTimestamp(vector.value);
  } catch {
    rejected = true;
  }
  assert(rejected, `${vector.name}: malformed timestamp was accepted`);
}

const expectedSemanticCategories = {
  array_order: 2,
  duplicate: 2,
  extra_field: 1,
  missing_field: 1,
  wrong_enum: 1,
  wrong_nested_field: 1,
};
const observedSemanticCategories = {};
for (const vector of vectors.semantic_invalid) {
  observedSemanticCategories[vector.category] =
    (observedSemanticCategories[vector.category] ?? 0) + 1;
  let rejected = false;
  try {
    validateDomain(vector.domain, vector.data);
  } catch {
    rejected = true;
  }
  assert(rejected, `${vector.name}: malformed semantic vector was accepted`);
}
assert(
  JSON.stringify(observedSemanticCategories, Object.keys(observedSemanticCategories).sort()) ===
    JSON.stringify(expectedSemanticCategories, Object.keys(expectedSemanticCategories).sort()),
  "semantic rejection category counts differ",
);

assert(vectors.event_conflicts.length === 1, "event conflict case count differs");
for (const conflict of vectors.event_conflicts) {
  exactObject(conflict, ["name", "domain", "original", "changed"], conflict.name);
  assert(conflict.domain === DOMAIN_ORDER[8], `${conflict.name}: wrong domain`);
  for (const [label, variant] of [
    ["original", conflict.original],
    ["changed", conflict.changed],
  ]) {
    exactObject(variant, ["event_id", "data", "canonical", "sha256"], `${conflict.name}.${label}`);
    digest(variant.event_id, `${conflict.name}.${label}.event_id`);
    const canonical = canonicalObject(conflict.domain, variant.data);
    assert(variant.data.event_id === variant.event_id, `${conflict.name}.${label}: ID unbound`);
    assert(canonical === variant.canonical, `${conflict.name}.${label}: bytes differ`);
    assert(sha256(canonical) === variant.sha256, `${conflict.name}.${label}: digest differs`);
  }
  assert(
    conflict.original.event_id === conflict.changed.event_id,
    `${conflict.name}: IDs differ`,
  );
  assert(
    conflict.original.sha256 !== conflict.changed.sha256,
    `${conflict.name}: payloads do not conflict`,
  );
}

assert(vectors.version_separation.length === 1, "version separation case count differs");
for (const separation of vectors.version_separation) {
  exactObject(separation, ["name", "domain", "v1", "v2"], separation.name);
  assert(separation.domain === DOMAIN_ORDER[5], `${separation.name}: wrong domain`);
  for (const [label, version] of [
    ["v1", separation.v1],
    ["v2", separation.v2],
  ]) {
    exactObject(version, ["data", "canonical", "sha256"], `${separation.name}.${label}`);
    exactObject(version.data, SCHEMAS.get(DOMAIN_ORDER[5]), `${separation.name}.${label}.data`);
    assert(
      version.data.contract_version === `dbtobsb.runtime-trust.${label}`,
      `${separation.name}.${label}: version literal differs`,
    );
    for (const [name, value] of Object.entries(version.data)) {
      if (name !== "contract_version") {
        validateField(name, value, `${separation.name}.${label}.${name}`);
      }
    }
    const canonical = canonicalJson({ data: version.data, domain: separation.domain });
    assert(canonical === version.canonical, `${separation.name}.${label}: bytes differ`);
    assert(sha256(canonical) === version.sha256, `${separation.name}.${label}: digest differs`);
  }
  assert(separation.v1.sha256 !== separation.v2.sha256, `${separation.name}: digest collision`);
}
const expectedSql = [
  ["create-ledger", "CREATE_LEDGER"],
  ["create-status-view", "CREATE_STATUS_VIEW"],
  ["append-registration", "APPEND_EVENT"],
  ["readback-registration", "READBACK_EVENT"],
  ["append-candidate", "APPEND_EVENT"],
  ["readback-candidate", "READBACK_EVENT"],
  ["append-acceptance", "APPEND_EVENT"],
  ["readback-acceptance", "READBACK_EVENT"],
  ["append-invalidation", "APPEND_EVENT"],
  ["readback-invalidation", "READBACK_EVENT"],
];
assert(vectors.sql.length === expectedSql.length, "SQL golden count differs");
vectors.sql.forEach((value, index) => {
  exactObject(value, ["name", "kind", "semantic_sha256", "utf8_size"], `sql[${index}]`);
  assert(
    value.name === expectedSql[index][0] && value.kind === expectedSql[index][1],
    `sql[${index}]: statement identity differs`,
  );
  digest(value.semantic_sha256, `sql[${index}].semantic_sha256`);
  assert(Number.isInteger(value.utf8_size) && value.utf8_size > 0, `sql[${index}]: size invalid`);
});

console.log(
  "runtime-trust JS semantic contract verified: 12 domains, 10 SQL, " +
    `${vectors.decimal_valid.length} decimal accepts, ` +
    `${vectors.decimal_invalid.length} decimal rejects, ` +
    `${vectors.canonical_invalid.length} canonical rejects, ` +
    `${vectors.timestamp_valid.length} timestamp accepts, ` +
    `${vectors.timestamp_invalid.length} timestamp rejects, ` +
    `${vectors.semantic_invalid.length} semantic rejects, ` +
    `${vectors.event_conflicts.length} event conflict, ` +
    `${vectors.version_separation.length} version separation`,
);
