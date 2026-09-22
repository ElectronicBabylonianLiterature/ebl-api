# TASK-764-r4-docs — TODO

Add the task documentation to commit `d83582a2`, at the user's explicit request.
This reverses the earlier call to keep them untracked.

## Gates to honour

- [x] Re-read `.github/instructions/copilot.instructions.md` before reporting complete
- [x] TODO + log created before any work, names checked against `git ls-files`
- [x] Amend once, on this explicit request; `d83582a2` is **unpushed**, so no
      pushed history is rewritten
- [x] Do not push
- [x] `task lint-md` clean on every markdown file committed

## Steps

- [x] 1. Correct `TASK-CURRENT-handoff.md`, which currently says "do not commit
      this file" — that would be committed as a falsehood
- [x] 2. Update the merge checklist: the documents are now tracked on #764 and
      must be removed before merge
- [x] 3. Stage every task document
- [x] 4. Confirm no Python file changed, so gates 1-9 still stand from `d83582a2`
- [x] 5. Run `task lint-md`
- [x] 6. Amend the commit
- [x] 7. Confirm nothing was pushed, and report the consequence for the
      stray-files gate

<!-- markdownlint-configure-file { "MD013": false } -->
