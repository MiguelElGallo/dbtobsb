# Decision 0002: Correct P1.1 invocation recovery before first release

- Status: accepted
- Date: 2026-07-15
- Scope: `dbtobsb.artifact-pair-report.v1` static invocation issue text

## Context

The P1.1 candidate originally told readers to recollect both artifacts from the same target directory and described mismatched invocation IDs as an untrusted pair. dbt commands can overwrite artifacts in a reused target path, while the inspector actually binds a pair through equal parseable `metadata.invocation_id` values. The wording was operationally insufficient and overstated provenance trust.

The candidate has not been distributed, released, or accepted by an external consumer. Every report fixture, generated JSON Schema variant, CLI output, Python constructor, and documentation contract remains under repository control.

## Decision

Correct the two static invocation actions to require both closed artifacts from one completed pinned `dbt build` invocation before another dbt command runs. Describe a mismatch as different invocation identity, and reserve `PAIR_VALID` for internal contract validity rather than authenticity or custody.

Retain report schema identifier `dbtobsb.artifact-pair-report.v1` for this pre-release correction. Regenerate and byte-check the schema and fixtures, run the full API/CLI/constructor gates, record the change in immutable review history, and require dbt, usability, and security re-review before release. Any equivalent post-release static-text change requires a new contract-version decision with consumer migration analysis.

## Consequences

The recovery guide also requires an empty attempt-specific target path and collection before another command can overwrite it. Directory co-location remains custody context, not pairing evidence. P1.1 still does not authenticate origin, prove absence of modification, or assign capture completeness.
