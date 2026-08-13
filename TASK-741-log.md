# TASK-741 Work Log — Review PR #741

PR: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/741>
Branch: `fix-afo-register-texts-numbers-split` -> `master`
Task type: review only (no code changes requested)

## 2026-08-13

### Step 0 — Instructions

- Read `.github/instructions/copilot.instructions.md` in full at the start of the
  session. All gates acknowledged as binding.

### Step 1 — Task tracking artefacts

- Determined the PR under review: `gh pr view --json ...` on the checked-out
  branch returned PR **#741**.
  - Note: the git snapshot in the session context showed branch `dep-upd`, but the
    working tree is actually on `fix-afo-register-texts-numbers-split`. Used the
    live `git status` output, not the stale snapshot.
- Created `TASK-741-todo.md` and `TASK-741-log.md` **before** starting review work.

### Step 2 — PR metadata

- PR #741, OPEN, `MERGEABLE` / `mergeStateStatus: CLEAN`, `reviewDecision: APPROVED`.
- 5 files changed, +403 / -54. 14 commits. Local HEAD `15c060bf` == PR head.
- Working tree clean apart from the two TASK-741 files created above.

### Step 3 — All GitHub feedback fetched (HARD GATE)

Commands run:

- `gh api repos/ElectronicBabylonianLiterature/ebl-api/pulls/741/reviews --paginate`
- `gh api repos/ElectronicBabylonianLiterature/ebl-api/pulls/741/comments --paginate`
- `gh api repos/ElectronicBabylonianLiterature/ebl-api/issues/741/comments --paginate`
- GraphQL `reviewThreads` for resolution state

Feedback found:

1. **sourcery-ai[bot]**, review `4734372789` (2026-07-20, COMMENTED) — remove
   task-tracking scaffolding before merge. **Status: addressed** (commit
   `15c060bf` removed them; tree confirms no `TASK-*.md` tracked).
2. **sourcery-ai[bot]**, issue comment `5021576863` — Reviewer's Guide, descriptive
   only, no actionable finding.
3. **Fabdulla1**, review `4753124320` (2026-07-22, CHANGES_REQUESTED) — three
   findings: (F1) unbounded `$or` fan-out on a public endpoint, (F2) missing
   ambiguous-multi-match test, (F3) deduplicate candidates.
   **Status: all three addressed** in `0872112c` / `5b716e5b` / `34a17823`.
4. **Fabdulla1**, review `4928617794` (2026-08-13, APPROVED) — "address the comment
   above and it should be good to merge".
5. **Fabdulla1**, inline comment `3776566330` on
   `ebl/afo_register/web/afo_register_records.py:25` —
   `MAX_QUERY_LENGTH` counts code points, not UTF-8 bytes; a request can pass every
   bound and still build a filter over the 16 MB BSON limit.
   **Status: UNRESOLVED** (`isResolved=false`, `isOutdated=false`). This is the
   only open thread on the PR.

### Step 4 — CI checks and qlty

`gh pr checks 741` — all green, nothing failing:

- Analyze (python) pass; CodeQL pass; GitGuardian x3 pass
- Test Python 3.11 / 3.12 / pypy-3.11 pass (both workflow runs)
- docker + Sourcery review: skipping (not failures)
- **qlty check: pass — "No blocking issues"**
- **qlty coverage: pass — 95.9% (+0.1%)**
- **qlty coverage diff: pass — 100.0% (75% threshold)**

### Step 5 — Verifying the open reviewer finding empirically

Wrote a scratchpad script that builds the worst-case request which still passes
every route bound, and measured the real BSON filter with `bson.encode`:

- 24 tokens / 479 code points per query, each a 4-byte UTF-8 cuneiform sign
  (U+12000) => 1,847 bytes per query, under `MAX_QUERY_LENGTH = 500`
- 434 queries, under `MAX_TEXTS_AND_NUMBERS_QUERIES = 1000`
- 9,982 candidates, under `MAX_CANDIDATES = 10000`
- `validate_texts_and_numbers_query` **PASSES** (no `DataError`)
- Resulting `$or` filter: **18,814,975 bytes = 17.9 MB**
- MongoDB BSON limit: 16,777,216 bytes = 16.0 MB => **over limit**
- ASCII baseline for the same shape: 5.3 MB (matches the ~4.8 MB figure the
  commit message assumed)

Conclusion: **Fabdulla1's open finding is CONFIRMED**, not theoretical.

### Step 6 — Local gates

| Gate | Result |
| --- | --- |
| `task format` | PASS — 802 files already formatted, no unstaged changes |
| `task lint` (ruff) | PASS — all checks passed |
| `task type` (**pyre**) | PASS — no type errors found |
| `task type-pyright` | PASS — 0 errors, 0 warnings, 0 informations |
| `flake8 --max-line-length=120` | PASS — exit 0 on all 5 changed files |
| `mypy --ignore-missing-imports` | PASS — no issues in 5 source files |
| `task lint-md` | PASS (after fixing my own TODO file — see below) |
| Coverage on changed modules | PASS — 100% on both changed source files |
| `task test` (full suite) | PASS — 4323 passed, 2 skipped, 1 xfailed |
| 250-line file gate | PASS — 162 / 93 / 75 / 205 / 223 lines |

Error made and recovered: my first `task lint-md` run reported 5 `MD013`
line-length errors — all of them in `TASK-741-todo.md`, which I had just written,
not in the PR. Rewrapped those lines; re-ran `task lint-md` => 0 errors. The PR
itself ships no markdown.

Coverage note: my first coverage run passed `--cov=<path/to/file.py>` and
coverage reported "module was never imported" / "No data was collected". Re-ran
with dotted module paths (`--cov=ebl.afo_register.web.afo_register_records`),
which reported correctly: **100%, 0 missed** on both changed source modules.

### Step 7 — Runtime verification (HARD GATE)

Started a local `mongod` on `127.0.0.1:27017` (a mongod was already listening;
`mongo ok: 4.4.30`). Deliberately did **not** source `.env` — its `MONGODB_URI`
points at the production cluster.

Booted the real Falcon app (`create_context()` + `create_app()`) on port 8899
against a local DB seeded with the shapes from the bug report, including the
`("OrNS", "59, 170")` decoy and an ambiguous `("OrNS 59,", "17")` record.

Live route results:

| Case | Result |
| --- | --- |
| `["OrNS 59, 17"]` | **200** — 2 records (see note below) |
| `["OrNS 59, 170"]` | 200 — only the `59, 170` record; no decoy leak |
| `["OrNS"]` (no split point) | 200 — `[]` |
| `[]` | 200 — `[]` |
| `["Nonexistent 1"]` | 200 — `[]` |
| `{"not": "a list"}` | 422 — "Request body must be a list of strings." |
| `["ok", 5]` | 422 — "Each query must be a string." |
| 501-char query | 422 — "Query too long: at most 500 characters allowed." |
| 25-token query | 422 — "Query has too many words: at most 24 allowed." |
| 436 x 24-token batch | 422 — "expand to more than 10000 ..." |

Note on the first row: the two records returned are `OrNS 59,` / `17` and
`OrNS` / `59, 17`. The fix works, and the ambiguous multi-match behaves as
documented.

### Step 8 — Error made and recovered: invalid first UTF-8 run

My first live UTF-8 worst-case request returned **200**, which contradicted the
18.8 MB figure computed in step 5. Rather than accept it, I inspected the
generator: I had built token `j` of query `i` as `chr(0x12000 + (i*24+j) % 900)`.
Since `gcd(24, 900) = 12`, query `i` and query `i+75` are **identical**, so the
repository's dedup collapsed 434 queries to 75 distinct ones (1,725 candidates)
and the filter stayed small. The test was measuring dedup, not byte width.

Per the "re-verify after every rewrite" gate, I rebuilt the generator to embed a
unique 4-byte marker (`chr(0x10000 + i)`) in token 0 of each query, asserted
`len(set(body)) == 434`, and re-ran against the **same running service**:

- 434 distinct queries, 479 code points each (limit 500), 24 tokens (limit 24)
- 9,982 unique candidates (limit 10,000)
- `validate_texts_and_numbers_query` PASSED — no `DataError`
- Request body 2,386,566 bytes; BSON `$or` filter **18,814,975 bytes = 17.9 MB**
- **LIVE ROUTE -> HTTP 500**

Server-side traceback:

```text
pymongo.errors.DocumentTooLarge: BSON document too large (18815074 bytes) -
the connected server supports BSON document sizes up to 16777216 bytes.
127.0.0.1 - - [13/Aug/2026 20:54:01]
  "POST /afo-register/texts-numbers HTTP/1.1" 500 38
```

This is the exact failure mode the PR set out to eliminate, reproduced against
the shipping code. **Fabdulla1's open comment is confirmed, not theoretical.**

### Step 9 — Verified the proposed remedy is sufficient

Simulated bounding `MAX_QUERY_LENGTH` on `len(query.encode("utf-8"))` instead of
`len(query)`. Worst case that such a validator still admits: 9,982 candidates,
**4,440,895 bytes = 4.24 MB**, comfortably under the 16 MB limit and in line with
the ~4.8 MB figure the `5b716e5b` commit message intended. So the one-line change
the reviewer suggests is both correct and sufficient; no other bound needs moving.

### Step 10 — Endpoint reachability

Confirmed the endpoint really is unauthenticated: `create_api` installs
`FalconAuthMiddleware(MultiAuthBackend(auth_backend, NoneAuthBackend(Guest)))`,
so an anonymous request falls through to `Guest`. Fabdulla1's "publicly
accessible" characterisation is accurate, which is what makes this reachable by
an unauthenticated caller.
