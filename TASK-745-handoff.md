<!-- markdownlint-disable MD013 -->
# Handoff — PR #743, everything outstanding before merge

Supersedes `TASK-743-fix-handoff.md`, which covers only the round-12 review.
This is the current, complete picture.

**Branch:** `fix-type-checker-blind-spots` -> `master`
**PR:** [#743](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743)
**HEAD:** `2a77229` — local and remote are in sync
**Written:** 2026-09-15

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

## 2. Blocking gates — none optional

These are in the PR description as a warning callout. **Do not approve or merge
while any is open.**

### Gate 1 — the frontend must read `nameBreaks`

```text
before  "nameParts":  [ValueToken("k"), BrokenAway("]"), ValueToken("u")]
after   "nameParts":  [ValueToken("k"), ValueToken("u")]
        "nameBreaks": [BrokenAway("]")]
interleave: parts[0], breaks[0], parts[1], ...  ->  k ] u
```

A client that ignores `nameBreaks` still renders names but silently drops the
brackets **inside** a name — a wrong reading, not a cosmetic loss. Brackets
*around* a name were never in `nameParts` and are unaffected.

**Status: NOT DONE. The work was written and then lost.** See section 4.

### Gate 2 — the data migration must be run

`nameParts` is also the stored Mongo shape at
`text.lines[].content[].parts[].nameParts` in every fragment and chapter
document. A `@pre_load` adapter keeps old documents loading, so the deploy will
not break — but until the migration runs the database holds two shapes and
every read pays to convert.

```bash
poetry run python task_743_migrate_name_breaks.py           # dry run, reports counts
poetry run python task_743_migrate_name_breaks.py --apply   # writes
```

Dry-run by default, batched, idempotent. **It has never been run against any
database.** It needs a target naming an explicit database — `.env` points at
production and must not be sourced.

### Gate 3 — fourteen branch-only files must not reach `master`

See section 8 for the full list, the commands, and how to verify.
Two non-`ebl` files are **real changes that must stay**:
`.github/instructions/copilot.instructions.md` (the qlty hard gate) and
`docs/ebl-atf.md` (the grammar path fix). Everything else outside `ebl/` goes.

---

## 3. Open issues on the backend

### 3.1 Uncommitted work in the tree

`git status` is dirty. These fixes are written and verified but **not
committed**:

| File | Change |
| --- | --- |
| `ebl/provenance/application/provenance_lookup.py` | `@abstractmethod` on the three Protocol methods |
| `ebl/tests/transliteration/test_named_sign_name.py` | calls hoisted out of assert expressions |
| `task_743_migrate_name_breaks_test.py` | single import style |
| `TASK-743-fix-pr-body.md`, `TASK-743-fix-handoff.md` | gate 3 widened |
| `TASK-745-todo.md`, `TASK-745-log.md` | new, untracked |

### 3.2 CodeQL is failing on `2a77229`

Three alerts, all **fixed in the working tree, not yet pushed**:

- `test_named_sign_name.py` x2 "assert statement has a side-effect" — the cause
  was `BrokenAway.close()` and `ValueToken.of("ku")` being *called* inside the
  assert. An earlier attempt hoisted the indexing and missed this, so the alert
  came back on the second push. Now module constants.
- `task_743_migrate_name_breaks_test.py` "Module imported with 'import' and
  'import from'".

### 3.3 Diff coverage regressed to 99.8%

Caused by fixing CodeQL: replacing the Protocol's `...` bodies with
`raise NotImplementedError` created three lines nothing executes. `@abstractmethod`
fixes both at once because `.coveragerc` already excludes that decorator.
`provenance_lookup.py` is back to 100% locally. **Verify the PR returns to
100.0% after the next push.**

### 3.4 qlty Cloud reports 5 blocking issues — NOT enumerated

Local `qlty smells` shows only 2:

- `tokens.py` and `fragmentarium/domain/fragment.py` hold `__all__` lists with
  the same shape — justified; the instructions give this exact case as
  legitimate.
- `Word.of` has 12 parameters — pre-existing, confirmed present at `HEAD`.

**Three are unaccounted for.** They must be read off
<https://qlty.sh/gh/ElectronicBabylonianLiterature/projects/ebl-api/pull/743/issues>
and each fixed or justified. Do not assume they are the same two.

### 3.5 The full local suite has not completed since the last edits

It was still running at handoff. Last complete run was **4543 passed** with
100% coverage on all changed source modules, but that predates the CodeQL and
qlty fixes. Re-run before trusting it.

---

## 4. The frontend work is LOST and must be redone

Gate 1 was implemented on a branch `add-name-breaks` in a scratchpad clone. The
scratchpad was cleared, nothing was committed or pushed, and
`git ls-remote` confirms no such branch exists on `ebl-frontend`. **The work is
gone.** It was small — this is the full specification to redo it:

Repository `ElectronicBabylonianLiterature/ebl-frontend`, default branch
`master`. `nameParts` appears in 17 files but only **three** are production
code:

| File | Use |
| --- | --- |
| `src/transliteration/domain/token.ts` (~line 116) | the `NamedSign` type: `readonly nameParts: readonly (ValueToken \| Enclosure)[]` |
| `src/transliteration/domain/token.ts` (~line 217) | `extractEnclosureTypes` maps over it |
| `src/transliteration/domain/accents.ts` (~line 117) | `addAccents` reduces over it |

The agreed design — **read both shapes**, so the repos need not deploy in
lock-step:

```ts
export interface NamedSign extends Sign {
  readonly nameParts: readonly (ValueToken | Enclosure)[]
  readonly nameBreaks?: readonly Enclosure[] | null
  // ...
}

export function nameTokens(
  namedSign: NamedSign,
): readonly (ValueToken | Enclosure)[] {
  const breaks = namedSign.nameBreaks
  if (!breaks) {
    return namedSign.nameParts        // legacy: already interleaved
  }
  return namedSign.nameParts.flatMap((part, index) =>
    index < breaks.length ? [part, breaks[index]] : [part],
  )
}
```

Then route both call sites through `nameTokens(namedSign)`. Keep `nameParts`
typed as the union — narrowing it breaks the legacy fallback.

Cover five cases: split input, no breaks, a trailing break, a legacy
interleaved payload, and an explicit `null`.

Frontend gates: `yarn install` (it uses **yarn**, not npm — there is no
`package-lock.json`), then `yarn lint`, `yarn test`. Budget time: the install
is slow.

---

## 5. Order of operations

1. Commit the working tree (3.1) and push.
2. Confirm CodeQL goes green and diff coverage returns to 100.0%.
3. Read qlty Cloud's 5 issues; fix or justify each (3.4).
4. Redo the frontend change, open its PR, cross-link #743 (section 4, gate 1).
5. Run the migration against a named database (gate 2).
6. Apply `TASK-743-fix-pr-body.md` to the PR description.
7. Work the cleanup checklist in section 8 — fourteen files.
8. Merge.

---

## 6. Traps worth knowing

- **Commits here can reach GitHub without `git push`.** It happened twice; I
  twice told the user something was unpushed when it was not. Always confirm
  with `git ls-remote` before claiming anything about the remote.
- **`qlty check` shows a green tick while reporting blocking issues.** Its
  status was `success` at both "10 blocking issues" and "5 blocking issues".
  Read the description, not the tick.
- **Local runs miss what the hosted ones catch.** Every CodeQL alert and eight
  of the ten qlty duplications were invisible locally. Push and read the hosted
  verdicts before declaring gates green.
- **Pyre catches what pyright and mypy do not.** It found five errors when both
  others were clean, including a real `Optional[int]` indexing bug. `task type`
  is the CI gate; never infer its result from another checker.
- **`task type-pyright` cannot run with uncommitted deletions** — it diffs
  against committed `HEAD`. Run pyright directly on the changed file list.
- **`gh pr edit --body` fails silently here.** Use
  `gh api repos/.../pulls/743 -X PATCH -F body=@file`.
- **Never source `.env`** — `MONGODB_URI` points at production. Pin to
  `127.0.0.1:27017`.

---

## 7. Documents on this branch

| File | What it is |
| --- | --- |
| `TASK-745-handoff.md` | this document — the current picture |
| `TASK-743-fix-pr-body.md` | the PR description to apply, including the three gates |
| `TASK-743-review.md` | the round-12 review, 14 findings |
| `TASK-743-fix-log.md` | work log for the review fixes |
| `TASK-745-log.md` | work log for the CodeQL/qlty fixes |
| `TASK-744-*.md` | the frontend task, now superseded by section 4 |
| `TASK-743-fix-handoff.md` | earlier handoff, superseded by this one |

All of them are deleted by gate 3 — see the checklist in section 8.

---

## 8. Cleanup checklist — delete before merge

Fourteen files. Tick them off; none may reach `master`.

### The migration (2 files)

- [ ] `task_743_migrate_name_breaks.py`
- [ ] `task_743_migrate_name_breaks_test.py`

### Round-12 review task (3 files)

- [ ] `TASK-743-todo.md`
- [ ] `TASK-743-log.md`
- [ ] `TASK-743-review.md`

### Review-fix task (4 files)

- [ ] `TASK-743-fix-todo.md`
- [ ] `TASK-743-fix-log.md`
- [ ] `TASK-743-fix-handoff.md`
- [ ] `TASK-743-fix-pr-body.md` — apply it to the PR description **before**
      deleting it; it is the source of the description, including the gates

### Frontend task (2 files)

- [ ] `TASK-744-todo.md`
- [ ] `TASK-744-log.md`

### CodeQL/qlty task (3 files)

- [ ] `TASK-745-todo.md`
- [ ] `TASK-745-log.md`
- [ ] `TASK-745-handoff.md` — this document; delete it last

### Commands

```bash
git rm task_743_migrate_name_breaks.py task_743_migrate_name_breaks_test.py
git rm TASK-743*.md TASK-744*.md TASK-745*.md
```

### MUST NOT be deleted

- `.github/instructions/copilot.instructions.md` — adds the qlty hard gate
- `docs/ebl-atf.md` — the grammar path fix
- everything under `ebl/`

### Verify nothing was missed

This must print only the two keepers above:

```bash
git diff --name-only origin/master...HEAD | grep -v '^ebl/'
```

And this must print nothing at all:

```bash
git ls-files | grep -E '^(TASK-|task_743_)'
```

### Also clean up outside the repository

- [ ] Drop any throwaway Mongo databases used for runtime checks
      (`ebl_task743_review_throwaway`, `ebl_task743fix_throwaway`,
      `ebl_migrate_probe`) — the real migration target is **not** one of these
- [ ] Delete the `add-name-breaks` frontend branch once its PR merges
