# TASK-743-fix — Address the review findings on PR #743 — TODO

Task: apply every finding recorded in `TASK-743-review.md` to the working
tree. No commit unless the user asks in their own words.

## Checklist

- [x] 1. Create task TODO + log (this file, `TASK-743-fix-log.md`)
- [x] 2. Inspect coverage config (`exclude_lines`, `branch`) before changing
      any `...` / `raise NotImplementedError` body or adding a branch
- [x] 3. Inspect qlty config to learn how `function-parameters` counts
- [x] 4. F1 — hoist `OneOfTokenSchema` out of `_dump_name_parts` /
      `_load_name_parts` (lazily cached module-level instance)
- [x] 5. F2 — reduce `named_signs._create` below the qlty parameter threshold
- [x] 6. F3 — resolve CodeQL 921/922 on `legacy_transformer_base.py:38,40`
- [x] 7. F4 — replace the nine unparameterized generics with precise types
- [x] 8. F5 — reconcile the `__all__` claim in the PR description (outward
      facing: ASK before touching the PR body)
- [x] 9. F6 — no action; record the accept rationale
- [x] 10. F7 — `_tree_to_string` must not stringify a `None` child
- [x] 11. F8 — validate `NamePart.name_contribution` against its token
- [x] 12. F9a — `commit_value` -> `_commit_value`
- [x] 13. F9b — merge the duplicated `domain.fragment` import
- [x] 14. F9c — redundant test in `test_chapter_visitor.py` (test REMOVAL
      needs explicit user approval: ASK, do not delete unilaterally)
- [x] 15. Add/extend tests so every added or modified line is covered
- [x] 16. Re-verify wire format + Museum enum are still identical to master
- [x] 17. Gates: format, lint, type (pyre), type-pyright, test, coverage,
      flake8, mypy, lint-md, 250-line limit
- [x] 18. Re-verify against the RUNNING service (a rewrite voids the earlier
      run — do it again)
- [x] 19. Update `TASK-743-review.md` with the resolution of each finding
- [x] 20. Re-read copilot instructions; report which gates ran and results
- [x] 21. Remind the user to remove the TASK-743* docs before merge
