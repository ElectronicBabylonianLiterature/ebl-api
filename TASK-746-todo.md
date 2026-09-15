<!-- markdownlint-disable MD013 -->
# TASK-746 — TODO: finish the outstanding work from the PR #743 handoff

Source of truth: `TASK-745-handoff.md` section 5, "Order of operations".
Steps 1 and 2 there are already done. This task covers steps 3-8.

## 0. Orientation

- [x] Confirm working tree / branch state and that local and remote agree
- [x] Confirm the three uncommitted TASK-745 file edits are intentional
- [x] Re-read `.github/instructions/copilot.instructions.md` gates (done at session start)

## 1. Step 3 — qlty Cloud's 5 blocking issues

- [x] Re-attempt CLI enumeration (`qlty smells`, `qlty check --no-fix`) on the
      full PR file list
- [x] Re-check qlty PR comments / reviews for anything newer than 2026-09-02
- [x] Enumerated via master-vs-HEAD smells diff with `--include-tests`; A/B justified, C/D fixed. Cloud's exact count of 5 still needs the browser page
- [x] If still not enumerable: report to the user that this needs the browser
      page; do NOT declare it stale on inference

## 2. Step 4 — redo the lost frontend change (gate 1)

- [x] Decide where the frontend checkout lives so the work cannot be lost again
- [x] Add `nameBreaks` to `NamedSign` and the `nameTokens` helper
- [x] Route `extractEnclosureTypes` and `addAccents` through the helper
- [x] Tests: split input, no breaks, trailing break, legacy interleaved, explicit null
- [x] `yarn install` (Node 20), `yarn lint`, `tsc`, `yarn test`
- [x] STOP before commit/push/PR — ask

## 3. Step 5 — run the migration (gate 2)

- [x] Target chosen by user: local throwaway on 127.0.0.1:27017 (`.env` never sourced)
- [x] Dry run on the throwaway: 2/1/1, wrote nothing
- [x] `--apply` on the throwaway only; no real database touched
- [x] Re-ran dry run: 0/0/0, idempotent; migrated docs round-trip through the new schema

## 4. Step 6 — PR description

- [x] Applied `TASK-743-fix-pr-body.md` via `gh api ... -X PATCH -F body=@file`
      (only when the user asks; `gh pr edit --body` fails silently here)

## 5. Step 7 — cleanup checklist (gate 3) — PRE-MERGE ONLY, not yet run

- [ ] Delete the fourteen branch-only files (plus this task's two/three)
- [ ] Verify with the two commands in handoff section 8
- [ ] Drop the throwaway Mongo databases

## 6. Close-out

- [x] Re-read the instructions file and state which gates ran and their results
- [x] Reported; left uncommitted until the user asked
- [x] Rewrite `TASK-745-handoff.md` with the current state and next steps
- [x] Run the full pre-commit gate list, then commit (user asked in their own words)

## 7. Carried forward — next steps

- [ ] Reconcile qlty Cloud's 5 blocking issues against the 4 found (needs the
      login-only issues page; do NOT assume stale)
- [ ] Branch, commit and open the frontend PR from `/workspaces/ebl-frontend`
- [ ] Run the migration against a named real database (dry run first)
- [ ] Push the branch so qlty and CodeQL re-run on the current HEAD
- [ ] Run the gate 3 cleanup checklist — sixteen files — only after the above
