# Review records

This directory preserves immutable findings and re-review verdicts for each independently deliverable part. The latest reports below are authoritative for baseline 0.20; earlier numbered reports remain as the audit trail and are not rewritten to hide failed passes.

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

- Every report names an exact file set and content hash.
- Reviewers do not edit the files they review.
- Findings remain in history after resolution.
- `CHANGES_REQUIRED` and blocking findings require a new frozen input and re-review.
- `PASS_WITH_FOLLOW_UP` is acceptable only when the report names a later product gate and the item does not block the reviewed slice.
- AI-generated reviews support defect finding and traceability; they do not replace accountable human approval.
- Rendered-site, browser, keyboard, contrast, responsive-layout, and screen-reader validation cannot pass until a complete documentation site exists.
