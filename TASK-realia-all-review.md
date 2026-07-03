# TASK-realia-all — Review

## Summary

Reviews the `GET /realia/all` change on branch `add-realia-slugs-endpoint`
(commit `f8e6c9e6`). The endpoint returns a deterministic JSON array of every
Realia entry's `_id`, mirroring `/signs/all` and `/bibliography/all` for
frontend sitemap generation.

Scope of diff (8 files): `realia_repository.py` (abstract method),
`mongo_realia_repository.py` (`list_all_realia`), `realia.py`
(`RealiaListResource`), `bootstrap.py` (route), two test files, two task docs.

Verdict: **correct, no regressions, no security concerns, 100% coverage.**
Two low/informational trade-offs are inherent to the required `/signs/all`
parity and are accepted.

### GitHub feedback incorporated (HARD GATE)

No PR is open for `add-realia-slugs-endpoint`, so there is no in-progress
review to wait on. PR **#715** (`add-realia`, MERGED) is the base of this
work; its feedback was fetched and dispositioned:

- **Sourcery — explicit result ordering (bug_risk):** Addressed for the new
  endpoint — `list_all_realia` returns `sorted(...)`, so output is stable
  regardless of Mongo's `distinct` order. The original comment targeted the
  `search` method (unchanged here); out of scope for this diff.
- **Human reviewer (Fabdulla1) — pagination as Realia grows:** Directly
  relevant (see Finding 2). Task mandated no pagination for parity with the
  sibling list-all endpoints; documented as an accepted trade-off.
- **Sourcery — `NotFoundError` re-raise / bibliography-injection duplication /
  apostrophe stripping; CodeQL — unnecessary lambdas in `factories/realia.py`;
  qlty — `conftest` parameter count:** All in pre-existing, already-merged
  code not touched by this change. Out of scope; no action.

## Findings

- **Finding 1** — Low, accepted — `bootstrap.py`: an entry whose `_id` is
  exactly `"all"` is shadowed by `/realia/all` and unreachable via
  `GET /realia/{id}`. Status: addressed — locked by regression test.
- **Finding 2** — Low, accepted — `mongo_realia_repository.py`: no pagination;
  returns every id via `distinct("_id")`. Status: addressed — no-cap test added.
- **Finding 3** — Info, positive — `mongo_realia_repository.py`: deterministic
  `sorted` ordering; proactively satisfies #715's ordering concern for the
  analogous case. Status: confirmed — covered by existing tests.

### How each finding was addressed

- **Finding 1:** Routing/pagination cannot change without breaking the required
  `/signs/all` parity, so the intentional shadow is now **locked and documented**
  by `test_list_all_realia_shadows_entry_named_all`
  (seed `all` + `Pig` → `GET /realia/all` returns the list `["Pig", "all"]`,
  proving the list resource wins and the behavior is deliberate, not accidental).
- **Finding 2:** The endpoint must return everything (sitemap use); the concern
  is silent truncation. `test_list_all_realia_returns_every_id_without_limit`
  seeds 25 entries and asserts all 25 come back, **guarding against any future
  `.limit()`/cap** being introduced. Pagination itself remains intentionally
  absent per the task contract and the reviewer's own "future" framing.
- **Finding 3:** Deterministic ordering is already implemented (`sorted`) and
  asserted by `test_list_all_realia` (repo) and `test_list_all_realia` (route);
  no change needed.

### Finding 1 — `_id == "all"` collision (Low, accepted)

Because `/realia/all` is a static route registered before `/realia/{realia_id}`
(and ahead of the slash-lemma sink), a hypothetical Realia entry whose `_id` is
literally `"all"` resolves to the list endpoint, not the single-entry handler.
This is the same, intentional collision `/signs/all` has, and the task
explicitly requires matching that registration. Realia lemmas are proper nouns
(e.g. `Pig`, `Anu`, `Elam (Geschichte)`), so a lemma named exactly `all` is
implausible. No change recommended.

### Finding 2 — No pagination (Low, accepted)

The endpoint materialises all ids. This is required for sitemap parity with
`/signs/all` and `/bibliography/all`, and the payload is short lemma strings
only (not documents), so the Mongo `distinct` 16 MB cap is far off for any
realistic corpus. Matches the reviewer's #715 growth note as a known future
consideration, not a defect in this change.

### Finding 3 — Deterministic ordering (Info, positive)

`return sorted(self._realia_collection.get_all_values("_id"))` guarantees
reproducible sitemaps and removes any dependency on Mongo's `distinct` order.

## Reproduction Steps

Correct behaviour (all verified locally):

- `poetry run pytest ebl/tests/realia -q` → 69 passed.
- Route: `GET /realia/all` on a seeded collection → `200` with a sorted string
  array (`test_list_all_realia`).
- Not shadowed by `{id}`: `GET /realia/all` on an empty collection → `200 []`
  (not `404`), proving the list resource wins over `find("all")`
  (`test_list_all_realia_is_not_shadowed_by_id`).
- Finding 1 confirmed by a throwaway test (since removed): with entries `all`
  and `Pig` seeded, `GET /realia/all` → `["Pig", "all"]` (the list, not the
  single entry).
- Auth: same unauthenticated `client` fixture as every other realia route test,
  matching `/signs/all`.

## Recommendation

**Approve.** No blocking issues. The two low-severity items are inherent to the
required `/signs/all` parity and were explicitly scoped that way by the task.

Gates re-confirmed: `task format` clean, `flake8 --max-line-length=120` clean,
`mypy` clean on changed files (repo-wide pre-existing mypy errors are unrelated
and untouched), 100% coverage on all four changed modules, full suite
**3786 passed**, all touched files < 250 lines.

> Remove this file (and `TASK-realia-all-todo.md`, `TASK-realia-all-log.md`)
> before the PR is merged.
