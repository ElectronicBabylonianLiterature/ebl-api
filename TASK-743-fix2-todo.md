<!-- markdownlint-disable MD013 -->

# TASK-743-fix2 — TODO

Address every finding from `TASK-743-review2-review.md` (review of PR #743).

## Checklist

- [x] 1. Create task TODO + log files (this file and `TASK-743-fix2-log.md`)
- [x] 2. F1 — remove the seven committed `TASK-743-*.md` files from the branch
- [x] 3. F2 — fix `Chapter._get_extant_lines` / `Chapter.extant_lines` annotation, drop the wrong `cast`
- [x] 4. F3 — restore `frozen=True` on `TransliterationQueryEmpty`
- [x] 5. F4 — memoize `MemoizingSignRepository.get_unicode_from_atf`
- [x] 6. F5 — pin the `name_parts` / `name_tokens` serialisation constraint
- [x] 7. F6 — align the four `list[...]` / `dict[...]` annotations with each file's `typing` style
- [x] 8. F7 — collapse the `Reading` / `Logogram` `of` / `of_name` duplication; re-check every other qlty item against HEAD
- [x] 9. Add / update tests for every behaviour change; 100% coverage on all touched lines
- [x] 10. HARD GATE: `*.py` 250-line cap on every touched file
- [x] 11. HARD GATE: no mixed-type arrays introduced
- [x] 12. Gate — `task format`
- [x] 13. Gate — `task lint`
- [x] 14. Gate — `task type` (pyre, the CI gate)
- [x] 15. Gate — `task type-pyright`
- [x] 16. Gate — `poetry run mypy <changed> --ignore-missing-imports`
- [x] 17. Gate — `poetry run flake8 <changed> --max-line-length=120`
- [x] 18. Gate — `task test` (full suite)
- [x] 19. Gate — coverage 100% on all changed lines
- [x] 20. Gate — `task lint-md`
- [x] 21. HARD GATE: re-verify at runtime against the final tree (previous run is void after these rewrites)
- [x] 22. Update `TASK-743-review2-review.md` with the disposition of each finding
- [x] 23. Report: gates run + results, changes uncommitted, remind to remove TASK-*.md before merge
