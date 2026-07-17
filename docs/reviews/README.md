# Review records

This directory preserves review evidence. Starting with v0.3.0, current work uses one [release acceptance ledger](v0.3.0-release/acceptance-ledger.md), stable domain rubrics, and re-review of changed criteria only. The older part-by-part reports below remain as historical evidence; their repeated three-reviewer cadence is not the current process.

See the [review process](../plans/review-process.md) for routing tags, boundary triggers, domain rubrics, evidence packets, and milestone gates.

## v0.3.0 release

| Record | Purpose |
|---|---|
| [Acceptance ledger](v0.3.0-release/acceptance-ledger.md) | One deduplicated list of release outcomes, owners, gates, and evidence |
| [Support contract](../releases/v0.3.0-support-contract.md) | Frozen customer promise under review |

## Historical records

## P2 native Databricks collector

| Review lens | Latest report | Verdict |
| --- | --- | --- |
| Databricks platform/security | [databricks.md](p2-native-collector/databricks.md) | `PASS` |
| dbt Core/artifact contract | [dbt-core.md](p2-native-collector/dbt-core.md) | `PASS` |
| Product usability/onboarding | [usability.md](p2-native-collector/usability.md) | `PASS` |
| Diataxis information architecture | [documentation-ia.md](p2-native-collector/documentation-ia.md) | `PASS` |
| FastAPI-style writing | [documentation-style.md](p2-native-collector/documentation-style.md) | `PASS` |
| Security/compliance documentation | [documentation-security.md](p2-native-collector/documentation-security.md) | `PASS` |
| Documentation usability/accessibility | [documentation-usability.md](p2-native-collector/documentation-usability.md) | `PASS` |

The [P2 review index](p2-native-collector/README.md) identifies the frozen
64-file authoring set. The [final resolution](p2-native-collector/resolution.md)
binds these reports to the intended release tag and requires that tag to point
to the merged commit containing the records.

## P1.1 local artifact-pair inspector

| Review lens | Latest report | Verdict |
| --- | --- | --- |
| Databricks platform/security | [databricks-rereview-4.md](p1.1-artifact-pair-inspector/databricks-rereview-4.md) | `PASS_WITH_FOLLOW_UP` |
| dbt Core/artifact contract | [dbt-core-rereview-4.md](p1.1-artifact-pair-inspector/dbt-core-rereview-4.md) | `PASS_WITH_FOLLOW_UP` |
| Usability/onboarding | [usability-rereview-4.md](p1.1-artifact-pair-inspector/usability-rereview-4.md) | `PASS_WITH_FOLLOW_UP` |
| Diátaxis information architecture | [documentation-ia-rereview-2.md](p1.1-artifact-pair-inspector/documentation-ia-rereview-2.md) | `PASS_WITH_FOLLOW_UP` |
| Security/compliance documentation | [documentation-security-rereview-2.md](p1.1-artifact-pair-inspector/documentation-security-rereview-2.md) | `PASS` |
| FastAPI-style writing | [documentation-style-rereview-2.md](p1.1-artifact-pair-inspector/documentation-style-rereview-2.md) | `PASS` |
| dbt subject-matter documentation | [documentation-dbt-rereview.md](p1.1-artifact-pair-inspector/documentation-dbt-rereview.md) | `PASS` |
| Documentation usability/accessibility | [documentation-usability-rereview-2.md](p1.1-artifact-pair-inspector/documentation-usability-rereview-2.md) | `PASS_WITH_FOLLOW_UP` |
| Final reader-journey consistency | [documentation-final-rereview.md](p1.1-artifact-pair-inspector/documentation-final-rereview.md) | `PASS` |

The [final resolution](p1.1-artifact-pair-inspector/resolution.md) binds the accepted source, documentation, evidence, and latest verdicts. Initial reviews and failed re-review cycles remain in the same directory as immutable `CHANGES_REQUIRED` evidence. Current follow-ups belong to later Databricks runtime, archive, full-lock, disconnected distribution, rendered-site, accessibility, and publication gates; they do not permit P1.1 to claim a complete capture or qualified production runtime.

## P0 planning and documentation

| Review lens | Latest report | Verdict |
| --- | --- | --- |
| Databricks platform | [databricks-rereview-18.md](p0-planning-baseline/databricks-rereview-18.md) | `PASS` |
| dbt Core | [dbt-core-rereview-17.md](p0-planning-baseline/dbt-core-rereview-17.md) | `PASS` |
| Usability/onboarding | [usability-rereview-17.md](p0-planning-baseline/usability-rereview-17.md) | `PASS_WITH_FOLLOW_UP` |
| Diataxis information architecture | [documentation-ia-final-rereview-2.md](p0-planning-baseline/documentation-ia-final-rereview-2.md) | `PASS_WITH_FOLLOW_UP` |
| FastAPI-style writing | [documentation-style-final-rereview-2.md](p0-planning-baseline/documentation-style-final-rereview-2.md) | `PASS` |
| Security/compliance documentation | [documentation-security-final-rereview.md](p0-planning-baseline/documentation-security-final-rereview.md) | `PASS` |
| Documentation usability/accessibility | [documentation-usability-final.md](p0-planning-baseline/documentation-usability-final.md) | `PASS_WITH_FOLLOW_UP` |

The [final resolution](p0-planning-baseline/resolution.md) binds the reviewed hashes and explains every retained nonblocking gate. The initial FastAPI-style and security reports remain visible as `CHANGES_REQUIRED` evidence before their fixes.

## P0 App smoke implementation

| Review lens | Latest report | Verdict |
| --- | --- | --- |
| Databricks platform | [databricks-rereview-3.md](p0-app-smoke/databricks-rereview-3.md) | `PASS_WITH_FOLLOW_UP` |
| dbt Core | [dbt-core-rereview-4.md](p0-app-smoke/dbt-core-rereview-4.md) | `PASS` |
| Usability/accessibility | [usability-rereview-4.md](p0-app-smoke/usability-rereview-4.md) | `PASS` |

## Rules

- Current reviews name an immutable evidence packet, affected rubric checks, and one acceptance outcome.
- Reviewers do not edit the files they review.
- Findings remain in history after resolution, but related symptoms are consolidated under one root outcome.
- `CHANGES_REQUIRED` and blocking findings require new evidence only for the changed criterion.
- `PASS_WITH_FOLLOW_UP` is acceptable only when the report names a later product gate and the item does not block the reviewed slice.
- One domain owner reviews an ordinary slice. Boundary triggers add only the named second owner. All three owners participate only at contract freeze, local release candidate, and live Azure proof.
- AI-generated reviews support defect finding and traceability; they do not replace accountable human approval.
- Rendered-site, browser, keyboard, contrast, responsive-layout, and screen-reader validation cannot pass until a complete documentation site exists.
