# TASK-741-recheck TODO — Sweep for remaining findings on PR #741

Branch: `fix-afo-register-texts-numbers-split`
Trigger: user asked whether any findings remain unaddressed.

## Scope

Find and fix anything still outstanding. Two categories deserve a fresh look:

1. The code **I** wrote in TASK-741-fix has been reviewed by nobody.
2. One behavioural question from the original diff that I noticed while
   reviewing but never chased to a conclusion: `candidate_splits` never
   produces an empty `text` or `textNumber`, so a single-token query matches
   nothing. Did the **old** implementation match such records via its
   concat fallback? If so this PR is an unflagged behaviour regression.

## TODO

- [x] 1. Create this TODO and `TASK-741-recheck-log.md` before starting
- [x] 2. Self-review the TASK-741-fix changes for defects
  - [x] 2a. Re-derive the post-fix worst-case BSON filter size and measure it
  - [x] 2b. Check `MAX_JSON_ESCAPE_EXPANSION = 6` is genuinely the max ratio
  - [x] 2c. Confirm no legitimate request is rejected by `MAX_REQUEST_BYTES`
  - [x] 2d. Check `Content-Length` cannot be used to smuggle a larger body
- [x] 3. Chase the single-token / empty-field question to a conclusion
  - [x] 3a. Read the **old** `split_text_and_number` + `_build_fallback_pipeline`
        from git history
  - [x] 3b. Determine what the old code returned for a single-token query and
        for records with an empty `text` or `textNumber`
  - [x] 3c. If behaviour changed, decide whether it is a regression to fix or
        intended, and prove it against a running service
- [x] 4. Re-check unresolved GitHub state (thread `3776566330`, CI)
- [x] 5. Fix anything found; if nothing is found, say so plainly
- [x] 6. Gates on any change: format, lint, pyre, pyright, mypy, flake8,
      test, lint-md, 100% coverage, 250-line limit
- [x] 7. Runtime verification of any behaviour change
- [x] 8. Update `TASK-741-review.md` with the outcome
- [x] 9. Re-read the copilot instructions and report gates
- [x] 10. Remind to remove all `TASK-741*.md` before merge

## Constraints

- No commit / push / GitHub write without an explicit request in that message.
