package bridge

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

type bootstrapRegistryVector struct {
	Binding     json.RawMessage `json:"binding"`
	Catalog     string          `json:"catalog"`
	MarkerToken string          `json:"marker_token"`
	Operations  []struct {
		Parameters        json.RawMessage `json:"parameters"`
		RegistryOperation string          `json:"registry_operation"`
		RegistryVersion   string          `json:"registry_version"`
		SemanticSHA256    string          `json:"semantic_sha256"`
	} `json:"operations"`
	Schema       string `json:"schema"`
	VectorSchema string `json:"vector_schema"`
}

func loadBootstrapRegistryVector(t *testing.T) bootstrapRegistryVector {
	t.Helper()
	path := filepath.Join(
		"..",
		"..",
		"contracts",
		"src",
		"dbtobsb_contracts",
		"bootstrap-operation-registry-v1-vectors.json",
	)
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var vector bootstrapRegistryVector
	if strictUnmarshal(raw, &vector) != nil ||
		vector.VectorSchema != "dbtobsb.native-bootstrap-registry-vectors.v1" ||
		!validBootstrapIdentifier(vector.Catalog) || !validBootstrapIdentifier(vector.Schema) ||
		len(vector.Binding) == 0 || !validMarkerToken(vector.MarkerToken) || len(vector.Operations) != 10 {
		t.Fatal("invalid bootstrap registry vector")
	}
	return vector
}

func TestOperationRegistryMatchesPackagedPythonBootstrapVectors(t *testing.T) {
	vector := loadBootstrapRegistryVector(t)
	seen := make(map[string]struct{}, len(vector.Operations))
	for _, operation := range vector.Operations {
		if operation.RegistryVersion != registryVersion {
			t.Fatal("registry version drift")
		}
		statement, err := renderRegisteredStatement(submitPayload{
			RegistryVersion:   operation.RegistryVersion,
			RegistryOperation: operation.RegistryOperation,
			Parameters:        operation.Parameters,
			SemanticSHA256:    operation.SemanticSHA256,
		})
		if err != nil || !strings.HasPrefix(
			statement,
			"/* DBTOBSB_MUTATION_MARKER_V1."+vector.MarkerToken+" */\n",
		) {
			t.Fatalf("registry vector mismatch for %s: %v", operation.RegistryOperation, err)
		}
		if _, duplicate := seen[operation.RegistryOperation]; duplicate {
			t.Fatal("duplicate registry operation")
		}
		seen[operation.RegistryOperation] = struct{}{}
	}
}

func TestOperationRegistryRejectsExtraAndMalformedBootstrapValues(t *testing.T) {
	vector := loadBootstrapRegistryVector(t)
	for _, operation := range vector.Operations {
		var parameters map[string]any
		if json.Unmarshal(operation.Parameters, &parameters) != nil {
			t.Fatal("invalid test vector parameters")
		}
		parameters["statement"] = "DROP TABLE customer_data"
		withExtra, _ := json.Marshal(parameters)
		_, err := renderRegisteredStatement(submitPayload{
			RegistryVersion:   registryVersion,
			RegistryOperation: operation.RegistryOperation,
			Parameters:        withExtra,
			SemanticSHA256:    operation.SemanticSHA256,
		})
		if errorCode(err) != CodeRegistryParametersInvalid {
			t.Fatalf("extra caller SQL accepted by %s", operation.RegistryOperation)
		}
	}

	manifest := vector.Operations[len(vector.Operations)-1]
	var parameters map[string]any
	if json.Unmarshal(manifest.Parameters, &parameters) != nil {
		t.Fatal("invalid manifest parameters")
	}
	mutations := map[string]any{
		"workspace_id":                     "01",
		"observed_job_id":                  "0",
		"evidence_schema":                  "different",
		"object_contract_sha256":           strings.Repeat("0", 64),
		"collector_service_principal_name": parameters["observed_service_principal_name"],
	}
	for field, value := range mutations {
		t.Run(field, func(t *testing.T) {
			copy := make(map[string]any, len(parameters))
			for key, original := range parameters {
				copy[key] = original
			}
			copy[field] = value
			raw, _ := json.Marshal(copy)
			_, err := renderRegisteredStatement(submitPayload{
				RegistryVersion:   registryVersion,
				RegistryOperation: manifest.RegistryOperation,
				Parameters:        raw,
				SemanticSHA256:    manifest.SemanticSHA256,
			})
			if errorCode(err) != CodeRegistryParametersInvalid {
				t.Fatalf("invalid manifest value accepted: %s", field)
			}
		})
	}
}
