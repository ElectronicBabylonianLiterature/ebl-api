# TASK meszl-kap2: log

- Removed the Einleitung/Anhänge display at the user's request; committed.
- Opened the PR (ebl-api #838 / ebl-frontend #872).
- Started an independent harsh review of the branch diff against origin/master.
- Review verdict: request changes (pyre error, unrelated reformat, N queries,
  conventions, test gaps, history).
- Error made: formatted with black instead of ruff format, which reformatted
  test_sign_search_route.py; restored it from origin/master.
- Error made: mypy/pyright first run against `origin/master` (two-dot) picked up
  master-only files; rerun on `origin/master...HEAD`.
- Merged origin/master (f58b520) into the branch.
- Restructured: domain module, single-query repository, schema, cache_control
  decorator, SignName; every Kap. II document stores `number`.
- Rewrote tests with made-up text; added scope test; 100% coverage.
- Addressed Sourcery/CodeQL findings (see review file).
- Live check with waitress + RS256 tokens: 200/404 with scope, 403 otherwise.
- qlty could not be installed (qlty.sh blocked by network policy).
- Import script (outside repo): upsert-then-prune, `number` on every document,
  HethZI → HethZL typo fix in entry 183.
