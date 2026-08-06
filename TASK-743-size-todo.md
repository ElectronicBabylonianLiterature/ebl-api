# TASK-743-size — TODO

Split every `.py` file **touched by PR #743** that exceeds the 250-line hard
gate. **No commits** — the user reviews first.

## Constraints

- All three type checkers stay green: `task type` (pyre, CI-enforced),
  `task type-pyright`, `mypy`.
- No suppressions: no `# type: ignore`, no `# noqa`, no lint/formatter config
  changes.
- Behaviour must be preserved exactly. Public import paths that other modules
  rely on must keep working.
- Never remove or weaken an existing test.
- 100% coverage on every line added, modified, **moved or relocated** — moving
  an uncovered line makes covering it my responsibility.

## Files to split (measured on the current working tree)

- [x] `ebl/tests/factories/fragment.py` — 718
- [x] `ebl/transliteration/domain/tokens.py` — 368
- [x] `ebl/fragmentarium/retrieve_annotations.py` — 323
- [x] `ebl/corpus/web/chapter_schemas.py` — 286
- [x] `ebl/transliteration/domain/sign_tokens.py` — 278
- [x] `ebl/transliteration/domain/enclosure_visitor.py` — 268

Not in scope: the 40 other files over 250 lines that PR #743 does not touch.

## Per-file procedure

- [x] Record the public names other modules import from the file
- [x] Choose a real seam, not an arbitrary line cut
- [x] Move code, keep every existing import path working
- [x] Re-run the file's own tests immediately after the move

## Final gates

- [x] `task format`
- [x] `task lint`
- [x] `task type` (pyre)
- [x] `task type-pyright`
- [x] `task test`
- [x] coverage on changed/moved modules
- [x] `flake8 --max-line-length=120` on changed modules
- [x] `mypy --ignore-missing-imports` on changed modules
- [x] `task lint-md`
- [x] Runtime verification of the running service
- [x] Confirm no PR-touched `.py` exceeds 250 lines
- [x] Report; **nothing committed**
- [x] Remind to remove all TASK docs before the PR is merged
