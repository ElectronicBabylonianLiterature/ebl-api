# TASK-741 TODO

Review of PR #741 — *Fix AfO Register texts-numbers match for references
containing spaces*.

## Scope

Fetch every piece of existing PR feedback, check CI status and qlty findings,
and produce `TASK-741-review.md` with a short friendly summary section first,
followed by a `Details` subsection carrying the full findings.

## Steps

- [x] Create task TODO and log files (this file + `TASK-741-log.md`)
- [x] Identify PR number, branch, base, and merged-in branches
- [x] Fetch submitted reviews (`/pulls/741/reviews`) — 2 reviews
- [x] Fetch inline diff review comments (`/pulls/741/comments`) — 0
- [x] Fetch issue/conversation comments (`/issues/741/comments`) — 1
- [x] Fetch review-thread resolution state (GraphQL) — 0 threads
- [x] Fetch feedback from any PR whose branch was merged into this one — only
      `origin/master` merges, none touching `ebl/afo_register/`
- [x] Check CI status: `gh pr checks 741` — no failing checks; 2 test jobs still
      in progress; duplicate workflow runs on the same head
- [x] Collect qlty findings — CI `qlty check` passes with no blocking issues;
      local CLI not initialized in this repo and deliberately not initialized
- [x] Read the full PR diff and the changed source/test files
- [x] Verify each reported finding against the current tree — all 4 addressed
- [x] Check the diff against the mixed-type-array hard gate — passes
- [x] Check the 250-line-per-`.py`-file hard gate — all 5 files pass
- [x] Check coverage of changed modules — 100%
- [x] Run the modified backend service and exercise the affected route — 16
      request bodies plus an index `explain`
- [x] Write `TASK-741-review.md`: friendly short summary first, then `Details`
- [x] Suppress the markdown line-length limit for `Details` only, inline —
      `.markdownlint.json` untouched (none exists in the repo)
- [x] Run `task lint-md` — 0 errors across 7 files
- [x] Full test suite — result recorded in `TASK-741-log.md`
- [x] Re-read the copilot instructions and report which gates ran
- [x] Remind the user to remove the task TODO/log/review files before merge
- [x] Do **not** commit or push — tree left uncommitted

## Open items for the author (not blocking)

- L1: reconcile `MAX_CANDIDATES` with the route limits, or reword its message
- L2: annotate `candidate_splits` as taking `str`, keeping the runtime guard
- L3: delete `TASK-741-{todo,log,review}.md` and fix the stale filenames in the
      PR body's "Before merge" section
- Get a re-review from `Fabdulla1` to clear the `CHANGES_REQUESTED` block
