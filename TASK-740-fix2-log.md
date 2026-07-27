# TASK-740-fix2 — Work Log

Task: address every finding in `TASK-740-review2.md` for PR #740.
Records what was actually done, including every error and its recovery.

## Entries

### 1. Task artefacts created

Created `TASK-740-fix2-todo.md` and this log before touching any code. The
review task's `review2` files do not carry forward.

Starting state: `HEAD` = `84acd6f7`, working tree clean apart from the three
untracked `TASK-740-review2*.md` artefacts from the review task.

### 2. Blocker for verification: pyre cannot run in this container

The single most important gate here is `task type` (pyre), because F1 is
precisely a pyre error and CI is red on it. During the review I established
pyre aborts in this container — it initialises an 8 GB shared-memory heap and
the box has 2 CPUs / ~2 GB free RAM.

Fixing a pyre error without being able to run pyre would mean shipping an
unverified fix for the exact gate that is failing. Attempting to make pyre
runnable before making the change.

**Resolved.** The container has passwordless sudo and 39 GB free on `/tmp`, so
I added a temporary 8 GB swap file:

```bash
sudo fallocate -l 8G /tmp/pyre-swapfile
sudo chmod 600 /tmp/pyre-swapfile && sudo mkswap /tmp/pyre-swapfile
sudo swapon /tmp/pyre-swapfile
```

`poetry run pyre check` then completed and reproduced the CI error **exactly**:

```text
ebl/transliteration/application/token_schemas_words.py:52:0
Uninitialized attribute [13]: Attribute `word_class` ... never initialized.
```

This is a temporary, reversible environment change and must be undone at the
end of the task (`sudo swapoff /tmp/pyre-swapfile && sudo rm /tmp/pyre-swapfile`).
No repository file was touched to achieve it.

### 3. F1 + F7a fixed together

The pyre error and the qlty `similar-code` duplication had the same root
cause: the `word_class` `ClassVar` existed only so one shared `make_token`
body could be reused across `WordSchema` and `LoneDeterminativeSchema`.

Removed `word_class` entirely and replaced the three near-identical
`make_token` bodies with two module-level helpers in
`token_schemas_words.py`:

- `shared_word_arguments(data)` — the nine keyword arguments common to
  `Word.of`, `LoneDeterminative.of`, `AkkadianWord.of` and `GreekWord.of`.
- `load_word(factory, parts, data, **arguments)` — applies the factory and
  `set_enclosure_type`.

Each `make_token` is now a single call. `AbstractWordSchema` retains only the
`@post_dump` hook, so `AkkadianWordSchema` / `GreekWordSchema` keep *not*
inheriting it, exactly as before.

**Care taken over an equality trap.** The original `AbstractWordSchema` passed
`data["parts"]` (a **list**) to `Word.of`, while the Akkadian and Greek
schemas passed `tuple(data["parts"])`. `AbstractWord` is a frozen attrs class,
so `parts` being a list vs a tuple changes `__eq__`. I deliberately preserved
each schema's original conversion rather than unifying it, which would have
broken token equality in tests.

Verified: `poetry run pyre check` → **`No type errors found`**, exit 0.
`ebl/tests/transliteration` → 1668 passed, 1 skipped, 1 xfailed.

### 4. F2 fixed — and an error I made along the way

`task type-pyright` went from **41 errors to 0**.

**F2b** (1 error): `LemmatizationToken(value, ("aklu I",))` in
`test_fragment_repository_updates.py` — `unique_lemma` is
`Sequence[WordId] | None`, so the literal needed wrapping as
`(WordId("aklu I"),)`.

**F2a** (40 errors in `ebl/tests/factories/archaeology.py`), in two steps:

1. 31 × `reportPrivateImportUsage` — `factory/__init__.py` ships `py.typed`
   but declares no `__all__`, so every `factory.X` attribute access is a
   private import. Fixed by importing from the defining modules:
   `factory.base`, `factory.declarations`, `factory.faker`,
   `factory.helpers`, `factory.random`. Submodule access
   (`factory.fuzzy.FuzzyChoice`) is not flagged and was left alone.
2. The remaining 9 — 5 × `Meta` override, 2 × `list_factory`, 2 × `Maybe`.

**Error I made:** I told the user these last 9 could not be fixed without a
suppression or a config change, and asked them to choose between accepting
them, authorizing suppressions, or reverting. **That was wrong**, and the user
correctly rejected it. What I had actually established was only that *one*
approach failed (`class Meta(Factory.Meta)` — `Factory.Meta` is popped by
`FactoryMetaClass`, so it exists statically but never at runtime, and
`class Meta(BaseMeta)` is a sibling, not a subtype). I generalised from that
one dead end to "impossible" without probing the alternatives.

On being pushed, I probed properly and found all three fix cleanly:

- **`Meta` override (5)** — `factory.helpers.make_factory(model, **declarations)`
  builds the `Meta` class internally, so no subclass ever overrides
  `Factory.Meta`. Converted all five factory classes to `make_factory`.
  `class Params` survives as a `Params=` keyword argument, which the
  metaclass picks up exactly as it does a nested class.
- **`list_factory` (2)** — `List.__init__(self, params, list_factory='factory.ListFactory')`
  infers `str` from its default. factory_boy accepts a dotted path there as
  first-class API, so `TUPLE_FACTORY = "ebl.tests.factories.collections.TupleFactory"`
  types cleanly and resolves lazily at runtime.
- **`Maybe` (2)** — `Maybe(decider, yes_declaration=SKIP, no_declaration=SKIP)`
  infers the sentinel type `Skip`, so *any* real declaration is an error.
  Replaced with `LazyAttribute(_random_day)` drawing from
  `factory.random.randgen` — the same seeded generator `FuzzyChoice` uses, so
  reproducibility under `reseed_random` is unchanged.

Verified: `npx pyright@1.1.411 ebl/tests/factories/archaeology.py` → 0 errors;
`task type-pyright` → **0 errors**; `test_archaeology_schemas.py`,
`test_findspot_repository.py`, `test_fragment_archaeology_route.py` → 77
passed.

**Lesson recorded:** "I could not fix it with the first approach I tried" is
not "it cannot be fixed". Probe the alternatives before escalating to the user
with a false constraint.

### 5. F8 — my review overstated the defect

The review claimed transliteration updates drop **all** word-level
annotations. I probed the real behaviour before changing anything, and that
was **wrong**.

`Merger` keeps the *old* token when a word is unchanged, so unchanged words
already retain their `named_entities` / `realia`; only the changed word loses
its own. Probe on `1. ku-nu-uk ba-bi-lu a-na` → `1. ku-nu-uk ba-bi-lu szu-nu`:

```text
BEFORE  Word-1 [Entity-1]  Word-2 realia [Realia-1]  Word-3 [Entity-2]
AFTER   Word-1 [Entity-1]  Word-2 realia [Realia-1]  Word-3 []
```

So the existing behaviour already matched the user's rule of thumb at the
*word* level. The genuine defect was narrower: `Entity-2` stayed in
`fragment.named_entities` with no word referencing it, so `/named-entities`
returned it with `"span": []` — an orphan.

Fixed exactly that: `retain_referenced` in `named_entity.py` plus
`Fragment.drop_orphaned_annotations`, called at the end of
`update_transliteration`. Unchanged words keep annotations; a changed word's
annotation is dropped from the fragment-level array too.

New tests in `ebl/tests/fragmentarium/test_annotations_after_transliteration.py`
(6 cases): unchanged words keep, changed word loses, orphaned entity dropped,
orphaned realia dropped, unrelated edit keeps everything, full replacement
drops everything. All pass.

**250-line gate incident:** the first version pushed `fragment.py` to **251
lines**, breaking the hard gate. Caught it immediately with `wc -l`, tightened
`drop_orphaned_annotations` from 12 lines to 9 by hoisting the two id-set
comprehensions into locals. Now 248.

### 6. F4 — mypy, 5 errors down to 1

- `fragment_metadata.py` `PARSE_ERRORS` — imported from
  `lark_parser_errors` instead of via the `lark_parser` re-export, matching
  what `signs_visitor.py` and `label_schemas.py` already do. Fixed.
- `text_line.py:120` — `attr.evolve(token, unique_lemma=…)` where `token` is
  a bare `Token`. Fixed with `cast(AbstractWord, token)`.
- `text_line.py:147` — `merge` widened the return type to
  `Union["TextLine", L]`. Root cause was that `text_line.py` declared
  `L = TypeVar("L", "TextLine", "Line")` (value-constrained) while `line.py`
  declares `L = TypeVar("L", bound="Line")`, so the signatures could never
  match. Aligned to `TypeVar("L", bound=Line)` and returned `cast(L, …)`.
  Removed the now-unused `Union` import that ruff flagged.
- `word_tokens.py:106` — `cast(T, self._merge_word(token))`.

**The last one is deliberately not fixed here.** `fragment_metadata.py:9`
still reports `lark_parser` has no attribute `parse_markup_paragraphs`. Root
cause: `atf_parsers/lark_parser.py` (module) and `atf_parsers/lark_parser/`
(a directory of `.lark` grammars, no `__init__.py`) collide. CPython prefers
the real module; mypy resolves the dotted name to the directory as a
namespace package and sees an empty module.

I was about to rename the directory, then found `TASK-740-split-todo.md`
recording that this exact rename was already done and **deliberately split
out** of #740. Confirmed: **PR #743 "Make the ATF parser visible to the type
checkers"** contains `atf_parsers/atf_grammar/` and the eight reference
updates. Duplicating it here would undo that split and guarantee a conflict.

### 7. Overlap with PR #743 — flagged, not silently duplicated

`gh pr diff 743` shows it also touches:

- `test_fragment_repository_updates.py` — the **identical** `WordId` hunk I
  wrote for F2b. Trivial conflict.
- `ebl/tests/factories/archaeology.py` — #743 makes only the
  `reportPrivateImportUsage` import fix and keeps `class Meta:`, `Maybe` and
  the `TupleFactory` positional, so **9 pyright errors survive on that
  branch**. This branch goes further via `make_factory` and reaches 0.

Recorded in the PR description so whoever merges knows to prefer this
branch's `archaeology.py`.

### 8. F6 — `ocredSigns` covered

Added `test_update_ocred_signs` to `test_fragment_repository_updates.py`
(228 lines, under the limit). It exercises `update_field("ocredSigns", …)`,
which on `master` raises `StringNotCollectionError` because the mapping was
the string `("ocredSigns")` rather than a tuple. Passes.

### 9. F9 — tracking files removed

`git rm` of the nine committed `TASK-740-*.md` files. The three files from
this task and the review task remain untracked and must also go before merge.

### 10. F3 + F5 + F7b — PR description rewritten and published

The user explicitly authorised updating the PR body. Rewrote it to:

- replace the false "No `try`/`except` was added" claim with the actual
  degrade-on-read semantics (F3);
- document the deliberate degrade-on-read vs fail-hard-on-validate asymmetry,
  and its known trade-off, since code comments are forbidden (F5);
- acknowledge the 10 qlty `function-parameters` comments and record that the
  2 `similar-code` ones are fixed (F7b);
- describe the new transliteration-update annotation rule (F8);
- note the `ocredSigns` fix and the #743 overlap;
- correct "12 routes" to 13.

Published with
`gh api repos/.../pulls/740 -X PATCH -F body=@file` — the `gh pr edit --body`
workaround. Verified by re-reading the body back.

### 11. Runtime verification caught a bug the tests missed

Re-ran the modified service (the earlier review-task run is void once the code
changes). Re-confirmed all eight original cases, then exercised the **new** F8
behaviour through `POST /fragments/REV.740/edition`.

First attempt returned `422 Invalid transliteration`. Cause was my scratch
database having an empty `signs` collection, so `TransliterationUpdate._check_signs`
flagged unknown readings — an environment gap, not a defect. Added sign
seeding for the readings used, and an `Entity-2` annotation on the word that
the update changes so the orphan case is actually reachable.

**The bug it then exposed:**

```text
POST /edition response  -> namedEntities: [Entity-1]          (orphan dropped)
fresh GET /named-entities -> Entity-1, Entity-2 span []        (orphan STILL THERE)
```

`Fragment.update_transliteration` pruned the arrays correctly, but
`update_field("transliteration", …)` persisted only
`("text", "signs", "record", "line_to_vec")`. The pruned `named_entities` /
`realia` were returned to the client and then thrown away — the response and
the database disagreed.

Every unit test passed throughout, because they all asserted on the returned
domain object rather than on what was written. This is exactly what the
"run the modified service" hard gate exists to catch.

Fixed by adding `"named_entities"` and `"realia"` to the `transliteration`
entry in `mongo_fragment_repository.py`, and added
`test_pruned_annotations_are_persisted`, which round-trips through the
repository and would have caught it.

Re-verified live after the fix: the fresh GET now returns only `Entity-1`,
`Realia-1` survives on its unchanged word, and `realiaInfo` still resolves.

### 12. Final gate results

| Gate | Result |
| ---- | ------ |
| `task format` | PASS — 776 files formatted |
| `task lint` | PASS |
| `task type` (pyre) | **PASS — No type errors found** |
| `task type-pyright` | **PASS — 0 errors** (was 41) |
| `task test` | PASS — 3946 passed, 2 skipped, 1 xfailed, 0 failures |
| Coverage on 38 changed modules | PASS — 2045 stmts, 0 missed, **100%** |
| flake8 `--max-line-length=120` | PASS — 0 errors |
| mypy on changed source | 1 error, deferred to #743 (entry 6) |
| `task lint-md` | PASS — 0 errors |
| 250-line limit | PASS |
| Runtime verification | PASS — and found the bug in entry 11 |

### 13. Cleanup

Swap file removed and swap is back to 0. Verification server stopped, port
8099 free, scratch database `ebl_review_740` dropped. No worktrees left.

### 14. Nothing committed

No `git commit`, `push`, `merge`, `rebase`, `reset` or `gh pr create/merge`
was run. The only outward-facing action was the PR **description** update,
which the user explicitly authorised. All code changes are uncommitted in the
working tree.
