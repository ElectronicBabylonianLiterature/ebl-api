# TASK pr735 — TODO

Review PR #735 (linked review 5367106362).

- [x] Fetch PR metadata (title, author, branches, head SHA, state, files)
- [x] Fetch all reviews, inline comments, issue comments (Sourcery, qlty, Codex,
      CodeQL, humans)
- [x] Fetch feedback of any PR merged into this branch
- [x] Check CI status checks (failing checks)
- [x] Check qlty results (Cloud + local `qlty smells --include-tests`, HEAD vs
      origin/master)
- [x] Check CodeQL alerts
- [x] Check for dev container configuration changes (warn explicitly)
- [x] Check for new `.md` files
- [x] Read the full diff; check data hard gate (no mixed-type arrays), 250-line
      limit, type hints, comments, tests/coverage
- [x] Check out PR locally; run gates relevant to the review (lint, type x3,
      tests, coverage on changed files)
- [x] Run the modified backend service and exercise affected routes (local Mongo
      only)
- [x] Write `TASK-pr735-review.md`: metadata header + verdict, friendly summary
      first, Summary/Findings/Severity/Reproduction Steps/Recommendation,
      Details subsection, no line wrapping
- [x] Address every existing unresolved PR finding in the review
- [x] `task lint-md` on the task/review files
- [x] Re-read instructions; report gates run; remind to remove TASK files before
      merge
