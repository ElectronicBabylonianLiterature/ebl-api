# TASK realia-detail-500 — Log

## 2026-09-23

- Created TODO and log first. Origin: finding R4 in the PR #735 review;
  user asked for a new PR instead of an issue.
- Branched `fix-realia-detail-unloadable-entries` from `origin/master`
  (`cd46110c`).
- Reproduced on master code (port 8740, DB `ebl_review_f4`, never `.env`):
  `/realia/Anu` 200; `NullType` (`type: null`), `NullRealiaId`
  (`realiaId: null`), `BadElement` (`relatedTerms: [5]`) all 500 via the
  generic `unexpected_error` handler. Server stopped; DB kept for
  re-verification.
- **Error I made:** tried to wait with a foreground `sleep`, which the
  harness blocks; killed the server directly instead.
- The fix is a design choice; asking the user before implementing.
- User chose "Tolerate null".
- `RealiaEntrySchema.treat_null_as_absent` (`@pre_load`): drops top-level
  `None` values so they load like missing fields (`load_default`). Non-dict
  input passes through unchanged. `_id: None` is still rejected (required),
  wrong-shaped elements still fail.
- New `ebl/tests/realia/test_realia_null_fields.py` (55 lines): schema load
  per nullable field, `_id: None` rejected, non-mapping passthrough, wrong
  element still rejected, route 200 per nullable field. Without the fix:
  18 failed / 3 passed; with it: 21 passed.
- **Error I made:** first version tested `load(["Anu"])`, which pyre and
  pyright reject as a type error; replaced with a direct call of the hook.
  Also first wrote a `client` fixture override; replaced with explicit
  seeding in the test.
- pyright found 2 pre-existing errors in the touched `realia_schemas.py`
  (`ReallexikonReferenceField._serialize`/`_deserialize` named the
  parameter `attr_name`, base class uses `attr`). Fixed by renaming to
  `attr`, matching `ebl/schemas.py`.
- Gates: format 0 (no changes), lint 0, pyre no errors, pyright on the two
  changed files 0 errors, flake8 0, mypy 0 errors in changed files,
  coverage `realia_schemas.py` 100% (89 stmts), new test file 100%.
- Runtime on the final tree (port 8742, DB `ebl_review_f4`): `Anu` 200,
  `NullType` 200 (`type: []`), `NullRealiaId` 200 (`realiaId: ""`),
  `BadElement` 500 (out of scope, as agreed). Server stopped, DB dropped.
- **Error I made:** an earlier `pgrep -f ... | xargs kill` matched my own
  shell (exit 144) because the same command line contained the pattern;
  statuses from that run were not captured, so I re-ran the check cleanly.
- Full suite on the branch: 4853 passed, 2 skipped, 1 xfailed, exit 0.
  lint-md on the whole repo: 0 errors. All gates pass. Nothing committed;
  waiting for approval to commit, then to push, before opening the PR.
- Committed `19dad310` (user-approved, fix files only). Not pushed; PR not
  opened.
