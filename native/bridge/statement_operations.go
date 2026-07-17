package bridge

import (
	"bytes"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/json"
	"fmt"
	"net/http"
	"regexp"
	"strings"
	"time"

	"github.com/databricks/databricks-sdk-go/service/sql"
	"github.com/google/uuid"
)

const (
	registryVersion              = "dbtobsb.native-operation-registry.v1"
	registryPreparationMarkerV1  = "preparation_marker_v1"
	registryFoundationSentinelV1 = "foundation_sentinel_v1"
	maxStatementBodyBytes        = 64 * 1024
	maxMarkerTokenBytes          = 16 * 1024
	statementKind                = "statement_execution_submit"
)

var base32TokenPattern = regexp.MustCompile(`^[A-Z2-7]+$`)

type submitPayload struct {
	WarehouseID         string          `json:"warehouse_id"`
	ExpectedActorSHA256 string          `json:"expected_actor_sha256"`
	RegistryVersion     string          `json:"registry_version"`
	RegistryOperation   string          `json:"registry_operation"`
	Parameters          json.RawMessage `json:"parameters"`
	SemanticSHA256      string          `json:"semantic_sha256"`
}

type submitOperation struct {
	payload   submitPayload
	statement string
}

type preparationMarkerParameters struct {
	MarkerToken string `json:"marker_token"`
}

type foundationSentinelParameters struct {
	MarkerToken   string `json:"marker_token"`
	OperationUUID string `json:"operation_uuid"`
}

type StatementResult struct {
	Kind        string `json:"kind"`
	Disposition string `json:"disposition"`
}

func (r StatementResult) String() string {
	return fmt.Sprintf("StatementResult(disposition=%s, <redacted>)", r.Disposition)
}

func renderRegisteredStatement(payload submitPayload) (string, error) {
	if len(payload.Parameters) == 0 || bytes.Equal(bytes.TrimSpace(payload.Parameters), []byte("null")) {
		return "", fail(CodeRegistryParametersInvalid)
	}
	var statement string
	var semanticBasis string
	switch payload.RegistryOperation {
	case registryPreparationMarkerV1:
		var parameters preparationMarkerParameters
		if strictUnmarshal(payload.Parameters, &parameters) != nil || !validMarkerToken(parameters.MarkerToken) {
			return "", fail(CodeRegistryParametersInvalid)
		}
		statement = "SELECT 'DBTOBSB_PREPARATION_MARKER_V1." + parameters.MarkerToken +
			"' AS dbtobsb_preparation_marker"
		semanticBasis = statement
	case registryFoundationSentinelV1:
		var parameters foundationSentinelParameters
		if strictUnmarshal(payload.Parameters, &parameters) != nil ||
			!validMarkerToken(parameters.MarkerToken) || !canonicalV4UUID(parameters.OperationUUID) {
			return "", fail(CodeRegistryParametersInvalid)
		}
		semanticBasis = "SELECT CAST(1 AS INT) AS dbtobsb_foundation_sentinel /* fixed-operation:" +
			parameters.OperationUUID + " */"
		statement = "/* DBTOBSB_MUTATION_MARKER_V1." + parameters.MarkerToken + " */\n" + semanticBasis
	default:
		var recognized bool
		var err error
		statement, semanticBasis, recognized, err = renderBootstrapRegisteredStatement(
			payload.RegistryOperation,
			payload.Parameters,
		)
		if err != nil {
			return "", err
		}
		if !recognized {
			return "", fail(CodeRegistryOperationDenied)
		}
	}
	digest := sha256.Sum256([]byte(semanticBasis))
	expected, err := decodeLowerHex(payload.SemanticSHA256)
	if err != nil {
		return "", fail(CodeRegistryDigestMismatch)
	}
	if subtle.ConstantTimeCompare(digest[:], expected) != 1 {
		return "", fail(CodeRegistryDigestMismatch)
	}
	return statement, nil
}

func validMarkerToken(value string) bool {
	if value == "" || len(value) > maxMarkerTokenBytes {
		return false
	}
	parts := strings.Split(value, ".")
	return len(parts) == 3 && sha256Pattern.MatchString(parts[0]) &&
		parts[1] != "" && base32TokenPattern.MatchString(parts[1]) &&
		parts[2] != "" && base32TokenPattern.MatchString(parts[2])
}

func canonicalV4UUID(value string) bool {
	parsed, err := uuid.Parse(value)
	return err == nil && parsed.Version() == 4 && parsed.String() == value
}

func (o submitOperation) buildRequest(host string) (*http.Request, error) {
	document := struct {
		Disposition   string `json:"disposition"`
		Format        string `json:"format"`
		OnWaitTimeout string `json:"on_wait_timeout"`
		Statement     string `json:"statement"`
		WaitTimeout   string `json:"wait_timeout"`
		WarehouseID   string `json:"warehouse_id"`
	}{
		Disposition:   "INLINE",
		Format:        "JSON_ARRAY",
		OnWaitTimeout: "CANCEL",
		Statement:     o.statement,
		WaitTimeout:   "50s",
		WarehouseID:   o.payload.WarehouseID,
	}
	body, err := json.Marshal(document)
	if err != nil {
		return nil, fail(CodeInternalFailure)
	}
	request, err := http.NewRequest(
		http.MethodPost,
		host+"/api/2.0/sql/statements",
		bytes.NewReader(body),
	)
	if err != nil {
		return nil, fail(CodeRequestInvalid)
	}
	request.GetBody = nil
	request.Header.Set("Accept", "application/json")
	request.Header.Set("Content-Type", "application/json")
	request.Header.Set("User-Agent", "dbtobsb-native-bridge/1")
	return request, nil
}

func (o submitOperation) parseResponse(status int, body []byte) (any, string, error) {
	switch status {
	case http.StatusOK:
		disposition, err := parseStatementDisposition(body)
		if err != nil {
			return nil, "", err
		}
		return StatementResult{Kind: statementKind, Disposition: disposition}, CodeStatementReceipt, nil
	case http.StatusBadRequest, http.StatusUnauthorized, http.StatusForbidden, http.StatusNotFound:
		return StatementResult{Kind: statementKind, Disposition: "TERMINAL_FAILURE"}, CodeStatementReceipt, nil
	default:
		return nil, "", fail(CodeStatementIndeterminate)
	}
}

func (submitOperation) maxResponseBytes() int64   { return maxStatementBodyBytes }
func (submitOperation) indeterminateCode() string { return CodeStatementIndeterminate }
func (submitOperation) timeout() time.Duration    { return 105 * time.Second }

func (o submitOperation) actorGuard() actorCheckOperation {
	return actorCheckOperation{payload: actorCheckPayload{
		WarehouseID:         o.payload.WarehouseID,
		ExpectedActorSHA256: o.payload.ExpectedActorSHA256,
	}}
}

func parseStatementDisposition(body []byte) (string, error) {
	top, err := strictStatementObject(
		body,
		[]string{"manifest", "result", "statement_id", "status"},
		[]string{"statement_id", "status"},
	)
	if err != nil {
		return "", err
	}
	var statementID string
	if strictUnmarshal(top["statement_id"], &statementID) != nil || !canonicalUUID(statementID) {
		return "", fail(CodeStatementResponseInvalid)
	}
	status, err := strictStatementObject(
		top["status"],
		[]string{"error", "sql_state", "state"},
		[]string{"state"},
	)
	if err != nil {
		return "", err
	}
	var state sql.StatementState
	if strictUnmarshal(status["state"], &state) != nil {
		return "", fail(CodeStatementResponseInvalid)
	}
	switch state {
	case sql.StatementStateSucceeded:
		if len(status) != 1 {
			return "", fail(CodeStatementResponseInvalid)
		}
		return "TERMINAL_SUCCESS", nil
	case sql.StatementStateFailed:
		return "TERMINAL_FAILURE", nil
	case sql.StatementStateCanceled:
		if len(status) != 1 {
			return "", fail(CodeStatementResponseInvalid)
		}
		return "CANCELLATION_NONTERMINAL", nil
	case sql.StatementStatePending, sql.StatementStateRunning:
		if len(status) != 1 {
			return "", fail(CodeStatementResponseInvalid)
		}
		return "NONTERMINAL", nil
	case sql.StatementStateClosed:
		if len(status) != 1 {
			return "", fail(CodeStatementResponseInvalid)
		}
		return "TERMINAL_SUCCESS", nil
	default:
		return "", fail(CodeStatementResponseInvalid)
	}
}

func strictStatementObject(raw json.RawMessage, allowed, required []string) (map[string]json.RawMessage, error) {
	var object map[string]json.RawMessage
	if strictUnmarshal(raw, &object) != nil || object == nil {
		return nil, fail(CodeStatementResponseInvalid)
	}
	allowedSet := make(map[string]struct{}, len(allowed))
	for _, key := range allowed {
		allowedSet[key] = struct{}{}
	}
	for key := range object {
		if _, accepted := allowedSet[key]; !accepted {
			return nil, fail(CodeStatementResponseInvalid)
		}
	}
	for _, key := range required {
		if _, present := object[key]; !present {
			return nil, fail(CodeStatementResponseInvalid)
		}
	}
	return object, nil
}
