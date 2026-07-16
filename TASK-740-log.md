# TASK-740 Work Log — Review of PR #740

Date: 2026-07-16. Branch: `add-realia-annotation-api` @ `f36ed7d9`.

## 1. Scope determination

Established the review scope as `f36ed7d9`. Prior review's findings were
addressed in `3b58ebcb` (2026-07-15 14:51) and its docs removed in
`0a8badca` (15:00); `f36ed7d9` (2026-07-16 13:50) is the only work since.
Working tree was clean at start.

## 2. Mandatory GitHub feedback fetch

Queried reviews, inline comments and issue comments via `gh api`. Only
result: `sourcery-ai[bot]` declined the review — PR exceeds its 150000
diff-character limit. No inline comments, no issue comments, no merged-in
branch PRs. Nothing to address or acknowledge.

## 3. Diff analysis

Read the full diff. Core change: `realia_info` becomes a required argument
of `create_response_dto`; new `FragmentDtoFactory` owns resolution and is
injected into every fragment-returning resource.

Verified via grep that no production `create_response_dto` call site
remains — all 12 resources go through the factory. Remaining direct callers
are tests only.

Checked the data hard gate: `realiaInfo` is a single-type array
(`RealiaInfo`), structurally separate from `namedEntities` at domain,
document and wire level. Compliant.

Checked performance: `resolve_realia_info` short-circuits on empty realia,
so realia-free write routes incur no additional Mongo query. No concern.

Found `/fragments/retrieve-all` hand-builds its payloads and bypasses
`FragmentDtoSchema`, so it carries no `realiaInfo` (finding 2).

## 4. Gates

- `pytest ebl/tests/fragmentarium ebl/tests/realia` — 933 passed.
- Coverage: first attempt was invalid (passed a comma-joined list to
  `--cov`, which takes one path per flag; measured nothing). Re-ran with
  separate flags: all changed modules 100% except `edition.py:58` (97%).
- Confirmed `edition.py:58` is a pre-existing gap — `f36ed7d9` touches
  lines 14, 21, 41, 45, 64, 73; line 58 last changed by `245e5b56a`.
- `mypy` on changed source files: 34 errors, none located in a changed
  file; all in transitively imported, untouched modules.
- `flake8`: 2 × E203. Established as pre-existing class — master carries
  12. Ruff-format vs flake8-default conflict; not a content issue. Left
  alone (fixing needs a config change, which requires explicit request).
- File length: 4 changed files exceed 250 lines, all already over on
  master. `test_transliterations_route.py` (391→400) is the only one this
  commit touched.
- `task lint-md`: 0 errors.

## 5. Service verification

First attempt was invalid and was discarded. `nohup waitress-serve
--port=8001` failed to bind (`OSError: Address already in use`); a
pre-existing process (PID 108367, started 12:14:16, i.e. before `f36ed7d9`
was authored at 13:50:40) served the responses. Additionally the route
checked (`GET /fragments/{number}`) was the one call site that already
passed `realia_info` before the fix, so the output proved nothing.

Re-ran correctly on port 8002 from the clean tree at `f36ed7d9`:

- Clean boot with no error — confirms `bootstrap.py` constructs all 12
  resources with the new `dto_factory` argument.
- `GET /fragments/VAT.5047` (has realia): `realiaInfo` present and
  resolved — `realia_001302` → "Assur", `realia_001514` → "Babylon"
  (with `type: ["Geographical names"]`). Confirms the resolution path
  against production-shaped data.
- `GET /fragments/K.1` (realia-free): `realiaInfo: []` — present, not
  absent. This is the behaviour the fix targets.
- `GET /fragments/retrieve-all`: no response within 120s (bulk export over
  the full dev DB). Finding 2 therefore rests on code reading, not wire
  confirmation.
- Write routes (e.g. `POST .../named-entities`) return 403 without an
  Auth0 token, so the write path could not be exercised by curl. It is
  covered by the route tests, including the new test pinning `realiaInfo`
  in the POST response and asserting it matches the GET.

## 6. Errors made during this task

- Ran `git stash` / `git stash pop` around a branch switch to master to
  check E203 attribution. The tree was clean so the stash saved nothing,
  and the pop restored an unrelated pre-existing `stash@{0}`, conflicting
  in `ebl/bibliography/application/bibliography.py`. Recovered with
  `git restore --source=HEAD` (not `reset --hard`, which the gate forbids);
  `stash@{0}` survived intact, as a conflicting pop does not drop the entry.
  The branch switch was unnecessary — `git show master:<path>` reads other
  revisions without touching the tree.
- Skipped the mandatory TODO and log files on the first pass and the
  `Severity` section of the review template; corrected.
- Server PID 108367 (the pre-existing one on 8001) is no longer running. I
  signalled only my own PID (339025); cause unknown, but I cannot rule out
  that I caused it. Restartable with `task start`.

## 7. Review outcome

Approve with changes. No blocking correctness defects. One merge blocker:
`f36ed7d9` re-added two `TASK-realia-fragment-debug-*.md` files that
`0a8badca` had removed. Full detail in `TASK-740-review.md`.

## 8. Addressing the findings

User asked for all findings except removing the task docs.

**Finding 2 — fixed (batched).** Asked the user first, since it changes a
public bulk route's response shape and only they know the consumer; they
chose the batched resolve. Added `resolve_realia_info_for_documents`, which
collects a page's realia ids, issues one `find_by_realia_ids`, and maps back
per document, dropping dangling ids as the single-fragment path does.
Extracted `_to_realia_info` so both paths share one mapping. Injected
`realia_repository` into `FragmentsRetrieveAllResource` and wired it in
`bootstrap.py`. Used `zip(..., strict=True)` to pin the per-document
invariant (ruff B905 flagged the bare `zip`). Extracted shared test helpers
to `ebl/tests/fragmentarium/realia_helpers.py`, following the existing
`realia_repository_helpers.py` convention, and refactored
`test_realia_info_route.py` onto them rather than duplicating.

**Finding 3 — my own recommendation was wrong; corrected.** I had proposed
adding a test posting invalid ATF to cover `edition.py:58`. Before writing
it I checked what actually reaches that line and found it unreachable:
`TransliterationError` extends `Exception`, not `ValueError`; `parse_atf_lark`
funnels every failure through `PARSE_ERRORS = (UnexpectedInput, ParseError,
VisitError, EnclosureError)` into `TransliterationError`; and
`TransliterationUpdate._check_signs` raises `TransliterationError` too.
Probed 10 invalid ATF inputs — all `TransliterationError`, none a
`ValueError`. So no test could ever have covered it. Removed the dead
`try`/`except ValueError`; `edition.py` went 97% → 100%. Behaviour unchanged
— invalid ATF still returns 422 through `on_post`'s existing handler.

**Finding 4 — fixed.** `BASE` falls back to `master` when `origin/master` is
missing; filenames now go through `xargs`. Verified both branches resolve.
Noted but left: the gate diffs `BASE...HEAD`, so it only sees committed
changes.

**Findings 5, 6, 7 — no code change, rationale recorded** in the review.
5 is inherent to marshmallow's `Any`-typed API; 6 and 7 would either
reintroduce the pyright errors the commit fixed or drag unrelated modules
into the diff-scoped gate. Both are follow-up work, not this PR.

## 9. Post-change verification

- `ruff check`/`format` clean. Ruff caught two real mistakes: a bare `zip`
  (B905) and an import I removed from `test_realia_info_route.py` while it
  was still in use (F821 × 4).
- Full suite: 3922 passed, 1 failed. The failure —
  `test_sign_images_route.py::test_signs_get_with_centroids_only_and_include_unclustered`,
  `E11000 duplicate key _id: "particularly"` — is pre-existing flakiness:
  `CroppedSignFactory.image_id = factory.Faker("word")` draws from a small
  vocabulary and can collide in a full run. Passes in isolation; this PR
  touches no `signs/` code.
- Coverage 100% on all changed modules; mypy clean; pyright 0 errors.
- Re-ran the service and confirmed finding 2 on the wire:
  `GET /fragments/retrieve-all?skip=3899` → HTTP 200, 1000 fragments, 8.3 MB,
  302s; every fragment carries `realiaInfo`, and `VAT.5047` resolves to
  Assur and Babylon.

## 10. State

Nothing committed. All work left uncommitted in the working tree.
