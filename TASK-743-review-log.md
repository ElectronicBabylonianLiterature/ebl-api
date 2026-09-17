<!-- markdownlint-disable MD013 -->
# TASK-743-review — Work Log

Review round 13 of PR #743. New task; own TODO/log per the task-tracking hard gate.

## 2026-09-16

### Step 0 — instructions

- Read `.github/instructions/copilot.instructions.md` in full before starting.
  Confirmed to the user which gates bind.

### Step 1 — task files

- Created `TASK-743-review-todo.md` and `TASK-743-review-log.md` BEFORE any
  review work, following the existing `TASK-743-fix-*` suffix precedent so the
  round-12 files (`TASK-743-todo.md`, `TASK-743-log.md`) are not clobbered.
- Decision: the review deliverable updates `TASK-743-review.md` in place rather
  than creating a second review file. Rationale: the review guideline says to
  keep the review file updated as findings change, one review document per PR,
  and the user asked for no new `.md` files.

### Step 2 — identifying the target

- `git branch --show-current` → `fix-type-checker-blind-spots`.
- `gh pr list --head fix-type-checker-blind-spots` → PR #743, OPEN, base `master`.
- Working tree clean at start.
- Noted 22 `TASK-*.md` files present in the repo root; whether the PR *adds* any
  of them is a review item (step 11), not assumed either way.

### Steps 2–3 — branch state

- `git fetch origin`; local `HEAD` = `549d45ae` = `git ls-remote` remote head. **Nothing unpushed**, so the PR-page verdicts are current, not stale.
- Merge base `c2b0a5ef`; `origin/master` has since moved to `e92b43d2` (PRs #763–#766 merged).
- 26 commits, 202 files, +15047 / −6910 (108 added, 78 modified, 16 renames).
- 9 commits since the round-12 review commit `16a84e20`.

### Steps 10–11 — dev container and markdown, checked early

- `git diff --name-status c2b0a5ef..HEAD -- .devcontainer` → **empty**. All five files byte-identical. **No dev-container warning needed.**
- Added `.md` files: **22 `TASK-*.md` task-tracking files, 4507 lines.** This is a regression against round 12, where the same query returned nothing. Blocking.
- Other config touched: `.github/instructions/copilot.instructions.md` (M), `ebl/fragmentarium/annotations.json` (M). No workflow/Dockerfile/pyproject/lockfile changes.

### Step 5–7 — GitHub feedback and checks

- Reviews: Sourcery ×1, qlty ×8, github-advanced-security ×5, `Fabdulla1` ×2 (CHANGES_REQUESTED 2026-08-07, APPROVED 2026-09-01 at `16a84e20`). Approval is **9 commits stale**.
- Inline comments: 26 qlty, 14 CodeQL, 1 Sourcery. 41 review threads; **3 unresolved**.
- Issue comments: Sourcery summary, plus my own 2026-08-25 comment.
- Check runs on `549d45ae`: all `success` or `skipped`. Commit statuses: `qlty check` = success but description reads **"2 blocking issues"**; coverage diff 100.0%; coverage 96.6% (+0.8%).
- **`mergeable=false`, `mergeable_state=dirty`** — a real conflict.
  `git merge-tree origin/master HEAD` → CONFLICT in `ebl/fragmentarium/domain/museum.py`. Caused by #765/#766 landing on master on 2026-09-16.
- CodeQL alert API returns 403 for this token; fell back to check runs (`CodeQL` and `Analyze (python)` both success) and the GAS review threads (all resolved).

### Step 8 — qlty reconciled against the base

- `qlty smells --all --include-tests` at HEAD: **106 findings**. Same in a detached worktree at merge base `c2b0a5ef`: **126**.
- Diff: branch **introduces 2 duplications spanning 4 files**, **removes 24 findings**. Net −20.
  - A: `transliteration/domain/tokens.py` ↔ `fragmentarium/domain/fragment.py`, 17 lines, mass 64 — two unrelated `__all__` lists.
  - B: `tests/factories/fragment.py` ↔ `tests/fragmentarium/test_museum_number.py`, 22 lines, mass 84 — an `__all__` list against `PREFIXES`, a list of museum-number prefixes. `test_museum_number.py` is **not** changed by the PR.
- Verdict: both are lists of bare string literals with no shared meaning — exactly the carve-out the instructions name. Justification exists in `TASK-748-log.md` and was moved into the PR description. Acceptable, non-blocking.

### Step 12 — round-12 blocking findings re-verified at `549d45ae`

- **F1 (mixed `nameParts`) — FIXED.** `NamePart` wrapper gone. `NamedSign` now has `name_parts: Sequence[ValueToken]` and `name_breaks: Sequence[BrokenAway]`, each with a validator. Wire: `nameParts` → `NameValueTokenSchema`, `nameBreaks` → `NameBreakSchema`; no `OneOfTokenSchema`, no discriminator. Domain split == wire split.
- **F2 (narrowed `__all__`) — FIXED.** `tokens.py` `__all__` now lists all 16 names including the nine locally defined classes.
- **F3 (load-bearing suppressions) — FIXED.** No `type: ignore` in `test_fragment_pattern_matcher_site.py`. Repo-wide, the PR adds **zero** new suppression comments; the two that exist (`lines_updater.py`, `annotations_service.py`) are pre-existing.
- **F4 (instruction file undisclosed) — FIXED.** Body line 324 now discloses it.

### Step 12b — behaviour equivalence, measured not assumed

- Wrote a 60-case ATF probe covering broken-away at every position, determinatives, `⸢⸣`, `<>`, `<<>>`, modifiers, flags, sub-indices, compound graphemes. Ran it at merge base and at HEAD, dumping `value`, `clean_value`, `name` and `Line.atf`.
- **Output byte-for-byte identical** (51 parsed, 9 rejected identically on both sides). The split is parser-behaviour-preserving.
- Legacy shape probe: every parser-produced legacy `name_parts` strictly alternates `ValueToken, BrokenAway, ...` starting with `ValueToken`. So the `separate_legacy_name_parts` even/odd split is sound for parser-produced data.

### Step 16 — running service (hard gate)

Booted the branch against a throwaway local Mongo (`127.0.0.1:27017`, db `ebl_t743_r13`) — `.env` deliberately not sourced, it points at production. Minted a throwaway RS256 JWT to reach authenticated routes.

- Seeded fragment `K.1` with **legacy interleaved** `nameParts` (as production holds today). `GET /fragments/K.1` → **200**, split correctly into `nameParts`/`nameBreaks`, values preserved (`ku[r`, `k[u]r`, `K]UR`). The shim works on a real route, not just in unit tests.
- `K.2`, legacy `nameParts` **not** alternating (leading `BrokenAway`) → **500** (marshmallow `ValidationError`). Master reads this shape fine, so it is a regression in reach — but PR #764's migration raises `NonAlternatingName` naming the document, so it is detectable before deploy.
- `K.3`, `nameBreaks` longer than `nameParts` → **500** via a bare `ValueError` from `_validate_name_breaks`. `ValueError` is not registered in `ebl/error_handler.py`, so it falls to `unexpected_error`. Every other domain validation error in this area surfaces as 422.
- First 500 seen was unrelated (`Invalid provenance: Assyria` — empty `provenances` collection in the throwaway db); re-seeded without `archaeology` and re-ran. Recorded here rather than silently dropped.

### Steps 14, 17 — file length and test loss

- No `.py` file changed by this PR exceeds 250 lines; the longest is `legacy_atf_converter.py` at 249. Gate clean. (The repo has pre-existing offenders up to 973 lines, none touched here.)
- Test functions 1647 → 1823. Three names disappear, all three **renamed with assertions intact** in `test_start_parser.py` (`__getattr__` was replaced by an explicit `options` property — the point of the change). Nothing skipped or xfailed.

### Step 11 — the markdown regression

- The PR adds **22 `TASK-*.md` files plus `TASK-749-frontend.patch`** — 23 stray root artefacts, 4507 lines of markdown.
- The description's own Gate 3 cleanup command is `git rm TASK-743*.md TASK-744*.md TASK-745*.md`, which **misses TASK-746 through TASK-749 and the `.patch`**.
- The migration scripts named in Gate 3 are already gone from the branch (moved to PR #764).

### Step 15 — local gates, all run at `549d45ae`

| Gate | Command | Result |
| --- | --- | --- |
| format | `ruff format --check ebl` | 886 files already formatted |
| lint | `ruff check ebl` | All checks passed |
| pyre | `pyre check` | **No type errors found** |
| pyright | `task type-pyright` (BASE=origin/master) | 0 errors, 0 warnings, 0 informations |
| test | `pytest` | **4530 passed, 2 skipped, 1 xfailed**, 282s |
| lint-md | `markdownlint-cli2` | 0 errors over 28 files |
| flake8 | `flake8 <160 changed> --max-line-length=120` | exit 0 |
| mypy | `mypy <160 changed> --ignore-missing-imports` | Success, no issues in 160 files |

`task test-all` exited 0. The 2 skips and 1 xfail are all pre-existing at the merge base (atf_importer integration test, exhaustive dollar-line module skip, a markup xfail) — none added here.

### Step 12c — remaining round-12 findings

- **F5 `GET /signs?listAll=true`** — was 500, now **200**. Fixed.
- **F6 `GET /markup` on unparsable input** — was 500, now **422** with `Invalid markup: "@i@kur@i@"`. Valid markup returns 200. Fixed. (My first probe showed 400 — that was my own missing `--data-urlencode`, not the service. Corrected and re-run.)
- **F7 redundant inner cast** — gone.
- **Sourcery's `TextLine.merge` cast** — the PR adds `@final` to `TextLine`. The cast is now sound by construction rather than merely unreachable. Structurally resolved.

### Step 13 — data hard gate sweep over the diff

- Only two mixed-type sequences remain in changed files: `manuscript_line.paratext: Sequence[Union[DollarLine, NoteLine]]` (with an `isinstance(line, DollarLine)` probe) and `chapter_query`'s `Sequence[Union["TextLine", L]]`. **Both are byte-identical at the merge base and untouched by this PR** — out of the gate's "any model you touch" scope. Informational only.
- `Branch = Union[str, Tree]` / `TreeChild = Optional[Union[Tree, Token]]` are new, but they mirror lark's own parse-tree shape, not a domain model.

### Step 18 — review document written

- Rewrote `TASK-743-review.md` in place for round 13. Sections: metadata header (commit, base, verdict, mergeability, stale-approval note), a short human-voiced `Summary` first, then `Findings` → `Details` with every finding in full, `Severity`, `Reproduction Steps`, `Recommendation`.
- `<!-- markdownlint-disable MD013 -->` kept at the top so the document has no line-length limit and pastes into GitHub cleanly. No lint config was modified to achieve this.
- Removed a table row naming the repository owner's GitHub username in the third person; the same reference in this task's TODO was reworded.
- `task lint-md` → 0 errors over 28 files, including the three files this task created/updated.

### Findings recorded

| Id | Severity | Finding |
| --- | --- | --- |
| B1 | High | 22 `TASK-*.md` + `TASK-749-frontend.patch` committed to the branch (4507 lines). Gate 3's own cleanup command misses TASK-746–749 and the `.patch`. |
| B2 | High | PR not mergeable — conflict in `ebl/fragmentarium/domain/museum.py` against `origin/master` (#765/#766). |
| B3 | Medium-High | `_validate_name_breaks` raises bare `ValueError`; unmapped in `error_handler.py` → 500 instead of 422. New path in this PR. Verified live on `GET /fragments/K.3`. |
| N1 | Low | Legacy shim keys on the absence of `nameBreaks`; a valid new-format payload with ≥2 `nameParts` and no `nameBreaks` is wrongly split and 422s. |
| N2 | Low | Non-alternating legacy document 500s where master reads it. Mitigated by #764's `NonAlternatingName`; deploy order should be stated. |
| N3 | Low | qlty's 2 blocking issues are justified false positives, but the description's "0 findings in any file this PR touches" row is stale. |
| N4 | Low | Description contradicts itself on whether the `nameParts` wire format changed (line 6 vs line 187). |
| N5 | Low | Approval is 9 commits stale. |
| N6 | Low | Companion PR #764 adds 14 `TASK-764-*.md` files — same cleanup needed. |
| I1 | Info | Pre-existing mixed arrays `manuscript_line.paratext`, `chapter_query` — untouched, out of gate scope. |
| I2 | Info | `_StartParser` no longer delegates arbitrary attributes; 3 tests renamed, not dropped. |
| I3 | Info | CodeQL alert API 403; verified indirectly via check runs and threads. |
| I4 | Info | Diff is 202 files; 4507 insertions are B1's artefacts. |

### Gates honoured for this task

Re-read `.github/instructions/copilot.instructions.md` before reporting. Confirmed: TODO and log created before work; all GitHub feedback fetched including bots and the merged-in companion PR; failing checks, qlty and CodeQL all checked; dev-container diff checked and reported (no change, so no warning raised); new `.md` files checked and reported as a blocking finding; data hard gate applied across the diff; running service exercised; three type checkers plus flake8, mypy, ruff, lint-md and the full suite all run and recorded; review exported to `TASK-<id>-review.md` with the required template; reminder to delete the artefacts before merge included. **Nothing committed or pushed — not requested.**
