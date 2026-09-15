<!-- markdownlint-disable MD013 -->

# TASK-746 — Work log

## 2026-09-15

### Start

- Read `.github/instructions/copilot.instructions.md` in full at session start.
- Read `TASK-745-handoff.md`.
- Created `TASK-746-todo.md` and this log before doing any work, per the task
  tracking hard gate: continuing earlier work does not carry TASK-745's files
  forward.
- Task scope: handoff section 5 steps 3-8. Steps 3 (qlty Cloud's 5 issues),
  4 (redo the lost frontend change) and 5 (run the migration) are the real work.

### Entries

#### Step 0 — orientation (done)

- Branch `fix-type-checker-blind-spots`, HEAD `589684d0`; `git ls-remote`
  confirms the remote is at the same commit. Working tree holds only the three
  uncommitted `TASK-745-*.md` edits plus this task's two new files.
- `gh pr checks 743`: all CI green. `qlty check` status still says
  **"5 blocking issues"** (green tick, as the handoff warns).

#### Step 3a — three CodeQL review comments dated today (2026-09-15T00:11:17Z)

Found three `github-advanced-security[bot]` review comments newer than the
handoff, which claims CodeQL is clear. Investigated rather than assume either
way:

- Alerts 1017, 1018 (`ebl/tests/transliteration/test_named_sign_name.py`,
  "assert statement has a side-effect") and 1019
  (`task_743_migrate_name_breaks_test.py`, "module imported with `import` and
  `import from`").
- `gh api .../code-scanning/alerts/<n>` returns **403** for this token, as the
  handoff records, so the alert state could not be read directly.
- Resolved it from the comment metadata instead: all three carry
  `commit_id = 2a772298`, the **previous** commit, and were posted at
  `00:11:17Z` while `589684d0` was committed at `01:15:37Z` — they predate the
  fix by an hour. They are stale re-postings, not new alerts.
- Verified the fixes are actually present at HEAD rather than trusting the tick:
  `CLOSE = BrokenAway.close()` is hoisted to line 20 and the three remaining
  `BrokenAway.close()` calls (65, 72, 85) are not inside assert expressions;
  the nested `import task_743_migrate_name_breaks as ...` is gone, replaced by
  `monkeypatch.setattr(MODULE + ".BATCH_SIZE", 2)`.
- Conclusion: CodeQL is clear on HEAD. No action needed.

#### Step 3b — why local qlty disagreed with Cloud

Root cause of the handoff's "could not be enumerated": `.qlty/` had been created
with `qlty init --yes --skip-plugins`, so **no plugins were installed at all**.
`qlty check --no-fix` reporting "No issues" was therefore meaningless — it ran
zero linters. Re-initialised with plugin detection (`.qlty/` is git-ignored;
nothing tracked changed; old config backed up to the scratchpad first).

- The auto-detected plugin set (bandit, mypy, ruff, radarlint-python,
  osv-scanner, shellcheck, trufflehog, ...) yields **744 issues** against
  `--upstream origin/master` — far broader than Cloud's 5, so local
  auto-detection does not reproduce Cloud's project configuration either.
- `https://qlty.sh/.../pull/743/issues` requires login; not fetchable.
- qlty publishes only a commit **status**, not a check run, so there are no
  GitHub annotations to enumerate from.
- qlty's newest PR comments are still 2026-09-02 (confirms the handoff).

#### Step 3c — enumerating the qlty issues properly

Found the real blind spot: **`qlty smells` excludes test files unless
`--include-tests` is passed**, and every qlty Cloud comment on this PR is in
`ebl/tests/`. The handoff's "2 findings" run was missing all of them. It also
ran over the PR file list only, so a duplication between a PR file and an
untouched file was invisible.

Method that does reproduce a usable list:

```bash
qlty smells --all --include-tests --no-snippets --quiet   # at HEAD

# and the same in a detached worktree at origin/master, then diff
```

HEAD: 99 distinct smells. master (`fea46b95`): 112. The branch **reduces** the
whole-repo count; seven location-entries are new, which collapse to **four
distinct duplications** (qlty reports both sides of a pair):

| # | Locations | Size | PR touches |
| --- | --- | --- | --- |
| A | `ebl/transliteration/domain/tokens.py` <-> `ebl/fragmentarium/domain/fragment.py` | 17 lines, mass 64 | one side |
| B | `ebl/tests/factories/fragment.py` <-> `ebl/tests/fragmentarium/test_museum_number.py` | 22 lines, mass 84 | one side |
| C | `ebl/tests/transliteration/test_parse_text_line.py` <-> `ebl/tests/transliteration/test_text_line.py` | 22 lines, mass 147 | one side |
| D | `ebl/tests/transliteration/test_word_merge.py` (x2) <-> `ebl/tests/transliteration/text_merge_cases_1.py` | 24 lines in 3 locations, mass 75 | both sides |

A and B match qlty Cloud's surviving comments (`tokens.py:31` and
`ebl/tests/factories/fragment.py:66`, both 2026-09-02), which corroborates the
list. Cloud's count of 5 vs these 4 cannot be reconciled exactly without the
login-only page — recorded as a known gap, **not** waved through as stale.

#### Step 3d — dispositions

**A — `ebl/transliteration/domain/tokens.py` <-> `ebl/fragmentarium/domain/fragment.py`
(17 lines, mass 64): JUSTIFIED, not a defect.** Two `__all__` re-export lists
that happen to have the same shape. This is the exact case the instructions name
as legitimate, and the alternative is leaving the facade incomplete, which was
review finding F2. Unchanged from the handoff's disposition.

**B — `ebl/tests/factories/fragment.py` <-> `ebl/tests/fragmentarium/test_museum_number.py`
(22 lines, mass 84): JUSTIFIED, not a defect.** Inspected both sides: one is the
`__all__` export list of the fragment factories module, the other is `PREFIXES`,
a list of museum-number prefixes (`"K"`, `"Sm"`, `"DT"`, ...). Identical shape —
22 short string literals — and no shared meaning whatever. There is nothing to
extract: the only thing they have in common is being a sorted list of strings.

**C — `test_parse_text_line.py` <-> `test_text_line.py` (22 lines, mass 147):
FIXED.** A real duplication: the same 17-row `code,language` language-shift
parametrize table verbatim in both files. Pre-existing (master has it in three
places) but it only became a reported finding on this branch, because the PR
shrank `test_parse_text_line.py` from 1265+ lines to 177 and changed what the
duplication detector pairs. Not waved through as "already there" — the
instructions are explicit that a pre-existing finding on a touched file must be
fixed.

- Extracted to `ebl/tests/transliteration/language_shift_cases.py` as
  `LANGUAGE_SHIFT_CASES`, imported by both.
- `test_language.py` was checked and deliberately **not** folded in: its table
  is a different 21-row set (adds `%e`, `%n`, `%akkgrc`, `%suxgrc`, `%grc`; no
  `%foo`) testing `Language.of_atf` rather than shift handling. Merging them
  would have coupled two different test intents.
- Side benefit: `test_text_line.py` was **257 lines, over the 250-line hard
  gate** (it is over on master too). The extraction brings it back under.

**D — `test_word_merge.py` (x2) <-> `text_merge_cases_1.py` (24 lines in 3
locations, mass 75): FIXED.** Caused directly by this PR. The `nameParts` split
replaced `Reading.of([ValueToken.of("k[ur")])` with the much more verbose
`Reading.of_arguments(name_arguments([...]))`, and the same broken variant was
then spelled out three times across the two files.

- Extracted to `ebl/tests/transliteration/broken_variant_fixtures.py`:
  `broken_reading(head, tail)` plus `VARIANT_WITH_UNPARSED_BREAK` and
  `VARIANT_WITH_PARSED_BREAK`.
- Verified both constants render the same ATF (`k[ur/r[a`) before substituting,
  so the merge cases still assert what they did.
- Removed the imports that became unused (`name_arguments`, `ValueToken` in
  both; `Variant` in `text_merge_cases_1.py`), after counting remaining uses
  rather than guessing.

Result: `qlty smells --all --include-tests` drops from 99 distinct smells to 95;
the only entries still new against master are A and B, both justified above.

Affected tests: `test_word_merge.py`, `test_text_merge.py`, `test_text_line.py`,
`test_parse_text_line.py`, `test_language.py` — 178 passed.

### Step 3e — gates after the qlty fixes (backend)

All run against the working tree, which is **uncommitted**:

| Gate | Result |
| --- | --- |
| `task format` | 886 files already formatted, nothing left unstaged |
| `task lint` (ruff) | All checks passed |
| `task type` (pyre) | No type errors found |
| pyright 1.1.411, 162 changed files | 0 errors, 0 warnings |
| `poetry run flake8 --max-line-length=120` | clean |
| `poetry run mypy --ignore-missing-imports` | no issues in 6 files |
| `task test` | **4544 passed, 2 skipped, 1 xfailed** |
| `qlty smells --include-tests` on changed files | no findings |
| `task lint-md` | 0 errors |
| 250-line gate | all changed files under; `test_text_line.py` 257 -> 240 |

`task type-pyright` was **not** used: it diffs `origin/master...HEAD`, so it sees
only committed files and would have skipped every file changed here. Ran pyright
directly on the union of the committed PR diff and the working-tree changes.

Coverage: `.coveragerc` has `omit = ebl/tests/*`, and no production file changed,
so diff coverage is untouched (a targeted `--cov` run collects nothing for these
modules by design — parametrize data is imported at collection time).

### Step 4 — redoing the lost frontend change (gate 1)

Confirmed the work really is gone: `git ls-remote` on `ebl-frontend` shows no
`add-name-breaks` branch.

Cloned to **`/workspaces/ebl-frontend`**, a persistent sibling of the api repo,
deliberately *not* the scratchpad — a cleared scratchpad is what destroyed the
previous attempt.

**Error and recovery.** The first `yarn install` reported success to the task
runner but had actually failed: the command ended in a `tail`, so the exit code
reported was `tail`'s, not yarn's. The log said
`The engine "node" is incompatible ... Expected "^20.0.0". Got "22.15.0"` and
`node_modules` was empty. The repo has `.nvmrc` = `20.0.0`; Node 20.19.1 is
present at `/usr/local/share/nvm/versions/node/v20.19.1`. Re-ran with that on
`PATH` — installed cleanly in 203s. Lesson recorded: read the log, not the
wrapper's exit code.

Changes, exactly the three production sites the handoff identified:

- `src/transliteration/domain/token.ts` — added
  `readonly nameBreaks?: readonly Enclosure[] | null` to `NamedSign`, and a new
  exported `nameTokens(namedSign)` that returns `nameParts` unchanged when
  `nameBreaks` is absent or null, and otherwise interleaves
  `parts[i], breaks[i]`.
- `src/transliteration/domain/token.ts` — `extractEnclosureTypes` now maps over
  `nameTokens(namedSign)`.
- `src/transliteration/domain/accents.ts` — `addAccents` now reduces over
  `nameTokens(namedSign)`.

`nameParts` deliberately keeps its union type; narrowing it to `ValueToken[]`
would break the legacy fallback, as the handoff warns.

The interleave was checked against the backend rather than taken from the
handoff: `NamedSign._interleaved` in `ebl/transliteration/domain/sign_token_base.py`
uses `zip_longest(name_parts, name_breaks)` yielding the part then the break when
present, and `_validate_name_breaks` enforces `len(breaks) <= len(parts)`, so the
two agree including the trailing-break case.

Tests — the five cases the handoff specifies, in `token.test.ts`: split input,
no breaks, trailing break, legacy interleaved payload, explicit `null`.

Added two more in `accents.test.ts`, because `nameTokens` alone is a unit test of
a helper: `DisplayToken.tsx:174` renders via `addAccents`, so these assert
through the function the UI actually calls, with a realistic backend-shaped
payload, that a split name renders `k ] u` and a legacy one still renders
`k ] u`.

| Frontend gate | Result |
| --- | --- |
| `tsc --noEmit` | 0 errors |
| `yarn lint` (eslint + stylelint) | clean |
| token + accents suites | 13 passed |
| full `yarn test` | see below |

**Error and recovery (second).** The first full frontend run was started before
`accents.test.ts` was added, so it was testing a stale tree. Stopped it and
restarted — but the restart command began with `pkill -f "craco test"`, and that
pattern matched the wrapper shell's **own** command line, killing the run it was
about to start (exit 144, empty log). Re-ran without the `pkill`. Noted because
the re-verify gate means a run against a stale tree is worth nothing; both runs
had to be discarded, and `tsc` and `yarn lint` were re-run against the current
tree too (both clean).

### Step 5 — migration (gate 2): pre-flight check, NOT yet run

The migration has still never been run against any database. It reads
`MONGODB_URI` and `MONGODB_DB` from the environment and `.env` points at
production, so it needs an explicit target from the user. **Blocked, asked.**

While blocked, audited the part of it that worries me most.
`separate_name_parts` splits **by position**:

```python
return list(name_parts[0::2]), list(name_parts[1::2])
```

That is only correct if legacy `nameParts` strictly alternates
part, break, part. If two `ValueToken`s could ever be adjacent, the migration
would silently move a `ValueToken` into `nameBreaks` — data corruption, in a
script that writes to a production database, with no error raised.

Tested it rather than assumed. Parsed a spread of ATF through the **pre-split**
parser in the `origin/master` worktree and dumped the token kinds of every
`name_parts`:

- `k[ur]`, `k[u]r`, `ku[r]-ra`, `KU[R]`, `1[2]`, `k[u]r[a]` -> all strictly
  alternating `ValueToken, BrokenAway, ValueToken, ...`
- no sample produced two adjacent `ValueToken`s
- the only token kind that ever appears inside `name_parts` is `ValueToken`,
  with `BrokenAway` as the only separator; `(...)`, `*...*`, `<...>`, `<<...>>`
  and `⸢...⸣` inside a name are all rejected by the parser

So the positional split is sound **for parser-produced data**, which de-risks
gate 2 considerably.

Residual risk, stated rather than waved away: this probes what the parser
produces today, not what is actually stored. Documents written by older parser
versions could in principle have a different shape. The dry run reports counts
only — it does not verify that each legacy `nameParts` alternates. Recommend
either a read-only shape audit on the target database first, or a guard in
`separate_name_parts` that raises on a non-alternating array instead of
mis-splitting it. Offered to the user; not done unilaterally, since the script
is the thing under discussion.

### Step 5 — migration guard, and a full throwaway run

User chose: local throwaway first, and add the guard.

**Guard.** Added to `task_743_migrate_name_breaks.py`: `NonAlternatingName`,
`_expected_type` and `_validate_alternating`, called from
`separate_name_parts` before the positional split. A legacy `nameParts` whose
positions do not alternate `ValueToken` / `BrokenAway` now raises instead of
being mis-split. Four tests added (the module goes from 14 tests to 18); it is at **100% coverage, 18 passed**.

**Throwaway run.** A local `mongod` was already listening on 127.0.0.1:27017.
`.env` was never sourced; `MONGODB_URI` and `MONGODB_DB` were set explicitly on
the command line.

The seed data was not hand-written. It was produced by the **pre-split** code in
the `origin/master` worktree — `parse_atf_lark` plus `TextSchema().dump()` on
`1. k[ur]` / `2. ku` / `3. k[u]r[a]` / `4. KU[R]-ra` — so the legacy shapes are
genuinely what the old code wrote (confirmed: no `nameBreaks` anywhere).
Seeded into `ebl_task746_throwaway` across `fragments` (3, one with no names),
`texts` (1) and `chapters` (1).

| Step | Result |
| --- | --- |
| dry run | fragments 2, texts 1, chapters 1 "would be migrated" |
| database after dry run | unchanged — `nameBreaks` still absent |
| `--apply` | fragments 2, texts 1, chapters 1 migrated |
| second dry run | 0 / 0 / 0 — idempotent |

Then the check that actually matters, which the handoff never did: the migrated
documents were loaded back through **HEAD's** `TextSchema` and re-serialised.

```text
separated arrays (parts, breaks)
    ['k', 'ur']            ['[']
    ['ku']                 []
    ['k', 'u', 'r', 'a']   ['[', ']', '[']
    ['KU', 'R']            ['[']
    ['ra']                 []

ATF round-tripped through the new schema
1. k[ur]
2. ku
3. k[u]r[a]
4. KU[R]-ra
```

Identical to the input ATF. The migration's output is loadable by the shipping
code and loses nothing.

**Guard verified against the database, not just in unit tests.** Inserted a
deliberately non-alternating document and re-ran the **dry run**: it aborted with

```text
NonAlternatingName: Expected a BrokenAway at position 1 of nameParts, found
{'value': 'u', 'type': 'ValueToken'}. Splitting by position would move it into
the wrong array; refusing to migrate.
```

This is the useful property for gate 2: a dry run against the real database now
surfaces any non-alternating legacy data **before** `--apply` writes anything.

`ebl_task746_throwaway` was dropped afterwards. The three stale databases the
handoff lists (`ebl_task743_review_throwaway`, `ebl_task743fix_throwaway`,
`ebl_migrate_probe`) were already gone. Note: ~25 `ebltest_*` databases remain
from test runs — not created by this task, left alone.

Gates re-run on the two changed migration files after the edit: ruff format,
ruff check, flake8, mypy, pyright 1.1.411, `qlty smells --include-tests` — all
clean; `task lint` and `task type` (pyre, `source_directories: ["."]`, so it does
cover the root-level scripts) clean across the tree.

### Step 6 — PR description applied

User asked for it now. Fetched the existing body first (327 lines, no gates
callout) and saved it to the scratchpad before overwriting. Applied with

```bash
gh api repos/.../pulls/743 -X PATCH -F body=@TASK-743-fix-pr-body.md
```

`gh pr edit --body` was avoided — it fails silently in this repo. Re-fetched the
body afterwards and diffed it against the file: identical apart from one
trailing newline the API adds. **Verified applied.**

### Not done, deliberately

- **Step 7, the cleanup checklist.** Must not run yet: it deletes the migration
  script before it has been run against the real database, and the task files
  still in use. It is a pre-merge step.
- **The frontend PR.** The change is complete and green in
  `/workspaces/ebl-frontend` but **uncommitted**, with no branch and no PR.
  Opening one needs an explicit request.
- **The real migration.** Only the local throwaway has been migrated. No real
  database has been touched.
- **qlty Cloud's exact count of 5.** Still unreconciled; needs the login-only
  page.

### Step 7 — documentation updated, commit requested

User asked for the handoff and documentation to be brought up to date and the
work committed.

`TASK-745-handoff.md` was rewritten end to end rather than patched, because most
of it was out of date: gate 1 now records the frontend work as written and green
but uncommitted, gate 2 records the guard and the throwaway verification, gate 3
grows from fourteen files to sixteen, and the qlty section is replaced with the
method that actually enumerates findings plus the one thing still unresolved.
Three new traps were added (qlty's `--include-tests` blindness, the frontend's
Node 20 requirement, and the self-matching `pkill`), and the note that
`task type-pyright` silently skips uncommitted work.

Section 3.4 records a gap in `.github/instructions/copilot.instructions.md`
itself — it prescribes `qlty smells <changed files>`, which cannot see test-file
duplication. Flagged, not changed; editing the instructions is the user's call.

### Remaining findings, carried forward

1. **qlty Cloud says 5 blocking issues; the reproduction finds 4.** Needs the
   login-only issues page. Must not be assumed stale — that assumption is what
   hid the problem for several rounds.
2. **The frontend change is uncommitted with no branch and no PR** (gate 1).
3. **The migration has not been run against any real database** (gate 2).
4. **The branch needs pushing** so qlty and CodeQL re-run on the current HEAD;
   their PR verdicts describe `589684d` only.
5. **The cleanup checklist has not been run** (gate 3) and must not be until the
   migration has run.
