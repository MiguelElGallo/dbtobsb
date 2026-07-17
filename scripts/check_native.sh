#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
build_root="$(mktemp -d)"
trap 'rm -rf "$build_root"' EXIT

cd "$repo_root/native"

go test ./...
go vet ./...
go test -race ./...
CGO_ENABLED=0 go build -trimpath -o "$build_root/dbtobsb-native-bridge" ./cmd/dbtobsb-native-bridge
CGO_ENABLED=0 go build -trimpath -o "$build_root/verify-databricks-cli-release" ./cmd/verify-databricks-cli-release

printf '%s\n' "DBTOBSB_NATIVE_CHECKS_PASSED"
