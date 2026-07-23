# TASK-740 Fix — TODO

Address every finding raised in `TASK-740-review.md` for PR #740.

## Findings to address

- [x] 1 (High) Factory id-space collision breaking
      `test_query_fragmentarium_number` in CI — `ArchaeologyFactory`
      now mints `EX.<n>`, disjoint from the museum `X.<n>`, accession
      `A.<n>` and cdli `cdli-<n>` namespaces
- [x] 2 (High) Invalid `namedEntities[].type` returned HTTP 500 — now
      `NameEnumField`; also hardened `EnumField` against unhashable
      values, which were a second 500; two validation cases added
- [x] 3 (Medium) Silent realia-store degradation — logs a warning with
      `exc_info` before returning `[]`, covered by a `caplog` test
- [x] 4 (Medium) mypy errors in touched files — all fixed; root cause of
      the `lark_parser` group was a grammar directory shadowing the
      module, not a missing `__all__`
- [x] 5 (Low) `annotation_key` `isinstance` probe — replaced by a
      `key_value` property on each span class; the mixed-type array in
      `_validate_unique_ids` is gone too
- [x] 6 (Low) Duplicated `make_token` bodies — extracted into
      `AbstractWordSchema`
- [x] 7 (Low) Weak type hints in `named_entities.py`
- [x] 8 (Low) Repo hygiene — `!.claude/settings.json` un-ignored;
      `"ocredSigns"` tuple/field-name bug fixed
- [x] Coverage note — `update_field` guard now covered

## Not done, and why

- Splitting the unrelated tooling and instruction changes out of PR #740
  into their own PR. This needs new branches and rewritten history, which
  the git hard gate forbids without an explicit request. Flagged for the
  user to decide.
- Removing the committed `TASK-740-todo.md` / `TASK-740-log.md`. The
  instructions say to remind before merge, not to delete mid-review;
  raised in the report instead.

## Gates before reporting complete

- [x] `task format`
- [x] `task lint`
- [~] `task type` (pyre) — crashes in this environment on the clean
      tree too; unverified, needs CI or a larger machine
- [~] pyright — 0 in my code; 9 remain in `archaeology.py`, all
      factory_boy stub bugs needing a suppression or config (your call)
- [x] `task test` — 3940 passed, 2 skipped, 1 xfailed
- [x] `task lint-md`
- [x] Coverage 100% on every added, modified or moved line
- [x] `flake8 --max-line-length=120` on changed modules
- [x] `mypy --ignore-missing-imports` on changed modules — zero errors
- [x] Every changed `*.py` under 250 lines
- [x] Run the modified backend service and exercise the affected routes
- [x] Re-verify after every rewrite
- [x] Re-read the copilot instructions; confirm and report every gate
- [x] Do not commit or push

## Added scope: repo-wide Pylance errors

- [x] Measure: 1237 errors across 158 files
- [x] Fix every error in files this work touched (53 -> 9)
- [ ] The other 153 files (~1184 errors) — not started; needs your
      decision, since it means touching files unrelated to this PR
- [ ] The 9 factory_boy stub errors — need a suppression or a pyright
      config setting, both of which need your explicit sign-off
