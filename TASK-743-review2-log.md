<!-- markdownlint-disable MD013 -->

# TASK-743-review2 — Work Log

## Step 1 — Read instructions, created tracking files

- Read `.github/instructions/copilot.instructions.md` in full before acting.
- Identified the PR: #743, `fix-type-checker-blind-spots` -> `master`, OPEN, not a draft.
- Created `TASK-743-review2-todo.md` and this log before starting review work.
- Observation while orienting: seven `TASK-743-*.md` files are **tracked by git** (`git ls-files 'TASK-*'` lists them) and the working tree is clean, so they are committed on the branch. This is directly relevant to the user's "no new `.md` files should be present" requirement — to be confirmed against the diff vs `master`.
- Note: repo has no `.markdownlint.json`; `task lint-md` runs markdownlint-cli2 over `**/*.md`, so MD013 (line length) is active by default. The user asked for no line-length limit in the review document, so the review file disables MD013 inline rather than changing any lint configuration file (config edits are forbidden without an explicit request).

## Step 2 — Fetched all GitHub feedback (HARD GATE)

- `gh api .../pulls/743` — 125 files, +6586/-3937, 10 commits, head `6926bc1a`, mergeable_state `blocked`.
- `gh api .../pulls/743/reviews` — 8 reviews: sourcery-ai[bot] (1 issue), qltysh[bot] x4, Fabdulla1 (CHANGES_REQUESTED, 5 points), github-advanced-security[bot] x2.
- `gh api .../pulls/743/comments` — 19 inline comments (sourcery 1, qlty 13, CodeQL 5).
- `gh api .../issues/743/comments` — 2 (sourcery Reviewer's Guide, khoidt reply to Fabdulla1).
- No PR whose branch was merged into this one carries further feedback (branch is a straight split from #740; #740's own review context is not part of this diff).

## Step 3 — Checks and qlty

- `gh pr checks 743`: CodeQL pass, Analyze (python) pass, GitGuardian pass x3, qlty check **pass — "No blocking issues"**, Sourcery review skipping, **Test Python 3.11 / 3.12 / pypy-3.11 in progress at the time of review** (6 jobs, two workflows). No failing check observed.
- Combined status rollup: `success`.

## Step 4 — Dev container check (user-requested warning)

- `git diff --name-status master..HEAD` over `.devcontainer/**`, `Dockerfile*`, `docker-compose*`, `.github/**`, `Taskfile*`, `pyproject.toml`, `poetry.lock`, `.vscode/**`, `.claude/**`, lint configs, `.pyre_configuration`: **empty**. No dev container or tooling configuration is touched by this PR. Nothing to warn about; reported explicitly.

## Step 5 — `.md` files check (user requirement)

- The PR **adds seven tracked `.md` files**: `TASK-743-todo.md`, `TASK-743-log.md`, `TASK-743-fix-todo.md`, `TASK-743-fix-log.md`, `TASK-743-review.md`, `TASK-743-commit-todo.md`, `TASK-743-commit-log.md`. Confirmed by `git diff --name-status` (all `A`) and `git ls-files 'TASK-*'`. This is finding F1.
- `docs/ebl-atf.md` is modified (grammar-path rename) — legitimate, not a new file.

## Step 6 — Local gates (run against the working tree at `6926bc1a`, clean)

| Gate | Command | Result |
| --- | --- | --- |
| format | `poetry run ruff format --check ebl` | 844 files already formatted, exit 0 |
| lint | `poetry run ruff check ebl` | All checks passed, exit 0 |
| type (pyre) | `poetry run pyre check` | **No type errors found** |
| type-pyright | pyright 1.1.411 on 101 changed files | **0 errors, 0 warnings** |
| mypy | `mypy <101 changed files> --ignore-missing-imports` | Success: no issues found in 101 source files |
| flake8 | `flake8 <changed> --max-line-length=120` | exit 0 |
| lint-md | `markdownlint-cli2 "**/*.md" ...` | 0 errors (13 files) |
| test | `pytest -q` (in-memory Mongo, `.env` not sourced) | **4385 passed, 2 skipped, 1 xfailed** in 360s |
| 250-line cap | every changed `.py` | none over 250 |
| line length | every changed `.py` | none over 120 |

Note: pytest was run via `poetry run` directly rather than `task test`, because `Taskfile.dist.yml` has `dotenv: [".env"]` and `.env` points `MONGODB_URI` at the production cluster. `MONGODB_URI`/`MONGODB_DB` were unset for the run; `ebl/tests/conftest.py` then uses `pymongo_inmemory`.

## Step 7 — Deep review of the diff

- Verified the grammar rename is `R100` for all 16 `.lark` files and that all 8 path references are updated.
- Verified sourcery's `TextLine.merge` finding is resolved by `@final` on `TextLine` (the only change to that file); no subclass of `TextLine` exists, so the `cast(L, ...)` is sound.
- Verified all 5 CodeQL findings are fixed at HEAD (`...` bodies replaced with `raise NotImplementedError`; `lambda value: bool(value)` replaced with `bool`).
- Verified all 72 `Museum` members are identical to master across `(value, museum_name, city, country, url)` — 0 differing.
- Verified `nameParts` wire format round-trips and is unchanged.
- Verified `LineVariant` converter order preserved (`pydash.flow` unrolled correctly).
- Verified `__all__` facades: nothing still imported from an old path is missing.
- Checked the data hard gate on the `NameParts` change — domain array is now single-type; wire array remains a deliberate `OneOfTokenSchema` union for backward compatibility, recorded explicitly in the review.

### Errors made and recovered during this task

1. First facade-completeness check spawned one `poetry run python` per name and timed out after 5 minutes before finishing `museum.py`. Recovered by rewriting it as a single in-process comparison.
2. First coverage/diff intersection used `comm` on numerically-sorted input, which emitted "file is not in sorted order" and made the result unreliable. Recovered by redoing the intersection in Python with set arithmetic; result: 0 uncovered lines among lines the PR adds or changes.
3. To confirm F3, `frozen=True` was temporarily restored in `transliteration_query.py`, the behaviour observed, and the file restored from a backup copy. `git status` confirms the tracked tree is clean — the only untracked files are this task's three artefacts.

## Step 8 — Runtime verification (HARD GATE)

- Started `waitress-serve` on port 8123 against a local MongoDB (`127.0.0.1:27017`, isolated database `ebl_review_743`), with `.env` explicitly not sourced. Seeded two signs, exercised 10 requests across the affected routes, then stopped the server and dropped the database.
- Key result: `GET /signs/transliteration/$$$` returns **422** on the running service, confirming the fix Fabdulla1 reported as missing.

## Step 9 — Review written

- `TASK-743-review2-review.md` created with the requested friendly short summary first, a `Details` subsection listing every finding, and the required `Summary` / `Findings` / `Severity` / `Reproduction Steps` / `Recommendation` sections.
- MD013 (line length) disabled inline in the document per the user's request, so it can be posted without re-wrapping. No lint configuration file was modified.
- `task lint-md` equivalent run over the whole repo: 0 errors.

## Final state

- **No commit, no push, no `gh pr` action was taken.** Working tree holds three new untracked files and no modification to any tracked file.
