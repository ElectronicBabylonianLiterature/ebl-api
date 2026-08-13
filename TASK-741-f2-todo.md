# TASK-741-f2 TODO — Close the chunked-body gap in F-2

Branch: `fix-afo-register-texts-numbers-split`

## Problem

`validate_request_size` only inspects `Content-Length`. A request sent with
`Transfer-Encoding: chunked` carries no `Content-Length`, so the guard passes
and `req.media` still parses an unbounded body into memory.

## Approach — planned, then corrected mid-task

**Original plan (abandoned):** bound the read at this endpoint —
`req.bounded_stream.read(MAX_REQUEST_BYTES + 1)` plus a manual `json.loads` —
assuming a global cap would break large uploads.

**What testing showed:** both halves of that plan were wrong.

1. The gap does not exist. In falcon 3.1.3 a request with no `Content-Length`
   yields **zero bytes** from `bounded_stream`, so a chunked body is never
   parsed. The endpoint was already fully bounded.
2. A global cap is in fact safe — every write handler is JSON and no route
   reads a raw or binary body, so there are no uploads to break.

**Actual fix:** revert the endpoint change; cap the body at the server, where
the real exposure was (waitress defaulted to 1 GB).

## TODO

- [x] 1. Create this TODO and `TASK-741-f2-log.md` before starting
- [x] 2. Confirm the premise before coding to it
- [x] 3. ~~Replace `req.media` with a capped read~~ — implemented, then
      **reverted**: it closed a gap that does not exist and turned falcon's
      400 for an empty body into a 422
- [x] 4. Tests
  - [x] 4a. Pin that a body with no `Content-Length` is never read
  - [x] 4b. Pin that a body is never read beyond its `Content-Length`
  - [x] 4c. Oversized `Content-Length` still rejected
  - [x] 4d. Existing route behaviour unchanged
- [x] 4e. Cap the body at the server: `--max-request-body-size` in `Dockerfile`
- [x] 5. Gates: format, lint, pyre, pyright, mypy, flake8, test, lint-md
- [x] 6. 100% coverage on changed files; 250-line limit on touched `*.py`
- [x] 7. Runtime verification against the rebuilt service, including an actual
      chunked request (HARD GATE: re-verify after every rewrite)
- [x] 8. Update `TASK-741-review.md`
- [x] 9. Re-read the copilot instructions; report gates
- [x] 10. Remind to remove all `TASK-741*.md` before merge

## Constraints

- No commit / push / GitHub write without an explicit request in that message.
