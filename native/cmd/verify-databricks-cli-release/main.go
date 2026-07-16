package main

import (
	"fmt"
	"os"

	nativerelease "github.com/miguelperedo/dbtobsb/native/release"
)

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stdout, "DBTOBSB_NATIVE_RELEASE_USAGE_INVALID")
		os.Exit(2)
	}
	if err := nativerelease.VerifyBuildDependencies(); err != nil {
		fmt.Fprintln(os.Stdout, err.Error())
		os.Exit(1)
	}
	if err := nativerelease.VerifyCLIExecutable(os.Args[1]); err != nil {
		fmt.Fprintln(os.Stdout, err.Error())
		os.Exit(1)
	}
	fmt.Fprintln(os.Stdout, "DBTOBSB_NATIVE_RELEASE_VERIFIED")
}
