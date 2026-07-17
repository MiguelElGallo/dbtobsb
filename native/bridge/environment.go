package bridge

import (
	"path/filepath"
	"strings"
)

var allowedEnvironmentNames = map[string]struct{}{
	"APPDATA":                  {},
	"DBUS_SESSION_BUS_ADDRESS": {},
	"DATABRICKS_AUTH_STORAGE":  {},
	"HOME":                     {},
	"LANG":                     {},
	"LC_ALL":                   {},
	"LC_CTYPE":                 {},
	"LOCALAPPDATA":             {},
	"LOGNAME":                  {},
	"SystemRoot":               {},
	"TEMP":                     {},
	"TMP":                      {},
	"TMPDIR":                   {},
	"TZ":                       {},
	"USER":                     {},
	"USERPROFILE":              {},
	"WINDIR":                   {},
	"XDG_RUNTIME_DIR":          {},
}

// validateEnvironment enforces the positive environment contract expected of
// the parent process. In particular, PATH, proxy settings, SDK debug settings,
// profile/host steering, PATs, and Azure/ARM credentials are not inherited.
func validateEnvironment(environ []string) error {
	values := make(map[string]string, len(environ))
	for _, assignment := range environ {
		name, value, ok := strings.Cut(assignment, "=")
		if !ok || name == "" {
			return fail(CodeEnvironmentInvalid)
		}
		if _, allowed := allowedEnvironmentNames[name]; !allowed {
			return fail(CodeEnvironmentInvalid)
		}
		if _, duplicate := values[name]; duplicate {
			return fail(CodeEnvironmentInvalid)
		}
		if strings.IndexByte(value, 0) >= 0 || strings.ContainsAny(value, "\r\n") {
			return fail(CodeEnvironmentInvalid)
		}
		values[name] = value
	}
	if values["DATABRICKS_AUTH_STORAGE"] != "secure" {
		return fail(CodeEnvironmentInvalid)
	}
	home := values["HOME"]
	if home == "" {
		home = values["USERPROFILE"]
	}
	if home == "" || !filepath.IsAbs(home) || filepath.Clean(home) != home {
		return fail(CodeEnvironmentInvalid)
	}
	return nil
}
