# TASK deps-msgpack — Log

## 2026-09-23

- Created TODO and log first. Request: open a separate PR updating
  `msgpack` to 1.2.1 (GHSA-6v7p-g79w-8964, high, likely Dependabot 75) and
  `click` to 8.3.3 (CVE-2026-7246).
- Branched `update-msgpack-click` from `origin/master` (`cd46110c`).
- Constraints: `msgpack = "*"` (from `falcon-caching`), `click >= 8.0.0`
  (`black`) and `*` (`pyre-check`). Project Python `>=3.11,<4.0`; CI
  3.11 / 3.12 / pypy-3.11; Docker `pypy:3.11`.
- `poetry update msgpack click`: lock now `msgpack` 1.1.2 → 1.2.2 (needs
  Python >= 3.10, fine) and `click` 8.3.1 → 8.5.0. Changed lock packages:
  `click`, `msgpack`, and `colorama` (marker only: click 8.5.0 no longer
  depends on colorama). `[metadata]` unchanged, `pyproject.toml` unchanged.
- **Error I made:** `poetry update` installed only msgpack (click is in the
  optional `dev` group), and a plain `poetry install` failed on the root
  package. Installed the CI way (`poetry install --no-root --with dev`):
  click 8.5.0 now installed. The shared `.venv` now has these versions on
  every branch.
- pip-audit on the updated environment: no known vulnerabilities.
- Runtime (Redis `redis:7-alpine` on 127.0.0.1:6379, port 8744, DB
  `ebl_review_deps`, never `.env`): `/statistics` twice → both 200,
  identical bodies, key `falcon_cache_/statistics:GET` in Redis, so the
  second came from the msgpack-packed cache. `Cache-Control` missing on the
  hit is the known `cache.cached` behaviour on master. Only traceback:
  `/realia/NullType` 500 (master; fixed in #767). Server and Redis stopped,
  DB dropped.
- Gates (run after installing click 8.5.0 with `--with dev`): `task format`
  no changes, `task lint` pass, `task type` (pyre) no errors,
  `task type-pyright` "No changed Python files", full suite 4832 passed /
  2 skipped / 1 xfailed, lint-md 0. No `.py` changed, so flake8, mypy and
  coverage on changed files have nothing to check.
- Waiting for approval to commit, then to push, before opening the PR.
- User approved commit and push (once each); notes included, as on the
  other branches. PR opening was approved earlier. PR creation and CI
  results come after this log is committed, so they are not recorded here.
