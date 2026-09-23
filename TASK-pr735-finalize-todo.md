# TASK pr735-finalize — TODO

- [x] Create TODO and log first
- [x] Pre-commit gates in order: format, lint, pyre, pyright, full tests,
      changed-module coverage, flake8, mypy, lint-md
- [x] Commit only the 8 staged TASK deletions (approved once)
- [x] Check `git ls-remote` after the commit (commits here can auto-push)
- [x] Push once (approved once); verify the remote head and PR file list
- [x] Do not post the F2 replies (declined)
- [x] Rewrite `TASK-pr735-review.md`: metadata header with verdict, short
      friendly summary first, template sections, "Details" subsection, no
      line-length limit, no third-person mention of the author's username
- [x] Watch CI on the new head; report
