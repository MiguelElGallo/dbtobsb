package bridge

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"regexp"
	"strconv"
	"strings"
	"unicode/utf8"
)

const (
	bootstrapCreateArtifactRegistryTableV1 = "bootstrap_create_artifact_registry_table_v1"
	bootstrapCreateInvocationsTableV1      = "bootstrap_create_invocations_table_v1"
	bootstrapCreateNodeResultsTableV1      = "bootstrap_create_node_results_table_v1"
	bootstrapCreateRawVolumeV1             = "bootstrap_create_raw_volume_v1"
	bootstrapCreateStageVolumeV1           = "bootstrap_create_stage_volume_v1"
	bootstrapCreateRunHealthViewV1         = "bootstrap_create_run_health_view_v1"
	bootstrapCreateNodeHealthViewV1        = "bootstrap_create_node_health_view_v1"
	bootstrapCreateCollectionHealthViewV1  = "bootstrap_create_collection_health_view_v1"
	bootstrapCreateObjectManifestTableV1   = "bootstrap_create_object_manifest_table_v1"
	bootstrapInsertObjectManifestV1        = "bootstrap_insert_object_manifest_v1"

	objectManifestVersion           = "dbtobsb.evidence.v1.0.0-rc.11"
	objectContractSHA256            = "603afcbf9a1b52d926a1aba6f46b74f76f1783dfd7edc66d1ccc9003ba3d7605"
	baseObservabilityContractSHA256 = "b1c28a474d2fa79f7e881f862a9f02c27a398261a90f723a07a3f5f54e6f02ae"
)

var regularIdentifierPattern = regexp.MustCompile(`^[A-Za-z_][A-Za-z0-9_]{0,127}$`)

type bootstrapObjectParameters struct {
	Catalog     string `json:"catalog"`
	MarkerToken string `json:"marker_token"`
	Schema      string `json:"schema"`
}

type bootstrapManifestParameters struct {
	BaseObservabilityContractSHA256 string `json:"base_observability_contract_sha256"`
	Catalog                         string `json:"catalog"`
	CollectorEnvironmentSHA256      string `json:"collector_environment_sha256"`
	CollectorJobID                  string `json:"collector_job_id"`
	CollectorServicePrincipalName   string `json:"collector_service_principal_name"`
	EvidenceCatalog                 string `json:"evidence_catalog"`
	EvidenceSchema                  string `json:"evidence_schema"`
	ExpectedRuntimePolicySHA256     string `json:"expected_runtime_policy_sha256"`
	InstallationID                  string `json:"installation_id"`
	JobManagerGroupName             string `json:"job_manager_group_name"`
	ManifestVersion                 string `json:"manifest_version"`
	MarkerToken                     string `json:"marker_token"`
	ObjectContractSHA256            string `json:"object_contract_sha256"`
	ObservedJobID                   string `json:"observed_job_id"`
	ObservedServicePrincipalName    string `json:"observed_service_principal_name"`
	ReconcilerJobID                 string `json:"reconciler_job_id"`
	Schema                          string `json:"schema"`
	SourceContractSHA256            string `json:"source_contract_sha256"`
	WarehouseID                     string `json:"warehouse_id"`
	WorkspaceID                     string `json:"workspace_id"`
}

type sqlField struct {
	name     string
	dataType string
}

var artifactRegistryFields = []sqlField{
	{"workspace_id", "BIGINT"},
	{"dbt_task_run_id", "BIGINT"},
	{"observed_job_id", "BIGINT"},
	{"observed_job_run_id", "BIGINT"},
	{"observed_task_key", "STRING"},
	{"repair_count", "INT"},
	{"execution_count", "INT"},
	{"attempt_number", "INT"},
	{"task_start_time", "TIMESTAMP"},
	{"task_end_time", "TIMESTAMP"},
	{"lakeflow_result_state", "STRING"},
	{"retrieval_state", "STRING"},
	{"capture_state", "STRING"},
	{"pair_state", "STRING"},
	{"dbt_include_deps", "BOOLEAN"},
	{"issue_code", "STRING"},
	{"logs_truncated", "BOOLEAN"},
	{"archive_sha256", "STRING"},
	{"archive_size_bytes", "BIGINT"},
	{"raw_archive_locator", "STRING"},
	{"manifest_sha256", "STRING"},
	{"manifest_size_bytes", "BIGINT"},
	{"run_results_sha256", "STRING"},
	{"run_results_size_bytes", "BIGINT"},
	{"structured_log_state", "STRING"},
	{"structured_log_sha256", "STRING"},
	{"structured_log_size_bytes", "BIGINT"},
	{"structured_log_file_count", "INT"},
	{"structured_log_version", "INT"},
	{"deps_structured_log_state", "STRING"},
	{"deps_structured_log_sha256", "STRING"},
	{"deps_structured_log_size_bytes", "BIGINT"},
	{"deps_structured_log_file_count", "INT"},
	{"deps_structured_log_version", "INT"},
	{"structured_log_expected_dbt_common_version", "STRING"},
	{"invocation_id", "STRING"},
	{"expected_node_count", "BIGINT"},
	{"normalized_digest", "STRING"},
	{"collector_state", "STRING"},
	{"collected_at", "TIMESTAMP"},
	{"published_at", "TIMESTAMP"},
	{"first_discovered_at", "TIMESTAMP"},
	{"last_attempted_at", "TIMESTAMP"},
	{"collection_attempt_count", "INT"},
	{"collection_issue_code", "STRING"},
	{"last_reconciliation_run_id", "BIGINT"},
}

var invocationFields = []sqlField{
	{"workspace_id", "BIGINT"},
	{"dbt_task_run_id", "BIGINT"},
	{"invocation_id", "STRING"},
	{"generated_at", "TIMESTAMP"},
	{"elapsed_time", "DOUBLE"},
	{"dbt_version", "STRING"},
	{"adapter_type", "STRING"},
	{"command", "STRING"},
	{"result_count", "BIGINT"},
	{"status_counts_json", "STRING"},
	{"normalized_digest", "STRING"},
}

var nodeResultFields = []sqlField{
	{"workspace_id", "BIGINT"},
	{"dbt_task_run_id", "BIGINT"},
	{"invocation_id", "STRING"},
	{"unique_id", "STRING"},
	{"resource_type", "STRING"},
	{"status", "STRING"},
	{"execution_time", "DOUBLE"},
	{"failures", "BIGINT"},
	{"normalized_digest", "STRING"},
}

var manifestFields = []sqlField{
	{"manifest_version", "STRING"},
	{"object_contract_sha256", "STRING"},
	{"source_contract_sha256", "STRING"},
	{"expected_runtime_policy_sha256", "STRING"},
	{"base_observability_contract_sha256", "STRING"},
	{"installation_id", "STRING"},
	{"workspace_id", "BIGINT"},
	{"evidence_catalog", "STRING"},
	{"evidence_schema", "STRING"},
	{"warehouse_id", "STRING"},
	{"observed_job_id", "BIGINT"},
	{"collector_job_id", "BIGINT"},
	{"reconciler_job_id", "BIGINT"},
	{"observed_service_principal_name", "STRING"},
	{"collector_service_principal_name", "STRING"},
	{"job_manager_group_name", "STRING"},
	{"collector_environment_sha256", "STRING"},
}

func renderBootstrapRegisteredStatement(
	operation string,
	raw json.RawMessage,
) (statement string, semanticBasis string, recognized bool, err error) {
	objectRole := ""
	objectName := ""
	var fields []sqlField
	viewQuery := ""
	switch operation {
	case bootstrapCreateArtifactRegistryTableV1:
		objectRole, objectName, fields = "dbt_artifact_registry", "dbt_artifact_registry", artifactRegistryFields
	case bootstrapCreateInvocationsTableV1:
		objectRole, objectName, fields = "dbt_invocations", "dbt_invocations", invocationFields
	case bootstrapCreateNodeResultsTableV1:
		objectRole, objectName, fields = "dbt_node_results", "dbt_node_results", nodeResultFields
	case bootstrapCreateRawVolumeV1:
		objectRole, objectName = "raw_volume", "dbtobsb_raw"
	case bootstrapCreateStageVolumeV1:
		objectRole, objectName = "artifact_stage", "dbtobsb_stage"
	case bootstrapCreateRunHealthViewV1:
		objectRole, objectName = "dbt_run_health", "dbt_run_health"
		viewQuery = runHealthViewSQL
	case bootstrapCreateNodeHealthViewV1:
		objectRole, objectName = "dbt_node_health", "dbt_node_health"
		viewQuery = nodeHealthViewSQL
	case bootstrapCreateCollectionHealthViewV1:
		objectRole, objectName = "dbt_collection_health", "dbt_collection_health"
		viewQuery = collectionHealthViewSQL
	case bootstrapCreateObjectManifestTableV1:
		objectRole, objectName, fields = "object_manifest", "dbtobsb_object_manifest", manifestFields
	case bootstrapInsertObjectManifestV1:
		return renderBootstrapManifestInsert(raw)
	default:
		return "", "", false, nil
	}
	var parameters bootstrapObjectParameters
	if strictUnmarshal(raw, &parameters) != nil ||
		!validBootstrapIdentifier(parameters.Catalog) ||
		!validBootstrapIdentifier(parameters.Schema) ||
		!validMarkerToken(parameters.MarkerToken) {
		return "", "", true, fail(CodeRegistryParametersInvalid)
	}
	qualified := qualifyBootstrap(parameters.Catalog, parameters.Schema, objectName)
	switch {
	case operation == bootstrapCreateRawVolumeV1 || operation == bootstrapCreateStageVolumeV1:
		role := "raw_volume"
		if operation == bootstrapCreateStageVolumeV1 {
			role = "artifact_stage"
		}
		semanticBasis = "CREATE VOLUME " + qualified + " COMMENT " + sqlLiteral(
			"dbtobsb|manifest="+objectManifestVersion+"|contract="+objectContractSHA256+"|role="+role,
		)
	case viewQuery != "":
		registry := qualifyBootstrap(parameters.Catalog, parameters.Schema, "dbt_artifact_registry")
		invocations := qualifyBootstrap(parameters.Catalog, parameters.Schema, "dbt_invocations")
		nodes := qualifyBootstrap(parameters.Catalog, parameters.Schema, "dbt_node_results")
		query := strings.NewReplacer(
			"__REGISTRY__", registry,
			"__INVOCATIONS__", invocations,
			"__NODES__", nodes,
		).Replace(viewQuery)
		semanticBasis = "CREATE VIEW " + qualified + "\nTBLPROPERTIES (\n  " +
			propertiesSQL(objectRole) + "\n)\nAS\n" + query
	default:
		semanticBasis = "CREATE TABLE " + qualified + " (\n  " + columnSQL(fields) +
			"\n) USING DELTA\nTBLPROPERTIES (\n  " + propertiesSQL(objectRole) + "\n)"
	}
	statement = mutationMarker(parameters.MarkerToken, semanticBasis)
	return statement, semanticBasis, true, nil
}

func renderBootstrapManifestInsert(raw json.RawMessage) (string, string, bool, error) {
	var p bootstrapManifestParameters
	if strictUnmarshal(raw, &p) != nil ||
		!validBootstrapIdentifier(p.Catalog) || !validBootstrapIdentifier(p.Schema) ||
		!validMarkerToken(p.MarkerToken) ||
		p.ManifestVersion != objectManifestVersion ||
		p.ObjectContractSHA256 != objectContractSHA256 ||
		!sha256Pattern.MatchString(p.SourceContractSHA256) ||
		!sha256Pattern.MatchString(p.ExpectedRuntimePolicySHA256) ||
		p.BaseObservabilityContractSHA256 != baseObservabilityContractSHA256 ||
		!sha256Pattern.MatchString(p.InstallationID) ||
		p.EvidenceCatalog != p.Catalog || p.EvidenceSchema != p.Schema ||
		!warehousePattern.MatchString(p.WarehouseID) ||
		!positiveDecimal(p.WorkspaceID) || !positiveDecimal(p.ObservedJobID) ||
		!positiveDecimal(p.CollectorJobID) || !positiveDecimal(p.ReconcilerJobID) ||
		!validBootstrapText(p.ObservedServicePrincipalName) ||
		!validBootstrapText(p.CollectorServicePrincipalName) ||
		p.ObservedServicePrincipalName == p.CollectorServicePrincipalName ||
		!validBootstrapText(p.JobManagerGroupName) ||
		!sha256Pattern.MatchString(p.CollectorEnvironmentSHA256) {
		return "", "", true, fail(CodeRegistryParametersInvalid)
	}
	expectedInstallationID, ok := bootstrapInstallationID(p)
	if !ok || p.InstallationID != expectedInstallationID {
		return "", "", true, fail(CodeRegistryParametersInvalid)
	}
	columns := make([]string, 0, len(manifestFields))
	for _, field := range manifestFields {
		columns = append(columns, field.name)
	}
	values := []string{
		sqlLiteral(p.ManifestVersion),
		sqlLiteral(p.ObjectContractSHA256),
		sqlLiteral(p.SourceContractSHA256),
		sqlLiteral(p.ExpectedRuntimePolicySHA256),
		sqlLiteral(p.BaseObservabilityContractSHA256),
		sqlLiteral(p.InstallationID),
		p.WorkspaceID,
		sqlLiteral(p.EvidenceCatalog),
		sqlLiteral(p.EvidenceSchema),
		sqlLiteral(p.WarehouseID),
		p.ObservedJobID,
		p.CollectorJobID,
		p.ReconcilerJobID,
		sqlLiteral(p.ObservedServicePrincipalName),
		sqlLiteral(p.CollectorServicePrincipalName),
		sqlLiteral(p.JobManagerGroupName),
		sqlLiteral(p.CollectorEnvironmentSHA256),
	}
	manifest := qualifyBootstrap(p.Catalog, p.Schema, "dbtobsb_object_manifest")
	semantic := "INSERT INTO " + manifest + " (" + strings.Join(columns, ", ") + ")\nVALUES (" +
		strings.Join(values, ", ") + ")"
	return mutationMarker(p.MarkerToken, semantic), semantic, true, nil
}

func bootstrapInstallationID(p bootstrapManifestParameters) (string, bool) {
	workspaceID, workspaceErr := strconv.ParseInt(p.WorkspaceID, 10, 64)
	observedJobID, observedErr := strconv.ParseInt(p.ObservedJobID, 10, 64)
	collectorJobID, collectorErr := strconv.ParseInt(p.CollectorJobID, 10, 64)
	reconcilerJobID, reconcilerErr := strconv.ParseInt(p.ReconcilerJobID, 10, 64)
	if workspaceErr != nil || observedErr != nil || collectorErr != nil || reconcilerErr != nil {
		return "", false
	}
	payload := map[string]any{
		"workspace_id":                       workspaceID,
		"catalog":                            p.Catalog,
		"schema":                             p.Schema,
		"warehouse_id":                       p.WarehouseID,
		"source_contract_sha256":              p.SourceContractSHA256,
		"expected_runtime_policy_sha256":      p.ExpectedRuntimePolicySHA256,
		"observed_job_id":                     observedJobID,
		"collector_job_id":                    collectorJobID,
		"reconciler_job_id":                   reconcilerJobID,
		"observed_service_principal_name":     p.ObservedServicePrincipalName,
		"collector_service_principal_name":    p.CollectorServicePrincipalName,
		"job_manager_group_name":              p.JobManagerGroupName,
		"collector_environment_sha256":        p.CollectorEnvironmentSHA256,
	}
	raw, err := json.Marshal(payload)
	if err != nil {
		return "", false
	}
	digest := sha256.Sum256(raw)
	return hex.EncodeToString(digest[:]), true
}

func validBootstrapIdentifier(value string) bool {
	return regularIdentifierPattern.MatchString(value)
}

func validBootstrapText(value string) bool {
	if value == "" || value != strings.TrimSpace(value) || len(value) > 512 || !utf8.ValidString(value) {
		return false
	}
	for _, character := range value {
		if character < 32 || character == 127 {
			return false
		}
	}
	return true
}

func positiveDecimal(value string) bool {
	if value == "" || value[0] == '0' {
		return false
	}
	parsed, err := strconv.ParseInt(value, 10, 64)
	return err == nil && parsed > 0 && strconv.FormatInt(parsed, 10) == value
}

func qualifyBootstrap(catalog, schema, object string) string {
	return "`" + catalog + "`.`" + schema + "`.`" + object + "`"
}

func sqlLiteral(value string) string {
	return "'" + strings.ReplaceAll(value, "'", "''") + "'"
}

func propertiesSQL(role string) string {
	return sqlLiteral("dbtobsb.product") + " = " + sqlLiteral("dbtobsb") + ",\n  " +
		sqlLiteral("dbtobsb.object_manifest_version") + " = " + sqlLiteral(objectManifestVersion) + ",\n  " +
		sqlLiteral("dbtobsb.object_contract_sha256") + " = " + sqlLiteral(objectContractSHA256) + ",\n  " +
		sqlLiteral("dbtobsb.object_role") + " = " + sqlLiteral(role)
}

func columnSQL(fields []sqlField) string {
	parts := make([]string, 0, len(fields))
	for _, field := range fields {
		parts = append(parts, "`"+field.name+"` "+field.dataType)
	}
	return strings.Join(parts, ",\n  ")
}

func mutationMarker(markerToken, semantic string) string {
	return "/* DBTOBSB_MUTATION_MARKER_V1." + markerToken + " */\n" + semantic
}

const runHealthViewSQL = `SELECT
  r.* EXCEPT (raw_archive_locator, collector_state),
  i.generated_at,
  i.elapsed_time,
  i.dbt_version,
  i.adapter_type,
  i.command,
  i.result_count,
  i.status_counts_json
FROM __REGISTRY__ AS r
LEFT JOIN __INVOCATIONS__ AS i
  ON r.workspace_id = i.workspace_id
  AND r.dbt_task_run_id = i.dbt_task_run_id
  AND r.normalized_digest = i.normalized_digest
WHERE r.collector_state = 'PUBLISHED'`

const nodeHealthViewSQL = `SELECT
  r.workspace_id,
  r.dbt_task_run_id,
  r.observed_job_id,
  r.observed_job_run_id,
  r.observed_task_key,
  r.capture_state,
  r.lakeflow_result_state,
  n.invocation_id,
  n.unique_id,
  n.resource_type,
  n.status,
  n.execution_time,
  n.failures
FROM __REGISTRY__ AS r
INNER JOIN __NODES__ AS n
  USING (workspace_id, dbt_task_run_id, normalized_digest)
WHERE r.collector_state = 'PUBLISHED'`

const collectionHealthViewSQL = `SELECT
  workspace_id,
  dbt_task_run_id,
  observed_job_id,
  observed_job_run_id,
  observed_task_key,
  repair_count,
  execution_count,
  attempt_number,
  task_start_time,
  task_end_time,
  lakeflow_result_state,
  collector_state,
  collection_issue_code,
  first_discovered_at,
  last_attempted_at,
  collection_attempt_count,
  published_at,
  last_reconciliation_run_id
FROM __REGISTRY__`
