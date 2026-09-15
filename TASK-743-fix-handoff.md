# TASK-743-fix Handoff — PR #743 after the round-12 review

<!-- markdownlint-disable MD013 -->

Working document. Not part of the PR — delete before merge, along with the
other `TASK-743*.md` files.

## Where things stand

All fourteen findings from `TASK-743-review.md` are addressed.

**Committed as `2b3b0668`** on `fix-type-checker-blind-spots` — code only.
The `TASK-743*.md` documents are deliberately **not** committed.

**That commit is on GitHub.** No `git push` was run, but `git ls-remote` shows
the remote branch at `2b3b0668`, so CI, CodeQL and qlty Cloud all analysed it.
They found things the local runs did not, and those are fixed in the follow-up
commit:

- **CodeQL failed** with six alerts — three `...` Protocol bodies in
  `provenance_lookup.py`, two asserts with side effects, and one unused import.
  All fixed.
- **qlty Cloud reported 10 blocking issues** where the local run had reported
  the same duplications as non-blocking. Eight are now genuinely deduplicated;
  two are justified (two unrelated `__all__` lists, and the pre-existing
  12-parameter `Word.of`).

The lesson worth carrying: local `qlty smells` and a clean local tree are not
substitutes for the hosted CodeQL and qlty runs.

| Gate | Result |
| --- | --- |
| `task format` | clean |
| `task lint` (ruff) | passed |
| `task type` (**pyre** — the CI gate) | No type errors found |
| pyright over the changed set | 0 errors |
| `mypy --ignore-missing-imports` | 0 issues, 158 files |
| `flake8 --max-line-length=120` | 0 |
| `task test` | 4543 passed, 2 skipped, 1 xfailed |
| Coverage on changed source modules | 100% on all 69 |
| 250-line limit | every changed file within it |
| `task lint-md` | 0 errors |
| `qlty smells` | 6 findings, each justified in the log; none blocking |
| Running service | all affected routes re-exercised after the rewrite |

Runtime verification against a booted service on a throwaway database:
`GET /signs/transliteration/[k]ur` and `/kur` both resolve to sign 74266,
proving the split round-trips over HTTP; `$$$` returns 422; `?listAll=true`
returns `["KUR","RA"]` instead of a 500; `/markup` and `/cached-markup` return
422 on unparsable input instead of a 500.

## The one thing a reviewer must know

**`nameParts` is a breaking wire-format change, and it is also the stored Mongo
shape.**

```text
before  "nameParts":  [ValueToken, BrokenAway, ValueToken]

after   "nameParts":  [ValueToken, ValueToken]
        "nameBreaks": [BrokenAway]
```

Names are strictly alternating in the grammar, so the split is lossless by
position — N parts, at most N breaks, no index and no discriminator.

Two consequences:

1. **The frontend must be updated** to read `nameBreaks` and interleave.
   Element shapes are otherwise unchanged, so a client that ignores
   `nameBreaks` still renders names correctly — it just loses the brackets
   *inside* a name. Brackets *around* a name were never in `nameParts`.
2. **Existing documents keep working without a migration.** A `@pre_load`
   adapter splits a legacy interleaved `nameParts` when `nameBreaks` is absent.
   Verified: a document rewritten into the old shape loads to an equal `Text`
   and round-trips the same ATF.

## Blocking gates for this PR

All three are written into the PR description as a warning callout. **None is
optional and the PR must not be approved while any of them is open.**

### Gate 1 — the frontend must read `nameBreaks`

`nameParts` no longer carries the brackets that fall *inside* a name; they are
in a new sibling array. A client that ignores `nameBreaks` still renders names
but silently drops those brackets, which produces a **wrong reading**, not a
cosmetic loss. Brackets *around* a name were never in `nameParts` and are
unaffected.

```text
before  "nameParts":  [ValueToken("k"), BrokenAway("]"), ValueToken("u")]
after   "nameParts":  [ValueToken("k"), ValueToken("u")]
        "nameBreaks": [BrokenAway("]")]
interleave: parts[0], breaks[0], parts[1], ...  ->  k ] u
```

Blocked until the matching frontend change is merged or queued.

### Gate 2 — the data migration must be run

`nameParts` is also the stored shape in every fragment and chapter document.
The `@pre_load` adapter means the deploy will not break, but until the
migration runs the database holds two shapes at once and every read pays for
the conversion.

```bash
poetry run python task_743_migrate_name_breaks.py           # dry run
poetry run python task_743_migrate_name_breaks.py --apply   # writes
```

Blocked until it has been run against production, or an owner has explicitly
scheduled it and said so on the PR. It has **not** been run against any
database.

### Gate 3 — the migration script and the task documents must not reach `master`

`task_743_migrate_name_breaks.py` and `task_743_migrate_name_breaks_test.py`
are **branch-only temporary files**, kept at the repository root with a
`task_743_` prefix so they cannot be mistaken for permanent modules. They are a
one-off for this data change and must be deleted before the branch merges:

The task documents are now committed too, so they fall under the same gate:

```bash
git rm task_743_migrate_name_breaks.py task_743_migrate_name_breaks_test.py
git rm TASK-743*.md TASK-744*.md TASK-745*.md
```

A merge that carries any of them into `master` is a defect regardless of what
else is green. All three gates are written into the PR description.

## All fourteen review findings and how each was addressed

| # | Finding | Resolution |
| --- | --- | --- |
| F1 | `NamePart` probed with `isinstance`; `nameParts` was a polymorphic wire array | **Fixed.** Split into `name_parts` / `name_breaks` at domain, Mongo and wire. Wrapper and probe deleted. See both blocking gates |
| F2 | `tokens.py` `__all__` dropped the nine classes it defines | **Fixed.** All seven facades completed; audit also found gaps in `chapter_schemas.py` and `tests/factories/fragment.py`. Pinned by `test_module_facades.py` |
| F3 | Two `# type: ignore[arg-type]` contradicted the PR's own claim | **Fixed.** `ProvenanceLookup` Protocol; both suppressions gone. Exposed a real stub/protocol mismatch |
| F4 | Instruction file changed while the body claimed no config was touched | **Fixed.** Both passages corrected; the rules change is called out |
| F5 | `GET /signs?listAll=true` returned 500 | **Fixed.** Ids and `Sign` objects no longer share a serialization path |
| F6 | `/markup` and `/cached-markup` returned 500 on bad input | **Fixed.** Both map parse failures to `DataError` (422) |
| F7 | Redundant `cast(TextLine, other)` | **Fixed.** Removed |
| F8 | `update_alignment` typed `object`, override unannotated | **Fixed.** `AlignmentMap` moved to a leaf module; both ends typed. Pyre then found a real `Optional[int]` indexing bug |
| F9 | `_StartParser.__getattr__ -> object` hid seven parsers | **Fixed.** Replaced with a typed `options` property; all six assertions still hold |
| F10 | Shared class-body `NullSignsCollectingVisitor` | **Fixed.** `attr.Factory` |
| F11 | Unannotated `make_token` hooks | **Fixed.** The three this PR rewrote are annotated |
| F12 | `Divider.string_flags` duplicated its base | **Fixed.** Deleted |
| F13 | `ChapterVisitor.visit` became a `singledispatchmethod` | Informational; accepted as-is |
| F14 | `lark_parser.py` at exactly 250 lines | Informational; still within the limit |

Two problems found while fixing these, not in the original review, were also
fixed: `sign_search.py` held `str` and `int` in one params mapping (eight
pre-existing pyright errors), and four test modules already over the 250-line
limit were pulled into the diff and had to be split.

## Next steps

1. **Update the PR description.** The corrected body, including both blocking
   gates, is in `TASK-743-fix-pr-body.md`. Apply it with:

   ```bash
   gh api repos/ElectronicBabylonianLiterature/ebl-api/pulls/743 -X PATCH -F body=@TASK-743-fix-pr-body.md
   ```

   `gh pr edit --body` fails silently in this environment; use the API call.
   I have not pushed it — the branch needs pushing first so the body matches
   the code.
2. **Push the branch**, then let CI, qlty Cloud and CodeQL run. The verdicts
   currently on the PR page describe the previous commit and are stale.
3. **Open the frontend issue/PR for `nameBreaks`** — blocking gate 1.
4. **Schedule or run the migration** — blocking gate 2.
5. **Re-review.** The diff grew substantially this round: the `nameParts`
   split, 15 new test-case modules, 2 fixture modules, and a migration script.
6. **Delete the six `TASK-743*.md` files** before merging.

## Decisions taken during this round

| Decision | Rationale |
| --- | --- |
| Full split including the wire | Your call. The data hard gate requires the wire to match the domain |
| Legacy-tolerant load + migration script | Your call. Avoids a forced migrate-then-deploy ordering and keeps rollback simple |
| `len(name_breaks) <= len(name_parts)` rather than exactly `N-1` | `master` accepted a trailing break (`ku]`); rejecting it would regress real data |
| `test_name_part.py` rewritten as `test_named_sign_name.py` | Its subject, the `NamePart` wrapper, is deleted. Every assertion was translated, not dropped — mapping table in the log. Net 10 -> 14 tests |
| Split four already-oversized test modules | My edits pulled them into the diff, so the 250-line gate began applying to them |

## Things worth a second opinion

- The `type` field on `nameParts` / `nameBreaks` elements is now a *validated
  constant* rather than a `OneOfSchema` discriminator. That is what makes a
  misplaced `BrokenAway` a 422 instead of a silent coercion into a `ValueToken`
  carrying `"]"` — `BaseTokenSchema` uses `unknown = EXCLUDE`. Keeping the
  field is redundant with the array it sits in, but it eases the frontend
  migration and costs nothing.
- `test_chapter_merge.py` builds a `Reading` whose name is `ku]`. The parser
  never produces that shape. If it is simply a stale fixture, the invariant
  could tighten to exactly `N-1` and the fixture be corrected — worth checking
  with someone who knows the corpus data.
