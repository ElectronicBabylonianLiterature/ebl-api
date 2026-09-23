# TASK pr735-rereview — TODO

- [x] Create TODO and log first
- [ ] Record PR metadata (head SHA, size, commits, state)
- [ ] Fetch all feedback: reviews, inline comments, issue comments (Sourcery,
    qlty, Codex, humans, all agents)
- [ ] Fetch feedback for any PR merged into this branch
- [ ] Check CI checks, qlty, CodeQL alerts on the head
- [ ] Check the diff for dev container / config changes (warn if any)
- [ ] Check the diff for new `.md` files
- [ ] Read the full diff; check data hard gate, 250-line gate, comments, type
    hints, tests
- [ ] Run local gates: format, lint, pyre, pyright, mypy, flake8, full tests,
    changed-module coverage, lint-md
- [ ] Run the service locally (127.0.0.1:27017, never `.env`) and exercise
    `/realia/all` and `/realia/{id}`
- [ ] Rewrite `TASK-pr735-review.md`: metadata header with verdict, short
    friendly summary first, template sections, "Details" subsection, no
    line-length limit
- [ ] Never refer to `khoidt` in the third person
- [ ] Re-read copilot instructions and report gates; remind to remove TASK files
    before merge; no commits
