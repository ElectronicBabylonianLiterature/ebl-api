# TASK pr735-fixes — TODO

Address every finding in `TASK-pr735-review.md` on branch
`add-realia-slugs-endpoint`.

- [x] Check out `add-realia-slugs-endpoint` (local = origin, `30a23b22`)
- [x] F1: non-string `reallexikon.reference.id` → schema treats as no
  reference; stub filter only counts string ids as resolvable; tests
- [x] F2: reserve the `by-id/` prefix; exclude such `_id`s from the list;
  by-id route uses the shared constant; tests
- [x] F3: exclude empty `_id` from the list; tests
- [x] F4: bound total staleness to 600 s via an `Age` header from the
  memoized timestamp; README note; tests
- [x] F5: one-type parametrize list for non-string identifiers
- [x] Keep every `.py` file ≤ 250 lines; 100% coverage on touched files
- [x] Gates: format, lint, pyre, pyright, mypy, flake8, full tests,
  coverage, qlty (changed + repo-wide vs master), lint-md
- [x] Runtime re-verify on the running service (local Mongo only)
- [x] P1: draft thread replies (posting is outward-facing — ask first)
- [ ] P2 (merge in TASK-pr735-merge): updating from `master` needs `git
      merge`/`rebase` — ask first;
  draft the PR description update (ask before editing on GitHub)
- [x] Update review file status; re-read instructions; report; do not commit
