# TASK-741-fix TODO — Address review findings on PR #741

PR: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/741>
Branch: `fix-afo-register-texts-numbers-split` -> `master`
Source of findings: `TASK-741-review.md`

## Scope

Apply both findings from the review. Code changes explicitly requested.

## TODO

- [x] 1. Create this TODO and `TASK-741-fix-log.md` before starting work
- [x] 2. **F-1 (blocking)** — bound query length in UTF-8 bytes, not code points
  - [x] 2a. Rename `MAX_QUERY_LENGTH` -> `MAX_QUERY_BYTES` so the unit is in
        the name and the bug cannot silently recur
  - [x] 2b. Enforce `len(query.encode("utf-8"))` in `validate_query`
  - [x] 2c. Update the 422 message to say bytes, not characters
  - [x] 2d. Update the import in `test_afo_register_route.py`
- [x] 3. **F-2** — bound the request before the body is parsed into memory
  - [x] 3a. Add a `Content-Length` guard that runs before `req.media`
  - [x] 3b. Derive the limit from the existing constants, not a magic number
  - [x] 3c. Record the chunked-transfer-encoding limitation honestly
- [x] 4. Tests (new module — `test_afo_register_route.py` is at 223 lines and
      would break the 250-line gate)
  - [x] 4a. 4-byte UTF-8 query rejected at the byte bound
  - [x] 4b. Query at exactly the byte bound accepted
  - [x] 4c. Oversized `Content-Length` rejected before parsing
  - [x] 4d. Missing `Content-Length` handled
  - [x] 4e. Route-level 422 for the wide-UTF-8 case
- [x] 5. Re-run the F-1 reproduction against the rebuilt service; it must now
      return 422 instead of 500 (HARD GATE: re-verify after every rewrite)
- [x] 6. Confirm the previously-passing runtime cases still behave (no regression)
- [x] 7. Gates: `task format`, `task lint`, `task type` (pyre),
      `task type-pyright`, `task test`, `task lint-md`
- [x] 8. `flake8 --max-line-length=120`, `mypy --ignore-missing-imports`
- [x] 9. 100% coverage on every changed file
- [x] 10. 250-line gate on every touched `*.py`
- [x] 11. Mixed-type-array gate on the changed shapes
- [x] 12. Update `TASK-741-review.md` to reflect the resolved findings
- [x] 13. Re-read `.github/instructions/copilot.instructions.md`; report gates
- [x] 14. Remind to remove all `TASK-741*.md` before merge

## Constraints

- No `git commit` / `git push` / `gh pr` write operations without an explicit
  request in that message.
- Do not weaken or reconfigure any linter to make a gate pass.
