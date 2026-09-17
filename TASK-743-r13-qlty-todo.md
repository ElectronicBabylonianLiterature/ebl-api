<!-- markdownlint-disable MD013 -->
# TASK-743-r13-qlty — TODO

Remove the two qlty blocking issues on PR #743 rather than justifying them.

New task; own TODO and log, created before work.

## Decision on record

The copilot instructions name "two unrelated `__all__` lists that happen to have
the same shape" as a legitimate justification, and earlier rounds justified these
two on exactly that basis. **The user has decided they must be addressed.** That
decision stands; comply first. What follows is how to fix them *properly*.

## Hard constraint

**Never silence qlty.** No `qlty.toml` threshold edit, no `# qlty-ignore`, no
exclusion pattern, and no cosmetic reshuffling of a list purely to slip under the
detector — that is silencing by another name. The fix has to be a real
improvement to the code, or it is not a fix.

## The two findings

- **A** — `ebl/transliteration/domain/tokens.py` (17 lines, mass 64)
  ↔ `ebl/fragmentarium/domain/fragment.py`. Two `__all__` export lists.
- **B** — `ebl/tests/factories/fragment.py` (22 lines, mass 84)
  ↔ `ebl/tests/fragmentarium/test_museum_number.py`. An `__all__` list against
  `PREFIXES`, a list of museum-number prefix strings.

## Steps

- [x] 1. Create TODO + log
- [x] 2. Reproduce both locally and capture the exact duplicated ranges
- [x] 3. Establish whether each `__all__` is load-bearing: does anything
      `import *`, does any test assert it, do the type checkers need it?
- [x] 4. Work out which of them this PR introduced vs which predate it
- [x] 5. Design a fix that is a genuine improvement, not detector-dodging
- [x] 6. Implement
- [x] 7. Confirm qlty is clean: changed files AND `--all --include-tests`
      repo-wide, diffed against the pre-change count
- [x] 8. Full gates: format, lint, pyre, pyright direct, test, coverage,
      flake8, mypy, lint-md
- [x] 9. Re-verify at runtime if anything with a runtime surface moved
- [x] 10. Update review, handoff and PR description (the justification text
      becomes wrong once the findings are gone)
- [x] 11. Report; **ask** before committing or pushing
