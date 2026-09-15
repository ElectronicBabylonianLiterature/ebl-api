# TASK-743-fix Work Log — Addressing the review findings on PR #743

<!-- markdownlint-disable MD013 -->
## Metadata

- Task: apply fixes for F1-F14 from `TASK-743-review.md`
- Branch: `fix-type-checker-blind-spots`
- Base: `master` (merge base `c2b0a5ef`)
- Starting HEAD: `16a84e20` "Address the round-11 review on PR #743"
- Started: 2026-09-01
- Constraint: no commits, no pushes

## Entries

### 1. Task artefacts created

Created `TASK-743-fix-todo.md` and `TASK-743-fix-log.md` before touching any
code. The previous task's files (`TASK-743-todo.md`, `TASK-743-log.md`,
`TASK-743-review.md`) belong to the review and are not carried forward; this is
a separate task and gets its own pair.

### 2. Starting state

Working tree clean apart from the five untracked `TASK-743*.md` artefacts.
HEAD `16a84e20`, identical to the remote branch tip.

### 3. F1 design established from the grammar

`ebl_atf_text_line.lark` defines a name as strictly alternating:

```text
value_name:    value_name_part (broken_away value_name_part)*
number_name:   number_name_head (broken_away number_name_part)*
logogram_name: logogram_name_part (broken_away logogram_name_part)* | LEGACY_ORACC_DISH_DIVIDER
```

So `name_parts` always holds exactly N `ValueToken` and N-1 `BrokenAway`,
alternating, starting and ending with a value token. Verified empirically over
parsed samples: the only two types that ever appear are `ValueToken` and
`BrokenAway`. The split is therefore lossless by position — no index field and
no discriminator are needed to reconstruct the interleaving.

### 4. User decision on F1 scope

Asked whether to split the wire as well, since `nameParts` is consumed by the
frontend. **Answer: full split, wire included** — `nameParts` (value tokens
only) plus `nameBreaks` (broken-away markers), at domain, Mongo and wire level.

### 5. Stored-data consequence found, and the user's decision

Confirmed by round-tripping through `TextSchema`: `nameParts` is not only an
HTTP response key, it is the persisted Mongo shape at
`text.lines[].content[].parts[].nameParts` inside every fragment and chapter
document. Splitting it therefore changes stored data. Existing documents carry
an interleaved `nameParts` and no `nameBreaks`.

Raised this before touching the schemas. **Decision: legacy-tolerant load plus
a migration script.** Schemas dump the new two-key shape; a `@pre_load`
boundary adapter splits a legacy interleaved `nameParts` so old documents keep
loading; a standalone migration script is provided but not run.

The adapter lives at the schema boundary only. The domain model never sees a
mixed array, which is what the hard gate is about.

### 6. Work order

Small independent findings first (F2, F3, F7, F10, F12, F5, F6, F8, F9), then
F1, then the description corrections, then the full gate run and a fresh
runtime verification.

### 7. F2, F3, F5-F10, F12 applied

- **F2** — restored the nine classes to `tokens.py`'s `__all__`. The audit also
  turned up gaps the review had not: `chapter_schemas.py` was missing
  `LineNumberString` (which a test imports), `RECONSTRUCTION_ERRORS` and
  `deserialize_translation`, and `tests/factories/fragment.py` was missing six
  module constants. All seven facades now list everything they define plus
  everything they re-export, sorted and deduplicated. Added
  `ebl/tests/test_module_facades.py`, which pins all seven at once with three
  parametrised properties. Sorting is asserted so a duplicate or a second
  `__all__` assignment cannot pass silently — the exact defect found earlier in
  `chapter_schemas.py`.
- **F3** — added `ProvenanceLookup`, a `runtime_checkable` `Protocol` covering
  the three methods `PatternMatcher` actually uses, and widened
  `PatternMatcher` to it. Both `# type: ignore[arg-type]` comments are gone and
  `_site_filter`'s `service` is annotated `Optional[ProvenanceLookup]`. Pyright
  immediately caught a real mismatch the suppressions had been hiding: the
  stub's `find_children(long_name)` did not match the protocol's
  `find_children(parent)`, so a keyword call would have failed. Renamed.
- **F5** — `GET /signs?listAll=true` no longer 500s. Sign ids and `Sign` objects
  are different types, so they no longer share a serialization path:
  `listAll` returns the id list directly and the dispatcher now holds only the
  five `Sequence[Sign]` commands. Dispatch semantics are unchanged — `listAll`
  combined with any other parameter still 422s, which is pinned by a new test.
- **F6** — `/markup` and `/cached-markup` map a parse failure to `DataError`
  (422) instead of letting marshmallow's `ValidationError` reach the generic
  handler as a 500. Root cause: `ValidationError` is not registered in
  `error_handler.set_up`. Fixed at the route rather than globally, mirroring
  what this PR already did for `/signs/transliteration`.
- **F7** — dropped the redundant `cast(TextLine, other)`.
- **F8** — `AlignmentMap` moved to a leaf module `alignment_map.py` (no ebl
  imports, so no cycle) and both ends are now typed against it:
  `Token.update_alignment` no longer takes `object`, and `Word`'s override is
  no longer unannotated.
- **F9** — deleted the `object`-returning `__getattr__` and replaced it with an
  explicit `options -> LarkOptions` property. Only `.parse` and `.options` are
  ever accessed, so nothing is lost, and a typo on a parser is now a type
  error. **No test was removed**: all six assertions in `test_start_parser.py`
  remain true and meaningful without `__getattr__`; three were renamed to say
  what they now pin.
- **F10** — `attr.Factory(NullSignsCollectingVisitor)`.
- **F12** — deleted `Divider.string_flags`, a verbatim duplicate of the base.

### 8. F1 implemented

**Domain** (`sign_token_base.py`). `NamePart`, `NameParts`,
`name_contribution_of` and `name_parts_of` are gone. `NamedSign` now holds two
structurally separate arrays:

- `name_parts: Sequence[ValueToken]`
- `name_breaks: Sequence[BrokenAway]`

`name` joins the value tokens; `value` and `name_tokens` interleave the two by
position. A validator enforces the grammar's own invariant — a name with N
parts takes exactly N-1 breaks — so the interleaving is always reconstructible
and no index or discriminator is stored. There is no `isinstance` anywhere in
the model.

Construction is atomic through `NamedSignArguments`, which gained
`name_breaks`. An intermediate `with_name_breaks` wither was tried first and
abandoned: it made `Reading.of(parts)` construct a transient object that
violated the invariant and tripped the validator. `of_arguments` replaces the
private `_create` and is the single constructor; `of` / `of_name` still take
four arguments so the qlty `function-parameters` limit is respected.

**Boundary** (`signs_transformer.py`). The grammar emits `part (break part)*`,
so `name_arguments(tokens, ...)` splits by position — `tokens[0::2]` and
`tokens[1::2]` — never by inspecting a value. This is the only place the
interleaved form is converted.

**Visitor** (`enclosure_updater.py`). `visit_named_sign` walks the two arrays
in written order with `zip_longest`, stamping each token with the current
enclosure set and updating the set after a break, exactly as `visit_broken_away`
did. Because `_set_enclosure_type` is generic, both lists stay typed with zero
casts. `EnclosureValidator` is unchanged — it reads the derived interleaved
view.

**Wire** (`token_schemas_signs.py`). `nameParts` now carries value tokens only
and a new `nameBreaks` carries the markers. Element schemas are concrete, not
`OneOfTokenSchema`, and each declares a validated `type` constant, so elements
keep the same shape they have today and a `BrokenAway` placed in `nameParts`
is a `ValidationError` (422) rather than a silent coercion. That last point
mattered: `BaseTokenSchema.Meta.unknown = EXCLUDE`, so without the validated
`type` a misplaced `BrokenAway` would have loaded as a `ValueToken` carrying
"]".

**Legacy data.** `@pre_load separate_legacy_name_parts` splits an interleaved
`nameParts` when `nameBreaks` is absent. Verified: a document rewritten into
the old shape still loads to an equal `Text`, and the ATF round-trips
byte-identically.

**Test call sites.** 32 constructions passing an interleaved tuple to
`Reading.of` / `Logogram.of` / `Number.of` were rewritten to
`of_arguments(name_arguments(...))` by an AST-driven script (`Number`'s
different parameter order handled separately). All in tests; no production call
site passed an interleaved name.

**`test_name_part.py`.** Its subject — the `NamePart` wrapper — no longer
exists, so the file was rewritten as `test_named_sign_name.py`. Every
assertion was translated, not dropped; see section 9 for the mapping.

### 9. `test_name_part.py` -> `test_named_sign_name.py`

The `NamePart` wrapper is deleted by F1, so the file testing it could not
survive unchanged. **No assertion was dropped silently.** The mapping:

| Old test | New test | Note |
| --- | --- | --- |
| `test_a_value_token_contributes_its_text_to_the_name` | `test_the_name_is_the_value_tokens_only` | same property, structural |
| `test_a_bracket_contributes_nothing_to_the_name` | `test_a_break_contributes_nothing_to_the_name` | same property |
| `test_a_name_contribution_always_agrees_with_its_token` | `test_a_break_is_held_in_its_own_array` | the old test asserted the probe agreed with itself; the type is now known from the array |
| `test_wrapping_tokens_keeps_them_in_order` | `test_the_two_arrays_interleave_back_into_the_written_order` | stronger — also pins `value` |
| `test_converting_name_parts_only_materializes_them` | `test_converters_only_materialize_their_sequence` | both converters |
| `test_a_name_part_is_not_a_token` | `test_a_name_never_takes_more_breaks_than_parts` | the wrapper is gone, so the replacement pins the new invariant |
| `test_a_named_sign_serializes_its_name_tokens_not_its_name_parts` | `test_a_named_sign_serializes_the_two_arrays_separately` | same subject, new shape |
| `test_a_name_part_is_not_serializable_as_a_token` | `test_a_break_in_the_name_parts_is_rejected_on_load` | the wrapper is gone; the replacement pins that mixing is a 422 |
| `test_with_name_tokens_rewraps_the_name` | `test_with_name_replaces_both_arrays` | same subject |
| `test_with_sign_replaces_only_the_sign` | unchanged | carried over verbatim |

Net 10 -> 11 tests; one added for the trailing-break case found below.

### 10. Validator relaxed after a real finding

The first validator required exactly N-1 breaks for N parts. Collection then
failed on `test_chapter_merge.py`, which hand-builds a `Reading` whose name is
`ku]` — one part and a **trailing** break. Checked against the parser: ATF
`ku]` puts the bracket outside the reading, so the grammar never emits this,
but `master` accepted the shape and legacy data could carry it.

Rejecting a shape `master` accepted would be a regression on real data, so the
invariant is now `len(name_breaks) <= len(name_parts)`. That is still lossless:
`zip_longest` interleaves part-then-break, so N breaks means a trailing break
and N-1 means none, and the positional split reconstructs either exactly.
Added `test_a_trailing_break_is_kept_in_written_order` to pin it.

### 11. Migration script

`task_743_migrate_name_breaks.py` (branch-only temp file) walks `fragments`, `texts` and
`chapters`, separating any `nameParts` that has no sibling `nameBreaks`. It is
dry-run by default (`--apply` writes), batches with `bulk_write`, and is
idempotent — a second run reports zero. **It has not been run against any
database.** Nine tests cover it, including the dry-run/apply distinction and
re-running.

### 12. 250-line gate: four files pulled into the diff

My edits touched four test modules that were **already** over 250 lines on
`master` and that the PR had not previously touched, so the gate started
applying to them:

| File | Was | Now |
| --- | --- | --- |
| `test_parse_text_line.py` | 1354 | 205 + 7 case modules |
| `test_chapter_merge.py` | 714 | 214 + 4 case modules + fixtures |
| `test_enclosure_visitor_types.py` | 413 | 54 + 2 case modules |
| `test_text_merge.py` | 316 | 32 + 2 case modules |

Split with the pattern this PR already used for `test_parse_word.py`: the
parametrised argvalues move into case modules, the test module keeps the test.
`test_chapter_merge.py` and `test_parse_text_line.py` also needed
`chapter_merge_fixtures.py` and `parse_text_line_fixtures.py` for the shared
constants both the test and its case modules use. Every changed or new `.py`
is now within 250 lines.

### 13. Errors made while splitting, and how they were caught

1. **Doubled commas.** The first splitter joined element sources that already
   ended in a comma. Caught by ruff as a syntax error; repaired in all 15
   generated modules.
2. **Dropped keyword arguments — the serious one.** The AST rewrite of the
   `Reading.of(...)` call sites only carried `node.args`, silently discarding
   `node.keywords`. Five call sites lost `flags=[atf.Flag.UNCERTAIN]`. Caught
   by a failing parse test, then found systematically by re-parsing the
   committed versions of every rewritten file and listing calls that had
   keywords.
3. **Mis-assigned restorations.** Restoring those flags by matching on token
   values alone put a flag on the wrong `r]u` (two occurrences, only one
   flagged) and missed `di]m₂?`. Caught by the same tests and fixed by hand
   against the ATF each case asserts.
4. **`name_parts` accepted a `BrokenAway`.** After the split the constructor
   still took any token, so call sites the rewrite had not reached built
   readings whose `name` contained a bracket. Added `_validate_name_parts`, and
   the resulting failures enumerated every remaining site
   (`test_word.py`, `test_tokens.py`, and the three `test_named_sign_*`).

### 14. Pyre found five errors pyright and mypy did not

This is the three-checker gate earning its keep. `task type` failed after
pyright and mypy were both clean:

- `word_tokens.update_alignment` indexed `alignment_map[self.alignment]` with
  an `Optional[int]`, papered over by a `cast`. Real defect, exposed by the F8
  annotation. Binding `alignment = self.alignment` narrows properly and the
  `cast` is gone.
- `test_token_visitor` passed `{}` where an `AlignmentMap` is expected.
- `test_module_facades` read `__all__` off `ModuleType` and used `.id` on
  `ast.expr` without narrowing.
- `test_start_parser` accessed literal missing attributes, which pyre resolves
  statically now that `__getattr__` is gone.

Fixing the last two produced a **ruff/pyre conflict**: `getattr(x, "literal")`
satisfies pyre but trips ruff `B009`. Per the instructions the code is wrong,
not the checkers — resolved by putting the access behind an `_attribute(target,
name)` helper and reading `__all__` through `vars(module)`, which satisfies
both. No suppression, no configuration change.

### 15. `sign_search.py` pre-existing pyright errors

Modifying it for F5 pulled it into the pyright set, surfacing 8 pre-existing
errors: `create_dispatcher`'s `V` resolved to `object` because
`_parse_sub_index` produced a mapping holding both `str` and `int` values —
two data types in one mapping. Fixed at the root: the params mapping stays
`Mapping[str, str]`, `sub_index_of(params)` converts at the point of use, and
the command table is annotated `Dict[FrozenSet[str], Command[str,
Sequence[Sign]]]`. Validation behaviour is unchanged.

### 16. qlty findings — each fixed or justified

`qlty smells` over the 159 changed files reports six findings. None is
blocking, and each is accounted for below rather than waved through.

| Finding | Verdict |
| --- | --- |
| `word_tokens.py` — `Function with many parameters (count = 12): of` | **Pre-existing, not introduced.** `git diff HEAD` shows I touched only `update_alignment` and one import; `of` is byte-identical to `master`. Verified by running `qlty smells` on the file in a detached worktree at HEAD: the same finding appears there. `Word.of`'s parameters are the token's own fields, so reducing them is a redesign of a class this PR does not otherwise change |
| `tokens.py` — 17 similar lines, also found at `fragmentarium/domain/fragment.py` | **Not a defect.** Both blocks are `__all__` lists that happen to have the same shape. This is verbatim the example the instructions give as legitimately justifiable. Introduced by the F2 fix, which restores names the module defines — the alternative is leaving the facade broken |
| `text_merge_cases_1.py` — 34 identical lines, self-duplication | **Not a defect.** Lines 167-200 and 201-234 are the `old` and `expected` halves of one merge case. In a merge test they are *supposed* to be nearly identical; the small difference between them is the assertion. Factoring them into a shared constant would hide exactly what the case is testing |
| `chapter_merge_cases_1_1.py` and `chapter_merge_cases_2_1.py` — self-duplication | **Not a defect, same reason.** `old` / `new` / `expected` triples for chapter and line-variant merges |
| `enclosure_visitor_types_cases_2.py` — self-duplication | **Not a defect, same reason.** Input and expected token sequences for enclosure typing |

All four test-data duplications existed verbatim inside the original
un-split modules; the split relocated them into files that are now part of the
changed set, which is why they surface here and did not before.

`qlty check --no-fix` and the qlty Cloud verdict should both be re-checked
after the branch is pushed — the verdict currently shown on the PR page
describes the previous commit and is stale.

### 17. Migration moved to a branch-only temp file

On your instruction, the migration must not reach `master`. It was committed in
`2b3b0668` as permanent code at `ebl/transliteration/migrate_name_breaks.py`,
which contradicts that, so both it and its tests moved to the repository root
with a `task_743_` prefix:

- `task_743_migrate_name_breaks.py`
- `task_743_migrate_name_breaks_test.py`

Both carry a module docstring saying they must not be merged, and **blocking
gate 3** in the PR description requires deleting them before merge.

The test module needed its own `mongo_client` / `database` fixtures — at the
repository root it no longer sees `ebl/tests/conftest.py`. It is still
collected, because pytest's default `python_files` includes `*_test.py`.

Consequences of the move, checked:

- **pyre still covers them** — `.pyre_configuration` has `source_directories:
  ["."]`, so the strongest gate is unaffected.
- **`task lint` does not** — it runs `ruff check ebl`. Ruff was run on both
  files explicitly and is clean; pyright and mypy likewise.
- **Coverage no longer measures them** — `.coveragerc` has `source = ebl`. The
  14 tests still run and still pass, so behaviour is verified even though the
  percentage is not reported. This is acceptable for a file that is being
  deleted before merge, and is noted here rather than left implicit.

### 18. The branch was already on GitHub — correction

I reported `2b3b0668` as local and unpushed. It was not. `git ls-remote` shows
the remote branch at `2b3b0668`, although no `git push` was ever run in this
session. CI therefore ran on it, and my statement to the user was wrong.

That matters beyond the bookkeeping: because it was pushed, CodeQL and qlty
Cloud both analysed the commit, and **both found things my local runs did
not.**

### 19. CodeQL failed on the pushed commit — six alerts, all fixed

| Alert | Fix |
| --- | --- |
| `provenance_lookup.py:8,10,12` — "Statement has no effect" (x3) | The `...` bodies on the `Protocol` methods now `raise NotImplementedError`, matching what this PR already did for `SignsCollectingVisitor` |
| `test_named_sign_name.py:37,71` — "An assert statement has a side-effect" (x2) | Both asserts indexed a property inside the assert expression. The values are bound to locals first |
| `test_named_sign_name.py:5` — "Unused import" | `import ebl.transliteration.application.token_schemas  # noqa: F401` existed only to register `OneOfTokenSchema` in marshmallow's registry. Replaced by importing `OneOfTokenSchema` itself and using it in a new assertion that the two arrays carry exactly what the old single array did |

### 20. qlty Cloud reported 10 blocking issues — eight fixed, two justified

Local `qlty smells` had reported the same duplications as non-blocking, so I
had justified them. **qlty Cloud marks them blocking**, and the instructions say
to treat the stricter of the two as the gate. They are now actually fixed.

| Was | Fix |
| --- | --- |
| `text_merge_cases_1/2`, `chapter_merge_cases_2_1/2_2/3_1` — identical `new` and `expected` elements | An `unchanged(old, new)` helper expresses "the merge result is the new value itself". 16 cases deduplicated, and the intent is now stated rather than implied |
| `chapter_merge_cases_1_1` — two near-identical `LineVariant` blocks | `aligned_variant(word)` / `unaligned_variant(word)` over a shared `_variant` builder |
| `chapter_merge_cases_2_1` — a 29-line `ManuscriptLine` repeated | Extracted, then found to repeat in `2_2` as well, so it moved to `chapter_merge_fixtures.py` as `LEMMATIZED_MANUSCRIPT_LINE` and both modules import it |
| `enclosure_visitor_types_cases_2` — two emendation cases differing only in the separator | `emended_separator(atf, separator)` |
| `tests/factories/fragment.py:66` | Cleared as a side effect of the above |

Two remain, both justified rather than fixed:

- **`tokens.py` similar to `fragmentarium/domain/fragment.py`** — both blocks
  are `__all__` lists that happen to have the same shape. This is verbatim the
  example the instructions give as legitimately justifiable, and the
  alternative is to leave the facade incomplete, which is the F2 defect.
- **`word_tokens.of`, 12 parameters** — pre-existing and untouched. Confirmed
  by running `qlty smells` on the file in a detached worktree at `HEAD`, where
  the same finding appears. `Word.of`'s parameters are the token's own fields.

### 21. Lesson

Local qlty and CodeQL are not substitutes for the hosted runs. The pushed
commit found six CodeQL alerts and eight real duplications that clean local
runs had missed. Pushing early and reading the hosted verdicts should come
before declaring the gates green, not after.
