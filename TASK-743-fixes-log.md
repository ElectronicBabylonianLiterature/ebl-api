# TASK-743-fixes — Work Log

## Task

Fix the four issues surfaced by the `master` merge on branch
`fix-type-checker-blind-spots` (PR #743). User selected all four and asked
that **nothing be committed** — review first.

Starting point: `4ab29000`, working tree clean, all merge gates green.

## Scope

1. `docs/ebl-atf.md` corrupted sentence.
2. flake8 E501 in `ebl/fragmentarium/domain/museum.py:130`.
3. 42 mypy errors across 31 files.
4. Three files over the 250-line hard gate.

Items 2–4 are pre-existing debt on `master`; none sits in a file this branch
authored. They are being fixed at explicit user request.

## Progress

- Created `TASK-743-fixes-todo.md` and this log before starting work.

## 1. `docs/ebl-atf.md` — no change was needed

The stashed edit (`stash@{0}`) turned out to contain **only** the corruption:
it joined two lines and dropped a letter, yielding `defined i[ebl-atf.lark]`.
The merged file already holds the correct text, and the only difference from
`master` is this branch's intended `lark_parser` → `atf_grammar` URL update.

Nothing was restored, because there was nothing of value to restore. The stash
still exists and can be dropped. `grep` confirms the corruption is absent from
the working tree.

## 2 + 4a. `museum.py` — E501 and the 250-line gate

Both violations lived in the same file, so they were fixed together.

`Museum` is a 72-member `Enum`. The member payloads were extracted into
sibling modules and the enum now assigns each member from them, so **every
member is still declared statically** and remains visible to all three type
checkers. The functional `Enum("Museum", ...)` API was deliberately **not**
used: it would have hidden all 72 members from static analysis, which is the
opposite of this branch's purpose.

The split is **alphabetical by member name** (user's instruction; an earlier
by-continent split was discarded):

| module | lines |
| --- | --- |
| `museum.py` | 112 |
| `museum_entries_a_l.py` | 174 |
| `museum_entries_m_s.py` | 178 |
| `museum_entries_t_y.py` | 82 |

Ranges are chosen so each module stays under 250 lines; letters are never
split across modules.

The E501 was the 167-character Hilprecht/Jena URL. It is now implicit string
concatenation broken at `/` path boundaries. The string value is unchanged.

`__init__` also gained type hints, which it previously lacked.

### Error made here, and how it was caught

The first generator classified any member with fewer than four values as a
sentinel. Five private-collection entries have only three (no URL), so they
were silently rewritten as one-element tuples, **losing their city and
country**.

This was caught because a snapshot of all 72 members was taken *before*
touching the file and compared after. The comparison reported the five
mismatches precisely. The generator was corrected to pad short entries to a
uniform 4-tuple, and the final state verifies as: names identical, order
identical, **0 attribute mismatches**, Jena URL byte-identical.

The lesson recorded: a refactor of pure data must be verified against a
pre-change snapshot, not by reading the diff.

## 4b + 4c. The other two oversized files

- `ebl/bibliography/infrastructure/lookup_reservations.py` **253 → 198**.
  Extracted the reservation state-transition logic into
  `lookup_reservation_reconciliation.py` (78 lines):
  `LookupReservationReconciler` plus `to_utc_datetime`. This is a real seam —
  state transitions versus the collection facade — not an arbitrary cut. All
  moved methods were private and had no callers outside the module (verified
  by grep before moving). `__init__` also gained its `database: Database`
  type hint, matching the convention in the other repositories.
- `ebl/tests/bibliography/test_bibliography_lookup_reservations.py`
  **282 → 88 + 197**, split by theme into the original file (claim / commit /
  release lifecycle) and `..._reconcile.py` (reconciliation, reclaim, retire),
  with shared fixtures in `lookup_reservation_test_helpers.py` (15 lines).
  **No test was removed**: the original file held 17 tests, and the two new
  files hold 7 + 10. The sorted lists of test names before and after are
  byte-identical (verified with `diff`).

## 3. The 42 mypy errors — 40 fixed, 2 environmental

Fixed by root cause rather than one-by-one; several single fixes cleared
whole groups. No `# type: ignore`, no `# noqa`, no config change was used.

- **10 `var-annotated`** — added real annotations
  (`list[Optional[int]]`, `dict[int, Sequence[TextLine]]`,
  `list[LineToVecEncoding]`, `list[Line]`, `list[Scope]`, …).
- **`_standardizations` (2 errors, one fix)** — the base `TokenVisitor`
  declared an untyped `_standardizations = []` that only `SignsVisitor`
  used, existing purely so `TransliterationQueryText._create_signs` could
  reset it through a base-typed reference. Replaced with a polymorphic
  `reset()` — a no-op on the base, clearing the list on `SignsVisitor` —
  matching the base class's existing null-visitor pattern. This removed both
  the `var-annotated` error in `tokens.py` and the `assignment` error in
  `signs_visitor.py`.
- **6 `override` (one fix)** — every `ChapterVisitor` subclass overrides
  `visit` with `@singledispatchmethod`, whose descriptor type differs from a
  plain method. The base now declares `visit` as a `singledispatchmethod`
  too, so the base and subclasses share one shape. Runtime behaviour is
  unchanged: the base implementation is still a no-op.
- **6 `call-arg` in `enclosure_visitor.py` (one fix)** —
  `_set_enclosure_type` returned the base `Token`, discarding the concrete
  type, so every following `attr.evolve(new_token, parts=…)` looked invalid.
  `Token.set_enclosure_type` was already generic; the wrapper is now generic
  too (`TokenT`), and all six errors disappeared.
- **4 `arg-type` in `sign_search.py` / `auth0.py` (two fixes)** —
  `ebl/dispatcher.py` hard-coded `Mapping[str, str]`, but `SignsSearch`
  legitimately passes an `int` after `_parse_sub_index` coerces it. The
  dispatcher is now generic over its value type (`V`). This is **not** a
  latent runtime bug: the coercion already happens before dispatch.
  `get_scopes` was declared `Optional[str]` for parameters that default to
  `""` and are never passed `None` by any caller (verified); the annotations
  now say `str`.
- **2 `union-attr`** — `_merge_pipelines` is only reached inside
  `if self._lemma_matcher and self._sign_matcher`, but narrowing does not
  cross a method boundary. The matchers are now passed in as parameters, so
  the narrowing propagates.
- **2 attrs converter `arg-type`** — with a converter present, the `__init__`
  parameter type comes from the *converter*, not the field annotation.
  `CompoundGrapheme.compound_parts` is a `Sequence[str]` but used
  `convert_token_sequence` (`Iterable[Token]`) — a genuine latent mistake,
  now `convert_string_sequence`. `LanguagePart.tokens` used the bare builtin
  `tuple`, now `convert_token_sequence`. Both converters are just
  `tuple(...)`, so runtime behaviour is identical.
- **`misc`/`index`/`assignment`/`operator` (the rest)** — bound the value
  before the `is not None` test in `ManuscriptLine` (a guard cannot narrow a
  subscript expression); replaced `pydash.flow(...)` with a named converter
  function `prepare_reconstruction`, which attrs and mypy both understand;
  annotated the Mongo `lemma_query` and the two dispatch dicts; hoisted
  `(*PARSE_ERRORS, ValueError)` into the typed constant
  `RECONSTRUCTION_ERRORS`, the same pattern `LINE_PARSE_ERRORS` already uses;
  and replaced `any(filter(lambda …))` with a generator expression, which is
  simpler and fixed two errors at once.
- **`File.content_type`** — the ABC promised `str` while the GridFS
  implementation genuinely returns `None`. The ABC was widened to
  `Optional[str]`; every consumer assigns it to Falcon's
  `resp.content_type`, which accepts `None`.

### The 2 remaining errors are environmental, not code defects

`ebl/ebl_ai_client.py:4` and `ebl/users/infrastructure/auth0.py:6` report
`Library stubs not installed for "requests"`.

Root cause: **`mypy` is not a project dependency.** `poetry run mypy`
resolves to a global pipx install at `/usr/local/py-utils/bin/mypy`, which
cannot see anything in the project virtualenv — so installing
`types-requests` into `.venv` does not help it.

This was investigated properly rather than guessed:

1. Added `types-requests` to the dev group and installed it — the errors
   persisted, and `requests-stubs` was confirmed present in `.venv`.
2. Located the cause: `poetry run which mypy` → `/usr/local/py-utils/bin/mypy`.
3. Added `mypy==1.15.0` (the same version) to the dev group so `poetry run
   mypy` would use the venv copy. It did, and the stubs errors vanished —
   **but the error count jumped from 14 to 38**, because the venv mypy can
   resolve `lark`, `marshmallow` and friends that the global one silently
   treated as `Any`. That surfaced 24 brand-new errors in files the user
   never asked about.
4. **Reverted the toolchain change entirely** (`pyproject.toml` and
   `poetry.lock` restored, both packages uninstalled). Silently swapping the
   toolchain would have moved the goalposts and expanded the task well past
   what was requested.

The two errors are therefore left as-is and reported. Fixing them properly is
a separate decision for the user, because it means either adding `mypy` +
`types-requests` to the project (and then fixing the 24 newly-visible errors)
or installing `types-requests` into the global pipx mypy environment, which is
machine-local and not reproducible.

### A checker conflict, resolved by restructuring

Two conflicts arose, and in both cases the code was changed so that every
checker passes — neither was suppressed:

- Asserting that a frozen `Context` rejects assignment needs a write that
  mypy rejects as a read-only property. `setattr(context, "…", …)` satisfied
  mypy but tripped ruff's `B010` (constant attribute). Binding the attribute
  name to a variable first satisfies both.
- `flake8` `E203` fires on `lines[start : end + 1]`, the spacing ruff-format
  requires for a complex slice. Fixed by extracting helpers
  (`Chapter._lines_in_range`, `_strip_line_number`) that compute the bound
  first and then slice with simple names, which ruff formats without the
  space. These E203s were pre-existing at `HEAD` and only became my
  responsibility because I touched the files.

## Coverage gate — two of my own lines were uncovered, and were fixed

The first full coverage run reported 97% across the touched modules, not 100%.
Every uncovered line was checked individually against what I actually edited.
All but two were pre-existing gaps in code I never touched (`ApiUser`
properties, `ManuscriptLine.get_atf`'s empty branch, the `else` branch of
`build_pipeline`, `File.can_be_read_by`, `query_if_file_exists`, and the
unexercised branches of `retrieve_annotations`).

Two uncovered lines **were mine**, and the hard gate covers exactly this case:

- `tokens.py:102` — the `return None` body of the `reset()` I added.
- `chapter.py:34` — the `pass` body of `ChapterVisitor.visit`, which I
  relocated when adding the `@singledispatchmethod` decorator above it.

Both are now covered by new tests:

- `ebl/tests/transliteration/test_token_visitor.py` (4 tests)
- `ebl/tests/corpus/test_chapter_visitor.py` (2 tests)

These were written as **new files** rather than appended to
`test_tokens.py` (274 lines) or `test_chapter.py` (516 lines), because adding
to those would have worsened an existing 250-line violation.

A first draft of these tests asserted `visitor.reset() is None`, which mypy
rejects (`func-returns-value`). Rewritten to assert observable effects
(`result == []`, and `not vars(visitor)` — the base visitors accumulate no
state), which is both type-correct and a stronger assertion.

## Runtime verification

Re-run after all the fixes, against a locally-pinned Mongo, with `get_app()`
bypassed so Sentry never initialises (see `TASK-743-merge-log.md` for the
rationale). The throwaway databases were dropped afterwards.

The code paths I actually changed were exercised, not just the app boot:

- `ebl/dispatcher.py` is the riskiest change, so all four of its branches were
  driven through the real `/signs` route:
  `?value=ku&subIndex=1` → **200**, `?listAll=true` → **200**,
  `?subIndex=notanumber` → **422** (the `DataError` message is preserved),
  `?bogusParam=1` → **422** (`DispatchError`). The generic-value change did
  not alter any behaviour.
- `Museum`: 72 members, still serialised by name via `NameEnumField`, members
  resolve correctly out of the split modules
  (`Museum.THE_BRITISH_MUSEUM.museum_name == "The British Museum"`), and the
  `UNKNOWN` sentinel still works.
- The two changed attrs converters produce identical values:
  `LanguagePart.tokens` is a `tuple`, and
  `CompoundGrapheme.of(["KU", "NU"])` still yields `('KU', 'NU')` / `|KU.NU|`.
- `get_scopes(prefix=…, suffix=…)` works with the narrowed `str` annotations.
- `GET /signs/transliteration/ku-nu-szi` → **200**, and the ATF parser still
  loads its grammar from the relocated `atf_grammar/` directory.

## Out of scope — flagged, not silently absorbed

- **43 other files exceed the 250-line gate** repo-wide (46 in total, of which
  I fixed 3). They are pre-existing, span the whole codebase
  (`test_parse_text_line.py` 1344, `test_corpus.py` 973, `genres.py` 643, …)
  and were never part of the merge's changed set. They were left alone rather
  than expanding a 3-file request into a 46-file refactor.
- **6 files I touched are themselves over 250 lines**
  (`tokens.py` 368, `factories/fragment.py` 718, `retrieve_annotations.py` 323,
  `chapter_schemas.py` 283, `sign_tokens.py` 278, `enclosure_visitor.py` 268).
  My edits to them are one to three lines each and did not push any of them
  over the limit — they were already over.
- **149 pyright errors** exist across the files I touched. They are
  pre-existing: the baseline at `HEAD`, measured in a throwaway worktree over
  the identical file list, was **158**. My changes removed 9 and added none —
  every error category is equal or lower, and `reportOperatorIssue` went to
  zero. `task type-pyright` (the actual gate, scoped to the branch diff)
  passes with 0 errors.

## Final gate results

All run against the final tree.

1. `task format` — **PASS**, 809 files, exit 0.
2. `task lint` (ruff) — **PASS**, all checks passed.
3. `task type` (pyre, the CI gate) — **PASS**, no type errors found.
4. `task type-pyright` — **PASS**, 0 errors / 0 warnings.
5. `task test` — **PASS**, **4251 passed**, 2 skipped, 1 xfailed, 0 failures
   (up from 4245: the 6 new visitor tests).
6. Coverage — every line I added or moved is covered. The two that were not
   (`tokens.py:102`, `chapter.py:34`) now are. All remaining uncovered lines
   were individually confirmed to be pre-existing code I did not touch.
7. `flake8 --max-line-length=120` on all changed files — **PASS**, clean
   (including the pre-existing E203s in files I touched).
8. `mypy --ignore-missing-imports` — **42 → 2**. The 2 remaining are the
   environmental `requests`-stubs issue described above, not code defects.

Plus `task lint-md` — **PASS**, 0 errors — and the runtime verification above.

**Nothing has been committed.** The working tree holds all of this work, as
requested.

## Reminder

`TASK-743-merge-todo.md`, `TASK-743-merge-log.md`, `TASK-743-fixes-todo.md`
and `TASK-743-fixes-log.md` must be removed before PR #743 is merged.
