package main

import (
	"context"
	"io"
	"os"

	"github.com/miguelperedo/dbtobsb/native/bridge"
	nativerelease "github.com/miguelperedo/dbtobsb/native/release"
)

var verifyBuildDependencies = nativerelease.VerifyBuildDependencies

func run(stdin io.Reader, stdout io.Writer, environ []string) int {
	if err := verifyBuildDependencies(); err != nil {
		response := bridge.Response{
			Protocol: bridge.ProtocolVersion,
			OK:       false,
			Code:     "DBTOBSB_NATIVE_RELEASE_BUILD_INVALID",
		}
		if bridge.EncodeResponse(stdout, response) != nil {
			return 2
		}
		return 1
	}
	engine := bridge.New()
	response := engine.Execute(context.Background(), environ, stdin)
	if err := bridge.EncodeResponse(stdout, response); err != nil {
		fallback := bridge.Response{
			Protocol: bridge.ProtocolVersion,
			OK:       false,
			Code:     "DBTOBSB_NATIVE_INTERNAL_FAILURE",
		}
		_ = bridge.EncodeResponse(stdout, fallback)
		return 2
	}
	if !response.OK {
		return 1
	}
	return 0
}

func main() {
	os.Exit(run(os.Stdin, os.Stdout, os.Environ()))
}
