# TASK-afo-register-link — PR Review

PR: [#741](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/741)
— *Fix AfO Register texts-numbers match for references containing spaces*
Branch: `fix-afo-register-texts-numbers-split` → `master`
Reviewer: automated review (local verification run)

## Summary

The fix replaces the fragile "split the joined string on the last space"
recovery of `(text, textNumber)` with `candidate_splits`, which enumerates
every possible split point of the query's tokens and `$or`s the resulting
exact `{text, textNumber}` conditions. This is provably equivalent to
matching the `text + " " + textNumber` concatenation while still hitting the
compound `(text, textNumber)` index, and it correctly handles references
where either field contains spaces (e.g. `"OrNS 59, 17"`). The dead
`split_text_and_number`, `_build_indexed_query`, and `_build_fallback_pipeline`
were removed; drive-by `cast(...)` type annotations were added. The HTTP
contract is unchanged.

**Core logic and tests are correct. The blocking issues are all
repository-hygiene / scope, not the AfO fix itself.**

### Local verification (all green)

- `pytest` (repo + route suites): **18 passed**.
- Coverage on `mongo_afo_register_repository.py`: **100%** (73/73 stmts).
- `flake8 --max-line-length=120`: **0 errors**.
- `mypy --ignore-missing-imports`: **clean**.
- `pyre check` (CI-enforced): **No type errors found**.
- All touched `.py` files under the 250-line gate (148 / 190 / 95).
- Removed functions have **no remaining references** anywhere in `ebl/`.

## Findings

### F1 — Local Claude config committed to shared repo (High, blocker)

**Status: RESOLVED** — both files untracked via `git rm --cached` (kept on
disk so the local push-guard still runs) and added to `.gitignore`.

`.claude/settings.local.json` and `.claude/hooks/block-master-push.sh` were
added by this PR. `.claude/` does not exist on `master`.

- The `.local.json` suffix is, by Claude Code convention, a **per-developer
  machine-local** settings file that should be git-ignored, not committed.
  Committing it forces one contributor's `PreToolUse` hook wiring onto every
  other contributor and onto any tooling that reads the file.
- It is **not** in `.gitignore`, which is why it was picked up.
- Both files are **unrelated to the AfO Register bug fix** — they are
  fallout from the master-push incident described in the PR body. Bundling
  unrelated infrastructure into a bugfix PR is scope creep and conflicts with
  "do not make changes unless explicitly requested."

If the team genuinely wants a shared push-guardrail hook, it belongs in a
**separate PR**, with team sign-off, wired through shared `.claude/settings.json`
(not `settings.local.json`).

### F2 — Task-tracking scaffolding must be removed before merge (Low)

**Status: RESOLVED** — `TASK-afo-register-link-{todo,log}.md` untracked via
`git rm --cached`, and the `TASK-*.md` pattern added to `.gitignore` so task
scaffolding can never be committed again. This review file
(`TASK-afo-register-link-review.md`) is untracked/ignored and should be
deleted from disk once the review is acted on.

### F3 — Whitespace-normalization edge case (Info, not a blocker)

`candidate_splits` collapses internal/leading/trailing whitespace in the
**query** (`strip().split()` + `" ".join(...)`) and then matches exactly
against the **raw** stored `text` / `textNumber`. A stored record whose
`text` or `textNumber` contains doubled or edge whitespace would not match.
The removed fallback pipeline concatenated the raw fields, so it had the
mirror-image quirk. For clean data the two are equivalent, and AfO data is
expected to be clean — noting only so it is a conscious choice.

### F4 — Index usage (positive note) — Severity: Info

The `$or` of exact `{text, textNumber}` equality conditions is index-friendly
and the candidate count per query is bounded by `tokens − 1`, so the query
stays cheap. Good that the fix preserved compound-index usage instead of
falling back to an `$concat` aggregation.

## Severity

| Finding | Severity | Blocks merge? | Status |
| --- | --- | --- | --- |
| F1 — `.claude` local config committed | High | Yes | Resolved |
| F2 — `TASK-*.md` scaffolding present | Low | Yes | Resolved |
| F3 — whitespace normalization edge | Info | No | No action (info) |
| F4 — index usage | Info | No | No action (positive) |

## Reproduction Steps

Behavior fix (verified locally):

1. Seed a record `text="OrNS"`, `text_number="59, 17"`.
2. `POST /afo-register/texts-numbers` with body `["OrNS 59, 17"]`.
3. Before: `[]` (last-space split produced `text="OrNS 59,"`, `textNumber="17"`).
   After: the record is returned. Covered by
   `test_search_by_texts_and_numbers_route_with_spaces` and the repository-level
   space tests.

F1 (config leak):

1. `git ls-tree master -- .claude/` → empty (no `.claude/` on master).
2. `git show HEAD:.claude/settings.local.json` → personal hook config present.
3. `grep -nE 'claude|settings.local' .gitignore` → no entry.

## Recommendation

- **Approve the AfO fix on its merits** — logic is correct, equivalent to
  concat matching, index-preserving, fully tested, 100% coverage, all gates
  (incl. pyre) green, clean removal of dead code.
- **F1 / F2 addressed** in this branch: the `.claude` local config and the
  `TASK-*.md` scaffolding were untracked and gitignored; the PR diff is now
  just the source fix plus its tests (and the `.gitignore` hardening).
- F3/F4 are informational; no action required.

## Resolution (follow-up commit)

- `git rm --cached` on `.claude/settings.local.json`,
  `.claude/hooks/block-master-push.sh`, `TASK-afo-register-link-log.md`,
  `TASK-afo-register-link-todo.md` — untracked, kept on disk.
- `.gitignore` extended with `.claude/settings.local.json`,
  `.claude/hooks/block-master-push.sh`, and `TASK-*.md`.
- Gates re-run: `task format` clean, `task test` 3848 passed / 0 failed,
  `task lint-md` clean.
- PR description updated to drop the stale `.claude`/`TASK-*` merge caveats.

## Existing PR feedback incorporated (Review-Guidelines hard gate)

- **Sourcery (`sourcery-ai[bot]`)** submitted review + reviewer's guide: only
  actionable item is "remove the `TASK-*` scaffolding files before merging" →
  captured as **F2**.
- Inline (diff) review comments: **none**.
- Issue/conversation comments: only the Sourcery reviewer's-guide auto-comment.
- No other branches have been merged into this one (branch history is the
  single re-applied fix commit + the incident-recovery doc commit).

*Remove this review file before the PR is merged.*
