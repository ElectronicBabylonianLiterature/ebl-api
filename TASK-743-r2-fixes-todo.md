# TASK-743-r2-fixes — TODO

Address every finding in `TASK-743-review-r2-review.md` on PR #743
(`fix-type-checker-blind-spots`, head `aed3979f`).

## Gates to honour

- [x] Re-read `.github/instructions/copilot.instructions.md` before
      reporting complete; state which gates ran and their results.
- [x] **No commit, push, merge, rebase or reset** unless the user asks
      for that exact action in that message.
- [x] **No test removal** without explicit user approval — F4 needs it.
- [x] No lint/format/type config changes; no `type: ignore`, `noqa`,
      `pyright: ignore` or `pragma: no cover` to close a finding.
- [x] Mixed-array hard gate on every data-shape change.
- [x] 250-line limit on every `.py` file touched.
- [x] 100% coverage on every line added, modified, moved or relocated.
- [x] Verify against the **running backend service**, and re-verify from
      scratch after any rewrite.
- [x] `task lint-md` clean.
- [x] Keep this TODO and `TASK-743-r2-fixes-log.md` updated as each step
      completes.

## Blocked — resolved by the user

- [x] **B1 (F1).** Fixing the conflict properly wants
      `git merge origin/master`, which the commit/push hard gate forbids
      without the user's own words. Mitigation that needs no merge:
      replay #749's six `TYPE` abbreviations and master's `docs/ebl-atf.md`
      addition onto the branch, so both sides become identical and a
      "keep ours" resolution can no longer lose them. **User chose to
      run the merge; done with `--no-commit`.**
- [x] **B2 (F4).** Removing `_StartParser.__getattr__` means deleting
      three tests that exist only to cover it. **User chose to keep
      them; only the dead `start` parameter was removed.**
- [x] **B3 (F13).** Deleting the six committed `TASK-743-*.md` tracking
      files is a merge-time action. **User chose to keep them until
      merge.**

## Findings to fix

- [x] **F2** — `task type-pyright` to zero, structurally.
  - [x] `signs/web/signs.py` (3): declare `find_signs_by_order`,
        `get_unicode_from_atf`, `list_all_signs` on the `SignRepository`
        ABC; handle `svg2png` returning `Optional[bytes]`.
  - [x] `signs/infrastructure/mongo_sign_repository.py` (6): cast at the
        marshmallow boundary, as the PR already does elsewhere.
  - [x] `tests/corpus/test_chapter_manuscript_schemas.py` (6): stop
        subscripting a possibly-`None` load result.
  - [x] `transliteration/application/token_schemas_signs.py` (2):
        annotate `_dump_name_parts` / `_load_name_parts` properly.
  - [x] `signs/infrastructure/sign_unicode_lookup.py` (2): fixed by F3.
  - [x] `fragmentarium/application/annotations_service.py` (1 warning):
        replace `len(x) and f(x)` with a real conditional.
- [x] **F3** — replace `getattr(part, "name_parts", [])` with
      `isinstance(part, NamedSign)`; annotate `word` and `result`.
- [x] **F4** — remove the unused `start` parameter from
      `_StartParser.parse` (safe, no test touches it). `__getattr__` is
      B2.
- [x] **F5** — wrap the 169-character URL comment at
      `annotations_service.py:140`.
- [x] **F6** — restore the five `PRIVATE_COLLECTION_*` entries to
      3-tuples and widen the `MuseumEntry` alias accordingly.
- [x] **F7** — add a focused `SignsVisitor.reset()` test: accumulate a
      real result, assert non-empty, `reset()`, assert empty.
- [x] **F8** — qlty: remove the 46-line duplication between
      `lemmatized_fragment_text.py` and `transliterated_fragment_lines.py`
      by deriving one from the other. The parameter-count and
      return-count findings are relocated code; record a rationale
      rather than restructuring working code for a metric.
- [x] **F11** — no action; note only.
- [x] **Extra** — a live 500 on erasure transliterations, found while
      verifying F3, fixed and pinned by a new route test.
- [x] **F12** — type hints on the new module-level functions; replace
      the bare `Callable` in `annotations_service.py`.

## Verification

- [x] `task format`, `task lint`, `task type` (pyre),
      `task type-pyright` (must be **0**), `task test`.
- [x] Coverage: 0 uncovered lines among lines this task touches.
- [x] `flake8 --max-line-length=120` and `mypy --ignore-missing-imports`
      on changed modules.
- [x] 250-line limit on every changed `.py`.
- [x] `task lint-md`.
- [x] Re-run the runtime smoke against the rewritten tree: the signs
      transliteration route (200 and 422), markup, fragment query,
      the three dispatcher keys and the dispatcher error path.
- [x] Update `TASK-743-review-r2-review.md` with the resolution of each
      finding.
- [x] Report: gates run, results, and that nothing was committed.

## Outcome

Every finding addressed except the two the user chose to leave (F4's
`__getattr__` proxy, F13's tracking files) and F11, which was a note.
All gates pass, including `task type-pyright` at **0 errors** — the gate
that was failing. Nothing committed; the `origin/master` merge is staged
but uncommitted.
