# TASK-743-review-fixes — Work Log

Detailed log of addressing the findings in `TASK-743-review.md`. Records what
was actually done, including every error made and how it was recovered.

## Entries

### 1. Task set-up

- Re-read `.github/instructions/copilot.instructions.md` before acting.
- Created this log and `TASK-743-review-fixes-todo.md` before starting work.
  The previous task's files (`TASK-743-review*`) do not carry forward.
- Baseline at start: working tree clean except the three `TASK-743-review*`
  files; HEAD `19a2f464`; `task type-pyright` failing with 149 errors.

### 2. Decisions referred to the user

F9 (`NameParts` two-type array) and F10 (pre-existing 500 on the signs route)
were raised as decisions rather than defects, and rewriting the PR body (F2)
is an outward-facing change. Asked before acting on those three.

Answers received:

- **F9 — introduce a wrapper type.** Replace
  `Sequence[Union[ValueToken, BrokenAway]]` with a single type carrying the
  distinction structurally.
- **F10 — fix in this PR.** Map the escaping `TransliterationError` to 422 on
  the signs route and cover it with a test.
- **F2 — update the PR body on GitHub** via
  `gh api ... -X PATCH -F body=@file` (`gh pr edit --body` fails silently on
  this repo).

### 3. Work order

Mechanical and low-risk first, then the two large changes, then the gates:
F3, F7, F5, F6, F10, F9, F1, F4, gates, F2.

### 4. F3 — tracking files removed

Deleted the six committed `TASK-743-{fixes,merge,size}-{log,todo}.md` files
(1089 lines).

### 5. F7 — unreachable filter in `parse_atf_lark`

`check_errors` now returns the validated lines and states the invariant once
with a `cast`, instead of a dead `if line is not None` filter downstream.
`if any(errors)` became `if errors`.

### 6. F5 — `TokenVisitor` lying default removed

Removed `result -> []` and `reset() -> None` from the `TokenVisitor` ABC.
Added `SignsCollectingVisitor(TokenVisitor, ABC)` in `token_base.py`
declaring `reset()` and `result_string` as **abstract**; `SignsVisitor` now
implements it and `TransliterationQuery.visitor` is typed
`Optional[SignsCollectingVisitor]`. Keeping the contract in the domain avoids
a domain -> application import.

`_create_signs` now reads `visitor.result_string` rather than `visitor.result`.
`result` is `Sequence[Union[int, str]]`, and the value feeds `re.escape`,
which requires `str` — so this fixes a latent inconsistency. Behaviour is
identical for every real construction path (`SignsVisitor` is always built
with `_to_unicode=False`).

`TransliterationQueryEmpty` lost `frozen=True`, which also cleared pyright's
"a frozen class cannot inherit from a class that is not frozen".

### 7. F6 — facade convention made uniform

Added `__all__` re-export facades to `retrieve_annotations.py` and
`chapter_schemas.py`, matching `sign_tokens.py` / `enclosure_visitor.py`.
`tokens.py` also got an explicit `__all__`.

### 8. F10 — signs route 500 -> 422

`TransliterationResource.on_get` now catches `LINE_PARSE_ERRORS` (the tuple
this PR introduced) and raises `DataError`, which the error handler already
maps to 422. Covered by `ebl/tests/signs/test_transliteration_route.py`.

### 9. F1 — pyright 149 -> 0

Fixed structurally; no `# type: ignore`, no `# pyright: ignore`, no config
change.

- **Factories (106 errors).** Converted `fragment.py` and
  `fragment_metadata_factories.py` to the convention already proven clean in
  `archaeology.py`: import declarations from `factory.declarations`,
  `factory.faker`, `factory.helpers`; use `make_factory` instead of
  `class X(factory.Factory)` with a nested `Meta` (which removes the
  `reportIncompatibleVariableOverride` on `Meta`); pass `list_factory` as the
  dotted string `TUPLE_FACTORY`. Subclassed factories use
  `make_factory(..., FACTORY_CLASS=Parent, ...)` with `__name__` restored.
- **`signs_visitor` (7).** `skip_enclosures` / `skip_erasures` were typed
  `Callable[[S, T], None] -> Callable[[S, T], None]`, which replaced the
  decorated method's signature and made every override look incompatible.
  Retyped as `VisitorMethod = TypeVar(..., bound=Callable[..., None])`,
  `func: VisitorMethod -> VisitorMethod`, so the original signature survives.
- **attrs validators (4).** `@field.validator` decorators in `tokens.py`,
  `sign_token_base.py`, `markup.py` and `line_variant.py` became module-level
  functions passed as `attr.ib(validator=...)`.
- **pymongo / marshmallow loose returns (~20).** Explicit `cast` at each
  boundary, annotated repository overrides to match `FragmentRepository`, and
  `_map_fragments` retyped `Sequence[Fragment] -> List[Fragment]`.
  `filter_query_by_transliteration` takes `Iterable[Dict[str, Any]]` (it is
  iterated, never used as a `Collection`).
- **`chronology.py`.** `chronology = cast(Chronology, ChronologySchema().load(...))`.
- **`auth0.py`.** One `profile_factory` instead of two conditional
  definitions; `issuer` coerced to `str`.
- **`signs_transformer.py`.** `scan_values(lambda value: bool(value))` keeps
  the original truthiness predicate with a `bool` return; `Grapheme.of` gets a
  real `SignName`.

**Error made and recovered:** my first `tree_to_string` rewrite replaced the
`hasattr(part, "value")` duck-typing with `isinstance(part, LarkToken)`. That
broke three `test_signs_visitor` cases, because `scan_values` also yields ebl
domain tokens that carry `.value` but are not lark tokens. Restored the
duck-typing and satisfied pyright with `cast(Any, part).value` instead. Also
caught that `lambda x: x` and `lambda _: True` are not the same predicate;
used `lambda value: bool(value)` to preserve the original filtering.

### 10. F9 — domain-only `NamePart` wrapper

The user first chose "introduce a wrapper type". While implementing I found
that `nameParts` is serialised through `OneOfTokenSchema`, so a full wrapper
would change the public JSON array shape and break every client — material
information the original question did not carry. Raised it and the user chose
**domain-only wrapper, wire unchanged**.

- `NamePart(Token)` wraps one token plus the text it contributes to the sign
  name. `NameParts = Sequence[NamePart]` — one type per array.
- `NamedSign.name` is now `"".join(part.name_contribution for part in ...)`.
  The `isinstance(token, ValueToken)` probe that every reader would otherwise
  repeat is gone; classification happens once, in `NamePart.of`.
- `NamedSign.name_tokens` exposes the unwrapped tokens, so `parts`, the
  enclosure visitor and the enclosure updater behave exactly as before.
- `mongo_sign_repository` no longer reaches into `ValueToken._value`; it reads
  `name_contribution`.
- `token_schemas_signs.NamedSignSchema.name_parts` became a `fields.Function`
  that dumps `name_tokens` and loads raw tokens, so the wire is untouched.

**Proof the contract is preserved:** dumped a parsed line through
`OneOfTokenSchema` before and after the change (`git stash` on the working
tree) and diffed the JSON — **identical**. Interleaving is intact:
`ValueToken, BrokenAway, ValueToken` for `š[u]`.

**Three-checker disagreement.** Pyright accepted `name: Sequence[Token]` on
the `of` factories because it models the attrs converter; pyre does not, and
typed `__init__` by the declared attribute. Resolved by wrapping explicitly
with `convert_name_parts(name)` at each construction site — all three pass.

### 11. F4 — coverage

Added tests for the relocated code:

- `test_token_visitor.py` rewritten: parametrised delegation test over all 24
  `visit_*` methods, plus `visit_number` -> `visit_named_sign` and
  `Token.update_alignment`.
- `test_retrieve_annotations_helpers.py` (new, 18 tests).
- `test_chapter_manuscript_schemas.py` (new, 6 tests) covering the four
  `ValidationError` paths.
- `test_named_sign_validation.py`, `test_name_part.py`, and
  `test_transliteration_route.py` (F10).

Two lines in `retrieve_annotations_helpers.py` were **provably unreachable**
defensive guards — `match()` can never return an empty or lowercase label, and
`BoundingBox.from_annotations` maps 1:1 so the length check can never fire.
Reported them; the user chose to remove them, which was done.
`write_annotations`' guard is genuinely reachable and stays, with a test.

**Result: 0 uncovered lines on code this PR adds or moves** (was 30).

### 12. 250-line gate

The F9 work pulled two pre-existing oversized files into the changed set, so
both had to be split:

- `mongo_sign_repository.py` 403 -> 235, extracting
  `sign_schemas.py` (148) and `sign_unicode_lookup.py` (45). An `__all__`
  facade keeps `MongoSignRepository`, `SignSchema` and `SignDtoSchema`
  importable from the original path.
- `test_sign_tokens.py` 491 -> 85, split into
  `test_named_sign_reading.py`, `test_named_sign_logogram.py`,
  `test_named_sign_number.py` and `test_grapheme_tokens.py`. All 45 original
  tests preserved.

### 13. Final gate results

| Gate | Result |
| --- | --- |
| `task format` | 831 files already formatted |
| `task lint` | All checks passed |
| `task type` (pyre) | **No type errors found** |
| `task type-pyright` | **0 errors** (was 149) |
| `task test` | **4308 passed**, 2 skipped, 1 xfailed |
| Coverage on changed modules | 98%; **0 gaps on PR-touched code** |
| `flake8 --max-line-length=120` | 0 errors |
| `mypy --ignore-missing-imports` | 5 errors, none in a changed file |
| 250-line gate | pass — no changed file over 250 |
| `task lint-md` | see below |

### 14. Runtime re-verification (after the rewrites)

Re-run in full, because the earlier evidence was void once the implementation
changed. `.env` was never sourced; `MONGODB_URI` pinned to
`mongodb://127.0.0.1:27017`, throwaway database `ebl_review_743_smoke`
dropped afterwards; `create_app()` used directly to avoid the production
Sentry DSN; throwaway RSA key.

| Request | Result |
| --- | --- |
| `GET /signs/transliteration/ku-nu-szi` | 200 |
| `GET /signs/transliteration/$$$` | **422**, was 500 |
| `GET /markup?text=@i{italic} and plain` | 200, correct parts |
| `GET /fragments/query?transliteration=ku-nu-szi` | 200 |
| `GET /fragments?random\|needsRevision\|interesting` | 200, 200, 200 |
| `GET /fragments?bogus=1` | 422 |
| `GET /signs?value=ku&subIndex=1` | 200 (split repository) |

In-process: `Museum` still has 72 members; ATF round-trips
(`1. ku-nu-szi GI₆ š[u]`); `NamePart` wraps and `name_tokens` unwraps; the
`nameParts` wire payload is unchanged; all four fragment factories build.
