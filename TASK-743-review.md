<!-- markdownlint-disable MD013 -->
# TASK-743 Review — PR #743 "Make the ATF parser visible to the type checkers"

## Metadata

| Field | Value |
| --- | --- |
| PR | [#743](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743) — Make the ATF parser visible to the type checkers |
| Repository | `ElectronicBabylonianLiterature/ebl-api` |
| Branch | `fix-type-checker-blind-spots` → `master` |
| Commit reviewed | `16a84e20059bd631a106f4862d594b95c23f8772` ("Address the round-11 review on PR #743", 2026-08-27) |
| Merge base | `c2b0a5ef4210ba83652e26d9852e1866fd6e430a` ("Add new manuscript types (#749)") |
| Local tree vs remote | identical — `git ls-remote` and local `HEAD` both at `16a84e20`; nothing unpushed, so the qlty/CodeQL verdicts on the PR page are current |
| Size | 142 files, +6770 / −4072 (62 added, 64 modified, 16 pure renames) |
| Review date | 2026-09-01 |
| Review round | 12 |
| Mergeability | `MERGEABLE`, `mergeStateStatus: CLEAN` |
| CI | all checks green (see Findings → CI and external analysers) |
| **Verdict** | **Request changes** — three open items, all of them raised in the 2026-09-01 review and none yet in the branch. Everything else is non-blocking. |
| Blocking findings | F1, F2, F3 |
| Non-blocking findings | F4 – F14 |

## Summary

This is a genuinely good PR and it has clearly had a lot of care put into it. The core insight — that a module and a directory with the same dotted name meant the ATF parser was never actually type-checked — is a real and slightly alarming discovery, and the follow-through is thorough: pyre, pyright, mypy, ruff, flake8 and qlty are all clean, the full suite passes 4494 tests, and I could not find a single test that was quietly dropped along the way (1530 → 1688 test function names, nothing missing). I booted the service against a throwaway database and walked the affected routes; the `422` fix, the erasure path and the non-text-line path all behave exactly as the description says.

So the remaining work is small. The three points from the 2026-09-01 review are all still open — the last commit predates that review by five days — and I confirmed each of them against the tree rather than taking them on trust. `NamePart` really does still probe with `isinstance`, `tokens.py`'s `__all__` really does drop the nine classes the module defines, and the two `# type: ignore` comments really are load-bearing (removing them produces two pyright errors and two mypy errors). Fix those three and this is ready.

A couple of smaller things worth a look while you're in there: `GET /signs?listAll=true` returns a 500, and `/markup` still 500s on unparsable input — the exact defect this PR just fixed on the sibling `/signs/transliteration` route. Both are pre-existing rather than caused here, so treat them as your call.

One thing to flag on process: the PR modifies `.github/instructions/copilot.instructions.md` (adding the qlty hard gate), while the description states the PR "touches no configuration file at all". The change itself is a good one — it just deserves a mention, since a reader trusting the description would not know the repo rules moved.

### Specifically checked

| Check | Result |
| --- | --- |
| **Dev container configuration** | **No warning needed.** `.devcontainer/` is byte-identical between the merge base and this branch — all five files (`README.md`, `devcontainer.json`, `setup.sh`, `sync-env.py`, `test_sync_env.py`) unchanged. `git diff --name-status <base> HEAD -- .devcontainer` is empty. Nothing to scrutinise. |
| **New `.md` files** | **None.** `git diff --diff-filter=A --name-only <base> HEAD -- '*.md'` is empty. Two markdown files are modified, neither added: `docs/ebl-atf.md` (a one-line grammar path update, correct) and `.github/instructions/copilot.instructions.md` (see F4). |
| **Failing checks** | None. All 14 check runs on `16a84e20` conclude `success` or `skipped`. |
| **qlty** | Clean. qlty Cloud: "No blocking issues"; coverage diff 100.0%. Local `qlty smells` over all 123 changed `.py` files: zero findings. |
| **CodeQL** | Clean. "No new alerts in code changed by this pull request". All five historical inline alerts are on lines that no longer exist in that form. |

The `TASK-743-todo.md`, `TASK-743-log.md` and `TASK-743-review.md` files in the working tree are my own untracked review artefacts. They are not part of the PR and must be deleted before merge.

### Details

#### F1 — `NamePart` does not satisfy the one-array/one-type hard gate — Blocking

**Status:** open. Raised in the 2026-09-01 review; confirmed against `16a84e20`.

The wrapper relocates the type question instead of answering it. At all three levels the data is still two types travelling as one:

- [`ebl/transliteration/domain/sign_token_base.py:29-30`](ebl/transliteration/domain/sign_token_base.py#L29-L30) — `name_contribution_of` is `token.value if isinstance(token, ValueToken) else ""`. This is exactly the "never discriminate by probing" case: a reader still has to ask the value what it is.
- [`ebl/transliteration/domain/sign_token_base.py:34-35`](ebl/transliteration/domain/sign_token_base.py#L34-L35) — `NamePart.token: Token` holds an arbitrary token. `Sequence[NamePart]` is homogeneous only in the wrapper; the payload inside it is not.
- [`ebl/transliteration/domain/sign_token_base.py:101-103`](ebl/transliteration/domain/sign_token_base.py#L101-L103) — `NamedSign.name_tokens` unwraps straight back to `Sequence[Token]`, which is the shape the gate objects to.
- [`ebl/transliteration/application/token_schemas_signs.py:29-33`](ebl/transliteration/application/token_schemas_signs.py#L29-L33) — `nameParts` is `fields.List(fields.Nested("OneOfTokenSchema"), attribute="name_tokens")`. The wire array still interleaves `ValueToken`, `BrokenAway`, `ValueToken`, told apart by a `OneOfSchema` discriminator.

The instructions name this precise signal: *"Reaching for a `OneOfSchema` to tell two types apart inside one array is the signal to split the array instead."* And *"An optional field present for one type and absent for another means you have two types in one array. Split the array."*

There is also a description/code mismatch of the same kind round 11 flagged. Part 5 of the PR body says "The `NamePart` converter no longer probes." That is true of `convert_name_parts`, which now takes `Iterable[NamePart]` only — but `name_contribution_of` immediately below it still probes, so the claim reads as broader than it is. A reviewer taking the description at face value would sign off on a gate that is not met.

The honest fix is the structural one the gate asks for: two arrays on the domain object and two keys on the wire — the readings/value tokens in one, the broken-away markers in the other — with the ordering that reconstructs the interleaved ATF carried explicitly rather than by array position across two types. That is a wire-format change, so if it is too large for this PR it should be split out into its own, with the gate deviation recorded explicitly rather than described as satisfied.

#### F2 — `tokens.py`'s `__all__` silently narrows the module's public API — Blocking

**Status:** open. Raised in the 2026-09-01 review; confirmed against `16a84e20`.

[`ebl/transliteration/domain/tokens.py:16-23`](ebl/transliteration/domain/tokens.py#L16-L23) declares:

```python
__all__ = [
    "ErasureState",
    "NullSignsCollectingVisitor",
    "SignsCollectingVisitor",
    "Token",
    "TokenVisitor",
    "ValueToken",
]
```

Every name in it is re-exported from `token_base`. The nine classes the module actually defines are omitted: `LanguageShift`, `UnknownNumberOfSigns`, `WordOmitted`, `Tabulation`, `CommentaryProtocol`, `Column`, `Variant`, `Joiner`, `LineBreak` (lines 27, 47, 62, 77, 92, 109, 126, 150, 191).

`master` has no `__all__` in this file at all, so `from ...tokens import *` exported all fifteen public names. It now exports six.

Two things make this worth fixing rather than waving through:

1. **It is inconsistent with its own siblings.** [`sign_tokens.py:22-33`](ebl/transliteration/domain/sign_tokens.py#L22-L33) lists its locally defined `CompoundGrapheme`, `Divider` and `Grapheme` alongside the re-exports, and [`enclosure_visitor.py:30-35`](ebl/transliteration/domain/enclosure_visitor.py#L30-L35) lists its locally defined `EnclosureValidator`. `tokens.py` is the only facade in the set that lists re-exports only. That inconsistency is the kind of thing that gets copied.
2. **`__all__` is not only about `import *`.** It is the module's declared public surface, and it is what IDEs, `pydoc` and downstream consumers read.

Nothing breaks today: `grep -rn "import \*" ebl` finds no star import anywhere in the repository, so this is a latent API narrowing rather than a live bug.

Restoring the nine local names is the fix. The regression test Fabdulla1 suggested is a good idea and cheap — assert that each facade module's `__all__` covers every public name defined in it plus everything it re-exports, which would pin all four facades at once rather than just this one.

#### F3 — Two `# type: ignore` comments contradict the PR's own claim and the repo rule — Blocking

**Status:** open. Raised in the 2026-09-01 review; confirmed against `16a84e20`.

[`ebl/tests/fragmentarium/test_fragment_pattern_matcher_site.py:35`](ebl/tests/fragmentarium/test_fragment_pattern_matcher_site.py#L35) and [`:63`](ebl/tests/fragmentarium/test_fragment_pattern_matcher_site.py#L63) both carry `# type: ignore[arg-type]`. These are the only two suppressions the diff adds, and they are load-bearing — I removed them in a scratch copy and both checkers fail:

```text
pyright: test_fragment_pattern_matcher_site.py:35:9 - error: Argument of type "Unknown | _StubProvenanceService" cannot be assigned to parameter "provenance_service" of type "ProvenanceService" (reportArgumentType)
pyright: test_fragment_pattern_matcher_site.py:63:34 - error: Argument of type "_StubProvenanceService" cannot be assigned to parameter "provenance_service" of type "ProvenanceService" (reportArgumentType)
mypy:    test_fragment_pattern_matcher_site.py:35: error: Argument 2 to "PatternMatcher" has incompatible type "Any | _StubProvenanceService"; expected "ProvenanceService"  [arg-type]
mypy:    test_fragment_pattern_matcher_site.py:63: error: Argument 2 to "PatternMatcher" has incompatible type "_StubProvenanceService"; expected "ProvenanceService"  [arg-type]
```

Part 2 of the PR description says the 149 pyright errors are "all now fixed **structurally** — no `# type: ignore`, no `# pyright: ignore`, and no type-checker or linter configuration was relaxed". That is not accurate for these two lines, and the description is the thing a reviewer reads first.

There is a second, smaller problem in the same helper. [`:32`](ebl/tests/fragmentarium/test_fragment_pattern_matcher_site.py#L32) is `def _site_filter(site: str, service=None) -> Dict:` — `service` has no annotation, which the coding standards require, and it is precisely why pyright's line-35 message reads `Unknown | _StubProvenanceService` rather than a clean type.

The fix Fabdulla1 suggested is the right one: either declare a `Protocol` covering the three methods `PatternMatcher` actually uses (`find_by_name`, `find_by_id`, `find_children`) and widen `PatternMatcher`'s parameter to it, or make `_StubProvenanceService` a real subclass of `ProvenanceService`. Either removes both suppressions and lets `service: Optional[ProvenanceService] = None` be annotated properly. The `Protocol` route is the better design — it is what the collaborator relationship actually is — and it would let other tests stub the service without a suppression too.

#### F4 — The PR edits the repo instruction file while claiming to touch no configuration — Non-blocking

[`.github/instructions/copilot.instructions.md`](.github/instructions/copilot.instructions.md) is modified by this branch: it adds gate 9 (`qlty smells <changed files>`) to the pre-commit list and a new `### HARD GATE: qlty Must Be Clean` section (about 30 lines).

Part 5 of the description says: *"This PR touches no configuration file at all — no `.coveragerc`, no `pyproject.toml`, no `mypy.ini`, no `ruff.toml`, no `.markdownlint*`, no `Taskfile`, no `.devcontainer/`, no `.github/workflows/`."* Every item in that list is individually true — I verified all of them, and `git diff --name-status` over those paths is empty. But the sentence's headline claim is not, and the file that *is* changed is the one that defines the repo's rules, which is a more consequential thing to change unannounced than any of the files listed.

The change itself is good and I would keep it. It just needs a line in the description, or — cleaner — its own small PR, so that a rules change is reviewed as a rules change rather than arriving inside a 142-file typing PR.

#### F5 — `GET /signs?listAll=true` returns 500 — Non-blocking, pre-existing

Found while exercising the running service:

```text
GET /signs?listAll=true  ->  500  {"title": "500 Internal Server Error"}
```

```text
File "ebl/signs/web/sign_search.py", line 53, in on_get
  resp.media = SignDtoSchema().dump(signs, many=True)
File "ebl/signs/infrastructure/sign_schemas.py", line 147, in make_sign_dto
  data["name"] = data.pop("_id")
KeyError: '_id'
```

`list_all_signs()` returns `Sequence[str]` (sign ids), but the `listAll` dispatcher branch feeds it through `SignDtoSchema().dump(..., many=True)`, whose `@post_dump make_sign_dto` expects a dumped sign document.

**This is not introduced here.** The identical `make_sign_dto` body is on `master` at `mongo_sign_repository.py:154-156`, and both `sign_search.py` and `list_all_signs` are untouched by this PR (`git diff` over them is empty). It surfaces in this review only because the line moved into the new `sign_schemas.py`.

I raise it because this PR *is* the one that added the `LINE_PARSE_ERRORS → DataError` mapping for the sibling route, and because the route is currently unreachable in practice. Fixing it is a couple of lines — have the `listAll` branch bypass `SignDtoSchema` and return the ids directly — but it changes a response shape, so it may belong in its own PR. Either fix it or add it to the "known pre-existing 500s" list in the description alongside the empty-transliteration one.

#### F6 — `/markup` and `/cached-markup` 500 on unparsable input — Non-blocking, pre-existing

```text
GET /markup?text=@i{italic text}   ->  200  [{"text": "italic text", "type": "EmphasisPart"}]
GET /markup?text=hello             ->  200  [{"text": "hello", "type": "StringPart"}]
GET /markup?text=@i@kur@i@         ->  500
GET /cached-markup?text=@i{...}    ->  200
```

[`ebl/markup/web/bootstrap.py`](ebl/markup/web/bootstrap.py) calls `markup_string_to_json(req.params["text"])` with no error mapping, so a lark parse error reaches the generic handler.

This is character-for-character the defect this PR fixed at [`ebl/signs/web/signs.py:61-64`](ebl/signs/web/signs.py#L61-L64):

```python
try:
    resp.media = self.sign_repository.get_unicode_from_atf(line)
except LINE_PARSE_ERRORS as error:
    raise DataError(f'Invalid transliteration: "{line}"') from error
```

The markup route is outside this PR's diff so it is legitimately out of scope, but it is the closest possible neighbour and the fix is the same four lines. Worth a follow-up issue at minimum.

#### F7 — Redundant `cast` left behind in `TextLine.merge` — Non-blocking

[`ebl/transliteration/domain/text_line.py:148-159`](ebl/transliteration/domain/text_line.py#L148-L159):

```python
def merge(self, other: L) -> L:
    if not isinstance(other, TextLine):
        return other

    other_text_line = cast(TextLine, other)     # <- redundant
    return cast(L, TextLine.of_iterable(...))
```

The `isinstance` guard on the line above already narrows `other`, and `@final` on `TextLine` (added by this PR, correctly, and it does resolve Sourcery's soundness concern about the outer `cast(L, ...)`) makes that narrowing exact.

Verified removable: I deleted `other_text_line` and read `other.line_number` / `other.content` directly, and both pyright and mypy stayed at zero errors on the file. (I did not re-run pyre for this one variant, so run `task type` before committing it.)

Small, but this PR's whole thesis is removing unnecessary escapes from the type system, so leaving one in the file it just marked `@final` is a bit of a loose end.

#### F8 — `Token.update_alignment` is typed `object`, erasing the real contract — Non-blocking

[`ebl/transliteration/domain/token_base.py:166`](ebl/transliteration/domain/token_base.py#L166):

```python
def update_alignment(self: T, alignment_map: object) -> T:
    return self
```

The real argument is `AlignmentMap = Sequence[Optional[int]]` ([`text_line.py:61`](ebl/transliteration/domain/text_line.py#L61)), and the call site at [`text_line.py:163`](ebl/transliteration/domain/text_line.py#L163) passes exactly that. Typing the parameter `object` means any argument type-checks — `token.update_alignment("nonsense")` is accepted by all three checkers.

The override at [`word_tokens.py:91`](ebl/transliteration/domain/word_tokens.py#L91) — `def update_alignment(self: A, alignment_map) -> A:` — is still unannotated, so neither end of that call is checked.

`master` had the base parameter unannotated too, so `object` is not a regression; it is the same blind spot in a different notation. Given the PR's title, annotating both as `AlignmentMap` would be the natural finish. (`AlignmentMap` lives in `text_line`, which imports tokens, so it likely needs to move to a small shared module — that is the only reason I am not calling this trivial.)

#### F9 — `_StartParser.__getattr__` returns `object`, hiding the seven module-level parsers — Non-blocking

[`ebl/transliteration/domain/atf_parsers/lark_parser.py:75-80`](ebl/transliteration/domain/atf_parsers/lark_parser.py#L75-L80) (the wrapper class starts at line 67):

```python
def __getattr__(self, name: str) -> object:
    try:
        parser = self.__dict__["_parser"]
    except KeyError:
        raise AttributeError(name)
    return getattr(parser, name)
```

A `__getattr__` returning `object` makes *every* attribute access on `_StartParser` type-check, including misspellings — statically, `WORD_PARSER.parse_intractive` is a valid `object`. The test at [`test_start_parser.py:26`](ebl/tests/transliteration/test_start_parser.py#L26) has to use `isinstance(WORD_PARSER.options, LarkOptions)` to get a usable type back, which is the symptom.

Seven module-level parsers go through this wrapper (`WORD_PARSER`, `NOTE_LINE_PARSER`, `MARKUP_PARSER`, `PARALLEL_LINE_PARSER`, `TRANSLATION_LINE_PARSER`, `PARATEXT_PARSER`, `LABEL_PARSER`), so this is a blind spot over the whole parser surface — in the PR whose stated purpose is removing exactly that.

The `except KeyError` branch is fine and needed: `copy.deepcopy` touches attributes on a not-yet-initialised instance, which `test_wrapper_is_copyable` covers.

If the delegation is only ever used for `options` in practice, an explicit `@property options -> LarkOptions` and no `__getattr__` at all would type properly. If broader delegation is genuinely needed, `-> Any` at least says so honestly rather than lying with a precise-looking `object`.

#### F10 — Shared class-body default visitor — Non-blocking

[`ebl/transliteration/domain/transliteration_query.py:210-216`](ebl/transliteration/domain/transliteration_query.py#L210-L216):

```python
class TransliterationQueryEmpty(TransliterationQuery):
    string: str = attr.ib(default="", converter=_strip_query_string)
    visitor: SignsCollectingVisitor = attr.ib(
        default=NullSignsCollectingVisitor(), eq=False
    )
```

`NullSignsCollectingVisitor()` is constructed once at import and shared by every `TransliterationQueryEmpty` instance. Harmless today — the class is stateless, which is exactly the point of it — but `attr.Factory(NullSignsCollectingVisitor)` is the idiom, costs nothing, and stays correct if the class ever grows a field. Worth changing while the file is open.

(Unrelated but noted for completeness: `TransliterationQueryFactory` shares one mutable `SignsVisitor` across every query it creates, and `TransliterationQuery` is now `frozen=True` and hashable while holding it. `transliteration_query_factory.py` is byte-identical to `master`, so this is squarely pre-existing and out of scope — but the `eq=False` change in this PR makes these objects usable as dict keys, which is a good reason to look at the sharing separately.)

#### F11 — Annotation coverage is uneven across the files this PR rewrote — Non-blocking

Round 11 annotated the nine marshmallow hooks in `sign_schemas.py`. The equivalent hooks in a file this PR also rewrote were not:

- [`token_schemas_signs.py:43`](ebl/transliteration/application/token_schemas_signs.py#L43), [`:61`](ebl/transliteration/application/token_schemas_signs.py#L61) and [`:78`](ebl/transliteration/application/token_schemas_signs.py#L78) — `ReadingSchema.make_token`, `LogogramSchema.make_token` and `NumberSchema.make_token`. This PR rewrote all three bodies (swapping `data["name_parts"]` for `data["name_tokens"]` and moving `sign` / `surrogate` onto the new withers) but left `def make_token(self, data, **kwargs):` unannotated. `GlossSchema.make_token` in the same file is annotated `-> Gloss`, so the convention exists here already.

Same pattern in the relocated token modules:

- [`token_base.py:193-195`](ebl/transliteration/domain/token_base.py#L193-L195) — `ValueToken.parts` has no return annotation, while the `Token.parts` it overrides is `Sequence["Token"]`.
- [`tokens.py:52-54`](ebl/transliteration/domain/tokens.py#L52-L54) — `UnknownNumberOfSigns.parts`, likewise; and `LanguageShift.language` (line 31), `.normalized` (line 35) and `.normalized_akkadian` (line 42) are unannotated.
- [`sign_tokens.py:46-48`](ebl/transliteration/domain/sign_tokens.py#L46-L48) — `Divider.parts`, likewise.

All of these are moved-not-new code, so nothing regressed. But the coding standard is "all functions and methods have appropriate type hints", and a moved line is a touched line. Since the checkers are already green, these are one-liners.

#### F12 — `Divider.string_flags` duplicates its own base class — Non-blocking, pre-existing

[`sign_tokens.py:55-57`](ebl/transliteration/domain/sign_tokens.py#L55-L57) is character-for-character [`sign_token_base.py:24-26`](ebl/transliteration/domain/sign_token_base.py#L24-L26), and `Divider` extends `AbstractSign`, so the override is dead code. It was dead on `master` too — but the two copies used to sit twenty lines apart in one file and now sit in two different files, which is the version that survives longer. Deleting the override is a three-line change with no behaviour effect.

#### F13 — `ChapterVisitor.visit` became a `singledispatchmethod` — Informational

[`ebl/corpus/domain/chapter.py:32-35`](ebl/corpus/domain/chapter.py#L32-L35). This is a good change: all three subclasses (`ChapterUpdater`, `TextValidator`, `ManuscriptReferenceInjector`) already declared their own `@singledispatchmethod visit`, so the base was the odd one out, and each subclass has its own dispatcher — nothing is shared.

One behaviour change worth knowing about: `singledispatchmethod` requires the dispatch argument to be **positional**. `visitor.visit(item=x)` raised nothing on `master` and now raises `TypeError`. No call site in the repository uses a keyword there, so there is no impact; noting it so it is not a surprise later.

#### F14 — `lark_parser.py` sits exactly at the 250-line limit — Informational

`ebl/transliteration/domain/atf_parsers/lark_parser.py` is 250 lines — compliant, but the next line added to it fails the gate. The other two closest changed files are `legacy_atf_converter.py` (249) and `chapter.py` (245). Nothing to do now; just be aware the margin is gone.

## Findings

| # | Finding | File | Severity | Status |
| --- | --- | --- | --- | --- |
| F1 | `NamePart` still probes with `isinstance`; `nameParts` still a `OneOfTokenSchema` array — one-array/one-type gate not met | `sign_token_base.py`, `token_schemas_signs.py` | High | Open — blocking |
| F2 | `tokens.py` `__all__` omits the nine classes the module defines; narrows the public API vs `master` | `tokens.py` | Medium | Open — blocking |
| F3 | Two load-bearing `# type: ignore[arg-type]` contradict the PR's "no `# type: ignore`" claim; `service` parameter unannotated | `test_fragment_pattern_matcher_site.py` | Medium | Open — blocking |
| F4 | Repo instruction file changed while the description says no configuration file is touched | `.github/instructions/copilot.instructions.md` | Low | Open |
| F5 | `GET /signs?listAll=true` returns 500 (`KeyError: '_id'`) | `sign_schemas.py`, `sign_search.py` | Medium | Pre-existing |
| F6 | `/markup` and `/cached-markup` 500 on unparsable markup — the defect this PR fixed next door | `ebl/markup/web/bootstrap.py` | Low | Pre-existing |
| F7 | Redundant `cast(TextLine, other)` after an `isinstance` guard | `text_line.py:152` | Low | Open |
| F8 | `Token.update_alignment(alignment_map: object)` erases the `AlignmentMap` contract; the `Word` override is unannotated | `token_base.py:166`, `word_tokens.py:91` | Low | Open |
| F9 | `_StartParser.__getattr__ -> object` makes every delegated attribute untyped across seven parsers | `lark_parser.py:75-80` | Low | Open |
| F10 | `NullSignsCollectingVisitor()` as a shared class-body default instead of `attr.Factory` | `transliteration_query.py:212-214` | Low | Open |
| F11 | Unannotated marshmallow hooks and properties in files this PR rewrote | `token_schemas_signs.py`, `token_base.py`, `tokens.py`, `sign_tokens.py` | Low | Open |
| F12 | `Divider.string_flags` duplicates `AbstractSign.string_flags`, now across two files | `sign_tokens.py:55-57` | Low | Pre-existing |
| F13 | `ChapterVisitor.visit` now requires a positional argument | `chapter.py:32-35` | Informational | Accepted |
| F14 | `lark_parser.py` at exactly 250 lines | `lark_parser.py` | Informational | Accepted |

### Existing PR feedback — disposition

Every submitted review, inline comment and conversation comment on #743 was fetched via `gh api` and is accounted for below — 12 reviews, 22 inline comments and 2 conversation comments, from Fabdulla1, three bots (Sourcery, qlty, CodeQL) and your own clarification reply of 2026-08-25.

The only merges into `fix-type-checker-blind-spots` are two merges of `master` (`525c4979`, `05051576`); both second parents are ancestors of `origin/master`, so no other PR's branch was merged in directly. The description notes this work was split out of #740, which merged to `master` on 2026-08-04, so I fetched that PR's feedback too: it is merged and approved, and every item on it (`ebl/fragmentarium/web/dtos.py`, `test_realia_info*`, the `fragment_updater` tests, `token_schemas_words.py`) is against a file this PR does not touch. Nothing to carry over.

No other PR's branch has been merged into `fix-type-checker-blind-spots`. The branch carries two merge commits, `05051576` and `525c4979`, and both second parents are plain `master` commits (`#749`, which is the merge base, and `#748`, which `git merge-base --is-ancestor` confirms is already inside it). This PR was split out of #740, which is merged and covers unrelated realia work; grepping all of its reviews, inline comments and conversation comments for `lark`, `atf_parser`, `type check`, `pyright`, `pyre`, `mypy`, `NamePart`, `__all__`, `token_base` and file-size terms returns nothing, so there is no upstream feedback to carry over.

**One point of note on the latest review's state:** it is marked `APPROVED` (2026-09-01), but its body raises three items that read as prerequisites — "just small changes that need to be done and then it should be good to merge after". The last commit on the branch, `16a84e20`, is dated 2026-08-27, five days earlier, so none of the three has been addressed. Treating the green approval as clearance to merge would ship all three.

| Source | Item | Disposition |
| --- | --- | --- |
| Fabdulla1, 2026-09-01 (APPROVED) | `NamePart` does not satisfy the one-array/one-type gate | **Confirmed, still open** — F1 |
| Fabdulla1, 2026-09-01 | `tokens.py` `__all__` drops nine locally defined classes | **Confirmed, still open** — F2 |
| Fabdulla1, 2026-09-01 | Two suppressions in `test_fragment_pattern_matcher_site.py` | **Confirmed, still open** — F3 |
| Fabdulla1, 2026-08-07 (CHANGES_REQUESTED) | `/signs/transliteration` 422 fix not in the branch | **Resolved.** Present at `signs.py:61-64`; verified live — `$$$` returns 422 |
| Fabdulla1, 2026-08-07 | 169-char URL line in `annotations_service.py:120` | **Resolved.** No line over 120 chars in any changed file |
| Fabdulla1, 2026-08-07 | Five `Museum` entries changed enum `.value` shape | **Resolved.** Dumped every member's value on base and HEAD: byte-identical, 72 members |
| Fabdulla1, 2026-08-07 | Add a focused `SignsVisitor.reset()` test | **Resolved.** `test_signs_visitor.py:126,137` |
| Fabdulla1, 2026-08-07 | Add a test for `_StartParser.parse(start=...)` | **Resolved differently, and correctly.** That parameter no longer exists — `parse` takes only `text`. `test_start_parser.py` pins the replacement behaviour. The reasoning was posted to the PR on 2026-08-25 |
| Fabdulla1, 2026-08-07 | "the qlty comments just need to be addressed" | **Resolved.** qlty Cloud reports "No blocking issues"; local `qlty smells` over all 123 changed files returns zero |
| sourcery-ai, 2026-07-23 | `merge`'s `cast(L, ...)` unsound for `TextLine` subclasses | **Resolved.** `@final` on `TextLine` makes the narrowing exact. See F7 for the leftover inner cast |
| sourcery-ai, 2026-07-23 | Reviewer's Guide (conversation comment) | Informational, no action |
| qltysh, 7 reviews / 16 inline comments | `return-statements` ×1, `similar-code` ×6, `function-parameters` ×9 | **All resolved.** All 16 anchor to lines that no longer exist in that form; qlty Cloud and local `qlty smells` both clean |
| github-advanced-security, 3 reviews / 5 inline comments | Unnecessary lambda ×1, statement-has-no-effect ×4 | **All resolved.** CodeQL on the head commit: "No new alerts in code changed by this pull request" |

### CI and external analysers

All checks on `16a84e20` pass. Local `HEAD` equals the remote branch tip, so these verdicts describe the code reviewed here — they are not stale.

| Check | Result |
| --- | --- |
| Test Python 3.11 / 3.12 / pypy-3.11 (both workflows) | success |
| Analyze (python) | success |
| CodeQL | success — "No new alerts in code changed by this pull request" |
| GitGuardian scan / Security Checks | success — no secrets detected |
| qlty check | success — "No blocking issues" |
| qlty coverage | success — 96.6% (+0.8% change) |
| qlty coverage diff | success — 100.0% (75% threshold) |
| docker, Sourcery review | skipped |

### Local gate results

Run against a clean working tree at `16a84e20`.

| Gate | Result |
| --- | --- |
| `task format` | 863 files already formatted |
| `task lint` (ruff) | All checks passed |
| `task type` (**pyre** — the CI gate) | No type errors found |
| `task type-pyright` | 0 errors, 0 warnings, 0 informations |
| `task test` | **4494 passed, 2 skipped, 1 xfailed** in 323s |
| `flake8 --max-line-length=120` over 123 changed files | 0 errors |
| `mypy --ignore-missing-imports` over 123 changed files | Success, 0 issues |
| `qlty smells` over 123 changed files | 0 findings |
| `qlty check --no-fix` over 123 changed files | **No issues** (runs the plugins as well) |
| `task lint-md` | 0 errors |
| 250-line limit on changed `*.py` | all within limit; max is 250 (F14) |
| Coverage on changed source modules | **100% on all 63 of them** — see below |
| Coverage repository-wide | 96% (18026 statements, 637 missed) |

**Coverage detail.** `poetry run pytest --cov=ebl --cov-report=term-missing` (full suite, 4494 passed / 2 skipped / 1 xfailed in 580s under instrumentation). Of the 123 changed `.py` files, 63 are source modules and all 63 appear in the coverage table at exactly `100%` — zero missed statements across every file this PR adds or modifies. The remaining 60 are test modules, which `.coveragerc` excludes from the report. This matches the PR description's claim and qlty Cloud's `coverage diff` verdict of 100.0%.

### Things that are right and worth saying

- **No test was lost in the splits.** Comparing every `def test_*` name between the merge base and the head: 1530 → 1688, and the set difference in the "removed" direction is empty. Ten test modules were split and not one assertion went missing.
- **The `Museum` split is genuinely value-preserving.** Dumping `{member.name: member.value}` for all 72 members on both sides gives identical output, including the five `PRIVATE_COLLECTION_*` three-tuples that were queried in review.
- **The 422 fix works, and so do the two latent 500s the description claims.** Verified live: `$$$` → 422, the erasure line `°nu : ši\ku°` → 200, and a dollar line → 200. All three raised on `master`.
- **The renamed grammar directory works end to end.** ATF parsed through the real service via `/signs/transliteration/...` and `/markup`.
- **Coverage is genuinely complete on the changed set,** not merely above a threshold: every one of the 63 changed source modules is at 100%, including the newly extracted `token_base.py`, `sign_token_base.py`, `named_signs.py`, `enclosure_state.py`, `enclosure_updater.py`, `sign_schemas.py`, `sign_unicode_lookup.py`, `retrieve_annotations_helpers.py`, `lookup_reservation_reconciliation.py` and the three `museum_entries_*` modules.
- **The core diagnosis is excellent.** A module and a directory sharing a dotted name, CPython preferring the module and the checkers preferring the namespace package, is a subtle failure mode, and "the noise trained us to ignore those errors" is exactly the right reading of why it survived.

## Severity

| Severity | Definition | Findings |
| --- | --- | --- |
| High | Violates a repo hard gate, or a correctness/security defect in changed code | F1 |
| Medium | Contradicts a stated rule or a claim in the PR description; or a broken route | F2, F3, F5 |
| Low | Type-safety or hygiene gap that does not change behaviour | F4, F6, F7, F8, F9, F10, F11, F12 |
| Informational | Noted for awareness; no action requested | F13, F14 |

Overall risk: **low**. The blocking items are correctness-of-contract and description-accuracy issues, not runtime defects. Nothing in this PR breaks a route that worked before — verified against the running service.

## Reproduction Steps

All steps were run from a clean checkout of `fix-type-checker-blind-spots` at `16a84e20`, with `.env` deliberately not sourced (it points at production).

### F1 — the probe and the polymorphic wire array

```bash
sed -n '29,46p'  ebl/transliteration/domain/sign_token_base.py        # isinstance probe, NamePart.token: Token
sed -n '101,103p' ebl/transliteration/domain/sign_token_base.py       # name_tokens unwraps to Sequence[Token]
sed -n '27,33p'  ebl/transliteration/application/token_schemas_signs.py  # nameParts -> OneOfTokenSchema list
```

### F2 — the narrowed `__all__`

```bash
sed -n '16,23p' ebl/transliteration/domain/tokens.py                  # six names, all re-exports
grep -nE '^class ' ebl/transliteration/domain/tokens.py               # nine locally defined classes, none listed
git show <merge-base>:ebl/transliteration/domain/tokens.py | grep -c '^__all__'   # -> 0, master has none
sed -n '22,33p' ebl/transliteration/domain/sign_tokens.py             # sibling facade does list its local classes
grep -rn "import \*" --include=*.py ebl                               # -> no matches, nothing breaks today
```

### F3 — the suppressions are load-bearing

```bash
cp ebl/tests/fragmentarium/test_fragment_pattern_matcher_site.py /tmp/orig.py
sed -i 's|  # type: ignore\[arg-type\]||' ebl/tests/fragmentarium/test_fragment_pattern_matcher_site.py
npx --yes pyright@1.1.411 ebl/tests/fragmentarium/test_fragment_pattern_matcher_site.py   # -> 2 errors
poetry run mypy ebl/tests/fragmentarium/test_fragment_pattern_matcher_site.py --ignore-missing-imports  # -> 2 errors
cp /tmp/orig.py ebl/tests/fragmentarium/test_fragment_pattern_matcher_site.py
```

### F4 — the instruction file is in the diff

```bash
git diff --name-status <merge-base> HEAD -- '.devcontainer/*' '.github/*' '*.toml' '*.ini' '*.cfg' '.coveragerc' 'Taskfile*' '.markdownlint*'
# -> M  .github/instructions/copilot.instructions.md   (and nothing else)
```

### F5, F6 and the live route verification

Boot the service against a throwaway database:

```bash
export PYTHONPATH=/workspaces/ebl-api
export MONGODB_URI="mongodb://127.0.0.1:27017"      # local; NOT the URI in .env
export MONGODB_DB="ebl_task743_review_throwaway"
export EBL_AI_API="http://127.0.0.1:9/unused"
export AUTH0_PEM="$(base64 -w0 <throwaway RSA public key PEM>)"
export AUTH0_AUDIENCE="https://example.invalid/api"
export AUTH0_ISSUER="https://example.invalid/"
export SENTRY_DSN="" CACHE_TYPE="NullCache"
poetry run python -c "
from waitress import serve
from ebl.app import create_context, create_app
import os
serve(create_app(create_context(), os.environ['AUTH0_ISSUER'], os.environ['AUTH0_AUDIENCE']),
      host='127.0.0.1', port=8123, threads=4)"
```

Then, with two signs seeded (`KUR`/`kur` → 74266, `RA`/`ra` → 74588):

```bash
curl -s -w ' %{http_code}\n' 'http://127.0.0.1:8123/signs/transliteration/kur'       # [{"unicode":[74266]}] 200
curl -s -w ' %{http_code}\n' 'http://127.0.0.1:8123/signs/transliteration/%24%24%24' # 422  <- the fix
curl -s -w ' %{http_code}\n' --get 'http://127.0.0.1:8123/signs' -d 'listAll=true'   # 500  <- F5
curl -s -w ' %{http_code}\n' --get 'http://127.0.0.1:8123/markup' -d 'text=@i{italic text}'  # 200
curl -s -w ' %{http_code}\n' --get 'http://127.0.0.1:8123/markup' -d 'text=@i@kur@i@'        # 500  <- F6
```

For the erasure and dollar-line cases, URL-encode `°nu : ši\ku°` and `nu` + newline + `$ blank` (the inputs `ebl/tests/signs/test_transliteration_route.py` uses) — both return 200.

### F7 — the inner cast is redundant

```bash
# delete `other_text_line = cast(TextLine, other)` and read other.line_number / other.content directly
npx --yes pyright@1.1.411 ebl/transliteration/domain/text_line.py                       # -> 0 errors
poetry run mypy ebl/transliteration/domain/text_line.py --ignore-missing-imports        # -> Success
```

### No test was lost

```bash
git grep -h -oE '^def (test_[A-Za-z0-9_]+)' <merge-base> -- 'ebl/tests/*.py' | sort -u > /tmp/base.txt
git grep -h -oE '^def (test_[A-Za-z0-9_]+)' HEAD         -- 'ebl/tests/*.py' | sort -u > /tmp/head.txt
comm -23 /tmp/base.txt /tmp/head.txt    # -> empty
```

### `Museum` values are preserved

```bash
git worktree add /tmp/base <merge-base> --detach
# dump {member.name: [repr(v) for v in member.value]} on each side and diff -> identical, 72 members
```

## Recommendation

**Request changes.** Three items, all of them from the 2026-09-01 review, all confirmed still open against `16a84e20`:

1. **F1 — split the `nameParts` array for real, or say plainly that it is not split.** The wrapper moved the probe rather than removing it, and the wire format still relies on `OneOfTokenSchema` to tell two types apart inside one array. If the wire change is too large for this PR, that is a fine answer — but it should be a stated deviation with a follow-up, not a claim in the description that the gate is met.
2. **F2 — restore the nine locally defined classes to `tokens.py`'s `__all__`,** and add the facade regression test. Asserting that each split module's `__all__` covers everything public it defines plus everything it re-exports would pin all four facades at once.
3. **F3 — remove both `# type: ignore[arg-type]` comments** by giving `PatternMatcher` a `Protocol` for the provenance collaborator (preferred) or making the stub a real subclass, and annotate `_site_filter`'s `service` parameter while you are there. Then the description's "no `# type: ignore`" claim becomes true.

Once those land, this is ready to merge. Everything else is a judgement call:

- **Worth doing in this PR** (all small, all in files already open): F7 the redundant cast, F10 the shared default visitor, F11 the missing annotations.
- **Worth a follow-up issue rather than more scope here:** F5 the `listAll` 500, F6 the markup 500, F8 the `AlignmentMap` contract, F9 the `_StartParser` delegation, F12 the duplicated `string_flags`.
- **Worth one sentence in the description:** F4, that the PR also updates the repo instruction file with the new qlty gate.

Please also correct the two description passages that no longer match the branch — the `NamePart` "no longer probes" claim in Part 5 and the "touches no configuration file at all" claim in the same part. Round 11's headline finding was a description that had drifted from the code; both of these are the same failure recurring, and the description is what a reviewer trusts first.

**Before merging:** delete `TASK-743-todo.md`, `TASK-743-log.md` and `TASK-743-review.md` from the working tree. They are review artefacts and must not reach `master`.
