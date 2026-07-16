# TASK-740 Review — Resolve realiaInfo on every fragment route

Scope: `f36ed7d9` (the only commit since the previous review, whose
findings landed in `3b58ebcb` and whose docs were removed in `0a8badca`).
PR: #740 — `add-realia-annotation-api` → `master`.

Findings 2, 3 and 4 have since been **fixed in the working tree** (all
changes uncommitted). Each finding below carries its resolution.

## Summary

The commit fixes a real defect correctly and at the right altitude.
`realia_info` was an optional argument of `create_response_dto`, and 11 of
12 call sites omitted it; `FragmentSchema.filter_none` then stripped the
`None`, so `realiaInfo` was silently absent from every write response.
Making the argument **required** and routing all resources through
`FragmentDtoFactory` converts a silent omission into a type error — the
defect class is designed out, not patched.

Verified locally: the full suite passes (3922 passed; the single failure is
pre-existing flakiness, see Gate status); all changed source modules are at
100% coverage, mypy-clean and pyright-clean. `resolve_realia_info`
short-circuits on empty realia, so write routes for realia-free fragments
incur no extra Mongo query.

**Data hard gate: compliant.** `realiaInfo` is its own array of one type
(`RealiaInfo`), structurally separate from `namedEntities` at domain,
document, and wire level. No mixed arrays, no discriminator, no probing.
The new `retrieve-all` payload keeps `realia` (annotation spans) and
`realiaInfo` (resolved info) as two separate single-type arrays.

No blocking correctness defects. The one remaining merge blocker is the
committed task docs (finding 1), left in place per instruction.

## Findings

### 1. Task tracking docs are committed — Severity: Medium (blocker)

`f36ed7d9` re-added `TASK-realia-fragment-debug-log.md` (406 lines) and
`TASK-realia-fragment-debug-todo.md` (74 lines), which `0a8badca` had
deliberately removed one commit earlier. Per the task-tracking convention
these must not reach `master`.

- Reproduction: `git show --stat f36ed7d9 | grep TASK-` — both listed as
  added.
- **Resolution: NOT ACTIONED** — explicitly excluded by the user. Still
  required before merge, together with the three `TASK-740-*.md` files.

### 2. `/fragments/retrieve-all` omits `realiaInfo` — Severity: Low

The commit message claims resolution on *every* fragment-returning route,
but `FragmentsRetrieveAllResource.on_get` hand-built its dicts — setting
`atf` and `hasPhoto` directly and bypassing `FragmentDtoSchema` entirely —
so `realiaInfo` was absent there. Any consumer feeding this route into
fragment state hit the same degradation class the PR fixes.

**Resolution: FIXED (batched).**

- New `resolve_realia_info_for_documents` in
  `ebl/fragmentarium/application/realia_info.py` collects the realia ids of
  a whole page, issues **one** `find_by_realia_ids`, and maps results back
  per document. Unknown (dangling) ids are dropped, matching the existing
  single-fragment behaviour.
- Extracted `_to_realia_info` so single and batched paths share one mapping.
- `FragmentsRetrieveAllResource` now takes `realia_repository`; wired in
  `bootstrap.py`. `zip(..., strict=True)` pins the per-document invariant.
- Tests: `realiaInfo == []` for a realia-free fragment; resolution across
  two fragments asserting exactly **one** batched call
  (`calls == [[APKALLU_ID, LAMASSU_ID]]`); a dangling id is skipped rather
  than raising.
- Verified on the wire (`skip=3899`, page of 1000): every fragment carries
  `realiaInfo`, and `VAT.5047` resolves to
  `[{Assur}, {Babylon, type: ["Geographical names"]}]`.

Cost: one extra Mongo query per page — negligible against a route that
takes ~300s to serialise 1000 fragments.

### 3. `edition.py:58` — Severity: Low (finding corrected)

Originally reported as an uncovered line with the recommendation "add a test
posting invalid ATF asserting 422". **That recommendation was wrong.**
Investigation showed the line is **unreachable dead code**:

- `_create_transliteration` catches `ValueError`, but
  `TransliterationError` extends `Exception`, not `ValueError`.
- `parse_atf_lark` converts every parse failure via
  `PARSE_ERRORS = (UnexpectedInput, ParseError, VisitError, EnclosureError)`
  into `TransliterationError` / `DuplicateLabelError`; none is a
  `ValueError`.
- `TransliterationUpdate._check_signs` likewise raises
  `TransliterationError`.
- Probed 10 invalid ATF inputs: all raised `TransliterationError`,
  `isinstance(e, ValueError)` false in every case.

A test could therefore never have covered it — it would have exercised
`on_post`'s own `except (..., TransliterationError)` handler, which already
returns 422 and is already tested.

**Resolution: FIXED** — removed the dead `try`/`except ValueError` from
`_create_transliteration`. `edition.py` is now 100% covered (was 97%).
Behaviour is unchanged: invalid ATF still yields 422 via the existing
handler.

### 4. `task type-pyright` is fragile — Severity: Low

Three failure modes: it required the `origin/master` ref (a shallow
`fetch-depth: 1` checkout would fail outright); `npx --yes pyright@1.1.411`
fetches from npm every run; `$FILES` was unquoted.

**Resolution: FIXED** — falls back to `master` when `origin/master` is
absent, and pipes filenames through `xargs` instead of unquoted expansion.
Verified both paths resolve correctly.

Two caveats deliberately left alone: the pinned pyright will drift from
whatever Pylance ships, and the gate diffs `BASE...HEAD`, so it only ever
sees **committed** changes — uncommitted work is not checked.

### 5. `cast()` proliferation suppresses rather than fixes — Severity: Info

~15 `cast()` calls were added purely to satisfy pyright, mostly around
marshmallow `load()`/`dump()`. They are unchecked at runtime: if a schema's
`@post_load` changes return type, the cast lies silently.

**Resolution: NO CHANGE — rationale.** This is inherent to marshmallow's
untyped API: `load()`/`dump()` are typed as returning `Any`, so there is no
fix available short of typed schema stubs or a wrapper layer. The casts are
locally correct. Removing them reintroduces the pyright errors the commit
set out to fix. Recorded as a known trade-off, not a defect.

### 6. `req.context["user"]` vs `req.context.user` — Severity: Info

Changed resources use mapping access while ~15 sites elsewhere
(`fragment_search.py`, `bibliography_entries.py`, `corpus/web/*`,
`require_scope.py`) keep attribute access.

**Resolution: NO CHANGE — rationale.** Both work (falcon's `Context`
supports both, and the route tests exercise these paths). Reverting the
changed files to attribute access would reintroduce pyright errors;
converting the other ~15 sites would touch modules unrelated to this PR and
pull them into the diff-scoped pyright gate. Best done as a dedicated
follow-up, not here.

### 7. Scope creep beyond the stated defect — Severity: Info

The devcontainer port forward and the pyright gate are unrelated to the
realiaInfo fix.

**Resolution: NO CHANGE — rationale.** Both are justified in the commit
message, are low-risk and dev-only, and reverting them would remove real
value (the gate caught genuine Pylance-only errors). Noted only because the
PR is already too large for automated review.

## Severity

| # | Finding | Severity | Resolution |
| --- | --- | --- | --- |
| 1 | Task tracking docs committed | Medium | Not actioned (excluded) |
| 2 | `retrieve-all` omits `realiaInfo` | Low | Fixed (batched) |
| 3 | `edition.py:58` dead code | Low | Fixed (removed) |
| 4 | `task type-pyright` fragile | Low | Fixed (fallback) |
| 5 | `cast()` suppresses | Info | No change — rationale |
| 6 | `req.context` inconsistency | Info | No change — rationale |
| 7 | Scope creep | Info | No change — rationale |

No finding is High or Critical. No correctness defect was found in the
change itself.

## Verification

Ran the modified backend service from the working tree (port 8002) against
the dev MongoDB, in addition to the test suite:

- **Clean boot, no error** — confirms `bootstrap.py` constructs all 12
  resources with the new `dto_factory` argument, and
  `FragmentsRetrieveAllResource` with its new `realia_repository`.
- **`GET /fragments/VAT.5047`**: `realiaInfo` resolved to
  `realia_001302` → "Assur", `realia_001514` → "Babylon".
- **`GET /fragments/K.1`** (realia-free): `realiaInfo: []` — present, not
  absent.
- **`GET /fragments/retrieve-all?skip=3899`** (HTTP 200, 1000 fragments,
  8.3 MB, 302s): every fragment carries `realiaInfo`; `VAT.5047` resolves
  correctly. Confirms the finding 2 fix.

One limit, stated plainly: **write routes were not exercised over HTTP** —
they return 403 without an Auth0 token. The write path is covered by the
route tests, including the test pinning `realiaInfo` in the POST response
and asserting it matches the GET. The read routes verified above were
already correct before this commit, so they do not by themselves
demonstrate the original fix.

## Gate status

| Gate | Result |
| --- | --- |
| `pytest ebl` (full) | 3922 passed, 1 failed (pre-existing flake) |
| Coverage, changed modules | 100% |
| `mypy` changed files | Clean |
| `pyright` changed files | 0 errors, 0 warnings |
| `ruff check` / `ruff format` | Clean |
| `flake8 --max-line-length=120` | 1 × E203, pre-existing class |
| File length ≤ 250 | Compliant; see note |
| `task lint-md` | 0 errors |

Notes:

- **The full-suite failure is pre-existing flakiness, unrelated to this PR.**
  `test_sign_images_route.py::test_signs_get_with_centroids_only_and_include_unclustered`
  died on `E11000 duplicate key: _id: "particularly"` in
  `cropped_sign_images`. `CroppedSignFactory.image_id = factory.Faker("word")`
  draws from a small vocabulary, so two builds can collide in a full run. It
  passes in isolation and this PR touches no `signs/` code. Worth a separate
  fix (seed or unique the id).
- **E203** is a ruff-format vs flake8-default conflict, not a content issue
  (`test_fragments_route.py:54` is formatter-produced slice spacing; master
  carries 12 of these). "Fixing" it would be reverted by `task format`.
  Resolving properly means ignoring E203 in flake8 config, which needs an
  explicit request.
- **`fragments.py` is now exactly 250 lines** — at the gate boundary, not
  over. Any further addition breaks it; `FragmentsRetrieveAllResource` is
  the natural extraction candidate.
- Pre-existing over-limit files this branch did not push past the limit:
  `token_schemas.py` (635), `test_fragment_updater.py` (417),
  `test_transliterations_route.py` (400), `test_word.py` (316).

## Existing PR feedback (mandatory check)

Fetched via `gh api` — reviews, inline comments, and issue comments:

- **sourcery-ai[bot]** (2026-07-16, COMMENTED): *"your pull request is larger
  than the review limit of 150000 diff characters"* — declined. No findings.
- Inline (diff) comments: none.
- Issue/conversation comments: none.
- No merged-in branch PRs to fetch feedback for.

No unresolved human or bot findings exist against this PR. The only signal is
that the PR (66 files, +2626/−419) exceeds automated review limits — worth
noting if you want bot coverage before merge.

## Reproduction Steps

```bash
# Finding 1 (still open)
git show --stat f36ed7d9 | grep TASK-

# Finding 3 — line 58 was unreachable (pre-fix)
poetry run python -c "
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
try: parse_atf_lark('invalid atf')
except Exception as e: print(type(e).__name__, isinstance(e, ValueError))"

# Gate verification
poetry run pytest ebl/tests/fragmentarium ebl/tests/realia -q -p no:randomly \
  --cov=ebl/fragmentarium/web --cov=ebl/fragmentarium/application \
  --cov=ebl/realia --cov-report=term-missing
npx --yes pyright@1.1.411 ebl/fragmentarium/web/fragments.py \
  ebl/fragmentarium/application/realia_info.py
```

## Recommendation

**Approve with changes.** The design is right and the defect properly fixed —
requiring the argument and injecting a factory removes the failure mode
rather than patching its symptom.

Findings 2, 3 and 4 are fixed in the working tree; 5, 6 and 7 are recorded
as accepted trade-offs with rationale above.

Before merge:

1. Remove the two committed `TASK-realia-fragment-debug-*.md` files and the
   three `TASK-740-*.md` files. **(blocker, not actioned)**
2. Consider extracting `FragmentsRetrieveAllResource` — `fragments.py` sits
   exactly on the 250-line limit.
3. Separately: fix the flaky `CroppedSignFactory` id collision.
