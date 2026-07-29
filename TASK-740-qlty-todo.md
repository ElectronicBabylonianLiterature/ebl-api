# TASK-740-qlty TODO — Address all qlty issues on PR #740

- [x] Determine the authoritative source of current qlty findings
- [x] Check the PR's qlty gate — `qlty check` passes, "No blocking issues"
- [x] Check every qlty review thread — all 14 resolved
- [x] Confirm which findings were cleared by `080766a9` / `d6208283`
- [x] Run qlty locally and diff against an `origin/master` baseline
- [x] Confirm the uncommitted test change introduces no qlty finding
- [x] Clean up: removed the generated `.qlty/qlty.toml` and the baseline
      worktree, leaving the repo as found
- [x] Report: no outstanding qlty issues
- [ ] **Awaiting decision** — refactor the three `of` signatures whose
      parameter count this branch raises by one (`word_tokens` 11→12,
      `greek_tokens` 10→11, `normalized_akkadian` 9→10)? Not qlty-blocking.
- [ ] Remove the TASK-740* `.md` files before the PR is merged

No code changed in this task, so the format / lint / type / test / coverage
gates have no new surface to cover; the previous task's gate results still
stand and the working tree is unchanged apart from that task's test edit.
