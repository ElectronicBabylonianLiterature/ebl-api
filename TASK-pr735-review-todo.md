# TASK pr735-review — TODO

Review PR #735 "Add GET /realia/all endpoint for listing Realia IDs for the
sitemap" (branch `add-realia-slugs-endpoint`).

- [x] Read copilot instructions; create TODO and log first
- [x] Fetch PR metadata, diff, file list, merge state vs `master`
- [x] Fetch all feedback: reviews, inline comments, issue comments (Sourcery,
      qlty, Codex, humans)
- [x] Fetch feedback on PRs merged into this branch
- [x] Check CI status checks (failing checks), qlty, CodeQL alerts
- [x] Check for dev container config changes (`.devcontainer/`, Dockerfile,
      compose) — warn if any
- [x] Check no new `.md` files are introduced by the PR
- [x] Read and review every changed file (correctness, regressions, security,
      coverage)
- [x] Data hard gate: no mixed-type arrays
- [x] File-length gate: no `*.py` > 250 lines
- [x] Run gates locally: format, lint, type (pyre), type-pyright, mypy, flake8,
      tests, coverage on changed modules, lint-md
- [x] Run the modified backend service and exercise `GET /realia/all` (local
      Mongo only, never `.env`)
- [x] Write `TASK-pr735-review.md`: metadata header, friendly summary,
      Summary/Findings/Details/Severity/Reproduction Steps/Recommendation, no
      line-length wrapping
- [x] Re-read instructions; report gates; remind to remove TASK files before
      merge
