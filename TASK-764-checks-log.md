# TASK-764-checks LOG — Verify remote checks and the release ordering

Running log of what was actually done, including every error and its recovery.

## Entries

### 1. Task start

- Request: monitor the remote checks on the pushed commit until they are all
  green, and separately verify a proposed five-step release ordering.
- New task, so a new TODO and log pair was created before any work. These two
  files are uncommitted: no commit was authorised in this message.
- Confirmed the push landed: local and remote both at
  `24ff519b0c004f8b20fbece17cf524139ac34e3a`, and PR #764's head moved to it.
- First look at the checks: Analyze (python), CodeQL, Sourcery review,
  GitGuardian (x3) and qlty check already pass; the six Test Python jobs
  (3.11, 3.12, pypy-3.11, across two workflow runs) are pending.

### 2. Remote checks on `24ff519b` — all green

Final rollup: **15 SUCCESS, 2 SKIPPED, 0 failures.**

| Check | Result |
| --- | --- |
| Analyze (python) | pass |
| CodeQL | pass |
| GitGuardian Security Checks | pass |
| GitGuardian scan (x2) | pass |
| Sourcery review | pass |
| Test Python 3.11 (x2) | pass |
| Test Python 3.12 (x2) | pass |
| Test Python pypy-3.11 (x2) | pass |
| qlty check | pass, "No blocking issues" |
| qlty coverage | pass, 96.0% (0.0% change) |
| qlty coverage diff | pass, 100.0% against a 75% threshold |
| docker (x2) | skipped by design |

`mergeStateStatus` is no longer BLOCKED on a check; `reviewDecision` is still
`REVIEW_REQUIRED`, which is the only thing holding the PR.

Sourcery's *check* passed but it did not post a new review. The two inline
comments on the PR still point at `aaffba18` lines 82 and 96, which no longer
exist. Both are fixed; they are stale, not outstanding. Comment
`@sourcery-ai review` to get a fresh pass, or `@sourcery-ai resolve` to clear
them.

### 3. Ordering verified — two errors found

- Steps 1 and 2 are right in direction. Frontend #817 is a tolerant reader
  (returns `nameParts` untouched when `nameBreaks` is absent), cut from master,
  7 files, all checks green, so it is genuinely independent and safe to deploy
  before ebl-api #743.
- Step 2 is incomplete: it stops at "deploy backend" and omits ebl-api #764,
  which must RUN after #743 is deployed, and the follow-up PR that deletes the
  `@pre_load` adapter.
- Step 3 needs the PR number, #773, and a warning: the branch is 18 commits
  behind master and diverged.
- Step 4 is wrong in two ways. #774's base is `chore/ts7-tsconfig-migration`,
  not master, so it needs retargeting as well as rebasing. And "picks up our
  test fix for free" is false as written: the fix is not on master, it is in
  **#817**. The failing test is
  `FragmentService.queries.test.ts > returns traditional reference to fragment
  numbers mapping data`, which compares two Promise objects whose
  `Symbol(async_id_symbol)` differ; #817 changes it to await the promise and
  compare the resolved value. The file's last change on master was 2026-08-04.
  #774 already contains `adc159d4`, the only recent test fix on master, and
  that one is a different test.
- Therefore the "separately, no deadline, any time" separator is wrong: step 4
  depends on step 1.

### 4. Corrected ordering delivered

The user's original diagram had four errors. Corrected version recorded here so
it is not lost:

```text
CHAIN A — the nameParts/nameBreaks split (strictly ordered)

1. ebl-frontend #817  add-name-breaks -> master      MERGE + DEPLOY FRONTEND
        |                                            7 files, cut from master,
        |                                            tolerant reader, all green
        v
2. ebl-api #743  fix-type-checker-blind-spots -> master
        |                                            MERGE, then DEPLOY BACKEND
        |                                            (202 files; drop its 24 .md
        |                                             files first)
        v
3. ebl-api #764  migrate-name-breaks -> master       MERGE any time (all green),
        |                                            but RUN only here:
        |                                              dry run -> read counts
        |                                              --apply
        v
4. ebl-api  follow-up PR                             DELETE the @pre_load adapter
                                                     separate_legacy_name_parts

CHAIN B — the bluebird removal
NOT independent: step B2 needs A1 merged.

B1. ebl-frontend #773  chore/ts7-tsconfig-migration -> master
        |                18 commits behind master and diverged; update it first
        v
B2. ebl-frontend #774  chore/remove-bluebird
        |                RETARGET from chore/ts7-tsconfig-migration to master
        |                (its base is not master), then rebase.
        |                The test fix is in #817, NOT on master, so this only
        |                goes green once A1 has merged.
        v
B3. #774 -> master       also clear qlty's 9 blocking issues
```

Errors corrected:

1. #764 and the adapter-deletion PR were missing from the sequence entirely.
2. The "separately, no deadline, any time" separator was wrong: B2 depends on
   A1, because the fix for #774's failing test lives in #817.
3. Step 3 needed its PR number (#773) and a warning that the branch is 18
   commits behind master.
4. #774's base is `chore/ts7-tsconfig-migration`, so it needs retargeting, not
   only a rebase.
