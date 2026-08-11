# TASK-741 Review

PR #741 — *Fix AfO Register texts-numbers match for references containing
spaces*
(<https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/741>)

## Review Summary

Had a good look through this one — the fix is the right call. Splitting on the
last space was never going to work when both fields can contain spaces, and
enumerating every split point is provably equivalent to matching the
concatenation while still hitting the compound index (I checked the explain
plan; every `$or` branch is an index scan, no collection scan). All three
points from the earlier review are addressed: the endpoint is bounded now,
duplicate candidates are deduplicated, and there is an explicit test for the
ambiguous `"A B C"` case. I pulled the branch, ran the service against a local
mongo and poked the route by hand — the original `OrNS 59, 17` case works, the
`59, 170` decoy stays out, and every limit returns a clean 422.

Nothing blocking from me. I raised two small things and both are now fixed in
the branch: the route validates the candidate budget itself, so a request it
accepts can no longer be rejected further down, and a non-string query raises
instead of being silently dropped. The only thing left is housekeeping — the
`TASK-741-*.md` files need deleting — and Fabdulla1's `CHANGES_REQUESTED` is
still sitting on the PR, so it needs a re-review to unblock.

### Details

<!-- markdownlint-disable MD013 -->

#### Existing PR feedback — status

All feedback on the PR was fetched via `gh api` (`/pulls/741/reviews`, `/pulls/741/comments`, `/issues/741/comments`, and the GraphQL `reviewThreads` connection). There are **0 inline diff comments** and **0 review threads**; all feedback arrived as top-level review bodies.

| # | Reviewer | Feedback | Status in current tree | Evidence |
| - | -------- | -------- | ---------------------- | -------- |
| 1 | `sourcery-ai[bot]` (review `4734372789`, 2026-07-20) | Remove the task-tracking scaffolding files `TASK-afo-register-link-log.md` and `TASK-afo-register-link-todo.md` before merging. | **Done** — removed in `388a96aa`; neither file appears in `git diff origin/master...HEAD`. **But see finding L3**: new `TASK-741-*.md` files exist again and must be removed before merge. | `git diff --name-only origin/master...HEAD` returns only the 5 code/test files |
| 2 | `sourcery-ai[bot]` (issue comment `5021576863`) | Reviewer's Guide — descriptive summary and sequence diagram. | No action required. Its file-level description still matches the implementation. | — |
| 3 | `Fabdulla1` (review `4753124320`, `CHANGES_REQUESTED`, 2026-07-22) — point 1 | `$or` clauses grow with both the number of submitted references and the token count per reference; the endpoint is public with no size validation. Add an upper bound on array length, individual string length, or total candidates. | **Done** — `ebl/afo_register/web/afo_register_records.py` adds `MAX_TEXTS_AND_NUMBERS_QUERIES = 1000`, `MAX_QUERY_LENGTH = 500`, `MAX_QUERY_TOKENS = 24`; `mongo_afo_register_repository.py` adds `MAX_CANDIDATES = 10000`. All four raise `DataError` → HTTP 422. | Verified live against the running service: 1001 queries → 422 "Too many queries: at most 1000 allowed."; 501-char query → 422 "Query too long…"; 25 tokens → 422 "Query has too many words…"; 435×24-token queries → 422 "Query is too broad…" |
| 4 | `Fabdulla1` — point 2 | Add coverage for an ambiguous joined reference where two records both match, e.g. `("A", "B C")` and `("A B", "C")` both concatenating to `"A B C"`; both should be returned. | **Done** — `test_search_by_texts_and_numbers_returns_all_ambiguous_matches` in `ebl/tests/afo_register/test_afo_register_repository.py` asserts both records are returned. | Verified live: `POST ["A B C"]` → `['A B\|C', 'A\|B C']` (both records) |
| 5 | `Fabdulla1` — point 3 | Duplicate request strings or overlapping candidate pairs produce repeated identical `$or` clauses; deduplicate by `(text, textNumber)` before building the query. | **Done** — `_build_candidate_query` keeps a `seen: Set[Tuple[str, str]]` and skips duplicates; covered by `test_build_candidate_query_deduplicates_candidates`. | Verified live: `POST ["A B C", "A B C"]` → 2 records, not 4 |

Feedback from PRs merged into this branch: the branch contains two merges of `origin/master` (`7a2d3285`, `7fc44160`). No commit reaching `master` since this branch's merge base touches `ebl/afo_register/` (`git log <merge-base>..origin/master -- ebl/afo_register/` is empty), so none of the merged-in PRs (#740, #747, #748, #749) overlap this change and none of their feedback applies here.

#### CI checks and qlty

| Check | Result |
| ----- | ------ |
| CodeQL / Analyze (python) | pass |
| GitGuardian scan | pass |
| Test Python 3.11 / 3.12 / pypy-3.11 | **5 of 6 jobs pass**; one `Test Python 3.11` job (run `31512085808`) was still pending when this review was finalized. **No failing checks anywhere on the PR.** Two duplicate workflow runs are queued against the same head SHA (`31512085808` and `31512087915`), which is why each job appears twice — that is a CI-configuration artefact, not a problem with this PR. |
| Sourcery review | `skipping` — Sourcery has **not** re-reviewed the latest commits (`0872112c`, `5b716e5b`), so its only feedback predates the bounds/dedup work. Comment `@sourcery-ai review` if a fresh bot pass is wanted. |
| qlty check | pass — **no blocking issues** (<https://qlty.sh/gh/ElectronicBabylonianLiterature/projects/ebl-api/pull/741/issues>). The local `qlty` CLI cannot corroborate this: the repo has no tracked `qlty.toml`, and `qlty check` exits with "Qlty must be set up in this repository". Not initialized here, since that would mean adding config the user did not request. |
| `reviewDecision` | `CHANGES_REQUESTED`; `mergeStateStatus: BLOCKED` |

#### Findings from this review

##### L1 — Low — The route's limits admit more candidates than the repository will build, so a validated request can still be rejected

`ebl/afo_register/web/afo_register_records.py` allows up to `MAX_TEXTS_AND_NUMBERS_QUERIES = 1000` queries of `MAX_QUERY_TOKENS = 24` tokens each. A 24-token query expands to 23 candidate splits, so the route admits up to **23,000** candidates — but `MAX_CANDIDATES = 10000` in `mongo_afo_register_repository.py` refuses anything past 10,000. The effective batch ceiling is therefore ~434 maximal-length queries, not the 1000 the route advertises.

Confirmed against the running service: 434 queries × 24 tokens → `200 []`; 435 queries × 24 tokens → `422 "Query is too broad: it expands to more than 10000 text and number combinations."` The project's own test `test_search_by_texts_and_numbers_route_rejects_too_broad_query` encodes exactly this reachability (`MAX_CANDIDATES // 23 + 1` queries).

Two sub-points: the wording says "**Query** is too broad" when the cause is the *batch*, which will read as confusing to a client that submitted 435 individually-legal references; and the two limits are set independently in two modules with no relationship asserted between them.

In practice AfO references are 2–5 tokens, so a full 1000-reference batch produces roughly 1,000–4,000 candidates and never approaches the cap — this is a consistency issue, not a live defect.

*Suggestion:* either make the bound self-consistent (e.g. `MAX_CANDIDATES >= MAX_TEXTS_AND_NUMBERS_QUERIES * (MAX_QUERY_TOKENS - 1)`, or derive one from the other), or reword the message to name the batch rather than a single query.

**RESOLVED.** The first half of that suggestion turned out to be wrong and was **not** taken: commit `5b716e5b` documents that `MAX_CANDIDATES = 10000` is sized so the worst-case BSON filter stays around 4.8 MB, under MongoDB's 16 MB document limit. Raising it to 23,000 would push the worst case to roughly 11 MB — so the cap is correct and the *route* had to become consistent with it, not the other way round.

The route now validates the candidate budget itself, against the same constant, before the repository is ever called:

```python
def count_candidate_splits(queries: Sequence[str]) -> int:
    return sum(max(len(query.split()) - 1, 0) for query in queries)


def validate_candidate_budget(queries: List[str]) -> List[str]:
    if count_candidate_splits(queries) > MAX_CANDIDATES:
        raise DataError(TOO_MANY_CANDIDATES_MESSAGE)
    return queries
```

Because the repository deduplicates candidates, its own count is always ≤ the route's estimate, so a request that passes route validation can no longer trip the repository bound — the inconsistency is closed by construction. The message moved to a single shared constant, `TOO_MANY_CANDIDATES_MESSAGE`, used by both layers, and now names the batch: *"The submitted queries expand to more than 10000 text and number combinations."*

New tests: `test_count_candidate_splits_counts_split_points`, `test_validate_candidate_budget_accepts_the_largest_allowed_batch`, `test_validate_candidate_budget_rejects_an_over_broad_batch`, and `test_search_by_texts_and_numbers_route_accepts_the_largest_allowed_batch` — the last one pins the boundary that used to fail. The pre-existing `test_search_by_texts_and_numbers_route_rejects_too_broad_query` still passes and now also asserts the message. Re-verified live: 434 maximal queries → `200 []`, 435 → `422` with the new wording.

##### L2 — Low — `candidate_splits` widened its parameter type to `object`

`def candidate_splits(query: object) -> List[Tuple[str, str]]` keeps an `isinstance(query, str)` guard even though `validate_query` at the route now guarantees `str` and `_build_candidate_query` iterates a `Sequence[str]`. The guard is defensive-in-depth for a public endpoint and is covered by `test_candidate_splits_rejects_non_string`, so it is defensible — but typing the parameter `object` means the type checkers can no longer flag a genuinely wrong argument at any other call site. `str` as the annotation, with the runtime guard retained, would keep both properties.

**RESOLVED — differently from the suggestion.** The suggested narrowing does not work: annotating `query: str` makes pyright reject the existing test, `Argument of type "None" cannot be assigned to parameter "query" of type "str" in function "candidate_splits" (reportArgumentType)`. Narrowing the type therefore costs either a `cast`/suppression or the deletion of `test_candidate_splits_rejects_non_string` — neither acceptable.

What was actually wrong here was subtler than the annotation, and is now fixed: the guard **silently returned `[]`**, so calling the repository directly with `["A B", 5]` quietly dropped the `5` and answered as though only `"A B"` had been asked for. That is a silent coercion of exactly the kind the project's data gate forbids. The guard now raises instead:

```python
def candidate_splits(query: object) -> List[Tuple[str, str]]:
    if not isinstance(query, str):
        raise DataError(NON_STRING_QUERY_MESSAGE)
```

`object` stays — it is what makes the guard checkable at all — but it is now load-bearing rather than merely tolerated, and a wrong type fails loudly at both layers with one shared message (`NON_STRING_QUERY_MESSAGE`, also used by the route's `validate_query`). `test_candidate_splits_rejects_non_string` was updated in place from `== []` to `pytest.raises(DataError)`; no test was removed. Verified live: `["A B", 5]` → `422 "Each query must be a string."`

##### L3 — Low (housekeeping, blocks merge) — Task-tracking files must be removed again

Sourcery's original request was satisfied, but this review re-created `TASK-741-todo.md`, `TASK-741-log.md`, and this file (`TASK-741-review.md`) — all currently untracked. They must be deleted before merge. The PR body's "Before merge" section also still names the *old* filenames (`TASK-afo-register-link-{log,todo}.md`), which no longer exist; worth updating so the reminder points at the right files.

**PARTLY RESOLVED.** The PR body's "Before merge" section was patched to name the current files (`TASK-741-{todo,log,review}.md` and `TASK-741-fix-{todo,log}.md`); nothing else in the description was touched. The files themselves still exist and **must still be deleted before merge** — they are the working record of this review and the follow-up fix, so removing them now would destroy the task tracking mid-task.

##### I1 — Info — `MAX_CANDIDATES` validation lives in the infrastructure layer

Every other request-shape rule for this endpoint is enforced in the web layer, but the candidate-count bound raises `DataError` from `MongoAfoRegisterRepository._build_candidate_query`. It works (the error handler maps `DataError` → 422, verified live), and the repository is the layer that actually knows the cost. Purely a placement observation: the candidate count is computable from token counts at the route, so all 422s for this endpoint could originate in one place.

**RESOLVED**, as a side effect of the L1 fix. Every 422 reachable through `POST /afo-register/texts-numbers` now originates in the web layer: body shape, batch size, query length, token count, candidate budget, and element type. The repository's `MAX_CANDIDATES` check remains as a backstop for direct callers of `MongoAfoRegisterRepository` — it is no longer reachable through the route, but is still exercised directly by `test_build_candidate_query_rejects_too_many_candidates` and `test_search_by_texts_and_numbers_rejects_too_many_candidates`, so coverage stays at 100%.

##### I2 — Info — Whitespace normalization is query-side only

`candidate_splits` normalizes via `strip().split()` and rejoins on single spaces, so a stored record whose `text` or `textNumber` carries a double space or leading/trailing whitespace can never be matched. Verified that the query side normalizes correctly (`["OrNS    59,   17"]` → matches `OrNS` / `59, 17`). This is identical to the previous behaviour — the old `$concat` fallback compared against a normalized query too — so it is **not a regression**, just an undocumented invariant on the imported data.

**ACKNOWLEDGED — no code change, deliberately.** The only fixes available are to normalize `text`/`textNumber` at import time or to match against a normalized projection, and both are data-side changes to the AfO Register import that reach well beyond this PR; the second would also give up the compound index that P1 confirms is being used. Since the behaviour is identical to what shipped before, this PR is not the place to change it. Worth a separate ticket if malformed whitespace is ever observed in the imported register.

##### P1 — Positive — The index claim in the PR description holds

`explain` on a two-branch candidate query against a seeded local mongo returns `SUBPLAN → FETCH → OR` over two `IXSCAN` stages: the exact branch uses the compound `text_1_textNumber_1` index, and the other uses `text_1` with a residual filter on `textNumber`. No `COLLSCAN`. The rewrite keeps the indexed lookup that the removed `_build_fallback_pipeline` aggregation would have given up.

##### P2 — Positive — The endpoint no longer echoes the request payload in its error

`NotFoundError(f"No AfO registry entries matching {str(req.media)} found.")` became a message carrying only `len(query_list)`. Unbounded caller-controlled input is no longer reflected into an error string or the logs. Good change, and it pairs well with the new size limits.

##### P3 — Positive — No behavioural regression against the removed code paths

The old code used the (broken) last-space split whenever *every* query was splittable, and fell back to the `$concat` aggregation only when one was not — so the correct path was unreachable for exactly the inputs that were broken. The new candidate `$or` returns the same set the `$concat` comparison would have (a record matches iff `text + " " + textNumber` equals the normalized query), including for single-token queries (no split point → no match, matching the old behaviour where a concatenation always contains a space).

#### Project hard gates, verified locally on this branch

Re-run in full after the findings were fixed; the figures below are for the
current tree, not the tree as reviewed.

| Gate | Result |
| ---- | ------ |
| `task format` (`ruff format --check`) | 802 files already formatted |
| `task lint` (ruff) | All checks passed |
| `task type` (**pyre** — the CI gate) | No type errors found |
| `task type-pyright` (pyright on changed files) | 0 errors, 0 warnings, 0 informations |
| `poetry run mypy <changed files> --ignore-missing-imports` | Success: no issues found in 4 source files |
| `poetry run flake8 <changed modules> --max-line-length=120` | exit 0, no output |
| `poetry run pytest ebl/tests/afo_register --cov=ebl/afo_register` | 49 passed; **100% coverage** on every `ebl/afo_register` module, including both changed source files (88 and 53 statements, 0 missed) |
| 250-line-per-`.py`-file limit | All changed files pass: repository 162, route 93, `test_afo_register_candidate_query.py` 75, `test_afo_register_repository.py` 205, `test_afo_register_route.py` 223 |
| Mixed-type-array hard gate | **Passes.** `query_list` is `Sequence[str]`; `candidate_splits` returns `List[Tuple[str, str]]`; the `$or` array holds only `Dict[str, str]` entries of the same shape. No id list mixes two types, nothing is discriminated by probing for an optional field, and the wire shape (array of strings in, array of records out) matches the domain shape. |
| Full test suite (`poetry run pytest -q`) | **4323 passed, 2 skipped, 1 xfailed, 0 failures** in 4m30s (4319 before the fixes; the 4 new tests are the L1 boundary and budget cases) |

## Summary

The change replaces an unrecoverable last-space split of joined `text`/`textNumber`
references with an exhaustive candidate-split `$or` query, restoring AfO
Register lookups for references containing spaces (the `MNAO.11676` /
`OrNS 59, 17` case). Since the previous review round it also bounds the public
endpoint, deduplicates candidates, and adds ambiguity coverage. All prior
reviewer feedback is addressed in the current tree.

## Findings

See the `Details` subsection above. In short: 3 low-severity findings (limit
inconsistency between route and repository, `object` parameter annotation on
`candidate_splits`, task-file housekeeping), 2 informational notes (validation
layering, query-side-only whitespace normalization), and 3 positive
confirmations (index use, no payload echoed in errors, no behavioural
regression). No correctness defect found.

**All findings have since been addressed in the branch.** L1 and I1 are fixed
together by moving the candidate-budget check to the route against the shared
`MAX_CANDIDATES`; L2 is fixed by making the non-string guard raise rather than
silently return `[]`; L3's PR-body half is patched and the file deletion is
pending merge; I2 is acknowledged with a rationale and deliberately left alone.
Two of the fixes differ from what the finding originally suggested — in both
cases the suggestion turned out to be unworkable, and the reason is recorded
under the finding.

## Severity

- **Blocking:** none on the code. Merge is procedurally blocked by the
  outstanding `CHANGES_REQUESTED` review and by the untracked `TASK-741-*.md`
  files.
- **Low:** L1 (fixed), L2 (fixed), L3 (PR body fixed; file deletion pending
  merge).
- **Informational:** I1 (fixed with L1), I2 (acknowledged, no change).
- **Positive confirmations:** P1, P2, P3.

## Reproduction Steps

The affected route was exercised against the modified service, not tests alone.
The table below is from the **re-run after the findings were fixed**; the
earlier run was voided by those changes and repeated in full.

1. Start a local mongo on `127.0.0.1:27017`. Do **not** source `.env` — its
   `MONGODB_URI` points at the production cluster.
2. Serve the AfO Register routes from this working tree, wiring
   `MongoAfoRegisterRepository` to a scratch database seeded with records for
   `OrNS`/`59, 17`, a `OrNS`/`59, 170` decoy, `*Bit meseri*`/`59, 17`,
   `A`/`B C`, and `A B`/`C`.
3. `POST /afo-register/texts-numbers` with each body below.

| Body | Observed |
| ---- | -------- |
| `["OrNS 59, 17"]` | `200` — the `OrNS` / `59, 17` record (the reported bug, fixed) |
| `["OrNS 59, 1"]` | `200 []` — the `59, 170` decoy correctly excluded |
| `["*Bit meseri* 59, 17"]` | `200` — spaces in both fields |
| `["A B C"]` | `200` — both ambiguous records |
| `["A B C", "A B C"]` | `200` — 2 records, duplicates deduplicated |
| `["OrNS    59,   17"]` | `200` — internal whitespace normalized |
| `["OrNS 59, 17 extra"]` | `200 []` — partial match rejected |
| `["OrNS"]`, `[]` | `200 []` |
| `{"a": 1}` | `422` "Request body must be a list of strings." |
| `["A B", 5]` | `422` "Each query must be a string." |
| 501-character query | `422` "Query too long: at most 500 characters allowed." |
| 25-token query | `422` "Query has too many words: at most 24 allowed." |
| 1001 queries | `422` "Too many queries: at most 1000 allowed." |
| 435 × 24-token queries | `422` "The submitted queries expand to more than 10000 text and number combinations." — now raised by the route, naming the batch (finding L1, fixed) |
| 434 × 24-token queries | `200 []` — the largest batch the limits allow, now pinned by a test |

Index verification: `db.command("explain", {"find": "afo_register", "filter": {"$or": [...]}})`
returns `SUBPLAN → FETCH → OR` over two `IXSCAN` stages
(`text_1_textNumber_1` and `text_1`), no `COLLSCAN`.

## Recommendation

**Approve, with two things to settle before merge.**

1. Get Fabdulla1 to re-review — all three of their points are addressed, but the
   `CHANGES_REQUESTED` verdict still blocks the merge
   (`mergeStateStatus: BLOCKED`).
2. Delete `TASK-741-{todo,log,review}.md` and `TASK-741-fix-{todo,log}.md`. The
   PR body's "Before merge" section has already been updated to name them.

The optional items L1 and L2 were subsequently implemented rather than deferred,
so nothing is left outstanding on the code. Both fixes are recorded under their
findings above, with the reasoning for departing from the original suggestions.
One `Test Python 3.11` job was still pending at review time; the other five test
jobs are green, so no failure is expected there — but note that CI has not yet
run against the fix commits, since they are uncommitted.
