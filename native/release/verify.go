// Package release verifies the exact Databricks CLI release executable shipped
// beside the self-contained native helper.
package release

import (
	"bytes"
	"crypto/sha256"
	_ "embed"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"os"
	"runtime/debug"
	"unicode/utf8"

	cliauth "github.com/databricks/cli/libs/auth"
	sdkversion "github.com/databricks/databricks-sdk-go/version"
)

const (
	ManifestSchema = "dbtobsb.databricks-cli-release.v1"
	CLIModule      = "github.com/databricks/cli"
	CLIVersion     = "v1.9.0"
	CLIModuleSum   = "h1:LY1uF6TP+3MT+VuIziaKLd1jjHua+OEeXd15uu4OxU4="
	CLICommit      = "51ce3c7c5c4d5ba7ea20b8c8742f8ee995b3f6f6"
	SDKModule      = "github.com/databricks/databricks-sdk-go"
	SDKVersion     = "v0.160.0"
	SDKModuleSum   = "h1:vwgT/11y2vMw41BxcKbUUqarg45lmoEdukk9yYJg5AM="
	ArtifactOS     = "darwin"
	ArtifactArch   = "arm64"
	ArtifactSHA256 = "5ee48369334289c1828a1fd96b6aa5e7f54c8adb5b1ab7cc97da625c9adf2782"
)

//go:embed manifest.json
var manifestBytes []byte

type manifest struct {
	Schema       string `json:"schema"`
	CLIModule    string `json:"cli_module"`
	CLIVersion   string `json:"cli_version"`
	CLIModuleSum string `json:"cli_module_sum"`
	CLICommit    string `json:"cli_commit"`
	SDKModule    string `json:"sdk_module"`
	SDKVersion   string `json:"sdk_version"`
	SDKModuleSum string `json:"sdk_module_sum"`
	Artifact     struct {
		OS     string `json:"os"`
		Arch   string `json:"arch"`
		SHA256 string `json:"sha256"`
	} `json:"artifact"`
}

// VerifyManifest ensures the checked-in release record cannot drift from the
// compile-time trust constants.
func VerifyManifest() error {
	return verifyManifestBytes(manifestBytes)
}

func verifyManifestBytes(raw []byte) error {
	if !utf8.Valid(raw) || rejectManifestDuplicateKeys(raw) != nil {
		return errors.New("DBTOBSB_NATIVE_RELEASE_MANIFEST_INVALID")
	}
	var got manifest
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&got); err != nil {
		return errors.New("DBTOBSB_NATIVE_RELEASE_MANIFEST_INVALID")
	}
	var trailing any
	if err := decoder.Decode(&trailing); !errors.Is(err, io.EOF) {
		return errors.New("DBTOBSB_NATIVE_RELEASE_MANIFEST_INVALID")
	}
	if got.Schema != ManifestSchema || got.CLIModule != CLIModule ||
		got.CLIVersion != CLIVersion || got.CLIModuleSum != CLIModuleSum ||
		got.CLICommit != CLICommit || got.SDKModule != SDKModule ||
		got.SDKVersion != SDKVersion || got.SDKModuleSum != SDKModuleSum ||
		got.Artifact.OS != ArtifactOS || got.Artifact.Arch != ArtifactArch ||
		got.Artifact.SHA256 != ArtifactSHA256 {
		return errors.New("DBTOBSB_NATIVE_RELEASE_MANIFEST_INVALID")
	}
	return nil
}

func rejectManifestDuplicateKeys(raw []byte) error {
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	var walk func() error
	walk = func() error {
		token, err := decoder.Token()
		if err != nil {
			return err
		}
		delimiter, objectOrArray := token.(json.Delim)
		if !objectOrArray {
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
					return errors.New("invalid manifest key")
				}
				if _, duplicate := seen[key]; duplicate {
					return errors.New("duplicate manifest key")
				}
				seen[key] = struct{}{}
				if err := walk(); err != nil {
					return err
				}
			}
			end, err := decoder.Token()
			if err != nil || end != json.Delim('}') {
				return errors.New("invalid manifest object")
			}
		case '[':
			for decoder.More() {
				if err := walk(); err != nil {
					return err
				}
			}
			end, err := decoder.Token()
			if err != nil || end != json.Delim(']') {
				return errors.New("invalid manifest array")
			}
		default:
			return errors.New("invalid manifest delimiter")
		}
		return nil
	}
	if err := walk(); err != nil {
		return err
	}
	if _, err := decoder.Token(); !errors.Is(err, io.EOF) {
		return errors.New("trailing manifest json")
	}
	return nil
}

// VerifyBuildDependencies confirms the compiled CLI credential strategy and
// SDK version match the pinned manifest. The exact CLI module tag is pinned in
// go.mod/go.sum; its release commit is separately frozen by the manifest.
func VerifyBuildDependencies() error {
	if err := VerifyManifest(); err != nil {
		return err
	}
	if (cliauth.CLICredentials{}).Name() != "databricks-cli" || "v"+sdkversion.Version != SDKVersion {
		return errors.New("DBTOBSB_NATIVE_RELEASE_BUILD_INVALID")
	}
	info, ok := debug.ReadBuildInfo()
	if !ok || verifyDependencyVersions(info.Deps) != nil {
		return errors.New("DBTOBSB_NATIVE_RELEASE_BUILD_INVALID")
	}
	return nil
}

func verifyDependencyVersions(dependencies []*debug.Module) error {
	foundCLI := false
	foundSDK := false
	for _, dependency := range dependencies {
		if dependency == nil || dependency.Replace != nil {
			continue
		}
		switch dependency.Path {
		case CLIModule:
			foundCLI = dependency.Version == CLIVersion && dependency.Sum == CLIModuleSum
		case SDKModule:
			foundSDK = dependency.Version == SDKVersion && dependency.Sum == SDKModuleSum
		}
	}
	if !foundCLI || !foundSDK {
		return errors.New("DBTOBSB_NATIVE_RELEASE_BUILD_INVALID")
	}
	return nil
}

// VerifyCLIExecutable hashes one local executable without executing it.
func VerifyCLIExecutable(path string) error {
	if err := VerifyManifest(); err != nil {
		return err
	}
	file, err := os.Open(path)
	if err != nil {
		return errors.New("DBTOBSB_NATIVE_RELEASE_ARTIFACT_UNAVAILABLE")
	}
	defer file.Close()
	info, err := file.Stat()
	if err != nil || !info.Mode().IsRegular() || info.Size() <= 0 {
		return errors.New("DBTOBSB_NATIVE_RELEASE_ARTIFACT_INVALID")
	}
	digest := sha256.New()
	if _, err := io.Copy(digest, file); err != nil {
		return errors.New("DBTOBSB_NATIVE_RELEASE_ARTIFACT_UNAVAILABLE")
	}
	if hex.EncodeToString(digest.Sum(nil)) != ArtifactSHA256 {
		return errors.New("DBTOBSB_NATIVE_RELEASE_ARTIFACT_MISMATCH")
	}
	return nil
}
