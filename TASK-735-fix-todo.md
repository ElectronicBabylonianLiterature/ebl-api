# TASK-735-fix TODO — Address review findings on PR #735

Branch: `add-realia-slugs-endpoint` → `master`
PR: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/735>
Source of findings: `TASK-735-review.md`

## Steps

- [x] 1. Create this TODO and `TASK-735-fix-log.md` before any change
- [x] 2. Confirm the two open design decisions with the user
      (route naming for Finding 1; redirect rule for Finding 5) and
      whether the PR title/body may be edited on GitHub (Finding 4)
- [x] 3. Finding 2 (High) — guard `$size`/`$filter` with `$isArray`/`$cond`
      in `realia_stub_filter.py` so a malformed legacy document cannot
      abort the query
- [x] 4. Finding 2 — add repository tests for every malformed shape:
      scalar and object in each own-content array field, malformed
      `crossReferences`, malformed `reallexikon`
- [x] 5. Finding 1 (High) — remove the raw-`_id` route collision for the
      listing endpoint per the user's chosen option
- [x] 6. Finding 1 — add a test proving no realia `_id` can shadow the
      listing route and that every listed ID is retrievable
- [x] 7. Finding 3 (High) — drop the three unrelated tooling files from the
      branch by restoring master's versions:
      `.github/instructions/copilot.instructions.md`, `.gitignore`,
      `Taskfile.dist.yml`; confirm conflicts are gone
- [ ] 8. Finding 4 (Medium) — update PR title and description to describe
      the real route and the redirect-stub exclusion (only if authorised)
- [x] 9. Finding 5 (Medium) — apply the user's decision on the
      exactly-one-cross-reference rule; rename the constant to say what
      the rule is
- [ ] 10. Finding 6 (Low) — record the full-scan/`$expr` trade-off in the
       PR description (no code comments — project forbids them)
- [x] 11. Finding 7 (Low) — disambiguate the `realia_id` path parameter
       between `_id` and `realiaId` routes
- [x] 12. Finding 8 (Low) — inline `IF_NULL`; re-check whether the `or ""`
       and the `cast(...)` calls are required by the type checkers before
       removing them (keep whatever pyre/pyright/mypy need)
- [x] 13. Keep every changed `.py` file under 250 lines; split if needed
- [x] 14. Gate: `task format`
- [x] 15. Gate: `task lint`
- [x] 16. Gate: `task type` (pyre — the CI gate, never inferred)
- [x] 17. Gate: `task type-pyright`
- [x] 18. Gate: `task test` (full suite)
- [x] 19. Gate: pytest with `--cov` on changed modules — 100%, no gaps
- [x] 20. Gate: `flake8 --max-line-length=120` on changed modules
- [x] 21. Gate: `mypy --ignore-missing-imports` on changed modules
- [x] 22. Gate: `task lint-md` for markdown changes
- [x] 23. Re-verify by RUNNING the service against local mongo and
       re-testing every reproduction in `TASK-735-review.md` — the
       previous run is void once the code is rewritten
- [x] 24. Update `TASK-735-review.md` to reflect resolved findings
- [x] 25. Re-read copilot instructions; confirm every gate; report results
- [x] 26. Report WITHOUT committing; remind to remove TASK files pre-merge

## Outstanding — need the user's decision

- Item 8 (Finding 4): PR title/body edit is outward-facing; awaiting
  authorisation.
- Item 10 (Finding 6): belongs in the PR description, so it is blocked
  on the same authorisation.
- Finding 5: the redirect-stub rule itself still needs a domain answer;
  behaviour left unchanged, constant renamed only.
- `test_entry_named_all_is_reachable` was replaced; test removal needs
  explicit approval per project rules.

## Notes

- No commit, push, or history rewrite unless the user explicitly asks.
- The previous verification run is void after each rewrite (hard gate) —
  re-run the service checks against the final code.
