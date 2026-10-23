# Media persistence work log

## Scope

Implement production media persistence on the existing application contracts.
No production database access, migration execution, deployment, or merge is in
scope. The coordinator owns committing and publishing the branch.

## Progress

- Read all repository instructions before implementation.
- Created task tracking files before changing source code.
- Verification tooling is being prepared by the environment agent.
- Implemented MongoDB state encoding, scoped/batch reads, and transactional
  writes serialized through a shared write lock. Source reservations use a
  separate collection so atomic source swaps do not reuse unique index keys
  inside a transaction.
- Added a server-only deletion token to distinguish otherwise identical
  deletion generations, retaining source reservations while cleanup is pending.
- Implemented typed legacy source identities, protected adoption, bounded
  raster validation, new-version writes, and exact-handle deletion. Pending
  owned writes remain visible in the registry for recovery after interruption.
- Added explicit index preparation and replica-set CI setup. Constructors and
  reads do not initialize collections or indexes.
- First isolated transaction suite: 12 tests passed. Expanded storage suite:
  54 tests passed; all new storage modules reached 100 percent line coverage,
  with only the standalone-topology rejection awaiting its dedicated test.

## Corrections during development

- An initial inspection used an incorrect existing module filename; the actual
  store contract is `media_store.py`.
- Initial selection helper names were corrected to the existing exported
  functions before tests.
- One multi-file patch had malformed patch syntax and was rejected without
  changes; it was reapplied in smaller valid patches.
- Pyright identified two deliberate invalid-input test arguments and a
  temporary-file protocol mismatch. Explicit test casts and the existing
  binary stream protocol resolved these without suppressions.
- Pyre requires local variables for optional attribute narrowing; checksum
  and import-source reads now use locals.
- Mypy encountered a sandbox process-visibility failure in optional psutil.
  The environment agent provided the same checker version in an isolated
  environment without psutil, retaining dependency discovery through the
  project interpreter.
- Independent review identified inherited secondary read preferences;
  transactions now explicitly use primary reads.
- Qlty identified the adoption helper's long argument list. Replaced both
  construction and adoption signatures with a shared frozen request object,
  matching existing representation write-request patterns. Dependent migration
  work was notified and updated.
- Markdown lint caught one long table row and an extra blank line. Shortened
  the table label and removed the blank line; the full Markdown gate passes.
- Historical foundation feedback prefers existing documentation. Operational
  material is now in README rather than a new permanent Markdown file.
- The first full-suite attempt exposed missing dummy application settings
  (`EBL_AI_API`) in the test environment. The environment agent supplied CI-like
  dummy settings; no production configuration was used.
- A serial full-suite rerun was interrupted after the environment agent fixed
  the test MongoDB file-descriptor pressure. The replacement run uses the
  tuned disposable replica set and four pytest workers.
- Final self-review extended primary reads to the repository and storage
  constructors, preventing stale registry reads immediately after adoption.
  Explicit secondary-preference integration tests verify both adapters.
- The final full-suite attempt stopped after 611 passing tests when the local
  MongoDB stopped responding during fixture index creation. No application
  assertion failed. Concurrent broad suites increased the environment's OOM
  counter; the environment agent is preserving failed server logs and the
  coordinator will serialize the retry to reduce memory pressure.
- One verification command ran Ruff formatting outside the repository task's
  `ebl` scope and reported two untouched devcontainer files. The mandated
  `task format` and `task lint` both pass. Another Flake8 invocation omitted
  the mandated 120-character limit; rerunning with the required option passes.
- The serialized full suite reached 4,289 passing tests and two existing skips
  before bootstrap downloaded another MongoDB platform build whose executable
  bit was missing in the environment. The environment agent repaired the
  executable and installed its official platform OpenSSL dependency locally.
  The sandbox also prevents MongoDB's process-metric health query from reading
  its PID in `/proc`; the coordinator approved adapting only the installed
  pymongo-inmemory readiness check to real `ping` and `buildInfo` commands.
  The original installed code is backed up. All four unchanged bootstrap tests
  now pass against real MongoDB. No repository dependency, source, assertion,
  lockfile, or CI change was made for these environment adaptations.
- Final documentation verification caught an overlong command line; the
  command now uses the equivalent relative wrapper path. A review-file patch
  initially expected bullets where the reviewer had numbered the steps;
  inspecting the current file and matching its numbered list resolved it.

## Verification status

- Final focused suite: 442 tests pass, including real MongoDB transactions,
  GridFS, concurrency, and existing media contracts.
- Changed production modules: 487 of 487 statements covered, 100 percent.
- Repository-task Ruff format, Ruff lint, and whole-project Pyre pass.
- Changed-file Pyright, mypy, and Flake8 pass with no suppressions.
- Qlty with tests included reports zero findings.
- Full Markdown lint and git whitespace checks pass.
- Independent review found no blocking persistence/ownership issue; 60 final
  infrastructure tests pass with the source digest stable throughout the run.
- Final full backend suite: 6,011 passed, two existing skips, one existing
  expected failure, zero failures, in 614.44 seconds. The source remained
  unchanged throughout the successful run.

## Final verification commands

The local wrapper starts a disposable MongoDB 7.0.2 replica set, sets only
synthetic test configuration, and cleans up the server and test processes.
Environment adaptations described above affect only the sandbox tooling.

```shell
source /workspace/scratch/47d0bc03bced/media-verification/environment.sh
poetry run python ../media-verification/with-mongo.py \
  poetry run pytest -q -x -n 2
```

The full-suite log is
`media-verification/persistence-full-suite-final-02.log` in the parent workspace.
Focused coverage used the same wrapper with `pytest ebl/tests/media -q`,
`--cov=ebl.media.infrastructure`, `--cov=ebl.media.application.media_stored`,
and `--cov-report=term-missing`.

All final Python files are at most 250 lines. Final Markdown and whitespace
checks include all three mandatory task documents. The coordinator may now
make the first commit and open the PR, then reconcile its new GitHub feedback.
No commit, push, production access, index preparation against production,
migration execution, deployment, or merge was performed by this task agent.

## Merge preparation

Remove the task TODO, log, and review files before merging, after preserving
operational instructions in the PR description or durable repository docs.
