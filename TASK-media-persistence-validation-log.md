# Media persistence validation follow-up log

## Scope

Address concrete Sourcery findings on PR #785: persisted source-key validation,
an explicit raster pixel bound, and meaningful partial-upload cleanup coverage.
The coordinator and independent reviewer confirmed these issues. Intentional
SVG rejection and deterministic test identifiers remain unchanged.

## Progress

- Read the affected source and tests before editing and created task tracking.
- An overly broad scratch-file inventory included MongoDB data files and
  produced truncated output. Further reads will target named source files.
- The existing source validator checks only documents already containing a
  source key, so missing keys and keys inconsistent with importSource escape it.
- Annotation code globally disables Pillow's pixel limit; owned raster
  validation therefore needs its own explicit bound.
- The current upload failure test raises before writing any GridFS content.
- The reviewer found no public replacement/deletion routes in this rollout;
  future concurrent-reader cleanup coordination will be documented.
- A guessed source-domain filename did not exist; a targeted search located
  MediaImportSource in the existing domain module, which remains unchanged.
- Source preparation now validates every stored importSource and requires its
  canonical key before comparing reservation owners. Missing, orphaned,
  mismatched, malformed, and duplicate identities fail before index writes.
- Owned raster writes enforce 40,000,000 pixels independently of global Pillow
  settings, matching the migration policy. Borrowed originals still use the
  audited adoption path without pixel decoding.
- Cleanup regressions now leave actual orphan chunks or a complete GridFS file
  before raising, then verify removal while preserving an unrelated file.
- README documents source consistency, the pixel cap, and future reader/cleanup
  coordination. Intentional SVG rejection and deterministic IDs remain intact.

## Verification

- Focused media suite: 456 tests passed in 9.45 seconds, with all 507 affected
  production statements covered, 100 percent.
- Repository formatting and lint, scoped Pyright, mypy, Flake8, Qlty with tests,
  and Markdown checks pass. Whole Pyre also passes after the correction below.
- Six source/test paths and their final hashes are recorded in the parent
  workspace at `media-verification/persistence-validation-frozen-hashes.json`.
- Whole Pyre found one test-only bytearray typing mismatch in the crafted PNG
  checksum. Converting its slice to bytes preserves the test input. The 13 tests
  in that file, all three type checkers, lint, formatting, and Qlty pass again;
  the final manifest has been refreshed for both dependent branches.
- A follow-up Flake8 invocation omitted the prescribed 120-character limit and
  reported default-width errors. The required invocation passes unchanged.
- A guessed Taskfile extension was absent; no task configuration was changed.
- Independent review passed all 74 infrastructure tests in 9.17 seconds. Its
  unchanged adversarial probe confirms missing and mismatched keys are rejected,
  and the raster cap survives importing the real annotation service.
- Final full suite: 6,025 passed, two existing skips, and one existing expected
  failure in 694.25 seconds, wrapper exit zero. It ran against an isolated
  replica set with `poetry run pytest -q -x -n 2` through the verification wrapper.
- All six source/test paths still match the manifest used by both dependent
  branches. The largest touched Python file contains 204 lines.
- Repository instructions were re-read and all applicable gates were honored.
  No production data access, migration, commit, or push was performed by this
  agent. The coordinator handles publishing and dependency integration.

Remove this temporary task file before merging.
