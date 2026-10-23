# Media migration tooling work log

## Scope

Implement PR 3 on `media/backend-03-migration`, depending on the persistence
branch. The user explicitly excludes running the production migration. Root
owns commits, publication and pull requests; this worker does not perform them.

## Progress

- Read `.github/instructions/copilot.instructions.md` completely.
- Created this log and the task checklist before source edits.
- Verification must use synthetic data in a disposable local database only.
- The complete historical audit manifests live in a separate Codespace; the
  local October audit report supplies evidence, not an invented manifest schema.

## Implementation

- Added a separate v1 JSONL migration plan and apply CLI with explicit database,
  source-write pause acknowledgement, deterministic typed source identities,
  primary source reads, full byte hashes and source revalidation.
- Planning performs no database writes or index creation. A separate explicit
  prepare-indexes command initializes the required indexes and transaction lock.
- Original imports borrow protected legacy handles; generated display and
  thumbnails use the owned media bucket. Existing legacy thumbnails are unused.
- Preserved EXIF Artist/Copyright evidence by default without inventing rights.
- Resumable durable journals bind target, policy and plan checksum; staged owned
  handles allow retry after ambiguous metadata acknowledgements without deleting
  files referenced by committed records.
- Root authorized temporary PR 1 dependency copies for local validation, tracked
  by SHA-256 in the scratch dependency-overlay-migration.json manifest. These are
  not owned changes and must not be committed with this branch.
- Review fixed a case-insensitive duplicate lookup that could scan the collection
  per original: the query now uses a case-sensitive canonical prefix and a required
  filename-leading index.
- Review fixed malformed JPEG handling: bounded originals receive pixel decoding;
  larger JPEGs explicitly record structural-only validation and deferred previews,
  without disabling Pillow's global safety limit.
- Review fixed apply preflight so missing indexes/transaction coordination fail
  before any adopted-handle registration.

## Verification

- 61 focused tests passed on disposable local MongoDB before the latest review
  changes; changed-code coverage was 96%. Additional parser/recovery coverage and
  full quality gates are in progress.
- Scoped mypy and Pyright passed. Pyright initially used the wrong interpreter;
  rerunning with --pythonpath .venv/bin/python corrected environment resolution.
- Initial GridFS length checks incorrectly rejected BSON Int64; a failing test
  exposed the issue and checks now accept int subclasses while rejecting bool.
- Whole Pyre exposed optional-value narrowing and Pillow stub differences; fixes
  are included and the full check will be rerun.
- Qlty identified parser/journal complexity and test argument counts; refactoring
  splits parsing responsibilities without weakening repository configuration.
- No production database, legacy files or running application was accessed.

## Final implementation review

- Added whole-plan schema validation before the first apply write, including
  missing policy fields, malformed later rows and boolean numeric limits.
- Required explicit source-write pause acknowledgement for apply. A fresh paused
  inventory is still necessary because completion covers the bound plan only.
- Staged reconciliation follows the current source owner even when a concurrent
  importer used a different media ID, while protecting referenced handles.
- Added the operator guide to the existing README. It describes merge/deploy
  order, exact commands, all indexes, protected originals, primary/credit policy,
  preview deferral and pending/ready registry crash windows. It explicitly
  distinguishes this migration planner from the historical complete binary audit.
- Reviewed the root-owned PR description. Clarified that index preparation creates
  reservation structures, while imports create reservations; qualified production
  exclusions and documented that retries do not add previews to existing records.
- No Python source or test file exceeds 250 lines: 29 owned files, largest 173.

## Final focused gates and error recovery

- Latest focused isolated-MongoDB run: 111 passed in 11.67 seconds; all 814
  statements across the 15 changed source modules have 100% line coverage.
- Whole repository `task format` and `task lint`: pass.
- Whole Pyre with two workers: zero errors. The worker bound avoids exhausting
  the shared verification container and does not change type-checking rules.
- Scoped Pyright, Flake8 and Qlty including tests: zero errors/findings.
- Mypy checked all 29 owned source/test files successfully. A final repeat hit
  mypy 2.4's optional psutil CPU-affinity discovery bug: `NoSuchProcess(pid=2)`
  in the execution namespace. A fresh cache reproduced it. The supported
  `--no-native-parser` mode avoided that runtime discovery path and completed
  with zero errors; no type-checking rule or repository configuration changed.
- `task lint-md`: zero errors after shortening three operator-table rows that
  initially exceeded the repository's 80-character Markdown line limit.
- Schema hardening initially introduced optional `.get` values rejected by mypy
  and Pyright. Explicit key reads with a normalized missing-field error fixed it.
- Flake8 exposed exception pickling and formatted slice issues. `SourceRejected`
  now preserves constructor arguments and its readable reason; test slices use
  named boundaries rather than conflicting formatter/linter whitespace.
- Pyre cannot resolve the installed pytest `CaptureResult` attributes or tuple
  access. CLI tests now capture output with explicit StringIO redirection during
  execution. The final focused suite and independent review were rerun after this
  test rewrite; no output assertions were removed or weakened.
- Invalid patch requests were rejected without changing files; correcting the
  update structure resolved them. Exploratory lookups of absent repository paths
  were corrected through file searches.

## Independent and runtime verification

- Independent review accepted the migration implementation with no blockers.
  Its final 111-test rerun passed in 11.08 seconds after the capture rewrite.
- The independent real-MongoDB rehearsal audited dry-run commands with zero
  writes, verified collection equality, rejected same-length byte tampering,
  withheld duplicates/missing bytes, retained legacy files and resumed safely.
- The malformed JPEG regression independently confirms that missing quantization
  tables are blocked under both preview policies without aborting the dry run.
- Root's composed migration-to-API-to-Chromium rehearsal passed: one test in
  6.41 seconds. It created a fresh synthetic plan, explicitly prepared indexes,
  applied and resumed idempotently, displayed owned previews and Artist/Copyright
  credits in the gallery, and matched original-download SHA-256 exactly.
  Legacy source bytes remained intact. The scratch log is
  `media-verification/migration-browser-runtime.log`.
- Final non-TASK independent-review digest before dependency integration:
  `a0dead33bfb0e6ed5e8e9a30d12c5909a8cf42f9c61c7b6ddd61b8b868adfa18`.

## Remaining release gate

- Final persistence integration, the filename-index correction, all quality
  gates and the full backend suite passed. The implementation is frozen for
  root-owned commits, push and PR publication.
- No production access, migration, index preparation or deployment occurred.
- Remove the temporary TASK TODO/log/review files before merging the PR, after
  retaining the operator instructions and useful verification evidence.

## Persistence integration and assertion review

- Root integrated published persistence PR 785 at
  `e5c3eee2836029761fa677516c37f09cdf16535d`. All nine dependency overlays were
  replaced by the actual parent commit; owned implementation/test hashes were
  unchanged and README integration was clean.
- Started the final two-worker full suite on 6,124 collected tests. Root then
  identified mutation calls inside assertions, analogous to a CodeQL finding in
  the persistence PR. The run was cleanly interrupted with exit 130 at about 27%
  without any reported failure. The interrupted log remains
  `media-verification/migration-full-suite-after-pr1-20261023.log`; it is not a
  passing full-suite result.
- Moved 23 migration apply, plan apply and CLI invocations out of assertions into
  assigned results across seven test files. An AST scan confirms those mutating
  invocations no longer occur inside assertions. No production source changed.
- The first mechanical edit lost continuation parentheses in two test files;
  Ruff rejected their syntax immediately. Restoring the comparison layout fixed
  the issue before executing tests; no rules or assertions were suppressed.
- Root overlaid six equivalent persistence test-only fixes, with unchanged old
  bytes verified against the parent commit. Their temporary overlay manifest is
  `media-verification/parent-test-followup-overlay.json`.
- Focused verification passed: 111 tests in 10.69 seconds, with all 814 changed
  source statements covered. Ruff, Flake8, Pyright, whole Pyre with two workers,
  mypy and Qlty including tests passed. The isolated mypy tool environment avoided
  the optional psutil discovery defect without changing type rules.
- Independent review confirmed the exact seven test diffs only moved 23 calls
  into assignments, preserving every assertion and operation order.
- The final two-worker full suite completed with exit 0: 6,123 passed, 2 skipped,
  1 xfailed in 650.37 seconds. Its log is
  `media-verification/migration-full-suite-final-assertions-20261023.log`.
  This includes the final six parent test overlays and precedes the index fix.

## Filename index correctness follow-up

- Root identified that a forced partial filename-index hint could omit competing
  originals and incorrectly make a duplicate eligible. Reproduction and a shared
  complete-index selector are required before publication; final verification
  will be repeated after this production correction.
- The selector must reject partial, hidden, sparse, non-simple-collation and
  non-B-tree indexes. Explicit preparation must create a complete simple-collation
  fallback without dropping or replacing an incompatible existing index.
- An exploratory read used a nonexistent test filename; a file inventory located
  the existing planning/preflight tests before further work.
- The regression failed against the earlier source: a partial index admitted the
  duplicated fragment without raising. Independent probes also demonstrated that
  a filename/geospatial compound index without a sparse flag hides competitors.
- Planning and preparation now share the complete-index selector. Duplicate
  queries explicitly use simple collation. Preparation creates an explicitly
  simple fallback even on a collection with a different default collation.
- Added regressions for read-only rejection and retained index/data state,
  competing-source withholding after explicit preparation, all unsafe index
  variants, valid B-tree indexes, default collation and an unsafe name collision.
- The first corrected focused run passed all 127 tests with 100% coverage.
  Qlty found a complex boolean expression in the selector; named predicates
  removed that complexity without changing its policy.
- The final corrected focused run passed 127 tests in 11.49 seconds with all
  824 source statements covered. Whole format/lint and Pyre with two workers,
  scoped Pyright/mypy/Flake8, Qlty including tests and Markdown lint passed.
- Root integrated actual published persistence follow-up
  `c844d2389e9d3f3680c1202f15625918fbe5b390` from PR 785. All 40 saved changed-file
  hashes were unchanged; the six temporary parent test overlays are now actual
  committed parent files.
- The API sibling is PR 786 and the dependency is PR 785. Root owns publication
  and the final dependency links; no production operations occurred.
- Independent review accepted the final correction: all 127 focused tests passed
  in 10.46 seconds, partial/geospatial omission probes were rejected safely, and
  the read-only planning rehearsal again recorded zero database mutations.
- The full suite on the exact committed parent and frozen migration source
  passed with exit 0: 6,139 passed, 2 skipped, 1 xfailed in 523.56 seconds. Existing
  deprecation/runtime warnings were reported; there were no test failures. Log:
  `media-verification/migration-full-suite-final-indexes-20261023.log`.
- The disposable local verification processes completed and were removed; no
  resource exhaustion occurred. Only task-documentation updates followed this
  final run. All migration, source-selection and runtime code remains frozen.
