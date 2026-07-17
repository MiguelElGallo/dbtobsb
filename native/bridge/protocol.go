// Package bridge implements the bounded, fixed-operation protocol used by the
// regulated dbtobsb installer. The credential boundary includes this helper
// and its OS-keyring adapter child; credentials and Authorization headers never
// cross into the installer parent or protocol output.
package bridge

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"unicode/utf8"
)

const (
	ProtocolVersion = "dbtobsb.native-bridge.v1"
	MaxInputBytes   = 64 * 1024
	// Query History accepts at most one record from a 4 MiB remote page.
	// Projection adds less than 16 KiB of fixed keys plus the bounded token,
	// while disabling HTML-only escapes prevents stdout amplification.
	MaxOutputBytes = maxHistoryBodyBytes + 16*1024
)

const (
	CodeHistoryPage               = "DBTOBSB_NATIVE_HISTORY_PAGE"
	CodeActorMatched              = "DBTOBSB_NATIVE_ACTOR_MATCHED"
	CodeActorMismatch             = "DBTOBSB_NATIVE_ACTOR_MISMATCH"
	CodeActorFingerprintObserved  = "DBTOBSB_NATIVE_ACTOR_FINGERPRINT_OBSERVED"
	CodeActorIndeterminate        = "DBTOBSB_NATIVE_ACTOR_INDETERMINATE"
	CodeActorResponseInvalid      = "DBTOBSB_NATIVE_ACTOR_RESPONSE_INVALID"
	CodeCancelAccepted            = "DBTOBSB_NATIVE_CANCEL_ACCEPTED"
	CodeCancelRejected            = "DBTOBSB_NATIVE_CANCEL_REJECTED"
	CodeStatementReceipt          = "DBTOBSB_NATIVE_STATEMENT_RECEIPT"
	CodeStatementIndeterminate    = "DBTOBSB_NATIVE_STATEMENT_INDETERMINATE"
	CodeStatementResponseInvalid  = "DBTOBSB_NATIVE_STATEMENT_RESPONSE_INVALID"
	CodeRegistryOperationDenied   = "DBTOBSB_NATIVE_REGISTRY_OPERATION_DENIED"
	CodeRegistryParametersInvalid = "DBTOBSB_NATIVE_REGISTRY_PARAMETERS_INVALID"
	CodeRegistryDigestMismatch    = "DBTOBSB_NATIVE_REGISTRY_DIGEST_MISMATCH"
	CodeProtocolInvalid           = "DBTOBSB_NATIVE_PROTOCOL_INVALID"
	CodeInputTooLarge             = "DBTOBSB_NATIVE_INPUT_TOO_LARGE"
	CodeEnvironmentInvalid        = "DBTOBSB_NATIVE_ENVIRONMENT_INVALID"
	CodeProfileInvalid            = "DBTOBSB_NATIVE_PROFILE_INVALID"
	CodeProfileUnavailable        = "DBTOBSB_NATIVE_PROFILE_UNAVAILABLE"
	CodeHostInvalid               = "DBTOBSB_NATIVE_HOST_INVALID"
	CodeHostMismatch              = "DBTOBSB_NATIVE_HOST_MISMATCH"
	CodeAuthTypeInvalid           = "DBTOBSB_NATIVE_AUTH_TYPE_INVALID"
	CodeAuthUnavailable           = "DBTOBSB_NATIVE_AUTH_UNAVAILABLE"
	CodeOperationDenied           = "DBTOBSB_NATIVE_OPERATION_DENIED"
	CodeRequestInvalid            = "DBTOBSB_NATIVE_REQUEST_INVALID"
	CodeRedirectRejected          = "DBTOBSB_NATIVE_REDIRECT_REJECTED"
	CodeHistoryUnavailable        = "DBTOBSB_NATIVE_HISTORY_UNAVAILABLE"
	CodeHistoryInvalid            = "DBTOBSB_NATIVE_HISTORY_RESPONSE_INVALID"
	CodeCancelIndeterminate       = "DBTOBSB_NATIVE_CANCEL_INDETERMINATE"
	CodeCancelResponseInvalid     = "DBTOBSB_NATIVE_CANCEL_RESPONSE_INVALID"
	CodeResponseTooLarge          = "DBTOBSB_NATIVE_RESPONSE_TOO_LARGE"
	CodeInternalFailure           = "DBTOBSB_NATIVE_INTERNAL_FAILURE"
)

type bridgeError struct {
	code string
}

func (e *bridgeError) Error() string { return e.code }

func fail(code string) error { return &bridgeError{code: code} }

func errorCode(err error) string {
	var target *bridgeError
	if errors.As(err, &target) {
		return target.code
	}
	return CodeInternalFailure
}

type requestEnvelope struct {
	Protocol      string          `json:"protocol"`
	Operation     string          `json:"operation"`
	Profile       string          `json:"profile"`
	CanonicalHost string          `json:"canonical_host"`
	Payload       json.RawMessage `json:"payload"`
}

// Response is the only stdout shape. Error responses contain a stable code and
// no remote error text, profile, host, identifier, SQL, or credential material.
type Response struct {
	Protocol string `json:"protocol"`
	OK       bool   `json:"ok"`
	Code     string `json:"code"`
	Result   any    `json:"result,omitempty"`
}

func (r Response) String() string {
	return fmt.Sprintf("Response(ok=%t, code=%s, <redacted>)", r.OK, r.Code)
}

func failureResponse(err error) Response {
	return Response{Protocol: ProtocolVersion, OK: false, Code: errorCode(err)}
}

func decodeRequest(reader io.Reader) (requestEnvelope, error) {
	if reader == nil {
		return requestEnvelope{}, fail(CodeProtocolInvalid)
	}
	raw, err := io.ReadAll(io.LimitReader(reader, MaxInputBytes+1))
	if err != nil {
		return requestEnvelope{}, fail(CodeProtocolInvalid)
	}
	if len(raw) > MaxInputBytes {
		return requestEnvelope{}, fail(CodeInputTooLarge)
	}
	if len(raw) == 0 || !utf8.Valid(raw) {
		return requestEnvelope{}, fail(CodeProtocolInvalid)
	}
	var request requestEnvelope
	if err := strictUnmarshal(raw, &request); err != nil {
		return requestEnvelope{}, fail(CodeProtocolInvalid)
	}
	if request.Protocol != ProtocolVersion {
		return requestEnvelope{}, fail(CodeProtocolInvalid)
	}
	if len(request.Payload) == 0 || bytes.Equal(request.Payload, []byte("null")) {
		return requestEnvelope{}, fail(CodeRequestInvalid)
	}
	return request, nil
}

func strictUnmarshal(raw []byte, destination any) error {
	if !utf8.Valid(raw) {
		return errors.New("invalid utf-8")
	}
	if err := rejectDuplicateKeys(raw); err != nil {
		return err
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(destination); err != nil {
		return err
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		return errors.New("trailing json")
	}
	return nil
}

func rejectDuplicateKeys(raw []byte) error {
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	var walk func() error
	walk = func() error {
		token, err := decoder.Token()
		if err != nil {
			return err
		}
		delimiter, ok := token.(json.Delim)
		if !ok {
			return nil
		}
		switch delimiter {
		case '{':
			seen := make(map[string]struct{})
			for decoder.More() {
				keyToken, err := decoder.Token()
				if err != nil {
					return err
				}
				key, ok := keyToken.(string)
				if !ok {
					return errors.New("non-string object key")
				}
				if _, exists := seen[key]; exists {
					return errors.New("duplicate object key")
				}
				seen[key] = struct{}{}
				if err := walk(); err != nil {
					return err
				}
			}
			end, err := decoder.Token()
			if err != nil || end != json.Delim('}') {
				return errors.New("invalid object")
			}
		case '[':
			for decoder.More() {
				if err := walk(); err != nil {
					return err
				}
			}
			end, err := decoder.Token()
			if err != nil || end != json.Delim(']') {
				return errors.New("invalid array")
			}
		default:
			return errors.New("unexpected delimiter")
		}
		return nil
	}
	if err := walk(); err != nil {
		return err
	}
	if _, err := decoder.Token(); !errors.Is(err, io.EOF) {
		return errors.New("trailing json")
	}
	return nil
}

// EncodeResponse emits one deterministic JSON line and enforces the stdout cap.
func EncodeResponse(writer io.Writer, response Response) error {
	var buffer bytes.Buffer
	encoder := json.NewEncoder(&buffer)
	encoder.SetEscapeHTML(false)
	if err := encoder.Encode(response); err != nil {
		return fail(CodeInternalFailure)
	}
	if buffer.Len() > MaxOutputBytes {
		return fail(CodeResponseTooLarge)
	}
	_, err := writer.Write(buffer.Bytes())
	return err
}
