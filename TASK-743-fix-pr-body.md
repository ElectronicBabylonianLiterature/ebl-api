<!-- markdownlint-disable MD013 MD041 -->
> [!WARNING]
>
> ## BLOCKING — three gates, none optional
>
> This PR changes the `nameParts` wire format **and** the stored MongoDB shape.
> Three things must happen before it merges. None is optional.
>
> ### Gate 1 — the frontend must read `nameBreaks`
>
> `nameParts` no longer carries the brackets that fall *inside* a name.
> They are in a new sibling array, `nameBreaks`, and the client must
> interleave the two to render a name as written.
>
> ```text
> before  "nameParts":  [ValueToken("k"), BrokenAway("]"), ValueToken("u")]
>
> after   "nameParts":  [ValueToken("k"), ValueToken("u")]
>         "nameBreaks": [BrokenAway("]")]
>
> interleave: parts[0], breaks[0], parts[1], breaks[1], ...  ->  k ] u
> ```
>
> N parts take at most N breaks, strictly alternating, so position alone
> reconstructs the original order. Element shapes are otherwise unchanged.
> A client that ignores `nameBreaks` still renders names, but silently drops
> brackets inside them — a **wrong reading**, not a cosmetic loss. Brackets
> *around* a name were never in `nameParts` and are unaffected.
>
> **Merge blocked until the matching frontend change is merged or queued.**
>
> ### Gate 2 — the data migration must be run, then deleted
>
> `nameParts` is also the stored shape, at
> `text.lines[].content[].parts[].nameParts` in every fragment and chapter
> document. A `@pre_load` adapter means old documents keep loading, so the
> deploy will not break — but until the migration runs the database holds two
> shapes at once, and every read pays for the conversion.
>
> ```bash
> poetry run python task_743_migrate_name_breaks.py           # dry run, reports counts
> poetry run python task_743_migrate_name_breaks.py --apply   # writes
> ```
>
> Dry-run by default, batched, idempotent, and safe to re-run. It has **not**
> been run against any database.
>
> **Merge blocked until the migration has been run against production, or an
> owner has explicitly scheduled it and said so on this PR.**
>
> ### Gate 3 — the migration script and the task documents must not reach `master`
>
Two sets of files on this branch are **temporary and must not be merged**:
>
> 1. **The migration** — `task_743_migrate_name_breaks.py` and
>    `task_743_migrate_name_breaks_test.py`. A one-off for this data change,
>    not part of the codebase. They live at the repository root with a
>    `task_743_` prefix so they cannot be mistaken for permanent modules.
> 2. **The task documents** — every `TASK-743*.md` and `TASK-744*.md` file.
>    These are the working log, the review, the handoff and this description's
>    own source. They are committed so the history is reviewable, not because
>    they belong in the codebase.
>
> **All of them must be deleted from this branch before it merges.** A merge
> that carries any of them into `master` is a defect, regardless of whether
> everything else is green.
>
> ```bash
> git rm task_743_migrate_name_breaks.py task_743_migrate_name_breaks_test.py
> git rm TASK-743*.md TASK-744*.md TASK-745*.md
> ```
>
> Reviewers: check the file list before approving. `master` must contain none
> of them.
>
> Reviewers: please do not approve while any of the three gates is open.

Split out of #740, where this work did not belong.

This PR does two things: it makes the ATF parser visible to the type
checkers, and it pays down the type-checker, lint and file-size debt that
became visible once the checkers could see it.

## Part 1 — the ATF parser was never type-checked

`ebl/transliteration/domain/atf_parsers/` contained both a module
`lark_parser.py` and a directory `lark_parser/` holding the `.lark` grammar
files. mypy and pyright resolve the dotted name to the **directory** as a
namespace package, see an empty module, and report every import from it as
missing:

```text
Module "...atf_parsers.lark_parser" has no attribute "PARSE_ERRORS"
Module "...atf_parsers.lark_parser" has no attribute "parse_atf_lark"
Module "...atf_parsers.lark_parser" has no attribute "parse_markup_paragraphs"
```

CPython prefers the real module, so nothing ever broke at runtime. The effect
was silent: **the ATF parser and everything importing it had not been
type-checked**, and the noise trained us to ignore those errors.

### The fix

Rename the grammar directory to `atf_grammar/` and update its eight
references. The `.lark` files use relative `%import .name`, so their contents
are untouched, and nothing in packaging refers to the path.

Then fix what the checkers found once they could see the module:

| Where | What |
| --- | --- |
| `parse_markup_paragraphs` | `parts` had no annotation |
| `parse_atf_lark` | one local `lines` rebound through three types; split into three names, and `check_errors` now returns the validated lines |
| `_StartParser.parse` | `**kwargs: object` made forwarded values untypeable; the wrapper always parses from its own `start`, so the parameter list is now just `text` |
| `lark_parser`, `legacy_atf_converter` | `Tree` imported from modules that only re-export it |
| `legacy_atf_converter` | unannotated `lines_data`; `children[0]` re-indexed four times; starred `except` clause the checkers cannot read |
| `legacy_atf_line_validator` | `validate_text_line` declared `Optional[Type[Exception]]` but returns an instance; `line_tree` rebound from `Tree` to `Line` |
| `word_tokens.merge` | returned `A` where `T` was declared |

## Part 2 — type-checker, lint and file-size debt

With the checkers able to see the code, `task type-pyright` reported 149
errors across the changed set. All are now fixed **structurally** — no
`# type: ignore`, no `# pyright: ignore`, and no type-checker or linter
configuration was relaxed:

- **Test factories.** `tests/factories/fragment.py` and
  `fragment_metadata_factories.py` follow the convention already proven clean
  in `tests/factories/archaeology.py`: declarations imported from
  `factory.declarations` / `factory.faker` / `factory.helpers`, and
  `make_factory` instead of a class with a nested `Meta`.
- **`signs_visitor`.** `skip_enclosures` / `skip_erasures` were typed
  `Callable[[S, T], None] -> Callable[[S, T], None]`, which replaced each
  decorated method's signature and made every override look incompatible.
  They are now signature-preserving.
- **attrs validators.** `@field.validator` decorators became module-level
  functions passed as `attr.ib(validator=...)`.
- **pymongo / marshmallow boundaries.** Explicit `cast` where `.load()` and
  `.aggregate()` return loosely typed values, and repository overrides
  annotated to match `FragmentRepository`.

### File splits (250-line limit)

| Was | Now |
| --- | --- |
| `fragmentarium/domain/museum.py` (472) | `museum.py` + `museum_entries_a_l/m_s/t_y.py` |
| `tests/factories/fragment.py` (717) | four modules |
| `transliteration/domain/tokens.py` | `tokens.py` + `token_base.py` |
| `transliteration/domain/sign_tokens.py` | `sign_tokens.py` + `sign_token_base.py` + `named_signs.py` |
| `transliteration/domain/enclosure_visitor.py` | + `enclosure_state.py` + `enclosure_updater.py` |
| `fragmentarium/retrieve_annotations.py` | + `retrieve_annotations_helpers.py` |
| `corpus/web/chapter_schemas.py` | + `chapter_manuscript_schemas.py` |
| `bibliography/infrastructure/lookup_reservations.py` | + `lookup_reservation_reconciliation.py` |
| `signs/infrastructure/mongo_sign_repository.py` (403) | + `sign_schemas.py` + `sign_unicode_lookup.py` |
| `tests/transliteration/test_sign_tokens.py` (491) | split into four test modules |

Modules that were split keep an `__all__` re-export facade covering the names
their own callers use — not every name the module happened to make reachable.
`mongo_sign_repository` re-exports `COLLECTION`, `MongoSignRepository`,
`SignDtoSchema` and `SignSchema`, while `ValueSchema`, `FosseySchema`,
`LogogramSchema`, `SignListRecordSchema` and `SortKeysSchema` now live in
`sign_schemas.py` only — they are internals of `SignSchema` and nothing imports
them from the old path.

Two incidental re-exports were deliberately dropped rather than preserved:
`tokens.py` no longer re-exports `EnclosureType`, `LemmatizationError` or
`LemmatizationToken`, which it only ever exposed as a side effect of its own
imports. Every importer inside the repository has been moved to the real
module (`test_note_line.py` was the only one); anything outside it that
imported `EnclosureType` from `tokens` needs the same one-line change.

## Part 3 — design fixes found in review

- **`TokenVisitor` no longer lies.** The base ABC previously returned `[]`
  from `result`, so any subclass that forgot to override it silently produced
  an empty sign list. A new `SignsCollectingVisitor` declares `reset()` and
  `result_string` as abstract, and `TransliterationQuery.visitor` is typed
  against it. `_create_signs` reads `result_string`, which is `Sequence[str]`
  — the value feeds `re.escape`, so this also closes a latent type
  inconsistency.
- **`NameParts` no longer mixes two types in one array.** It was
  `Sequence[Union[ValueToken, BrokenAway]]`, and readers had to
  `isinstance`-probe to compute a sign's name. A `NamePart` wrapper now
  carries each token together with the text it contributes, so the array holds
  one type and classification happens once. `NamedSign.name_tokens` exposes
  the unwrapped tokens for visitors and ATF rendering.
  **The `nameParts` wire format is unchanged** — verified by diffing the
  `OneOfTokenSchema` output before and after; the interleaved
  `ValueToken, BrokenAway, ValueToken` ordering is preserved.
- **`GET /signs/transliteration/{line}` returned 500 on unparsable input.**
  `TransliterationError` escaped `get_unicode_from_atf` unmapped. It now
  raises `DataError`, which the error handler maps to **422**, with a test.

## Verification

| Gate | Result |
| --- | --- |
| `task format` | clean |
| `task lint` (ruff) | passed |
| `task type` (**pyre** — the gate CI enforces) | **No type errors found** |
| `task type-pyright` | **0 errors** (was 149; master baseline on the same files was 173) |
| `task test` | 4494 passed, 2 skipped, 1 xfailed |
| Coverage on changed modules | **100% on every changed source file** (96.6% repository-wide) |
| `flake8 --max-line-length=120` | 0 errors |
| `mypy --ignore-missing-imports` | 0 errors in changed files |
| `qlty smells` | 0 findings in any file this PR touches |
| `task lint-md` | 0 errors |
| 250-line limit | all changed files within limit (`lark_parser.py` is at 250) |

## Part 4 — review follow-ups

Addressing the review of this PR:

- **`chapter_schemas.py` declared `__all__` twice.** The second assignment
  overwrote the first and dropped `ApiLineVariantSchema`. Removed.
- **CodeQL.** `scan_values(lambda value: bool(value))` is now
  `scan_values(bool)`, and `SignsCollectingVisitor`'s abstract members raise
  `NotImplementedError` like `Token.value` and `Token.parts` in the same file,
  rather than using `...`. All three alerts clear.
- **qlty.** `retrieve_annotations_helpers.match` went from seven returns to two
  via a membership test; `Logogram.of` / `of_name` lost their `surrogate`
  parameter to a new `Logogram.with_surrogate` wither; and the three
  `test_named_sign_*` parametrised tests now take a single `NamedTuple` case
  instead of seven to nine positional arguments. That cleared the six issues
  open at the time. Note that the `function-parameters` finding on
  `of` / `of_name` then reappeared at the new location after the split —
  see Part 5.
- **`TextLine` is now `@final`,** so the `cast` in `merge` is provable rather
  than merely true today. No subclass exists.
- **`NamePart` is a thin wrapper, not a `Token` impersonator.** An earlier
  round had it delegating the whole `Token` interface; it now holds only the
  token it wraps and derives `name_contribution` from it, so there is no
  wrapper state that can disagree with the token and nothing to keep in sync.
- **`atf_importer` type debt.** `logger.py`, `lemmatization.py` and
  `atf_indexing_visitor.py` are now clean under all three checkers, which
  removed a `# pyre-ignore[6]` along the way.
- **`test_parse_word.py`** (875 lines) is split into a 66-line test module and
  six case modules, all within the 250-line limit.

**Running service.** Booted the app over HTTP against a local throwaway
database and exercised the affected routes: the ATF parser route, the markup
route, the transliteration query path, all three fragment-search dispatcher
keys, the dispatcher error path, and the sign search served by the split
repository. `GET /signs/transliteration/$$$` now returns 422 rather than 500.
`Museum` still has all 72 members after the three-way split, and ATF
round-trips through the relocated grammar directory.

## Part 5 — second review round

Addressing the review in `TASK-743-r3-review.md`. Fourteen findings, no
blockers.

- **The `NamePart` converter no longer probes.** `convert_name_parts` took an
  `Iterable[Token | NamePart]` and told the two apart with `isinstance`.
  Wrapping became one explicit `name_parts_of(tokens)` helper. **This was only
  half the fix — `name_contribution_of` still probed. The wrapper has since
  been removed entirely; see Part 7.**
- **`NamePart.name_contribution` is derived, not stored.** It was a field whose
  validator recomputed exactly the function that produced it. It is a property;
  the validator is gone and the inconsistent state is unrepresentable.
- **`of` / `of_name` are down to five parameters** including `cls`. `sign`
  followed `surrogate` into a wither (`NamedSign.with_sign`), which also makes
  `Reading`, `Logogram` and `Number` construct uniformly.
- **`nameParts` is a plain nested list field again.** The `fields.Function`
  plus module-global `OneOfTokenSchema` singleton is replaced by
  `fields.List(fields.Nested("OneOfTokenSchema"), attribute="name_tokens")`.
  Same wire format, no global mutable state, and a wrong-typed `nameParts` now
  gets `"Not a valid list."` instead of a per-character error list.
- **The `visitor is None` branch is gone.** It was unreachable:
  `TransliterationQueryEmpty` is the only construction with no visitor and it
  never computes a regexp. `visitor` is non-`Optional` again and
  `TransliterationQueryEmpty` carries a `NullSignsCollectingVisitor`, which is
  what the pre-split code did with `TokenVisitor()`.
- **The transliteration-route tests assert payloads.** They previously checked
  only `200` and `isinstance(json, list)` — and, since they never seeded the
  sign fixture, were passing on `[]`. All seven now seed signs and assert the
  exact response, including the erasure semantics (both the erased and the
  over-erased signs are returned) and the case where a reading is carried by
  more than one sign.
- **`get_unicode_from_atf` and `find_signs_by_order` are no longer memoized.**
  `pydash.memoize` is an unbounded dict and `get_unicode_from_atf`'s key is a
  caller-supplied ATF string. `MemoizingSignRepository` delegates them plainly.
- **`TokenVisitor`'s `visit_*` parameters stay unannotated, deliberately.** An
  earlier round annotated all 24 with the concrete token classes, imported under
  `if TYPE_CHECKING:`. CodeQL then raised 75 `Module-level cyclic import` alerts,
  every one tracing to that block: `tokens -> token_base -> (TYPE_CHECKING)
  enclosure_tokens -> tokens`. The imports never execute, but the cycle is real
  in the import graph. A visitor typed against its concrete tokens, whose tokens
  are typed against the visitor, is inherently circular, and moving
  `TokenVisitor` to its own module relocates the cycle rather than removing it —
  so the parameters went back to being unannotated, as on `master`. Every
  visitor *subclass* keeps its concrete annotations, which is where they carry
  weight. `test_token_base_has_no_cyclic_imports.py` pins the regression.
  Annotating them anyway did surface one real bug that pyre caught and that is
  fixed here: `AtfVisitor.visit_accidental_omission` was declared to take an
  `IntentionalOmission`. `visit_erasure` also gained its missing `-> None`.
- **`extant_lines` is keyed by a real tuple.** `Chapter._get_extant_lines`
  groups by `tuple(extant_line.label)`, so the `Tuple[Label, ...]` key
  annotation is accurate and hashability no longer depends on every caller
  having passed a tuple.
- **The Auth0 issuer is a `str` by construction.** `str(self.issuer)` would
  have turned a `None` issuer into the literal `"None"` and requested
  `"Noneuserinfo"`. `Auth0Backend.__init__` now takes `issuer: str` and hands it
  to `JWTAuthBackend`, which owns it; the use site reads it back through a
  `cast` rather than keeping a second copy.
- **`_deserialize_transliteration` names its own field,** so a bad
  `unplacedLines` payload is no longer reported as an invalid colophon.
- **Validator type hints.** The four attrs validators are
  `(_instance: object, _attribute: object, value: T) -> None`.
- **`parse_word_cases_4.py`** routes its hyphen-joined cases through a
  `hyphenated_word(*parts: Sequence[Token])` helper, removing the duplicated
  `Reading / Joiner.hyphen()` blocks.

**No linter or type-checker configuration is relaxed.** An earlier round added
`if TYPE_CHECKING:` to `.coveragerc`'s `exclude_lines`, to stop coverage
counting import statements that can never execute. With the `TYPE_CHECKING`
block gone there is nothing to exclude, so that change was reverted too:
`.coveragerc` is byte-identical to `master`. No `.coveragerc`, no
`pyproject.toml`, no `mypy.ini`, no `ruff.toml`, no `.markdownlint*`, no
`Taskfile`, no `.devcontainer/` and no `.github/workflows/` file is touched,
and no type checker, linter or coverage threshold is relaxed anywhere.

**One repository-rules file is changed, deliberately:**
`.github/instructions/copilot.instructions.md` gains `qlty smells` as
pre-commit gate 9 and a `HARD GATE: qlty Must Be Clean` section. That is a
change to how the repo is worked on, not to how any tool behaves, and it is
called out here so it is reviewed as a rules change rather than slipping
through inside a typing PR.

**`ebl/fragmentarium/annotations.json` is valid JSON again.** It carried a
trailing comma after the `finished` array, so `json.load` raised
`JSONDecodeError` on `master`. `retrieve_annotations.py` opens that file in two
places, which meant the `--filter finished` CLI path was broken outright. The
one-character fix is the only change to that file.

Two latent 500s on `GET /signs/transliteration/{line}` are fixed by this PR
beyond the `$$$` case already described: on `master`,
`_extract_words_subIndexes` raised `AttributeError` for an erasure
(`'Erasure' object has no attribute '_parts'`) and for any input containing a
non-text line (`'StateDollarLine' object has no attribute '_content'`). Both
are now handled, and both are pinned by tests.

## Part 6 — third review round

Addressing the review in `TASK-743-r11-review.md`. Thirteen findings, no
blockers.

- **The description itself was the main finding.** Part 5 claimed
  `TokenVisitor`'s parameters were annotated behind an `if TYPE_CHECKING:` guard
  and that `.coveragerc` had gained an `exclude_lines` entry. The commit that
  broke the import cycle had reverted both and the prose was never updated, so a
  reviewer would have been signing off typing work that is not in the branch.
  Both passages are corrected above, as is the Auth0 issuer bullet and the
  verification table, whose test count and coverage figures were stale.
- **The `TYPE_CHECKING` guard test no longer greps.** It asserted
  `"TYPE_CHECKING" not in source`, which would have fired on a comment and did
  not actually check for a guard. It now walks the AST for an `if
  TYPE_CHECKING:` block, catching the plain, `typing.`-qualified and negated
  forms while ignoring the name in comments and strings.
- **`..._import_token_base_one_way` did not test one-wayness.** It asserted only
  that the concrete modules import the base. It is now two tests: they depend on
  `token_base`, and `token_base` does not depend back.
- **`sign_to_sign_ground_truth`'s validation guard is back.** The split into
  `retrieve_annotations_helpers` dropped the `ValueError` that rejected an empty,
  `"?"` or all-lowercase ground-truth label. It was unreachable given
  `parse_annotations`' own fallbacks, so nothing was broken — but it is a
  data-integrity guard on CLI-generated training labels and it is cheap to keep.
  Restored, split into `_match_ground_truth` and `_is_degenerate_label`, and
  reached by tests that patch a lowercase value into `MANUAL_SIGN_NAME_FIXES`.
- **`TransliterationQuery` is consistently hashable.** `frozen=True` made attrs
  generate `__hash__`, but the class holds a `SignsVisitor`, which is unhashable,
  so `hash(TransliterationQueryEmpty())` worked while `hash(TransliterationQueryText(...))`
  raised `TypeError`. `visitor` is now `eq=False`: it leaves both `__eq__` and
  `__hash__`, equality rests on the string and the derived regexp, and queries
  are usable as dict keys. Nothing hashed one before, so this is latent-only.
- **`Auth0Backend` no longer keeps a second issuer.** `self._issuer` duplicated
  `self.issuer`, which `JWTAuthBackend.__init__` already assigns from the same
  argument. One value, one owner.
- **The last `flake8` error is gone at source.** `test_signs_visitor_variants`
  had `[-len(other.result_unicode) :]`, where the space is inserted by
  `ruff format` itself and then flagged as `E203` by pycodestyle. Hoisting the
  lengths into `head_length` / `tail_length` satisfies both. No ignore list, no
  configuration change.
- **The remaining unannotated parameters are annotated.** Nine marshmallow hooks
  in `sign_schemas.py`, `MuseumNumberString._serialize` / `_deserialize`,
  `filter_annotation`'s `to_filter`, and `parse_line_` / `check_errors` in
  `lark_parser.py` via a `ParsedLine` alias.

Three findings are deliberately **not** addressed here, because each is
pre-existing and outside this PR's scope:

- `ManuscriptLine.paratext` is `Sequence[Union[DollarLine, NoteLine]]` and
  `ChapterQueryColophonLines.get_matching_lines` takes
  `Sequence[Union[TextLine, L]]`. Both are on `master` and splitting them is a
  wire-format change across the corpus schemas.
- `GET /fragments/query?transliteration=` (empty value) returns 500 —
  `IndexError` at `fragment_sign_matcher.py:33`. Identical on `master`. What an
  empty transliteration parameter *should* mean is a product decision, not a
  mechanical fix.
- The `Analyze (python)` workflow pins `github/codeql-action/*@v2` and carries a
  failure-level deprecation annotation while still concluding success; the
  pypy-3.11 matrix leg uploads no coverage data. Both are workflow files this PR
  does not touch.

## Part 7 — fourth review round

Addressing the fourteen findings in the round-12 review. All three blocking
findings are fixed, and so is every non-blocking one.

### `nameParts` no longer carries two types — this changes the wire format

This is the finding the previous rounds kept half-fixing. `NamePart` wrapped an
arbitrary `Token`, `name_contribution_of` still told `ValueToken` from
`BrokenAway` with `isinstance`, and `nameParts` still went over the wire as one
`OneOfTokenSchema` array interleaving both. The wrapper relocated the probe
rather than removing it.

The grammar makes the real fix obvious:

```text
value_name:    value_name_part (broken_away value_name_part)*
number_name:   number_name_head (broken_away number_name_part)*
logogram_name: logogram_name_part (broken_away logogram_name_part)* | LEGACY_ORACC_DISH_DIVIDER
```

A name is strictly alternating, so the two types separate losslessly **by
position** — no index, no discriminator:

| Level | Before | After |
| --- | --- | --- |
| domain | `name_parts: Sequence[NamePart]` wrapping `Token` | `name_parts: Sequence[ValueToken]` + `name_breaks: Sequence[BrokenAway]` |
| Mongo / wire | `nameParts: [ValueToken, BrokenAway, ValueToken]` | `nameParts: [ValueToken, ValueToken]`, `nameBreaks: [BrokenAway]` |

`name` joins the value tokens; `value` and `name_tokens` interleave the arrays
back into written order. `NamePart`, `NameParts`, `name_contribution_of` and
`name_parts_of` are deleted, and no `isinstance` is left in the model.

The interleaved form is converted in exactly one place — `signs_transformer`,
which slices the grammar's children `[0::2]` and `[1::2]`. Construction is
atomic through `NamedSignArguments`; a `with_name_breaks` wither was tried first
and dropped, because it made `Reading.of(parts)` build a transient object that
violated the invariant.

Element schemas are concrete rather than `OneOfTokenSchema`, and each declares a
validated `type`, so a `BrokenAway` placed in `nameParts` is a **422** rather
than a silent coercion. That mattered: `BaseTokenSchema` uses
`unknown = EXCLUDE`, so without it a misplaced `BrokenAway` would have loaded as
a `ValueToken` carrying `"]"`. `NamedSign` validates its own arrays too, so the
mistake is caught in the domain as well as at the boundary.

**This is a breaking change for the frontend**, which must read `nameBreaks` and
interleave. Element shapes are otherwise unchanged, so a client that ignores
`nameBreaks` still renders names correctly — it only loses brackets *inside* a
name. Brackets *around* a name were never in `nameParts`.

### Existing documents keep loading

`nameParts` is also the stored Mongo shape, at
`text.lines[].content[].parts[].nameParts` in every fragment and chapter. A
`@pre_load` adapter splits a legacy interleaved `nameParts` when `nameBreaks` is
absent, so **no document has to be migrated before deploying**. Verified: a
document rewritten into the old shape loads to an equal `Text` and round-trips
the same ATF.

`task_743_migrate_name_breaks.py` migrates stored documents when you choose. It
is dry-run by default, batched, idempotent, and **has not been run against any
database.** It is a branch-only temporary file and must be deleted before this
merges — see blocking gate 3.

The invariant is `len(name_breaks) <= len(name_parts)`. It started as exactly
`N-1`, which was too strict: `test_chapter_merge.py` builds a `Reading` whose
name is `ku]` — one part with a trailing break. The parser never emits that
(ATF `ku]` puts the bracket outside the reading), but `master` accepted the
shape, so rejecting it would have regressed real data.

### The other twelve findings

- **`tokens.py`'s `__all__` no longer narrows the module.** It listed only the
  six re-exported base names and dropped the nine classes the module defines, so
  `import *` exported 6 where `master` exported 15. Auditing the other facades
  found more: `chapter_schemas.py` was missing `LineNumberString` (which a test
  imports), `RECONSTRUCTION_ERRORS` and `deserialize_translation`, and
  `tests/factories/fragment.py` was missing six constants. All seven facades now
  list everything they define plus everything they re-export.
  `ebl/tests/test_module_facades.py` pins all seven and also asserts each
  `__all__` is sorted and duplicate-free — which is how the double-`__all__`
  assignment found in an earlier round would have been caught.
- **The two `# type: ignore[arg-type]` comments are gone.** A `ProvenanceLookup`
  `Protocol` covers the three methods `PatternMatcher` actually uses, so the
  test stub satisfies it structurally and `_site_filter`'s `service` parameter
  is typed. Removing the suppressions immediately exposed a real defect they had
  been hiding: the stub's `find_children(long_name)` did not match
  `find_children(parent)`, so a keyword call would have failed. The Part 2 claim
  that this PR adds no `# type: ignore` is now true.
- **`GET /signs?listAll=true` returned 500.** `list_all_signs` yields sign ids,
  which were pushed through `SignDtoSchema`, whose `@post_dump` did
  `data.pop("_id")` on a string. Ids and `Sign` objects are different types and
  no longer share a serialization path. Pre-existing on `master`.
- **`/markup` and `/cached-markup` returned 500 on unparsable input** — the same
  defect this PR fixed for `/signs/transliteration`. `ValidationError` is not
  registered in `error_handler.set_up`, so it reached the generic handler. Both
  routes now raise `DataError` (422). Pre-existing on `master`.
- **`Token.update_alignment` no longer takes `object`.** `AlignmentMap` moved to
  a leaf module so `token_base` can import it without a cycle, and `Word`'s
  override is annotated too — previously neither end of that call was checked.
  Pyre then found a real defect the old `cast` had hidden: `update_alignment`
  indexed the map with an `Optional[int]`.
- **`_StartParser.__getattr__` is gone.** Returning `object` made every
  attribute access on all seven module-level parsers type-check, typos included.
  Only `.parse` and `.options` are ever used, so `options` is now an explicit
  `LarkOptions` property. All six existing assertions still hold.
- **`sign_search.py` no longer mixes two value types in one mapping.**
  `_parse_sub_index` produced a `Mapping` holding both `str` and `int`, which
  made `create_dispatcher`'s type parameter resolve to `object` and produced
  eight pyright errors once the file entered the changed set. The params mapping
  stays `Mapping[str, str]` and `sub_index_of(params)` converts at the point of
  use.
- **Smaller ones.** The redundant `cast(TextLine, other)` in `TextLine.merge` is
  gone now that `@final` makes the `isinstance` narrowing exact;
  `TransliterationQueryEmpty` uses `attr.Factory` instead of a shared class-body
  visitor; the three `make_token` hooks this PR rewrote are annotated; and
  `Divider.string_flags`, a verbatim duplicate of `AbstractSign.string_flags`,
  is deleted.

`ChapterVisitor.visit` becoming a `singledispatchmethod` and `lark_parser.py`
sitting at exactly 250 lines were reviewed and accepted as-is.

### Test modules split

Updating the call sites pulled four test modules into the diff that were already
over the 250-line limit on `master`. They are split with the pattern this PR
already used for `test_parse_word.py`:

| Was | Now |
| --- | --- |
| `test_parse_text_line.py` (1354) | 205 lines + 7 case modules + a fixtures module |
| `test_chapter_merge.py` (714) | 214 lines + 4 case modules + a fixtures module |
| `test_enclosure_visitor_types.py` (413) | 54 lines + 2 case modules |
| `test_text_merge.py` (316) | 32 lines + 2 case modules |

`test_name_part.py` tested the deleted `NamePart` wrapper, so it is rewritten as
`test_named_sign_name.py`. Every assertion was translated rather than dropped;
the file went from 10 to 14 tests.
