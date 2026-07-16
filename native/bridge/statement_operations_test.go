package bridge

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
	"testing"
)

const testMarkerToken = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.A.B"

func preparationSubmitRequest(overrides string) string {
	statement := "SELECT 'DBTOBSB_PREPARATION_MARKER_V1." + testMarkerToken +
		"' AS dbtobsb_preparation_marker"
	digest := sha256.Sum256([]byte(statement))
	payload := fmt.Sprintf(
		`{"warehouse_id":%q,"expected_actor_sha256":"%x","registry_version":%q,"registry_operation":%q,"parameters":{"marker_token":%q},"semantic_sha256":"%x"}`,
		testWarehouse,
		sha256.Sum256([]byte(testActor)),
		registryVersion,
		registryPreparationMarkerV1,
		testMarkerToken,
		digest,
	)
	if overrides != "" {
		payload = overrides
	}
	return fmt.Sprintf(
		`{"protocol":%q,"operation":%q,"profile":"operator","canonical_host":%q,"payload":%s}`,
		ProtocolVersion,
		operationSubmit,
		testHost,
		payload,
	)
}

func statementResponse(state string) []byte {
	return []byte(fmt.Sprintf(`{"statement_id":%q,"status":{"state":%q}}`, testQueryID, state))
}

func TestStatementSubmitUsesActorGuardAndOneExactRegisteredRequest(t *testing.T) {
	sender := &fakeSender{status: http.StatusOK, body: statementResponse("SUCCEEDED")}
	engine, factory, authenticator := testEngine(sender)
	response := engine.Execute(
		t.Context(),
		validEnvironment(),
		strings.NewReader(preparationSubmitRequest("")),
	)
	result, ok := response.Result.(StatementResult)
	if !response.OK || response.Code != CodeStatementReceipt || !ok ||
		result.Kind != statementKind || result.Disposition != "TERMINAL_SUCCESS" ||
		factory.calls != 1 || authenticator.calls != 1 || sender.calls != 2 {
		t.Fatalf("unexpected submit result: %s", response)
	}
	guard := sender.requests[0]
	request := sender.requests[1]
	if guard.URL.String() != testHost+"/api/2.0/sql/statements" ||
		request.URL.String() != testHost+"/api/2.0/sql/statements" ||
		request.Method != http.MethodPost || request.GetBody != nil ||
		request.Header.Get("Authorization") != guard.Header.Get("Authorization") {
		t.Fatal("registered submission did not preserve the protected one-send boundary")
	}
	body, err := io.ReadAll(request.Body)
	if err != nil {
		t.Fatal(err)
	}
	var document map[string]any
	if json.Unmarshal(body, &document) != nil || len(document) != 6 ||
		document["disposition"] != "INLINE" || document["format"] != "JSON_ARRAY" ||
		document["on_wait_timeout"] != "CANCEL" || document["wait_timeout"] != "50s" ||
		document["warehouse_id"] != testWarehouse ||
		document["statement"] != "SELECT 'DBTOBSB_PREPARATION_MARKER_V1."+testMarkerToken+"' AS dbtobsb_preparation_marker" {
		t.Fatalf("registered statement request drifted: %s", body)
	}
	var encoded strings.Builder
	if err := EncodeResponse(&encoded, response); err != nil {
		t.Fatal(err)
	}
	for _, forbidden := range []string{testQueryID, testMarkerToken, "SELECT", testActor, testToken} {
		if strings.Contains(encoded.String(), forbidden) {
			t.Fatalf("statement detail escaped response: %s", encoded.String())
		}
	}
}

func TestMutationRegistryRendersMarkerAndFixedBaseWithoutCallerSQL(t *testing.T) {
	operationID := "12345678-1234-4abc-8abc-1234567890ab"
	base := "SELECT CAST(1 AS INT) AS dbtobsb_foundation_sentinel /* fixed-operation:" + operationID + " */"
	digest := sha256.Sum256([]byte(base))
	payload := fmt.Sprintf(
		`{"warehouse_id":%q,"expected_actor_sha256":"%x","registry_version":%q,"registry_operation":%q,"parameters":{"marker_token":%q,"operation_uuid":%q},"semantic_sha256":"%x"}`,
		testWarehouse,
		sha256.Sum256([]byte(testActor)),
		registryVersion,
		registryFoundationSentinelV1,
		testMarkerToken,
		operationID,
		digest,
	)
	sender := &fakeSender{status: http.StatusOK, body: statementResponse("RUNNING")}
	engine, _, _ := testEngine(sender)
	response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(preparationSubmitRequest(payload)))
	result, ok := response.Result.(StatementResult)
	if !response.OK || !ok || result.Disposition != "NONTERMINAL" || sender.calls != 2 {
		t.Fatalf("unexpected mutation receipt: %s", response)
	}
	body, _ := io.ReadAll(sender.request.Body)
	var document struct {
		Statement string `json:"statement"`
	}
	if json.Unmarshal(body, &document) != nil ||
		document.Statement != "/* DBTOBSB_MUTATION_MARKER_V1."+testMarkerToken+" */\n"+base {
		t.Fatalf("fixed mutation rendering drifted: %s", body)
	}
}

func TestStatementSubmitExhaustivelyMapsSixStates(t *testing.T) {
	tests := map[string]string{
		"SUCCEEDED": "TERMINAL_SUCCESS",
		"CLOSED":    "TERMINAL_SUCCESS",
		"FAILED":    "TERMINAL_FAILURE",
		"CANCELED":  "CANCELLATION_NONTERMINAL",
		"PENDING":   "NONTERMINAL",
		"RUNNING":   "NONTERMINAL",
	}
	for state, expected := range tests {
		t.Run(state, func(t *testing.T) {
			body := statementResponse(state)
			if state == "FAILED" {
				body = []byte(fmt.Sprintf(
					`{"statement_id":%q,"status":{"state":"FAILED","sql_state":"XX000","error":{"error_code":"redacted","message":"redacted"}}}`,
					testQueryID,
				))
			}
			sender := &fakeSender{status: http.StatusOK, body: body}
			engine, _, _ := testEngine(sender)
			response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(preparationSubmitRequest("")))
			result, ok := response.Result.(StatementResult)
			if !response.OK || !ok || result.Disposition != expected || sender.calls != 2 {
				t.Fatalf("unexpected %s result: %s", state, response)
			}
		})
	}
}

func TestStatementRegistryRejectsInvalidDescriptorsBeforeAuthentication(t *testing.T) {
	validStatement := "SELECT 'DBTOBSB_PREPARATION_MARKER_V1." + testMarkerToken +
		"' AS dbtobsb_preparation_marker"
	validDigest := fmt.Sprintf("%x", sha256.Sum256([]byte(validStatement)))
	actorDigest := fmt.Sprintf("%x", sha256.Sum256([]byte(testActor)))
	tests := map[string]struct {
		payload string
		code    string
	}{
		"unknown operation": {
			payload: fmt.Sprintf(`{"warehouse_id":%q,"expected_actor_sha256":%q,"registry_version":%q,"registry_operation":"arbitrary_sql_v1","parameters":{"marker_token":%q},"semantic_sha256":%q}`, testWarehouse, actorDigest, registryVersion, testMarkerToken, validDigest),
			code:    CodeRegistryOperationDenied,
		},
		"extra parameter": {
			payload: fmt.Sprintf(`{"warehouse_id":%q,"expected_actor_sha256":%q,"registry_version":%q,"registry_operation":%q,"parameters":{"marker_token":%q,"statement":"DROP TABLE x"},"semantic_sha256":%q}`, testWarehouse, actorDigest, registryVersion, registryPreparationMarkerV1, testMarkerToken, validDigest),
			code:    CodeRegistryParametersInvalid,
		},
		"digest mismatch": {
			payload: fmt.Sprintf(`{"warehouse_id":%q,"expected_actor_sha256":%q,"registry_version":%q,"registry_operation":%q,"parameters":{"marker_token":%q},"semantic_sha256":"%064d"}`, testWarehouse, actorDigest, registryVersion, registryPreparationMarkerV1, testMarkerToken, 0),
			code:    CodeRegistryDigestMismatch,
		},
		"marker injection": {
			payload: fmt.Sprintf(`{"warehouse_id":%q,"expected_actor_sha256":%q,"registry_version":%q,"registry_operation":%q,"parameters":{"marker_token":"x'; DROP TABLE x --"},"semantic_sha256":%q}`, testWarehouse, actorDigest, registryVersion, registryPreparationMarkerV1, validDigest),
			code:    CodeRegistryParametersInvalid,
		},
	}
	for name, test := range tests {
		t.Run(name, func(t *testing.T) {
			sender := &fakeSender{}
			engine, factory, authenticator := testEngine(sender)
			response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(preparationSubmitRequest(test.payload)))
			if response.OK || response.Code != test.code || sender.calls != 0 ||
				factory.calls != 0 || authenticator.calls != 0 {
				t.Fatalf("invalid registry descriptor reached auth or network: %s", response)
			}
		})
	}
}

func TestStatementSubmitResponseAndTransportAmbiguityNeverRetry(t *testing.T) {
	tests := map[string]*fakeSender{
		"transport": {err: fmt.Errorf("response lost")},
		"server":    {status: http.StatusServiceUnavailable, body: []byte(`{"error_code":"redacted"}`)},
		"malformed": {status: http.StatusOK, body: []byte(`{"statement_id":"not-a-uuid","status":{"state":"SUCCEEDED"}}`)},
	}
	for name, sender := range tests {
		t.Run(name, func(t *testing.T) {
			engine, _, _ := testEngine(sender)
			response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(preparationSubmitRequest("")))
			expected := CodeStatementIndeterminate
			if name == "malformed" {
				expected = CodeStatementResponseInvalid
			}
			if response.OK || response.Code != expected || sender.calls != 2 {
				t.Fatalf("ambiguous statement was retried or misclassified: %s", response)
			}
		})
	}
}

func TestStatementSubmitExplicitClientRejectionIsTerminalFailure(t *testing.T) {
	for _, status := range []int{http.StatusBadRequest, http.StatusUnauthorized, http.StatusForbidden, http.StatusNotFound} {
		sender := &fakeSender{status: status, body: []byte(`{"error_code":"redacted"}`)}
		engine, _, _ := testEngine(sender)
		response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(preparationSubmitRequest("")))
		result, ok := response.Result.(StatementResult)
		if !response.OK || !ok || result.Disposition != "TERMINAL_FAILURE" || sender.calls != 2 {
			t.Fatalf("explicit rejection was not terminal: %s", response)
		}
	}
}
