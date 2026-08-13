# TASK-741-fix Work Log — Address review findings on PR #741

Branch: `fix-afo-register-texts-numbers-split`
Findings applied from: `TASK-741-review.md`

## 2026-08-13

### Step 0 — Task artefacts

Created `TASK-741-fix-todo.md` and this log before touching any code, per the
task-tracking hard gate. This is a separate task from the review; the review's
own TODO/log do not carry forward.

### Step 1 — Design decisions

**F-1.** The defect is a unit mismatch: `MAX_QUERY_LENGTH` was compared against
`len(query)` (code points) but sized as if it were bytes. Two changes:

1. Rename the constant to `MAX_QUERY_BYTES`. The bug was possible because the
   name did not carry the unit; putting it in the name is what stops a future
   reader reintroducing `len(query)`.
2. Compare `len(query.encode("utf-8"))` and say "bytes" in the 422 message.

Verified in the review that this alone caps the worst case at 4.24 MB, so no
other constant needs to move.

**F-2.** Guard on `Content-Length` before `req.media` parses the body. The limit
is derived from the constants already in the module rather than hand-picked:
a JSON string can escape one source character to at most six bytes (`\u00XX`),
so the largest legitimate body is bounded by
`MAX_TEXTS_AND_NUMBERS_QUERIES * (MAX_QUERY_BYTES * 6 + 3) + 2`.

Honest limitation, recorded rather than glossed over: a request using
`Transfer-Encoding: chunked` has no `Content-Length`, so this guard cannot see
its size and the body is still parsed before validation. Fully closing that
requires a body-size limit at the WSGI server or reverse proxy, which is
API-wide and outside this endpoint. The guard covers every client that sends a
`Content-Length`, which is the realistic case.

### Step 2 — Implementation

`ebl/afo_register/web/afo_register_records.py`:

- `MAX_QUERY_LENGTH = 500` -> `MAX_QUERY_BYTES = 500`. The rename also removes a
  name collision: `ebl/dossiers/infrastructure/mongo_dossiers_repository.py`
  already defines an unrelated `MAX_QUERY_LENGTH = 256`.
- `validate_query` now tests `len(query.encode("utf-8")) > MAX_QUERY_BYTES` and
  reports "at most 500 bytes allowed" instead of "characters".
- New `validate_request_size(content_length)`, called from `on_post` **before**
  `req.media`, with `MAX_REQUEST_BYTES` derived from the existing constants:
  `1000 * (500 * 6 + 3) + 2 = 3,003,002` bytes.
- `req.content_length` is `Optional[int]`; the guard is written
  `if content_length and ...` so an absent length is one expression, not a
  separate branch.

`ebl/tests/afo_register/test_afo_register_route.py`: import and single use of
`MAX_QUERY_LENGTH` updated to `MAX_QUERY_BYTES`. No test removed or disabled.

New `ebl/tests/afo_register/test_afo_register_request_limits.py` (74 lines) with
7 tests. A new module was required, not a preference: the route test file was
already at 223 lines and adding these would have broken the 250-line gate.

### Step 3 — Errors made and how they were recovered

1. **`pkill` killed my own shell.** `pkill -f "scratchpad/serve.py"` matched the
   shell running it (exit 144), so the old server was never replaced and the log
   I then read was stale. Recovered by using the regex `serve[.]py`, which does
   not match its own literal command line, and by splitting stop/start into
   separate invocations.
2. **Stale reproduction script.** `exercise2.py` still imported
   `MAX_QUERY_LENGTH` and failed on import after the rename. Updated it; the
   in-process call then raised `DataError` — the fix working, but it meant the
   script's own assertion was now the wrong shape, so I wrote
   `verify_f1_fixed.py` to drive the live route instead.
3. **Miscomputed boundary probe.** My first "at the byte limit" probe built
   `SIGN * 124 + " " + SIGN` = 501 bytes, not 500, so its 422 looked like a
   false rejection. Rebuilt at exactly 500 bytes and re-checked both sides.

### Step 4 — Runtime re-verification against the REBUILT service (HARD GATE)

Restarted the service and confirmed the running process was the current tree
(`MAX_QUERY_BYTES = 500`, `MAX_REQUEST_BYTES = 3003002`, `validate_query`
encodes UTF-8, `on_post` calls `validate_request_size`) before trusting any
result.

| Case | Before fix | After fix |
| --- | --- | --- |
| F-1 payload: 434 wide queries, 2.39 MB | **500** too large | **422** |
| Wide query at exactly 500 bytes | n/a | 200 |
| Wide query at 501 bytes | n/a | 422 |
| F-2: `Content-Length` over the cap | parsed, then 422 | 422, unparsed |
| `["OrNS 59, 17"]` (the original bug) | 200, 2 records | 200, 2 records |

All ten previously-passing runtime cases were re-run and behave identically,
except the one message that intentionally changed from "characters" to "bytes".

### Step 5 — Gates

| Gate | Result |
| --- | --- |
| `task format` | PASS — 803 files already formatted |
| `task lint` (ruff) | PASS |
| `task type` (**pyre**) | PASS — no type errors found |
| `task type-pyright` | PASS — 0 errors, 0 warnings, 0 informations |
| `flake8 --max-line-length=120` | PASS — exit 0 |
| `mypy --ignore-missing-imports` | PASS — 3 files, no issues |
| Coverage on changed modules | PASS — **100%**, 0 missed |
| 250-line gate | PASS — 104 / 223 / 74 lines |
| `task test` | PASS — 4330 passed, 2 skipped, 1 xfailed, 0 failures |
| `task lint-md` | PASS — 0 errors |

The suite went from 4323 to 4330 passed: the 7 new tests, no test lost.

Mixed-type-array gate: nothing changed shape. `MAX_REQUEST_BYTES` is an int,
`content_length` is `Optional[int]`, `query_list` stays `List[str]`. No array
gained a second type.
