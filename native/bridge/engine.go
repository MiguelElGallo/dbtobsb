package bridge

import (
	"context"
	"crypto/tls"
	"errors"
	"io"
	"net"
	"net/http"
	"strings"
	"time"
)

const maxInvocationTimeout = 75 * time.Second

var errRedirectRejected = errors.New("redirect rejected")

type requestSender interface {
	Do(*http.Request) (*http.Response, error)
}

// Engine has only two injectable seams: credential attachment and a one-send
// HTTP client. Production construction is fixed and not configurable by stdin.
type Engine struct {
	auth   authenticatorFactory
	sender requestSender
}

func New() *Engine {
	dialer := &net.Dialer{Timeout: 5 * time.Second, KeepAlive: -1}
	protocols := new(http.Protocols)
	protocols.SetHTTP1(true)
	transport := &http.Transport{
		Proxy:             nil,
		DialContext:       dialer.DialContext,
		ForceAttemptHTTP2: false,
		DisableKeepAlives: true,
		Protocols:         protocols,
		TLSClientConfig: &tls.Config{
			MinVersion: tls.VersionTLS12,
			NextProtos: []string{"http/1.1"},
		},
		// An explicit empty map disables automatic alternate-protocol
		// registration as defense in depth alongside Protocols and ALPN.
		TLSNextProto:          map[string]func(string, *tls.Conn) http.RoundTripper{},
		TLSHandshakeTimeout:   5 * time.Second,
		ResponseHeaderTimeout: 65 * time.Second,
		ExpectContinueTimeout: time.Second,
	}
	client := &http.Client{
		Transport: transport,
		Timeout:   maxInvocationTimeout,
		CheckRedirect: func(*http.Request, []*http.Request) error {
			return errRedirectRejected
		},
	}
	return &Engine{auth: sdkAuthenticatorFactory{}, sender: client}
}

// Execute consumes exactly one protocol document. Enrollment operations issue
// one workspace request. Protected history and cancellation operations first
// issue the fixed actor statement, then issue the protected request only after
// a match, using the same resolved credential value and HTTP client. Neither
// request is retried. A CLICredentials OAuth refresh may perform its distinct
// token-endpoint exchange before the fixed actor request.
func (e *Engine) Execute(ctx context.Context, environ []string, reader io.Reader) Response {
	if e == nil || e.auth == nil || e.sender == nil {
		return failureResponse(fail(CodeInternalFailure))
	}
	if err := validateEnvironment(environ); err != nil {
		return failureResponse(err)
	}
	requestEnvelope, err := decodeRequest(reader)
	if err != nil {
		return failureResponse(err)
	}
	operation, err := parseOperation(requestEnvelope)
	if err != nil {
		return failureResponse(err)
	}
	bounded, cancel := context.WithTimeout(ctx, operation.timeout())
	defer cancel()
	authenticator, err := e.auth.Resolve(
		bounded,
		requestEnvelope.Profile,
		requestEnvelope.CanonicalHost,
	)
	if err != nil {
		return failureResponse(err)
	}
	if protected, ok := operation.(actorProtectedOperation); ok {
		return e.executeProtected(
			bounded,
			authenticator,
			requestEnvelope.CanonicalHost,
			protected,
		)
	}
	request, err := operation.buildRequest(requestEnvelope.CanonicalHost)
	if err != nil {
		return failureResponse(err)
	}
	request = request.WithContext(bounded)
	if err := authenticator.Authenticate(request); err != nil {
		return failureResponse(fail(CodeAuthUnavailable))
	}
	authorization := request.Header.Values("Authorization")
	if !validAuthorization(authorization) {
		return failureResponse(fail(CodeAuthUnavailable))
	}
	return e.executeRequest(operation, request)
}

func (e *Engine) executeProtected(
	ctx context.Context,
	authenticator requestAuthenticator,
	host string,
	operation actorProtectedOperation,
) Response {
	guard := operation.actorGuard()
	guardRequest, err := guard.buildRequest(host)
	if err != nil {
		return failureResponse(err)
	}
	guardRequest = guardRequest.WithContext(ctx)
	if err := authenticator.Authenticate(guardRequest); err != nil {
		return failureResponse(fail(CodeAuthUnavailable))
	}
	authorization := guardRequest.Header.Values("Authorization")
	if !validAuthorization(authorization) {
		return failureResponse(fail(CodeAuthUnavailable))
	}
	guardResponse := e.executeRequest(guard, guardRequest)
	if !guardResponse.OK {
		return guardResponse
	}
	result, ok := guardResponse.Result.(ActorCheckResult)
	if !ok || guardResponse.Code != CodeActorMatched || !result.Matched {
		return failureResponse(fail(CodeActorMismatch))
	}
	request, err := operation.buildRequest(host)
	if err != nil {
		return failureResponse(err)
	}
	request = request.WithContext(ctx)
	request.Header["Authorization"] = append([]string(nil), authorization...)
	if !validAuthorization(request.Header.Values("Authorization")) {
		return failureResponse(fail(CodeInternalFailure))
	}
	return e.executeRequest(operation, request)
}

func (e *Engine) executeRequest(operation fixedOperation, request *http.Request) Response {
	response, err := e.sender.Do(request)
	if err != nil {
		if response != nil && response.Body != nil {
			_ = response.Body.Close()
		}
		if errors.Is(err, errRedirectRejected) {
			return failureResponse(fail(CodeRedirectRejected))
		}
		return failureResponse(fail(operation.indeterminateCode()))
	}
	if response == nil || response.Body == nil {
		return failureResponse(fail(operation.indeterminateCode()))
	}
	defer response.Body.Close()
	if response.StatusCode >= 300 && response.StatusCode < 400 {
		return failureResponse(fail(CodeRedirectRejected))
	}
	body, err := io.ReadAll(io.LimitReader(response.Body, operation.maxResponseBytes()+1))
	if err != nil {
		return failureResponse(fail(operation.indeterminateCode()))
	}
	if int64(len(body)) > operation.maxResponseBytes() {
		return failureResponse(fail(CodeResponseTooLarge))
	}
	result, code, err := operation.parseResponse(response.StatusCode, body)
	if err != nil {
		return failureResponse(err)
	}
	if code == CodeActorMismatch {
		return failureResponse(fail(CodeActorMismatch))
	}
	return Response{Protocol: ProtocolVersion, OK: true, Code: code, Result: result}
}

func validAuthorization(values []string) bool {
	if len(values) != 1 || len(values[0]) > 16_391 || !strings.HasPrefix(values[0], "Bearer ") {
		return false
	}
	token := strings.TrimPrefix(values[0], "Bearer ")
	if token == "" || strings.TrimSpace(token) != token {
		return false
	}
	for _, character := range token {
		if character < 33 || character == 127 {
			return false
		}
	}
	return true
}
