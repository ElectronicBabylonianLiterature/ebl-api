<!-- markdownlint-disable MD013 -->

# TASK-743-review2 — Review of PR #743

**PR:** [#743 — Make the ATF parser visible to the type checkers](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743) · branch `fix-type-checker-blind-spots` → `master` · head `6926bc1a` · 125 files, +6586 / −3937

## Review summary

Nice piece of work — finding that `lark_parser.py` and `lark_parser/` were shadowing each other, and that the whole ATF parser had therefore never been type-checked, is a genuinely good catch, and the follow-through is thorough. Everything green on my side: pyre, pyright and mypy are all clean, the full suite passes (4385 passed, 2 skipped, 1 xfailed), no file is over 250 lines, and I confirmed the 422 fix on a running server rather than just in tests. All five CodeQL alerts are fixed, and I diffed all 72 `Museum` entries against master — every value is byte-identical, so that review point is fully settled. No dev container or tooling configuration is touched.

Two things I'd like sorted before merge. The seven `TASK-743-*.md` files are committed on the branch and would land on master — they need to come off. And in `chapter.py` there's a `cast` that claims `pydash.group_by` returns a plain `ExtantLine` per label when it actually returns a list of them, so a public property's declared type is now wrong; that's the one change that works against the goal of the PR. Three smaller notes below, all easy.

Thanks for pushing this through — it's a lot of surface area handled carefully.

### Details

| # | Severity | Where | Finding |
| --- | --- | --- | --- |
| F1 | **Blocker** | repo root | Seven `TASK-743-*.md` task-tracking files are committed on the branch and would be merged into `master`. |
| F2 | **Medium** | `ebl/corpus/domain/chapter.py:224` | `cast(Mapping[ManuscriptLineLabel, ExtantLine], ...)` asserts a type the value does not have — `pydash.group_by` returns a list per key. |
| F3 | **Low** | `ebl/transliteration/domain/transliteration_query.py:196` | `TransliterationQueryEmpty` silently lost `frozen=True`; it is now mutable, and nothing in the PR requires that. |
| F4 | **Low** | `ebl/signs/infrastructure/memoizing_sign_repository.py:25` | `get_unicode_from_atf` is the only delegate in the memoizing repository that is not memoized. |
| F5 | **Low** | `ebl/transliteration/domain/sign_token_base.py:47` | `NamePart` is a `Token` subclass with no `OneOfTokenSchema` entry; serialising `name_parts` instead of `name_tokens` fails at runtime with no static warning. |
| F6 | **Nit** | 4 files | New `list[...]` / `dict[...]` builtin generics in files that otherwise use `typing.List` / `Dict`. |
| F7 | **Info** | qlty | Three `similar-code` findings and several `function-parameters` / `return-statements` findings remain open. qlty check itself is green ("No blocking issues"). |

---

## Summary

PR #743 renames `ebl/transliteration/domain/atf_parsers/lark_parser/` to `atf_grammar/` so that the sibling module `lark_parser.py` is no longer shadowed by a namespace package, then fixes the type-checker, lint and file-size debt that became visible once the checkers could actually see the ATF parser. It also carries three design fixes found in earlier review rounds: `TokenVisitor` no longer returns a fake empty `result`, `NameParts` no longer mixes two token types in one domain array, and `GET /signs/transliteration/{line}` now returns 422 instead of 500 on unparsable input.

The core change is sound and well executed. The renamed grammar directory is a pure `R100` rename (all sixteen `.lark` files byte-identical), the `.lark` files use relative `%import`, and all eight path references are updated. Behaviour-preservation is good throughout: the `nameParts` wire format round-trips unchanged, all 72 `Museum` entries are value-identical to master, and `pydash.flow(set_enclosure_type, set_language)` was correctly unrolled to `set_language(set_enclosure_type(tokens))` in `LineVariant`.

All existing GitHub feedback was fetched and is accounted for below. The PR is blocked only by Fabdulla1's outstanding `CHANGES_REQUESTED` review — every CI check now passes.

### Gates run

| Gate | Command | Result |
| --- | --- | --- |
| format | `poetry run ruff format --check ebl` | **pass** — 844 files already formatted |
| lint | `poetry run ruff check ebl` | **pass** — all checks passed |
| type (pyre — the gate CI enforces) | `poetry run pyre check` | **pass** — No type errors found |
| type (pyright) | `pyright@1.1.411` on the 101 changed `.py` files | **pass** — 0 errors, 0 warnings, 0 informations |
| type (mypy) | `mypy <101 changed files> --ignore-missing-imports` | **pass** — no issues found in 101 source files |
| tests | `pytest -q` (full suite) | **pass** — 4385 passed, 2 skipped, 1 xfailed in 361 s |
| coverage | `pytest --cov=<60 changed source modules> --cov-report=term-missing` | 98% overall; **0 uncovered lines among lines this PR adds or changes** (verified line-by-line, see below) |
| flake8 | `flake8 <changed> --max-line-length=120` | **pass** — 0 errors |
| lint-md | `markdownlint-cli2 "**/*.md" '#.venv/**' '#.pytest_cache/**'` | **pass** — 0 errors |
| 250-line cap | every changed `.py` file | **pass** — no file over 250 lines |
| line length | every changed `.py` file | **pass** — no line over 120 characters |
| runtime | live `waitress-serve` against a local MongoDB, affected routes exercised | **pass** — see Reproduction Steps |

Coverage was verified against the hard gate ("any line you add, modify, move, or relocate must end at 100%") by intersecting the `--cov-report=term-missing` line numbers with the added/changed line numbers from `git diff -U0 master..HEAD` for each of the 20 modules that still report misses. The intersection is empty for every one of them: all 63 uncovered lines sit at unchanged positions with unchanged content. All 60 changed source modules were measured — none was silently absent from the report.

### Dev container check

**No dev container or tooling configuration is touched by this PR.** `git diff --name-status master..HEAD` over `.devcontainer/**`, `Dockerfile*`, `docker-compose*`, `.github/**`, `Taskfile*`, `pyproject.toml`, `poetry.lock`, `.vscode/**`, `.claude/**`, `.markdownlint*`, `mypy.ini`, `ruff.toml` and `.pyre_configuration` returns nothing. The only non-`.py`, non-`.lark` changes are `docs/ebl-atf.md` (grammar-path rename) and the seven `TASK-743-*.md` files in F1.

### Data hard gate — different data types never intermix in one array

The PR's `NameParts` change is a genuine fix and passes the gate at the domain level.

- **Before:** `NameParts = Sequence[Union[ValueToken, BrokenAway]]` — two types in one array, and every reader had to `isinstance`-probe to work out a sign's name.
- **After:** `NameParts = Sequence[NamePart]` — one type. `NamePart` carries the token together with the text it contributes, and classification happens exactly once, in `name_contribution_of`, at construction. `_validate_name_contribution` pins the invariant so a hand-built `NamePart` cannot lie about its contribution, and `convert_name_parts` is idempotent so `attr.evolve` round-trips cleanly.

Two observations, neither of which I am raising as a defect:

1. The **wire** `nameParts` array is still a `OneOfTokenSchema`-discriminated mixed array of `ValueToken` and `BrokenAway`. This is deliberate and documented in the PR description as a backward-compatibility requirement, and I verified the format is unchanged (see Reproduction Steps). It is also consistent with the codebase-wide polymorphic token stream (`parts`, `content`), so the alternative would be a much larger change than this PR. Flagging it only so the decision is on the record.
2. `sign_unicode_lookup.py:21` reads `name_parts[0].name_contribution` where master read `name_parts[0]._value`. These differ only when the first name part is a `BrokenAway` (`""` vs `"["`) — both fail to match any sign, so the observable behaviour is identical. Confirmed live with `[k]u-nu`, which returns only the `nu` match on both.

No shared-id-space invariant is affected: the split is within one sign's name, not across two id namespaces.

---

## Findings

### F1 — Seven task-tracking `.md` files are committed on the branch

**Severity: Blocker.** `git diff --name-status master..HEAD` shows these as `A`, and `git ls-files 'TASK-*'` confirms they are tracked:

```text
A  TASK-743-commit-log.md
A  TASK-743-commit-todo.md
A  TASK-743-fix-log.md
A  TASK-743-fix-todo.md
A  TASK-743-log.md
A  TASK-743-review.md
A  TASK-743-todo.md
```

These are working artefacts, not deliverables, and they would land on `master` on merge. Commit `55827af1` ("Remove the PR #743 task tracking docs") removed them once; the three later commits reintroduced them. `TASK-743-review.md` alone is 34 KB.

**Recommendation:** `git rm` all seven (they will need to stay out of subsequent commits on this branch too). Nothing else in the PR adds a `.md` file — `docs/ebl-atf.md` is an existing file modified for the grammar-path rename, which is correct.

### F2 — `cast` asserts a type `pydash.group_by` does not return

**Severity: Medium.** `ebl/corpus/domain/chapter.py:212-224`:

```python
def _get_extant_lines(self, manuscript_id: int) -> Mapping[ManuscriptLineLabel, ExtantLine]:
    grouped = pydash.group_by(
        (ExtantLine.of(line, manuscript_id) for line in self.lines if ...),
        lambda extant_line: extant_line.label,
    )
    return cast(Mapping[ManuscriptLineLabel, ExtantLine], grouped)
```

`pydash.group_by` returns `Dict[key, List[value]]`, so the runtime value is `Mapping[ManuscriptLineLabel, Sequence[ExtantLine]]`. Two independent confirmations in the tree:

- `ebl/tests/corpus/test_chapter.py:433-439` asserts `chapter.extant_lines == {siglum: {labels: [ExtantLine(...)]}}` — a list.
- `ebl/corpus/web/extant_lines.py:22` declares `fields.Dict(Labels(), fields.Nested(ExtantLineSchema, many=True))` — `many=True`, i.e. a list.

Master carried the same wrong annotation, but without a `cast`; once the checkers could see this code they would have flagged it. Adding the `cast` records the wrong type as intentional and silences all three checkers at once. That is a suppression in everything but name, and it contradicts the PR's own stated rule ("All are now fixed structurally — no `# type: ignore`, no `# pyright: ignore`, no configuration change"). The declared type propagates to the public `Chapter.extant_lines` property, so every consumer now reads a type the value never has.

No runtime impact today — the schema handles the real shape.

**Recommendation:** annotate the truth and drop the cast:

```python
def _get_extant_lines(self, manuscript_id: int) -> Mapping[ManuscriptLineLabel, Sequence[ExtantLine]]:
    return pydash.group_by(...)
```

and widen `extant_lines` at line 139 to `Mapping[Siglum, Mapping[ManuscriptLineLabel, Sequence[ExtantLine]]]`.

### F3 — `TransliterationQueryEmpty` silently lost `frozen=True`

**Severity: Low.** `ebl/transliteration/domain/transliteration_query.py:196-204`:

```diff
-@attr.s(auto_attribs=True, frozen=True)
+@attr.s(auto_attribs=True)
 class TransliterationQueryEmpty(TransliterationQuery):
     string: str = ""
-    visitor: TokenVisitor = TokenVisitor()
+    visitor: Optional[SignsCollectingVisitor] = None
```

The class is now mutable. Nothing in the PR requires this: the `visitor` default change from a shared mutable `TokenVisitor()` singleton to `None` is a good fix in its own right and is orthogonal to `frozen`. The inherited `__attrs_post_init__` is still overridden with `pass` at line 203, which is the only reason `frozen=True` worked on master, and it still works — I verified by restoring the decorator locally:

```text
frozen construction OK: Type.UNDEFINED ''
immutable as expected: FrozenInstanceError
```

**Recommendation:** restore `frozen=True`. If it was dropped deliberately, say why in the PR description — a value object quietly becoming mutable is the kind of change that is invisible in review.

### F4 — `get_unicode_from_atf` is the one delegate the memoizing repository does not memoize

**Severity: Low.** `ebl/signs/infrastructure/memoizing_sign_repository.py:17-25`:

```python
self._find_signs_by_order = pydash.memoize(delegate.find_signs_by_order)
self._get_unicode_from_atf = delegate.get_unicode_from_atf
```

Every other delegate in this class is wrapped in `pydash.memoize`; this one is a bare bound method, so `MemoizingSignRepository.get_unicode_from_atf` re-parses on every call. That may well be intentional — the key space is unbounded ATF strings — but it is invisible at the call site and reads as an oversight next to the line above it.

Context: `MemoizingSignRepository` is currently only constructed in tests (`ebl/app.py:104` wires `MongoSignRepository` directly), so there is no production impact either way.

**Recommendation:** memoize it for consistency, or leave it and add a one-line comment saying why it is excluded.

### F5 — `NamePart` is a `Token` with no schema

**Severity: Low.** `NamePart` (`ebl/transliteration/domain/sign_token_base.py:47`) subclasses `Token`, but `OneOfTokenSchema` has no entry for it — `grep -rn "NamePart" ebl/transliteration/application/` returns nothing. The wire format is preserved precisely because `_dump_name_parts` goes through `named_sign.name_tokens` (unwrapped) rather than `named_sign.name_parts`.

That works, but it leaves a trap: `name_parts` is the natural-looking attribute, it is typed `Sequence[NamePart]` where `NamePart` *is* a `Token`, and passing it to any token schema type-checks fine and fails only at runtime. `enclosure_updater.py:68` already reaches for `name_tokens` correctly, so the convention exists — it just isn't enforceable.

**Recommendation:** either make `NamePart` not a `Token` (it only needs to delegate, not to be one), or add a test that asserts `OneOfTokenSchema().dump(named_sign.name_parts, many=True)` raises, so the constraint is pinned rather than remembered.

### F6 — Mixed builtin/`typing` generics

**Severity: Nit.** Four newly annotated locals use PEP 585 builtin generics in files that otherwise import from `typing`:

- `ebl/corpus/domain/create_alignment_map.py:23` — `self._result: list[Optional[int]] = []`
- `ebl/fragmentarium/application/matches/create_line_to_vec.py:155` — `line_to_vec_intermediate_result: list[LineToVecEncoding] = []`
- `ebl/corpus/application/lines_updater.py:17` — `self._lines: list[Line] = []`
- `ebl/corpus/domain/chapter_query.py:15` — `matching_colophon_lines: dict[int, Sequence[TextLine]] = {}`

All four sit next to `Sequence`, `List` or `Dict` imported from `typing` in the same file. Correct on the supported Python versions (3.11/3.12/pypy-3.11); just inconsistent with the surrounding style.

**Recommendation:** use `List` / `Dict` to match each file, or leave as-is if the project intends to migrate to builtin generics — but then do it as its own change.

### F7 — Outstanding qlty maintainability findings

**Severity: Info.** The `qlty check` status is green ("No blocking issues"), so none of these gate the merge, and khoidt's comment on 25 Aug already acknowledged the duplication findings as open. For completeness, what is still reported:

| Finding | Location | Status at `6926bc1a` |
| --- | --- | --- |
| `similar-code`, 17 lines, mass 76 (x2) | `named_signs.py:33` and `:85` | Still present — `Reading.of` / `of_name` and `Logogram.of` / `of_name` are near-identical |
| `similar-code`, 19 lines, mass 142 | `parse_word_cases_4.py:63` | Still present |
| `similar-code`, 46 lines, mass 240 (x2) | `lemmatized_fragment_text.py:111`, `transliterated_fragment_lines.py:70` | Still present — two deliberately parallel test fixtures |
| `function-parameters` count 6 | `named_signs.py` `of` / `of_name` | Pre-existing public API signatures, moved not changed |
| `function-parameters` count 6 | `named_signs.py:25` `_create` | **Fixed** — `NamedSignArguments` reduces `_create` to one argument |
| `function-parameters` count 7–9 | `test_named_sign_{logogram,number,reading}.py` | Parametrised test signatures |
| `return-statements` count 7 | `retrieve_annotations_helpers.py:53` | Still present |

**Recommendation:** the two `named_signs.py` duplications are the only ones worth acting on — `Reading` and `Logogram` differ only in return type, so a shared helper would clear both. The rest are test fixtures and public signatures; I would leave them and say so on the PR rather than churn the API.

---

## Existing PR feedback — disposition

Fetched via `gh api repos/ElectronicBabylonianLiterature/ebl-api/pulls/743/reviews`, `.../pulls/743/comments` and `.../issues/743/comments`: 8 reviews, 19 inline comments, 2 conversation comments. No PR whose branch was merged into this one carries further feedback — the branch is a straight split out of #740.

### sourcery-ai[bot]

| Finding | Disposition |
| --- | --- |
| `TextLine.merge` return type `L` + `cast(L, ...)` is unsound for `TextLine` subclasses (`text_line.py:153`) | **Addressed, and correctly.** The PR adds `@final` to `TextLine` (`text_line.py:70`) — the only change to that file. With `TextLine` final, `L` can never be a proper subclass of it, so the `cast` is sound. `grep` confirms no subclass of `TextLine` exists. The `merge` body itself is unchanged from master. |
| Reviewer's Guide describes `_StartParser.parse` as taking "an explicit optional start parameter" | **Stale, as khoidt noted.** The final implementation drops the parameter entirely: `def parse(self, text: str) -> Tree`. I verified no caller passes `start=` to a `_StartParser` instance — every `start=` call site targets a real `Lark` object (`LINE_PARSER`, `CHAPTER_PARSER`, `MANUSCRIPT_PARSER`, `RECONSTRUCTED_LINE_PARSER`). Behaviour is pinned by `test_parse_uses_default_start`. |

### Fabdulla1 (CHANGES_REQUESTED — still the only thing blocking merge)

| Point | Disposition |
| --- | --- |
| The `/signs/transliteration` 422 fix is not in the branch | **Now present and verified live.** `ebl/signs/web/signs.py:61-65` catches `LINE_PARSE_ERRORS` and raises `DataError`; `ebl/tests/signs/test_transliteration_route.py` covers valid, unparsable and erasure input. Confirmed against a running server: `$$$` → **422**, `°nu : ši\ku°` → **200**. |
| 169-character URL line at `annotations_service.py:120` | **Fixed.** The URL is now split across three comment lines; no line in the file exceeds 100 characters. |
| Five `PRIVATE_COLLECTION_*` entries changed `.value` shape during the museum split | **Fixed and independently verified.** All five are back to 3-tuples via `MuseumEntryWithoutUrl` (`museum_entries_m_s.py:104-129`). I compared `(value, museum_name, city, country, url)` for all 72 members against master's module: **72 entries, 0 differing.** |
| Add a focused test for `SignsVisitor.reset()` | **Addressed.** `test_reset_clears_accumulated_signs` and `test_reset_lets_a_visitor_be_reused` (`test_signs_visitor.py:118,131`). |
| Add a test for `_StartParser.parse(start=...)` | **Correctly declined.** The parameter no longer exists; khoidt's explanation is accurate and I verified it independently. Worth resolving explicitly on the PR so the `CHANGES_REQUESTED` can be cleared. |
| "The qlty comments just need to be addressed" | **Partly.** See F7 — `_create` is fixed, the duplication findings remain, and qlty's own check is green. |

### github-advanced-security[bot] / CodeQL — all five fixed at `6926bc1a`

| Alert | Location at time of report | Status at HEAD |
| --- | --- | --- |
| Unnecessary lambda (919) | `signs_transformer.py:27` — `tree.scan_values(lambda value: bool(value))` | **Fixed** — now `tree.scan_values(bool)` |
| Statement has no effect (917, 918) | `token_base.py:98,102` — `def reset(self) -> None: ...` | **Fixed** — now `raise NotImplementedError` |
| Statement has no effect (921, 922) | `legacy_transformer_base.py:38,40` — `def _transform_tree(...) -> Branch: ...` | **Fixed** — now `@abstractmethod` + `raise NotImplementedError` |

The `Analyze (python)` and `CodeQL` checks both pass on `6926bc1a` and no new alerts were posted, corroborating this.

### qltysh[bot]

See F7. Check status: **pass, "No blocking issues."**

### CI checks at `6926bc1a`

All green: `Test Python 3.11` (x2), `Test Python 3.12` (x2), `Test Python pypy-3.11` (x2), `CodeQL`, `Analyze (python)`, `GitGuardian scan` (x2), `GitGuardian Security Checks`, `qlty check`. `Sourcery review` reports `skipping`. Combined status rollup: `success`. `mergeable_state` is `blocked` **solely** because of Fabdulla1's outstanding `CHANGES_REQUESTED` review, not because of any check.

---

## Things I checked that are fine

Recorded so they don't get re-litigated:

- **Grammar rename is a pure rename.** All sixteen `.lark` files are `R100` (100% similarity); the `.lark` sources use relative `%import .name` so their contents are untouched; all eight path references updated (`lark_parser.py` x4, `legacy_atf_converter.py`, `docs/ebl-atf.md`, tests).
- **`check_errors` `any(errors)` → `if errors`.** `create_transliteration_error_data` always returns a truthy dict, so this is equivalent — and strictly more correct.
- **`LINE_PARSE_ERRORS` == `(*PARSE_ERRORS, TransliterationError, ExtentLabelError)`,** exactly the tuple both call sites open-coded before.
- **`LineVariant.reconstruction` converter order preserved.** `pydash.flow(set_enclosure_type, set_language)` applies `set_enclosure_type` first; `prepare_reconstruction` does `set_language(set_enclosure_type(tokens))` — same order. Easy thing to get backwards; it isn't.
- **`markup.LanguagePart.tokens` converter `tuple` → `convert_token_sequence`** is a no-op rename: `convert_token_sequence` is literally `tuple(tokens)`.
- **`ChapterVisitor.visit` gaining `@singledispatchmethod`** aligns the base with all three subclasses (`ChapterUpdater`, `TextValidator`, `ManuscriptReferenceInjector`), which already declared their own `@singledispatchmethod` and use `@visit.register`. All call sites pass the item positionally.
- **`QueryArgs(TypedDict)` losing `= ""` defaults** is correct — `TypedDict` never honoured them.
- **`get_scopes(prefix: Optional[str] = "")` → `prefix: str = ""`** is safe: no caller passes `None` (all six call sites pass either nothing or string literals).
- **`MemoizingSignRepository.search_composite_signs` narrowing to `sub_index: int`** matches the ABC, which already declared `int` on master. The only caller (`sign_search.py:26`) always supplies it.
- **`SignRepository` gaining two abstract methods** (`find_signs_by_order`, `get_unicode_from_atf`) is consistent — the one implementation that needed updating (`MemoizingSignRepository`) was updated, and `TestSignRepository` inherits from `MongoSignRepository`.
- **`TokenVisitor` losing `result` and the class-level `_standardizations = []`** removes a shared mutable class attribute — a real latent bug, not just a typing cleanup.
- **`__all__` re-export facades are complete for everything still imported.** I compared each split module's public names on master against what resolves at HEAD: `tokens`, `sign_tokens`, `enclosure_visitor` and `retrieve_annotations` are complete; `mongo_sign_repository` drops `ValueSchema`, `FosseySchema`, `LogogramSchema`, `SignListRecordSchema`, `SortKeysSchema` and `chapter_schemas` drops three private helpers — nothing imports any of them from the old path, matching the PR description.
- **`auth0.py` closure change.** Capturing `req.auth` eagerly instead of holding `req` is safe; `req.auth` is a plain header read.

---

## Severity

| Severity | Count | Findings |
| --- | --- | --- |
| Blocker | 1 | F1 |
| Medium | 1 | F2 |
| Low | 3 | F3, F4, F5 |
| Nit | 1 | F6 |
| Info | 1 | F7 |

No correctness, security or regression defect was found in the shipped code paths. F1 is a repository-hygiene blocker; F2 is a type-correctness defect with no runtime effect.

---

## Reproduction Steps

### F1 — committed `.md` files

```bash
git diff --name-status master...HEAD -- '*.md'
git ls-files 'TASK-*'
```

Both list the same seven `TASK-743-*.md` files.

### F2 — `group_by` returns lists

```bash
poetry run python -c "
import pydash
print(pydash.group_by([1,2,3], lambda x: x % 2))
"
# {1: [1, 3], 0: [2]}
```

and `ebl/tests/corpus/test_chapter.py:433` already asserts the list shape:

```python
assert chapter.extant_lines == {
    manuscript.siglum: {
        manuscript_line.labels: [ExtantLine(manuscript_line.labels, LineNumber(1), True)]
    }
}
```

### F3 — `TransliterationQueryEmpty` is mutable

```bash
poetry run python -c "
from ebl.transliteration.domain.transliteration_query import TransliterationQueryEmpty
e = TransliterationQueryEmpty()
e.string = 'MUTATED'
print(e.string)
"
# MUTATED   (raises FrozenInstanceError on master)
```

Restoring `frozen=True` on line 196 and re-running gives `FrozenInstanceError`, with construction still succeeding.

### Runtime verification (hard gate)

A live server was run against a local MongoDB — `.env` was **not** sourced, because it points `MONGODB_URI` at the production cluster:

```bash
env -u MONGODB_URI -u MONGODB_DB \
  MONGODB_URI="mongodb://127.0.0.1:27017" MONGODB_DB="ebl_review_743" \
  EBL_AI_API="http://localhost:9999" AUTH0_PEM="$(cat auth0_pem.b64)" \
  AUTH0_AUDIENCE="dummy-audience" AUTH0_ISSUER="https://example.invalid/" \
  poetry run waitress-serve --port=8123 --call ebl.app:get_app
```

with two signs (`KU`, `NU`) seeded into an isolated database, which was dropped afterwards.

| Request | Result |
| --- | --- |
| `GET /signs/transliteration/ku-nu` | **200** `[{"unicode": [74054]}, {"unicode": [74177]}]` |
| `GET /signs/transliteration/$$$` | **422** `{"description": "Invalid transliteration: \"$$$\""}` — the fix Fabdulla1 could not find, confirmed on the running service |
| `GET /signs/transliteration/°nu : ši\ku°` | **200** — the erasure line that used to 500 |
| `GET /signs/transliteration/[ku]-nu` | **200** `[{"unicode": [74054]}, {"unicode": [74177]}]` — `NamePart` path with an enclosure |
| `GET /signs/transliteration/ku[r]-nu` | **200** — interleaved `ValueToken, BrokenAway, ValueToken` name parts |
| `GET /signs/transliteration/[k]u-nu` | **200** `[{"unicode": [74177]}]` — matches master's behaviour for a leading `BrokenAway` |
| `GET /signs/all` | **200** `["KU", "NU"]` |
| `GET /signs/KU/neoAssyrianPeriod` | **200** — `find_signs_by_order`, newly on the `SignRepository` interface |
| `GET /signs?value=ku&subIndex=1` | **200** — the `create_dispatcher` path whose generics changed |
| `GET /signs/KU` | **200** — the `svg2png` `cast` path |

### `nameParts` wire format is unchanged

```python
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_line

line = parse_line("1. ku[r]-ra KI[MIN] 1[2] [ku]-nu")
schema = OneOfTokenSchema()
dumped = schema.dump(list(line.content), many=True)
loaded = schema.load(dumped, many=True)

assert schema.dump(loaded, many=True) == dumped     # round-trip stable: True
assert tuple(loaded) == tuple(line.content)         # reload equals original: True
```

The dumped `nameParts` still holds the interleaved `ValueToken, BrokenAway, ValueToken` sequence, and `test_named_sign_reading.py:123` pins it independently by asserting `"nameParts": OneOfTokenSchema().dump(case.name_parts, many=True)` against the raw input tokens.

### Museum values are byte-identical

```bash
git show master:ebl/fragmentarium/domain/museum.py > /tmp/museum_master.py
# import both and compare (value, museum_name, city, country, url) for every member
# -> total: 72 | differing: 0
```

---

## Disposition of the findings (TASK-743-fix2)

All findings were acted on. Working tree only — nothing is committed.

| # | Disposition |
| --- | --- |
| F1 | **Fixed.** All seven `TASK-743-*.md` files removed with `git rm`; `git ls-files 'TASK-*'` is now empty. |
| F2 | **Fixed, and the finding understated the problem.** The `cast` is gone. Correcting the value type exposed that the **key** type was wrong too: `ExtantLine.label` is `Sequence[Label]`, not `ManuscriptLineLabel` (`Tuple[int, Sequence[Label], AbstractLineNumber]`). Both `_get_extant_lines` and the public `extant_lines` property are now `Mapping[Sequence[Label], Sequence[ExtantLine]]`. |
| F3 | **Fixed by restructuring, not by the one-line change the finding proposed.** Restoring `frozen=True` on its own fails pyright: *"A frozen class cannot inherit from a class that is not frozen."* That is why it was dropped, and a one-line revert would have satisfied pyre and mypy while breaking the third checker. The whole `TransliterationQuery` hierarchy is now frozen: `__attrs_post_init__` mutation is replaced by a `string` converter and two `attr.Factory(..., takes_self=True)` defaults for `type` and `regexp`, computed in field order. `TransliterationQueryEmpty` no longer needs its `__attrs_post_init__` override. All three checkers pass. |
| F4 | **Fixed.** `get_unicode_from_atf` is now memoized like every other delegate, with a new `test_get_unicode_from_atf_memoization`. The existing delegation test was kept, not replaced. |
| F5 | **Fixed structurally.** `NamePart` no longer subclasses `Token`; the eleven members that existed only to satisfy the ABC are gone, and passing `name_parts` where tokens are expected is now a type error rather than a silent error payload. The thirteen tests covering the removed members were deleted with the author's approval. |
| F6 | **Fixed, and one more instance found.** The four annotations named in the finding now use `typing.List` / `Dict`. A wider grep found a fifth introduced by this PR — `ebl/tests/factories/fragment.py:76` — now `TypingList[Scope]`, matching that file's existing `TypingSequence` alias (it cannot import `typing.List` plainly because `factory.declarations` exports its own `List`). Two further builtin generics in `lookup_reservations.py:59` and `mongo_sign_repository.py:41` are **pre-existing on master** and untouched by this PR, so they were left alone. |
| F7 | **Acted on where recommended.** `NamedSignWithLeadingSubIndex` in `sign_token_base.py` now carries the shared `of` / `of_name`; `Reading` and `Logogram` inherit them and `named_signs.py` drops from 107 to 69 lines. `Number` keeps its own overrides — its parameter order puts `sub_index` last, and unifying it would break positional call sites in `signs_transformer.py:89` and `token_schemas_signs.py:103`. The remaining qlty items are left deliberately: `parse_word_cases_4.py` and the two fragment-text factories are parallel fixtures whose duplication is what makes each case readable in isolation, and the `function-parameters` / `return-statements` findings were anchored to older commits and no longer hold at HEAD. |

### F5 — resolved structurally

The finding assumed a `NamePart` reaching `OneOfTokenSchema` would raise. It does not — it returns `[(None, {'_schema': 'Unsupported object type: NamePart'})]`, so the mistake would put an error object into a response body rather than fail loudly. That made the structural option the right one, and it was taken.

Every production consumer of `name_parts` was enumerated first: only `.token`, `.name_contribution` and `.value` are used (`sign_unicode_lookup.py:21` and three properties on `NamedSign`). The other eleven members were dead in production, present only to satisfy the `Token` ABC. `NamePart` is now a plain frozen attrs class with `token`, `name_contribution`, `of` and `value`.

Thirteen tests covering the removed members were deleted. Two replaced them: `test_converting_name_parts_is_idempotent`, which pins the invariant that actually protects `attr.evolve` (the deleted `test_wrapping_is_idempotent` asserted double-wrapping, which is not that invariant), and `test_a_name_part_is_not_a_token`.

Pyre then caught a genuine follow-on: `convert_name_parts` declared `Iterable[Token]`, which could no longer accept the already-wrapped parts `attr.evolve` feeds back through the converter. Declared honestly as `NamePartInput = Union[Token, NamePart]`. The union lives only in the converter's parameter; the stored `name_parts` stays `Tuple[NamePart, ...]` — one type per array, as the data hard gate requires.

## Recommendation

**Request changes** — one blocker, one type-correctness fix, then this is good to merge.

**Before merge:**

1. **F1** — remove the seven `TASK-743-*.md` files from the branch. (Blocker.)
2. **F2** — fix the `extant_lines` annotation and drop the `cast` in `chapter.py:224`.

**Worth doing in the same pass (small, low-risk):**

1. **F3** — restore `frozen=True` on `TransliterationQueryEmpty`.
2. **F4** — memoize `get_unicode_from_atf`, or comment why not.
3. **F5** — pin the `name_parts` / `name_tokens` serialisation constraint with a test.

**Optional / can be deferred:**

1. **F6** — align the four `list[...]` / `dict[...]` annotations with each file's existing style.
2. **F7** — collapse the `Reading` / `Logogram` `of` / `of_name` duplication in `named_signs.py`; reply on the remaining qlty items rather than churning test fixtures and public signatures.

**Also:** ask Fabdulla1 to re-review — every point they raised is now either fixed or answered, and their `CHANGES_REQUESTED` is the only thing keeping `mergeable_state` at `blocked`.

**Housekeeping:** the review artefacts for this task (`TASK-743-review2-todo.md`, `TASK-743-review2-log.md`, `TASK-743-review2-review.md`) are untracked and must be deleted before the PR is merged, along with the seven files in F1.
