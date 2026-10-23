# Independent legacy media migration review

## Summary

No blocking correctness finding remains in the reviewed migration code. Final
repository-wide suites and quality gates remain author-owned requirements;
committed identity and new PR feedback review are pending. No production
migration was run.

Reviewed base commit: `3602c2b8d71637369a9f25cd6d29293f57cc70e6`.
Final reviewed 40-path digest after persistence integration and index correction:
`a0c01f9499e1c062f0db37dd48c3164742e657c21cf3b9e077a6079f614e0942`.
This excludes TASK files and includes the reconciled persistence dependencies.
Production code is identical to the command-audited probe snapshot. Final
committed identity still needs recording.

The independent reviewer inspected the seven-file test correction that moves
23 mutating calls outside assertions; operation order and assertions are
preserved. The author then reran all 111 migration tests successfully in 10.69
seconds, retaining 814 of 814 production statements covered. The inherited
six-file persistence test correction also passed an independent 61-test run.
These test-only changes do not alter the migration behavior reviewed below.

## Findings

- A forced partial filename-index hint omitted a competing original and
  incorrectly marked a duplicate source eligible. The independent reviewer also
  reproduced the same failure with a compound geospatial index whose metadata
  had no sparse flag. The shared selector now accepts only complete visible
  simple-collation B-tree indexes with ordinary ascending/descending keys.
  Partial, sparse, hidden, wildcard, text, and geospatial variants are rejected.
  With a valid complete index, both originals are withheld for review. Planning
  remains read-only; explicit preparation creates a complete fallback without
  dropping existing indexes. The README states this dry-run prerequisite.
- A malformed small JPEG without quantization segments passed the first
  structural-only inspector. Preview generation then raised an unclassified
  Pillow error. The author added bounded pixel decoding and normalized preview
  errors. The independent no-DQT reproduction now classifies both policies as
  blocked and classifies preview failures without aborting the source scan.
- The apply path now preflights initialized media indexes and the transaction
  lock before adoption, and source revalidation uses primary reads.
- The resumable plan binds database endpoint identity, policy, and completed-plan
  checksum. Apply uses a verified local plan snapshot and validates every row
  before the first write. Malformed policies and boolean numeric limits fail.
- Staged preview reconciliation checks both the current source owner and the
  deterministic candidate identity before cleanup. Pending work produces exit 2.
- The README accurately distinguishes bounded structural-only JPEG validation,
  source inventory limits, withheld exceptions, preview policy, and manual
  recovery of process-death gaps. It does not promise blanket orphan deletion.
- A separate independent real-Mongo probe audited 34 read commands and zero
  writes during a resumable preview dry run. Full collection contents were
  identical before and after planning.
- The probe changed source bytes without changing source length. Apply rejected
  that source, withheld duplicate and missing-data originals, created one safe
  nonprimary record with four owned previews, and resumed idempotently. All five
  legacy original metadata records were retained.
- This tool produces a migration plan. Mapping failures short-circuit binary
  inspection; it does not replace the earlier comprehensive production audit.
- Completion covers the bound plan, not sources added outside its inventory.
  Final rollout needs a fresh inventory comparison while source writes pause.

## Severity

No remaining current-code correctness blocker has been identified after the
JPEG and filename-index corrections. Final publication checks remain required.

## Reproduction Steps

Create a small valid JPEG, remove its DQT segments, and inspect it using default
and preview policies. The corrected tool must emit a blocked result without
terminating a scan containing subsequent valid originals.

The final migration test directory independently passed **127 tests in
10.46 seconds**, including schema, CLI, JPEG, preflight, index, and recovery
cases. All 40 reviewed files remained unchanged during the run. The author
reports 824 of 824 production statements covered and passing static gates.

For the index reproduction, insert two originals for one fragment and create a
partial filename index, then separately a filename-plus-geospatial index. Both
unsafe hints count one original while an unhinted query counts two. The fixed
planner rejects each unsafe-only setup; adding a complete index produces
`multiple-originals`. The command-audited end-to-end probe passed again on this
final source, with 34 reads and zero writes during resumable planning.

The independent synthetic probe also exercises resumable planning, command
monitoring, byte tampering, duplicate withholding, owned previews, nonprimary
creation, and resumed apply. It runs only on a disposable local replica set.

## Recommendation

Publish after required full-suite and quality gates pass. Keep production apply
actions separate from this development work, retain the documented source-write
pause and fresh inventory comparison, and review withheld outcomes explicitly.

## What Has To Be Done

1. Record the final committed SHA after the reviewed persistence integration.
2. Finish required full-suite, coverage, static-analysis, and markdown checks.
3. Fetch all new PR comments, reviews, and inline threads after publication.
4. Remove temporary TASK documents according to repository policy before merge.

Foundation PR #738 feedback and the October production-audit handoff were read.
This review does not claim access to its remote Codespaces audit code or source
manifest, and the new tool has its own explicitly versioned plan format.

Root also ran the composed migration-to-browser workflow: a new versioned
synthetic plan, explicit index preparation, apply, idempotent resume, owned
gallery preview, EXIF Artist/Copyright attribution, and byte-exact original
download all passed. The prior ten gallery checks passed in the same composition.
This separate root-run test completed in 6.41 seconds; its log and composition
manifest are retained outside the implementation trees. No production operation
was involved.

## Publication CI follow-up

The first published commit, `6dec01f1e667f42f0f894ac09f199cf8c9af4727`,
matched all 40 reviewed file hashes. Its Python 3.11 CI run exposed a test-only
portability error: the invalid-URI test required the existing test database URI
to use `127.0.0.1`, while CI uses `localhost`. The corrected test captures the
original URI and asserts exact preservation after the invalid alternate URI.

The independent reviewer inspected this isolated change and reran it using the
CI hostname: one test passed in 0.07 seconds without a MongoDB process. The
author also verified both hostname spellings. No migration production code
changed. The two inherited persistence validation corrections are reviewed in
the persistence follow-up; final dependency composition and CI remain gates.
