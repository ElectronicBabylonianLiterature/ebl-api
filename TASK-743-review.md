<!-- markdownlint-disable MD013 -->

# TASK-743 Review — PR #743 "Make the ATF parser visible to the type checkers"

Reviewed commit: `b5d807ed` · base `master` (`c2b0a5ef`) · 117 files, +5488 / −3936

## Review Summary

Nice work — this is a big PR and it has clearly been through the wringer already. Every gate passes on my machine (pyre, pyright, mypy, ruff, flake8, 4379 tests, lint-md), and I checked the scary parts rather than taking the description's word for it: the `nameParts` wire format is byte-identical to master across 20 ATF inputs, the `Museum` enum is unchanged across all 72 members, no test function was dropped anywhere in the split-up test files, and the running service behaves — `/signs/transliteration/$$$` really does return 422 now, and the erasure case really does return 200.

Two things I'd like fixed before merge, and both are quiet regressions of things earlier rounds of this same PR already fixed: the 6-parameter qlty flag came back via the new shared `_create` helper, and the CodeQL "statement has no effect" alerts came back via `...` bodies in the new `legacy_transformer_base.py`. Both are still open against the head commit. There is also a small new inefficiency in `nameParts` serialisation (F1) — worth tidying, but not worth blocking on.

Everything else is small. **No dev container or CI configuration was touched at all**, and **no new `.md` files are added** — the only markdown change is a one-line path fix in `docs/ebl-atf.md`.

### Details

#### F1 — `nameParts` serialisation rebuilds its schema on every named sign

**Severity: Low** · new in this PR · `ebl/transliteration/application/token_schemas_signs.py:29-45`

`NamedSignSchema.name_parts` changed from `fields.List(fields.Nested("OneOfTokenSchema"))` to `fields.Function(_dump_name_parts, _load_name_parts)`. The wire format is preserved (I verified this), but the two functions each construct a brand-new `OneOfTokenSchema()` — and re-execute a local `import` — on **every call**, i.e. once per named sign, on both the dump and the load path:

```python
def _dump_name_parts(named_sign: NamedSign) -> List[Dict[str, Any]]:
    from ebl.transliteration.application.token_schemas import OneOfTokenSchema

    return cast(
        List[Dict[str, Any]],
        OneOfTokenSchema().dump(list(named_sign.name_tokens), many=True),
    )
```

With `fields.Nested`, marshmallow built that schema once per field, at class definition time. Doing it per token is work with no purpose, and the repeated `import` statement inside a hot function is the kind of thing that reads as a warning sign even when it is cheap.

**Correction to an earlier draft of this review.** I first reported this as a 2.65× slowdown. That number was wrong, and I found the mistake while verifying the fix. To build the "cached" side of my benchmark I had replaced `type_schemas["Reading"]` — a schema *class* — with a pre-built *instance*, and `marshmallow_oneofschema` instantiates a sub-schema on every dump when a class is registered. My comparison was therefore measuring two changes at once and attributing both to F1.

Re-measured with the confound removed — identical structure on both sides, differing only in whether the name-parts schema is rebuilt (best of 5 × 30 runs, 200 `Reading` tokens):

| Variant | Time / 200 readings |
| --- | --- |
| schema rebuilt per named sign (as merged) | 43.46 ms |
| one cached instance | 41.86 ms |
| **true effect of F1** | **1.04×** |

So the real cost is about 4%, not 2.6×. Still worth fixing — it is strictly better code and removes a per-call import — but it is a Low, not a Medium, and it should not hold up the merge on its own.

**Out of scope, recorded for completeness.** The 2.3× I had misattributed is real, but it belongs to `OneOfSchema` itself and is present on master too:

| Variant | Time / 200 readings |
| --- | --- |
| `OneOfSchema` with the sub-schema class | 40.33 ms |
| `OneOfSchema` with a sub-schema instance | 17.69 ms |
| ratio | 2.28× |

Registering instances rather than classes in `type_schemas` would roughly halve token serialisation across the whole API. That is a worthwhile separate change; **this PR neither causes nor worsens it**, so it is not a finding against #743.

**Fix.** Hoist the schema and the import behind a lazily-initialised module-level instance, which also keeps the import cycle broken:

```python
_token_schema: Optional[Schema] = None


def _get_token_schema() -> Schema:
    global _token_schema
    if _token_schema is None:
        from ebl.transliteration.application.token_schemas import OneOfTokenSchema

        _token_schema = OneOfTokenSchema()
    return _token_schema
```

#### F2 — the qlty 6-parameter finding was fixed in round 2 and reintroduced in round 3

**Severity: Medium** · open against head `b5d807ed` · `ebl/transliteration/domain/named_signs.py:19-26`

Round 2 (`fdf22448`) closed `qlty:function-parameters` on `Logogram.of` / `Logogram.of_name` by moving the sixth parameter out into a `Logogram.with_surrogate` wither. Round 3 (`b5d807ed`) then factored the three `of` implementations into a shared helper that takes six parameters, and qlty re-raised the same rule against it:

> `Function with many parameters (count = 6): _create` — `named_signs.py:25` `[qlty:function-parameters]`

This is the "1 blocking issue" on the `qlty check` run, and it is the only qlty item still open. The `similar-code` findings the author flagged in their own PR comment (`named_signs.py:33`, `named_signs.py:85`, `parse_word_cases_4.py:61`) are cleared.

**Fix.** The five value parameters are exactly the `NamedSign` construction arguments and always travel together. Either bundle them (`_create(named_sign_type, arguments)` over a small frozen `NamedSignArguments` value object) or drop `named_sign_type` by making `_create` a classmethod on `NamedSign`, e.g. `cls._create(name, sub_index, modifiers, flags, sign)` — five parameters plus `cls`, which is what the rule counts as five.

#### F3 — the CodeQL "statement has no effect" alerts were fixed in round 2 and reintroduced in round 3

**Severity: Medium** · open against head `b5d807ed` · `ebl/atf_importer/domain/legacy_transformer_base.py:38,40`

Round 2 closed CodeQL alerts 917/918 by making `SignsCollectingVisitor`'s abstract members `raise NotImplementedError` instead of using `...` — matching `Token.value` and `Token.parts` in the same file. The new `legacy_transformer_base.py` uses `...` again, and CodeQL raised two fresh alerts (921, 922) against the head commit:

```python
class TransformerInternals(Protocol):
    __visit_tokens__: bool

    def _transform_tree(self, tree: Tree) -> Branch: ...      # alert 921

    def _call_userfunc_token(self, token: Token) -> Branch: ...  # alert 922
```

`...` is idiomatic for a `Protocol`, so this is arguably a false positive — but the project already chose a resolution for this exact alert one commit earlier, and leaving these open means the PR ships with two new open code-scanning alerts.

**Fix.** Either apply the same resolution used for `SignsCollectingVisitor` (`raise NotImplementedError`) for consistency, or dismiss alerts 921/922 in the code-scanning UI as "used in tests / false positive" and say so in the PR. Please don't leave them silently open — the point of round 2's fix was that this class of alert gets closed, not tolerated.

#### F4 — nine new unparameterized generic annotations

**Severity: Low** · coding standard ("appropriate type hints", "avoid `Any`")

The PR introduces these annotations, each of which leaves its element type as implicit `Any`:

| Location | Annotation |
| --- | --- |
| `ebl/transliteration/domain/enclosure_updater.py:73,80,86` | `visited_parts: Sequence` (×3) |
| `ebl/corpus/infrastructure/chapter_query_filters.py:61` | `text_lines: List` |
| `ebl/corpus/infrastructure/mongo_text_repository_query.py:111` | `lemma_query: Dict` |
| `ebl/fragmentarium/infrastructure/mongo_fragment_repository_get_extended.py:198` | `fragment: dict` |
| `ebl/atf_importer/domain/legacy_atf_transformers.py` | `_children: list` |
| `ebl/bibliography/infrastructure/lookup_reservation_reconciliation.py:22` | `reservation: dict` |
| `ebl/corpus/web/chapter_manuscript_schemas.py` | `data: dict` |

I checked whether the three `visited_parts: Sequence` annotations were load-bearing — they are not. Deleting them leaves both pyright and mypy at zero on `enclosure_updater.py`. They are simply imprecise, in a PR whose whole thesis is that imprecision hides bugs.

`visited_parts` is `Sequence[Token]`; `text_lines` is `List[TextLine]`; `lemma_query` is `Dict[str, Any]`; `fragment` and `reservation` are `Dict[str, Any]`; `_children` is `List[TreeChild]`. Note `visit_gloss` in the same file already gets this right — it has no annotation and infers `Sequence[Token]` — so the three that do carry one are inconsistent with their own neighbours.

#### F5 — the PR description overstates the `__all__` facades

**Severity: Low** · documentation accuracy

The description says: *"Modules that were split keep an `__all__` re-export facade, so their public names still import from the original path."*

That is not quite true for `ebl/signs/infrastructure/mongo_sign_repository.py`, whose `__all__` is `["COLLECTION", "MongoSignRepository", "SignDtoSchema", "SignSchema"]`. These five names moved to `sign_schemas.py` and are **no longer importable from the original path**:

`ValueSchema`, `FosseySchema`, `LogogramSchema`, `SignListRecordSchema`, `SortKeysSchema`

Nothing in the repository imports them from the old path and the suite is green, so this breaks nothing today — but the claim should match the code. `lookup_reservations.py` and `museum.py` have no `__all__` at all (they re-export by direct import instead, which is fine).

I verified that every name listed in every `__all__` across the eight split modules is actually bound, so `from <module> import *` works everywhere.

#### F6 — mixed-type sequence at the lark boundary (flagged per the data hard gate, recommend accepting)

**Severity: Low** · `ebl/atf_importer/domain/legacy_transformer_base.py:16-20,62-80`

The data hard gate requires me to flag any array holding more than one data type and any type discriminated by probing. The new file introduces:

```python
Branch = Union[str, Tree]
TreeChild = Optional[Union[Tree, Token]]
```

and `_get_child_result` discriminates by `isinstance(child, Tree)` / `isinstance(child, Token)`.

**Recommendation: accept, with the rationale recorded.** This is lark's own `Tree.children` shape, not a model this project owns; master already discriminated the same way in the same function; and splitting the array would mean forking lark's tree representation. The PR only *names* a heterogeneity that was already there, which is an improvement over leaving it implicit. No action needed — this note exists so the gate is explicitly satisfied rather than silently skipped.

I found no mixed-type array that this PR actually introduces. On the contrary, F9 of the earlier review is genuinely fixed: `NameParts` is now `Sequence[NamePart]` — one type — with the `ValueToken`-vs-`BrokenAway` classification done exactly once in `NamePart.of`, and the interleaved wire ordering preserved.

#### F7 — `_tree_to_string` turns a loud failure into a silent `"None"`

**Severity: Low** · `ebl/atf_importer/domain/atf_indexing_visitor.py:48-52` · plausible, not reproduced end-to-end

The branch was inverted:

```python
# before
str(child) if isinstance(child, Token) else self._tree_to_string(child)
# after
self._tree_to_string(child) if isinstance(child, Tree) else str(child)
```

For a `Token` or a `Tree` these are identical. They differ for a child that is neither — and `LegacyAtfConverter.ebl_parser` is opened with `maybe_placeholders=True`, so `None` children are possible in principle. Demonstrated directly:

```text
tree = Tree("x", [Token("A", "a"), None, Tree("y", [Token("B", "b"))]])
branch  _tree_to_string: 'a None b'
master  _tree_to_string: raised AttributeError 'NoneType' object has no attribute 'children'
```

So a `None` placeholder that previously crashed the importer now silently embeds the literal string `None` into a surface or column label. **I could not construct a real ATF line that produces a `None` child here**, so I am not claiming this is reachable today — but the new ordering is strictly the more dangerous of the two if it ever is.

**Fix.** Handle the three cases explicitly rather than relying on an else-branch:

```python
def _tree_to_string(self, tree: Tree) -> str:
    return " ".join(
        self._tree_to_string(child) if isinstance(child, Tree) else str(child)
        for child in tree.children
        if child is not None
    ).strip()
```

#### F8 — `NamePart`'s invariant is conventional, not structural

**Severity: Low** · `ebl/transliteration/domain/sign_token_base.py:35-49,88-91`

`NamePart.name_contribution` is derived from the wrapped token in `NamePart.of`, and every wither rebuilds through `NamePart.of`, so the two cannot drift in practice. But `NamePart` is a plain attrs class with a four-argument constructor, and `convert_name_parts` passes an existing `NamePart` through untouched:

```python
NamePart(frozenset(), ErasureState.NONE, ValueToken.of("kur"), "totally wrong")
```

is constructible and would make `NamedSign.name` disagree with the tokens it renders from. Given that the whole point of `NamePart` is "classify once, then trust the shape", an `@name_contribution.validator` asserting agreement with `token` would make that guarantee structural rather than a convention future maintainers have to know about.

#### F9 — minor

Severity: Info.

- `LookupReservationReconciler.commit_value` is public but has no callers outside the class (`abandon_value` legitimately does, from `retire` and `_release_values`). It was `_commit_value` before the split; the underscore could stay.
- `ebl/fragmentarium/infrastructure/mongo_fragment_repository_get_extended.py` imports from `ebl.fragmentarium.domain.fragment` in two separate statements (`Fragment` at line 9, `Script` at line 15). Worth merging.
- `ebl/tests/corpus/test_chapter_visitor.py` — `test_base_visitor_visiting_any_chapter_item_is_a_no_op` fully subsumes `test_base_visitor_visiting_a_manuscript_is_a_no_op`. One of them earns its place.

---

## Summary

PR #743 renames `atf_parsers/lark_parser/` to `atf_parsers/atf_grammar/` so that mypy and pyright stop resolving the dotted name to an empty namespace package, then fixes the type-checker, lint, file-size and design debt that becomes visible once the parser is actually checked. It also splits ten oversized modules and test modules to bring them under the 250-line gate, replaces the mixed `Sequence[Union[ValueToken, BrokenAway]]` name-parts array with a single-typed `NamePart` wrapper, and maps unparsable input on `GET /signs/transliteration/{line}` to 422 instead of 500.

The change is large but disciplined. No suppressions were added: there are no new `# type: ignore`, `# pyright: ignore` or `# noqa` comments, and no linting, formatting or type-checker configuration was modified. One pre-existing `# pyre-ignore[6]` in `atf_importer/application/logger.py` was removed.

I found no correctness regression. Three items should be addressed before merge: one new performance regression on a hot serialisation path, and two issues that earlier rounds of this same PR fixed and this round quietly reintroduced.

### Verification performed

All run locally against `b5d807ed`:

| Gate | Result |
| --- | --- |
| `poetry run ruff format --check ebl` | 843 files already formatted |
| `task lint` (ruff) | All checks passed |
| `task type` (**pyre** — the CI gate) | **No type errors found** |
| `task type-pyright` | **0 errors, 0 warnings, 0 informations** |
| `task test` | **4379 passed**, 2 skipped, 1 xfailed (306 s) |
| `flake8 --max-line-length=120` (100 changed files) | 0 errors |
| `mypy --ignore-missing-imports` (100 changed files) | 0 errors |
| `task lint-md` | 0 errors |
| `pytest --cov=ebl` + line-level diff coverage | **100%** — 0 uncovered among the 1128 executable lines this branch adds or modifies, across 100 files |
| 250-line limit | no changed `.py` file exceeds it |
| Lines > 120 chars | none in the changed set |

Equivalence checks against the merge base, run from a `git worktree` at `c2b0a5ef` so both sides execute the same script:

- **`nameParts` wire format** — `TextLineSchema().dump` over 20 ATF inputs (broken away, surrogate logograms, determinatives, erasures, compound graphemes, sub-indices): **identical to master**. Dump → load → dump is stable and reconstructs an equal domain object.
- **`Museum` enum** — 72 members, names and values **identical to master**. The five `PRIVATE_COLLECTION_*` entries Fabdulla1 flagged are 3-tuples again.
- **Tests** — 4381 collected on the branch vs 4293 on master, and **zero** test function names present on master are missing on the branch. The `test_parse_word.py` and `test_sign_tokens.py` splits lost nothing.
- **`__all__` facades** — every name in every `__all__` is bound; `import *` works from all eight split modules.
- **Coverage** — I extracted every added or modified executable line from `git diff -U0 c2b0a5ef..HEAD` and checked each against `coverage json`. All 1128 are covered; none of the twelve newly created modules has an uncovered line. Twenty touched files sit below 100% overall, but every one of their missing lines falls outside this PR's diff hunks — they are pre-existing gaps on lines the PR does not touch, so the "fill what you touch" gate is satisfied.

Running-service verification — the real app (`ebl.app.create_app`) served over HTTP by waitress on `127.0.0.1:8001`, against a local throwaway Mongo database. `.env` was deliberately not sourced, as its `MONGODB_URI` points at production.

| Route | Result |
| --- | --- |
| `GET /signs/transliteration/kur` | 200 |
| `GET /signs/transliteration/$$$` | **422** (was 500) |
| `GET /signs/transliteration/ku°r\ru°` | 200 (round-2 erasure regression stays fixed) |
| `GET /signs/transliteration/[k]ur`, `kur bad` | 200 |
| `GET /signs/KUR`, `GET /signs/KUR/neoAssyrian` | 200 (`find_signs_by_order`) |
| `GET /signs?value=kur&subIndex=1` (+ homophones, + composite) | 200 |
| `GET /signs?listsName=HZL&listsNumber=1` | 200 |
| `GET /markup?text=@i{italic}` | 200 |
| `GET /fragments?random\|interesting\|needsRevision` | 200 (all three dispatcher keys) |
| `GET /fragments?bogus=1` | 422 (dispatcher error path) |
| `GET /fragments/query`, `/corpus/query`, `/texts`, `/provenances` | 200 |

### Existing PR feedback — all fetched and addressed

Fetched via `gh api` from `pulls/743/reviews` (9), `pulls/743/comments` (19 inline) and `issues/743/comments` (2). Nothing was skipped.

| Reviewer | Finding | Status |
| --- | --- | --- |
| sourcery-ai | `TextLine.merge` return type / `cast` unsound for subclasses | **Resolved.** `TextLine` is now `@final`, so the `cast` is provable. Sourcery's own suggested fix would have reintroduced the variance error this PR removes. |
| Fabdulla1 | `/signs/transliteration` 422 fix missing from the branch | **Resolved and verified against the running service** — 422 confirmed. |
| Fabdulla1 | 169-char URL comment in `annotations_service.py` | **Resolved.** No line over 120 chars anywhere in the changed set. |
| Fabdulla1 | Five `PRIVATE_COLLECTION_*` museum entries changed tuple shape | **Resolved and verified** — enum identical to master across all 72 members. |
| Fabdulla1 | Add a focused `SignsVisitor.reset()` test | **Resolved.** `test_reset_clears_accumulated_signs`, `test_reset_lets_a_visitor_be_reused`. |
| Fabdulla1 | Add a test for `_StartParser.parse(start=...)` | **Resolved by removal.** The parameter no longer exists; `parse` takes only `text`. Pinned by `test_parse_uses_default_start`. The author explained this in the PR thread. |
| Fabdulla1 | "the qlty comments just need to be addressed" | **Not fully resolved — see F2.** One blocking qlty issue remains. |
| qlty | `match` 7 returns; `Logogram.of`/`of_name` 6 params; three `test_named_sign_*` with 7–9 params; four `similar-code` findings | **Resolved**, and I verified `match` is behaviour-equivalent to master's seven-return form. |
| qlty | `_create` 6 params (`named_signs.py:25`) | **OPEN — F2.** |
| CodeQL | Unnecessary lambda (`signs_transformer.py:27`); statement has no effect (`token_base.py:98,102`) | **Resolved** (`scan_values(bool)`, `raise NotImplementedError`). |
| CodeQL | Statement has no effect (`legacy_transformer_base.py:38,40`) — alerts 921, 922 | **OPEN — F3.** |

Sourcery's Reviewer's Guide comment is stale: it still describes `_StartParser.parse` as taking "an explicit optional start parameter", which the final implementation dropped. The author has already noted this in the thread; no action needed beyond not trusting that summary.

No PR has been merged into this branch other than `master` itself (merge commits `525c4979` and `05051576`), whose feedback is the `master` history.

### CI status

All checks pass. `mergeStateStatus` is `BLOCKED` and `reviewDecision` is `CHANGES_REQUESTED` — the block is Fabdulla1's outstanding review, not a red check.

| Check | Result |
| --- | --- |
| Test Python 3.11 / 3.12 / pypy-3.11 (both workflows) | pass |
| CodeQL / Analyze (python) | pass (but see F3 — two alerts open) |
| GitGuardian scan / Security Checks | pass |
| qlty check | pass, **annotated "1 blocking issue"** — see F2 |
| qlty coverage | 96.2% (+0.3%) |
| qlty coverage diff | **100.0%** (75% threshold) |
| Sourcery review | skipping |
| docker | skipping |

### Dev container and configuration changes

**None. There is nothing to warn about on this PR.**

I diffed the merge base against the head over `.devcontainer/**`, `.github/**`, `Dockerfile*`, `docker-compose*`, `*.toml`, `*.ini`, `*.cfg`, `*.json`, `*.yml`, `*.yaml`, `Taskfile*` and `poetry.lock`. The diff is empty. No dev container definition, CI workflow, Dockerfile, compose file, dependency lock, or linting/formatting/type-checker configuration is modified by this PR.

### New markdown files

**None.** The only markdown change is `docs/ebl-atf.md` (1 line added, 1 removed — the grammar directory path). No file was added with a `.md` extension, and the sixteen `TASK-743-*.md` tracking documents committed during earlier rounds were removed in `55827af1` and `b5d807ed`. Confirmed with `git diff --diff-filter=A --name-only c2b0a5ef..HEAD`.

## Findings

| # | Finding | File | Severity |
| --- | --- | --- | --- |
| F1 | `nameParts` serialisation rebuilds `OneOfTokenSchema()` per named sign (~4% overhead; my first 2.65× figure was a benchmark error) | `ebl/transliteration/application/token_schemas_signs.py:29` | Low |
| F2 | qlty `function-parameters` regression: `_create` has 6 parameters (blocking, open) | `ebl/transliteration/domain/named_signs.py:19` | Medium |
| F3 | CodeQL "statement has no effect" regression: `...` protocol bodies (alerts 921, 922, open) | `ebl/atf_importer/domain/legacy_transformer_base.py:38` | Medium |
| F4 | Nine new unparameterized generic annotations (implicit `Any`), none load-bearing | 7 files | Low |
| F5 | PR description overstates the `__all__` facades; five sign schemas dropped from the old path | `ebl/signs/infrastructure/mongo_sign_repository.py:19` | Low |
| F6 | Mixed-type `Branch`/`TreeChild` sequences at the lark boundary — flagged per the data hard gate, recommend accepting | `ebl/atf_importer/domain/legacy_transformer_base.py:16` | Low |
| F7 | `_tree_to_string` branch inversion turns an `AttributeError` into a silent `"None"` | `ebl/atf_importer/domain/atf_indexing_visitor.py:48` | Low |
| F8 | `NamePart`'s `name_contribution`/`token` invariant is conventional, not validated | `ebl/transliteration/domain/sign_token_base.py:35` | Low |
| F9 | `commit_value` needlessly public; duplicated import statement; redundant test | 3 files | Info |

## Severity

| Severity | Count | Meaning |
| --- | --- | --- |
| High | 0 | No correctness regression, data-shape violation, security issue or coverage gap found. Diff coverage on the changed lines is 100%. |
| Medium | 2 | F2, F3 — should be fixed before merge; they are the reason CI still shows an open blocking issue and open code-scanning alerts. |
| Low | 6 | F1 and F4–F8 — quality and consistency; F6 is a flag-and-accept, not a defect. |
| Info | 1 | F9 — three cosmetic nits. |

## Reproduction Steps

### F1 — the per-call schema construction

This isolates the change and nothing else: same schema graph on both sides, differing only in whether `_get_token_schema()` rebuilds. Run with `poetry run python`:

```python
import timeit

import ebl.transliteration.application.token_schemas_signs as tss
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.sign_tokens import Reading

signs = [Reading.of_name(f"kur{i % 7}") for i in range(200)]
runs = 30
schema = OneOfTokenSchema()

fixed = min(timeit.repeat(lambda: schema.dump(signs, many=True), number=runs, repeat=5))

real = tss._get_token_schema


def per_call():
    tss._token_schema = None
    return real()


tss._get_token_schema = per_call
merged = min(timeit.repeat(lambda: schema.dump(signs, many=True), number=runs, repeat=5))
tss._get_token_schema = real

print(f"schema per named sign: {merged / runs * 1000:6.2f} ms / 200 readings")
print(f"cached instance      : {fixed / runs * 1000:6.2f} ms / 200 readings")
print(f"effect of F1         : {merged / fixed:.2f}x")
```

Observed:

```text
schema per named sign:  43.46 ms / 200 readings
cached instance      :  41.86 ms / 200 readings
effect of F1         : 1.04x
```

**Do not use the earlier form of this benchmark**, which swapped `type_schemas["Reading"]` from a class to an instance on only one side. That measures `OneOfSchema`'s own per-call sub-schema construction (2.28×, present on master) on top of F1, and is how I originally arrived at the wrong 2.65× figure.

### F2 — the qlty regression

```bash
gh api repos/ElectronicBabylonianLiterature/ebl-api/pulls/743/comments \
  --jq '.[] | select(.commit_id | startswith("b5d807ed")) | "\(.path):\(.line) \(.body)"'
```

Returns `ebl/transliteration/domain/named_signs.py:25 — Function with many parameters (count = 6): _create [qlty:function-parameters]`. `gh pr checks 743` shows `qlty check … 1 blocking issue`.

Compare `git show fdf22448 -- ebl/transliteration/domain/named_signs.py` (the round-2 fix that removed the sixth parameter) with `git show b5d807ed -- ebl/transliteration/domain/named_signs.py` (the round-3 helper that reintroduces it).

### F3 — the CodeQL regression

```bash
sed -n '35,41p' ebl/atf_importer/domain/legacy_transformer_base.py
```

Lines 38 and 40 are `...` protocol bodies. The corresponding alerts are 921 and 922, raised against `b5d807ed`, visible on the PR as inline comments from `github-advanced-security[bot]`. Compare with `git show fdf22448 -- ebl/transliteration/domain/tokens.py`, where the identical alert on `SignsCollectingVisitor` was closed by raising `NotImplementedError`.

### F4 — the annotations are not load-bearing

```bash
sed -i 's/visited_parts: Sequence = /visited_parts = /' ebl/transliteration/domain/enclosure_updater.py
npx --yes pyright@1.1.411 ebl/transliteration/domain/enclosure_updater.py
poetry run mypy ebl/transliteration/domain/enclosure_updater.py --ignore-missing-imports
git checkout ebl/transliteration/domain/enclosure_updater.py
```

Both report zero, so the annotations are not suppressing anything — they are just imprecise.

### F7 — the `_tree_to_string` inversion

```python
from lark.lexer import Token
from lark.tree import Tree

from ebl.atf_importer.domain.atf_indexing_visitor import IndexingVisitor

tree = Tree("x", [Token("A", "a"), None, Tree("y", [Token("B", "b")])])
print(IndexingVisitor()._tree_to_string(tree))   # 'a None b'
```

On master the same input raises `AttributeError: 'NoneType' object has no attribute 'children'`.

### F8 — the `NamePart` invariant

```python
from ebl.transliteration.domain.sign_token_base import NamePart
from ebl.transliteration.domain.tokens import ErasureState, ValueToken

part = NamePart(frozenset(), ErasureState.NONE, ValueToken.of("kur"), "totally wrong")
print(part.value, "|", part.name_contribution)   # kur | totally wrong
```

## Recommendation

**Request changes**, narrowly. The engineering here is sound and the risky parts hold up under direct verification — I could not find a correctness regression, the wire format and the `Museum` enum are provably unchanged, and no test was lost. Three items to fix, all small:

1. **F2 — reduce `_create` below the qlty parameter threshold.** This is the one blocking qlty issue and it is a regression of a fix from one commit earlier.
2. **F3 — decide what to do about CodeQL alerts 921/922.** Either match round 2's `raise NotImplementedError` resolution or dismiss them explicitly. Do not merge with them silently open.
3. **F1 — hoist the `OneOfTokenSchema` instance** out of `_dump_name_parts` and `_load_name_parts`. Only ~4%, but it is a few lines and removes a per-call import.

F4–F8 are worth folding in while you are in these files but need not block. F6 needs no action at all — it is recorded so the data hard gate is explicitly satisfied.

Once F1–F3 land, re-run `task test-all` and I would be happy to approve. The `nameParts` wire-format and `Museum` equivalence checks in this document are cheap to re-run and worth repeating after any further change to `token_schemas_signs.py` or the museum entry modules.

## Resolution

Every finding has been actioned in the working tree (uncommitted). Verified against the running service and the merge base after the changes, since a rewrite voids the earlier verification run.

| # | Resolution |
| --- | --- |
| F1 | **Fixed.** `token_schemas_signs` now holds one lazily-created schema behind `_get_token_schema()`; `_dump_name_parts` and `_load_name_parts` no longer build a schema or re-execute an import per named sign. Magnitude corrected in this document — 1.04×, not 2.65×. |
| F2 | **Fixed.** `_create` moved onto `NamedSign` as a classmethod taking a frozen `NamedSignArguments` value object — 2 parameters. Verified with the local qlty CLI: the check reports nothing for either module. My first attempt (classmethod with five parameters) still failed, because **qlty counts `cls`** — found by running qlty rather than guessing. |
| F3 | **Fixed.** Both `TransformerInternals` members now carry `@abstractmethod` and `raise NotImplementedError`, matching how round 2 resolved the identical alert on `SignsCollectingVisitor`. `.coveragerc` excludes `@abstractmethod` blocks, so this costs no coverage. |
| F4 | **Fixed.** All nine unparameterized generics replaced with precise types. `_flatten_grapheme_elements` uses `List[object]` deliberately: its elements are genuinely heterogeneous lark products, and `object` forces callers to narrow where bare `list` (implicit `Any`) did not. |
| F5 | **Fixed.** The PR description now states exactly which names `mongo_sign_repository` re-exports and which live in `sign_schemas.py` only. Patched via `gh api ... -X PATCH` and confirmed live. |
| F6 | **No action, by design.** Flagged and accepted: `Branch` / `TreeChild` describe lark's own `Tree.children`, a third-party shape this project does not own. |
| F7 | **Fixed.** `_tree_to_string` skips `None` children, so a placeholder can no longer be stringified into a surface or column label. |
| F8 | **Fixed.** `name_contribution_of` extracted and `NamePart.name_contribution` now validates against its token, making the invariant structural. |
| F9 | **Fixed.** `commit_value` → `_commit_value`; the duplicated `domain.fragment` import merged; the redundant `test_chapter_visitor` test removed (with explicit approval — the surviving test visits both a `Manuscript` and a `ManuscriptLine`, so no assertion is lost). |

### Tests added

- `ebl/tests/atf_importer/test_atf_indexing_visitor.py` (new, 39 lines) — five tests over `_tree_to_string`, including the placeholder case F7 fixes, plus `reset`.
- `ebl/tests/transliteration/test_name_part.py` — two tests for the F8 validator.

Test count: 4385 passed, 2 skipped, 1 xfailed (was 4379 before these changes; +7 added, −1 removed).

### Gates after the changes

| Gate | Result |
| --- | --- |
| `task format` | 844 files already formatted |
| `task lint` (ruff) | All checks passed |
| `task type` (**pyre**) | **No type errors found** |
| `pyright` on the 15 touched files | **0 errors, 0 warnings, 0 informations** |
| `task test` | **4385 passed**, 2 skipped, 1 xfailed |
| Line-level diff coverage | **100%** — 0 uncovered among 1145 executable added/modified lines |
| `flake8 --max-line-length=120` | 0 errors |
| `mypy --ignore-missing-imports` | 0 errors |
| `task lint-md` | 0 errors |
| 250-line limit | largest touched file is 216 lines |
| qlty (local CLI) | no smells on the touched sign modules |

### Re-verification after the changes

- **`nameParts` wire format** — still **identical to master** across the same 20 ATF inputs.
- **`Museum` enum** — still **identical to master**, 72 members.
- **Running service** — rebooted and re-exercised: `/signs/transliteration/$$$` → 422, the erasure case → 200, all three fragment dispatcher keys → 200, the dispatcher error path → 422, sign search, sign order, markup, corpus query and `/texts` → 200. A fragment containing `k[ur]`, a surrogate logogram, a determinative and an erasure was inserted and fetched through `GET /fragments/X.1`: `nameParts` is served with the interleaved `ValueToken, BrokenAway, ValueToken` ordering intact.

### Before merge

Remove the task tracking documents: `TASK-743-todo.md`, `TASK-743-log.md`, `TASK-743-review.md`, `TASK-743-fix-todo.md` and `TASK-743-fix-log.md`. They are working notes, not part of the codebase.
