# TASK-743 Work Log — Review PR #743

PR: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743>
Branch: `fix-type-checker-blind-spots` -> `master`
Started: 2026-08-16

## Entries

### 1. Read the instructions

Read `.github/instructions/copilot.instructions.md` in full before any action.
Confirmed the binding gates back to the user.

### 2. Identified the task target

Ran `gh pr view` — PR #743, "Make the ATF parser visible to the type checkers",
open, branch `fix-type-checker-blind-spots`. Working tree clean.

Note: the branch changed from `add-realia-slugs-endpoint` (the session-start
snapshot) to `fix-type-checker-blind-spots` before this task began.

### 3. Checked for an existing review document

`find . -iname 'TASK-*'` and `git status --ignored` found none. The user's
instruction to add a section "in the beginning of the document" therefore means
creating `TASK-743-review.md` fresh with that section first.

### 4. Created task tracking files

Created `TASK-743-todo.md` and `TASK-743-log.md` before starting review work,
per the task-tracking hard gate.

### 5. Fetched all existing PR feedback (review hard gate)

- `pulls/743/reviews` — 5 reviews: sourcery-ai (1 issue), qltysh x2, Fabdulla1
  (CHANGES_REQUESTED, 5 points), github-advanced-security (CodeQL).
- `pulls/743/comments` — 13 inline comments: 1 Sourcery, 9 qlty, 3 CodeQL.
- `issues/743/comments` — 1 (Sourcery reviewer's guide).
- Related PR #740 (this PR was split out of it, merged 2026-08-04) — fetched its
  reviews; final state APPROVED, outstanding items concern `dtos.py` / realia,
  none of which is in #743's diff.
- No feature PR was merged into this branch; the two merge commits merge
  `master` only.

### 6. CI status

All checks green. `qlty check` reports SUCCESS but with **6 blocking issues**;
`qlty coverage diff` 100.0%, total coverage 96.1% (+0.3%).

### 7. Verified each existing finding against the current tree

Findings the branch has since fixed (reviewers looked at older commits):

- 422 on `GET /signs/transliteration/{line}` — now present at
  `ebl/signs/web/signs.py:63-65`.
- Long URL line in `annotations_service.py` — no line >120 in any changed file.
- Museum 3-tuple shape — all five private-collection entries are 3-tuples again.
- `SignsVisitor.reset()` test — `test_reset_clears_accumulated_signs` exists.
- Explicit-`start` parser test — see the correction below.

Findings still open: Sourcery's `TextLine.merge` cast, 3 CodeQL alerts, 6 qlty
issues.

### 8. Correction to my own reading of the reviewer's fifth point

I first recorded Fabdulla1's request for a `_StartParser.parse(..., start=...)`
test as "resolved by `test_parse_uses_default_start`". That was wrong. Reading
`lark_parser.py:72-73` showed the final signature is `parse(self, text: str)` —
the `start` parameter was **removed entirely**, not made optional. The test
passes `start=` to `LINE_PARSER` (a raw `Lark`), not to `_StartParser`. The
request is therefore moot, and the PR description is stale on this point.
Recorded as a finding rather than as "addressed".

### 9. Ran the verification gates

- `task format` — clean, 835 files already formatted.
- `task lint` (ruff) — All checks passed.
- `task type` (pyre) — No type errors found.
- `task type-pyright` — 0 errors, 0 warnings.
- `task test` — 4366 passed, 2 skipped, 1 xfailed (352s).
- `flake8 --max-line-length=120` on 85 changed files — 0 errors.
- `mypy --ignore-missing-imports` on 85 changed files — 5 errors, all in
  `ebl/atf_importer/**` modules that are **not** in the changed set (pulled in
  transitively by following imports). The PR's claim of 0 errors in changed
  files holds.
- `task lint-md` — only my own TASK-743 files errored; fixed.
- 250-line limit — every changed `.py` is within limit.

### 10. Ran the modified service (runtime hard gate)

Booted `waitress-serve --call ebl.app:get_app` on port 8123 against
`mongodb://127.0.0.1:27017` and a throwaway DB, with a locally generated
throwaway RSA cert. Deliberately did **not** source `.env` — its `MONGODB_URI`
points at production.

- `GET /signs/transliteration/$$$` -> **422** `Invalid transliteration: "$$$"`
- `GET /signs/transliteration/[[[` -> **422**
- `GET /signs/transliteration/ku` -> **200**
- `GET /markup?text=@i{italic} plain` -> **200**, parsed correctly (proves the
  relocated grammar directory loads at runtime)
- `GET /signs?value=ku&subIndex=1` -> **200**

### 11. Independently verified the "wire format unchanged" claim

Dumped `OneOfTokenSchema` output for six ATF lines (broken-away interleaving,
determinative, compound grapheme, number with sign, flags, sub-indices) on
`origin/master` in a git worktree and on the branch, using the same interpreter.
500 lines each, **byte-identical**. `nameParts` ordering and `enclosureType`
propagation are preserved by the `NamePart` refactor.

Also confirmed at runtime: `Museum` has 72 members and the five private
collections carry `url=''` with 3-tuple values.

### 12. New findings from reading the diff

- `ebl/corpus/web/chapter_schemas.py` declares `__all__` twice (lines 37 and
  47); the second overwrites the first and drops `ApiLineVariantSchema`, which
  is defined at line 97 and used at line 148. Ruff does not flag module-level
  rebinding, so no gate caught it.
- `NamePart` subclasses `Token` but delegates only `value`, `parts` and
  `accept`. `clean_value`, `get_key`, `lemmatizable` and the `set_*` helpers
  fall through to `Token` and would be wrong for a wrapped `BrokenAway`.
  Traced every reader — none currently reaches them — so latent, not live.
- `_StartParser.parse` no longer accepts `start`; no caller passed it, so the
  narrowing is safe.
- `check_errors` changed `if any(errors)` to `if errors`. `ErrorAnnotation` is
  an attrs instance and always truthy, so the two are equivalent in practice.
- `sign_unicode_lookup.extract_word_sub_indexes` replaced master's
  `getattr(part, "name_parts", [])` probe plus `name_parts[0]._value` with an
  `isinstance` check plus `name_contribution`. A leading `BrokenAway` used to
  raise `AttributeError` and now yields `""` — a strict improvement.

### 13. Coverage gate

`pytest ebl/tests --cov=<each changed source module> --cov-report=term-missing`
finished at 98% (3350 statements, 54 missed) with 4366 passed.

I did not stop at the percentage. I parsed the missing-line spec per file and
intersected it with the new-file line ranges from
`git diff -M --unified=0 origin/master...HEAD`: **0 of the 54 missed lines fall
on a line this PR adds, modifies or moves.** Every newly created or split-out
module is at 100%.

Spot-checked the largest gap by hand: `retrieve_annotations.py` sits at 79%,
but the uncovered lines (100, 109-127, 135, 167-173) are the CLI `main()` path,
exist verbatim on `origin/master`, were last touched by an unrelated commit, and
only shifted position when the helpers module was extracted. Consistent with
`qlty coverage diff` reporting 100.0%.

### 14. Markdown line-length handling in the review document

The user asked for the `Details` subsection to drop the line-length limit so it
pastes cleanly into GitHub. `.markdownlint.json` sets MD013 to 80, and the rule
against touching lint configuration without an explicit request applies. I
resolved this with in-document
`<!-- markdownlint-disable MD013 -->` / `<!-- markdownlint-enable MD013 -->`
directives — no configuration file was modified.

Three disabled regions in total: the `Details` subsection as requested, plus the
`Findings` table and the gate-results table, whose rows cannot be wrapped
without breaking the table. Everywhere else I shortened the content for real
(split the `export` lines, narrowed a `grep` pattern, moved an inline comment
onto its own line) rather than suppressing. `task lint-md` is at 0 errors.

### 15. Teardown

Stopped the review server, removed the `origin/master` git worktree, and dropped
the `ebl_review_743_throwaway` database. Working tree holds only the three
`TASK-743-*.md` files; no source file was modified.

### 16. Final gate confirmation

Re-read `.github/instructions/copilot.instructions.md` and confirmed every
section was honoured. Nothing was committed or pushed — no such request was
made.
