package main

import (
	"bytes"
	"errors"
	"strings"
	"testing"
)

func TestReleaseGateRunsBeforeProtocolEnvironmentOrAuth(t *testing.T) {
	original := verifyBuildDependencies
	t.Cleanup(func() { verifyBuildDependencies = original })
	verifyBuildDependencies = func() error {
		return errors.New("hostile release detail with secret-token")
	}
	var output bytes.Buffer
	exitCode := run(
		strings.NewReader(`{"protocol":"hostile"}`),
		&output,
		[]string{"DATABRICKS_TOKEN=secret-token"},
	)
	if exitCode != 1 {
		t.Fatalf("unexpected exit code: %d", exitCode)
	}
	want := `{"protocol":"dbtobsb.native-bridge.v1","ok":false,"code":"DBTOBSB_NATIVE_RELEASE_BUILD_INVALID"}` + "\n"
	if output.String() != want || strings.Contains(output.String(), "secret-token") ||
		strings.Contains(output.String(), "hostile release detail") {
		t.Fatalf("startup gate was not stable and redacted: %q", output.String())
	}
}

func TestValidReleaseGateContinuesToEnvironmentValidation(t *testing.T) {
	original := verifyBuildDependencies
	t.Cleanup(func() { verifyBuildDependencies = original })
	verifyBuildDependencies = func() error { return nil }
	var output bytes.Buffer
	exitCode := run(strings.NewReader(`{}`), &output, []string{"PATH=/hostile"})
	if exitCode != 1 || !strings.Contains(output.String(), "DBTOBSB_NATIVE_ENVIRONMENT_INVALID") {
		t.Fatalf("bridge did not continue after a valid release gate: %q", output.String())
	}
}
