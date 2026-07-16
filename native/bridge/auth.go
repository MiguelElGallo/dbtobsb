package bridge

import (
	"context"
	"net/http"
	"reflect"

	cliauth "github.com/databricks/cli/libs/auth"
	"github.com/databricks/cli/libs/databrickscfg"
	"github.com/databricks/databricks-sdk-go/config"
)

const requiredAuthType = "databricks-cli"

type requestAuthenticator interface {
	Authenticate(*http.Request) error
}

type authenticatorFactory interface {
	Resolve(context.Context, string, string) (requestAuthenticator, error)
}

type sdkAuthenticatorFactory struct{}

// newUnresolvedSDKConfig freezes the exact CLI-native auth strategy. The
// metadata resolver deliberately returns no metadata so configuration loading
// cannot add an unauthenticated discovery request before the one fixed
// workspace operation.
func newUnresolvedSDKConfig(profile string) *config.Config {
	return &config.Config{
		Profile:     profile,
		Credentials: cliauth.CLICredentials{},
		Loaders:     databrickscfg.ProfileAuthLoaders,
		HostMetadataResolver: func(context.Context, string) (*config.HostMetadata, error) {
			return nil, nil
		},
		HTTPTimeoutSeconds:  10,
		RetryTimeoutSeconds: 0,
	}
}

func (sdkAuthenticatorFactory) Resolve(_ context.Context, profile, expectedHost string) (requestAuthenticator, error) {
	cfg := newUnresolvedSDKConfig(profile)
	if err := cfg.EnsureResolved(); err != nil {
		return nil, fail(CodeProfileUnavailable)
	}
	if cfg.Profile != profile {
		return nil, fail(CodeProfileInvalid)
	}
	if cfg.CanonicalHostName() != expectedHost {
		return nil, fail(CodeHostMismatch)
	}
	if cfg.AuthType != requiredAuthType || cfg.Credentials.Name() != requiredAuthType {
		return nil, fail(CodeAuthTypeInvalid)
	}
	if reflect.TypeOf(cfg.Credentials) != reflect.TypeOf(cliauth.CLICredentials{}) {
		return nil, fail(CodeAuthTypeInvalid)
	}
	// A selected U2M profile has a positive configuration shape: only the
	// explicit profile, canonical host, exact auth type, and our fixed refresh
	// timeout may be populated. This rejects every alternative current or future
	// SDK auth attribute, routing override, custom scope, insecure/debug option,
	// executable path, and config-file steering without maintaining a secret
	// field blacklist.
	allowedAttributes := map[string]struct{}{
		"auth_type":            {},
		"host":                 {},
		"http_timeout_seconds": {},
		"profile":              {},
	}
	for index := range config.ConfigAttributes {
		attribute := &config.ConfigAttributes[index]
		if attribute.IsZero(cfg) {
			continue
		}
		if _, allowed := allowedAttributes[attribute.Name]; !allowed {
			return nil, fail(CodeAuthTypeInvalid)
		}
	}
	if cfg.HTTPTimeoutSeconds != 10 {
		return nil, fail(CodeAuthTypeInvalid)
	}
	return cfg, nil
}
