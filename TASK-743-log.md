# TASK-743 Work Log — Review of PR #743

## Metadata

- Task: review PR #743 "Make the ATF parser visible to the type checkers"
- Branch under review: `fix-type-checker-blind-spots`
- Started: 2026-09-01
- Constraint: review only; no code changes, no commits, no pushes

## Entries

### 1. Read the instructions (2026-09-01)

Read `.github/instructions/copilot.instructions.md` in full before touching
anything. Confirmed every section is a hard gate.

### 2. Created task artefacts

Created `TASK-743-todo.md` and `TASK-743-log.md` before starting any review
work, per the Task Tracking hard gate.

### 3. Identified the review target

`git branch --show-current` -> `fix-type-checker-blind-spots`.
`gh pr list` -> PR #743, "Make the ATF parser visible to the type checkers".
HEAD at start: `16a84e20 Address the round-11 review on PR #743`.
Working tree clean at start.

### 4. Fetched all PR feedback

- `gh api .../pulls/743/reviews` -> 12 reviews. Humans: Fabdulla1
  (CHANGES_REQUESTED 2026-08-07, APPROVED 2026-09-01). Bots: sourcery-ai (1),
  qltysh (7), github-advanced-security/CodeQL (3).
- `gh api .../pulls/743/comments` -> 22 inline comments (sourcery 1, qlty 16,
  CodeQL 5).
- `gh api .../issues/743/comments` -> 2 (Sourcery reviewer's guide; one reply).
- Local HEAD == remote head == `16a84e20`. The 2026-09-01 approval post-dates
  the last commit (2026-08-27), so its three points are unaddressed in the tree.

### 5. Checks

`gh pr checks 743`: all green. CodeQL "No new alerts in code changed by this
pull request". qlty check "No blocking issues", coverage 96.6% (+0.8%),
coverage diff 100.0%. `docker` and `Sourcery review` skipped.

### 6. Mechanical scans

- New `.md` files added by the PR: none. Modified: `docs/ebl-atf.md`,
  `.github/instructions/copilot.instructions.md`.
- `.devcontainer/`: untouched. `.github/workflows/`: untouched.
- Changed `.py` files over 250 lines: none. Closest: `lark_parser.py` at 250.
- Suppressions added by the diff: two `# type: ignore[arg-type]` in
  `ebl/tests/fragmentarium/test_fragment_pattern_matcher_site.py`, plus two
  pre-existing `# noqa` moved with `TokenVisitor` into `token_base.py`.

### 7. Local gates (against HEAD 16a84e20, tree clean)

| Gate | Result |
| --- | --- |
| `task format` | 863 files already formatted |
| `task lint` (ruff) | All checks passed |
| `task type` (pyre) | No type errors found |
| `task type-pyright` | 0 errors, 0 warnings |
| `flake8 --max-line-length=120` (123 changed files) | 0 |
| `mypy --ignore-missing-imports` (123 changed files) | Success, 0 issues |
| `qlty smells` (123 changed files) | 0 findings |
| `task test` | running |

### 8. Evidence gathered for individual findings

- Removed the two `# type: ignore[arg-type]` from
  `test_fragment_pattern_matcher_site.py` in a scratch copy: pyright reports 2
  `reportArgumentType` errors, mypy 2 `arg-type` errors. The suppressions are
  load-bearing, so the PR body's "no `# type: ignore`" claim is false. Restored
  the file; `git diff --stat` clean afterwards.
- Dumped `Museum` name -> value for base `c2b0a5ef` and HEAD via a scratch
  script and a detached worktree: **identical**, 72 members. The round-1 review
  finding about five `PRIVATE_COLLECTION_*` value shapes is resolved.
- `.devcontainer/` tree is byte-identical between base and HEAD (5 files).
  Nothing to warn about for this PR. Separately, `ruff format --check .` would
  reformat `.devcontainer/sync-env.py` and `test_sync_env.py`; both are
  pre-existing on master and outside `task format`'s `ebl` scope.
- `grep -rn "import \*"` over `ebl`: no star imports, so the `tokens.py`
  `__all__` narrowing breaks nothing in-repo today.
- `master`'s `tokens.py` has no `__all__`; sibling facade `sign_tokens.py`
  lists its locally-defined classes. `tokens.py` is the outlier.
- `search_composite_signs` and `File.content_type` signature changes align the
  ABCs with implementations that already had those types on master — correct,
  not defects.
- `TransliterationQueryFactory`'s shared mutable `SignsVisitor` is byte-identical
  to master; pre-existing, out of scope.

### 9. Full test suite

`task test` -> **4494 passed, 2 skipped, 1 xfailed in 323s**. Matches the count
claimed in the PR description.

### 10. Runtime verification (hard gate)

Booted the real service: `create_context()` + `create_app()` under waitress on
127.0.0.1:8123, against `mongodb://127.0.0.1:27017` database
`ebl_task743_review_throwaway` (a throwaway; `.env` was deliberately NOT
sourced — it points at production). `AUTH0_PEM` was a freshly generated
throwaway RSA public key, so `Auth0Backend.__init__` — which this PR changes —
really ran. Seeded two signs (KUR/kur, RA/ra).

The erasure line was `°nu : ši\ku°` and the dollar line was
`nu` followed by a newline and `$ blank`, matching the repo's own tests.

Results:

| Request | Status | Note |
| --- | --- | --- |
| `GET /signs/transliteration/kur` | 200 `[{"unicode":[74266]}]` | |
| `GET /signs/transliteration/kur%20ra` | 200 | whitespace marker between |
| `GET /signs/transliteration/$$$` | **422** | the claimed fix works |
| erasure line (see below) | **200** | no longer `AttributeError` |
| dollar line (see below) | **200** `[]` | non-text line handled |
| second erasure line | 200 | erased and over-erased both returned |
| `GET /signs?value=kur&subIndex=1` | 200 | split repository serves |
| `GET /signs?value=kur&subIndex=abc` | 422 | |
| `GET /signs?value=kur&subIndex=1&isComposite=true` | 200 | |
| `GET /signs?bogus=1` | 422 | dispatcher error path |
| `GET /signs?listAll=true` | **500** | see finding F5 — pre-existing |
| `GET /signs/KUR`, `/signs/KUR/order` | 200 | |
| `GET /signs/KUR/images` | 200 | |
| `GET /markup?text=@i{italic text}` | 200 | |
| `GET /markup?text=@i@kur@i@` | **500** | see finding F6 — pre-existing |
| `GET /fragments?random` (+ 2 more keys) | 200 | all dispatcher keys |
| `GET /fragments/query?transliteration=kur` | 200 | |
| `GET /fragments/query?transliteration=` | **500** | `IndexError`; disclosed |

Server stopped and the throwaway database dropped afterwards.

Error recovered during this step: the first boot attempt failed with
`ModuleNotFoundError: No module named 'ebl'` because the script ran from the
scratchpad without `PYTHONPATH`. Re-run with `PYTHONPATH=/workspaces/ebl-api`.
Also mis-guessed the erasure and dollar-line ATF syntax on the first pass and
got 422s; re-ran with the syntax the repo's own tests use
(`°nu : ši\ku°`, `nu\n$ blank`) and both returned 200.

### 11. Review document

Wrote `TASK-743-review.md` (456 lines) with a metadata header, a short
human-readable summary, a `Details` subsection covering every finding, and the
required `Summary` / `Findings` / `Severity` / `Reproduction Steps` /
`Recommendation` sections.

`task lint-md` initially failed on my own artefacts, twice, and both were fixed
rather than suppressed:

- `TASK-743-log.md` had four MD013 over-length lines and an MD056/MD060 table
  breakage caused by an unescaped `|` inside the erasure ATF in a table cell.
  Rewrote the affected rows.
- `TASK-743-review.md` had five MD036 violations (bold used as a heading in the
  Reproduction Steps section). Converted all eight step labels to real `###`
  headings.

The one rule deliberately turned off is MD013 in `TASK-743-review.md` only,
via a document-local `<!-- markdownlint-disable MD013 -->` on line 1. This is
the explicit user instruction ("remove the line length limit in the document,
so it can be nicely posted"). **No configuration file was touched** — not
`.markdownlint.json` (which does not exist in this repo), not
`.markdownlintignore`, not the `lint-md` task. `task lint-md` is green with
that directive in place, and the directive is an HTML comment so it is
invisible when the document is pasted into GitHub.

### 12. Findings recorded

F1 `NamePart` one-array/one-type gate (blocking), F2 `tokens.py` `__all__`
(blocking), F3 two load-bearing `# type: ignore` (blocking), F4 instruction
file changed vs description claim, F5 `/signs?listAll=true` 500 (pre-existing),
F6 `/markup` 500 (pre-existing), F7 redundant cast, F8 `update_alignment:
object`, F9 `_StartParser.__getattr__ -> object`, F10 shared default visitor,
F11 uneven annotation coverage, F12 duplicated `string_flags` (pre-existing),
F13 `singledispatchmethod` positional requirement (informational), F14
`lark_parser.py` at exactly 250 lines (informational).

All 12 prior reviews and all 22 inline comments are dispositioned in the review
file's "Existing PR feedback — disposition" table.

### 11. Review document written

`TASK-743-review.md` created with a metadata header (PR, branch, base, commit
reviewed, date, round, verdict), a short human-readable summary section, a
`Details` subsection carrying every finding in full, and the required
`Summary` / `Findings` / `Severity` / `Reproduction Steps` / `Recommendation`
sections.

The document carries `<!-- markdownlint-disable MD013 -->` at the top so its
lines are not wrapped at 80 characters and it pastes cleanly into GitHub. This
was an explicit user instruction. No linting configuration file was changed —
`.markdownlint.json` does not exist in this repo and none was created; the
directive is local to this one review artefact. `task lint-md` reports
**0 errors** across all 7 markdown files with it in place.

Error recovered: the first draft used bold paragraphs as section labels in
`Reproduction Steps`, which `task lint-md` rejected with 5 x MD036
(no-emphasis-as-heading). Converted them to `###` headings; re-ran, clean.

### 12. Coverage run

First attempt was killed at 62% when the previous session ended, leaving no
coverage table. Re-run from scratch against the same clean tree at `16a84e20`.

### 13. qlty plugins

`qlty check --no-fix` over all 123 changed files: **No issues**. This is in
addition to `qlty smells`, which also returned zero. Both agree with qlty
Cloud's "No blocking issues" on the PR page, and since local `HEAD` equals the
remote branch tip that cloud verdict is current, not stale.

### 14. Error recovered: duplicate coverage run

The backgrounded coverage command was re-executed by the harness, so two full
`pytest --cov=ebl` runs were live at once, both redirecting to the same
`cov.log` with `>`; the second truncated the file the first was still writing
to. Killed the older pair of processes (PIDs 37395/37396) and let the newer run
own the file from offset zero. No effect on the review's conclusions — the
earlier plain `task test` run had already completed cleanly at 4494 passed.

Second attempt completed: `4494 passed, 2 skipped, 1 xfailed in 580s` under
instrumentation, repository-wide `TOTAL 18026 statements, 637 missed, 96%`.

Cross-referencing the per-file table against the 123 changed `.py` files: 63
are source modules, all 63 appear in the table, and **all 63 are at exactly
100%** with zero missed statements. The other 60 changed files are test
modules, which `.coveragerc` excludes from the report. This corroborates both
the PR description and qlty Cloud's `coverage diff` verdict of 100.0%.

Error recovered: the first analysis pass used a malformed `awk`/`grep`
pipeline and reported "0 changed files in the coverage table", which was a bug
in my parsing, not a coverage gap. Re-sliced the table by line range and
re-ran; every changed source module was present.

### 13. qlty (fuller check)

`qlty check --no-fix` over all 123 changed files — which runs the plugins on
top of the structure and duplication analysis that `qlty smells` covers —
reports **"No issues"**. Together with the clean `qlty smells` run and qlty
Cloud's "No blocking issues", the qlty hard gate is satisfied three ways.

### 14. Upstream feedback check

Confirmed no other PR's branch was merged into `fix-type-checker-blind-spots`:
the two merge commits `05051576` and `525c4979` both take their second parent
from `master` (`#749`, which is the merge base itself, and `#748`, which
`git merge-base --is-ancestor` places inside the base). This PR was split out
of #740, which is merged and covers unrelated realia work; grepping all of
that PR's reviews, inline comments and conversation comments for `lark`,
`atf_parser`, `type check`, `pyright`, `pyre`, `mypy`, `NamePart`, `__all__`,
`token_base` and file-size terms returns nothing.

### 15. Task complete

Review exported to `TASK-743-review.md`. Verdict: request changes on F1-F3.
Nothing was committed or pushed; the working tree holds only the three
untracked `TASK-743-*.md` artefacts. HEAD is unchanged at `16a84e20`.
