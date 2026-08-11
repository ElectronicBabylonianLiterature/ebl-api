# TASK-741 Review — PR #741

PR: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/741>
Title: Fix AfO Register texts-numbers match for references containing spaces
Branch: `fix-afo-register-texts-numbers-split` → `master`
Head reviewed: `8e30b353b606331fd8b3bb7202d41719d597bb58`
Review decision on GitHub: `CHANGES_REQUESTED` (Fabdulla1)
Merge state: `CONFLICTING` / `DIRTY`

## Summary

The fix itself is correct and well tested. Replacing `split_text_and_number`
(single `rsplit`) plus the `$concat` aggregation fallback with an exhaustive
`candidate_splits` + `$or` query restores matching for references where the
space falls inside `text` or inside `textNumber`, and it keeps every lookup on
the compound `(text, textNumber)` index instead of a collection scan. The
matching semantics are equivalent to the old aggregation fallback ("some split
of the query equals `text` + `" "` + `textNumber`"), so the previously used
fallback path is not weakened — it is simply applied consistently and with an
index.

Two of the three points from the standing `CHANGES_REQUESTED` review are fully
addressed. The third — bounding the endpoint — is only partially addressed: the
limits added in `validate_texts_and_numbers_query` bound the *request*, not the
*generated query*, and a request that passes validation still produces an 85 MB
MongoDB query and an HTTP 500.

Verified locally against the in-memory MongoDB used by the test suite (the
production `MONGODB_URI` in the shell environment was not used; `conftest.py`
falls back to `pymongo_inmemory` outside CI and the suite additionally refuses
production database names).

### Existing GitHub feedback incorporated

- Sourcery review `4734372789` (COMMENTED, 2026-07-20): remove task-tracking
  scaffolding before merge. **Addressed** in `8e30b353` for the old
  `TASK-afo-register-link-*.md` files; see finding 9 for the new ones.
- Sourcery Reviewer's Guide comment `5021576863`: informational, no action.
- Fabdulla1 review `4753124320` (CHANGES_REQUESTED, 2026-07-22), 3 points:
  - Bound the endpoint. **Partially addressed** — see finding 2.
  - Test ambiguous joined references. **Addressed** by
    `test_search_by_texts_and_numbers_returns_all_ambiguous_matches`
    (`ebl/tests/afo_register/test_afo_register_repository.py:162`).
  - Deduplicate candidates. **Addressed** by the `seen` set in
    `_build_candidate_query` and
    `test_build_candidate_query_deduplicates_candidates`.
- Inline (diff) review comments: none exist (`/pulls/741/comments` is empty,
  `reviewThreads.totalCount` is 0).
- Merged-in branches: the only merge commit on the branch is `7a2d3285`, a
  merge of `origin/master`. No feature-branch PRs were merged in, so there is
  no additional PR feedback to fetch.

### CI and qlty status (head `8e30b353`)

- All required checks pass: `Test Python 3.11`, `Test Python 3.12`,
  `Test Python pypy-3.11` (both workflow runs), `Analyze (python)`, `CodeQL`
  ("No new alerts"), `GitGuardian scan`, `GitGuardian Security Checks`.
- `qlty check`: success, "No blocking issues".
- `qlty coverage`: success, 95.5% (+0.1%). `qlty coverage diff`: 100.0%
  against a 75% threshold.
- `Sourcery review`: **skipped** — "Auto re-review limit reached". Sourcery has
  therefore *not* reviewed `0872112c` or `8e30b353`. Comment
  `@sourcery-ai review` to get fresh bot feedback on the latest changes.
- `docker`: skipped (expected for a PR build).

### Local gate results on changed modules

- `poetry run pytest ebl/tests/afo_register
  ebl/tests/fragmentarium/test_retrieve_annotations.py
  --cov=ebl/afo_register --cov-report=term-missing` — 41 passed, **100%**
  coverage on every `ebl/afo_register` module.
- `poetry run flake8 <changed modules> --max-line-length=120` — clean.
- `poetry run mypy <changed modules> --ignore-missing-imports` — no errors in
  any changed file. The 87 reported errors are all in pre-existing, unrelated
  modules pulled in transitively (`ebl/corpus/**`, `ebl/fragmentarium/**`).
- 250-line file cap: all changed files pass
  (`mongo_afo_register_repository.py` 151, `afo_register_records.py` 73,
  `test_afo_register_repository.py` 216, `test_afo_register_route.py` 159,
  `test_retrieve_annotations.py` 126).

## Findings

1. **Branch conflicts with `master` because of out-of-scope changes that are
   already on `master`.** `.gitignore` and
   `ebl/tests/fragmentarium/test_retrieve_annotations.py` are both modified on
   this branch and were separately landed on `master` in a slightly different
   form (`master` has `.claude/` and `.qlty/` with trailing slashes under a
   `# Claude Code` heading; this branch has `.claude` and `.qlty` under
   `# Claude`; `master` keeps the `# Mock MongoDB components` comments that
   this branch deletes). `git merge-tree` reports exactly these two files as
   "changed in both". Neither file is related to the AfO Register fix.

2. **The new request bounds do not bound the generated MongoDB query; the
   endpoint still returns HTTP 500 on a modest request.** `MAX_QUERY_LENGTH`
   (500 characters) and `MAX_TEXTS_AND_NUMBERS_QUERIES` (1000) cap the request,
   but `candidate_splits` emits `len(tokens) - 1` candidates per query, so a
   500-character query of 2-character tokens yields 166 candidates. A 504 KB
   request body that passes validation produces 166,000 `$or` clauses, ~142 MB
   of peak Python allocation, 1.6 s of CPU in `_build_candidate_query` alone,
   and an **85.4 MB** BSON filter — far past MongoDB's 16 MB document limit.
   The resulting driver exception is not handled by
   `AfoRegisterTextsAndNumbersResource.on_post` (which only catches
   `ValueError`), so the client gets a bare `500 Internal Server Error`. This
   is the concern Fabdulla1 raised, and the endpoint is reachable by guest
   users via the `NoneAuthBackend` fallback in `ebl/app.py`. Even well-behaved
   traffic is affected in a milder way: 1000 four-token references produce
   ~3000 indexed `$or` branches per request.

3. **`candidate_splits` dropped the `isinstance(query, str)` guard that
   `split_text_and_number` had.** Line 41 of
   `mongo_afo_register_repository.py` calls `query.strip()` unconditionally.
   The repository is now correct only because the web layer validates first;
   any other caller of the `AfoRegisterRepository` interface passing a
   non-string gets an `AttributeError` instead of the previous silent skip.

4. **The 404 message interpolates the whole request body.**
   `ebl/afo_register/web/afo_register_records.py:60` builds
   `f"No AfO registry entries matching {str(req.media)} found."`, which can now
   echo up to ~500 KB of attacker-controlled input back to the client and into
   the logs. Pre-existing, but the new explicit size limits make the ceiling
   concrete.

5. **The `CHANGES_REQUESTED` review is still standing.** `reviewDecision` is
   `CHANGES_REQUESTED`; `0872112c` addresses two of the three points but the
   review has not been re-requested or dismissed, so the PR is blocked on
   Fabdulla1 regardless of the findings above.

6. **Behaviour broadening is intended but is a real contract change.** A
   reference that can be split in more than one way now returns *every*
   matching record rather than only the `rsplit` interpretation. This matches
   the old aggregation fallback and is covered by
   `test_search_by_texts_and_numbers_returns_all_ambiguous_matches`, but any
   client assuming a single result per reference should be checked.

7. **The new validation is a breaking change for oversized clients.** A client
   that batches more than 1000 references, or sends a reference longer than 500
   characters, now receives `422` where it previously received results. Worth
   confirming against the frontend's batching behaviour before merge.

8. **Single-token queries return `[]`.** Verified as *not* a regression: the
   old aggregation fallback matched against `concat(text, " ", textNumber)`,
   which always contains a space, so a space-free query could never match there
   either. Covered by
   `test_search_by_texts_and_numbers_without_splittable_query`.
   No action needed.

9. **Task-tracking files must be removed before merge.** `8e30b353` removed the
   original `TASK-afo-register-link-*.md` pair, but the working tree still
   carries `TASK-741-todo.md`, `TASK-741-log.md` and this review file. A `find`
   for `TASK-*.md` shows these three are the only task docs in the repository.
   None of them belong in `master`.

10. **`ebl/tests/afo_register/test_afo_register_repository.py` is at 216 of the
    250-line cap.** Not a violation, but the next few tests added there — for
    example the bound tests suggested in finding 2 — will need a split into a
    separate module.

## Severity

- Blocking: finding 1 (merge conflict), finding 5 (unresolved
  `CHANGES_REQUESTED`).
- High: finding 2 (unbounded generated query, reproducible HTTP 500 from a
  504 KB request by a guest user).
- Low: finding 3 (lost type guard), finding 4 (request echoed in error
  message), finding 7 (client-visible validation change).
- Informational: finding 6, finding 8, finding 9, finding 10.

## Reproduction Steps

Finding 1 — merge conflict:

```bash
git fetch origin master
git merge-tree $(git merge-base HEAD origin/master) HEAD origin/master \
  | grep -A3 'changed in both'
# -> .gitignore
# -> ebl/tests/fragmentarium/test_retrieve_annotations.py
gh pr view 741 --json mergeable,mergeStateStatus
# -> {"mergeStateStatus":"DIRTY","mergeable":"CONFLICTING"}
```

Finding 2 — HTTP 500 from a valid-looking request. Add this temporary test
under `ebl/tests/afo_register/` and run it with `poetry run pytest`:

```python
import json
import string

from ebl.afo_register.web.afo_register_records import (
    MAX_QUERY_LENGTH,
    MAX_TEXTS_AND_NUMBERS_QUERIES,
)

ALPHABET = string.ascii_lowercase + string.digits


def test_repro_oversized_candidate_query(client) -> None:
    token_count = (MAX_QUERY_LENGTH + 1) // 3
    tokens = [f"{a}{b}" for a in ALPHABET for b in ALPHABET]
    body = [
        " ".join([token] + ["ab"] * (token_count - 1))
        for token in tokens[:MAX_TEXTS_AND_NUMBERS_QUERIES]
    ]
    assert max(len(query) for query in body) <= MAX_QUERY_LENGTH
    result = client.simulate_post(
        "/afo-register/texts-numbers", body=json.dumps(body)
    )
    print("BODY BYTES:", len(json.dumps(body)))
    print("STATUS:", result.status)
```

Observed: `BODY BYTES: 504000`, `STATUS: 500 Internal Server Error`.

Query-size measurement without a server:

```python
import bson
from ebl.afo_register.infrastructure.mongo_afo_register_repository import (
    MongoAfoRegisterRepository,
)

repository = MongoAfoRegisterRepository.__new__(MongoAfoRegisterRepository)
candidate_query = repository._build_candidate_query(body)
len(candidate_query["$or"])            # 166000
len(bson.encode(candidate_query))      # 89_596_000 bytes (85.4 MB)
```

## Resolution

Applied in the working tree on 2026-08-11 (not committed).

- **Finding 1 — fixed.** `.gitignore` and
  `ebl/tests/fragmentarium/test_retrieve_annotations.py` were restored to the
  `origin/master` versions with `git checkout origin/master -- <paths>`. Both
  files are now byte-identical to `master`, so the conflict is gone. A merge or
  rebase onto `master` still has to be committed and pushed to clear the PR's
  `CONFLICTING` state.
- **Finding 2 — fixed.** Two bounds were added:
  - `MAX_QUERY_TOKENS = 24` in `afo_register_records.py`, enforced by the new
    `validate_query` helper, which caps the fan-out of a single reference at
    23 candidates;
  - `MAX_CANDIDATES = 10000` in `mongo_afo_register_repository.py`, enforced
    inside `_build_candidate_query`, which raises `DataError` (mapped to 422)
    so the repository is bounded independently of the web layer.

  Measured worst case that now survives validation: 9,982 `$or` clauses,
  0.08 s build time, 8.2 MB peak allocation, **4.78 MB** BSON — down from
  166,000 clauses / 1.59 s / 141.8 MB / 85.4 MB, and comfortably inside
  MongoDB's 16 MB limit. The original repro body now returns **422** instead of
  **500**, and a realistic batch of 1000 `"OrNS 59, N"` references still
  returns **200**.
- **Finding 3 — fixed.** `candidate_splits` returns `[]` for a non-`str` input
  again, restoring the guard `split_text_and_number` used to have. Its
  parameter is annotated `object` rather than `str`, so the runtime guard is
  something the type checkers can actually verify; `str` with an `isinstance`
  guard (what `split_text_and_number` had) makes the guard unreachable
  according to pyright and made the new test a type error.
- **Finding 4 — fixed.** The 404 message no longer interpolates the request
  body; it reports the number of submitted queries instead.
- **Finding 10 — fixed.** Candidate-query tests were extracted into
  `ebl/tests/afo_register/test_afo_register_candidate_query.py` (72 lines).
  `test_build_candidate_query_deduplicates_candidates` was moved there
  verbatim, not deleted. `test_afo_register_repository.py` is now 205 lines.
- **Findings 5 and 9 — open, and deliberately not actioned.** Re-requesting
  review, commenting `@sourcery-ai review`, and deleting the task-tracking
  files are outward-facing or merge-time actions awaiting the author's
  decision.
- **Findings 6, 7, 8 — informational, no change made.** Finding 7's surface
  grew slightly: a reference with more than 24 whitespace-separated words is
  now also rejected with 422.

### Gates after the fixes

- `poetry run pytest ebl/tests/afo_register
  ebl/tests/fragmentarium/test_retrieve_annotations.py --cov=ebl/afo_register
  --cov-report=term-missing` — 51 passed, **100%** coverage on every
  `ebl/afo_register` module.
- `task format` — 750 files already formatted, nothing left unformatted.
- `task lint` (ruff) — all checks passed.
- `poetry run flake8 ebl/afo_register ebl/tests/afo_register
  --max-line-length=120` — clean.
- `poetry run mypy ... --ignore-missing-imports` — no errors in any changed
  file.
- `poetry run pyre check` (`task type`) — no errors in `ebl/afo_register`.
- `npx pyright@1.1.411 <changed files>` — 0 errors. Note that
  `task type-pyright` exists on `origin/master` but **not** on this branch's
  `Taskfile.dist.yml`, so the branch is missing a gate that master enforces;
  the merge in recommendation 1 brings it back. Pyright was the only checker
  that caught the `candidate_splits` annotation problem above.
- 250-line cap: 160 / 80 / 205 / 188 / 72 lines — all pass.
- `task lint-md` — 0 errors.
- `task test` (full suite) — 3868 passed, 2 skipped, 1 xfailed, exit 0, run
  twice (before and after the `candidate_splits` annotation change). The skips
  and the xfail are pre-existing and unrelated to this change.

## Recommendation

Request changes. The core fix is good and I would approve it on its own merits;
these items should land first.

Before merge, in priority order:

1. Drop this branch's `.gitignore` and `test_retrieve_annotations.py` changes
   in favour of the versions already on `master`, then merge or rebase onto
   `master` so the PR is mergeable again. Both files are out of scope for this
   PR and are the sole cause of the conflict.

2. Bound the *generated* query, not just the request. Suggested shape, keeping
   the limits next to the existing constants:

   - add `MAX_QUERY_TOKENS` (real references are well under ~16 whitespace
     tokens) and reject longer queries in
     `validate_texts_and_numbers_query` with a `DataError`;
   - and/or add a `MAX_TOTAL_CANDIDATES` guard in `_build_candidate_query`
     that raises `DataError` once the candidate list exceeds it, so the
     repository is safe independently of the web layer.

   Add tests for both new limits — and note finding 10 when choosing where to
   put them.

3. Restore an explicit string guard in `candidate_splits` (return `[]` for a
   non-`str` input) so the repository does not depend on route-level
   validation for type safety.

4. Replace `str(req.media)` in the 404 message with something bounded, e.g. the
   number of queries, or a truncated preview.

5. Re-request review from Fabdulla1 and comment `@sourcery-ai review` so the
   latest two commits actually get bot coverage.

6. Delete `TASK-741-todo.md`, `TASK-741-log.md` and `TASK-741-review.md` before
   merging. They are the only task docs in the repository.

Optionally confirm with the frontend that no client batches more than 1000
references per request (finding 7).
