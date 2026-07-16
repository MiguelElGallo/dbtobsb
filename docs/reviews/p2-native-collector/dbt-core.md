# P2 dbt Core and artifact-contract review

| Field | Value |
| --- | --- |
| Review date | 2026-07-16 |
| Review role | Independent dbt Core and artifact-contract reviewer |
| Frozen authoring set | [64 path-sorted files](author-set.sha256) |
| Authoring-set SHA-256 | `b09ac6b72039490080ce7f2ea1dcb00a604f3388f1c5b81215e979e590304898` |
| Verdict | **PASS** |

This verdict applies only to the private personal/test
`v0.2.0-alpha.1` engineering preview.

## Verified findings

- Release wheels are capture `0.2.0a3` and collector `0.2.0a14`; the
  rendered Bundle refers to those versions.
- Tagged dbt Core `1.11.12` manifest-v12 and run-results-v6 schemas match
  the vendored checksum pins.
- The Databricks JavaScript materialization exception is restricted to one
  macro, one schema path, and the exact language list.
- Validation enforces the artifact-attested dbt version and adapter type,
  exact build command and selector, invocation equality, result membership,
  resource-aware statuses, finite timing, and nonempty results.
- Primary artifacts are accepted only at `target/manifest.json` and
  `target/run_results.json`; exact bytes are preserved before validation.
- Three models, one seed, and five tests correctly produce nine result nodes.
  dbt outcome remains distinct from evidence-pair and Lakeflow state.
- The final packaged Azure run was `COMPLETE` and `PAIR_VALID` with nine
  nodes. Identical replay retained one invocation and nine nodes with unchanged
  digest and timestamps.

The review found one nonblocking wording ambiguity: the Bundle pins the full
dependency combination, but artifacts cannot attest every transitive installed
distribution. The wiring guide was corrected before this final record to state
that distinction and require requalification for any dependency change.

The missing native failed-dbt proof, custom-profile alignment, dedicated
identities, sealed parameters, retention controls, and SBOM remain future
production gates. No dbt blocker remains for the stated alpha.
