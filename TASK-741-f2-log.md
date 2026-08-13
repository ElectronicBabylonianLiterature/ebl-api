# TASK-741-f2 Work Log — Close the chunked-body gap

Branch: `fix-afo-register-texts-numbers-split`

## 2026-08-13

### Step 0 — Task artefacts

Created `TASK-741-f2-todo.md` and this log before touching code.

### Step 1 — The premise of this task was WRONG, and I disproved it

I set out to add a capped read (`req.bounded_stream.read(MAX_REQUEST_BYTES + 1)`
plus a manual `json.loads`) to close the chunked gap. I implemented it, and the
tests failed with an empty body. Instead of patching the tests, I probed falcon
directly — and the failure was telling me the gap does not exist.

**falcon 3.1.3, WSGI:**

| Case | Behaviour |
| --- | --- |
| No `Content-Length` (chunked), 5 MB sent | reads **0 bytes** |
| No `Content-Length`, then `req.media` | `MediaNotFoundError` (400) |
| `Content-Length: 100`, 5 MB sent | reads exactly **100 bytes** |
| `Content-Length` over the cap | rejected before `req.media` |

`Request.bounded_stream` is constructed with `content_length`; when that is
`None` it yields nothing. So a chunked request never gets its body materialised
by the app — it gets a 400. The "multi-gigabyte body parsed before validation"
scenario I described in F-2 cannot happen through falcon.

**Conclusion: the endpoint's body read was already bounded in every case** by
the `Content-Length` guard added in TASK-741-fix. My stated "remaining
limitation" was an assumption about falcon that I had never verified, and it
was wrong.

### Step 2 — Reverted the unnecessary change

Removed `read_json_body`, `INVALID_JSON_MESSAGE` and the `json` import, and
restored `validate_request_size(req.content_length)` + `req.media` in `on_post`.

Reason for reverting rather than keeping it as belt-and-braces: it changed the
response for an empty or malformed body from falcon's 400 to a 422, replaced
falcon's well-tested media handling with hand-rolled parsing, and bought
nothing. Kept the `REQUEST_TOO_LARGE_MESSAGE` constant extraction, which is a
genuine tidy-up.

Replaced the `read_json_body` tests with two that **pin the falcon behaviour my
safety argument depends on**, so a future falcon upgrade that changed it would
fail loudly instead of silently reopening the hole:

- `test_a_body_without_content_length_is_never_read`
- `test_a_body_is_never_read_beyond_its_content_length`

### Step 3 — The real residual risk, and the real fix

The body never reaches the app unbounded, but **waitress buffers the request
body before the app runs**, and its `max_request_body_size` defaults to
**1 GB**. That is the genuine exposure, and it sits exactly where I originally
said it belonged: the server layer.

Checked first that a global cap is safe: all 28 `on_post` / `on_put` handlers
are JSON, no route reads a raw or binary body, and GridFS has no
route-reachable write path. So no upload can be broken by this.

`Dockerfile`: added `--max-request-body-size=67108864` (64 MB) to the
`waitress-serve` command — a 16x reduction from the default, still far above any
plausible JSON payload for this API.

Verified end to end by running waitress with the exact production flags against
a trivial WSGI app:

- 1,000,000 byte body -> **HTTP 200**, "read 1000000 bytes"
- 67,108,865 byte body (one over the cap) -> **connection reset**, refused

Also confirmed the flag parses into the adjustment correctly
(`max_request_body_size = 67108864`, `connection_limit = 500`, `port = 8000`).

### Step 4 — Errors made and recovered

1. **Acted on an unverified assumption.** I wrote F-2's "remaining limitation"
   into the review without testing falcon. Building the fix is what exposed it.
   Recovered by probing falcon, reverting, and correcting the review.
2. **`pkill` self-match, again.** `pkill -f "waitress-serve --port=8901"`
   matched its own shell (exit 144). Same trap as earlier in the session; the
   results were already printed so nothing was lost.
3. **Bad verification script.** My first waitress check passed `parse_args`
   output straight into `Adjustments(**kw)`, which contains a `help` key, and
   raised `ValueError: Unknown adjustment 'help'`. Filtered the keys and re-ran
   rather than concluding the flag was invalid.

### Step 5 — Runtime re-verification after the revert (HARD GATE)

Restarted the service and confirmed the running process was the reverted tree
(`read_json_body` absent, `on_post` back on `req.media`, size guard present)
before trusting results. All eleven cases behave exactly as before the revert:

- `["OrNS 59, 17"]` -> 200, 2 records (original bug still fixed)
- F-1 payload (434 wide queries) -> **422**, not 500
- oversized `Content-Length` -> 422
- all five other rejection paths -> 422 with unchanged messages

### Step 6 — Gates

| Gate | Result |
| --- | --- |
| `task format` | PASS |
| `task lint` (ruff) | PASS |
| `task type` (**pyre**) | PASS — no type errors |
| `task type-pyright` | PASS — 0 errors, 0 warnings |
| `flake8 --max-line-length=120` | PASS |
| `mypy --ignore-missing-imports` | PASS — 3 files |
| Coverage on changed modules | PASS — **100%**, 0 missed |
| 250-line gate | PASS — 105 / 97 lines |
| `task test` | PASS — 4332 passed, 2 skipped, 1 xfailed, 0 failures |
| `task lint-md` | PASS — 0 errors |

Suite went 4330 -> 4332: two new pinning tests, four `read_json_body` tests
added then removed with the revert. No pre-existing test lost.
