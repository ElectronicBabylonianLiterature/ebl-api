# Independent media API review

## Summary

No blocking correctness finding remains in the reviewed API integration.
Reviewed base commit: `3602c2b8d71637369a9f25cd6d29293f57cc70e6`.
Final reviewed 39-path digest after persistence integration:
`ffc21dfbbb060b0534b30af4479e29d61dc82efdd54a3eb4a0920c35b83396f2`.
The published persistence parent and its six-file CodeQL test correction were
reconciled with the independently reviewed persistence snapshot. All inherited
implementation files match; the README combines the two reviewed sections.
API production code is unchanged from the independent focused test run. TASK
files are excluded. Final committed identity still needs recording.

## Findings

- Fragment authorization precedes media lookup and storage opening. Binary
  access is scoped to the requested fragment association.
- Invalid identifiers and thumbnail sizes are client errors. Missing optional
  representations are 404; missing stored bytes remain integrity failures.
- Private responses use no-store, Authorization variation, and nosniff headers.
  SVG is attachment-only with restrictive CSP.
- Original-only nonprimary media remains discoverable. Fragment detail and
  paginated search expose summaries without rewriting legacy thumbnail paths.
- The explicit optional `legacyHasPhoto` field preserves the pre-enrichment
  legacy availability independently of the combined `hasPhoto` value. This
  supports frontend partial-migration access and rollback behavior.
- Runtime construction does not prepare media indexes or migrate data.
- Successful and rejected streaming responses close their opened streams.

## Severity

No open blocking API finding. Publication feedback review is still required
before final handoff.

## Reproduction Steps

The independent reviewer ran new web integration tests and URL tests against a
disposable local MongoDB replica set: **59 tests passed in 45.75 seconds**.
This includes real Mongo/GridFS, actual HTTP serving, scoped authorization,
legacy availability, one-query summary batching, stream cleanup, and disabled
runtime behavior. Existing datetime and Marshmallow deprecations were emitted.

Five synthetic responses were also exported through actual Falcon routes and
DTOs, then consumed by the frontend repository and binary loader. Original-only
nonprimary media, attribution, and exact scoped URLs survived for museum numbers
containing slashes, spaces, percent, Unicode, question marks, hash, and `!'()*`.

No production database or migration was used.

## Recommendation

Publish after the repository-required full-suite and static gates pass. Merge
persistence first, integrate its final primary-read preference changes, and keep
the runtime flag disabled until the documented rollout is ready.

## What Has To Be Done

1. Integrate the final persistence commit and record the final API SHA.
2. Retain the passing full-suite, focused coverage, and static-analysis evidence.
3. Fetch all new PR timeline comments, review submissions, and inline threads
  after first publication and address actionable feedback before final handoff.
4. Remove temporary TASK documents according to repository policy before merge.

Merged foundation PR #738 comments, reviews, and threads were fully inspected.
Its historical concerns about real Mongo semantics and DTO/route roundtrips
were specifically exercised. New PR feedback remains pending first publication.

Root separately reported a real-browser integration pass against actual API,
MongoDB/GridFS, frontend provider/adapters, ApiClient, and gallery components.
Ten checks covered pagination, lazy original access, downloaded-byte SHA-256,
slash-containing museum numbers, credits, original-only media, partial legacy
selection, and 403 without fallback. Runtime JavaScript errors were zero; the
only browser console entry was the expected denied network request. Evidence is
in the external verification log and screenshot. This is additional root-run
evidence, distinct from the independent reviewer's focused tests.

Root also ran the composed migration-to-browser workflow: a new versioned
synthetic plan, explicit index preparation, apply, idempotent resume, owned
gallery preview, EXIF Artist/Copyright attribution, and byte-exact original
download all passed. The prior ten gallery checks passed in the same composition.
This separate root-run test completed in 6.41 seconds; its log and composition
manifest are retained outside the implementation trees. No production operation
was involved.

The author reports the integrated full suite passed: 6,059 tests, two existing
skips, and one expected failure. A subsequent test-only addition checks the
existing Sentry callback in an isolated scope without sending an event. The
independent reviewer inspected that addition and reran its complete bootstrap
file: six tests passed in 2.52 seconds. Existing Sentry and datetime deprecation
warnings remain. Production source did not change after the full-suite run.
The author also reports 573 of 573 affected production statements covered and
passing Pyre, Pyright, mypy, and Flake8 gates.
