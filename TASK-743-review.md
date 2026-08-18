# TASK-743 Review — PR #743 "Make the ATF parser visible to the type checkers"

PR: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743>
Branch: `fix-type-checker-blind-spots` -> `master`
Reviewed at: `55827af1` (in sync with `origin/fix-type-checker-blind-spots`)
Date: 2026-08-16

## Review Summary

Really nice piece of work — finding that `lark_parser/` was shadowing
`lark_parser.py` and quietly hiding the whole ATF parser from mypy and pyright
is a great catch, and fixing it with a plain directory rename rather than a
config override is exactly right. I checked the five points from the last round
and they are all done: the 422 on `/signs/transliteration/{line}` is in and I
saw it return 422 on a running server, the long URL line is gone, the five
private-collection museum entries are back to 3-tuples, and there are now two
tests for `SignsVisitor.reset()`. I also diffed the `nameParts` JSON before and
after and it came out byte-identical, so the `NamePart` refactor really is
wire-compatible.

Nothing here blocks, but a few small things are still open: the six qlty issues
haven't been touched, the three CodeQL alerts are still showing, and there is a
duplicate `__all__` in `chapter_schemas.py` that silently drops
`ApiLineVariantSchema`. The PR description is also slightly out of date about
`_StartParser.parse`. All quick fixes. Details below.

> **Update — 2026-08-16, after the review.** All of the above has now been
> fixed in the working tree, plus most of the `atf_importer` type debt. One
> item is deliberately left (`legacy_atf_transformers.py`) and one is
> deliberately declined (the test-factory duplication); both are explained in
> the `Resolution` section at the end. The changes are **uncommitted**.

### Details

<!-- markdownlint-disable MD013 -->

#### F1 — `chapter_schemas.py` declares `__all__` twice; the second one drops `ApiLineVariantSchema` (new finding)

`ebl/corpus/web/chapter_schemas.py` has two consecutive `__all__` assignments, at lines 37 and 47. The second rebinds the name and wins, and it omits `"ApiLineVariantSchema"` — a class that is defined in the same module at line 97 and used at line 148. This looks like a copy-paste left over from the `chapter_manuscript_schemas.py` split.

No runtime breakage: nothing star-imports this module, and `__all__` does not restrict explicit imports. The cost is that the facade's declared public surface is wrong, which matters because the whole point of the `__all__` facades in this PR is to document what each split module still re-exports. Ruff, pyre, pyright and flake8 all pass over it, because none of them flags a module-level rebinding.

Fix: delete the second block (lines 47-54) and keep the first, which is the complete list.

#### F2 — Sourcery: the `TextLine.merge` cast is unsound for subclasses (open, but I'd keep the code as-is)

`ebl/transliteration/domain/text_line.py:146-157`. Sourcery is technically right — `merge` is declared `(self, other: L) -> L` and returns `cast(L, TextLine.of_iterable(...))`, so if `L` were ever bound to a `TextLine` subclass the caller would get a plain `TextLine` while the type system claimed otherwise.

I checked and there is currently no subclass of `TextLine` anywhere in `ebl/` — the `Line` subclasses are `NoteLine`, `TranslationLine`, `DollarLine`, `AtLine`, `ParallelLine`, `ControlLine`, `EmptyLine` and `TextLine` itself. So the cast is sound today.

I would not take Sourcery's suggested fix. Reverting the signature to `Union[TextLine, L]` reintroduces exactly the variance error against `Line.merge(self, other: L) -> L` that this PR set out to remove. The other suggestion — construct `type(other)` instead — does not work either, because `of_iterable` is a `@staticmethod` that hard-codes `TextLine(...)` (lines 83-89), so it would not dispatch to a subclass anyway.

Suggestion: leave the cast, and reply to Sourcery on the PR with the "no subclasses exist" rationale so the thread can be resolved rather than left hanging. If you want belt and braces, a `@final` decorator on `TextLine` would let the checkers prove the cast rather than trust it.

#### F3 — Three CodeQL alerts are still open

- `ebl/transliteration/domain/signs_transformer.py:27` — "Unnecessary lambda". `tree.scan_values(lambda value: bool(value))` can be `tree.scan_values(bool)`.
- `ebl/transliteration/domain/token_base.py:98` and `:102` — "Statement has no effect", on the `...` bodies of `SignsCollectingVisitor.reset` and `SignsCollectingVisitor.result_string`.

The second pair is a CodeQL false positive on the `def f() -> None: ...` abstract-stub idiom, but it is worth fixing anyway for a reason that has nothing to do with CodeQL: the *same file* already spells its abstract members the other way. `Token.value` (line 121) and `Token.parts` (line 126) both use `raise NotImplementedError`. Switching the two new stubs to match would make `token_base.py` internally consistent and clear both alerts for free.

The CodeQL *check* is green — these are alerts on the security tab, not build failures — so this is cleanup, not a blocker.

#### F4 — The six qlty blocking issues have not been addressed

This was the last item in the previous review and it is still outstanding. `qlty check` reports SUCCESS with **6 blocking issues** on the current head. Grouped by fix:

| # | Location | Rule | Note |
| - | -------- | ---- | ---- |
| 1 | `ebl/fragmentarium/retrieve_annotations_helpers.py:40` (`match`) | `return-statements` (7) | Six of the seven returns are `if type == X: return X.name`. A `{AnnotationValueType.SURFACE_AT_LINE: ..., ...}` dict lookup with a fallback collapses this to two returns and is shorter than the current chain. |
| 2 | `ebl/transliteration/domain/named_signs.py:68` (`Logogram.of`) | `function-parameters` (6) | |
| 3 | `ebl/transliteration/domain/named_signs.py:88` (`Logogram.of_name`) | `function-parameters` (6) | Same shape as #2; both are pre-existing signatures that only moved here in the `sign_tokens.py` split. |
| 4 | `ebl/tests/transliteration/test_named_sign_logogram.py:104` (`test_logogram`) | `function-parameters` (9) | |
| 5 | `ebl/tests/transliteration/test_named_sign_number.py:85` (`test_number`) | `function-parameters` (7) | |
| 6 | `ebl/tests/transliteration/test_named_sign_reading.py:86` (`test_reading`) | `function-parameters` (8) | #4-#6 are `@pytest.mark.parametrize` tests. Folding the expectations into a small `namedtuple`/dataclass per case, or splitting the `expected_*` trio into one `Expected` object, drops all three under the threshold at once. |

An earlier qlty round also flagged a similar-code pair between `ebl/tests/factories/lemmatized_fragment_text.py:111` and `ebl/tests/factories/transliterated_fragment_lines.py:70` (46 lines, mass 240). It is not in the current blocking six, but the duplication is real and both files are new in this PR, so it is worth a look while you are in there.

Also, `retrieve_annotations_helpers.py:41` shadows the `type` builtin (`type = annotation_data.type`). That is moved code rather than new code, but if you are rewriting `match` for qlty anyway, renaming it to `annotation_type` costs nothing.

#### F5 — The PR description is stale about `_StartParser.parse` (new finding)

The description says `_StartParser.parse` "takes an optional `start` instead" of `**kwargs: object`. The code at `ebl/transliteration/domain/atf_parsers/lark_parser.py:72-73` is:

```python
def parse(self, text: str) -> Tree:
    return self._parser.parse(text, start=self._start)
```

There is no `start` parameter at all — it was removed, not made optional. I checked every call site and no caller ever passed `start=` to a `_StartParser` instance (`WORD_PARSER`, `NOTE_LINE_PARSER`, `MARKUP_PARSER`, `PARALLEL_LINE_PARSER`, `TRANSLATION_LINE_PARSER`, `PARATEXT_PARSER`, `LABEL_PARSER`), so narrowing the signature is safe and is the better design. Only the description needs updating.

Two consequences worth stating explicitly, since the PR body is what ends up in the merge record:

- The previous review's request for "one focused test calling `_StartParser.parse(..., start=...)`" is now **moot**, not outstanding. `test_parse_uses_default_start` passes `start="any_word"` to `LINE_PARSER`, which is a raw `Lark` instance, not to the wrapper. There is no explicit-`start` path on `_StartParser` left to pin.
- The verification table says `task test` gives "4308 passed"; on the current head it is 4366 passed, 2 skipped, 1 xfailed.

#### F6 — `NamePart` is a `Token` subclass that delegates only three of its members (latent)

`ebl/transliteration/domain/sign_token_base.py:24-47`. `NamePart` wraps a `Token` and overrides `value`, `parts` and `accept`. Everything else — `clean_value`, `get_key`, `lemmatizable`, `alignable`, `set_unique_lemma`, `update_alignment`, `set_enclosure_type`, `set_erasure`, `merge` — falls through to `Token`'s defaults and describes the *wrapper*, not the wrapped token.

Concretely, for a `NamePart` wrapping `BrokenAway("[")`:

- `NamePart.clean_value` returns `"["`, whereas `BrokenAway.clean_value` is `""`.
- `NamePart.get_key()` returns `NamePart⁝[`, whereas the wrapped token's key is `BrokenAway⁝[`.
- `set_enclosure_type` evolves the wrapper's own `enclosure_type` field and leaves the inner token's untouched, so the two can diverge.

None of this is reachable today. I traced every reader of `name_parts`: `NamedSign.name`, `.value`, `.clean_value` and `.parts` all go through `name_contribution` or the unwrapped `name_tokens`; `_dump_name_parts` serialises `name_tokens`; `EnclosureUpdater.visit_named_sign` visits `name_tokens` and lets the converter re-wrap with a fresh snapshot; `sign_unicode_lookup` reads `name_contribution`. So this is a trap for the next person, not a live bug.

Cheapest guard: don't make `NamePart` a `Token` at all. It is a wrapper carrying a classification, not a token in the ATF sense, and nothing appears to require it to be one. If it must stay a `Token`, delegate the remaining members explicitly.

#### F7 — Pre-existing mypy errors surface from the `atf_importer` package (informational)

Running `poetry run mypy <85 changed files> --ignore-missing-imports` reports 5 errors, all in `ebl/atf_importer/**`:

```text
ebl/atf_importer/domain/legacy_atf_transformers.py:232: error: Argument 1 to "search" of "Pattern" has incompatible type "str | None"; expected "str"  [arg-type]
ebl/atf_importer/application/logger.py:61: error: Argument 1 to "Path" has incompatible type "PathLike[str] | str | None"; expected "str | PathLike[str]"  [arg-type]
ebl/atf_importer/application/lemmatization.py:13: error: Right hand side values are not supported in TypedDict  [misc]
ebl/atf_importer/application/lemmatization.py:14: error: Right hand side values are not supported in TypedDict  [misc]
ebl/atf_importer/domain/atf_indexing_visitor.py:35: error: Incompatible types in assignment (expression has type "str", target has type "None")  [assignment]
```

None of those four files is in this PR's changed set — mypy reaches them by following imports out of `legacy_atf_converter.py`, which the PR does touch. The pre-commit gate scopes to changed files, so the PR's "0 errors in changed files" claim holds and this does not block. Given that the whole point of this PR is that hidden type errors are a liability, a follow-up issue for the `atf_importer` package would be in the spirit of the change.

#### Previous-round findings I confirmed are now fixed

All five points from the CHANGES_REQUESTED review were raised against an earlier commit and have since been addressed. Re-verified on `55827af1`:

| Previous finding | Status | Evidence |
| ---------------- | ------ | -------- |
| 422 fix for `GET /signs/transliteration/{line}` not in the branch | **Fixed** | `ebl/signs/web/signs.py:62-65` catches `LINE_PARSE_ERRORS` and raises `DataError`. On a running server: `GET /signs/transliteration/$$$` -> `422 {"title": "422 Unprocessable Entity", "description": "Invalid transliteration: \"$$$\""}`; `GET /signs/transliteration/[[[` -> 422; `GET /signs/transliteration/ku` -> 200. |
| ~169-char URL line in `annotations_service.py:120` | **Fixed** | No line exceeds 120 characters in `ebl/fragmentarium/application/annotations_service.py`, nor in any of the 85 changed `.py` files. `flake8 --max-line-length=120` returns 0 errors. |
| Five `Museum` entries changed `.value` shape | **Fixed** | All five are `MuseumEntryWithoutUrl = Tuple[str, str, str]` in `museum_entries_m_s.py:104-128`, matching `origin/master`. At runtime `len(Museum.PRIVATE_COLLECTION_CHICAGO.value) == 3` and `url == ''` for all five; `len(list(Museum)) == 72`. |
| No focused test for `SignsVisitor.reset()` | **Fixed** | `ebl/tests/transliteration/test_signs_visitor.py:118-141` adds `test_reset_clears_accumulated_signs` (accumulates `["KU", "BU"]`, resets, asserts `[]`) and `test_reset_lets_a_visitor_be_reused`. |
| No test for `_StartParser.parse(start=...)` | **Moot** | The `start` parameter was removed from `_StartParser.parse` entirely — see F5. There is no such path to pin. |

#### Related PR #740

This PR was split out of #740 (`add-realia-annotation-api`, merged 2026-08-04). I fetched its reviews as well. Its final state is APPROVED; the outstanding discussion there concerns `ebl/fragmentarium/web/dtos.py`, realia lookup failure modes and the no-retry regression test in `test_realia_info_route.py`. None of that code is in #743's diff, so nothing carries over. No feature branch has been merged into `fix-type-checker-blind-spots` — both merge commits merge `master`.

#### What I checked and found clean

- **Data hard gate.** The `NameParts` change is the right direction: `Sequence[Union[ValueToken, BrokenAway]]` became `Sequence[NamePart]`, one type per array, with the classification done once in `NamePart.of` instead of by `isinstance` probing at every reader. Structurally separate, and the shared id space question does not arise here.
- **Wire format.** I dumped `OneOfTokenSchema` output for six ATF lines covering broken-away interleaving, a determinative, a compound grapheme, a number with a sign, multiple flags and sub-indices, on `origin/master` in a worktree and on the branch, using the same interpreter. 500 lines each, **byte-identical**. The `nameParts` claim holds.
- **The rename is pure.** All 16 `.lark` files moved with zero content changes (`git diff -M` shows `0 insertions(+), 0 deletions(-)`). No stale `lark_parser/` path remains anywhere in the tree, and nothing in `pyproject.toml`, `Dockerfile` or packaging refers to the directory. The `docs/ebl-atf.md` link was updated. Verified at runtime: `GET /markup?text=@i{italic} plain` returns the correct parse, so the relocated grammar loads.
- **No suppressions, no config edits.** The diff adds no `# type: ignore`, no `# pyright: ignore`, no `# noqa` and no `# pragma: no cover`. The two `# noqa: B024` / `B027` that appear as added lines are the pre-existing ones moving from `tokens.py` to `token_base.py`. No linting or formatting configuration file is touched.
- **No tests removed or skipped.** Test function count goes from 1861 on master to 1868 on the branch; no new `@pytest.mark.skip` or `xfail`.
- **250-line limit.** Every changed `.py` file is within the limit.
- **Narrowing `_StartParser.parse` is safe** (see F5), and `check_errors` changing `if any(errors)` to `if errors` is equivalent in practice — `create_transliteration_error_data` always returns an `ErrorAnnotation` attrs instance, which is always truthy.
- **`sign_unicode_lookup.extract_word_sub_indexes` is a small improvement.** Master used `getattr(part, "name_parts", [])` plus `name_parts[0]._value`; the branch uses an `isinstance(sign, NamedSign)` check plus `name_contribution`. A leading `BrokenAway` used to raise `AttributeError` and now yields `""`.
- **Coverage on touched lines.** Overall 98% on the changed source modules (3350 statements, 54 missed), and I checked every missed line against the diff hunks: **none of the 54 falls on a line this PR adds, modifies or moves.** Every newly created or split-out module is at 100% — `retrieve_annotations_helpers.py`, `sign_schemas.py`, `sign_unicode_lookup.py`, `token_base.py`, `sign_token_base.py`, `named_signs.py`, `enclosure_state.py`, `enclosure_updater.py`, `chapter_manuscript_schemas.py`, `lookup_reservation_reconciliation.py`, all three `museum_entries_*` modules, `museum_entry.py`, `lark_parser.py` and `lark_parser_errors.py`. The largest remaining gap, `retrieve_annotations.py` at 79%, is the CLI `main()` path; those exact lines exist verbatim on `origin/master`, are uncovered there too, and only shifted position when the helpers were extracted. This matches the `qlty coverage diff` result of 100.0%.

<!-- markdownlint-enable MD013 -->

## Summary

PR #743 fixes a real and well-diagnosed defect: the directory
`ebl/transliteration/domain/atf_parsers/lark_parser/` shadowed the module
`lark_parser.py` as a namespace package, so mypy and pyright had never
type-checked the ATF parser or anything importing it. The fix is a pure rename
of the grammar directory to `atf_grammar/`, followed by structural repairs to
everything the checkers could then see: 149 pyright errors down to zero with no
suppressions and no configuration change, ten oversized modules split under the
250-line limit behind `__all__` re-export facades, and three design fixes found
in review (`SignsCollectingVisitor`, the `NamePart` array split, and a 422
instead of a 500 on unparsable transliteration input).

The change is large (102 files, +4208 / -2992) but the risk is concentrated in
places I was able to verify directly. All eight pre-commit gates pass locally,
the affected routes behave correctly on a running server, and the `nameParts`
wire format is byte-identical to master.

Everything the previous review asked for has been done. What remains is
cleanup: six qlty issues, three CodeQL alerts, one duplicate `__all__`, and a
stale paragraph in the PR description.

## Findings

<!-- markdownlint-disable MD013 -->

| ID | Finding | Severity | Source | Status |
| -- | ------- | -------- | ------ | ------ |
| F1 | Duplicate `__all__` in `chapter_schemas.py` drops `ApiLineVariantSchema` | Low | This review | Open |
| F2 | `TextLine.merge` cast unsound for subclasses | Low | Sourcery | Open — recommend documenting, not changing |
| F3 | Three CodeQL alerts (unnecessary lambda; two no-effect statements) | Low | CodeQL | Open |
| F4 | Six qlty blocking issues untouched | Low | qlty / Fabdulla1 | Open |
| F5 | PR description stale on `_StartParser.parse`; test counts stale | Low | This review | Open |
| F6 | `NamePart` delegates only 3 of ~13 `Token` members | Low | This review | Open — latent |
| F7 | Five pre-existing mypy errors in `ebl/atf_importer/**` | Informational | This review | Out of scope, follow-up |
| — | 422 on `/signs/transliteration/{line}` | — | Fabdulla1 | **Fixed and verified** |
| — | ~169-char URL line in `annotations_service.py` | — | Fabdulla1 | **Fixed and verified** |
| — | Five `Museum` entries changed `.value` shape | — | Fabdulla1 | **Fixed and verified** |
| — | Missing `SignsVisitor.reset()` test | — | Fabdulla1 | **Fixed and verified** |
| — | Missing `_StartParser.parse(start=...)` test | — | Fabdulla1 | **Moot** — see F5 |
| — | `dtos.py` / realia concerns from PR #740 | — | Fabdulla1 (#740) | Not applicable to this diff |

<!-- markdownlint-enable MD013 -->
## Severity

No blocking findings. Every open item is Low or Informational.

- **Blocker / High:** none.
- **Medium:** none.
- **Low:** F1-F6. F1 is objectively wrong but has no runtime effect. F2 and F6
  are latent traps that no current code path reaches. F3 and F4 are static
  analysis cleanup that the previous review already asked for. F5 is
  documentation.
- **Informational:** F7.

The one finding I would not merge without touching is F1, purely because it is a
two-line deletion and leaving a wrong `__all__` in a facade module defeats the
purpose of the facades this PR introduces.

## Reproduction Steps

All commands run from the repository root on `55827af1`.

**F1 — duplicate `__all__`:**

```bash
grep -n "^__all__" -A 9 ebl/corpus/web/chapter_schemas.py
grep -n "ApiLineVariantSchema" ebl/corpus/web/chapter_schemas.py
```

Two `__all__` blocks at lines 37 and 47; `ApiLineVariantSchema` appears in the
first list, is defined at line 97 and used at line 148, and is absent from the
second list that actually takes effect.

**F2 — no `TextLine` subclasses exist:**

```bash
grep -rn "class .*(.*TextLine.*)" --include=*.py ebl/
grep -rn "^class .*(Line)" --include=*.py ebl/
```

**F3 — CodeQL alert sites:**

```bash
grep -n "scan_values" ebl/transliteration/domain/signs_transformer.py
grep -n "raise NotImplementedError\|: \.\.\." ebl/transliteration/domain/token_base.py
```

Lines 98 and 102 use `...`; lines 122 and 127 in the same file use
`raise NotImplementedError`.

**F4 — qlty issues:**

<https://qlty.sh/gh/ElectronicBabylonianLiterature/projects/ebl-api/pull/743/issues>
— reported by `gh pr checks 743` as "qlty check … 6 blocking issues".

**F5 — `_StartParser.parse` has no `start` parameter:**

```bash
sed -n '69,80p' ebl/transliteration/domain/atf_parsers/lark_parser.py
grep -rn "_PARSER\.parse" --include=*.py ebl/
```

**F6 — `NamePart` delegation gaps:**

```bash
sed -n '24,50p' ebl/transliteration/domain/sign_token_base.py
sed -n '112,168p' ebl/transliteration/domain/token_base.py
```

**F7 — pre-existing mypy errors:**

```bash
FILES=$(git diff --name-only --diff-filter=ACMR \
  origin/master...HEAD -- '*.py' | tr '\n' ' ')
poetry run mypy $FILES --ignore-missing-imports
```

**Verification of the fixed items — running service:**

```bash
# Never source .env — its MONGODB_URI points at the production cluster.
export MONGODB_URI="mongodb://127.0.0.1:27017"
export MONGODB_DB="ebl_review_743_throwaway"
export EBL_AI_API="http://127.0.0.1:9/unused"
export AUTH0_PEM="$(openssl genrsa 2048 | openssl rsa -pubout | base64 -w0)"
export AUTH0_AUDIENCE="https://localhost/api"
export AUTH0_ISSUER="https://localhost/"
export SENTRY_DSN=""
poetry run waitress-serve --port=8123 --call ebl.app:get_app &

curl -s -w '\nHTTP %{http_code}\n' 'http://127.0.0.1:8123/signs/transliteration/%24%24%24'
curl -s -w '\nHTTP %{http_code}\n' 'http://127.0.0.1:8123/signs/transliteration/ku'
curl -s -w '\nHTTP %{http_code}\n' 'http://127.0.0.1:8123/markup?text=%40i%7Bitalic%7D%20plain'
```

**Verification that the `nameParts` wire format is unchanged:**

```bash
git worktree add /tmp/master-wt origin/master
# Dump OneOfTokenSchema output for the same ATF on both trees,
# using the same interpreter, then diff the two dumps.
```

## Recommendation

**Approve with minor comments.** I would ask for F1 and F5 before merge — a
two-line deletion and a description edit — and treat F3 and F4 as either
part of this PR or a tracked follow-up, since the previous review already
asked for the qlty issues. F2 deserves a reply on the Sourcery thread rather
than a code change. F6 and F7 are worth issues, not changes here.

Concretely, in order of cost:

1. Delete the second `__all__` block in `ebl/corpus/web/chapter_schemas.py`
   (lines 47-54). **(F1)**
2. Update the PR description: `_StartParser.parse` takes no `start` parameter,
   and the test count is 4366, not 4308. **(F5)**
3. Change `SignsCollectingVisitor.reset` and `.result_string` from `...` to
   `raise NotImplementedError`, matching `Token.value` and `Token.parts` in the
   same file, and simplify `scan_values(lambda value: bool(value))` to
   `scan_values(bool)`. Clears all three CodeQL alerts. **(F3)**
4. Address the six qlty issues — the `match` dict lookup and one shared
   `Expected` object across the three `test_named_sign_*` parametrised tests
   cover four of the six. **(F4)**
5. Reply to Sourcery explaining that no `TextLine` subclass exists and that its
   suggested fix would reintroduce the variance error, then resolve. **(F2)**
6. Open follow-up issues for `NamePart`'s partial `Token` delegation **(F6)** and
   the `ebl/atf_importer/**` mypy errors **(F7)**.

### Gate results on `55827af1`

<!-- markdownlint-disable MD013 -->

| Gate | Result |
| ---- | ------ |
| `task format` | clean — 835 files already formatted |
| `task lint` (ruff) | All checks passed |
| `task type` (**pyre** — the gate CI enforces) | **No type errors found** |
| `task type-pyright` | **0 errors, 0 warnings** |
| `task test` | **4366 passed, 2 skipped, 1 xfailed** (352s) |
| Coverage on changed source modules | 98% overall (3350 stmts, 54 missed); **0 uncovered lines among lines this PR adds, modifies or moves** |
| `flake8 --max-line-length=120` (85 changed files) | 0 errors |
| `mypy --ignore-missing-imports` (85 changed files) | 0 in changed files; 5 in untouched `atf_importer` modules reached by import-following (F7) |
| `task lint-md` | 0 errors |
| 250-line limit | every changed `.py` within limit |
| Running service | 422 / 200 / markup routes all correct |
| `nameParts` wire format vs master | byte-identical |
| CI on the PR | all checks green; `qlty check` SUCCESS with 6 blocking issues; `qlty coverage diff` 100.0% |

<!-- markdownlint-enable MD013 -->

## Resolution

Every finding was worked through on 2026-08-16. The changes are **uncommitted**
in the working tree. Work log: `TASK-743-fix-log.md`.

<!-- markdownlint-disable MD013 -->

| ID | Status | What changed |
| -- | ------ | ------------ |
| F1 | **Fixed** | Deleted the second `__all__` block in `ebl/corpus/web/chapter_schemas.py`. The surviving list includes `ApiLineVariantSchema`. |
| F2 | **Fixed** | `TextLine` is now `@final`. That makes Sourcery's failure case — `L` bound to a `TextLine` subclass — impossible, so the `cast` is provable rather than true by accident. The cast stays; Sourcery's own suggestion would have reintroduced the variance error this PR removed. |
| F3 | **Fixed** | `scan_values(lambda value: bool(value))` -> `scan_values(bool)`; `SignsCollectingVisitor.reset` and `.result_string` now `raise NotImplementedError` instead of `...`, matching `Token.value` and `Token.parts` in the same file. All three alerts clear. |
| F4 | **Fixed** (6 of 6) | `match`: seven returns -> two via a `TYPES_MATCHED_BY_NAME` membership test, and the `type` builtin shadow renamed to `annotation_type`. `Logogram.of` / `of_name`: sixth parameter removed, `surrogate` moved to a new `Logogram.with_surrogate` wither matching the existing `set_enclosure_type` / `set_erasure` idiom. The three `test_named_sign_*` tests take one `NamedTuple` case instead of 9/7/8 positional arguments. Verified by AST scan that nothing in the changed set is over either threshold. |
| F5 | **Fixed** | PR #743's description patched on GitHub: the `_StartParser.parse` row now says the parameter list is just `text`, the test count reads 4376, and a "Part 4 — review follow-ups" section describes this work. |
| F6 | **Fixed** | `NamePart` now delegates the whole `Token` interface — `clean_value`, `lemmatizable`, `alignable`, `get_key`, `set_unique_lemma`, `update_alignment`, `set_enclosure_type`, `set_erasure`, `merge`. The `set_*` withers rebuild through `NamePart.of`, so the wrapper and the wrapped token can no longer drift apart. 10 new tests. *(I did not take the other option — dropping the `Token` base class — because it would have removed the code paths behind two existing tests, and deleting tests needs explicit approval first.)* |
| F7 | **Partly fixed** (4 of 5) | `logger.py`, `lemmatization.py` and `atf_indexing_visitor.py` are clean under all three checkers; fixing `logger.py` also removed a `# pyre-ignore[6]`. **`legacy_atf_transformers.py` is deliberately untouched** — see below. |

### The two items deliberately not changed

**`legacy_atf_transformers.py` (one mypy error).** The error itself is a
one-word annotation fix. The problem is what editing the file costs: it enters
the `task type-pyright` scope, where it carries five more errors. Three of them
are `self._transform_tree`, `self.__visit_tokens__` and
`self._call_userfunc_token` — Lark internals that exist at runtime but are
absent from the `lark-stubs/visitors.pyi` shipped with lark 0.12.0, which
declares only `__init__`, `transform` and `__mul__` on `Transformer`. Clearing
them needs a suppression (banned by the PR's own no-`type: ignore` standard), a
shim declaration, or reimplementing Lark's private child-dispatch — all worse
than the error. Worth its own issue: either upgrade lark to a version that ships
inline types, or stop overriding Lark's private traversal.

**The test-factory duplication** (`lemmatized_fragment_text.py:111` /
`transliterated_fragment_lines.py:70`, 46 lines, mass 240). Not deduplicated,
and not in the current blocking six either. The two are not really duplicates:
`LEMMATIZED_FRAGMENT_TEXT` carries a `unique_lemma` on every word and uses
different readings (`u₄`, `š[u` against `Reading.of((ValueToken…))`), and their
line-2 words differ structurally. Factoring out the overlap would couple two
independent expected-value fixtures, so a change to one would silently move the
other — the failure mode that makes shared test fixtures painful. Explicit,
literal fixtures are the right call here. Happy to be overruled.

### Gate results after the fixes

| Gate | Result |
| ---- | ------ |
| `task format` | clean — 841 files already formatted |
| `task lint` (ruff) | All checks passed |
| `task type` (**pyre** — the gate CI enforces) | **No type errors found** |
| `task type-pyright` (96-file post-commit set) | **0 errors, 0 warnings** |
| `task test` | **4376 passed, 2 skipped, 1 xfailed** (302s) |
| Coverage on changed source modules | 98% (3642 stmts, 61 missed); **0 uncovered lines among lines these fixes add or modify**, checked by intersecting the missing-line spec with the diff hunks. Every module touched by the fixes is at 100%: `sign_token_base.py`, `named_signs.py`, `text_line.py`, `token_base.py`, `retrieve_annotations_helpers.py`, `token_schemas_signs.py`, `lemmatization.py`. The residual gaps in `logger.py` (25, 51-53), `atf_indexing_visitor.py` (55-57) and `chapter_schemas.py` (56-57) are all pre-existing lines outside the edited hunks. |
| `flake8 --max-line-length=120` (96 files) | 0 errors |
| `mypy --ignore-missing-imports` (96 files) | 1 error, in the untouched `legacy_atf_transformers.py` reached by import-following; was 5 |
| `task lint-md` | 0 errors |
| 250-line limit | every changed `.py` within limit, including the newly split `test_parse_word.py` |
| Running service | re-run against the rebuilt tree: 422 / 422 / 200 / markup / sign-search / texts all correct |
| `nameParts` wire format vs master | re-diffed with surrogate logograms added — byte-identical |

Pyre caught four errors that mypy and pyright both passed, and flake8 caught a
124-character line neither type checker cares about. Worth repeating that all
three checkers plus flake8 have to run.

<!-- markdownlint-enable MD013 -->

---

**Before merging, remove `TASK-743-todo.md`, `TASK-743-log.md`,
`TASK-743-review.md`, `TASK-743-fix-todo.md` and `TASK-743-fix-log.md` from the
branch.**
