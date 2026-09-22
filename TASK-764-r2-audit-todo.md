# TASK-764-r2-audit — TODO

Account for every outstanding finding, on both PRs. Triggered by "Did you
address all the findings?" — the honest answer needs PR #764's own feedback
fetched first, which has never been done in this session.

## Gates to honour

- [x] Re-read `.github/instructions/copilot.instructions.md` before reporting complete
- [x] TODO + log created before any work (this file + `TASK-764-r2-audit-log.md`)
- [x] Nothing committed or pushed
- [x] No test removed, disabled or skipped without explicit approval
- [x] No linter / formatter / type-checker configuration modified
- [x] Every changed `*.py` stays at or under 250 lines; changed source at 100% coverage
- [x] One array never holds two data types

## Steps

- [x] 1. Audit the round-14 findings R14-1..R14-10 and state each one's real status
- [x] 2. **Fetch all PR #764 feedback** — reviews, inline comments, issue comments,
      bots (Sourcery, qlty, CodeQL, GitGuardian); this has not been done
- [x] 3. Fetch #764's CI, qlty and CodeQL state
- [x] 4. Enumerate every #764 finding still unresolved
- [x] 5. Check #764 for stray `TASK-*.md` / non-`ebl/` added files
- [x] 6. Check the #764 diff against the data hard gate and the file-length gate
- [x] 7. Address what is genuinely outstanding
- [x] 8. Resolve R14-4 — decided 2026-09-17: keep it in #743 (split the instructions change, or record the decision)
- [x] 9. Run the gates over anything changed
- [x] 10. Report: what was outstanding, what is fixed, what remains and why

<!-- markdownlint-configure-file { "MD013": false } -->
