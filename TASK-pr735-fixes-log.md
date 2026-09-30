# TASK pr735-fixes — Log

## 2026-09-30

- Request: "address all the (known) findings" from `TASK-pr735-review.md`.
- Created this log and the TODO before starting work.
- Local `add-realia-slugs-endpoint` equals `origin` (`30a23b22`); no pull
  needed.
- F1: `ReallexikonReferenceField._from_id` now returns `None` for a non-string
  id (same as the field already does for non-str/non-dict values); stub filter
  `_is_resolvable_reference` now requires a non-empty *string* reference or
  `reference.id` (`$type` check), replacing the `$switch`.
- F2/F3: `reserved_identifiers.py` gains `BY_ID_ROUTE_SEGMENT`,
  `EMPTY_IDENTIFIER` (added to `RESERVED_REALIA_IDS`) and
  `RESERVED_REALIA_ID_PREFIXES = ("by-id/",)`. The listing query adds
  `"$not": re.compile("^(?:by\-id/)")`; `bootstrap.py` builds the by-id route
  from the constant.
- F4: memoized value is now a frozen attrs `RealiaIdListing(computed_at,
  identifiers)` (not a mixed tuple, per the data hard gate); `on_get` sets
  `Age` from it so downstream freshness is bounded to 600 s total.
- `ruff format` reformatted `bootstrap.py` (my edit wrapped a line that fits).
- **Error:** wrote a mixed-type parametrize list (`[5, {...}, [...]]`) in
  `test_realia_entry.py`, the same defect as F5; caught on re-read and wrapped
  in `pytest.param`.
- F5: `NON_STRING_IDENTIFIERS` and (same defect, also found)
  `NON_ARRAY_VALUES` in `test_realia_stub_filter_robustness.py` now hold only
  `pytest.param` sets with ids.
- Tests added: stub filter treats int/object/list `reference.id` and a list
  `reference` as unresolvable; non-string `reference.id` entries are listed
  and retrievable (200, `reference` null); schema unit test; `by-id/` prefix
  excluded while `by-id`, `by-idx/foo`, `a/by-id/foo` stay listed; route
  test seeds `by-id/foo` + `Other(realiaId=foo)` and URL-encodes ids; `Age`
  is 0 uncached, 599 after 599 s cached, 0 after expiry (freezegun).
- Realia tests: 203 passed.
- **Error / environment:** the codespace restarted (uptime 15 min), wiping
  the scratchpad `pr735/` folder; my first mutation-check command failed to
  write its patch there. The `&&` chain stopped before `git checkout`, so
  nothing was lost (verified with `git status`). Re-ran with the folder
  recreated.
- **Error:** the second attempt reverted `ebl/realia/domain` too, so the tests
  failed at import and gave no signal. Third attempt reverted only
  `infrastructure` + `web`: 13 new tests fail on the unfixed code (F1 schema,
  F1 stub filter, F1 retrievability, F2 prefix, F2 route, F4 Age), 181 pass.
  Fixes re-applied from the patch; diff verified.
- README caching section: added a paragraph on the compounded lifetimes and
  the `Age` header pattern.
- Gate run 1 findings and fixes:
  - pyre rejected `map(re.escape, …)` → generator expression.
  - pyright: 62 **pre-existing** errors in `test_realia_entry.py` (untyped
    marshmallow `load`/`dump` results) + 5 from my new test. Fixed all by
    typed helpers `_load_reallexikon`/`_load_realia` and `cast(dict, dump)`,
    matching `cast(...)` use in `mongo_realia_repository.py`.
  - pyre then flagged Optional narrowing on an indexed expression → bound to
    a local.
  - pyright: 2 pre-existing override errors in `realia_schemas.py`
    (`attr_name` vs marshmallow's `attr`) → renamed to `attr`, identical to
    what #767 already did on master (no merge conflict expected).
  - `ruff format` reformatted `mongo_realia_repository.py`.
- mypy reports 26 errors, all in files this PR does not touch
  (`lark_parser` visibility etc.). They exist because the branch predates
  #743; on master+PR earlier mypy was clean. Zero in touched files.
- Gate run 2: format 0, lint 0, pyright 0 errors (all 15 touched/PR files),
  flake8 0, mypy 0 in touched files, `task type` (pyre) rc=0 no errors.
- Coverage: all 9 touched source modules 100% (203 tests).
- qlty: `smells --include-tests` on the 15 touched/PR files → no findings.
  Repo-wide `--all --include-tests`: the working tree shows one extra
  duplication (mass 64, 5 locations) that the merge-base and PR-head
  worktrees do not; all 5 locations are in untouched, unchanged files
  (`ebl/corpus/infrastructure/queries.py` ×3,
  `mongo_text_repository_query.py`, `ebl/fragmentarium/infrastructure/
  queries.py`). Not introduced by this change; appears to be a
  checkout-location difference in qlty's run. No finding in any touched file.
- Runtime (local Mongo `pr735_review`, `SENTRY_DSN=`, simple cache; the
  seed script asserts no `srv.mwn.de`): `/realia/all` → 200, `Age: 0`,
  `Cache-Control: public, max-age=600`; lists `Anu, by-id, IntRefId,
  ListRefId, ObjectRefId, Other, Query?x, trailing/`. Excluded: `""`, `all`,
  `by-id/foo`, `Stub`, and `StubBadRef` (single cross-ref + non-string
  reference id → stub, as on the frontend). Each listed id (URL-encoded)
  → 200 with its own `_id`; the bad-reference entries now return
  `reference: null` instead of 500. No tracebacks in the server log. A
  cached request later returned `Age: 11`. Server stopped, scratch DB
  dropped.
- Drafted (scratchpad, not posted): new PR body, two thread replies, a response
  to review 5367106362.
- Full suite on the fixed branch: 4458 passed, 2 skipped, 1 xfailed, 0
  failures (268 s). Fewer tests than master because the branch predates 12
  master commits.
- Re-read the instructions; nothing committed or pushed; P1/P2 await the
  user.

## Handoff

- Code findings F1–F5 from `TASK-pr735-review.md` are fixed and verified
  (tests, all type checkers, qlty, running service).
- Still open:
  - P2: merge `master` (done next in `TASK-pr735-merge-log.md`), then re-run
    the gates on the merged tree.
  - Push, then check CI, qlty and CodeQL on the new head.
  - P1: post the two thread replies and resolve the threads; post the review
    response and the new PR description. All drafts are in
    `TASK-pr735-review.md` → "GitHub drafts".
  - Re-request review from Fabdulla1.
  - Remove every `TASK-pr735-*` file before the PR is merged.
