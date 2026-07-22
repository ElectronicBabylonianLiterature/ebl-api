# TASK-741 — Address all review findings on PR #741

PR: Fix AfO Register texts-numbers match for references containing spaces
Branch: fix-afo-register-texts-numbers-split

## TODO

- [x] Fetch all submitted reviews (`gh api .../pulls/741/reviews`)
- [x] Fetch all inline diff review comments — none exist
- [x] Fetch all issue/conversation comments (`gh api .../issues/741/comments`)
- [x] Fetch feedback for any branch merged into this one — merge 7a2d3285 pulled
      origin/master only; no outstanding feedback
- [x] Include bot feedback (Sourcery) — captured
- [x] Catalogue every finding into TASK-741-review.md
- [x] F1: bound public endpoint (DataError → 422) in web resource
- [x] F2: add ambiguous multi-match repository test
- [x] F3: deduplicate candidates in `_build_candidate_query` + test
- [x] F4: remove task-tracking scaffolding — already done in commit 388a96aa
- [x] Data hard-gate check — no mixed-type arrays introduced
- [x] Gate: task format — clean
- [x] Gate: task lint (ruff) — passed
- [x] Gate: task type (pyre) — No type errors (1 worker; parallel workers OOM here)
- [x] Gate: pyright — 0 errors (run via npx; no `task type-pyright` exists here)
- [x] Gate: task test — 3858 passed, 0 failures
- [x] Gate: 100% coverage on both changed source modules
- [x] Gate: flake8 --max-line-length=120 — 0 errors
- [x] Gate: mypy --ignore-missing-imports — 0 errors
- [x] Gate: all touched *.py files ≤ 250 lines
- [x] Runtime verification: booted real WSGI app on a live TCP socket, curled
      the route — valid→200 (correct record), oversized→422, non-list→422
- [ ] Remove TASK-741-{todo,log,review}.md before merge (reminder)
