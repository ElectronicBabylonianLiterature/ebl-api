<!-- markdownlint-disable MD013 -->

# TASK-743-fix2 — Work Log

## Step 1 — Task set-up

- Re-read `.github/instructions/copilot.instructions.md` before starting.
- New task (addressing the findings of the review just completed), so new TODO and log created before any change — the previous task's files do not carry forward.
- Starting state: working tree clean apart from three untracked review artefacts (`TASK-743-review2-{todo,log,review}.md`). HEAD `6926bc1a`.

## Step 2 — F1: committed task files removed

- `git rm` on the seven tracked `TASK-743-*.md` files. `git ls-files 'TASK-*'` now returns nothing. Deletions are **staged only — not committed.**

## Step 3 — F2: `extant_lines` typing

- Dropped `cast(Mapping[ManuscriptLineLabel, ExtantLine], grouped)` and returned `pydash.group_by(...)` directly.
- While fixing the value type, pyright revealed the **key** type was wrong too: `ExtantLine.label` is `Sequence[Label]`, not `ManuscriptLineLabel` (`Tuple[int, Sequence[Label], AbstractLineNumber]`). The original annotation was wrong on both sides. Correct type is `Mapping[Sequence[Label], Sequence[ExtantLine]]`, applied to both `_get_extant_lines` and the public `extant_lines` property. `Label` imported; `cast` import dropped (no longer used in the module).

## Step 4 — F4: memoization

- `self._get_unicode_from_atf = pydash.memoize(delegate.get_unicode_from_atf)`.
- Added `test_get_unicode_from_atf_memoization` asserting `first is second`. The existing `test_get_unicode_from_atf_delegates` was **kept**, not replaced — no test was removed.

## Step 5 — F6: builtin generics

- `create_alignment_map.py`, `create_line_to_vec.py`, `lines_updater.py`, `chapter_query.py` switched to `typing.List` / `Dict` with the matching imports.
- A wider grep found a fifth instance introduced by this PR: `ebl/tests/factories/fragment.py:76`. That file already aliases `typing.Sequence` as `TypingSequence` because `factory.declarations` exports its own `List`/`Sequence`, so `List as TypingList` was added and the annotation is now `TypingList[Scope]`.
- Two further builtin generics exist in `lookup_reservations.py:59` and `mongo_sign_repository.py:41`, but both are **pre-existing on master** and untouched by this PR, so they were left alone.

## Step 6 — F5: `NamePart` serialisation constraint

- Investigated the structural option first (making `NamePart` not a `Token`). Discovered the failure mode is **worse than reported**: `OneOfTokenSchema().dump(name_parts, many=True)` does not raise — it silently returns `[(None, {'_schema': 'Unsupported object type: NamePart'})]`, which would go straight into a response body.
- The structural fix would delete the twelve delegation tests in `test_name_part.py`, and removing tests requires explicit user approval, so it was **not** done. Escalated to the user instead.
- Implemented the sanctioned alternative: two tests pinning the constraint — one asserting `NamedSignSchema` serialises `name_tokens`, one asserting a `NamePart` is not serialisable as a token.

## Step 7 — F7: `Reading` / `Logogram` duplication

- Added `NamedSignWithLeadingSubIndex` to `sign_token_base.py` carrying the shared `of` / `of_name` classmethods; `Reading` and `Logogram` now inherit them. `Number` keeps its own overrides because its parameter order differs (`sub_index` last) and unifying it would break positional call sites in `signs_transformer.py:89` and `token_schemas_signs.py:103`.
- `named_signs.py` shrank from 107 to 69 lines; `sign_token_base.py` grew to 208 (both under the 250 cap).

## Step 8 — F3 turned out to need a restructure, not a one-line revert

Restoring `frozen=True` alone made **pyright** fail:

```text
transliteration_query.py:196:28 - error: A frozen class cannot inherit from a class that is not frozen (reportGeneralTypeIssues)
```

pyre and mypy both accepted it. This is exactly the "checkers disagree — the code is wrong, not the checkers" case, so the fix was to restructure rather than pick a checker:

- `TransliterationQuery` and all four subclasses are now `frozen=True`.
- `__attrs_post_init__` mutation replaced by `string: str = attr.ib(converter=_strip_query_string)` plus `attr.Factory(_classify_query, takes_self=True)` / `attr.Factory(_build_query_regexp, takes_self=True)` for `type` and `regexp`. attrs evaluates defaults in field order, so `type` is set before `regexp` is computed, matching the original post-init ordering.
- `TransliterationQueryEmpty` no longer needs its `__attrs_post_init__` override.
- Module-level helper functions were used rather than `@field.default` decorators, matching the convention this PR already established for validators.

Two further pyright errors surfaced and were fixed:

1. `TransliterationQueryEmpty.string: str = ""` "overrides symbol of same name" because the base field now carries a converter descriptor — resolved by redeclaring it as `attr.ib(default="", converter=_strip_query_string)`.
2. The new tests in `test_name_part.py` subscripted loosely typed marshmallow results — resolved with `cast`, matching the convention used elsewhere at marshmallow boundaries.

pyre also rejected the first version of the F7 change (`Variable[NamedSignT (bound to NamedSign)] has no attribute 'of'`), fixed with a dedicated `LeadingSubIndexSignT` TypeVar bound to the new class.

## Step 9 — Errors made and recovered

1. Ran the full suite in the background before the F3 restructure was finished; that result was void and the run was discarded.
2. Started the coverage run before the final two edits (`_strip_query_string` rename, `TransliterationQueryEmpty` converter). Under the "re-verify after every rewrite" gate the result would not cover the shipped code, so the run was killed and restarted against the final tree.
3. The scratchpad directory was cleared mid-session, which made one background run fail with "No such file or directory"; recreated and re-run.

## Step 10 — Runtime re-verification against the final tree (HARD GATE)

Server started on port 8124 against a local MongoDB in an isolated database (`.env` not sourced), then stopped and the database dropped.

| Request | Result |
| --- | --- |
| `GET /signs/transliteration/ku-nu` | 200 |
| `GET /signs/transliteration/$$$` | **422** |
| `GET /signs/transliteration/°nu : ši\ku°` | 200 |
| `GET /signs/transliteration/ku[r]-nu` | 200 |
| `GET /signs/all`, `/signs/KU`, `/signs/KU/neoAssyrianPeriod`, `/signs?value=ku&subIndex=1` | 200 |
| `GET /textsearch?transliteration=ku-nu` | 200 — `TransliterationQueryText` |
| `GET /textsearch?transliteration=[ku\|nu]` | 200 — `TransliterationQueryWildCard`, `Type.ALTERNATIVE` |
| `GET /textsearch?transliteration=ku ?` | 200 — `Type.ANY_SIGN` |
| `GET /textsearch?transliteration=ku\nnu` | 200 — `Type.LINES` / `TransliterationQueryLine` |
| `GET /textsearch?transliteration=` | 200 — `TransliterationQueryEmpty` |
| `GET /textsearch?transliteration=$$$` | **422** — "Invalid transliteration query." |
| `GET /fragments/query?transliteration=ku-nu` | 200 |

Every `TransliterationQuery` subclass path was exercised on the running service after the freeze.

## Step 11 — F5 structural fix (user approved the test removal)

`NamePart` no longer subclasses `Token`.

Before making the change, every production consumer of `name_parts` was enumerated to confirm which members are actually used:

- `sign_unicode_lookup.py:21` — `.name_contribution`
- `sign_token_base.py` `name_tokens` — `.token`
- `sign_token_base.py` `name` — `.name_contribution`
- `sign_token_base.py` `value` — `.value`

Nothing else. The other eleven members (`clean_value`, `parts`, `lemmatizable`, `alignable`, `get_key`, `set_unique_lemma`, `update_alignment`, `set_enclosure_type`, `set_erasure`, `merge`, `accept`) existed only to satisfy the `Token` ABC and were dead in production. They are removed, along with the now-unused `TokenT` TypeVar and the `LemmatizationToken` / `EnclosureType` / `AbstractSet` imports.

`NamePart` is now:

```python
@attr.s(auto_attribs=True, frozen=True)
class NamePart:
    token: Token
    name_contribution: str = attr.ib(validator=_validate_name_contribution)

    @staticmethod
    def of(token: Token) -> "NamePart":
        return NamePart(token, name_contribution_of(token))

    @property
    def value(self) -> str:
        return self.token.value
```

### Tests removed (approved by the user, code paths removed)

Thirteen tests in `test_name_part.py` covered members that no longer exist: `test_parts_delegate_to_the_wrapped_token`, `test_accept_delegates_to_the_wrapped_token`, `test_wrapping_is_idempotent`, `test_clean_value_delegates_to_the_wrapped_token`, `test_get_key_delegates_to_the_wrapped_token`, `test_lemmatizable_delegates_to_the_wrapped_token`, `test_alignable_delegates_to_the_wrapped_token`, `test_set_unique_lemma_delegates_to_the_wrapped_token`, `test_set_unique_lemma_propagates_the_wrapped_token_error`, `test_update_alignment_delegates_to_the_wrapped_token`, `test_set_enclosure_type_keeps_wrapper_and_token_in_step`, `test_set_erasure_keeps_wrapper_and_token_in_step`, `test_merge_delegates_to_the_wrapped_token`. The `RecordingVisitor` helper they shared went with them.

`test_wrapping_is_idempotent` asserted `NamePart.of(part).token is part` — double wrapping, which is not what protects `attr.evolve`. It is replaced by `test_converting_name_parts_is_idempotent`, which pins the invariant that actually matters: `convert_name_parts(convert_name_parts(tokens)) == convert_name_parts(tokens)`.

`test_a_name_part_is_not_a_token` was added, so the structural constraint is asserted directly rather than inferred.

### Follow-on the checkers caught

Pyre flagged `convert_name_parts` twice once `NamePart` left the `Token` hierarchy: its declared input `Iterable[Token]` could no longer accept the already-wrapped parts that `attr.evolve` feeds back through the converter, and the `isinstance` branch therefore leaked `Union[NamePart, Token]` into the return type. Fixed by declaring the boundary honestly — `NamePartInput = Union[Token, NamePart]` — so the union exists only in the converter's parameter, never in a stored array. The stored `name_parts` remains `Tuple[NamePart, ...]`, one type, as the data hard gate requires.

## Step 12 — Runtime re-verification after the F5 rewrite

The Step 10 run is void — it predates the `NamePart` change. Re-run on port 8125 against an isolated local MongoDB (`.env` not sourced), server stopped and database dropped afterwards.

| Request | Result |
| --- | --- |
| `GET /signs/transliteration/ku-nu` | 200 |
| `GET /signs/transliteration/$$$` | **422** |
| `GET /signs/transliteration/°nu : ši\ku°` | 200 |
| `GET /signs/transliteration/ku[r]-nu` | 200 — `NamePart` with an interleaved `BrokenAway` |
| `GET /signs/transliteration/[ku]-nu` | 200 |
| `GET /signs/all`, `/signs/KU`, `/signs/KU/neoAssyrianPeriod`, `/signs?value=ku&subIndex=1` | 200 |
| `GET /textsearch?transliteration=ku-nu` | 200 — `TransliterationQueryText` |
| `GET /textsearch?transliteration=[ku\|nu]` | 200 — `Type.ALTERNATIVE` |
| `GET /textsearch?transliteration=ku ?` | 200 — `Type.ANY_SIGN` |
| `GET /textsearch?transliteration=ku\nnu` | 200 — `Type.LINES` |
| `GET /textsearch?transliteration=` | 200 — `TransliterationQueryEmpty` |
| `GET /textsearch?transliteration=$$$` | **422** |
| `GET /fragments/query?transliteration=ku-nu` | 200 |

Wire format re-checked against the final tree:

```text
round-trip stable: True
reload equals original: True
NamePart is a Token: False
nameParts: [ValueToken "ku", BrokenAway "[", ValueToken "r", ...]
```

`nameParts` is unchanged by the `NamePart` change, as intended.

## Step 13 — Observation raised but not changed

`ebl/signs/web/signs.py:37` has a dead statement — `attr.evolve(sign, fossey=fosseysBase64)` whose result is discarded, immediately followed by the same call inline on line 38. It is pre-existing on master, outside the review's findings, and not part of this PR's diff, so it was left alone and reported to the user instead.

## Step 14 — Pre-commit gates (run in order, against the final tree)

| # | Gate | Result |
| --- | --- | --- |
| 1 | `task format` (`ruff format --check ebl`) | 844 files already formatted |
| 2 | `task lint` (`ruff check ebl`) | All checks passed |
| 3 | `task type` (**pyre — the gate CI enforces**) | **No type errors found** |
| 4 | `task type-pyright` (101 changed files) | **0 errors, 0 warnings, 0 informations** |
| 5 | `task test` (full suite) | **4377 passed, 2 skipped, 1 xfailed** in 547 s, exit 0 |
| 6 | coverage on the 60 changed source modules | 98% overall; **0 uncovered lines among lines this PR adds or changes** |
| 7 | `flake8 <changed> --max-line-length=120` | 0 errors |
| 8 | `mypy <changed> --ignore-missing-imports` | no issues in 101 source files |
| — | `task lint-md` | 0 errors |

The test count moved from 4385 to 4377 exactly as expected: 13 tests removed with the F5 rewrite, 5 added (2 for F5, 1 for F4, plus the two replacements).

Coverage was checked against the hard gate by intersecting the `term-missing` line numbers with the added/changed line numbers from `git diff -U0` — both against `master` for the PR as a whole and against `HEAD` for this task's changes. Both intersections are empty: all 63 remaining uncovered lines sit at unchanged positions with unchanged content.

## Step 15 — Commits (explicitly requested by the user)

The user asked for two commits: one carrying all the changes including the docs, then a second removing the docs.
