package bridge

import (
	"bytes"
	"context"
	"crypto/sha256"
	"crypto/x509"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"
	"time"

	cliauth "github.com/databricks/cli/libs/auth"
)

const (
	testHost      = "https://adb-7405613481361850.10.azuredatabricks.net"
	testWarehouse = "0123456789abcdef"
	testQueryID   = "123e4567-e89b-12d3-a456-426614174000"
	testToken     = "native-keyring-secret-token"
	testActor     = "approved.actor@example.com"
)

type fakeAuthenticator struct {
	token string
	calls int
	err   error
}

func (a *fakeAuthenticator) Authenticate(request *http.Request) error {
	a.calls++
	if a.err != nil {
		return a.err
	}
	if a.token != "" {
		request.Header.Set("Authorization", "Bearer "+a.token)
	}
	return nil
}

type fakeFactory struct {
	authenticator *fakeAuthenticator
	calls         int
	profile       string
	host          string
	err           error
}

func (f *fakeFactory) Resolve(_ context.Context, profile, host string) (requestAuthenticator, error) {
	f.calls++
	f.profile = profile
	f.host = host
	if f.err != nil {
		return nil, f.err
	}
	return f.authenticator, nil
}

type fakeSender struct {
	calls            int
	request          *http.Request
	requests         []*http.Request
	body             []byte
	status           int
	err              error
	wait             bool
	disableAutoActor bool
}

func (s *fakeSender) Do(request *http.Request) (*http.Response, error) {
	s.calls++
	s.request = request
	s.requests = append(s.requests, request)
	if !s.disableAutoActor && s.calls == 1 && request.URL.Path == "/api/2.0/sql/statements" {
		return &http.Response{
			StatusCode: http.StatusOK,
			Body:       io.NopCloser(strings.NewReader(actorResponse(testActor, "SUCCEEDED"))),
			Header:     make(http.Header),
		}, nil
	}
	if s.wait {
		<-request.Context().Done()
		return nil, request.Context().Err()
	}
	if s.err != nil {
		return nil, s.err
	}
	return &http.Response{
		StatusCode: s.status,
		Body:       io.NopCloser(bytes.NewReader(s.body)),
		Header:     make(http.Header),
	}, nil
}

func validEnvironment() []string {
	return []string{"HOME=/tmp/dbtobsb-operator", "DATABRICKS_AUTH_STORAGE=secure", "LANG=C"}
}

func historyRequest(payload string) string {
	digest := sha256.Sum256([]byte(testActor))
	if payload == "" {
		payload = fmt.Sprintf(
			`{"warehouse_id":%q,"expected_actor_sha256":"%x","start_time_ms":1000,"end_time_ms":2000}`,
			testWarehouse,
			digest,
		)
	} else if !strings.Contains(payload, `"expected_actor_sha256"`) {
		payload = strings.TrimSuffix(payload, "}") + fmt.Sprintf(`,"expected_actor_sha256":"%x"}`, digest)
	}
	return fmt.Sprintf(
		`{"protocol":%q,"operation":"query_history_list","profile":"operator","canonical_host":%q,"payload":%s}`,
		ProtocolVersion,
		testHost,
		payload,
	)
}

func cancelRequest(payload string) string {
	digest := sha256.Sum256([]byte(testActor))
	if payload == "" {
		payload = fmt.Sprintf(
			`{"statement_id":%q,"warehouse_id":%q,"expected_actor_sha256":"%x"}`,
			testQueryID,
			testWarehouse,
			digest,
		)
	} else if !strings.Contains(payload, `"expected_actor_sha256"`) {
		payload = strings.TrimSuffix(payload, "}") + fmt.Sprintf(
			`,"warehouse_id":%q,"expected_actor_sha256":"%x"}`,
			testWarehouse,
			digest,
		)
	}
	return fmt.Sprintf(
		`{"protocol":%q,"operation":"statement_execution_cancel","profile":"operator","canonical_host":%q,"payload":%s}`,
		ProtocolVersion,
		testHost,
		payload,
	)
}

func actorRequest(identity string) string {
	digest := sha256.Sum256([]byte(identity))
	payload := fmt.Sprintf(
		`{"warehouse_id":%q,"expected_actor_sha256":"%x"}`,
		testWarehouse,
		digest,
	)
	return fmt.Sprintf(
		`{"protocol":%q,"operation":"actor_identity_check","profile":"operator","canonical_host":%q,"payload":%s}`,
		ProtocolVersion,
		testHost,
		payload,
	)
}

func actorObserveRequest(payload string) string {
	if payload == "" {
		payload = fmt.Sprintf(`{"warehouse_id":%q}`, testWarehouse)
	}
	return fmt.Sprintf(
		`{"protocol":%q,"operation":"actor_fingerprint_observe","profile":"operator","canonical_host":%q,"payload":%s}`,
		ProtocolVersion,
		testHost,
		payload,
	)
}

func actorResponse(identity, state string) string {
	return fmt.Sprintf(
		`{"statement_id":%q,"status":{"state":%q},"manifest":{"format":"JSON_ARRAY","schema":{"column_count":1,"columns":[{"name":"session_user()","position":0,"type_name":"STRING","type_text":"STRING"}]},"total_chunk_count":1,"total_row_count":1,"truncated":false,"chunks":[{"chunk_index":0,"row_count":1,"row_offset":0}]},"result":{"chunk_index":0,"data_array":[[%q]],"row_count":1,"row_offset":0}}`,
		testQueryID,
		state,
		identity,
	)
}

func testEngine(sender *fakeSender) (*Engine, *fakeFactory, *fakeAuthenticator) {
	authenticator := &fakeAuthenticator{token: testToken}
	factory := &fakeFactory{authenticator: authenticator}
	return &Engine{auth: factory, sender: sender}, factory, authenticator
}

func TestHistoryListUsesSameCredentialForActorGuardThenOneProtectedRequest(t *testing.T) {
	remote := fmt.Sprintf(
		`{"has_next_page":true,"next_page_token":"next+token","res":[{"query_id":%q,"warehouse_id":%q,"query_text":"SELECT marker","status":"STARTED","duration":3}]}`,
		testQueryID,
		testWarehouse,
	)
	sender := &fakeSender{status: http.StatusOK, body: []byte(remote)}
	engine, factory, authenticator := testEngine(sender)
	payload := fmt.Sprintf(
		`{"warehouse_id":%q,"start_time_ms":1000,"end_time_ms":2000,"page_token":"a+b"}`,
		testWarehouse,
	)
	response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(historyRequest(payload)))
	if !response.OK || response.Code != CodeHistoryPage {
		t.Fatalf("unexpected response: %s", response)
	}
	if factory.calls != 1 || authenticator.calls != 1 || sender.calls != 2 {
		t.Fatalf("unexpected calls: factory=%d auth=%d send=%d", factory.calls, authenticator.calls, sender.calls)
	}
	if factory.profile != "operator" || factory.host != testHost {
		t.Fatal("factory did not receive the explicit profile and host")
	}
	guardRequest := sender.requests[0]
	if guardRequest.Method != http.MethodPost || guardRequest.URL.String() != testHost+"/api/2.0/sql/statements" {
		t.Fatal("protected history did not begin with the fixed actor statement")
	}
	request := sender.request
	if request.Method != http.MethodGet || request.Body != nil {
		t.Fatalf("unexpected method/body: %s", request.Method)
	}
	wantURL := testHost + "/api/2.0/sql/history/queries?" +
		"filter_by.query_start_time_range.end_time_ms=2000&" +
		"filter_by.query_start_time_range.start_time_ms=1000&" +
		"filter_by.warehouse_ids=0123456789abcdef&" +
		"include_metrics=false&max_results=1&page_token=a%2Bb"
	if request.URL.String() != wantURL {
		t.Fatalf("unexpected URL: %s", request.URL)
	}
	if request.Header.Get("Authorization") != "Bearer "+testToken ||
		guardRequest.Header.Get("Authorization") != request.Header.Get("Authorization") ||
		request.Header.Get("Accept") != "application/json" ||
		request.Header.Get("User-Agent") != "dbtobsb-native-bridge/1" {
		t.Fatal("unexpected fixed headers")
	}
	guardDeadline, guardHasDeadline := guardRequest.Context().Deadline()
	requestDeadline, requestHasDeadline := request.Context().Deadline()
	remaining := time.Until(requestDeadline)
	if !guardHasDeadline || !requestHasDeadline || !guardDeadline.Equal(requestDeadline) ||
		remaining < 104*time.Second || remaining > 105*time.Second {
		t.Fatalf("protected requests did not share one bounded invocation: %v %v", guardDeadline, requestDeadline)
	}
	page, ok := response.Result.(HistoryPage)
	if !ok || len(page.Records) != 1 || page.Records[0].Status != "STARTED" ||
		page.NextPageToken == nil || *page.NextPageToken != "next+token" {
		t.Fatalf("unexpected projection: %s", page)
	}
}

func TestProtectedActorMismatchBlocksHistoryWithoutASecondRequest(t *testing.T) {
	sender := &fakeSender{
		status:           http.StatusOK,
		body:             []byte(actorResponse("different.actor@example.com", "SUCCEEDED")),
		disableAutoActor: true,
	}
	engine, _, authenticator := testEngine(sender)
	response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(historyRequest("")))
	if response.OK || response.Code != CodeActorMismatch || response.Result != nil ||
		sender.calls != 1 || authenticator.calls != 1 {
		t.Fatalf("actor mismatch reached protected history: %s", response)
	}
}

func TestProtectedActorMismatchBlocksCancellationWithoutASecondRequest(t *testing.T) {
	sender := &fakeSender{
		status:           http.StatusOK,
		body:             []byte(actorResponse("different.actor@example.com", "SUCCEEDED")),
		disableAutoActor: true,
	}
	engine, factory, authenticator := testEngine(sender)
	response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(cancelRequest("")))
	if response.OK || response.Code != CodeActorMismatch || response.Result != nil ||
		sender.calls != 1 || factory.calls != 1 || authenticator.calls != 1 {
		t.Fatalf("actor mismatch reached protected cancellation: %s", response)
	}
	if sender.request.URL.String() != testHost+"/api/2.0/sql/statements" {
		t.Fatalf("unexpected request before cancellation block: %s", sender.request.URL)
	}
}

func TestProtectedPayloadRequiresActorAndWarehouseBeforeAuthentication(t *testing.T) {
	digest := sha256.Sum256([]byte(testActor))
	tests := map[string]string{
		"history missing actor": fmt.Sprintf(
			`{"warehouse_id":%q,"start_time_ms":1000,"end_time_ms":2000}`,
			testWarehouse,
		),
		"history missing warehouse": fmt.Sprintf(
			`{"expected_actor_sha256":"%x","start_time_ms":1000,"end_time_ms":2000}`,
			digest,
		),
		"cancel missing actor": fmt.Sprintf(
			`{"statement_id":%q,"warehouse_id":%q}`,
			testQueryID,
			testWarehouse,
		),
		"cancel missing warehouse": fmt.Sprintf(
			`{"statement_id":%q,"expected_actor_sha256":"%x"}`,
			testQueryID,
			digest,
		),
	}
	for name, payload := range tests {
		t.Run(name, func(t *testing.T) {
			operation := operationHistoryList
			if strings.HasPrefix(name, "cancel") {
				operation = operationCancel
			}
			input := fmt.Sprintf(
				`{"protocol":%q,"operation":%q,"profile":"operator","canonical_host":%q,"payload":%s}`,
				ProtocolVersion,
				operation,
				testHost,
				payload,
			)
			sender := &fakeSender{}
			engine, factory, authenticator := testEngine(sender)
			response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(input))
			if response.OK || response.Code != CodeRequestInvalid || sender.calls != 0 ||
				factory.calls != 0 || authenticator.calls != 0 {
				t.Fatalf("incomplete actor binding reached authentication/send: %s", response)
			}
		})
	}
}

func TestHistoryOneRecordEnvelopeBoundariesAndPagination(t *testing.T) {
	tests := []struct {
		name         string
		queryBytes   int
		requestToken *string
		nextToken    *string
	}{
		{name: "large first page", queryBytes: 260 * 1024, nextToken: stringPointer("page-2")},
		{name: "exact maximum final page", queryBytes: maxQueryTextBytes, requestToken: stringPointer("page-2")},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			queryText := strings.Repeat("x", test.queryBytes)
			hasNext := test.nextToken != nil
			nextField := ""
			if test.nextToken != nil {
				nextField = fmt.Sprintf(`,"next_page_token":%q`, *test.nextToken)
			}
			remote := fmt.Sprintf(
				`{"has_next_page":%t%s,"res":[{"query_id":%q,"warehouse_id":%q,"query_text":%q,"status":"FINISHED"}]}`,
				hasNext,
				nextField,
				testQueryID,
				testWarehouse,
				queryText,
			)
			if len(remote) > maxHistoryBodyBytes {
				t.Fatalf("valid boundary fixture exceeds remote cap: %d", len(remote))
			}
			payload := fmt.Sprintf(
				`{"warehouse_id":%q,"start_time_ms":1000,"end_time_ms":2000}`,
				testWarehouse,
			)
			if test.requestToken != nil {
				payload = fmt.Sprintf(
					`{"warehouse_id":%q,"start_time_ms":1000,"end_time_ms":2000,"page_token":%q}`,
					testWarehouse,
					*test.requestToken,
				)
			}
			sender := &fakeSender{status: http.StatusOK, body: []byte(remote)}
			engine, _, _ := testEngine(sender)
			response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(historyRequest(payload)))
			page, ok := response.Result.(HistoryPage)
			if !response.OK || response.Code != CodeHistoryPage || !ok || len(page.Records) != 1 ||
				len(page.Records[0].QueryText) != test.queryBytes || sender.calls != 2 {
				t.Fatalf("unexpected boundary page result: %s", response)
			}
			if test.nextToken == nil && page.NextPageToken != nil {
				t.Fatal("final page unexpectedly returned a token")
			}
			if test.nextToken != nil && (page.NextPageToken == nil || *page.NextPageToken != *test.nextToken) {
				t.Fatal("pagination token was not preserved")
			}
			if test.requestToken != nil && !strings.Contains(sender.request.URL.RawQuery, "page_token=page-2") {
				t.Fatalf("next request did not use the prior token: %s", sender.request.URL.RawQuery)
			}
			var output bytes.Buffer
			if err := EncodeResponse(&output, response); err != nil {
				t.Fatalf("valid boundary page exceeded stdout cap: %v", err)
			}
			if output.Len() > MaxOutputBytes {
				t.Fatalf("stdout cap exceeded: %d", output.Len())
			}
		})
	}

	// The parser allows any valid UTF-8 query text. Each decoded control byte
	// below occupies six bytes in JSON, proving the cap covers the maximum
	// escaping amplification at the exact decoded query-text limit.
	worstEscapedQuery := strings.Repeat(`\u0001`, maxQueryTextBytes)
	remote := fmt.Sprintf(
		`{"res":[{"query_id":%q,"warehouse_id":%q,"query_text":"%s","status":"FINISHED"}]}`,
		testQueryID,
		testWarehouse,
		worstEscapedQuery,
	)
	if len(remote) > maxHistoryBodyBytes || len(remote) < 3*maxQueryTextBytes {
		t.Fatalf("worst-escape fixture does not prove the intended envelope: %d", len(remote))
	}
	sender := &fakeSender{status: http.StatusOK, body: []byte(remote)}
	engine, _, _ := testEngine(sender)
	response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(historyRequest("")))
	page, ok := response.Result.(HistoryPage)
	if !response.OK || response.Code != CodeHistoryPage || !ok || len(page.Records) != 1 ||
		len(page.Records[0].QueryText) != maxQueryTextBytes || sender.calls != 2 {
		t.Fatalf("valid worst-escape boundary was rejected: %s", response)
	}
	var worstOutput bytes.Buffer
	if err := EncodeResponse(&worstOutput, response); err != nil || worstOutput.Len() > MaxOutputBytes {
		t.Fatalf("valid worst-escape output exceeded its cap: %d %v", worstOutput.Len(), err)
	}

	overMaximum := strings.Repeat("x", maxQueryTextBytes+1)
	remote = fmt.Sprintf(
		`{"res":[{"query_id":%q,"warehouse_id":%q,"query_text":%q,"status":"FINISHED"}]}`,
		testQueryID,
		testWarehouse,
		overMaximum,
	)
	sender = &fakeSender{status: http.StatusOK, body: []byte(remote)}
	engine, _, _ = testEngine(sender)
	response = engine.Execute(t.Context(), validEnvironment(), strings.NewReader(historyRequest("")))
	if response.OK || response.Code != CodeHistoryInvalid || sender.calls != 2 {
		t.Fatalf("over-maximum query text was accepted: %s", response)
	}

	twoRecords := fmt.Sprintf(
		`{"res":[{"query_id":%q,"warehouse_id":%q,"query_text":"one","status":"FINISHED"},{"query_id":%q,"warehouse_id":%q,"query_text":"two","status":"FINISHED"}]}`,
		testQueryID,
		testWarehouse,
		"123e4567-e89b-12d3-a456-426614174001",
		testWarehouse,
	)
	sender = &fakeSender{status: http.StatusOK, body: []byte(twoRecords)}
	engine, _, _ = testEngine(sender)
	response = engine.Execute(t.Context(), validEnvironment(), strings.NewReader(historyRequest("")))
	if response.OK || response.Code != CodeHistoryInvalid || sender.calls != 2 {
		t.Fatalf("two-record page was accepted: %s", response)
	}
}

func stringPointer(value string) *string { return &value }

func TestCancelConstructsOneExactAuthenticatedRequest(t *testing.T) {
	sender := &fakeSender{status: http.StatusOK, body: []byte("{}")}
	engine, _, authenticator := testEngine(sender)
	response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(cancelRequest("")))
	if !response.OK || response.Code != CodeCancelAccepted || sender.calls != 2 || authenticator.calls != 1 {
		t.Fatalf("unexpected response/calls: %s", response)
	}
	request := sender.request
	guardRequest := sender.requests[0]
	if request.Method != http.MethodPost ||
		request.URL.String() != testHost+"/api/2.0/sql/statements/"+testQueryID+"/cancel" ||
		request.Header.Get("Content-Type") != "application/json" {
		t.Fatal("unexpected cancel request")
	}
	if guardRequest.URL.String() != testHost+"/api/2.0/sql/statements" ||
		guardRequest.Header.Get("Authorization") != request.Header.Get("Authorization") {
		t.Fatal("cancel did not reuse the actor-guard credential")
	}
	body, err := io.ReadAll(request.Body)
	if err != nil || string(body) != "{}" {
		t.Fatalf("unexpected cancel body: %q", body)
	}
}

func TestActorIdentityCheckUsesOneExactFixedStatementAndReturnsOnlyMatch(t *testing.T) {
	identity := "approved.actor@example.com"
	sender := &fakeSender{status: http.StatusOK, body: []byte(actorResponse(identity, "SUCCEEDED")), disableAutoActor: true}
	engine, factory, authenticator := testEngine(sender)
	response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(actorRequest(identity)))
	result, ok := response.Result.(ActorCheckResult)
	if !response.OK || response.Code != CodeActorMatched || !ok || !result.Matched ||
		factory.calls != 1 || authenticator.calls != 1 || sender.calls != 1 {
		t.Fatalf("unexpected actor response: %s", response)
	}
	request := sender.request
	if request.Method != http.MethodPost || request.URL.String() != testHost+"/api/2.0/sql/statements" ||
		request.Header.Get("Content-Type") != "application/json" {
		t.Fatal("unexpected actor-check request")
	}
	body, err := io.ReadAll(request.Body)
	if err != nil {
		t.Fatal(err)
	}
	wantBody := `{"disposition":"INLINE","format":"JSON_ARRAY","on_wait_timeout":"CANCEL","statement":"SELECT session_user()","wait_timeout":"50s","warehouse_id":"0123456789abcdef"}`
	if string(body) != wantBody {
		t.Fatalf("actor statement drifted: %s", body)
	}
	deadline, present := request.Context().Deadline()
	remaining := time.Until(deadline)
	if !present || remaining < 69*time.Second || remaining > 70*time.Second {
		t.Fatalf("unexpected actor-check deadline: %v %v", present, remaining)
	}
	var output bytes.Buffer
	if err := EncodeResponse(&output, response); err != nil {
		t.Fatal(err)
	}
	if strings.Contains(output.String(), identity) || strings.Contains(output.String(), testQueryID) ||
		strings.Contains(output.String(), "session_user") || strings.Contains(output.String(), testToken) {
		t.Fatalf("actor identity, statement, ID, or token escaped: %s", output.String())
	}
}

func TestActorIdentityMismatchIsTypedAndRedacted(t *testing.T) {
	sender := &fakeSender{status: http.StatusOK, body: []byte(actorResponse("different.actor@example.com", "SUCCEEDED")), disableAutoActor: true}
	engine, _, _ := testEngine(sender)
	response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(actorRequest("approved.actor@example.com")))
	if response.OK || response.Code != CodeActorMismatch || response.Result != nil || sender.calls != 1 {
		t.Fatalf("unexpected mismatch result: %s", response)
	}
}

func TestActorFingerprintObserveUsesOneExactFixedStatementAndReturnsOnlyDigest(t *testing.T) {
	identity := "confirmed.actor@example.com"
	digest := sha256.Sum256([]byte(identity))
	wantDigest := fmt.Sprintf("%x", digest)
	sender := &fakeSender{status: http.StatusOK, body: []byte(actorResponse(identity, "SUCCEEDED")), disableAutoActor: true}
	engine, factory, authenticator := testEngine(sender)
	response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(actorObserveRequest("")))
	result, ok := response.Result.(ActorFingerprintResult)
	if !response.OK || response.Code != CodeActorFingerprintObserved || !ok ||
		result.ActorSHA256 != wantDigest || !sha256Pattern.MatchString(result.ActorSHA256) ||
		factory.calls != 1 || authenticator.calls != 1 || sender.calls != 1 {
		t.Fatalf("unexpected actor observation response: %s", response)
	}
	request := sender.request
	if request.Method != http.MethodPost || request.URL.String() != testHost+"/api/2.0/sql/statements" ||
		request.Header.Get("Content-Type") != "application/json" {
		t.Fatal("unexpected actor-observation request")
	}
	body, err := io.ReadAll(request.Body)
	if err != nil {
		t.Fatal(err)
	}
	wantBody := `{"disposition":"INLINE","format":"JSON_ARRAY","on_wait_timeout":"CANCEL","statement":"SELECT session_user()","wait_timeout":"50s","warehouse_id":"0123456789abcdef"}`
	if string(body) != wantBody {
		t.Fatalf("actor observation statement drifted: %s", body)
	}
	resultJSON, err := json.Marshal(result)
	if err != nil || string(resultJSON) != fmt.Sprintf(`{"actor_sha256":%q}`, wantDigest) {
		t.Fatalf("observation result exposed more than the fingerprint: %s %v", resultJSON, err)
	}
	var output bytes.Buffer
	if err := EncodeResponse(&output, response); err != nil {
		t.Fatal(err)
	}
	if strings.Count(output.String(), wantDigest) != 1 || strings.Contains(output.String(), identity) ||
		strings.Contains(output.String(), testQueryID) || strings.Contains(output.String(), "session_user") ||
		strings.Contains(output.String(), testToken) || strings.Contains(fmt.Sprint(result), wantDigest) {
		t.Fatalf("actor observation was not redacted to one fingerprint: %s", output.String())
	}
}

func TestActorCheckAdversarialResponsesFailClosed(t *testing.T) {
	identity := "approved.actor@example.com"
	valid := actorResponse(identity, "SUCCEEDED")
	tests := map[string]struct {
		body   string
		status int
		code   string
	}{
		"running":                {body: actorResponse(identity, "RUNNING"), status: 200, code: CodeActorIndeterminate},
		"pending":                {body: actorResponse(identity, "PENDING"), status: 200, code: CodeActorIndeterminate},
		"failed":                 {body: strings.Replace(actorResponse(identity, "FAILED"), `"state":"FAILED"`, `"state":"FAILED","sql_state":"XX000","error":{"error_code":"redacted","message":"redacted"}`, 1), status: 200, code: CodeActorIndeterminate},
		"canceled":               {body: actorResponse(identity, "CANCELED"), status: 200, code: CodeActorIndeterminate},
		"closed no result":       {body: actorResponse(identity, "CLOSED"), status: 200, code: CodeActorIndeterminate},
		"remote failure":         {body: `{"error_code":"redacted"}`, status: 500, code: CodeActorIndeterminate},
		"duplicate key":          {body: strings.Replace(valid, `"state":"SUCCEEDED"`, `"state":"SUCCEEDED","state":"FAILED"`, 1), status: 200, code: CodeActorResponseInvalid},
		"unknown top field":      {body: strings.TrimSuffix(valid, "}") + `,"identity":"leak"}`, status: 200, code: CodeActorResponseInvalid},
		"uppercase statement id": {body: strings.Replace(valid, testQueryID, strings.ToUpper(testQueryID), 1), status: 200, code: CodeActorResponseInvalid},
		"external link":          {body: strings.Replace(valid, `"data_array":[["`+identity+`"]]`, `"external_links":[{"external_link":"https://invalid"}]`, 1), status: 200, code: CodeActorIndeterminate},
		"external format":        {body: strings.Replace(valid, `"format":"JSON_ARRAY"`, `"format":"EXTERNAL_LINKS"`, 1), status: 200, code: CodeActorIndeterminate},
		"truncated":              {body: strings.Replace(valid, `"truncated":false`, `"truncated":true`, 1), status: 200, code: CodeActorResponseInvalid},
		"two rows":               {body: strings.Replace(valid, `[["`+identity+`"]]`, `[["`+identity+`"],["second@example.com"]]`, 1), status: 200, code: CodeActorResponseInvalid},
		"two values":             {body: strings.Replace(valid, `[["`+identity+`"]]`, `[["`+identity+`","second@example.com"]]`, 1), status: 200, code: CodeActorResponseInvalid},
		"null identity":          {body: strings.Replace(valid, `[["`+identity+`"]]`, `[[null]]`, 1), status: 200, code: CodeActorResponseInvalid},
		"wrong type":             {body: strings.Replace(valid, `"type_name":"STRING"`, `"type_name":"INT"`, 1), status: 200, code: CodeActorResponseInvalid},
		"next chunk":             {body: strings.Replace(valid, `"row_offset":0}}`, `"row_offset":0,"next_chunk_index":1}}`, 1), status: 200, code: CodeActorResponseInvalid},
	}
	inputs := map[string]string{
		"authorization check": actorRequest(identity),
		"enrollment observe":  actorObserveRequest(""),
	}
	for name, test := range tests {
		for mode, input := range inputs {
			t.Run(name+"/"+mode, func(t *testing.T) {
				sender := &fakeSender{status: test.status, body: []byte(test.body), disableAutoActor: true}
				engine, _, _ := testEngine(sender)
				response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(input))
				if response.OK || response.Code != test.code || sender.calls != 1 || response.Result != nil {
					t.Fatalf("unexpected adversarial actor result: %s", response)
				}
			})
		}
	}
}

func TestActorCheckTimeoutIsIndeterminateAndNeverRetried(t *testing.T) {
	for name, input := range map[string]string{
		"authorization check": actorRequest("approved.actor@example.com"),
		"enrollment observe":  actorObserveRequest(""),
	} {
		t.Run(name, func(t *testing.T) {
			sender := &fakeSender{err: context.DeadlineExceeded, disableAutoActor: true}
			engine, _, _ := testEngine(sender)
			response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(input))
			if response.OK || response.Code != CodeActorIndeterminate || sender.calls != 1 {
				t.Fatalf("unexpected actor timeout result: %s", response)
			}
		})
	}
}

func TestActorCheckRejectsNoncanonicalFingerprintBeforeAuthOrSend(t *testing.T) {
	digest := sha256.Sum256([]byte("approved.actor@example.com"))
	payload := fmt.Sprintf(
		`{"warehouse_id":%q,"expected_actor_sha256":"%s"}`,
		testWarehouse,
		strings.ToUpper(fmt.Sprintf("%x", digest)),
	)
	input := fmt.Sprintf(
		`{"protocol":%q,"operation":"actor_identity_check","profile":"operator","canonical_host":%q,"payload":%s}`,
		ProtocolVersion,
		testHost,
		payload,
	)
	sender := &fakeSender{}
	engine, factory, authenticator := testEngine(sender)
	response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(input))
	if response.OK || response.Code != CodeRequestInvalid || sender.calls != 0 ||
		factory.calls != 0 || authenticator.calls != 0 {
		t.Fatalf("noncanonical fingerprint reached auth/send: %s", response)
	}
}

func TestTokenNeverAppearsInProtocolOutputOrSafeRepresentations(t *testing.T) {
	remote := fmt.Sprintf(
		`{"res":[{"query_id":%q,"warehouse_id":%q,"query_text":"SELECT marker","status":"FINISHED"}]}`,
		testQueryID,
		testWarehouse,
	)
	sender := &fakeSender{status: http.StatusOK, body: []byte(remote)}
	engine, _, _ := testEngine(sender)
	response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(historyRequest("")))
	var output bytes.Buffer
	if err := EncodeResponse(&output, response); err != nil {
		t.Fatal(err)
	}
	if strings.Contains(output.String(), testToken) {
		t.Fatalf("token escaped protocol output: %s", output.String())
	}
	safeRepresentations := response.String() + fmt.Sprint(response.Result)
	if strings.Contains(safeRepresentations, testToken) || strings.Contains(safeRepresentations, "SELECT marker") ||
		strings.Contains(safeRepresentations, testQueryID) {
		t.Fatalf("secret or sensitive value escaped safe representation: %s", safeRepresentations)
	}
	if !strings.Contains(output.String(), "SELECT marker") {
		t.Fatal("typed history result must remain available to the installer parent")
	}
}

func TestHostileProtocolInputsFailBeforeAuthenticationOrSend(t *testing.T) {
	tests := map[string]string{
		"duplicate outer key":  strings.Replace(historyRequest(""), `"profile":"operator"`, `"profile":"operator","profile":"evil"`, 1),
		"duplicate nested key": historyRequest(fmt.Sprintf(`{"warehouse_id":%q,"warehouse_id":%q,"start_time_ms":1,"end_time_ms":2}`, testWarehouse, testWarehouse)),
		"unknown outer field":  strings.TrimSuffix(historyRequest(""), "}") + `,"method":"DELETE"}`,
		"unknown nested field": historyRequest(fmt.Sprintf(`{"warehouse_id":%q,"start_time_ms":1,"end_time_ms":2,"sql":"DROP TABLE x"}`, testWarehouse)),
		"observe extra field":  actorObserveRequest(fmt.Sprintf(`{"warehouse_id":%q,"expected_actor_sha256":"%064d"}`, testWarehouse, 0)),
		"multiple documents":   historyRequest("") + historyRequest(""),
		"unknown operation":    strings.Replace(historyRequest(""), "query_history_list", "generic_request", 1),
		"default profile":      strings.Replace(historyRequest(""), `"profile":"operator"`, `"profile":"DEFAULT"`, 1),
		"host with path":       strings.Replace(historyRequest(""), testHost, testHost+"/login", 1),
		"host with query":      strings.Replace(historyRequest(""), testHost, testHost+"?o=1", 1),
		"noncanonical id":      cancelRequest(`{"statement_id":"123E4567-E89B-12D3-A456-426614174000"}`),
		"oversized window":     historyRequest(fmt.Sprintf(`{"warehouse_id":%q,"start_time_ms":0,"end_time_ms":1200001}`, testWarehouse)),
		"float timestamp":      historyRequest(fmt.Sprintf(`{"warehouse_id":%q,"start_time_ms":1.0,"end_time_ms":2}`, testWarehouse)),
	}
	for name, input := range tests {
		t.Run(name, func(t *testing.T) {
			sender := &fakeSender{status: http.StatusOK, body: []byte(`{"res":[]}`)}
			engine, factory, authenticator := testEngine(sender)
			response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(input))
			if response.OK || sender.calls != 0 || factory.calls != 0 || authenticator.calls != 0 {
				t.Fatalf("hostile input was not rejected before auth/send: %s", response)
			}
		})
	}
}

func TestOversizedInputIsBounded(t *testing.T) {
	sender := &fakeSender{}
	engine, factory, _ := testEngine(sender)
	response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(strings.Repeat("x", MaxInputBytes+1)))
	if response.OK || response.Code != CodeInputTooLarge || factory.calls != 0 || sender.calls != 0 {
		t.Fatalf("unexpected oversized-input handling: %s", response)
	}
}

func TestPositiveEnvironmentContractRejectsHostileOrImplicitState(t *testing.T) {
	tests := map[string][]string{
		"missing secure mode": {"HOME=/tmp/operator"},
		"plaintext mode":      {"HOME=/tmp/operator", "DATABRICKS_AUTH_STORAGE=plaintext"},
		"profile steering":    {"HOME=/tmp/operator", "DATABRICKS_AUTH_STORAGE=secure", "DATABRICKS_CONFIG_PROFILE=evil"},
		"pat":                 {"HOME=/tmp/operator", "DATABRICKS_AUTH_STORAGE=secure", "DATABRICKS_TOKEN=secret"},
		"azure cli":           {"HOME=/tmp/operator", "DATABRICKS_AUTH_STORAGE=secure", "ARM_CLIENT_ID=id"},
		"proxy":               {"HOME=/tmp/operator", "DATABRICKS_AUTH_STORAGE=secure", "HTTPS_PROXY=http://evil"},
		"path":                {"HOME=/tmp/operator", "DATABRICKS_AUTH_STORAGE=secure", "PATH=/tmp/evil"},
		"relative home":       {"HOME=relative", "DATABRICKS_AUTH_STORAGE=secure"},
		"duplicate":           {"HOME=/tmp/operator", "HOME=/tmp/other", "DATABRICKS_AUTH_STORAGE=secure"},
	}
	for name, environment := range tests {
		t.Run(name, func(t *testing.T) {
			sender := &fakeSender{}
			engine, factory, _ := testEngine(sender)
			response := engine.Execute(t.Context(), environment, strings.NewReader(historyRequest("")))
			if response.OK || response.Code != CodeEnvironmentInvalid || factory.calls != 0 || sender.calls != 0 {
				t.Fatalf("unexpected environment result: %s", response)
			}
		})
	}
}

func TestAuthenticationFailureNeverSends(t *testing.T) {
	sender := &fakeSender{}
	engine, factory, authenticator := testEngine(sender)
	authenticator.err = errors.New("contains " + testToken)
	response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(historyRequest("")))
	if response.OK || response.Code != CodeAuthUnavailable || sender.calls != 0 || factory.calls != 1 {
		t.Fatalf("unexpected auth failure handling: %s", response)
	}
	var output bytes.Buffer
	if err := EncodeResponse(&output, response); err != nil || strings.Contains(output.String(), testToken) {
		t.Fatal("auth error detail escaped")
	}
}

func TestMissingOrMalformedAuthorizationNeverSends(t *testing.T) {
	for _, token := range []string{"", "bad token", strings.Repeat("x", 16_500)} {
		sender := &fakeSender{}
		engine, _, authenticator := testEngine(sender)
		authenticator.token = token
		response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(historyRequest("")))
		if response.OK || response.Code != CodeAuthUnavailable || sender.calls != 0 {
			t.Fatalf("unexpected authorization handling: %s", response)
		}
	}
}

func TestRedirectTimeoutAndOversizeFailAfterExactlyOneSend(t *testing.T) {
	tests := []struct {
		name   string
		sender *fakeSender
		code   string
	}{
		{name: "redirect response", sender: &fakeSender{status: http.StatusTemporaryRedirect, body: []byte("redirect")}, code: CodeRedirectRejected},
		{name: "redirect error", sender: &fakeSender{err: errRedirectRejected}, code: CodeRedirectRejected},
		{name: "transport timeout", sender: &fakeSender{err: context.DeadlineExceeded}, code: CodeHistoryUnavailable},
		{name: "oversized response", sender: &fakeSender{status: http.StatusOK, body: bytes.Repeat([]byte("x"), maxHistoryBodyBytes+1)}, code: CodeResponseTooLarge},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			engine, _, authenticator := testEngine(test.sender)
			response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(historyRequest("")))
			if response.OK || response.Code != test.code || test.sender.calls != 2 || authenticator.calls != 1 {
				t.Fatalf("unexpected response: %s", response)
			}
		})
	}
}

func TestCallerCancellationBoundsHungSend(t *testing.T) {
	sender := &fakeSender{wait: true}
	engine, _, _ := testEngine(sender)
	ctx, cancel := context.WithTimeout(t.Context(), 10*time.Millisecond)
	defer cancel()
	response := engine.Execute(ctx, validEnvironment(), strings.NewReader(historyRequest("")))
	if response.OK || response.Code != CodeHistoryUnavailable || sender.calls != 2 {
		t.Fatalf("unexpected timeout result: %s", response)
	}
}

func TestCancelTransportFailureIsIndeterminateAndNeverRetried(t *testing.T) {
	sender := &fakeSender{err: context.DeadlineExceeded}
	engine, _, _ := testEngine(sender)
	response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(cancelRequest("")))
	if response.OK || response.Code != CodeCancelIndeterminate || sender.calls != 2 {
		t.Fatalf("unexpected cancel result: %s", response)
	}
}

func TestCancelRejectedStatusesRemainNonterminalTypedResults(t *testing.T) {
	for _, status := range []int{400, 401, 403, 404} {
		sender := &fakeSender{status: status, body: []byte(`{"error_code":"redacted"}`)}
		engine, _, _ := testEngine(sender)
		response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(cancelRequest("")))
		result, ok := response.Result.(CancelResult)
		if !response.OK || response.Code != CodeCancelRejected || !ok || result.Accepted || sender.calls != 2 {
			t.Fatalf("unexpected status %d result: %s", status, response)
		}
	}
}

func TestHostileHistoryResponsesFailClosed(t *testing.T) {
	validRecord := fmt.Sprintf(
		`{"query_id":%q,"warehouse_id":%q,"query_text":"marker","status":"FINISHED"}`,
		testQueryID,
		testWarehouse,
	)
	tests := map[string]string{
		"duplicate key":           `{"res":[],"res":[]}`,
		"unknown top level":       `{"res":[],"future":true}`,
		"missing records":         `{}`,
		"null records":            `{"res":null}`,
		"invalid status":          strings.Replace(`{"res":[`+validRecord+`]}`, "FINISHED", "UNKNOWN", 1),
		"wrong warehouse":         strings.Replace(`{"res":[`+validRecord+`]}`, testWarehouse, "ffffffffffffffff", 1),
		"uppercase id":            strings.Replace(`{"res":[`+validRecord+`]}`, testQueryID, strings.ToUpper(testQueryID), 1),
		"empty query text":        strings.Replace(`{"res":[`+validRecord+`]}`, "marker", "", 1),
		"next without flag":       `{"next_page_token":"next","res":[]}`,
		"next flag without token": `{"has_next_page":true,"res":[]}`,
		"null next flag":          `{"has_next_page":null,"res":[]}`,
	}
	for name, body := range tests {
		t.Run(name, func(t *testing.T) {
			sender := &fakeSender{status: http.StatusOK, body: []byte(body)}
			engine, _, _ := testEngine(sender)
			response := engine.Execute(t.Context(), validEnvironment(), strings.NewReader(historyRequest("")))
			if response.OK || response.Code != CodeHistoryInvalid || sender.calls != 2 {
				t.Fatalf("unexpected hostile response handling: %s", response)
			}
		})
	}
}

func TestProductionConfigPinsProfileLoadersAndNativeCLICredentials(t *testing.T) {
	cfg := newUnresolvedSDKConfig("operator")
	if cfg.Profile != "operator" || cfg.Credentials.Name() != requiredAuthType {
		t.Fatal("profile or credential strategy was not pinned")
	}
	if _, ok := cfg.Credentials.(cliauth.CLICredentials); !ok {
		t.Fatal("credential strategy is not CLI CLICredentials")
	}
	wantLoaders := []string{"environment (excluding auth)", "config-file", "environment (auth gap-fill)"}
	if len(cfg.Loaders) != len(wantLoaders) {
		t.Fatalf("unexpected loader count: %d", len(cfg.Loaders))
	}
	for index, loader := range cfg.Loaders {
		if loader.Name() != wantLoaders[index] {
			t.Fatalf("unexpected loader %d: %s", index, loader.Name())
		}
	}
	metadata, err := cfg.HostMetadataResolver(t.Context(), testHost)
	if err != nil || metadata != nil {
		t.Fatal("host metadata resolver must suppress discovery I/O")
	}
}

func TestProductionTransportIsHTTP11OnlyAndDoesNotReplay(t *testing.T) {
	engine := New()
	client, ok := engine.sender.(*http.Client)
	if !ok {
		t.Fatal("production sender is not the fixed HTTP client")
	}
	transport, ok := client.Transport.(*http.Transport)
	if !ok {
		t.Fatal("production client does not use the fixed HTTP transport")
	}
	if transport.ForceAttemptHTTP2 || !transport.DisableKeepAlives || transport.Protocols == nil ||
		!transport.Protocols.HTTP1() || transport.Protocols.HTTP2() || transport.Protocols.UnencryptedHTTP2() {
		t.Fatalf("production protocol set is not HTTP/1-only: %+v", transport.Protocols)
	}
	if transport.TLSNextProto == nil || len(transport.TLSNextProto) != 0 ||
		transport.TLSClientConfig == nil || len(transport.TLSClientConfig.NextProtos) != 1 ||
		transport.TLSClientConfig.NextProtos[0] != "http/1.1" {
		t.Fatal("production TLS transport can negotiate an alternate protocol")
	}

	t.Run("TLS ALPN refuses HTTP/2", func(t *testing.T) {
		var calls atomic.Int32
		protocol := make(chan string, 1)
		server := httptest.NewUnstartedServer(http.HandlerFunc(func(writer http.ResponseWriter, request *http.Request) {
			calls.Add(1)
			protocol <- request.Proto
			writer.Header().Set("Content-Type", "application/json")
			_, _ = writer.Write([]byte(`{}`))
		}))
		server.EnableHTTP2 = true
		server.StartTLS()
		defer server.Close()

		testClient := productionClientForTLSServer(t, client, transport, server)
		request, err := (actorObserveOperation{payload: actorObservePayload{WarehouseID: testWarehouse}}).buildRequest(server.URL)
		if err != nil || request.GetBody != nil {
			t.Fatalf("fixed POST exposes a replay body: %v", err)
		}
		response, err := testClient.Do(request)
		if err != nil {
			t.Fatal(err)
		}
		_, _ = io.Copy(io.Discard, response.Body)
		_ = response.Body.Close()
		if got := <-protocol; got != "HTTP/1.1" || calls.Load() != 1 {
			t.Fatalf("unexpected negotiated protocol or sends: protocol=%s calls=%d", got, calls.Load())
		}
	})

	for _, fixture := range []struct {
		name  string
		build func(string) (*http.Request, error)
	}{
		{
			name: "GET failure",
			build: func(host string) (*http.Request, error) {
				return (historyOperation{payload: historyPayload{
					WarehouseID: testWarehouse,
					StartTimeMS: 1000,
					EndTimeMS:   2000,
				}}).buildRequest(host)
			},
		},
		{
			name: "POST failure",
			build: func(host string) (*http.Request, error) {
				return (actorObserveOperation{payload: actorObservePayload{WarehouseID: testWarehouse}}).buildRequest(host)
			},
		},
	} {
		t.Run(fixture.name+" is one wire send", func(t *testing.T) {
			var calls atomic.Int32
			server := httptest.NewUnstartedServer(http.HandlerFunc(func(writer http.ResponseWriter, _ *http.Request) {
				calls.Add(1)
				connection, _, err := writer.(http.Hijacker).Hijack()
				if err == nil {
					_ = connection.Close()
				}
			}))
			server.EnableHTTP2 = true
			server.StartTLS()
			defer server.Close()

			testClient := productionClientForTLSServer(t, client, transport, server)
			request, err := fixture.build(server.URL)
			if err != nil || request.GetBody != nil {
				t.Fatalf("request exposes an internal replay body: %v", err)
			}
			response, err := testClient.Do(request)
			if response != nil && response.Body != nil {
				_ = response.Body.Close()
			}
			if err == nil || calls.Load() != 1 {
				t.Fatalf("ambiguous protocol failure was replayed: err=%v calls=%d", err, calls.Load())
			}
		})
	}
}

func productionClientForTLSServer(
	t *testing.T,
	client *http.Client,
	transport *http.Transport,
	server *httptest.Server,
) *http.Client {
	t.Helper()
	clone := transport.Clone()
	clone.TLSClientConfig = transport.TLSClientConfig.Clone()
	roots := x509.NewCertPool()
	roots.AddCert(server.Certificate())
	clone.TLSClientConfig.RootCAs = roots
	t.Cleanup(clone.CloseIdleConnections)
	return &http.Client{
		Transport:     clone,
		Timeout:       client.Timeout,
		CheckRedirect: client.CheckRedirect,
	}
}

func TestSDKFactoryLoadsExplicitProfileAndChecksHostAndAuthTypeWithoutTokenRead(t *testing.T) {
	home := t.TempDir()
	profile := "operator"
	configText := fmt.Sprintf("[%s]\nhost = %s\nauth_type = databricks-cli\n", profile, testHost)
	if err := os.WriteFile(filepath.Join(home, ".databrickscfg"), []byte(configText), 0o600); err != nil {
		t.Fatal(err)
	}
	t.Setenv("HOME", home)
	t.Setenv("DATABRICKS_AUTH_STORAGE", "secure")
	factory := sdkAuthenticatorFactory{}
	authenticator, err := factory.Resolve(t.Context(), profile, testHost)
	if err != nil || authenticator == nil {
		t.Fatalf("valid profile failed to resolve: %v", err)
	}
	if _, err := factory.Resolve(t.Context(), profile, "https://adb-1.1.azuredatabricks.net"); errorCode(err) != CodeHostMismatch {
		t.Fatalf("host mismatch did not fail closed: %v", err)
	}
	configText = fmt.Sprintf("[%s]\nhost = %s\nauth_type = azure-cli\n", profile, testHost)
	if err := os.WriteFile(filepath.Join(home, ".databrickscfg"), []byte(configText), 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := factory.Resolve(t.Context(), profile, testHost); errorCode(err) != CodeAuthTypeInvalid {
		t.Fatalf("auth type mismatch did not fail closed: %v", err)
	}
	for name, extra := range map[string]string{
		"alternative credential": "metadata_service_url = https://metadata.invalid\n",
		"workspace routing":      "workspace_id = 12345\n",
		"unsafe debug":           "debug_headers = true\n",
		"custom scope":           "scopes = all-apis\n",
	} {
		t.Run(name, func(t *testing.T) {
			configText := fmt.Sprintf(
				"[%s]\nhost = %s\nauth_type = databricks-cli\n%s",
				profile,
				testHost,
				extra,
			)
			if err := os.WriteFile(filepath.Join(home, ".databrickscfg"), []byte(configText), 0o600); err != nil {
				t.Fatal(err)
			}
			if _, err := factory.Resolve(t.Context(), profile, testHost); errorCode(err) != CodeAuthTypeInvalid {
				t.Fatalf("unexpected profile field did not fail closed: %v", err)
			}
		})
	}
}

func TestEncodeResponseIsOneBoundedJSONLine(t *testing.T) {
	response := Response{Protocol: ProtocolVersion, OK: false, Code: CodeProtocolInvalid}
	var output bytes.Buffer
	if err := EncodeResponse(&output, response); err != nil {
		t.Fatal(err)
	}
	if bytes.Count(output.Bytes(), []byte("\n")) != 1 || !bytes.HasSuffix(output.Bytes(), []byte("\n")) {
		t.Fatalf("response is not exactly one JSON line: %q", output.Bytes())
	}
	oversized := Response{Protocol: ProtocolVersion, OK: true, Code: CodeHistoryPage, Result: strings.Repeat("x", MaxOutputBytes)}
	if err := EncodeResponse(io.Discard, oversized); errorCode(err) != CodeResponseTooLarge {
		t.Fatalf("oversized output did not fail: %v", err)
	}
}
