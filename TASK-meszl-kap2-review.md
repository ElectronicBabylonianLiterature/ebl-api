# TASK meszl-kap2: review of PR #838

## Summary

The PR adds the restricted endpoint `GET /signs/{sign_name}/meszl-kap2` for
Borger, MesZL² Kapitel II.

- **Sources:** an independent harsh review, plus the bot reviews already on
  the PR (Sourcery, CodeQL).
- **Verdict before fixes:** request changes.
  - A pyre error would have failed CI.
  - An unrelated file was reformatted.
  - The repository made one query per MesZL number, and handled missing
    entries by catching exceptions.
  - The code did not follow the repo's conventions for the domain layer,
    schemas and cache control.
  - Tests had gaps.
  - Earlier commits put copyrighted book text into the branch history.
- **Status:** all findings are fixed, except the git history. That one is
  handled with "Squash and merge"; see Recommendation.

## Findings

- F1: Pyre and mypy: `SignRepository.find` received a `str` instead of a
  `SignName` (review, gates). Status: Fixed.
- F2: `ebl/tests/signs/test_sign_search_route.py` was reformatted by black,
  unrelated to the PR (review). Status: Fixed: identical to master.
- F3: Copyrighted MesZL passages in tests of commits 62bdf4a, b8a97cc and
  a27dc1d (files since deleted) (review). Status: Squash on merge; test data
  is now made-up text.
- F4: `find_many` made one query per number, swallowed `NotFoundError`, and
  de-duplicated in quadratic time (review). Status: Fixed: one `$in` query,
  ordered de-duplication.
- F5: `find()` existed only for the tests (review). Status: Removed; the
  interface has only `find_by_numbers`.
- F6: Layering: the domain value lived in `application`; the response was built
  by hand; `cache_control` was set inline (review). Status: Fixed:
  `ebl/signs/domain/mes_zl_kap2.py`, `MesZlKap2EntrySchema`, `@cache_control`.
- F7: Test gaps: implicit no-scope user; no scope test; no prime or alias case
  at route level; inexact Cache-Control assertion; no 403 for an unknown sign
  (review). Status: Fixed: tests in `test_mes_zl_kap2_route.py`,
  `test_mongo_mes_zl_kap2_repository.py` and `test_scopes.py`.
- F8: `"MZL"` defined twice (review). Status: Fixed: shared `MES_ZL_LIST`.
- F9: Variants returned as a list (review). Status: Fixed: tuple; exact
  spelling tried first.
- F10: Literal route segment `meszl-kap2` takes precedence over `{sort_era}`
  (review). Status: Accepted: no sort era has that name; falcon matches
  literal segments first.
- F11: An alias returned the target's number without saying so (review).
  Status: By design: the entry shown is Borger's, under his number; noted in
  the PR description.
- F12: Optional `number` existed only on alias documents (repo data rule)
  (own). Status: Fixed: every document stores `number`.
- F13: Sourcery: missing entries appear complete (bot). Status: Skipping is
  intended: most MesZL numbers have no Kapitel II entry. The importer now
  upserts and then deletes stale entries, so readers never see a gap.
- F14: Sourcery: apostrophe and prime variants could return inconsistent text
  (bot). Status: Fixed: the exact spelling wins deterministically.
- F15: Sourcery: missing type hints (bot). Status: Fixed.
- F16: Sourcery: abbreviated `_req` (bot). Status: Fixed: `_request`.
- F17: Sourcery: code comment (bot). Status: Fixed: removed.
- F18: CodeQL: statement has no effect (`...` in the abstract method) (bot).
  Status: Fixed: `raise NotImplementedError()`, as in other repositories.

## Severity

- **Blockers:** findings 1–3.
- **Major:** findings 4–7, 12 and 13.
- **Minor or nits:** the rest.

## Reproduction Steps

1. **Finding 1:** run `pyre check` at commit a025da6. It reported one error at
   `ebl/signs/web/mes_zl_kap2.py:29`.
2. **Finding 2:** run `ruff format --check ebl`. It reported "Would reformat
   test_sign_search_route.py".
3. **Finding 4:** call `find_many` with N numbers. It issued N `find_one`
   queries.

## Recommendation

**Gates run on the final tree:**

- `ruff format --check`: clean for the changed files.
  - `test_sign_search_route.py` is byte-identical to master.
  - The local ruff version still flags that file on master as well.
- `ruff check`: clean.
- `flake8 --max-line-length=120`: clean.
- `mypy`: clean.
- `pyright@1.1.411`: 0 errors.
- `pyre check`: 0 errors.
- Signs, common and app-bootstrap tests: 341 passed.
- Coverage: 100% on every changed module.

**Live service check** (waitress with the real auth backend, RS256 tokens and
an in-memory MongoDB):

- With the scope: existing sign 200, all entries, `private, no-store`; unknown
  sign 404.
- Without the scope: existing sign 403; unknown sign 403.
- Guest: existing sign 403; unknown sign 403.

**Not run:** qlty smells. Its host (qlty.sh) is blocked by this environment's
network policy, so qlty Cloud's verdict on the PR is the gate.

**History:** merge with "Squash and merge". This keeps the deleted
copyrighted test text out of master without rewriting the pushed branch.

## Second review (merciless)

Findings and what was done:

- R2-1 (blocker): the task files were committed while the review file said
  they were not. The claim is corrected. They stay committed until the user
  asks to remove them, and must be removed before merging.
- R2-2 (blocker): qlty was not run. It is still blocked here (qlty.sh is not
  reachable). The duplicated fixture `mes_zl_kap2_entries` was moved into
  `ebl/tests/signs/conftest.py`.
- R2-3 (major): aliases were full copies of an entry, told apart by
  comparing `_id` with `number`. Fixed: one document per entry,
  `{_id, text, aliases: [...]}`, and entries are de-duplicated by number.
- R2-4 (major): spellings were handled at query time. Fixed at the source,
  at the user's request: the data scripts write every MesZL number with
  Borger's prime (′), both in `signs.lists` and in `meszl_kap2`. The API
  matches numbers exactly and has no normalizer; an apostrophe does not
  match (tested).
- R2-5 (major): the precedence rule had no test. This is moot after R2-4:
  there is a single spelling, and exact matching is tested.
- R2-6 (major): documents were read without the schema. Fixed:
  `MesZlKap2DocumentSchema` loads them, and malformed documents raise a
  ValidationError (tested).
- R2-7 (major): copyrighted text is in the PR history, and GitHub keeps
  `refs/pull/838/head`. This is the owner's decision: squash-merge, or
  rewrite the history or open a clean PR. Not changed without an explicit
  request.
- R2-8 (major): an alias resolves without saying so. Not changed: the
  response is the set of Borger's entries under his numbers, and the UI does
  not need to know which of the sign's numbers matched.
- Minor findings, all fixed:
  - `MES_ZL_LIST` moved to `ebl/transliteration/domain/sign.py`.
  - `mes_zl_numbers` moved to the domain module.
  - Empty and blank numbers return early without querying.
  - Type hints added to `context_fixtures.py` and `create_signs_routes`.
  - New tests: duplicate MZL numbers, and no Cache-Control on a 403.
- Nits: the test scopes are now minimal and the imports sorted. The `get`
  helper is kept, because pyright needs the `cast` (same pattern as
  `ebl/tests/media/web/helpers.py`).

Gates after the second round:

- ruff format and check: clean.
- flake8, mypy and pyright: clean.
- pyre: no type errors.
- Tests: signs, common, transliteration and app bootstrap, 2514 passed.
- Coverage: 100% on every changed module.
- Live service check: repeated with the new storage format, same results.

## Comment status tracking

- Resolved by code changes, pending re-review on the next push:
  - Sourcery threads: missing entries, variants, type hints, `_req`, comment.
  - CodeQL thread: statement has no effect.
- Unresolved: none.

## What Has To Be Done

1. Push the fixes and let Sourcery, CodeQL and qlty re-review.
2. Merge with "Squash and merge".
3. Remove the `TASK-meszl-kap2-*.md` files before merging. They are
   committed on the branch.
4. Decide how to handle the PR history (R2-7).
