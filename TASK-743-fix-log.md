# TASK-743-fix Work Log — Address the findings of the PR #743 review

PR: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743>
Branch: `fix-type-checker-blind-spots` -> `master`
Started: 2026-08-16, from `55827af1` with a clean tree

## Entries

### 1. Task setup

New task, so new tracking files. `TASK-743-todo.md` / `TASK-743-log.md` belong
to the review task and do not carry forward.

Baseline before any edit: working tree clean apart from the four `TASK-743*.md`
files; all gates green as recorded in `TASK-743-review.md`.

### 2. F1 — duplicate `__all__`

Deleted the second `__all__` block in `ebl/corpus/web/chapter_schemas.py`. The
surviving list is the complete one and includes `ApiLineVariantSchema`.

### 3. F3 — CodeQL

- `signs_transformer.py`: `scan_values(lambda value: bool(value))` ->
  `scan_values(bool)`.
- `token_base.py`: `SignsCollectingVisitor.reset` and `.result_string` changed
  from `...` to `raise NotImplementedError`, matching `Token.value` and
  `Token.parts` in the same file.

### 4. F2 — `TextLine.merge`

Marked `TextLine` `@final`. The `cast(L, ...)` is now provable rather than only
true by accident: `@final` makes "`L` is bound to a `TextLine` subclass" —
Sourcery's failure case — impossible. Kept the cast; reverting the signature to
`Union[TextLine, L]` as Sourcery suggested would reintroduce the variance error
this PR removed.

### 5. F6 — `NamePart` delegation

I first planned to stop `NamePart` being a `Token`. Abandoned that: it would
have removed the code paths behind `test_parts_delegate_to_the_wrapped_token`
and `test_accept_delegates_to_the_wrapped_token`, and deleting tests needs
explicit user approval first. Took the other half of the recommendation instead
and completed the delegation — `clean_value`, `lemmatizable`, `alignable`,
`get_key`, `set_unique_lemma`, `update_alignment`, `set_enclosure_type`,
`set_erasure` and `merge` now all forward to the wrapped token. The `set_*`
withers rebuild through `NamePart.of`, so wrapper and inner token can no longer
drift apart. Added 10 tests; every added line is covered.

### 6. F4 — qlty

- `match`: seven returns -> two, via a `TYPES_MATCHED_BY_NAME` membership test.
  Also renamed the `type` local to `annotation_type` (builtin shadowing).
- `Logogram.of` / `of_name`: sixth parameter removed. `surrogate` moves to a new
  `Logogram.with_surrogate` wither, matching the existing wither idiom
  (`set_enclosure_type`, `set_erasure`, `update_alignments`). Four call sites
  updated.
- The three `test_named_sign_*` tests: 9/7/8 parameters -> 1, via a per-file
  `NamedTuple` case object.
- Verified with an AST scan that no function in the changed set is now over
  either threshold.

The similar-code pair between the two test factories is **deliberately left**.
See the review file for the rationale; it is also not in the current blocking
six.

### 7. F7 — `atf_importer` mypy errors, and where I stopped

Fixed three of the four files (four of the five errors):

- `lemmatization.py`: removed the two right-hand-side values from the
  `TypedDict`. Confirmed first that nothing reads them as class attributes —
  every access is by dict key, guarded by an `in` check.
- `logger.py`: `_write_log` now takes the directory as a parameter, so the
  `if self.logdir:` narrowing reaches it. This deleted a `# pyre-ignore[6]`.
- `atf_indexing_visitor.py`: imports `Tree`/`Token` from `lark.tree` /
  `lark.lexer`, and `cursor` is annotated `Dict[str, Optional[str]]`.

**`legacy_atf_transformers.py` is deliberately untouched.** Its one mypy error
is trivial, but any edit pulls the file into the `task type-pyright` scope,
where it has five more errors. Three of those are `self._transform_tree`,
`self.__visit_tokens__` and `self._call_userfunc_token` — Lark internals that
exist at runtime but are missing from the `lark-stubs` `visitors.pyi` that ships
with lark 0.12.0. Clearing them needs either a suppression (banned), a shim
declaration, or reimplementing Lark's private dispatch. Left it; reported.

### 8. Errors I made and how they were caught

1. **Fixing the imports in `atf_indexing_visitor.py` exposed five new pyright
   errors** — once `Tree` resolved, pyright could finally see that
   `tree.children[i]` is `str | Tree`. Fixed properly: `int(str(...))`, an
   inverted `isinstance(child, Tree)` narrowing, and two `cast(Tree, ...)` at
   the Lark boundary (the pattern this PR already uses in `lark_parser.py`).
2. **pyre crashed** with `End_of_file` mid-run. Not a real error — a stale
   incremental server. `pyre kill` plus removing `.pyre` fixed it. Worth noting
   because the crash exits non-zero and could be mistaken for a gate failure.
3. **pyre found four errors that pyright and mypy both passed.** `logger.py`
   (pyre will not narrow `self.logdir` across a call — bound it to a local) and
   the three named-sign tests. Exactly the three-checker disagreement the
   instructions warn about.
4. **My first two fixes for the named-sign tests were wrong.** I assumed the
   problem was narrowing `case.sign`, then that an explicit annotation would
   settle it. Neither worked: pyre types `(*sequence, x)` as
   `Tuple[object, ...]` — the star-unpack in a tuple display is what widens.
   Resolved by removing the construct, per the instructions' worked example:
   `tuple(case.name_parts) + ((sign,) if sign is not None else ())`. All three
   checkers pass.
5. **flake8 caught a pre-existing 124-character line** in `lemmatization.py`
   that only became my problem because I touched the file. Wrapped it.
6. **I broke the 250-line gate without noticing at first.** Editing the three
   `surrogate=` call sites pulled `test_parse_word.py` (875 lines) into the
   changed set. Split it with an AST script into a 66-line test module plus six
   case modules, all under the limit. Test count before and after: 108 both
   times, so nothing was lost.

### 9. F5 — PR description

Drafted the corrected body, then **asked before touching the live PR**, since
editing a PR description is outward-facing. The user chose "patch it now".
Applied with `gh api repos/... -X PATCH -F body=@file` (per the known
`gh pr edit --body` failure in this environment) and verified by re-fetching:
the `_StartParser.parse` row, the test count and the new "Part 4" section are
all live.

### 10. Gates after the fixes

- `task format` — clean, 841 files.
- `task lint` (ruff) — All checks passed.
- `task type` (pyre) — No type errors found.
- `task type-pyright` — 0 errors over the 96-file post-commit set (simulated by
  running pyright on committed-changed UNION working-tree-changed UNION new
  files, since the task itself only sees committed changes).
- `task test` — 4376 passed, 2 skipped, 1 xfailed.
- Coverage — 98%; 0 uncovered lines among lines these fixes add or modify,
  verified by intersecting the missing-line spec with the diff hunks.
- `flake8 --max-line-length=120` — 0 errors.
- `mypy --ignore-missing-imports` — 1 error, down from 5, in the untouched
  `legacy_atf_transformers.py`.
- `task lint-md` — 0 errors.
- 250-line limit — every changed and new `.py` within limit.

### 11. Runtime re-verification (the rewrite gate)

The earlier run was void once the code changed, so it was redone against the
rebuilt tree on port 8124: `GET /signs/transliteration/$$$` -> 422,
`/[[[` -> 422, `/ku` -> 200, `/markup?text=@i{italic} plain` -> 200 and
correctly parsed, `/signs?value=ku&subIndex=1` -> 200, `/texts` -> 200 (that
last one exercises the `chapter_schemas.py` edit).

Re-diffed the `nameParts` wire output against `origin/master` in a worktree,
this time adding two surrogate-logogram lines (`MIN<(ta-ne₂-hi)>`,
`BA<(ku-u₄)>-ma`) because `with_surrogate` changed that path. 736 lines each,
byte-identical.

### 12. Teardown

Server stopped, both `origin/master` worktrees removed, throwaway databases
dropped.
