# TASK-745 TODO — Clear the hosted CodeQL and qlty findings on PR #743

<!-- markdownlint-disable MD013 -->

Task: fix what the hosted CodeQL and qlty runs reported on the pushed commits
`2b3b0668` and `2a77229`, which clean local runs had missed.

Status legend: `[ ]` pending, `[~]` in progress, `[x]` done, `[!]` blocked

## 0. Task artefacts (hard gate)

- [x] Create `TASK-745-todo.md` — **created late, after work had begun; see the
      log. This is a gate violation, recorded rather than hidden.**
- [x] Create `TASK-745-log.md`
- [x] Keep both updated as each step completes

## 1. CodeQL on `2b3b0668` — 6 alerts

- [x] `provenance_lookup.py` x3 "Statement has no effect" (`...` bodies)
- [x] `test_named_sign_name.py` x2 "assert has a side-effect"
- [x] `test_named_sign_name.py` "Unused import"

## 2. qlty on `2b3b0668` — 10 blocking

- [x] Deduplicate 16 identical merge cases via `unchanged(old, new)`
- [x] Share `LEMMATIZED_MANUSCRIPT_LINE` across `chapter_merge_cases_2_1/2_2`
- [x] `aligned_variant` / `unaligned_variant` in `chapter_merge_cases_1_1`
- [x] `emended_separator` in `enclosure_visitor_types_cases_2`
- [x] Justify the two that remain (`__all__` pair, pre-existing `Word.of`)

## 3. CodeQL on `2a77229` — 3 alerts

- [x] Two asserts still called `BrokenAway.close()` / `ValueToken.of()` inside
      the assert expression — hoisted to module constants
- [x] `task_743_migrate_name_breaks_test.py` imported the module with both
      `import` and `from ... import`

## 4. Coverage regression on `2a77229`

- [x] Diff coverage fell 100.0% -> 99.8%: the `raise NotImplementedError`
      bodies added for CodeQL are never executed. Fixed with `@abstractmethod`,
      which `.coveragerc` already excludes

## 5. Still open

- [ ] Enumerate qlty Cloud's remaining 5 blocking issues (local shows 2)
- [ ] Full suite with coverage, green
- [x] Commit
- [ ] Ask before pushing

## 6. Cleanup before merge

- [x] Enumerate every branch-only file and record it as a checklist in
      `TASK-745-handoff.md` section 8 (14 files, plus the 2 that must stay)
- [ ] Actually delete them before merge

## 7. Handoff

- [x] `TASK-745-handoff.md` written — supersedes `TASK-743-fix-handoff.md`
