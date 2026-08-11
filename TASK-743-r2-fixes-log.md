# TASK-743-r2-fixes — Work Log

Addressing every finding in `TASK-743-review-r2-review.md` on PR #743.

## Entries

### 1. Created the tracking files

Created `TASK-743-r2-fixes-todo.md` and this log before touching any
source file. New task, new files — the previous task's
`TASK-743-review-r2-*` files do not carry forward.

Starting state: branch `fix-type-checker-blind-spots` at `aed3979f`,
working tree carrying only the three untracked
`TASK-743-review-r2-*.md` files from the review task.

### 2. Three findings need a user decision before I can act

Raised before acting, not afterwards:

- **F1** — the proper fix is `git merge origin/master`, which the
  "Never Commit or Push Unless Explicitly Told To" gate forbids without
  the user asking in their own words.
- **F4** — removing `_StartParser.__getattr__` requires deleting the
  three tests that exist only to cover it, and test removal needs
  explicit user approval.
- **F13** — deleting the six committed `TASK-743-*.md` files is a
  merge-time action the user has not asked for.

Asked the user before starting the rest.

### 3. F1 — merged master (user authorised the command explicitly)

`git merge --no-commit --no-ff origin/master` — `--no-commit` so the
merge stays uncommitted, per the commit gate. Result: **"Automatic merge
went well"**, no conflict markers. Git's rename detection carried #749's
change across the `lark_parser/` -> `atf_grammar/` rename.

Verified after the merge:

- `atf_grammar/ebl_atf_abbreviations.lark` now ends with `MultCol`,
  `Coll`, `StuTea`, `SchLen`, `Prism`, `Unc` — all six survive.
- The old `atf_parsers/lark_parser/` directory is gone.
- `ManuscriptType` has the six new members.
- `docs/ebl-atf.md` auto-merged: master's additions plus the branch's
  `atf_grammar/` link, zero conflict markers.

No extra regression test was needed: #749's own
`test_parse_siglum` is now parametrised over all six new types and runs
against the renamed grammar, which pins exactly the regression F1
warned about.

### 4. F3 / F12 — `sign_unicode_lookup.py` rewritten

Replaced `getattr(part, "name_parts", [])` with
`isinstance(sign, NamedSign) and sign.name_parts`, swapped the three
private attribute reads (`word._parts`, `part._parts`, `line._content`)
for the public `parts` / `content` properties, narrowed `text.lines` with
`isinstance(line, TextLine)`, and annotated every parameter.

One real typing correction fell out: the yielded tuple was declared
`Tuple[str, int]`, but `NamedSign.sub_index` is `Optional[int]` — `kurₓ`
has no sub-index. Introduced `ValueSubIndex = Tuple[str, Optional[int]]`,
which is what the code has always produced.

### 5. F2 — pyright errors fixed structurally

- `sign_repository.py`: `find_signs_by_order` and `get_unicode_from_atf`
  were called through a `SignRepository`-typed field but declared only on
  `MongoSignRepository`. Both are now on the ABC. `list_all_signs` was
  already there — the review's claim that all three were missing was
  wrong on that one.
- `memoizing_sign_repository.py`: adding two abstract methods would have
  made this class impossible to instantiate, so it now implements and
  delegates both. It had been silently missing them.
- `mongo_sign_repository.py`: extracted `_load_signs`, one typed cast at
  the marshmallow boundary, and used it at all seven load sites. Closes
  six errors and removes six duplicated lines.
- `signs/web/signs.py`: `svg2png` is typed `Optional[bytes]`; wrapped the
  call in an explicit `cast(bytes, ...)`.
- `token_schemas_signs.py`: `_dump_name_parts` / `_load_name_parts` now
  take and return precise types instead of bare `list`.
- `annotations_service.py`: replaced `len(x) and f(x)` with a real `if`,
  which removes the unused-expression warning.

No `type: ignore`, `pyright: ignore`, `noqa` or config change was used.

### 6. F5 / F12 — `annotations_service.py`

Split the 169-character URL comment across three lines. Added
`LineLabels` and `LineLabelHandler` aliases, replacing the bare
`Callable` (which was `Callable[..., Any]`) with one whose return type is
checked, and annotated `get_labels(lines: Sequence[Line])`. The handler
parameter stays unconstrained: the dict is keyed by concrete line type
and each lambda reads attributes that only its own type has, so pinning
the parameter to `Line` would create new errors.

### 7. F4 — removed the dead `start` parameter

`_StartParser.parse(text)` no longer takes `start`; nothing passed it.
`Optional` became an unused import and was dropped. Per the user's
decision, `__getattr__` and its three tests are left in place.

### 8. F6 — Museum values restored, and an error I made

Removed the padding `""` from the five `PRIVATE_COLLECTION_*` entries and
replaced the `MuseumEntry` alias — triplicated across the three entry
modules as `tuple[str, str, str, str]` — with a single shared
`ebl/fragmentarium/domain/museum_entry.py` defining
`Union[Tuple[str, str, str], Tuple[str, str, str, str]]`.

**Error made.** While comparing the enum against master I ran
`git stash push -q --include-untracked -- ebl/fragmentarium/domain` as
part of a scratch script. It was not a no-op: it stashed and reverted the
museum edits I had just made. Recovered with `git stash pop`, which
restored every change and dropped the accidental entry, leaving the
stash list exactly as it was. Verified afterwards that `MERGE_HEAD` is
still `c2b0a5ef`, the six #749 grammar types and enum members survive,
and `docs/ebl-atf.md` still points at `atf_grammar/`. Re-ran the enum
comparison with no stash involved.

Result: the `Museum` enum is **byte-identical to master** across all 78
members — name, value tuple, `museum_name`, `city`, `country`, `url` —
and zero members carry a padded 4-tuple value.

### 9. F7 — focused `reset()` tests

Added two tests to `test_signs_visitor.py`: one accumulates a real
result, asserts it is non-empty, calls `reset()` and asserts the result
is empty; the other proves a visitor can be reused across two parses
after a reset. Both pass.

### 10. F8 — removed the 46-line duplication

The duplicated block qlty flagged is the **first `TextLine`**, which was
byte-identical in `transliterated_fragment_lines.py` and
`lemmatized_fragment_text.py`. Extracted it to
`ebl/tests/factories/first_text_line.py` and imported it in both.

The other lines are genuinely different — the lemmatized fixture carries
`unique_lemma` and uses different token structures for lines 2, 3 and 6
— so deriving one whole fixture from the other is not possible without
changing values. Only the identical block was shared.

Verified equivalence by loading the pre-change versions of both modules
from `git show HEAD:...` alongside the new ones:
`LEMMATIZED_FRAGMENT_TEXT`, its `.atf`, and `FIRST_TEXT_LINES` all
compare equal. `ruff check --fix` then removed 15 imports that became
unused.

The remaining qlty findings (`function-parameters` on `named_signs.of` /
`of_name` and the three `test_named_sign_*` tests, `return-statements` on
`match`) are relocated pre-existing code, unchanged by this PR in
substance. Restructuring working code to satisfy a count metric is not
worth the regression risk; recorded as such rather than changed.

### 11. Two problems my own fixes introduced, and how they were found

Running pyright over the full changed set after the edits reported **71**
errors, not zero:

- **70 in `museum.py`.** Declaring `MuseumEntry` as
  `Union[Tuple[str, str, str], Tuple[str, str, str, str]]` stopped
  pyright unpacking each enum value into `Museum.__init__`, so it read
  the whole tuple as `museum_name`. Fixed by keeping two concrete
  aliases — `MuseumEntry` (4-tuple) and `MuseumEntryWithoutUrl`
  (3-tuple) — and annotating the five private collections with the
  latter. Concrete fixed-length tuples are what pyright needs.
- **1 in `memoizing_sign_repository.py`.** A pre-existing LSP mismatch,
  invisible until I pulled the file into the changed set:
  `search_composite_signs` widened `sub_index` to `Optional[int] = None`
  while the delegate it calls requires `int`. Aligned the signature with
  the ABC. No caller passed the default.

After both fixes: **pyright 0 errors, 0 warnings**; pyre clean; the
`Museum` enum still byte-identical to master.

### 12. A live 500 found and fixed while verifying F3

To prove the rewritten `extract_words_sub_indexes` was behaviour-
preserving, I loaded `git show HEAD:...sign_unicode_lookup.py` alongside
the new module and diffed their output over 17 ATF inputs.

The old implementation **crashed** on erasures:

```text
AttributeError: 'Erasure' object has no attribute '_parts'
```

`Erasure` exposes the public `parts` property but no `_parts` attribute.
`AttributeError` is not in `LINE_PARSE_ERRORS`, so it escaped
`TransliterationResource.on_get` and surfaced as a **500** on
`GET /signs/transliteration/{line}` for any line containing an erasure.
Switching to the public property fixes it.

Every other case produces byte-identical output. Confirmed live:
`GET /signs/transliteration/°nu : ši\ku°` now returns 200 with a unicode
list. Added `test_erasure_transliteration_is_not_a_server_error` to pin
it.

### 13. Runtime verification against the fixed tree

Same harness as the review round: `create_app(create_context())` under
waitress on `127.0.0.1:8123`, `MONGODB_URI` pinned to
`mongodb://127.0.0.1:27017`, throwaway db `ebl_review_743_r2_smoke`,
throwaway `AUTH0_PEM`, `SENTRY_DSN` unset, `.env` never sourced.

| Request | Result |
| --- | --- |
| `GET /signs/transliteration/ku-nu-szi` | 200 |
| `GET /signs/transliteration/$$$` | 422 |
| `GET /signs/transliteration/(((((` | 422 |
| `GET /signs/transliteration/k[u]r` | 200 |
| `GET /signs/transliteration/°nu : ši\ku°` | **200** (was 500) |
| `GET /signs/transliteration/{d}INANA` | 200 |
| `GET /signs/transliteration/{m}{d}EN-lil₂` | 200 |
| `GET /signs/all` | 200 |
| `GET /signs/KU/neo-assyrian` | 200 (new ABC method) |
| `GET /markup?text=@i{italic} and plain` | 200 |
| `GET /fragments/query?transliteration=ku-nu-szi` | 200 |
| `GET /fragments` with `random`/`needsRevision`/`interesting` | 200 |
| `GET /fragments?bogus=1` | 422 |

### 14. Test-run error and recovery

I added `test_erasure_transliteration_is_not_a_server_error` **after**
starting the full suite, so that run no longer covered the tree under
test. Rather than report a stale result, I killed it at 41% and started a
clean run over the final tree. The re-verify-after-every-rewrite gate
does not accept evidence gathered before the change.

### 15. Extra coverage the gate demanded

The coverage intersection showed three uncovered lines among the lines
this task touched:

- `memoizing_sign_repository.py` 63, 66 — the two new delegating
  methods. Added `test_find_signs_by_order_memoization` and
  `test_get_unicode_from_atf_delegates`.
- `mongo_sign_repository.py` 227 — `search_composite_signs`, whose real
  implementation never ran because `TestSignRepository` in `conftest.py`
  stubs it. The stub's comment blames mongomock, but the suite runs a
  real `pymongo_inmemory` mongod, so the real query works. Added
  `ebl/tests/signs/test_sign_repository_composite.py`, which drives a
  plain `MongoSignRepository`. The stub was left untouched — removing it
  would change existing tests.

While there I closed two adjacent gaps of the same class rather than
leave them: `list_all_signs` on the memoizing repository, and the
`/signs/{sign_name}/{sort_era}` route, whose handler calls the
`find_signs_by_order` method I had just added to the ABC
(`ebl/tests/signs/test_sign_order_route.py`).

`test_sign_repository.py` is already 322 lines, so the new repository
test went into its own module rather than pushing an existing file
further past the 250-line gate.

Second error found by pyright: my new memoizing test passed the string
`"SI"` where `find_signs_by_order` expects `SignName`. Wrapped it in
`SignName(...)`.

### 16. Interrupted runs, and why the suite was run three times

The full suite was started, then abandoned, twice — each time because I
had changed the tree after the run began, and the re-verify gate does
not accept evidence gathered before the change. A third interruption was
not mine: the session tore down and killed the in-flight run and the
smoke server, and cleared the scratchpad. Recreated the harness and ran
everything again from scratch on the final tree.

`pyre check` also failed once with an internal exception
(`Worker.Worker_exited_abnormally`) while the test suite was running
concurrently. That was resource contention, not a type error: run on its
own it reports no errors.

### 17. Final gate results on the shipping tree

| Gate | Result |
| --- | --- |
| `task format` | pass — 835 files already formatted |
| `task lint` (ruff) | pass |
| `task type` (pyre) | **pass, no type errors** |
| `task type-pyright` (85 files) | **0 errors, 0 warnings** |
| `task test` | **4366 passed**, 2 skipped, 1 xfailed |
| Coverage on lines touched vs master | **0 uncovered** |
| `flake8 --max-line-length=120` | pass |
| `mypy --ignore-missing-imports` | 5 errors, none in the changed set |
| 250-line limit (85 files) | pass |
| `task lint-md` | pass |
| Runtime smoke, 14 routes | all as expected |

The five mypy errors are pre-existing, in `atf_importer` modules the
changed files import but neither this PR nor this task touches.

Nothing was committed and nothing was pushed. The `origin/master` merge
is staged but uncommitted (`MERGE_HEAD` = `c2b0a5ef`).
