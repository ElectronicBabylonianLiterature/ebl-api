# Independent media persistence review

## Summary

No blocking correctness finding remains in the reviewed persistence code.
This is an implementation review, not approval to access production or migrate.

Reviewed base commit: `3602c2b8d71637369a9f25cd6d29293f57cc70e6`.
Reviewed changed-file digest after the primary-read preference correction:
`18fd3727165a186eb331e3959fac099fa5a1891daa789333050d5014368e0663`.
The digest includes changed tracked files and new untracked implementation/test
files, excluding temporary TASK documents. Final commit identity must be recorded
when the branch is committed.

## Findings

- Source uniqueness is reserved by complete typed identity, not filename or hash.
  Reservation updates and all metadata mutations share a transaction lock.
- A three-way source swap and a late conflicting replacement were exercised on
  real MongoDB. The conflict rolled back the earlier replacement completely.
- Tombstones retain source ownership. An older deletion completion cannot remove
  a newer otherwise-identical deletion generation.
- Exact logical handles bind media, representation, and role. Forged handles
  cannot open or delete another logical representation.
- Two borrowed handles referencing one physical legacy original were exercised.
  Deleting one preserved both the original bytes and the other readable handle.
- Concrete adapters now force primary reads, including immediate registry
  verification after adoption. This avoids inherited secondary-preference lag.
- Existing legacy maintenance commands remain capable of deleting legacy bytes.
  The README states this boundary and requires preserving adopted originals.
- SVG storage fails closed; the current adapter supports raster writes only.
  The README documents this explicitly.

## Severity

No open blocking finding in this branch. Deployment prerequisites and unfinished
publication feedback checks below remain operational requirements.

## Reproduction Steps

The independent reviewer ran the infrastructure directory against a disposable
MongoDB replica set: **60 tests passed in 8.01 seconds**. A separate scratch probe
also passed real source swaps, rollback, tombstone generations, shared borrowed
byte protection, and forged-handle isolation.

These checks accessed only synthetic local test databases. No production
credentials, database indexes, source files, or migration records were changed.

## Recommendation

Publish after the repository-required full test and static-analysis gates pass.
Keep index preparation explicit and require transaction-capable MongoDB before
any metadata mutation. Preserve the first-merge dependency documented in README.

## What Has To Be Done

1. Record the committed SHA and reconcile any changes after the reviewed digest.
2. Author verification is complete: 6,011 full-suite tests passed, with two
  existing skips and one expected failure; 442 focused media tests passed and
  changed production code has 100 percent line coverage. Static gates pass.
3. Fetch all new PR timeline comments, review submissions, and inline threads
  after first publication and address actionable feedback before final handoff.
4. Remove temporary TASK documents according to repository policy before merge.

Merged foundation PR #738 feedback was fully fetched: 39 timeline entries,
16 reviews, and 22 threads. All threads were resolved; the latest human review
approved it. Current-state Mongo transactions, typed source uniqueness, and
storage ownership were independently checked rather than inferred from its
in-memory foundation tests.

## Publication follow-up

PR #785 at `e5c3eee2836029761fa677516c37f09cdf16535d` matched the reviewed
implementation. All available timeline comments, reviews, and threads were read.
CodeQL then reported four side-effecting assertions and one empty exception
handler in test infrastructure. No production-code finding was reported.

The six-file correction moves mutating calls outside assertions, including
analogous adoption and concurrency cases. Replica-set startup now preserves the
last connection error as the bounded-timeout cause, with a regression test.
Production code is unchanged. The independent reviewer inspected the full diff
and reran the infrastructure suite: **61 tests passed in 6.88 seconds**.

The reviewed 22-path digest remained stable during that run:
`70d0d97c632e25f16115fbbc703c7278338d150d8efd265c9bfb19cf296c0d90`.
The author also reports 443 focused media tests passing, 100 percent production
and replica-set-helper statement coverage, and passing static gates. The full
repository follow-up suite remains an author-owned publication gate. The final
follow-up commit and its remote CodeQL result still require reconciliation.
