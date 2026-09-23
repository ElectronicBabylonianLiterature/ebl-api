# TASK deps-msgpack — TODO

- [x] Create TODO and log first
- [x] Branch `update-msgpack-click` from `origin/master`
- [x] Check constraints: who requires msgpack / click, allowed ranges
- [x] `poetry update msgpack click` only; diff must touch only those two
- [x] pip-audit again: both advisories gone, nothing new
- [x] Gates: format, lint, pyre, pyright, full suite, flake8, mypy, lint-md
- [x] Runtime: app with the Redis cache (msgpack is used by falcon-caching)
- [x] Ask before commit and before push; then open the PR (approved)
