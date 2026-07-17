package bridge

import (
	"bytes"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/json"
	"fmt"
	"net/http"
	"net/url"
	"regexp"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/databricks/databricks-sdk-go/service/sql"
	"github.com/google/uuid"
)

const (
	operationHistoryList  = "query_history_list"
	operationCancel       = "statement_execution_cancel"
	operationSubmit       = "statement_execution_submit"
	operationActorCheck   = "actor_identity_check"
	operationActorObserve = "actor_fingerprint_observe"
	maxHistoryResults     = 1
	maxHistoryWindowMS    = 20 * 60 * 1000
	// A 512 KiB decoded query may require six JSON bytes per input byte when
	// every byte is represented as a Unicode escape. Four MiB leaves a bounded
	// envelope for that 3 MiB value plus the single-record response structure.
	maxHistoryBodyBytes = 4 * 1024 * 1024
	maxCancelBodyBytes  = 128
	maxQueryTextBytes   = 512 * 1024
	maxPageTokenBytes   = 4096
	maxActorBodyBytes   = 64 * 1024
	maxActorValueBytes  = 4096
)

var (
	profilePattern   = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$`)
	azureHostPattern = regexp.MustCompile(`^https://adb-[0-9]{1,20}\.[0-9]{1,20}\.azuredatabricks\.net$`)
	warehousePattern = regexp.MustCompile(`^[0-9a-f]{16}$`)
	sha256Pattern    = regexp.MustCompile(`^[0-9a-f]{64}$`)
)

type fixedOperation interface {
	buildRequest(contextHost string) (*http.Request, error)
	parseResponse(status int, body []byte) (any, string, error)
	maxResponseBytes() int64
	indeterminateCode() string
	timeout() time.Duration
}

type actorProtectedOperation interface {
	fixedOperation
	actorGuard() actorCheckOperation
}

type historyPayload struct {
	WarehouseID         string  `json:"warehouse_id"`
	ExpectedActorSHA256 string  `json:"expected_actor_sha256"`
	StartTimeMS         int64   `json:"start_time_ms"`
	EndTimeMS           int64   `json:"end_time_ms"`
	PageToken           *string `json:"page_token,omitempty"`
}

type cancelPayload struct {
	StatementID         string `json:"statement_id"`
	WarehouseID         string `json:"warehouse_id"`
	ExpectedActorSHA256 string `json:"expected_actor_sha256"`
}

type actorCheckPayload struct {
	WarehouseID         string `json:"warehouse_id"`
	ExpectedActorSHA256 string `json:"expected_actor_sha256"`
}

type actorObservePayload struct {
	WarehouseID string `json:"warehouse_id"`
}

type historyOperation struct{ payload historyPayload }
type cancelOperation struct{ payload cancelPayload }
type actorCheckOperation struct{ payload actorCheckPayload }
type actorObserveOperation struct{ payload actorObservePayload }

type HistoryRecord struct {
	QueryReference string          `json:"query_reference"`
	WarehouseID    string          `json:"warehouse_id"`
	QueryText      string          `json:"query_text"`
	Status         sql.QueryStatus `json:"status"`
}

func (r HistoryRecord) String() string {
	return fmt.Sprintf("HistoryRecord(status=%s, <redacted>)", r.Status)
}

type HistoryPage struct {
	Kind          string          `json:"kind"`
	Records       []HistoryRecord `json:"records"`
	NextPageToken *string         `json:"next_page_token"`
}

func (p HistoryPage) String() string {
	return fmt.Sprintf("HistoryPage(record_count=%d, <redacted>)", len(p.Records))
}

type CancelResult struct {
	Kind     string `json:"kind"`
	Accepted bool   `json:"accepted"`
}

type ActorCheckResult struct {
	Kind    string `json:"kind"`
	Matched bool   `json:"matched"`
}

func (r ActorCheckResult) String() string {
	return fmt.Sprintf("ActorCheckResult(matched=%t, <redacted>)", r.Matched)
}

// ActorFingerprintResult contains the sole enrollment observation value. Its
// safe representation deliberately omits even the pseudonymous fingerprint.
type ActorFingerprintResult struct {
	ActorSHA256 string `json:"actor_sha256"`
}

func (ActorFingerprintResult) String() string {
	return "ActorFingerprintResult(<redacted>)"
}

func parseOperation(request requestEnvelope) (fixedOperation, error) {
	if !profilePattern.MatchString(request.Profile) || strings.EqualFold(request.Profile, "DEFAULT") {
		return nil, fail(CodeProfileInvalid)
	}
	if !azureHostPattern.MatchString(request.CanonicalHost) {
		return nil, fail(CodeHostInvalid)
	}
	switch request.Operation {
	case operationHistoryList:
		var payload historyPayload
		if err := strictUnmarshal(request.Payload, &payload); err != nil {
			return nil, fail(CodeRequestInvalid)
		}
		if !warehousePattern.MatchString(payload.WarehouseID) ||
			!sha256Pattern.MatchString(payload.ExpectedActorSHA256) ||
			payload.StartTimeMS < 0 || payload.EndTimeMS <= payload.StartTimeMS ||
			payload.EndTimeMS-payload.StartTimeMS > maxHistoryWindowMS ||
			(payload.PageToken != nil && !validPageToken(*payload.PageToken)) {
			return nil, fail(CodeRequestInvalid)
		}
		return historyOperation{payload: payload}, nil
	case operationCancel:
		var payload cancelPayload
		if err := strictUnmarshal(request.Payload, &payload); err != nil ||
			!canonicalUUID(payload.StatementID) ||
			!warehousePattern.MatchString(payload.WarehouseID) ||
			!sha256Pattern.MatchString(payload.ExpectedActorSHA256) {
			return nil, fail(CodeRequestInvalid)
		}
		return cancelOperation{payload: payload}, nil
	case operationSubmit:
		var payload submitPayload
		if err := strictUnmarshal(request.Payload, &payload); err != nil ||
			!warehousePattern.MatchString(payload.WarehouseID) ||
			!sha256Pattern.MatchString(payload.ExpectedActorSHA256) ||
			!sha256Pattern.MatchString(payload.SemanticSHA256) ||
			payload.RegistryVersion != registryVersion {
			return nil, fail(CodeRequestInvalid)
		}
		statement, err := renderRegisteredStatement(payload)
		if err != nil {
			return nil, err
		}
		return submitOperation{payload: payload, statement: statement}, nil
	case operationActorCheck:
		var payload actorCheckPayload
		if err := strictUnmarshal(request.Payload, &payload); err != nil ||
			!warehousePattern.MatchString(payload.WarehouseID) ||
			!sha256Pattern.MatchString(payload.ExpectedActorSHA256) {
			return nil, fail(CodeRequestInvalid)
		}
		return actorCheckOperation{payload: payload}, nil
	case operationActorObserve:
		var payload actorObservePayload
		if err := strictUnmarshal(request.Payload, &payload); err != nil ||
			!warehousePattern.MatchString(payload.WarehouseID) {
			return nil, fail(CodeRequestInvalid)
		}
		return actorObserveOperation{payload: payload}, nil
	default:
		return nil, fail(CodeOperationDenied)
	}
}

func (o historyOperation) buildRequest(host string) (*http.Request, error) {
	query := url.Values{}
	query.Set("filter_by.query_start_time_range.end_time_ms", strconv.FormatInt(o.payload.EndTimeMS, 10))
	query.Set("filter_by.query_start_time_range.start_time_ms", strconv.FormatInt(o.payload.StartTimeMS, 10))
	query.Set("filter_by.warehouse_ids", o.payload.WarehouseID)
	query.Set("include_metrics", "false")
	query.Set("max_results", strconv.Itoa(maxHistoryResults))
	if o.payload.PageToken != nil {
		query.Set("page_token", *o.payload.PageToken)
	}
	request, err := http.NewRequest(http.MethodGet, host+"/api/2.0/sql/history/queries?"+query.Encode(), nil)
	if err != nil {
		return nil, fail(CodeRequestInvalid)
	}
	// Do not expose a replayable body to net/http. The operation is sent once
	// and any ambiguous write/read failure is indeterminate.
	request.GetBody = nil
	request.Header.Set("Accept", "application/json")
	request.Header.Set("User-Agent", "dbtobsb-native-bridge/1")
	return request, nil
}

func (o historyOperation) parseResponse(status int, body []byte) (any, string, error) {
	if status != http.StatusOK {
		return nil, "", fail(CodeHistoryUnavailable)
	}
	page, err := parseHistoryResponse(body, o.payload.WarehouseID)
	if err != nil {
		return nil, "", err
	}
	return page, CodeHistoryPage, nil
}

func (historyOperation) maxResponseBytes() int64   { return maxHistoryBodyBytes }
func (historyOperation) indeterminateCode() string { return CodeHistoryUnavailable }
func (historyOperation) timeout() time.Duration    { return 105 * time.Second }

func (o historyOperation) actorGuard() actorCheckOperation {
	return actorCheckOperation{payload: actorCheckPayload{
		WarehouseID:         o.payload.WarehouseID,
		ExpectedActorSHA256: o.payload.ExpectedActorSHA256,
	}}
}

func (o cancelOperation) buildRequest(host string) (*http.Request, error) {
	request, err := http.NewRequest(
		http.MethodPost,
		host+"/api/2.0/sql/statements/"+o.payload.StatementID+"/cancel",
		bytes.NewReader([]byte("{}")),
	)
	if err != nil {
		return nil, fail(CodeRequestInvalid)
	}
	// Do not expose a replayable body to net/http. The operation is sent once
	// and any ambiguous write/read failure is indeterminate.
	request.GetBody = nil
	request.Header.Set("Accept", "application/json")
	request.Header.Set("Content-Type", "application/json")
	request.Header.Set("User-Agent", "dbtobsb-native-bridge/1")
	return request, nil
}

func (cancelOperation) parseResponse(status int, body []byte) (any, string, error) {
	switch status {
	case http.StatusOK:
		if len(body) != 0 && !bytes.Equal(body, []byte("{}")) {
			var document map[string]json.RawMessage
			if err := strictUnmarshal(body, &document); err != nil || len(document) != 0 {
				return nil, "", fail(CodeCancelResponseInvalid)
			}
		}
		return CancelResult{Kind: "statement_execution_cancel", Accepted: true}, CodeCancelAccepted, nil
	case http.StatusBadRequest, http.StatusUnauthorized, http.StatusForbidden, http.StatusNotFound:
		return CancelResult{Kind: "statement_execution_cancel", Accepted: false}, CodeCancelRejected, nil
	default:
		return nil, "", fail(CodeCancelIndeterminate)
	}
}

func (cancelOperation) maxResponseBytes() int64   { return maxCancelBodyBytes }
func (cancelOperation) indeterminateCode() string { return CodeCancelIndeterminate }
func (cancelOperation) timeout() time.Duration    { return 105 * time.Second }

func (o cancelOperation) actorGuard() actorCheckOperation {
	return actorCheckOperation{payload: actorCheckPayload{
		WarehouseID:         o.payload.WarehouseID,
		ExpectedActorSHA256: o.payload.ExpectedActorSHA256,
	}}
}

func (o actorCheckOperation) buildRequest(host string) (*http.Request, error) {
	return buildActorRequest(host, o.payload.WarehouseID)
}

func (o actorObserveOperation) buildRequest(host string) (*http.Request, error) {
	return buildActorRequest(host, o.payload.WarehouseID)
}

func buildActorRequest(host, warehouseID string) (*http.Request, error) {
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
		Statement:     "SELECT session_user()",
		WaitTimeout:   "50s",
		WarehouseID:   warehouseID,
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
	// Do not expose a replayable body to net/http. The operation is sent once
	// and any ambiguous write/read failure is indeterminate.
	request.GetBody = nil
	request.Header.Set("Accept", "application/json")
	request.Header.Set("Content-Type", "application/json")
	request.Header.Set("User-Agent", "dbtobsb-native-bridge/1")
	return request, nil
}

func (o actorCheckOperation) parseResponse(status int, body []byte) (any, string, error) {
	if status != http.StatusOK {
		return nil, "", fail(CodeActorIndeterminate)
	}
	identity, err := parseActorResponse(body)
	if err != nil {
		return nil, "", err
	}
	expected, err := decodeLowerHex(o.payload.ExpectedActorSHA256)
	if err != nil {
		return nil, "", fail(CodeInternalFailure)
	}
	actual := sha256.Sum256([]byte(identity))
	matched := subtle.ConstantTimeCompare(actual[:], expected) == 1
	code := CodeActorMismatch
	if matched {
		code = CodeActorMatched
	}
	return ActorCheckResult{Kind: "actor_identity_check", Matched: matched}, code, nil
}

func (actorCheckOperation) maxResponseBytes() int64   { return maxActorBodyBytes }
func (actorCheckOperation) indeterminateCode() string { return CodeActorIndeterminate }
func (actorCheckOperation) timeout() time.Duration    { return 70 * time.Second }

func (actorObserveOperation) maxResponseBytes() int64   { return maxActorBodyBytes }
func (actorObserveOperation) indeterminateCode() string { return CodeActorIndeterminate }
func (actorObserveOperation) timeout() time.Duration    { return 70 * time.Second }

func (actorObserveOperation) parseResponse(status int, body []byte) (any, string, error) {
	if status != http.StatusOK {
		return nil, "", fail(CodeActorIndeterminate)
	}
	identity, err := parseActorResponse(body)
	if err != nil {
		return nil, "", err
	}
	digest := sha256.Sum256([]byte(identity))
	return ActorFingerprintResult{ActorSHA256: fmt.Sprintf("%x", digest)}, CodeActorFingerprintObserved, nil
}

func decodeLowerHex(value string) ([]byte, error) {
	if !sha256Pattern.MatchString(value) {
		return nil, fail(CodeRequestInvalid)
	}
	decoded := make([]byte, sha256.Size)
	for index := range decoded {
		high := hexNibble(value[index*2])
		low := hexNibble(value[index*2+1])
		if high < 0 || low < 0 {
			return nil, fail(CodeRequestInvalid)
		}
		decoded[index] = byte(high<<4 | low)
	}
	return decoded, nil
}

func hexNibble(value byte) int {
	switch {
	case value >= '0' && value <= '9':
		return int(value - '0')
	case value >= 'a' && value <= 'f':
		return int(value-'a') + 10
	default:
		return -1
	}
}

func canonicalUUID(value string) bool {
	parsed, err := uuid.Parse(value)
	return err == nil && parsed.String() == value
}

func validPageToken(value string) bool {
	if value == "" || len(value) > maxPageTokenBytes || !utf8.ValidString(value) {
		return false
	}
	for _, character := range value {
		if character < 33 {
			return false
		}
	}
	return true
}

type rawHistoryPage struct {
	HasNextPage   *bool              `json:"has_next_page,omitempty"`
	NextPageToken *string            `json:"next_page_token,omitempty"`
	Records       []rawHistoryRecord `json:"res"`
}

type rawHistoryRecord struct {
	QueryID     string          `json:"query_id"`
	QueryText   string          `json:"query_text"`
	Status      sql.QueryStatus `json:"status"`
	WarehouseID string          `json:"warehouse_id"`
}

func parseHistoryResponse(body []byte, expectedWarehouse string) (HistoryPage, error) {
	var top map[string]json.RawMessage
	if err := strictUnmarshal(body, &top); err != nil {
		return HistoryPage{}, fail(CodeHistoryInvalid)
	}
	for key := range top {
		if key != "has_next_page" && key != "next_page_token" && key != "res" {
			return HistoryPage{}, fail(CodeHistoryInvalid)
		}
	}
	if _, present := top["res"]; !present {
		return HistoryPage{}, fail(CodeHistoryInvalid)
	}
	recordsJSON := bytes.TrimSpace(top["res"])
	if len(recordsJSON) == 0 || recordsJSON[0] != '[' {
		return HistoryPage{}, fail(CodeHistoryInvalid)
	}
	if _, present := top["has_next_page"]; present {
		hasNextJSON := bytes.TrimSpace(top["has_next_page"])
		if bytes.Equal(hasNextJSON, []byte("null")) {
			return HistoryPage{}, fail(CodeHistoryInvalid)
		}
	}
	var raw rawHistoryPage
	// Records have additional GA response fields. Decode the frozen projection
	// only after the top-level allowlist and global duplicate-key check.
	if err := json.Unmarshal(body, &raw); err != nil || len(raw.Records) > maxHistoryResults {
		return HistoryPage{}, fail(CodeHistoryInvalid)
	}
	hasNext := raw.HasNextPage != nil && *raw.HasNextPage
	if raw.HasNextPage == nil {
		hasNext = false
	}
	if hasNext {
		if raw.NextPageToken == nil || !validPageToken(*raw.NextPageToken) {
			return HistoryPage{}, fail(CodeHistoryInvalid)
		}
	} else if raw.NextPageToken != nil {
		return HistoryPage{}, fail(CodeHistoryInvalid)
	}
	records := make([]HistoryRecord, 0, len(raw.Records))
	for _, record := range raw.Records {
		if !canonicalUUID(record.QueryID) || record.WarehouseID != expectedWarehouse ||
			record.QueryText == "" || len(record.QueryText) > maxQueryTextBytes ||
			!validQueryStatus(record.Status) {
			return HistoryPage{}, fail(CodeHistoryInvalid)
		}
		records = append(records, HistoryRecord{
			QueryReference: record.QueryID,
			WarehouseID:    record.WarehouseID,
			QueryText:      record.QueryText,
			Status:         record.Status,
		})
	}
	return HistoryPage{
		Kind:          "query_history_page",
		Records:       records,
		NextPageToken: raw.NextPageToken,
	}, nil
}

func validQueryStatus(status sql.QueryStatus) bool {
	switch status {
	case sql.QueryStatusCanceled, sql.QueryStatusCompiled, sql.QueryStatusCompiling,
		sql.QueryStatusFailed, sql.QueryStatusFinished, sql.QueryStatusQueued,
		sql.QueryStatusRunning, sql.QueryStatusStarted:
		return true
	default:
		return false
	}
}

func parseActorResponse(body []byte) (string, error) {
	top, err := strictActorObject(
		body,
		[]string{"manifest", "result", "statement_id", "status"},
		[]string{"manifest", "result", "statement_id", "status"},
	)
	if err != nil {
		return "", err
	}
	var statementID string
	if strictUnmarshal(top["statement_id"], &statementID) != nil || !canonicalUUID(statementID) {
		return "", fail(CodeActorResponseInvalid)
	}
	status, err := strictActorObject(
		top["status"],
		[]string{"error", "sql_state", "state"},
		[]string{"state"},
	)
	if err != nil {
		return "", err
	}
	var state string
	if strictUnmarshal(status["state"], &state) != nil {
		return "", fail(CodeActorResponseInvalid)
	}
	if state != string(sql.StatementStateSucceeded) {
		return "", fail(CodeActorIndeterminate)
	}
	if len(status) != 1 {
		return "", fail(CodeActorResponseInvalid)
	}
	if err := validateActorManifest(top["manifest"]); err != nil {
		return "", err
	}
	identity, err := validateActorResult(top["result"])
	if err != nil {
		return "", err
	}
	return identity, nil
}

func validateActorManifest(raw json.RawMessage) error {
	manifest, err := strictActorObject(
		raw,
		[]string{"chunks", "format", "schema", "total_chunk_count", "total_row_count", "truncated"},
		[]string{"format", "schema", "total_chunk_count", "total_row_count"},
	)
	if err != nil {
		return err
	}
	var format string
	var chunkCount int
	var rowCount int64
	if strictUnmarshal(manifest["format"], &format) != nil {
		return fail(CodeActorResponseInvalid)
	}
	if format == string(sql.DispositionExternalLinks) {
		return fail(CodeActorIndeterminate)
	}
	if format != string(sql.FormatJsonArray) ||
		strictUnmarshal(manifest["total_chunk_count"], &chunkCount) != nil || chunkCount != 1 ||
		strictUnmarshal(manifest["total_row_count"], &rowCount) != nil || rowCount != 1 {
		return fail(CodeActorResponseInvalid)
	}
	if truncatedRaw, present := manifest["truncated"]; present {
		var truncated bool
		if strictUnmarshal(truncatedRaw, &truncated) != nil || truncated {
			return fail(CodeActorResponseInvalid)
		}
	}
	if chunksRaw, present := manifest["chunks"]; present {
		var chunks []json.RawMessage
		if strictUnmarshal(chunksRaw, &chunks) != nil || len(chunks) != 1 ||
			validateActorChunk(chunks[0]) != nil {
			return fail(CodeActorResponseInvalid)
		}
	}
	return validateActorSchema(manifest["schema"])
}

func validateActorSchema(raw json.RawMessage) error {
	schema, err := strictActorObject(raw, []string{"column_count", "columns"}, []string{"column_count", "columns"})
	if err != nil {
		return err
	}
	var columnCount int
	var columns []json.RawMessage
	if strictUnmarshal(schema["column_count"], &columnCount) != nil || columnCount != 1 ||
		strictUnmarshal(schema["columns"], &columns) != nil || len(columns) != 1 {
		return fail(CodeActorResponseInvalid)
	}
	column, err := strictActorObject(
		columns[0],
		[]string{"name", "position", "type_interval_type", "type_name", "type_precision", "type_scale", "type_text"},
		[]string{"position", "type_name"},
	)
	if err != nil {
		return err
	}
	var position int
	var typeName string
	if strictUnmarshal(column["position"], &position) != nil || position != 0 ||
		strictUnmarshal(column["type_name"], &typeName) != nil || typeName != string(sql.ColumnInfoTypeNameString) {
		return fail(CodeActorResponseInvalid)
	}
	return nil
}

func validateActorChunk(raw json.RawMessage) error {
	chunk, err := strictActorObject(
		raw,
		[]string{"chunk_index", "row_count", "row_offset"},
		[]string{"chunk_index", "row_count", "row_offset"},
	)
	if err != nil {
		return err
	}
	var index int
	var rowCount int64
	var rowOffset int64
	if strictUnmarshal(chunk["chunk_index"], &index) != nil || index != 0 ||
		strictUnmarshal(chunk["row_count"], &rowCount) != nil || rowCount != 1 ||
		strictUnmarshal(chunk["row_offset"], &rowOffset) != nil || rowOffset != 0 {
		return fail(CodeActorResponseInvalid)
	}
	return nil
}

func validateActorResult(raw json.RawMessage) (string, error) {
	var untrusted map[string]json.RawMessage
	if strictUnmarshal(raw, &untrusted) != nil || untrusted == nil {
		return "", fail(CodeActorResponseInvalid)
	}
	if _, external := untrusted["external_links"]; external {
		return "", fail(CodeActorIndeterminate)
	}
	result, err := strictActorObject(
		raw,
		[]string{"chunk_index", "data_array", "row_count", "row_offset"},
		[]string{"chunk_index", "data_array", "row_count", "row_offset"},
	)
	if err != nil {
		return "", err
	}
	var index int
	var rowCount int64
	var rowOffset int64
	var rows [][]json.RawMessage
	if strictUnmarshal(result["chunk_index"], &index) != nil || index != 0 ||
		strictUnmarshal(result["row_count"], &rowCount) != nil || rowCount != 1 ||
		strictUnmarshal(result["row_offset"], &rowOffset) != nil || rowOffset != 0 ||
		strictUnmarshal(result["data_array"], &rows) != nil || len(rows) != 1 || len(rows[0]) != 1 {
		return "", fail(CodeActorResponseInvalid)
	}
	identityRaw := bytes.TrimSpace(rows[0][0])
	if len(identityRaw) < 2 || identityRaw[0] != '"' {
		return "", fail(CodeActorResponseInvalid)
	}
	var identity string
	if strictUnmarshal(identityRaw, &identity) != nil || identity == "" || len(identity) > maxActorValueBytes {
		return "", fail(CodeActorResponseInvalid)
	}
	for _, character := range identity {
		if character < 33 || character == 127 {
			return "", fail(CodeActorResponseInvalid)
		}
	}
	return identity, nil
}

func strictActorObject(raw json.RawMessage, allowed, required []string) (map[string]json.RawMessage, error) {
	var object map[string]json.RawMessage
	if strictUnmarshal(raw, &object) != nil || object == nil {
		return nil, fail(CodeActorResponseInvalid)
	}
	allowedSet := make(map[string]struct{}, len(allowed))
	for _, key := range allowed {
		allowedSet[key] = struct{}{}
	}
	for key := range object {
		if _, accepted := allowedSet[key]; !accepted {
			return nil, fail(CodeActorResponseInvalid)
		}
	}
	for _, key := range required {
		if _, present := object[key]; !present {
			return nil, fail(CodeActorResponseInvalid)
		}
	}
	return object, nil
}
