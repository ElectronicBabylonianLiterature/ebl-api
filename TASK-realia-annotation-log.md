# TASK-realia-annotation — Work Log

## Branch

`add-realia-annotation-api`, created from `master` at `670a1ce5`.

## Investigation

`grep -rn "named_entities" ebl/` gives these serialization points:

| Location | Role |
| --- | --- |
| `application/named_entity_schema.py` | API + persistence entity schemas |
| `application/fragment_schema.py:109` | nested `namedEntities` field |
| `infrastructure/mongo_fragment_repository.py` | `update_field` projection |
| `domain/fragment.py:162,258` | attribute, `set_named_entities` |
| `transliteration/domain/text.py:250` | builds the token to ids map |
| `transliteration/domain/text_line.py:156` | writes `token.named_entities` |
| `transliteration/application/token_schemas.py` | `word.named_entities` |
| `web/named_entities.py` | GET / POST resource |

`FragmentSchema` is used for **both** Mongo persistence
(`mongo_fragment_repository_base.py:23`) and the API DTO (`web/dtos.py:17`), so
the single `named_entities` nested field covers both. `word.named_entities` is
already a plain `List[str]` of ids, so realia ids need no token-schema change.

## Decisions

1. **Polymorphic schema via `marshmallow_oneofschema.OneOfSchema`.** Already a
   repo idiom (`transliteration/application/one_of_line_schema.py`).
   `get_data_type` is overridden to dispatch on the *presence* of `realiaId`
   rather than on a discriminator value, and `_dump` is overridden so the base
   class does not inject its `type_field` into the output.

2. **Both `type` and `realiaId`, or neither, is a `ValidationError`.**
   `get_data_type` raises when `("realiaId" in data) == ("type" in data)`.
   `OneOfSchema._load` forwards `unknown` to the concrete sub-schema, so
   `unknown=RAISE` still rejects extra keys such as the client-derived `tier`
   and `name`.

3. **`to_named_entity()` kept as the method name on both span classes.**
   `Fragment` calls it uniformly over the union; in this codebase
   `named_entities` already denotes the merged annotation id list on a word, so
   the name stays accurate.

4. **Referential integrity: implemented.** `NamedEntityResource.on_post`
   resolves every *distinct* `realia_id` in the payload through
   `RealiaRepository.find_by_realia_id` before the update. Cost is one indexed
   lookup per distinct realia id (`realiaId` carries a unique index, see
   `mongo_realia_repository.create_indexes`), and a fragment carries a handful
   of realia spans at most, so the per-request cost is acceptable. An unknown id
   raises `DataError` (422) rather than the repository's `NotFoundError` (404),
   since the missing resource is in the request body, not the route.

5. **`ValidationError` mapped to `DataError`.** Previously a malformed
   annotations payload escaped `on_post` as an unhandled `ValidationError` and
   became a 500. It now returns 422, matching `fragment_script.py` and
   `fragment_date.py`.

## Changes

- `domain/named_entity.py` — `REALIA_ID_PATTERN`, `RealiaEntity`,
  `RealiaAnnotationSpan`, and the `AnnotationEntity` / `AnnotationSpan` unions.
- `application/named_entity_schema.py` — `RealiaEntitySchema`,
  `RealiaAnnotationSpanSchema`, and the polymorphic `AnnotationEntitySchema` /
  `AnnotationSpanSchema`.
- `application/fragment_schema.py` — nests `AnnotationEntitySchema`.
- `application/fragment_updater.py`, `domain/fragment.py`,
  `transliteration/domain/text.py` — union aliases in the signatures.
- `web/named_entities.py` — polymorphic load/dump, realia existence check,
  `DataError` on invalid payloads.
- `web/bootstrap.py` — injects `context.realia_repository`.
- Tests: new `tests/fragmentarium/conftest.py` and
  `test_named_entity_route_validation.py`; extended `test_named_entities.py`,
  `test_named_entity_schemas.py`, `test_named_entity_route.py`.

## Gate results

| Gate | Command | Result |
| --- | --- | --- |
| Format | `ruff format --check ebl` | 737 files already formatted |
| Lint | `ruff check ebl` | All checks passed |
| Types (pyre) | `pyre check` | No type errors found |
| Types (pyright) | `pyright <touched files>` | 0 errors, 0 warnings |
| Tests | `pytest` | 3874 passed, 2 skipped, 1 xfailed |
| Coverage | changed lines | 100% on every added/modified line |
| Markdown | `markdownlint-cli2` | clean |

### Pylance `Unknown` cascade — root cause and permanent fix

The IDE reported errors the CLI did not, e.g. `Type of "routes" is
"list[Unknown]"` (`reportUnknownVariableType`) in `web/bootstrap.py`. That rule
only fires in `strict`, and the underlying cause was not the code:

```text
reportMissingImports      | Import "falcon" could not be resolved
reportUnknownVariableType | Type of "make_fragment_pager_resource" is partly unknown
reportUnknownMemberType   | Type of "add_route" is unknown
```

When `falcon` / `marshmallow` do not resolve, every resource type collapses to
`Unknown`, and `routes` — a list of those resources — becomes `list[Unknown]`.
With the venv resolved, `bootstrap.py` drops from 170 strict errors to 0.

Pylance was resolving against the **system** interpreter, not `.venv`:
`.vscode/settings.json` carried `"python-envs.defaultEnvManager":
"ms-python.python:system"` (the recent Python Environments extension — this is
why the problem "started recently"). `.vscode/` is gitignored, and the repo
pinned **no** pyright configuration, so every developer's Pylance used a
different, drifting default.

Permanent fix — pin the configuration in version control so Pylance and the CLI
resolve identically for everyone:

- **`pyrightconfig.json`** (new, tracked): pins `venvPath` / `venv` to `.venv`,
  `pythonVersion`, and `typeCheckingMode: standard`. Pylance and
  `npx pyright` now read the same file; the gate command needs no flags.
- **`.vscode/settings.json`** (local, gitignored): env manager switched to
  `venv`, and `python.defaultInterpreterPath` set to the project `.venv`.

`typeCheckingMode` is deliberately `standard`, not `strict`: `marshmallow`,
`attrs`, `pydash` and `factory_boy` ship no type information, so strict reports
~24,319 `Unknown` cascades repo-wide (vs 1,347 at standard) — unachievable
without hand-writing stubs for four libraries.

### Pyright / Pylance

The IDE surfaced Pylance errors; Pylance runs the Pyright engine, so
`npx pyright` reproduces them. Across the touched files Pyright reported 18
errors: 4 in the new schema, 3 in the rewritten web resource, and 11 pre-existing
in files this change edits. All 18 are fixed, none suppressed:

- `named_entity_schema.py` — import `OneOfSchema` from its submodule (the package
  `__init__` does not re-export it, so the top-level import is flagged private);
  widen `type_schemas` to the base `Mapping[str, Union[Type[Schema], Schema]]` to
  satisfy `reportIncompatibleVariableOverride`; `cast(dict, ...)` the
  `many=False` dump result.
- `named_entities.py` — `cast(dict, ...)` and
  `cast(List[AnnotationSpan], ...)` around marshmallow dump/load (both typed as
  `Any`); read the user via `req.context["user"]` (Falcon `Context` has no static
  `user` attribute).
- `fragment_updater.py` — `cast(dict, schema.dump(...))` before dict-unpack.
- `fragment.py` — replace the `@category.validator` decorator with a module-level
  `_validate_genre_category`, and `converter=tuple` with a typed
  `_to_entity_tuple`; Pyright cannot model either dynamic `attr.ib` form.
- `text.py` — same validator conversion for `Text.lines`; `cast` each `Line`
  subtype in the `labels` handler lambdas; index `TextLemmaAnnotation` with
  `LineIndex(index)` rather than a bare `int`.

All refactors are behaviour-preserving and confirmed by the full suite (3874
passed) and `pyre check`.

## Line-count gate: modules split

`domain/fragment.py` and `transliteration/domain/text.py` were already over the
250-line hard gate on `master` (284 and 266); the Pyright fixes pushed them
further. Both are now split under 250, with the public import surface preserved:

- `domain/fragment_metadata.py` (new) holds the fragment value objects
  (`Acquisition`, `Genre`, `Script`, `Introduction`, `Notes`, `Measure`,
  `UncuratedReference`, `DossierReference`, `MarkupText`, `NotLowestJoinError`,
  `parse_markup_with_paragraphs`, `to_entity_tuple`). `fragment.py` (292 -> 207)
  re-imports them, so `from ebl.fragmentarium.domain.fragment import Genre` etc.
  still resolve. `Period` / `PeriodModifier` / `DossierReference` /
  `NotLowestJoinError` use the explicit `import X as X` re-export form so the
  names stay part of `fragment.py`'s public surface without a spurious F401.
- `transliteration/domain/labels_validator.py` (new) holds `LabelsValidator`
  and `_validate_extents`. `text.py` (285 -> 195) imports `_validate_extents`
  back for the `Text.lines` validator, and keeps re-exporting `TranslationLine`
  (a name external code imports from `text`). `LabelsValidator.__init__` types
  its argument with a local `HasLabels` `Protocol` instead of a
  `TYPE_CHECKING` forward reference to `Text`, which both avoids the circular
  import and keeps every line runtime-coverable.

`pyre check` validates the whole repo, so it is the safety net that every
re-export still resolves (it caught the one `TranslationLine` case). The
relocated `Acquisition.of` was uncovered on `master`; it is now covered by
`tests/fragmentarium/test_fragment_metadata.py` (a new file, so the pre-existing
508-line `test_fragment.py` is left untouched). Full suite: 3876 passed.

The Taskfile defines `format` as `ruff format --check`, `lint` as `ruff check`
and `type` as `pyre check`. The copilot instructions also name `flake8` and
`mypy`; both were run on the changed modules as a cross-check:

- `flake8 --max-line-length=120` reports only `E203 whitespace before ':'` at
  `domain/fragment.py:253`. That line is untouched by this change and reports
  identically on `master`. `E203` is the known `flake8`/`ruff format`
  incompatibility (the formatter requires the space in a slice); fixing it would
  break the mandatory `task format` gate, and lint configuration must not be
  edited. Every other file is clean.
- `mypy --ignore-missing-imports` reports the same 26 errors on
  `domain/fragment.py` before and after this change, including the
  `converter=tuple` `_T_co` complaint at line 261. This change introduces **zero
  new mypy errors**. The repository is not mypy-clean on `master`
  (41 errors across 19 files, in `corpus`, `bibliography`, `web/dtos.py` and
  others); clearing them is out of scope for this task.

## Two pre-existing files exceed the 250-line gate

`domain/fragment.py` (284) and `transliteration/domain/text.py` (266) were
already over the limit on `master` and this change does not grow either — both
edits are one-for-one type-annotation replacements. `tests/conftest.py` (740) is
also over; the new fixtures were placed in a new
`tests/fragmentarium/conftest.py` (55 lines) rather than growing it. Every file
added or grown by this change is under 250 lines.

## Before merge

Remove `TASK-realia-annotation-todo.md` and `TASK-realia-annotation-log.md`.

## Uniqueness of tags and realia

A duplicate is the **same value on the same span**: the same tag type on a token
range, or the same `realiaId` on a token range. Duplicates are silently dropped,
keeping the first occurrence, and the request returns 200.

Deliberately still allowed, because they are meaningful annotations:

- the same realia at a *different* token range (a tablet can mention one object
  in two places), and likewise the same tag at a different range;
- two *different* tags on one range;
- a tag and a realia on one range — that is the point of the feature.

`annotation_key` builds `(kind, value, frozenset(span))`, so span **order**
cannot defeat deduplication: `["Word-2", "Word-3"]` and `["Word-3", "Word-2"]`
are the same range.

Deduplication lives in `Fragment.set_named_entities`, not only in the web layer,
so no duplicate can enter fragment state through any caller.

### Conflicting ids are rejected (422), not dropped

`_create_annotation_spans` keys a dict by `entity.id`. Two *different*
annotations sharing an id would silently collapse into one and fuse their spans
— data corruption, not a duplicate. `_validate_unique_ids` therefore raises
`DataError` (422) and writes nothing.

The dedupe runs **before** the id check, so an *exact* duplicate that repeats the
same id is still dropped silently, as specified, and only genuinely conflicting
ids reach the check.
