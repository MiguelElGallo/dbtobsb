package release

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"runtime/debug"
	"testing"
)

func TestManifestAndDependencyContractArePinned(t *testing.T) {
	if err := VerifyManifest(); err != nil {
		t.Fatal(err)
	}
	dependencies := []*debug.Module{
		{Path: CLIModule, Version: CLIVersion, Sum: CLIModuleSum},
		{Path: SDKModule, Version: SDKVersion, Sum: SDKModuleSum},
	}
	if err := verifyDependencyVersions(dependencies); err != nil {
		t.Fatal(err)
	}
	dependencies[0].Version = "v1.7.1"
	if err := verifyDependencyVersions(dependencies); err == nil {
		t.Fatal("changed CLI version was accepted")
	}
	dependencies[0] = &debug.Module{Path: CLIModule, Version: CLIVersion, Sum: CLIModuleSum, Replace: &debug.Module{Path: "local"}}
	if err := verifyDependencyVersions(dependencies); err == nil {
		t.Fatal("replaced CLI module was accepted")
	}
}

func TestManifestRejectsDuplicateAndUnknownFields(t *testing.T) {
	duplicate := append(
		[]byte(fmt.Sprintf(`{"schema":%q,`, ManifestSchema)),
		bytes.TrimPrefix(manifestBytes, []byte("{"))...,
	)
	if err := verifyManifestBytes(duplicate); err == nil || err.Error() != "DBTOBSB_NATIVE_RELEASE_MANIFEST_INVALID" {
		t.Fatalf("duplicate manifest field was accepted: %v", err)
	}
	duplicateNested := bytes.Replace(
		manifestBytes,
		[]byte(`"artifact": {`),
		[]byte(`"artifact": {"os":"darwin",`),
		1,
	)
	if err := verifyManifestBytes(duplicateNested); err == nil || err.Error() != "DBTOBSB_NATIVE_RELEASE_MANIFEST_INVALID" {
		t.Fatalf("duplicate nested manifest field was accepted: %v", err)
	}
	unknownTop := append([]byte(`{"unknown":true,`), bytes.TrimPrefix(manifestBytes, []byte("{"))...)
	if err := verifyManifestBytes(unknownTop); err == nil || err.Error() != "DBTOBSB_NATIVE_RELEASE_MANIFEST_INVALID" {
		t.Fatalf("unknown manifest field was accepted: %v", err)
	}
	unknownNested := bytes.Replace(
		manifestBytes,
		[]byte(`"artifact": {`),
		[]byte(`"artifact": {"unknown":true,`),
		1,
	)
	if err := verifyManifestBytes(unknownNested); err == nil || err.Error() != "DBTOBSB_NATIVE_RELEASE_MANIFEST_INVALID" {
		t.Fatalf("unknown nested manifest field was accepted: %v", err)
	}
}

func TestExecutableVerificationFailsClosed(t *testing.T) {
	path := filepath.Join(t.TempDir(), "databricks")
	if err := os.WriteFile(path, []byte("not the release"), 0o700); err != nil {
		t.Fatal(err)
	}
	if err := VerifyCLIExecutable(path); err == nil || err.Error() != "DBTOBSB_NATIVE_RELEASE_ARTIFACT_MISMATCH" {
		t.Fatalf("unexpected verification result: %v", err)
	}
	if err := VerifyCLIExecutable(filepath.Join(t.TempDir(), "missing")); err == nil || err.Error() != "DBTOBSB_NATIVE_RELEASE_ARTIFACT_UNAVAILABLE" {
		t.Fatalf("unexpected missing result: %v", err)
	}
}
