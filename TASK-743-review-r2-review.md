# TASK-743-review-r2 — Review of PR #743 (round 2)

**PR:** [#743 Make the ATF parser visible to the type
checkers](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743)
**Branch:** `fix-type-checker-blind-spots` -> `master`
**Head:** `aed3979f` · **Base (merge-base):** `32f6ddae` ·
**master now:** `c2b0a5ef` · 105 files, +5953 / -2966
**Review decision on GitHub:** CHANGES_REQUESTED (Fabdulla1, at
`19a2f464`)

## Status: every finding addressed

All fixes are on the working tree and **uncommitted**. The merge of
`origin/master` was made with `git merge --no-commit` at the user's
explicit request and is likewise uncommitted.

| Gate | Before (`aed3979f`) | After |
| --- | --- | --- |
| `task type-pyright` | **19 errors, 1 warning** | **0 errors, 0 warnings** |
| `task type` (pyre) | pass | pass |
| `task format` / `task lint` | pass | pass |
| flake8, mypy (changed) | pass | pass |
| 250-line limit | pass | pass |
| `task lint-md` | pass | pass |
| Mergeable | **CONFLICTING** | merged clean, #749 preserved |

Resolutions, in short:

- **F1** — merged master. Git's rename detection carried #749's six
  `TYPE` abbreviations across the `lark_parser/` -> `atf_grammar/`
  rename; `docs/ebl-atf.md` auto-merged. #749's own `test_parse_siglum`
  already pins all six against the renamed grammar.
- **F2** — driven to zero structurally, no suppression: two methods
  added to the `SignRepository` ABC (and implemented in
  `MemoizingSignRepository`, which had been silently missing them), a
  single typed `_load_signs` helper replacing six duplicated
  marshmallow loads, precise types on the `nameParts` (de)serialisers,
  and explicit casts at the `svg2png` and marshmallow boundaries.
- **F3** — `getattr` probe replaced with `isinstance(sign, NamedSign)`,
  private attribute reads replaced with public properties. This turned
  out to fix a live 500 (see below).
- **F4** — the unused `start` parameter removed. `__getattr__` and its
  three tests kept, at the user's direction.
- **F5** — URL comment wrapped. **F6** — the five `Museum` entries are
  3-tuples again and the enum is byte-identical to master.
  **F7** — two focused `reset()` tests added. **F8** — the duplicated
  first `TextLine` extracted to one shared module. **F12** — annotations
  added; the bare `Callable` given a checked return type.
- **F13** — deferred: the user chose to keep the tracking files until
  merge.

### A live 500 fixed as a side effect of F3

The old `extract_word_sub_indexes` read `word._parts`. `Erasure` tokens
expose `parts` but not `_parts`, so any transliteration containing an
erasure raised `AttributeError` — which is **not** in `LINE_PARSE_ERRORS`
and so escaped the route's handler as a **500**.

```text
GET /signs/transliteration/°nu : ši\ku°
  before: AttributeError: 'Erasure' object has no attribute '_parts'
  after:  200 [{"unicode": [9999]}, ...]
```

Differential check over 17 ATF inputs: old and new produce identical
output on every case that the old code survived, and the erasure case is
the only behavioural difference. Pinned by a new route test.

## Summary

The PR does what it says: the grammar directory rename makes the ATF
parser visible to the checkers, pyre is clean, the full suite passes
(4308 passed, 2 skipped, 1 xfailed), every line the PR adds or modifies
is covered, and no changed `.py` file exceeds 250 lines. The 422 fix on
`GET /signs/transliteration/{line}` that the last human review could not
find **is** present at `aed3979f` and I confirmed it against a running
service.

Two things block merge. The branch is in **merge conflict with master**,
and the conflicting file is the renamed grammar — resolved carelessly it
silently drops the six manuscript types #749 just added. And
**`task type-pyright` fails with 19 errors** on the PR's own changed
set, which is hard gate 4 and contradicts the PR description's claim of
zero. Three of Fabdulla1's five points are still open, all minor.

Sourcery has **not** reviewed the last two commits — its run was skipped
because the diff exceeds its 150 000-character limit — so there is no bot
review of the largest and most invasive part of this PR.

### Gate results at `aed3979f` (clean working tree)

| Gate | Result |
| --- | --- |
| `task format` | pass (831 files already formatted) |
| `task lint` (ruff) | pass |
| `task type` (pyre) | **pass, no type errors** |
| `task type-pyright` | **FAIL — 19 errors, 1 warning** |
| `task test` | pass — 4308 passed, 2 skipped, 1 xfailed |
| Coverage on PR-touched lines | pass — 0 uncovered |
| `flake8 --max-line-length=120` (changed) | pass |
| `mypy --ignore-missing-imports` (changed) | pass (see F12) |
| 250-line limit (77 changed `.py`) | pass |
| `task lint-md` | pass — 0 errors |
| CI at head | all green; `qlty check` "8 blocking issues" |
| Mergeable | **CONFLICTING / DIRTY** |

## Findings

### F1 — Merge conflict with master drops #749's manuscript types

**Severity: High (blocking).**

`gh pr view` reports `mergeable: CONFLICTING`, `mergeStateStatus: DIRTY`
across three polls. The legacy three-way `git merge-tree` shows two
conflicts:

- `docs/ebl-atf.md` — changed in both.
- `ebl/transliteration/domain/atf_parsers/lark_parser/`
  `ebl_atf_abbreviations.lark` — **modify/delete**. Master's #749 added
  `MultCol`, `Coll`, `StuTea`, `SchLen`, `Prism`, `Unc` to the `TYPE`
  rule at the old path; this branch deleted that path when it renamed
  the directory to `atf_grammar/`.

Git's `ort` strategy follows the rename and carries the six types into
`atf_grammar/ebl_atf_abbreviations.lark` (I verified the merged blob).
GitHub still reports the conflict, so a human will resolve it — and
"keep ours" is the natural, wrong choice. The branch's copy of that file
contains **zero** of the six new types.

Reproduce with:

```bash
git fetch origin master
git merge-tree $(git merge-base HEAD origin/master) HEAD origin/master \
  | grep -n 'changed in both\|removed in local'
# -> docs/ebl-atf.md changed in both
# -> .../lark_parser/ebl_atf_abbreviations.lark removed in local
grep -c 'MultCol\|StuTea\|SchLen\|Prism' \
  ebl/transliteration/domain/atf_parsers/atf_grammar/ebl_atf_abbreviations.lark
# -> 0
```

**Recommendation.** Merge `origin/master` into the branch and resolve
explicitly: append the six types to
`atf_grammar/ebl_atf_abbreviations.lark`, take master's `docs/ebl-atf.md`
additions, and keep the branch's `lark_parser/` -> `atf_grammar/` path
edit. Then add a parse test for one new type (e.g. `Prism`) so the
regression cannot recur silently.

### F2 — `task type-pyright` fails: 19 errors on the changed set

**Severity: High (blocking — hard gate 4).**

The PR description states "task type-pyright (0 errors)". Running the
Taskfile's own pinned command at `aed3979f` gives 19 errors and 1
warning. Pyright resolves the project venv correctly (a probe file
reports the fully typed `marshmallow.Schema.load` signature), so these
are real diagnostics, not unresolved-import noise.

- `signs/infrastructure/mongo_sign_repository.py` — 6.
  `SignSchema().load(...)` is typed `Unknown | list | dict | None`, not
  `Sequence[Sign]`.
- `tests/corpus/test_chapter_manuscript_schemas.py` — 6. Subscripting a
  load result that may be `None`.
- `signs/web/signs.py` — 3. `find_signs_by_order` and
  `get_unicode_from_atf` are not declared on the `SignRepository` ABC;
  plus a `b64encode` argument type.
- `transliteration/application/token_schemas_signs.py` — 2.
  `_dump_name_parts` and `_load_name_parts` declare `-> list`.
- `signs/infrastructure/sign_unicode_lookup.py` — 2. `name_parts` and
  `sub_index` are not accessible on `Token`.
- `fragmentarium/application/annotations_service.py` — 1 warning.
  `len(x) and f(x)` value unused.

Reproduce with:

```bash
git diff --name-only --diff-filter=ACMR origin/master...HEAD -- '*.py' \
  | xargs npx --yes pyright@1.1.411
# -> 19 errors, 1 warning, 0 informations
```

**Recommendation.** Fix structurally, as the earlier round did. The
`signs.py` pair is the cheapest and most valuable: `find_signs_by_order`,
`get_unicode_from_atf` and `list_all_signs` are called through a
`SignRepository`-typed field but declared only on `MongoSignRepository`.
Adding them to the ABC closes three errors and fixes a genuine interface
lie. The `mongo_sign_repository` and test-file errors want the same
explicit `cast` at the marshmallow boundary the PR already uses
elsewhere. See F10 and F12 for the remaining two files.

I have not investigated why the author's run reported zero; the command
above is reproducible on a clean tree at the head commit.

### F3 — `extract_word_sub_indexes` still discriminates by probing

**Severity: Medium.**

`ebl/signs/infrastructure/sign_unicode_lookup.py:15`

```python
def extract_word_sub_indexes(word) -> Iterable[Tuple[str, int]]:
    for part in word._parts:
        if isinstance(part, Determinative):
            part = part._parts[0]
        if getattr(part, "name_parts", []):
            yield (part.name_parts[0].name_contribution, part.sub_index)
```

The code is byte-equivalent to master's `_extract_word_subIndex`, but the
PR **moved** it into a new module, which brings it into scope. It asks
"does this object have `name_parts`?" to learn whether it is a
`NamedSign` — the exact probe the data hard gate forbids ("Fix the model;
do not write a smarter probe"). It is also why pyright cannot narrow
`part`, producing two of the 19 errors in F2, and it reads three private
attributes (`word._parts`, `part._parts`, `line._content`).

**Failure scenario.** Any new `Token` subclass that happens to expose a
`name_parts` attribute is silently treated as a named sign here, and the
`sub_index` access then raises `AttributeError` at request time on
`GET /signs/transliteration/{line}`. The probe cannot be checked by any
of the three checkers.

Reproduce with:

```bash
npx --yes pyright@1.1.411 ebl/signs/infrastructure/sign_unicode_lookup.py
# -> Cannot access attribute "name_parts" for class "Token"
# -> Cannot access attribute "sub_index" for class "Token"
```

**Recommendation.** `if isinstance(part, NamedSign):` — one line, closes
both pyright errors, and the type checker then knows `sub_index` exists.
While there, annotate the parameters: `word` and `result` are bare, and
the coding standard requires type hints on every function.

### F4 — `_StartParser.parse(start=...)` is dead, not merely untested

**Severity: Medium.**

Fabdulla1 asked for a test pinning `_StartParser.parse(..., start="...")`.
The stronger finding is that **no caller anywhere passes it**:

- The seven `_StartParser` instances (`WORD_PARSER`, `NOTE_LINE_PARSER`,
  `MARKUP_PARSER`, `PARALLEL_LINE_PARSER`, `TRANSLATION_LINE_PARSER`,
  `PARATEXT_PARSER`, `LABEL_PARSER`) are only ever called as
  `.parse(atf)`.
- `MANUSCRIPT_PARSER`, the one call site that does pass `start=`
  (`ebl/corpus/domain/parser.py:40`), is a raw `Lark`, not a
  `_StartParser`.
- `test_start_parser.py:22` and `:53` pass `start=` to `LINE_PARSER`,
  which is also a raw `Lark`.

The commit message states "No caller passes anything but the text, so
take an optional `start` instead" — but then keeps the parameter.

Related: `_StartParser.__getattr__` returns `object` and has **no
production consumer**; its only users are the three tests written to
cover it (`test_getattr_delegates_to_wrapped_parser`,
`test_getattr_raises_for_missing_attribute`,
`test_getattr_without_initialised_parser_raises_attribute_error`). An
untyped `-> object` escape hatch is the exact hole this PR set out to
close, kept alive by tests that exist only to cover it.

Reproduce with:

```bash
grep -rn "WORD_PARSER\.\|NOTE_LINE_PARSER\.\|MARKUP_PARSER\.\|LABEL_PARSER\.\|\
PARATEXT_PARSER\.\|PARALLEL_LINE_PARSER\.\|TRANSLATION_LINE_PARSER\." \
  --include=*.py ebl
# no occurrence passes start=
```

**Recommendation.** Drop the `start` parameter and the `__getattr__`
proxy, and delete the three tests that exist only to cover the proxy —
this is code removal, so it needs your explicit approval before anyone
touches those tests. If the proxy must stay (something outside this
repo may rely on `WORD_PARSER.options`), type it rather than returning
`object`. Either way, F4 as Fabdulla1 phrased it — "add a test" — is the
weaker fix.

### F5 — Fabdulla1: 169-character URL in `annotations_service.py`

**Severity: Low. Still present, but not a lint failure.**

`ebl/fragmentarium/application/annotations_service.py:140` is a
169-character line. It does **not** fail `flake8 --max-line-length=120`:
pycodestyle exempts a comment made of exactly `#` plus one long token
(`maximum_line_length`, the "long URLs in comments" special case). The
Hilprecht URL the PR did split was a string literal inside a tuple —
more than two chunks — so it genuinely raised E501. The two cases differ
mechanically, which is why one was fixed and the other was not.

**Recommendation.** Cosmetic. Either wrap it at path boundaries for
consistency, or reply to Fabdulla1 with the pycodestyle distinction so
the point can be closed. It is also outside the PR's diff for that file.

### F6 — Fabdulla1: five `Museum` entries changed value shape

**Severity: Low. Still present.**

`PRIVATE_COLLECTION_CHICAGO`, `..._OF_J_CARRE`, `..._OF_M_FOEKEN`,
`..._OF_W_LAMPLOUGH` and `..._OF_Z_YILDIZ` were 3-tuples on master and
are 4-tuples in `museum_entries_m_s.py` (trailing `""` for `url`),
because the new `MuseumEntry = tuple[str, str, str, str]` alias is
uniform.

Confirmed harmless: `Museum` is serialised by `NameEnumField(Museum)` in
`fragment_schema.py:54`, so `.value` is never on the wire, and nothing in
the repo reads `.value` or looks a member up by value. `museum_name`,
`city`, `country` and `url` are identical either way, since `url`
defaults to `""`.

**Recommendation.** Fabdulla1's preference is reasonable and cheap — a
"value-preserving split" should preserve values. Either restore the
3-tuples (and widen the alias to
`tuple[str, str, str] | tuple[str, str, str, str]`), or reply that the
uniform 4-tuple was deliberate and is unobservable. Note `UNKNOWN` and
`HYPERURANION` in `museum.py:111-112` are still 1-tuples, so the alias
does not describe every member anyway.

### F7 — Fabdulla1: no focused test for `SignsVisitor.reset()`

**Severity: Low. Still open.**

No test calls `reset()` on any visitor. It is covered only indirectly,
through `transliteration_query.py:147`, which is why line coverage passes
and the gap is invisible.

**Recommendation.** Add the test Fabdulla1 described: accumulate a real
result, assert non-empty, `reset()`, assert empty. `reset()` is now an
abstractmethod on `SignsCollectingVisitor`, so it is part of a contract
and deserves a direct assertion.

### F8 — Fabdulla1: qlty comments

**Severity: Low.**

Eight blocking issues, nine bot comments. Every one is **pre-existing
code that a file split relocated**, not newly written logic:

| Issue | Origin |
| --- | --- |
| `retrieve_annotations_helpers.py:53` `match` | identical to master |
| `named_signs.py:74` `of`, 6 params | from `sign_tokens.py` |
| `named_signs.py:94` `of_name`, 6 params | from `sign_tokens.py` |
| `test_named_sign_*.py` param counts | from `test_sign_tokens.py` |
| 46 similar lines, two factory modules | halves of `factories/fragment.py` |

Precedent: #740 was approved and merged carrying ~14 unresolved qlty
`function-parameters` / `similar-code` comments of exactly these kinds.

**Recommendation.** The only one worth real effort is the duplication:
the lemmatized fixture is the transliterated fixture plus lemmas, so
deriving one from the other would remove 46 duplicated lines and a
maintenance trap. The parameter-count and return-count findings are noise
against relocated code; reply to close them rather than restructuring
working code to satisfy a metric.

### F9 — Sourcery's `TextLine.merge` finding is no longer this PR's

**Severity: None — acknowledge and close.**

Sourcery flagged `merge(self, other: L) -> L` with `cast(L, TextLine...)`
as unsound for `TextLine` subclasses, at commit `e3150b3d`. That code
reached master independently via #740 (`a238304d`).
`git diff origin/master...HEAD -- ebl/transliteration/domain/text_line.py`
is now **empty** — the file is identical to master.

The underlying concern is still technically true of master: if `L` binds
to a `TextLine` subclass, callers get a plain `TextLine` typed as `L`. No
subclass of `TextLine` exists today, so nothing is broken.

**Recommendation.** Reply to Sourcery that the code is no longer in this
diff. If the soundness point is worth pursuing, open a separate issue
against master.

Also note: **Sourcery's latest run was skipped** — "your pull request is
larger than the review limit of 150000 diff characters". Commits
`19a2f464` and `aed3979f`, which contain the file splits, the `NamePart`
rework and the 422 fix, have had no bot review at all.

### F10 — `NamePart` and the data hard gate: passes, deliberately

**Severity: None — recorded so it is not "fixed" later.**

`name_parts` was `Sequence[Union[ValueToken, BrokenAway]]` and every
reader `isinstance`-probed. It is now `Sequence[NamePart]`, one type per
array, with classification done once in `NamePart.of`.

A strict reading could object that `NamePart.token` still holds either a
`ValueToken` or a `BrokenAway`, and that `name_contribution` is a
precomputed discriminator (`""` for one type, non-empty for the other).
Two separate arrays — the gate's usual remedy — is **not** available
here: the interleaved order of `ValueToken`, `BrokenAway`, `ValueToken`
is what `k[u]r` means, and splitting the arrays would destroy it. The
wrapper is the right call, and I verified it is behaviour-preserving.

Verified in-process against the running tree:

```text
'1. k[u]r-ra'  atf-roundtrip=True  equal=True
   name='kur'  nameParts=[ValueToken, BrokenAway, ValueToken,
                          BrokenAway, ValueToken]
NamePart leaked to wire: False
all name_parts are NamePart: True
```

`name` for `k[u]r` is `kur`, identical to master's `isinstance`-filtered
`"".join(...)`. `NamePart` never reaches the wire.

### F11 — Wire-format field swap changes validation error shape

**Severity: Low — note only.**

`NamedSignSchema.name_parts` went from
`fields.List(fields.Nested("OneOfTokenSchema"), required=True)` to
`fields.Function(_dump_name_parts, _load_name_parts, required=True)`.
The serialised payload is unchanged (verified above), but marshmallow no
longer wraps per-element errors with their index — an invalid third
`nameParts` entry now reports against the whole field instead of
`{"nameParts": {2: ...}}`. Only matters if a client parses the error
detail.

### F12 — Missing type hints on new module-level functions

**Severity: Low.**

The coding standard requires type hints on every function and discourages
`Any`. New or relocated functions that do not comply:

- `sign_unicode_lookup.py:11,20` — `word` and `result` unannotated.
- `token_schemas_signs.py:27,33` — `named_sign` and `value` unannotated;
  both return bare `list`, which is 2 of the 19 pyright errors in F2.
- `annotations_service.py:144` — `handlers: Dict[type, Callable]`; a bare
  `Callable` is `Callable[..., Any]`.

`mypy --ignore-missing-imports` over the 77 changed files reports 5
errors, but all 5 are in modules the changed files import and the PR does
not touch (`atf_importer/application/lemmatization.py`,
`.../logger.py`, `atf_importer/domain/legacy_atf_transformers.py`,
`.../atf_indexing_visitor.py`). Gate 8 as scoped to changed files
passes.

### F13 — Committed task-tracking files must be removed before merge

**Severity: Low — merge checklist.**

The branch carries six committed tracking files:
`TASK-743-fixes-{log,todo}.md`, `TASK-743-merge-{log,todo}.md`,
`TASK-743-review-{log,todo}.md`, `TASK-743-review-fixes-{log,todo}.md`,
`TASK-743-size-{log,todo}.md` and `TASK-743-review.md`. This round adds
`TASK-743-review-r2-{todo,log,review}.md`, currently uncommitted.

**Recommendation.** Delete all of them before merge.

## Severity

| # | Finding | Severity | State |
| --- | --- | --- | --- |
| F1 | Merge conflict drops #749's types | **High** | **Fixed** |
| F2 | `task type-pyright` fails (19 errors) | **High** | **Fixed** |
| F3 | `extract_word_sub_indexes` probes by `getattr` | Medium | **Fixed** |
| F4 | `_StartParser` `start=` dead | Medium | **Fixed** |
| F4b | `__getattr__` proxy dead | Medium | Kept, user's call |
| F5 | 169-char URL (Fabdulla1) | Low | **Fixed** |
| F6 | Five `Museum` 4-tuples (Fabdulla1) | Low | **Fixed** |
| F7 | No focused `reset()` test (Fabdulla1) | Low | **Fixed** |
| F8 | qlty: duplication | Low | **Fixed** |
| F8b | qlty: parameter / return counts | Low | Kept, relocated code |
| F9 | Sourcery `TextLine.merge` | None | Not in this diff |
| F10 | `NamePart` vs data hard gate | None | Passes, deliberate |
| F11 | `fields.Function` error shape | Low | Note only |
| F12 | Missing type hints | Low | **Fixed** |
| F13 | Tracking files committed | Low | Deferred to merge |
| — | 500 on erasure transliterations | Medium | **Fixed** (new) |

## Reproduction Steps

All of the below were run at `aed3979f` on a clean working tree.

```bash
# Gates
poetry run ruff format --check ebl
poetry run ruff check ebl
poetry run pyre check                                    # no type errors
git diff --name-only --diff-filter=ACMR origin/master...HEAD -- '*.py' \
  | xargs npx --yes pyright@1.1.411                      # 19 errors  <-- F2
env -u MONGODB_URI -u MONGODB_DB poetry run pytest -q --cov=ebl \
  --cov-report=term-missing                              # 4308 passed
git diff --name-only origin/master...HEAD -- '*.py' \
  | xargs poetry run flake8 --max-line-length=120        # clean
git diff --name-only origin/master...HEAD -- '*.py' \
  | xargs poetry run mypy --ignore-missing-imports       # see F12
npx markdownlint-cli2@0.22.1 "**/*.md" '#.venv/**' '#.pytest_cache/**'

# Merge state                                            # F1
git fetch origin master
git merge-tree $(git merge-base HEAD origin/master) HEAD origin/master \
  | grep -n 'changed in both\|removed in local'
```

### Runtime verification

`.env` was **never** sourced — it points at the production cluster.
`create_app(create_context())` was served with waitress on
`127.0.0.1:8123`, `MONGODB_URI` pinned to `mongodb://127.0.0.1:27017`,
throwaway database `ebl_review_743_r2_smoke`, a freshly generated
throwaway `AUTH0_PEM`, `SENTRY_DSN` unset. Re-run against the current
head, not carried over from the previous round.

| Request | Result | Exercises |
| --- | --- | --- |
| `GET /signs/transliteration/ku-nu-szi` | 200 | `atf_grammar/`, split repo |
| `GET /signs/transliteration/$$$` | **422** | F10 of round 1, now fixed |
| `GET /signs/transliteration/(((((` | **422** | same, the exact round-1 500 |
| `GET /markup?text=@i{italic} and plain` | 200 | `parse_markup_paragraphs` |
| `GET /fragments/query?transliteration=..` | 200 | `SignsVisitor.reset()` |
| `GET /fragments?random=true` | 200 | dispatcher generics |
| `GET /fragments?needsRevision=true` | 200 | same |
| `GET /fragments?interesting=true` | 200 | same |
| `GET /fragments?bogus=1` | 422 | dispatcher error path |

## Recommendation

**Request changes.** Two blockers, both cheap relative to the size of
this PR:

1. **F1** — merge master, resolve the `.lark` modify/delete by hand so
   #749's six manuscript types survive the rename, and add a parse test
   for one of them.
2. **F2** — drive `task type-pyright` back to zero. Start with the three
   `signs.py` errors by declaring `find_signs_by_order`,
   `get_unicode_from_atf` and `list_all_signs` on the `SignRepository`
   ABC; that also fixes a real interface lie. F3 and F12 close four more
   between them.

Then close out the human review: F7 is a ten-line test, F4 is code
removal (needs your approval for the test deletions), and F5, F6 and F8
can reasonably be answered in a reply rather than changed — F5 because
pycodestyle exempts the line, F6 because `.value` is never observed, F8
because every finding is relocated pre-existing code and #740 set the
precedent for merging with them open.

Two process points. Sourcery has reviewed **none** of the last two
commits because the diff exceeds its size limit, so the file splits, the
`NamePart` rework and the 422 fix have had no bot review — the human
review carries more weight here than usual. And re-request review from
Fabdulla1 once F1 and F2 are addressed: the CHANGES_REQUESTED verdict
stands against `19a2f464` and their first point is already fixed at
`aed3979f`.

Finally, delete every `TASK-743-*.md` file, including the three this
round added, before merging (F13).
