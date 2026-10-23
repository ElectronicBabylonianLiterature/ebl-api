# Media v5 review log

## Scope and authority

The user requested the attached v5 orchestrator for all four media PRs, fixes
using agents, and commits/pushes under their account. The standing instruction
leaves CI unmonitored. The invoked protocol delegates full suites to CI and uses
targeted local checks, overriding repository full-suite timing for this review.
No production migration, indexes, deployment or PR merge is authorized.

## Preparation

- Inspected the attached ZIP without executing its contents and extracted
  validated paths.
- Read the v5 protocol, record schema/checker and current repository
  instructions.
- Pinned head, base, merge base, parents and changed paths before source review.
- Initial combined tool output was truncated; reread the protocol in bounded
  sections.
- Created task records before substantive source inspection.

## Review and verification

Independent discovery, adjudication and scoped correction verification are
complete. Historical test results remain context, not new-review evidence.

- Verified all kit manifest hashes and current tool/dependency versions.
- Collection preflight showed Jest can echo a requested nonexistent path;
  checked file existence and repeated with the actual fragmentarium path before
  dispatch.
- Captured complete paginated published feedback separately for post-discovery
  closure; no CI polling.

- Dispatched six fresh-context discovery reviewers (runtime, tests, operations,
  maintenance, invariants, presentation) using hashed isolated role packets.
  They may use shared infrastructure, but no prior conclusions or feedback.
- Feedback closure inventory verified contiguous paginated receipts and all
  inline comments represented by thread data; dispositions await frozen
  discovery and fresh adjudication.
- Initial API+migration merge-tree succeeds without conflicts (tree
  `85b4f37506e5c5ba02e66f1ffdecd0e45e6f8210`); no integration branch or remote
  mutation made.

- Renamed this review task trail with a branch-specific scope before commits,
  preventing unrelated task files from conflicting during dependency
  integration.

## C-F01 authorized implementation

- Root released the API worktree at `6538ac0203471c987758d60aa8a2dec33317b446`
  for the adjudicated projected authorization lookup. Read the current backend
  instructions and the v5 COMMON/Role I protocol before implementation.
- Inspected C's retained real HTTP finding and canonical fragment lookup,
  repository scope API, scope deserialization, and media request consumers.
  Existing `fetch_scopes` deliberately returns no scopes for a missing fragment;
  media authorization needs an existence-enforcing operation instead.
- Combined initial reads were truncated and were repeated in bounded sections.
  Several guessed source/probe paths did not exist; corrected them with `rg`.
  One artifact-reading command ran Poetry outside a project and failed before
  execution; reran from the API worktree. No source changed during those reads.
- The implementation preserves current full-hydration callers, legacy scope
  lookups, canonical MuseumNumber filtering, missing-fragment errors, and
  fail-closed malformed scopes. No persistence index/binary modules are owned
  by this task. Root owns commits and pushes; no production operations occur.
- Added the real Mongo command-monitor regression before production edits.
  Its exact one-node collection matched the expected set, then execution failed
  as intended: public media list authorization performed a fragment aggregate
  instead of the expected single projected find. Retained the failing output
  and commands under `media-review-v5/roles/i_api` outside tracked source.
- Added `query_read_scopes` to the repository contract and Mongo implementation.
  It uses the canonical museum-number filter, projects only authorized scopes,
  preserves the exact missing-fragment error and uses the existing ScopeField
  list deserialization. Media routes now use it; no other callers changed.
- All 47 explicitly collected scope/repository cases passed. The actual HTTP
  probe then passed 39 requests through real media routes and Mongo/GridFS:
  the 14-request gallery used 14 projected fragment finds, zero fragment
  aggregates and zero bibliography/findspot/join hydration. Restricted, allowed,
  missing, cross-fragment and malformed-scope controls retained their expected
  responses. This is synthetic local evidence, not measured production latency.
- The first HTTP probe omitted Auth0User's required profile factory and failed
  in its synthetic principal middleware after the public gallery passed. Kept
  that output, supplied the required local profile factory, and reran the full
  probe successfully. Production authentication code was unchanged.
- Pyright rejected direct invocation of an abstract method in the contract
  regression, including through a local reference. The test now obtains the
  abstract implementation from the class namespace to explicitly verify its
  fail-closed stub; Pyright passes without suppressions or configuration
changes.
- Previewed 115 candidate focused nodes, reviewed their scope, and selected 89
  relevant authorization, binary integrity, runtime, and repository
compatibility
  cases. The final runner rechecks the exact expected node set before executing
  the identical selection with unique coverage output. Full suites remain in CI.
- The 89-node run passed. Coverage confirmed the authorization changes and
  resources were covered, while seven untouched lines in the existing extended
  reader needed compatibility cases. Added focused empty-review-list, OCR-sign,
  and successful folio-navigation tests to cover those existing reader paths.
- Coverage also showed abstract stubs are already excluded by the established
  coverage behavior. Replaced the newly introduced, unnecessary stub-invocation
  test with a real control: scope projection can read valid scopes while the
  unchanged full-detail query still rejects unrelated invalid fragment content.
  No pre-existing test was removed or disabled.
- The six explicit repository delta tests passed, with actual JUnit testcase
  IDs matching the exact collection preview. Combined production coverage is
  174 of 174 statements, 100%, across all three changed production modules.
- All six final Python files pass whole-project formatting/Ruff/Pyre, scoped
  Pyright/Mypy/Flake8, and qlty with tests included. Whole Pyre used the shared
  heavy-gate lock; no tool installation or checker configuration changed.
- A final explicit 92-node run retains fresh coverage, preview node IDs, actual
  executed JUnit IDs, exact arguments and changed-source hashes. This replaces
  count-only execution evidence for the final implementation without running
  the full suite. Root owns the subsequent independent verification and push.
- Packaging caught a preparation-order lapse: current backend instructions and
  COMMON/Role I were read before implementation, but the case manifest and
  ancillary coverage/workflow/configuration inventory were verified late.
  Read all seven PR786 instruction/configuration files and verified their exact
  hashes against the supplied pin. No drift or additional unmet constraint was
  found; this is retained as a protocol-order incident, not backdated
preparation.
- Final authoritative execution passed all 92 selected tests in 128.76 seconds.
  Expected, collected, and actual JUnit testcase IDs match exactly. Fresh
  coverage is 174 of 174 statements, 100%, for every changed production module.
  All six changed Python file hashes match the pre-run snapshot. Source digest:
  `f23abf4ef2036da4a64507c02e891d86cb544c7d15de93e3969b64ee81e5ca07`.
- Markdown initially rejected overlong lines in the prework task records and an
  added TODO item. Wrapped those documentation lines without changing content;
  the final Markdown check is repeated before handoff. No Python changes follow
  the authoritative run. Independent V and publication remain root-owned.

## Exact parent integration

- Root authorized integrating parent
  `86957afbac52b403716b4e905e0d76a61845332a` into API head
  `6538ac0203471c987758d60aa8a2dec33317b446`, leaving an uncommitted merge.
- Read the current backend instructions in full. Existing API changes are six
  frozen Python files plus review task records. No production operation or
  remote publication is part of this task.
- Initial broad artifact discovery produced excessive truncated output; used
  a bounded role-directory inventory to locate the exact manifests instead.
  Combined follow-up reads also truncated; relevant sections are reread in
  bounded outputs before use. These were read-only inspection incidents.
- Independent backend verification records C-F01 as verified fixed with no
  new findings. Final integration and publication remain root-owned.

### Integration steps

- Copied all ten modified/untracked files into an explicit external backup,
  retaining hashes, status and patches. Verified all six API source files and
  all eight published parent commit blobs against their frozen manifests.
- Preserved changes in stash `70ff87eabc3f153c7a3a9590270b86a3f54c7875`, then
  ran the authorized nonrewriting merge with `--no-ff --no-commit` and restored
  that exact stash object. No conflict occurred; README merged automatically.
- HEAD remains the original API revision and MERGE_HEAD is the exact published
  parent. Both source manifests remain byte-identical after integration.
- Selected 20 bounded controls covering all media endpoint forms, public and
  restricted scopes, missing and unrelated fragments, malformed stored scopes,
  canonical repository lookup, real HTTP/GridFS, index preparation, WebP pixel
  limits, animated WebP and truncated/complete JPEG storage. The runner will
  reconcile exact preview nodes and actual executed JUnit IDs.

- Root requested consolidation of the temporary integration task records.
  Copied both complete files into the external implementation artifacts with
  hashes before folding their content into this branch-specific review trail.
  No unique evidence was discarded; parent task records are unchanged.
- The exact composed 20-node collection and execution passed in 23.72 seconds;
  the wrapper exited zero. Actual JUnit testcase IDs equal both the expected
  and collected sets. The selection includes real HTTP and Mongo/GridFS,
  every endpoint form, scope/existence controls, image validation and index
  preparation. No full suite was repeated and CI remains unmonitored.
- Added the required review template with numbered What Has To Be Done.
  Scoped repair verification is complete; root still owns final structural
  records, feedback closure checks and publication. All source bytes remain
  frozen; there was no source edit or conflict resolution during integration.
- Final source equality verifies six API files, eight parent files and all
  three parent task records. Markdown checked 22 documents with zero errors;
  tracked and staged whitespace checks passed. npm emitted existing environment
  option notices, not Markdown diagnostics. Final staging retains the two
  exact merge parents and is handed to root without a commit or push.
