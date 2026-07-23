# TASK-740 Review — PR #740

Realia annotation API: resolve `realiaInfo` on every fragment-returning
route (`add-realia-annotation-api` to `master`, head `d99cd834`).

## Summary

The PR adds a `realia` annotation type alongside named entities and
resolves `realiaInfo` on every fragment-returning route. The core design
is sound and honours the project's hardest structural rule: named
entities and realia are kept in **structurally separate arrays** at every
level — `Word.named_entities` / `Word.realia`,
`Fragment.named_entities` / `Fragment.realia`, and the wire keys
`namedEntities` / `realia`. No discriminator, no mixed id list, no
`OneOfSchema` to tell the two apart. Uniqueness over the **shared id
space** is enforced across the union of both arrays, which is the correct
reading of the rule. I verified all of this against the running service,
not just the tests.

Wiring is complete: every `create_response_dto` call site now goes
through `FragmentDtoFactory`, so `realiaInfo` appears on all 15
fragment-returning routes. The 250-line limit is met on every changed
file. pyre, pyright, ruff, ruff-format and markdownlint are clean, and
the full suite passes locally.

Two issues block merge:

1. **CI is red.** One test fails deterministically on `Test Python 3.12`
   in both workflow runs. The cause is a latent test-isolation defect in
   the *factories*, not in this PR's code — but this PR is what triggers
   it, and it must be fixed here because CI cannot go green otherwise.
2. **A malformed `type` in a `namedEntities` payload returns HTTP 500**,
   found by exercising the running service. Not a regression, but the PR
   introduces the validation layer that is supposed to prevent exactly
   this, and the new validation test matrix has no case for it.

The rest are smaller quality items. Reviewer `Fabdulla1`'s two concerns
have both been addressed on the branch — see "Existing PR feedback".

## Findings

### 1. CI failure: `test_query_fragmentarium_number`

Severity: **High** (blocking — CI is red)

`ebl/tests/fragmentarium/test_fragment_repository_query.py:26` fails on
`Test Python 3.12` in both CI runs (jobs 88973247745 and 88973258912):

    AssertionError: assert QueryResult(items=[QueryItem(... 'X', '252')])
                        == QueryResult(items=[QueryItem(... 'X', '251')])

The query for one museum number returns more than one fragment. Root
cause:

- `number_is()` in
  [queries.py:46](ebl/fragmentarium/infrastructure/queries.py#L46) builds
  an `$or` across `externalNumbers.cdliNumber`, `museumNumber`,
  `accession` **and** `archaeology.excavationNumber`.
- `FragmentFactory.number` mints `MuseumNumber("X", str(n))`
  ([fragment.py:245](ebl/tests/factories/fragment.py#L245)) and
  `ArchaeologyFactory.excavation_number` mints
  `ExcavationNumber("X", str(n))`
  ([archaeology.py:71](ebl/tests/factories/archaeology.py#L71)) — **same
  prefix, two independent sequence counters**.

When the counters cross, one fragment's museum number equals another
fragment's excavation number, the `$or` matches both documents, and the
test's single-item expectation fails. This is a shared id namespace split
across two unrelated counters — the same class of defect the data hard
gate warns about, here in test fixtures.

The test file, the factories and `number_is` are all untouched by this
PR. Master's test jobs are green (run 29823535384; the recent master run
failures are Dependabot jobs, not tests). What this PR changes is the
*number* of factory instances built per xdist worker — it adds and splits
many `ebl/tests/fragmentarium/*` files — which moves the counters into
collision. So: latent defect, deterministically surfaced here.

Recommendation: make the two id spaces disjoint at the source rather than
patching the one test, so the whole class of flake goes away.

    # ebl/tests/factories/archaeology.py:71
    excavation_number = factory.Sequence(
        lambda n: ExcavationNumber("EX", str(n))
    )

Then re-run the affected suites (`test_fragment_repository_*`,
`test_fragment_archaeology_route`, `test_findspot_repository`) since some
assert on excavation-number strings.

### 2. Invalid `namedEntities[].type` returns HTTP 500, not 422

Severity: **High**

`AbstractNamedEntitySchema.type` in
[named_entity_schema.py:17](ebl/fragmentarium/application/named_entity_schema.py#L17)
is a `fields.Function` whose deserializer calls
`NamedEntityType.from_name`, which raises **`ValueError`** via
`get_by_attribute_value`
([named_enum.py:8](ebl/common/domain/named_enum.py#L8)). Marshmallow only
converts `ValidationError` into field errors, so the `ValueError` escapes
`NamedEntityResource._load`'s `except ValidationError`
([named_entities.py:63](ebl/fragmentarium/web/named_entities.py#L63)) and
leaves the handler as a 500.

Not a regression — master had no handler at all — but this PR adds
`_load` precisely to turn malformed payloads into a 422, and the hole is
in that new code. It also means every typo'd `type` value from a client
becomes a Sentry error rather than a client-side validation message.

Recommendation: use the repo's existing enum field, which already
converts `KeyError` / `ValueError` into `ValidationError`
([schemas.py:28](ebl/schemas.py#L28)). For `NamedEntityType` the member
name and `long_name` are identical for every member, so this is
wire-compatible with the current `fields.Function`.

    from ebl.schemas import NameEnumField

    class AbstractNamedEntitySchema(Schema):
        id = fields.String(required=True)
        type = NameEnumField(NamedEntityType, required=True)

Add the missing case to the parametrized matrix in
[test_named_entity_route_validation.py:22](ebl/tests/fragmentarium/test_named_entity_route_validation.py#L22),
which covers cross-field, missing-field, malformed-`realiaId` and
unknown-key payloads but **no invalid `type` value**.

    pytest.param(
        {"namedEntities": [{**ENTITY_SPAN, "type": "PersonalName"}]},
        id="invalid_type",
    ),

### 3. Realia-store failure degrades silently

Severity: **Medium**

`_find_by_realia_ids` in
[realia_info.py:26](ebl/fragmentarium/application/realia_info.py#L26)
swallows every `PyMongoError` and returns `[]`. This correctly closes the
post-write 500 window Fabdulla1 raised, and is well tested. But the
resulting `realiaInfo: []` is **indistinguishable from "this fragment has
no realia"** — there is no log line, no metric, no response signal. A
realia store that is down or slow looks to clients and to operators
exactly like a corpus with no realia annotations, and the fragment's own
`realia` array still lists the annotations, so the two fields silently
disagree.

Recommendation: log a warning (or add a Sentry breadcrumb) in the
`except` branch before returning `[]`. Degrading is right; degrading
invisibly is not.

Related asymmetry worth a comment in the code: `_validate_realia_ids`
([named_entities.py:78](ebl/fragmentarium/web/named_entities.py#L78))
calls `find_by_realia_ids` **unguarded**, so a store failure during a
POST raises a 500 before anything is written. That is the right call —
fail closed before a write, degrade after one — but it is currently
implicit and untested.

### 4. mypy errors remain in files this PR touches

Severity: **Medium** (gate 8)

`poetry run mypy <changed> --ignore-missing-imports` reports 10 errors in
changed files:

| File and line | Error |
| --- | --- |
| `domain/fragment.py:176` | `Sequence[Enum]` vs `Iterable[Scope]` |
| `domain/fragment_metadata.py:9` | no attr `PARSE_ERRORS` |
| `domain/fragment_metadata.py:9` | no attr `parse_markup_paragraphs` |
| `domain/text_line.py:120` | bad kwarg `unique_lemma` for `evolve` |
| `domain/text_line.py:144` | `merge` return type vs supertype |
| `domain/word_tokens.py:106` | `AbstractWord` where `T` expected |
| 4 test files | no attr `parse_atf_lark` |

I verified every one against an `origin/master` worktree: **all are
pre-existing**, and the branch actually *removes* two of them. So this is
not a regression. It is still gate 8 as written — "a pre-existing error
in a file you touched is not acceptable; fix it" — so flagging it rather
than waving it through. The `lark_parser` group is a repo-wide
dynamic-module pattern and is best fixed once with an `__all__` or a
stub, not per-file.

### 5. `annotation_key` discriminates by `isinstance` probe

Severity: **Low**

[named_entity.py:57](ebl/fragmentarium/domain/named_entity.py#L57):

    value = (
        span.realia_id
        if isinstance(span, RealiaAnnotationSpan)
        else span.type.long_name
    )

This is the "does it have `type`, or does it have `realiaId`?" probe the
data hard gate calls out, even though the arrays themselves are correctly
separated. `deduplicate_spans` is already generic over a **homogeneous**
`Sequence[SpanT]`, so the probe buys nothing.

Recommendation: give each span class the key directly and drop the union,
the `isinstance` and the `AnnotationSpan` alias from this path.

    class EntityAnnotationSpan(NamedEntity):
        @property
        def key_value(self) -> str:
            return self.type.long_name

    class RealiaAnnotationSpan(RealiaEntity):
        @property
        def key_value(self) -> str:
            return self.realia_id

### 6. Duplicated `make_token` bodies

Severity: **Low** (qlty `similar-code`, 2 occurrences)

`WordSchema.make_token` and `LoneDeterminativeSchema.make_token` at
[token_schemas_words.py:68](ebl/transliteration/application/token_schemas_words.py#L68)
and
[:90](ebl/transliteration/application/token_schemas_words.py#L90) are 20
identical lines apart from the target class. Extract the argument
assembly into `BaseWordSchema` and have each subclass supply only its
`.of` target. This also removes the risk of a third field (after
`named_entities` and now `realia`) being added to one copy and not the
other.

### 7. Weak type hints in `named_entities.py`

Severity: **Low**

In
[named_entities.py:45](ebl/fragmentarium/web/named_entities.py#L45):
`entities: Sequence` is an implicit `Sequence[Any]`,
`word_ids: Dict[str, list]` an implicit `Dict[str, list[Any]]`, and
`_load(self, data, ...)` has no annotation on `data` at all. Suggest
`Sequence[AnnotationEntity]`, `Dict[str, List[str]]` and
`data: Mapping[str, object]`.

### 8. Repo hygiene

Severity: **Low**

- `TASK-740-todo.md` and `TASK-740-log.md` are committed on the branch —
  removed in `0c7ec147`, re-added in `d99cd834`. Delete before merge,
  together with this review file and its TODO and log.
- `.gitignore` adds `.claude/` while the same PR commits
  `.claude/settings.json`. Tracked files stay tracked, so it works, but
  future edits to that file will never show in `git status`. Either
  un-ignore it explicitly or do not commit it.
- The PR carries tooling and instruction changes unrelated to the realia
  API (`.github/instructions/copilot.instructions.md` +209,
  `.claude/settings.json`, `Taskfile.dist.yml`,
  `.devcontainer/devcontainer.json`). Splitting them into their own PR
  would make both easier to review — Sourcery already refused this one
  for exceeding its 150000-character diff limit.
- Pre-existing, adjacent to a line this PR edits:
  [mongo_fragment_repository.py:112](ebl/fragmentarium/infrastructure/mongo_fragment_repository.py#L112)
  has `"ocredSigns": ("ocredSigns")` — a bare string among tuples,
  missing its trailing comma. Worth fixing while the dict is open.

## Severity

| # | Finding | Severity | Blocking |
| --- | --- | --- | --- |
| 1 | Factory id-space collision | High | Yes |
| 2 | Invalid `type` gives HTTP 500 | High | Yes |
| 3 | Silent realia-store degradation | Medium | No |
| 4 | mypy errors in touched files | Medium | No |
| 5 | `isinstance` probe | Low | No |
| 6 | Duplicated `make_token` bodies | Low | No |
| 7 | Weak type hints | Low | No |
| 8 | Repo hygiene | Low | No |

## Reproduction Steps

### Finding 1

Isolated to the exact mechanism, since the CI ordering is not
reproducible locally. Save as
`ebl/tests/fragmentarium/test_zz_repro.py`:

    import attr
    from ebl.common.query.query_schemas import QueryResultSchema
    from ebl.fragmentarium.domain.archaeology import ExcavationNumber
    from ebl.tests.factories.fragment import FragmentFactory
    from ebl.tests.fragmentarium.fragment_query_test_helpers import (
        query_item_of,
    )
    from ebl.tests.fragmentarium.fragment_repository_test_helpers import (
        COLLECTION,
        SCHEMA,
    )


    def test_number_query_collides(database, fragment_repository):
        fragment = FragmentFactory.build()
        other = FragmentFactory.build()
        other = attr.evolve(
            other,
            archaeology=attr.evolve(
                other.archaeology,
                excavation_number=ExcavationNumber(
                    fragment.number.prefix, fragment.number.number
                ),
            ),
        )
        database[COLLECTION].insert_many(
            [SCHEMA.dump(fragment), SCHEMA.dump(other)]
        )

        result = fragment_repository.query(
            {"number": str(fragment.number)}
        )

        assert result == QueryResultSchema().load(
            {"items": [query_item_of(fragment)], "matchCountTotal": 0}
        )

Run `poetry run pytest ebl/tests/fragmentarium/test_zz_repro.py`: queried
`X.0`, returned `['X.0', 'X.1']`. Delete the file afterwards.

### Finding 2

Against the running service (real WSGI server, real mongod, real HTTP):

    curl -s -X POST "$BASE/fragments/$NUMBER/named-entities" \
      -H 'Content-Type: application/json' \
      -d '{"namedEntities":[{"id":"E-1","type":"PersonalName",
           "span":["Word-1"]}],"realia":[]}'
    # {"title": "500 Internal Server Error"}

The same request with `"type": "PERSONAL_NAME"` returns 200. Control
cases on the same server all behave correctly: `realiaId` inside
`namedEntities` gives 422, `namedEntities` not a list gives 422,
malformed `realiaId` gives 422, unknown `realiaId` gives 422, and a
duplicate id across both arrays gives 422.

## Existing PR feedback

Per the review hard gate, all GitHub feedback was fetched
(`/pulls/740/reviews`, `/pulls/740/comments`,
`/issues/740/comments`) and every item is addressed below. No PRs other
than `origin/master` are merged into this branch.

### `Fabdulla1` — CHANGES_REQUESTED, 2026-07-22

Concern 1, *"the mutation is persisted before `FragmentDtoFactory.create()`
performs the Realia lookup … the client could receive a 500 even though
the update has already been committed"* — **addressed on the branch**.
Commit `ec77d757` added the `except PyMongoError` guard in
`_find_by_realia_ids`, so a post-write lookup failure now degrades to
`realiaInfo: []` and returns 200. Covered by
`test_write_commits_and_degrades_realia_info_on_infrastructure_failure`,
which asserts the write persisted and a later GET returns the correct
`realiaInfo`. See finding 3 for the one thing still missing: the
degradation is silent.

Concern 2, *"tests cover missing Realia records being omitted but I
couldn't find coverage for an actual infrastructure failure from
`find_by_realia_ids`"* — **addressed**. Three route-level tests now cover
it (GET, retrieve-all, and post-write) plus two unit tests in
`test_realia_info.py`. All pass locally.

### `sourcery-ai[bot]` — 2026-07-16

*"Your pull request is larger than the review limit of 150000 diff
characters."* — **acknowledged, not directly actionable**. Noted under
finding 8: splitting the unrelated tooling and instruction changes out
would bring the diff back under Sourcery's limit and restore automated
review coverage.

### `qltysh[bot]` — 12 inline comments, 2026-07-22

Two `similar-code` findings in `token_schemas_words.py` — **valid, see
finding 6**.

Ten `function-parameters` findings (count 6-9) — **acknowledged, no
change recommended**. Every one is a pytest test function or helper whose
"parameters" are injected fixtures (`client`, `database`,
`fragmentarium`, `user`, `when`, `changelog`), not a caller-facing
signature. Collapsing fixtures into a container object to satisfy a
parameter-count metric would make the tests harder to read and is not how
pytest is meant to be used. The one non-fixture case,
`expect_changelog(when, changelog, user, number, before, after)` at
[fragment_updater_test_helpers.py:13](ebl/tests/fragmentarium/fragment_updater_test_helpers.py#L13),
takes four fixtures plus the before/after pair it exists to compare —
also reasonable. If the project wants the qlty dashboard clean, suppress
`qlty:function-parameters` for `ebl/tests/**` in the qlty config rather
than distorting the tests.

## Gates run for this review

| Gate | Result |
| --- | --- |
| `task format` | 775 files formatted, nothing unstaged |
| `task lint` (ruff) | All checks passed |
| `task type` (**pyre**, the CI gate) | No type errors found |
| `task type-pyright` | 0 errors, 0 warnings |
| `task test` (`pytest -n auto`) | 3933 passed, 2 skipped, 1 xfail |
| `task lint-md` | 0 errors |
| `flake8 --max-line-length=120` | 1 E203, pre-existing, untouched |
| `mypy --ignore-missing-imports` | 10 errors, pre-existing — finding 4 |
| Coverage on changed modules | 100% on all but one line |
| 250-line file limit | met; longest changed file is 240 |
| Live service verification | ran the real app; found finding 2 |
| Data hard gate | passes — see below |

The E203 is in the repo's own ruff ignore list (`pyproject.toml:69`), is
a known formatter-versus-PEP-8 conflict, and sits on a line this PR does
not touch.

Coverage was measured with the full suite under
`--cov=ebl.fragmentarium --cov=ebl.transliteration --cov=ebl.realia`.
All 36 changed source modules report **100%** except
`mongo_fragment_repository.py` at 98%: line 117, the
`raise ValueError("Unexpected update field ...")` guard, is unhit. That
line is **not** added, modified or moved by this PR — the diff replaces
only line 113 — so the touched-lines coverage requirement is met. It is
still an uncovered branch in a file this PR opens, and one small test
would close it; noting it rather than counting it against the PR.

On the data hard gate: arrays are separated at domain, Mongo and wire
level; union-wide id uniqueness is enforced by
`_validate_unique_ids([*entity_spans, *realia_spans])` and confirmed live
(422); cross-field payloads are rejected as unknown fields (422). One
probe to clean up, finding 5.

## Recommendation

**Request changes.** Findings 1 and 2 must be fixed before merge — CI
cannot go green without 1, and 2 turns a client typo into a 500 in a code
path this PR introduced specifically to validate payloads. Both fixes are
small and both have a clear in-repo idiom to follow.

Findings 3 and 4 should be handled in this PR (a log line, and the gate-8
cleanup on touched files). Findings 5 to 8 are quality items that can
ride along or follow.

The underlying design is good and the hardest structural requirement —
never mixing two data types in one array, while still enforcing
invariants across the union of the separated arrays — is met properly, at
every level, and holds up under live traffic.

Before merge, delete `TASK-740-todo.md`, `TASK-740-log.md`,
`TASK-740-review.md`, `TASK-740-review-todo.md` and
`TASK-740-review-log.md`.
