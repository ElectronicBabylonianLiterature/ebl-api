# TASK realia-mapping — Log

## 2026-09-23

- Created TODO and log first. Request: fix Sourcery's `Mapping` point on
  #767; don't post #735 replies yet; find Dependabot alert 75 or give the
  link.
- Branch `fix-realia-detail-unloadable-entries` at `3ac43099` (= remote).
- `treat_null_as_absent` now checks `typing.Mapping` (repo convention)
  instead of `dict`. New test
  `test_null_field_in_non_dict_mapping_loads_as_absent` uses
  `MappingProxyType`; it fails without the change and passes with it
  (22 tests in the file).
- Dependabot alert 75: the REST API returns 403 and GraphQL
  `vulnerabilityAlerts` returns an empty list for this token. Ran
  `pipx run pip-audit` on the venv's frozen packages (99; same `click` and
  `msgpack` versions as `origin/master`'s `poetry.lock`):
  - `msgpack` 1.1.2: GHSA-6v7p-g79w-8964 / CVE-2026-57585, **high**
    ("Out-of-bounds read / crash on Unpacker reuse after a caught error"),
    vulnerable <= 1.2.0, fixed in 1.2.1. Pulled in by `falcon-caching`
    (main group, runtime). The only high one, so almost certainly alert 75.
  - `click` 8.3.1: PYSEC-2026-2132 / GHSA-47fr-3ffg-hgmw / CVE-2026-7246,
    fixed in 8.3.3. GitHub's advisory API returns 404 for that GHSA, so its
    severity is unknown. Pulled in by `black` and `pyre-check` (dev tools).
  - Not fixed here: a dependency bump belongs in its own PR and wasn't
    requested.
- Gates on the change: format (no changes), lint, pyre no errors, pyright
  on the two files 0, flake8, mypy 0 in the changed files, full suite
  4854 passed / 2 skipped / 1 xfailed, `realia_schemas.py` 100%, test file
  100% (31 statements).
- **Error I made:** the scratchpad had been cleared, so my first coverage
  and runtime commands pointed at missing scripts (the coverage line printed
  nothing, and every curl returned 000). Recreated `covrc`, `serve.py` and
  `seed.py`, then re-ran both.
- Runtime on the changed tree (port 8743, DB `ebl_review_map`, never
  `.env`): `Anu` 200, `NullType` 200, `NullRealiaId` 200, `BadElement` 500
  (out of scope). Server stopped, DB dropped.
- CI on #767 head `3ac43099`: 15 pass, 2 skipped, so the earlier PyPy
  flake is gone without a re-run.
- Updated `TASK-realia-detail-500-handoff.md`. Nothing committed or pushed.
- User approved commit and push (once each). Code unchanged since the gate
  run (only `.md` files edited after). Committing the two code files, the
  updated handoff and this TODO/log.
