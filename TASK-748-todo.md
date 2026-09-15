<!-- markdownlint-disable MD013 -->
# TASK-748 — TODO: address the remaining issues before merge

## 1. PR feedback on #743 (hard gate)

- [x] Scope: **PR #743 only** (user: "In this PR")
- [x] Reviews, inline diff comments, issue comments, bots — 41 threads, 3 unresolved
- [x] All three addressed: Sourcery's bug_risk is closed by the `@final` this PR adds; the two qlty duplications are justified

## 2. Durable justification for the 2 qlty findings

- [x] Moved into `TASK-743-fix-pr-body.md` -> the PR description, which
      survives gate 3

## 3. The instructions-file gap

- [x] Fixed, with proof: the old command analysed **0 files**. Also documented
      the whole-repo diff method and Cloud's per-file counting

## 4. CI

- [x] Checks on #743 green through `15da7c12`; `38b042a6` re-running
- [x] #764 fully green, no blocking issues

## 5. Cannot be addressed here

- [ ] Frontend push — no credential in this environment reaches `ebl-frontend`
- [ ] Gate 3 cleanup — premature; it deletes the handoff while work is open

## 6. Close-out

- [x] Re-read the instructions file; gates and results stated
- [ ] Ask before any commit or push

## 7. Needs the user

- [x] Commit and push these changes — `5c94f201`
- [x] Applied `TASK-743-fix-pr-body.md` to the #743 description, verified
- [ ] Optionally reply to / resolve the Sourcery thread on GitHub
- [ ] Gate 3 cleanup — deliberately NOT done: it deletes the handoff the
      frontend push still depends on
