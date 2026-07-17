# dbtobsb native request bridge

This directory is an isolated Go 1.26.5 foundation for the attended regulated installer. It does not call `databricks auth token`, `databricks auth env`, Current User Preview, or a generic API/SQL surface. It loads one explicit non-`DEFAULT` profile through Databricks CLI `ProfileAuthLoaders`, pins the in-process `auth.CLICredentials` strategy, and requires `DATABRICKS_AUTH_STORAGE=secure`. Enrollment operations issue one fixed workspace request. Each protected history, cancellation, or registered-statement invocation issues the fixed actor statement and, only after an exact match, one fixed protected request.

The credential boundary comprises this helper and the CLI native-store adapter. On macOS, the adapter reads OS Keychain through the absolute `/usr/bin/security` executable used by `zalando/go-keyring`; the bearer can therefore transit that private child-process pipe. The bearer must never cross into the installer parent, stdin/stdout, argv, logs, errors, or safe string representations. `PATH`, proxy variables, SDK debug variables, profile/host steering, PATs, and Azure/ARM credentials are not inherited.

## Fixed v1 operations

The bounded stdin/stdout protocol supports only:

- `query_history_list`: one GA Query History page for one 16-hex warehouse ID, an approved lowercase actor SHA-256, and a time window no longer than 20 minutes. The helper first runs the fixed actor statement, then fixes `max_results=1` on the history request. Decoded query text is capped at 512 KiB, a page token at 4 KiB, and the remote/output JSON envelope at approximately 4 MiB to cover worst-case six-byte JSON escaping.
- `statement_execution_cancel`: GA Statement Execution cancellation for one canonical lowercase UUID, the exact warehouse, and the approved actor SHA-256. The helper first runs the fixed actor statement. An accepted cancellation remains nonterminal.
- `statement_execution_submit`: one operation from `dbtobsb.native-operation-registry.v1`, on the exact warehouse and approved actor. Python sends only a registry operation ID, strictly typed parameters, the registry version, and the expected semantic digest; executable SQL is rendered and digest-checked inside the native helper. The request always uses inline JSON, `wait_timeout=50s`, and `on_wait_timeout=CANCEL`, is sent once, and maps all six Statement Execution states to a sanitized exhaustive disposition without returning SQL, statement ID, result data, or remote error text. The current foundation registry contains the signed preparation marker and a harmless test sentinel. Production DDL, DML, and readback entries remain a separate release gate; unknown registry entries and extra or hostile parameters fail before authentication or network activity.
- `actor_fingerprint_observe`: enrollment observation using one fixed read-only GA Statement Execution request containing exactly `SELECT session_user()`, `wait_timeout=50s`, `on_wait_timeout=CANCEL`, and inline JSON output. Its payload contains only the verified warehouse ID. It accepts only a terminal one-row/one-string result and returns only the lowercase SHA-256 fingerprint; the raw identity and statement ID never cross stdout. This operation observes an identity during attended enrollment. It does not authorize any later operation.
- `actor_identity_check`: the same fixed statement, response parser, warehouse boundary, and cost boundary, plus an approved lowercase SHA-256 input. It hashes the observed identity in-process and returns only `matched`. Protected history and cancellation do not trust a previous check: they run this guard inside their own helper invocation, and mismatch or indeterminate results block the protected request.

The parent sends one JSON document no larger than 64 KiB and reads exactly one JSON line. Duplicate keys, unknown fields, unknown operations, redirects, noncanonical Azure hosts, hostile identifiers, oversized responses, and ambiguous transport outcomes fail closed with stable codes. The helper resolves one authenticator for the invocation, attaches its credential once to the actor request, then copies that exact internal authorization value to the protected request. Both requests use the same fixed HTTP client, and neither request is retried. The bearer never crosses the process protocol. OAuth refresh is a separate token-endpoint exchange before the actor request. The production workspace transport is HTTP/1.1-only: its protocol set and TLS ALPN exclude HTTP/2, alternate TLS protocols are disabled, keep-alives are disabled, and POST bodies are not exposed through `GetBody` for replay. This prevents Go's HTTP/2 retry paths and reused-connection HTTP/1 retry path; every ambiguous wire failure is terminal and indeterminate.

## Launch prerequisites and enrollment

The signed, typed connection is a prerequisite; this helper does not create, infer, or approve it. Before launching the helper, the parent must independently verify a signed connection that binds the exact profile, canonical Azure host, dedicated installer-only warehouse ID, and, after enrollment, the approved actor fingerprint. It must reject user-, AI-, plan-, shared-, or dbt-workload-warehouse values before authentication or network activity. This helper validates the warehouse ID syntax and resolved profile/host, but cannot prove that a warehouse is dedicated.

First enrollment must be an explicit attended sequence:

1. Verify the signed typed profile, host, and dedicated installer warehouse; show and obtain explicit approval for the bounded Statement Execution cost.
2. Complete browser/OAuth login and explicitly confirm the displayed human identity.
3. Invoke `actor_fingerprint_observe` once on that approved dedicated warehouse.
4. Show the fingerprint for human confirmation. Only after explicit approval may the parent persist it and sign a new typed connection.
5. Persist only the signed binding. Protected history, cancellation, and registered submission consume it and perform their own actor guard in the same native invocation as the protected request.

## Query History data boundary

A successful Query History page intentionally contains sensitive raw query text, a control-plane query reference, the verified installer warehouse ID, and possibly a page token. The parent must keep the raw page in memory only: never log, checkpoint, persist, cache, or normalize it. Query text may be consumed only for signed preparation-marker recovery. Pagination is one helper invocation per page; that invocation sends one actor request and, after a match, one history request, with no automatic retry.

`query_reference` is a Query History control-plane reference; a cancellation `statement_id` is only a Statement Execution recovery handle. Neither is a dbt `AttemptKey`, dbt `invocation_id`, artifact identity, Databricks Job/task identity, or normalized dbt evidence.

## Build and verify

```text
go test ./...
go vet ./...
go test -race ./...
CGO_ENABLED=0 go build -trimpath -buildvcs=false -ldflags='-buildid=' ./cmd/dbtobsb-native-bridge
go run ./cmd/verify-databricks-cli-release /absolute/path/to/databricks
```

`release/manifest.json` freezes Databricks CLI `v1.7.0`, release commit `2f68ee4951ef96fa9d99e40c8ebadccf08412d58`, SDK `v0.154.0`, both Go module sums, and the official darwin-arm64 executable SHA-256. Its parser rejects duplicate and unknown fields. The bridge verifies its embedded dependency versions and sums before environment parsing, authentication, or network setup.

## Parent integration and remaining qualification

The Python parent now provides the fixed release-layout seal, positive environment allowlist, bounded process group, exact protocol parser, signed actor/connection binding, memory-only history projection, and session-bound one-shot cancellation handles. It opens and hashes the helper before launch and attempts execution through the inherited descriptor; platforms that refuse descriptor-bound execution fail closed with a stable code rather than falling back to the replaceable pathname.

Before production release, the product still must:

- complete and review the production DDL, DML, and readback entries in the versioned closed operation registry; the helper must never add a generic SQL entry;
- sign the final helper, include its final checksum and dependencies in the wrapper manifest/SBOM, and verify provenance before execution; and
- complete independent security/usability re-review plus live Keychain, OAuth refresh, canonical Azure workspace, dedicated warehouse, timeout/cancellation, cost, and zero-running-resource cleanup qualification.

The tests in this directory use fake credentials and transports. They do not prove live Keychain, OAuth, workspace, cloud, packaging, parent recovery, or cleanup behavior.
