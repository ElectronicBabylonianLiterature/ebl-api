# TASK-741 Review — PR #741

PR: [Fix AfO Register texts-numbers match for references containing spaces][pr]
Branch: `fix-afo-register-texts-numbers-split` -> `master`
Head reviewed: `15c060bf` · State: OPEN, MERGEABLE, `mergeStateStatus: CLEAN`
GitHub review decision: **APPROVED** (Fabdulla1, with one comment outstanding)

[pr]: https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/741

> **Update — both findings have since been fixed on this branch.**
> F-1 and F-2 were applied at the user's request; see `TASK-741-fix-log.md`.
> The F-1 payload that returned HTTP 500 now returns HTTP 422 against the
> rebuilt service, and the original bug still returns its 2 records. The
> findings below are kept as the record of what was found and why.

## Summary

The change is correct and well-tested, and it genuinely fixes the reported bug.
`POST /afo-register/texts-numbers` previously recovered `(text, textNumber)` from
a joined string by splitting on the last space, which is unrecoverable in
principle because both fields routinely contain spaces. Replacing that with
`candidate_splits` — enumerate every split point and `$or` them — is provably
equivalent to matching the concatenation while still using the compound
`(text, textNumber)` index. I confirmed the fix against the running service:
`["OrNS 59, 17"]` now returns the record it should, and the near-miss
`("OrNS", "59, 170")` decoy is correctly excluded.

Because that rewrite turns one request into an unbounded fan-out of `$or`
clauses, the PR then added request bounds. Those bounds are the right idea and
are nearly right, but **one of them is off, and the reviewer already spotted it**:
`MAX_QUERY_LENGTH` counts Python code points, not UTF-8 bytes. I reproduced the
consequence end to end against the shipping code — a request that passes every
single validator still builds a **17.9 MB** BSON filter and the endpoint answers
**HTTP 500**. That is the exact failure mode this PR set out to eliminate, still
reachable, on an endpoint an unauthenticated caller can hit.

Recommendation: **one blocking change** (F-1), a one-line fix the reviewer has
already proposed. Everything else is clean.

All CI checks pass, including `qlty check` (no blocking issues) and
`qlty coverage diff` (100.0%). All local gates pass. This is not a "CI is red"
situation — the defect is invisible to the current test suite because every
existing test uses ASCII.

## Findings

### F-1 (Blocking) — `MAX_QUERY_LENGTH` bounds code points, not bytes

**File:** [ebl/afo_register/web/afo_register_records.py:22-25](ebl/afo_register/web/afo_register_records.py#L22-L25)
**Origin:** Fabdulla1, inline comment `3776566330` — **still unresolved**
(`isResolved=false`, `isOutdated=false`). This is the only open thread on the PR.
**Status: CONFIRMED by reproduction, not merely plausible.**

```python
if len(query) > MAX_QUERY_LENGTH:      # code points, not bytes
```

The three bounds were sized on the assumption that a query costs at most
~500 bytes, which yields a worst-case filter of ~4.8 MB — safely under MongoDB's
16 MB BSON limit. That assumption holds only for ASCII. A code point outside the
BMP costs 4 bytes in UTF-8, so the same 500-code-point budget buys ~2,000 bytes.
The candidate count is bounded, but the *size* of each candidate is not, and the
filter scales with the product.

This is not an exotic input for this project: the AfO Register is Assyriological
data, and cuneiform signs (`U+12000`–`U+123FF`) are exactly the 4-byte code points
that trigger it. It is also reachable anonymously — `create_api` installs
`MultiAuthBackend(auth_backend, NoneAuthBackend(Guest))`, so an unauthenticated
request falls through to `Guest`.

Measured against the running service (see Reproduction Steps):

| Bound | Limit | Worst case that passes | Under limit? |
| --- | --- | --- | --- |
| `MAX_TEXTS_AND_NUMBERS_QUERIES` | 1000 | 434 queries | yes |
| `MAX_QUERY_LENGTH` | 500 | 479 code points | yes |
| `MAX_QUERY_TOKENS` | 24 | 24 tokens | yes |
| `MAX_CANDIDATES` | 10,000 | 9,982 candidates | yes |
| **Resulting BSON filter** | **16 MB** | **18,814,975 B = 17.9 MB** | **NO** |

A 2.4 MB request body expands to a 17.9 MB server-side filter — a ~7.9x
amplification — and the response is a 500, not a 422.

**Fix** (as the reviewer proposed):

```python
if len(query.encode("utf-8")) > MAX_QUERY_LENGTH:
```

I verified this is sufficient rather than just directionally right: under a
byte-based bound, the worst case a validator still admits is 9,982 candidates at
**4,440,895 bytes = 4.24 MB**, comfortably under 16 MB and in line with the
~4.8 MB figure the `5b716e5b` commit message intended. **No other constant needs
to move.** The tightening is harmless for real data — actual references such as
`"OrNS 59, 17"` are tens of bytes, and even an all-diacritic transliteration
(`š`, `ṣ`, `ṭ` are 2 bytes) still gets ~250 characters.

**Suggested test** (the current suite cannot catch this because every test is ASCII):

```python
def test_validate_texts_and_numbers_query_rejects_wide_utf8_query():
    with pytest.raises(DataError):
        wide = "\U00012000" * (MAX_QUERY_LENGTH // 4 + 1)
        validate_texts_and_numbers_query([wide])
```

### F-2 (Nit, non-blocking) — request body is fully parsed before any bound applies

**File:** [ebl/afo_register/web/afo_register_records.py:72](ebl/afo_register/web/afo_register_records.py#L72)

`validate_texts_and_numbers_query(req.media)` bounds the request only *after*
Falcon has parsed the entire body into memory, and the app sets no global body
size limit. A multi-gigabyte body is therefore materialised before being rejected
with a 422.

This is pre-existing and applies to every POST route in the API, not just this
one, so I am **not** treating it as a finding against this PR. Noting it only
because this PR is specifically about bounding this endpoint, and a body-size
limit at the server or reverse-proxy layer would be the natural complement. Out
of scope here; worth a separate issue.

### Resolved prior feedback — verified, no action needed

1. **sourcery-ai**, review `4734372789` — remove task-tracking scaffolding
   before merge.
   **Done** — `15c060bf`; no `TASK-*.md` is tracked in the branch.
2. **sourcery-ai**, comment `5021576863` — Reviewer's Guide.
   Descriptive only; no actionable finding.
3. **Fabdulla1 F1**, review `4753124320` — unbounded `$or` fan-out on a
   public endpoint.
   **Addressed** — route-level bounds in `0872112c` / `5b716e5b` /
   `34a17823`. Correct in structure; the byte-width hole left in it is F-1.
4. **Fabdulla1 F2**, review `4753124320` — add an ambiguous multi-match test
   (`("A", "B C")` and `("A B", "C")` both joining to `"A B C"`).
   **Done** — [test_afo_register_repository.py:159][t159]; I also confirmed
   it live, where the route returns both records.
5. **Fabdulla1 F3**, review `4753124320` — deduplicate candidates by
   `(text, textNumber)`.
   **Done** — `seen` set in `_build_candidate_query`, first-seen order
   preserved, covered by
   `test_build_candidate_query_deduplicates_candidates`.

[t159]: ebl/tests/afo_register/test_afo_register_repository.py#L159

### Equivalence with the old implementation — verified, no regression

The new `candidate_splits` never yields an empty `text` or `textNumber`, so a
single-token query matches nothing. I checked whether the old concat fallback
did match such records, which would have made this PR a silent regression.

It did not: `_build_fallback_pipeline` matched
`{"$concat": ["$text", " ", "$textNumber"]}`, and that separator is
unconditional, so a record with an empty `textNumber` concatenates to
`"Solo "` and never equals a normalized query.

Confirmed by differential test against a real mongo over 15 queries, seeding
empty `text`, empty `textNumber`, trailing-space and double-space records,
ambiguous pairs and decoys:

- mismatches vs the old concat semantics: **0**
- results the old indexed path found that the new code loses: **0**

The new logic is exactly equivalent to the old concat semantics and a strict
superset of the old indexed path. Records with an empty `text` or `textNumber`
remain unreachable through this endpoint — pre-existing, unchanged by this PR.

### Checks I ran that found nothing

- **Route/repository bound consistency.** The route estimates splits without
  dedup (`count_candidate_splits`) and the repository counts after dedup, so the
  repository count is always <= the route estimate. A route-validated request can
  no longer trip the repository backstop. Off-by-one checked at both edges: the
  route rejects `> MAX_CANDIDATES` and the repository raises when a new candidate
  would make it exceed `MAX_CANDIDATES`, so both admit exactly 10,000. Both sides
  of the boundary are tested (`..._accepts_the_largest_allowed_batch` /
  `..._rejects_an_over_broad_batch`) and I confirmed both live.
- **Mixed-type array hard gate.** Clean. `query_list` is `Sequence[str]`;
  `candidates` is a homogeneous list of `{"text", "textNumber"}` dicts. No id list
  carries two types, nothing is discriminated by probing for an optional field,
  and the domain/wire shapes match. `candidate_splits` takes `object` and raises
  `DataError` rather than silently dropping a non-string — the right call, and
  the `object` annotation is what keeps the guard checkable.
- **250-line file gate.** All five touched files pass: 162, 93, 75, 205, 223.
  The `5b716e5b` extraction of `test_afo_register_candidate_query.py` was what
  kept the repository test file under the limit.
- **Error contract.** `DataError` maps to `unprocessable_entity` (422) via
  `ebl/error_handler.py:39`; verified live for all five rejection paths.
- **Index use.** The `$or` of exact `(text, textNumber)` equality predicates can
  still use the compound index created in `create_indexes`.

## Severity

- **F-1 — Medium, blocking.** An unauthenticated caller gets a 500 plus
  ~19 MB of server-side allocation from a 2.4 MB request. Not data loss and
  not a security breach, but it reinstates the exact failure mode this PR
  exists to remove, and the fix is one line.
- **F-2 — Low, non-blocking, out of scope.** Pre-existing and API-wide; no
  regression is introduced by this PR.

## Reproduction Steps

For F-1, against the code as it stands on `15c060bf`:

1. Start a local `mongod` on `127.0.0.1:27017`. (Do **not** source `.env` — its
   `MONGODB_URI` points at the production cluster.)
2. Boot the real service with `create_context()` + `create_app()` on port 8899,
   `MONGODB_DB=ebl_task741_local`.
3. Build a request in which every bound is satisfied but every code point is
   4 bytes wide, with a unique marker per query so dedup cannot collapse them:

   ```python
   SIGN = "\U00012000"          # 4 bytes in UTF-8
   body = [
       " ".join([SIGN * 18 + chr(0x10000 + i)] + [SIGN * 19] * 23)
       for i in range(434)
   ]
   # 434 distinct queries, 479 code points each, 24 tokens each -> 9,982 candidates
   ```

4. `validate_texts_and_numbers_query(body)` returns without raising — every bound
   passes.
5. `POST /afo-register/texts-numbers` with that body.

**Observed:** `HTTP 500`, with this server-side traceback:

```text
pymongo.errors.DocumentTooLarge: BSON document too large (18815074 bytes) -
the connected server supports BSON document sizes up to 16777216 bytes.
```

**Expected:** either a `422` naming the limit, or a filter that stays under 16 MB.

Caveat worth recording: my *first* attempt at this reproduction returned 200 and
looked like a refutation. The generator built token `j` of query `i` as
`chr(0x12000 + (i*24+j) % 900)`; since `gcd(24, 900) = 12`, queries `i` and `i+75`
were identical, so dedup collapsed 434 queries into 75 and the filter stayed
small. The test was measuring dedup, not byte width. The reproduction above uses
a per-query unique marker and asserts `len(set(body)) == 434`.

## Verification performed for this review

| Gate | Result |
| --- | --- |
| `task format` | PASS — 802 files already formatted |
| `task lint` (ruff) | PASS |
| `task type` (**pyre** — the CI gate) | PASS — no type errors found |
| `task type-pyright` | PASS — 0 errors, 0 warnings, 0 informations |
| `mypy <changed> --ignore-missing-imports` | PASS — 5 files, no issues |
| `poetry run flake8 <changed> --max-line-length=120` | PASS — exit 0 |
| `task lint-md` | PASS |
| Coverage on changed modules | **100%**, 0 missed (both changed source files) |
| `task test` (full suite) | PASS — 4323 passed, 2 skipped, 1 xfailed |
| CI: `qlty check` | PASS — "No blocking issues" |
| CI: `qlty coverage` / `coverage diff` | PASS — 95.9% (+0.1%) / 100.0% |
| CI: 3.11 / 3.12 / pypy-3.11, CodeQL, GitGuardian | PASS — nothing failing |
| Runtime verification, live service | Done — 11 cases, see the task log |

`docker` and `Sourcery review` report as *skipping*, not failing.

## Recommendation

Original recommendation was **request changes for F-1, then merge**. Both
findings have now been applied on this branch:

1. ✅ `validate_query` compares `len(query.encode("utf-8"))`, and the constant
   was renamed `MAX_QUERY_LENGTH` -> `MAX_QUERY_BYTES` so the unit lives in the
   name. No other constant moved.
2. ✅ Regression tests added in
   `ebl/tests/afo_register/test_afo_register_request_limits.py`, including
   4-byte-per-character queries on both sides of the boundary — the class of
   input no existing test used.
3. ✅ F-2 addressed within this endpoint: `validate_request_size` guards
   `Content-Length` before `req.media` parses the body, with the cap derived
   from the existing constants rather than hand-picked.
4. ⏳ Fabdulla1's inline thread `3776566330` should be resolved on GitHub once
   these changes are pushed. **Not done — no GitHub write action was taken.**

**Correction to an earlier claim in this review.** I previously recorded a
"remaining limitation" that a `Transfer-Encoding: chunked` request would bypass
the F-2 guard and still be parsed unbounded. **That was wrong** — I had assumed
it rather than tested it. In falcon 3.1.3, `Request.bounded_stream` is built
from `content_length`; with no `Content-Length` it yields **zero bytes**, and
`req.media` raises `MediaNotFoundError` (400). A chunked body is never
materialised by the app. Verified directly; see `TASK-741-f2-log.md`.

With that corrected, the endpoint's body read is bounded in every case:
declared length over the cap is rejected before parsing, a declared length
under the cap bounds the read, and an absent length reads nothing.

The genuine residual sat one layer lower: **waitress buffers the request body
before the app runs, with `max_request_body_size` defaulting to 1 GB.**
`Dockerfile` now passes `--max-request-body-size=67108864` (64 MB). Safe to
apply globally — all 28 write handlers are JSON, no route reads a raw or binary
body, and GridFS has no route-reachable write path. Verified end to end against
waitress with the production flags: 1 MB accepted, one byte over 64 MB refused.

The underlying fix is sound and the test coverage around it is genuinely good —
the ambiguous multi-match case, the partial-match rejection, and both sides of
the candidate-budget boundary are all covered. F-1 is a one-line correction to an
otherwise well-constructed set of bounds.

## Before merge

`TASK-741-todo.md`, `TASK-741-log.md` and `TASK-741-review.md` are task-tracking
scaffolding and **must be removed before this PR is merged.** They are currently
untracked in the working tree and are not part of the PR.
