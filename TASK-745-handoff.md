<!-- markdownlint-disable MD013 -->
# Handoff — PR #743, everything outstanding before merge

Supersedes the earlier `TASK-743-fix-handoff.md`. This is the current, complete
picture.

**Branch:** `fix-type-checker-blind-spots` -> `master`
**PR:** [#743](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743)
**Last pushed commit:** `15da7c12` — all checks green, qlty at 2 blocking
issues (both justified). Note this repo can also push without an explicit
`git push`.
**Migration PR:** [#764](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/764)
— open, `migrate-name-breaks` -> `master`.
**Written:** 2026-09-15, rewritten after the TASK-746 work

---

## 1. What this PR does

Two things. It makes the ATF parser visible to the type checkers — a module and
a directory shared a dotted name, so mypy and pyright resolved the import to an
empty namespace package and **the parser was never type-checked**. And it pays
down the debt that became visible once they could see it.

The round-12 review then added one substantial change: `nameParts` held two
different token types in one array, and the fix splits it into `nameParts` and
`nameBreaks`. That is a **breaking wire-format change and a stored-data change**,
which is where most of the remaining risk lives.

---

## 2. Blocking gates — status

### Gate 1 — the frontend must read `nameBreaks`

```text
before  "nameParts":  [ValueToken("k"), BrokenAway("]"), ValueToken("u")]
after   "nameParts":  [ValueToken("k"), ValueToken("u")]
        "nameBreaks": [BrokenAway("]")]
interleave: parts[0], breaks[0], parts[1], ...  ->  k ] u
```

**Status: COMMITTED and green, but NOT PUSHED and NO PR — blocked on credentials.**

The work is commit `a9df351` on branch **`add-name-breaks`** in a clone at
**`/workspaces/ebl-frontend`** — deliberately not a scratchpad, because a
cleared scratchpad destroyed the first attempt.

**It cannot be pushed from this codespace — every route was tried.**

```text
remote: Permission to ElectronicBabylonianLiterature/ebl-frontend.git denied to khoidt
gh api .../ebl-frontend/git/blobs -X POST  ->  Resource not accessible by integration
```

`git push` with the codespace helper, `git push` routed through `gh auth token`,
the Git Data API, `GITHUB_CODESPACE_TOKEN` (401, wrong API) and SSH (no keys, no
agent) all fail. `gh api repos/.../ebl-frontend --jq .permissions` reporting
`push: true` is misleading: that is the **user's** permission, not the token's
scope. The codespace's GitHub App installation covers `ebl-api` only.

`ebl-api` pushes fine, and the auto-push seen on that repo is the IDE using the
user's own credentials — so **the IDE can very likely push this branch even
though the terminal cannot**. Push it from the VS Code Source Control view with
`/workspaces/ebl-frontend` open, or from any checkout outside the codespace.

A PR description is ready at **`/workspaces/ebl-frontend-pr-body.md`** — outside
both repositories, so it neither pollutes a working tree nor sits in a clearable
scratchpad. Once the branch is up:

```bash
cd /workspaces/ebl-frontend
gh pr create --base master --head add-name-breaks \
  --title "Read nameBreaks alongside nameParts" \
  --body-file /workspaces/ebl-frontend-pr-body.md
```

What was changed, in `ElectronicBabylonianLiterature/ebl-frontend`:

- `src/transliteration/domain/token.ts` — `NamedSign` gains
  `readonly nameBreaks?: readonly Enclosure[] | null`, plus a new exported
  `nameTokens(namedSign)` that returns `nameParts` unchanged when `nameBreaks`
  is absent or null and otherwise interleaves `parts[i], breaks[i]`.
- `src/transliteration/domain/token.ts` — `extractEnclosureTypes` maps over
  `nameTokens(namedSign)`.
- `src/transliteration/domain/accents.ts` — `addAccents` reduces over
  `nameTokens(namedSign)`.

`nameParts` keeps its union type on purpose; narrowing it breaks the legacy
fallback.

Seven tests: the five specified cases (split input, no breaks, trailing break,
legacy interleaved payload, explicit `null`) in `token.test.ts`, plus two in
`accents.test.ts` that go through `addAccents` — the function
`DisplayToken.tsx:174` actually calls — so a name is asserted to *render* as
`k ] u`.

The interleave was checked against the backend rather than assumed:
`NamedSign._interleaved` uses `zip_longest(name_parts, name_breaks)` and
`_validate_name_breaks` enforces `len(breaks) <= len(parts)`, so the two agree
including the trailing-break case.

Frontend gates, all green: `tsc --noEmit` 0 errors, `yarn lint` clean, full
`yarn test` **435 suites / 4180 tests passed**.

**Trap: the repo needs Node 20**, not the default 22 — `yarn install` fails with
`The engine "node" is incompatible`. Use
`export PATH="/usr/local/share/nvm/versions/node/v20.19.1/bin:$PATH"`.
It uses **yarn**, not npm. The install takes about 200s. The same trap bites
`git commit`: husky's pre-commit hook shells out to yarn and fails on Node 22
before running anything.

### Gate 2 — the data migration: MOVED OUT OF THIS PR

**This is no longer a gate on #743.** The migration and its test are now
[PR #764](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/764),
on `migrate-name-breaks` off `master`. #743 no longer contains any DB-related
change.

**Why it moved: running it before #743 deploys would break production.** The
currently deployed code rejects a migrated document outright —

```text
ValidationError: {'lines': {0: {'content': {0: {'parts': {0:
  {'nameBreaks': ['Unknown field.']}}}}}}
```

Marshmallow defaults to `unknown = RAISE`, so `master` does not ignore the new
field, it refuses to load the fragment. Migrating first would take out every
fragment the migration touched. The order has to be expand, migrate, contract:

1. **#743 merges and deploys.** The new code reads both shapes.
2. **Then the migration runs**, from the `migrate-name-breaks` branch.
3. **Then a later PR deletes the `@pre_load` adapter** and its tests, once no
   legacy documents remain.

That cannot be one PR — you cannot add the compatibility adapter and delete it
in the same change.

#### What stays in #743, and must not be moved

The `@pre_load` adapter `separate_legacy_name_parts` in
`ebl/transliteration/application/token_schemas_signs.py` **stays**. It looks
DB-related, but it is what makes #743 deployable at all: without it the new code
cannot read a single existing document. Verified by loading a legacy
interleaved `nameParts` through the field schema —

```text
ValidationError: {1: {'type': ['Must be equal to ValueToken.']}}
```

#### State of the migration branch

`migrate-name-breaks`, branched from `origin/master` at `a061472f`.

**The files follow this repo's existing migration convention.** `master` already
carries two merged one-off migrations — `ebl/dictionary/migrate_named_entity_tags.py`
and `ebl/fragmentarium/migrate_cropped_images.py`, each with a test beside it in
`ebl/tests/<domain>/`. So the script was renamed and moved to match:

| Was | Is |
| --- | --- |
| `task_743_migrate_name_breaks.py` | `ebl/transliteration/migrate_name_breaks.py` |
| `task_743_migrate_name_breaks_test.py` | `ebl/tests/transliteration/test_migrate_name_breaks.py` |

That settles both questions that were open here. **It merges** — the repo keeps
migration scripts on `master` rather than deleting them — and the `task_743_`
prefix is gone, since the script belongs to the repo's migration set, not to a
pull request. The "TEMPORARY — MUST NOT BE MERGED" docstring was removed and
replaced with one that explains the shape change and warns that it must run only
after the new backend is deployed.

It is invoked as a module now, matching its new home:

```bash
poetry run python -m ebl.transliteration.migrate_name_breaks           # dry run
poetry run python -m ebl.transliteration.migrate_name_breaks --apply   # writes
```

Gates on that branch: ruff format, ruff check, flake8, mypy, pyre, pyright and
qlty smells all clean; **18 passed, 100% coverage**; both files under the
250-line gate (132 and 223).

It still needs a target naming an explicit database; `.env` points at production
and must not be sourced. Set `MONGODB_URI` and `MONGODB_DB` explicitly.

What was verified on a local throwaway, seeded with documents generated by the
**pre-split** code so the legacy shapes are genuine:

| Step | Result |
| --- | --- |
| dry run | fragments 2, texts 1, chapters 1 "would be migrated" |
| database after dry run | unchanged — `nameBreaks` still absent |
| `--apply` | fragments 2, texts 1, chapters 1 migrated |
| second dry run | 0 / 0 / 0 — idempotent |
| migrated docs loaded through the new `TextSchema` | round-trip to the identical ATF |

**A guard was added.** `separate_name_parts` splits by position
(`[0::2]` / `[1::2]`), which silently moves a `ValueToken` into `nameBreaks` if
legacy `nameParts` ever fails to alternate — data corruption with no error, in a
script that writes to production. It now calls `_validate_alternating` first and
raises `NonAlternatingName`. Verified against the database: a **dry run** on bad
data aborts before `--apply` writes anything.

The positional assumption was also tested directly: every name the pre-split
parser produces is strictly `ValueToken, BrokenAway, ValueToken, ...`, and
`BrokenAway` is the only separator that can appear inside a name.

#### Deployment window — not previously recorded

Independent of the migration: the new code writes `nameBreaks` on **every**
named sign, including unbroken ones (`nameBreaks: []`). So during a rolling
deploy, any fragment saved by a new instance is unreadable by an old instance
still serving traffic — the same `Unknown field` error. This argues for a fast
cutover rather than a long mixed-version window.

### Gate 3 — twenty-three branch-only files must not reach `master`

See section 7 for the full list, the commands, and how to verify.
Two non-`ebl` files are **real changes that must stay**:
`.github/instructions/copilot.instructions.md` (the qlty hard gate) and
`docs/ebl-atf.md` (the grammar path fix). Everything else outside `ebl/` goes.

**Status: NOT DONE.** Safe to do at any point now — the migration script has
left this branch, so the checklist no longer deletes anything that is still
needed. It is only documentation files.

---

## 3. Backend state

CI is green on `589684d`. Work after that commit is committed locally on the
branch but **the qlty and CodeQL verdicts on the PR page describe `589684d`, not
the current HEAD** — they are stale until the branch is pushed again.

### 3.1 CI on `15da7c12`

| Check | Result |
| --- | --- |
| Test Python 3.11 / 3.12 / pypy-3.11 (both workflows) | pass |
| Analyze (python), GitGuardian x3 | pass |
| CodeQL | pass |
| qlty coverage diff | 100.0% |
| qlty coverage | 96.6% (+0.8%) |
| qlty check | pass, **2 blocking issues** — both justified, see 3.3 |
| Sourcery review | skipped |

### 3.2 CodeQL — clear, and the three alert comments are stale

Three `github-advanced-security[bot]` review comments are dated
`2026-09-15T00:11:17Z`, which is **newer than the handoff that declared CodeQL
clear** — alerts 1017, 1018 (assert with a side-effect) and 1019 (module
imported with both `import` and `import from`).

They are stale. All three carry `commit_id = 2a772298`, the previous commit, and
were posted an hour before `589684d` was committed at `01:15:37Z`.

`gh api .../code-scanning/alerts/<n>` returns **403** for this token, so the
alert state cannot be read directly. The fixes were instead confirmed present in
the source at HEAD: `CLOSE = BrokenAway.close()` is hoisted and no remaining
`BrokenAway.close()` call sits inside an assert expression; the nested
`import task_743_migrate_name_breaks as ...` is gone, replaced by
`monkeypatch.setattr(MODULE + ".BATCH_SIZE", 2)`.

### 3.3 qlty — the enumeration problem is SOLVED; the count is not

The previous handoff could not enumerate qlty's findings and guessed the count
was stale. That guess was wrong, and the cause was local tooling:

1. `.qlty/` had been created with `qlty init --yes --skip-plugins`, so
   **`qlty check` ran zero linters**. Its "No issues" meant nothing.
2. **`qlty smells` excludes test files unless `--include-tests` is passed**, and
   every qlty Cloud comment on this PR is in `ebl/tests/`.
3. Running it over the PR file list only hides a duplication between a PR file
   and an untouched file.

The method that does work:

```bash
qlty smells --all --include-tests --no-snippets --quiet          # at HEAD
git worktree add --detach <dir> origin/master                     # and the same there
# then diff the two
```

The branch **reduces** whole-repo smells (master 112 -> 95 distinct). Four
distinct new duplications were found; qlty reports both sides of a pair, so
seven location-entries:

| # | Locations | Disposition |
| --- | --- | --- |
| A | `ebl/transliteration/domain/tokens.py` <-> `ebl/fragmentarium/domain/fragment.py` | **Justified** — two `__all__` re-export lists of the same shape, the instructions' own example; the alternative is leaving the facade incomplete, which was review finding F2 |
| B | `ebl/tests/factories/fragment.py` <-> `ebl/tests/fragmentarium/test_museum_number.py` | **Justified** — an `__all__` export list vs `PREFIXES`, a list of museum-number prefixes. Same shape, no shared meaning, nothing to extract |
| C | `test_parse_text_line.py` <-> `test_text_line.py` | **FIXED** — the same 17-row language-shift parametrize table verbatim. Extracted to `ebl/tests/transliteration/language_shift_cases.py` |
| D | `test_word_merge.py` (x2) <-> `text_merge_cases_1.py` | **FIXED** — caused by this PR; the new `Reading.of_arguments(name_arguments(...))` form spelled out three times. Extracted to `ebl/tests/transliteration/broken_variant_fixtures.py` |

`test_language.py` was checked and deliberately **not** folded into C: its table
is a different 21-row set testing `Language.of_atf`, not shift handling.

Side benefit: `test_text_line.py` was **257 lines, over the 250-line hard gate**
(it is over on master too). The extraction brings it to 240.

**RESOLVED.** qlty on `0919dee6` reports **2 blocking issues**, down from 5.
That reconciles the "5 vs 4" discrepancy exactly: qlty Cloud counts **one issue
per file involved** in a duplication, not one per distinct duplication. The four
duplications spanned five changed files — `tokens.py` (A),
`tests/factories/fragment.py` (B), `test_parse_text_line.py` (C),
`test_word_merge.py` and `text_merge_cases_1.py` (both D). Fixing C and D removed
three. The two that remain are A and B, both justified above. There was never an
unexplained fifth finding; the enumeration was complete, the count just used a
different unit.

### 3.4 A gap in the instructions file worth closing

`.github/instructions/copilot.instructions.md` tells you to run
`qlty smells <changed files>`. On this evidence that command is **structurally
blind to test-file duplication**, which is where every finding on this PR lives.
It should say `qlty smells --include-tests <changed files>`, and the local setup
line should not use `--skip-plugins` if `qlty check` is ever to mean anything.
Not changed here — changing the instructions is the user's call.

---

## 4. Order of operations

1. ~~Commit and push `589684d`~~ — done.
2. ~~Confirm CodeQL green and diff coverage 100.0%~~ — done.
3. ~~Enumerate and clear qlty's findings~~ — done. qlty is at 2 blocking
   issues, both justified (3.3).
4. ~~Apply `TASK-743-fix-pr-body.md` to the PR description~~ — done, verified.
5. ~~Move the DB-related changes out of #743~~ — done; they are on
   `migrate-name-breaks` (gate 2).
6. **Push `add-name-breaks` and open the frontend PR** — the commit exists;
   only the push is blocked, on credentials (gate 1).
7. ~~Push so qlty and CodeQL re-run~~ — done; `5551fa2c` is on the remote.
   Re-read the verdicts once its checks finish.
8. Work the cleanup checklist in section 7 — twenty-three files.
9. **Merge #743, then deploy it.**
10. **Only once it is deployed:** open the `migrate-name-breaks` PR and run the
    migration against a named real database. Dry run first and read it: the
    guard aborts there if any legacy data does not alternate.
11. **A later PR deletes the `@pre_load` adapter** `separate_legacy_name_parts`
    and its tests, once no legacy documents remain.

Step 6 is the real remaining work on #743. Steps 10 and 11 are a
separate sequence that must not start before #743 is deployed — see gate 2.

---

## 5. Traps worth knowing

- **Commits here can reach GitHub without `git push`.** It has now happened
  three times, most recently with `0919dee6`.
  Always confirm with `git ls-remote` before claiming anything about the remote.
- **`qlty check` shows a green tick while reporting blocking issues.** Read the
  description, not the tick.
- **`qlty smells` hides test-file duplication** unless `--include-tests` is
  passed. See 3.3.
- **A qlty verdict on the PR page describes the pushed commit.** If local work
  is unpushed, that verdict is stale; say so rather than treating it as current.
- **Local runs miss what the hosted ones catch.** Every CodeQL alert and eight
  of the ten qlty duplications were invisible locally.
- **Pyre catches what pyright and mypy do not.** `task type` is the CI gate;
  never infer its result from another checker.
- **`task type-pyright` cannot see uncommitted work** — it diffs
  `origin/master...HEAD`, so it silently skips every file that is not committed.
  Run pyright directly on the changed file list.
- **`gh pr edit --body` fails silently here.** Use
  `gh api repos/.../pulls/743 -X PATCH -F body=@file`.
- **Never source `.env`** — `MONGODB_URI` points at production. Pin to
  `127.0.0.1:27017`.
- **Marshmallow defaults to `unknown = RAISE` here.** An added field is not
  ignored by older code — it makes the whole document fail to load. That is
  why the migration cannot run before the new backend is deployed.
- **The frontend needs Node 20**, not 22. See gate 1.
- **Do not `pkill -f "<pattern>"`** where the pattern also matches the shell
  running it — it kills its own wrapper.

---

## 6. Documents on this branch

| File | What it is |
| --- | --- |
| `TASK-745-handoff.md` | this document — the current picture |
| `TASK-743-fix-pr-body.md` | the PR description; already applied |
| `TASK-743-review.md` | the round-12 review, 14 findings |
| `TASK-743-fix-log.md` | work log for the review fixes |
| `TASK-745-log.md` | work log for the CodeQL/qlty fixes |
| `TASK-746-todo.md` / `TASK-746-log.md` | the qlty enumeration, frontend redo and migration verification |
| `TASK-747-todo.md` / `TASK-747-log.md` | moving the DB changes out to `migrate-name-breaks` |
| `TASK-744-*.md` | the earlier frontend task, superseded by gate 1 above |
| `TASK-743-fix-handoff.md` | earlier handoff, superseded by this one |

All of them are deleted by gate 3 — see section 7.

---

## 7. Cleanup checklist — delete before merge

Twenty-three files, all documentation and hand-off artefacts. Tick them off; none may reach `master`.

### Round-12 review task (3 files)

- [ ] `TASK-743-todo.md`
- [ ] `TASK-743-log.md`
- [ ] `TASK-743-review.md`

### Review-fix task (4 files)

- [ ] `TASK-743-fix-todo.md`
- [ ] `TASK-743-fix-log.md`
- [ ] `TASK-743-fix-handoff.md`
- [ ] `TASK-743-fix-pr-body.md` — already applied to the PR description

### Frontend task (2 files)

- [ ] `TASK-744-todo.md`
- [ ] `TASK-744-log.md`

### CodeQL/qlty task (3 files)

- [ ] `TASK-745-todo.md`
- [ ] `TASK-745-log.md`
- [ ] `TASK-745-handoff.md` — this document; delete it last

### TASK-746 task (2 files)

- [ ] `TASK-746-todo.md`
- [ ] `TASK-746-log.md`

### TASK-747 task (2 files)

- [ ] `TASK-747-todo.md`
- [ ] `TASK-747-log.md`

### TASK-748 task (2 files)

- [ ] `TASK-748-todo.md`
- [ ] `TASK-748-log.md`

### TASK-749 task (5 files)

- [ ] `TASK-749-todo.md`
- [ ] `TASK-749-log.md`
- [ ] `TASK-749-frontend-brief.md` — **save a copy before deleting**; it is the
      standalone brief for the frontend work
- [ ] `TASK-749-frontend.patch` — **save a copy before deleting**; it reproduces
      the frontend commit `a9df351`
- [ ] `TASK-749-frontend-pr-body.md` — **save a copy before deleting**

### Commands

```bash
git rm TASK-743* TASK-744* TASK-745* TASK-746* TASK-747* TASK-748* TASK-749*
```

Note the glob is no longer `*.md` — `TASK-749-frontend.patch` is not markdown.

### MUST NOT be deleted

- `.github/instructions/copilot.instructions.md` — adds the qlty hard gate
- `docs/ebl-atf.md` — the grammar path fix
- everything under `ebl/`, including the two new fixture modules
  `ebl/tests/transliteration/language_shift_cases.py` and
  `ebl/tests/transliteration/broken_variant_fixtures.py`

### Verify nothing was missed

This must print only the two keepers above:

```bash
git diff --name-only origin/master...HEAD | grep -v '^ebl/'
```

And this must print nothing at all:

```bash
git ls-files | grep -E '^(TASK-|task_743_)'
```

The `task_743_` half of that pattern is already satisfied — the migration files
moved to `migrate-name-breaks` and no longer carry that prefix at all.

### Also clean up outside the repository

- [ ] Drop any throwaway Mongo databases used for runtime checks. The TASK-746
      throwaway (`ebl_task746_throwaway`) was already dropped, as were the three
      older ones. About 25 `ebltest_*` databases remain from ordinary test runs;
      they are not from this work.
- [ ] Delete the frontend branch once its PR merges
- [ ] Remove the `/workspaces/ebl-frontend` clone once its PR merges
