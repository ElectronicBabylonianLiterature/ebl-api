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
