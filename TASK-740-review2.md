# TASK-740-review2 — Review of PR #740

**PR:** [#740](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/740)
— "Realia annotation API: resolve realiaInfo on every fragment-returning route"

**Branch:** `add-realia-annotation-api` → `master`
**Reviewed SHA:** `84acd6f7` (identical to local `HEAD`)
**Review decision on GitHub:** `CHANGES_REQUESTED` · `mergeStateStatus: BLOCKED`

## Summary

The core change is sound and the central design constraint is genuinely met.
`realia_info` is now a required argument of `create_response_dto`, and a
`FragmentDtoFactory` is injected into all 13 fragment-returning resources, so
a route can no longer forget to resolve it. I verified the fix end to end
against a running instance of the modified service: on `master` the write
routes call `create_response_dto(fragment, user, has_photo)` and the
`realiaInfo` key is absent from the response; on this branch it is present and
populated on both read and write routes.

The **data hard gate is fully satisfied** — `namedEntities` and `realia` are
structurally separate at domain, Mongo and wire level, there is no
discriminator and no probing, and uniqueness is still enforced across the
union of the two id arrays. I confirmed all of this against the running
service, not just by reading the code (see Reproduction Steps).

Both concerns in Fabdulla1's `CHANGES_REQUESTED` review have since been
addressed by commits `ec77d757` and `84acd6f7`; that review is stale. See
Findings 3 for the one place this is not reflected.

**The blocking problem is that the branch does not pass its own gates.** CI is
red at the reviewed SHA on `task type` (pyre), and `task type-pyright` — a gate
this very PR introduces — fails on two files the PR changes.

## Findings

### Finding 1 — CI is red: pyre error introduced by this PR's own refactor

Severity: **Blocker**

`task type` (pyre) is the checker CI enforces, and it fails at `84acd6f7`:

```text
ebl/transliteration/application/token_schemas_words.py:52:0
Uninitialized attribute [13]: Attribute `word_class` is declared in class
`AbstractWordSchema` to have type `Type[Word]` but is never initialized.
```

`AbstractWordSchema` declares `word_class: ClassVar[Type[Word]]`
([token_schemas_words.py:53](ebl/transliteration/application/token_schemas_words.py#L53))
with no value. `WordSchema` and `LoneDeterminativeSchema` assign it, but the
declaring class never does, and the class is not an ABC. The class was created
by this PR when `token_schemas.py` was split, so this is a new error, not an
inherited one.

Consequence: the `Test Python 3.11` job fails, and the `3.12` and `pypy-3.11`
jobs are **CANCELLED** — so the test suite never completed in CI on this SHA.

This also means the PR's stated verification ("pyre, pyright, mypy … all
clean") predates the final rewrite. The instructions' "re-verify after every
rewrite" gate applies: the earlier verification run is void.

**Recommendation:** give the base class a value (`word_class: ClassVar[Type[Word]]
= Word`) or make `AbstractWordSchema` genuinely abstract. Confirm with
`task type` — do not infer the result from mypy or pyright, which both accept
the current code.

### Finding 2 — `task type-pyright` fails on files this PR changes

Severity: **Blocker** (for the repo's own gate; CI does not run this task)

This PR adds `task type-pyright` and wires it into `test-all`, describing it as
closing a gate gap. The branch does not pass it:

```text
41 errors, 0 warnings, 0 informations
task: Failed to run task "type-pyright": exit status 123
```

| Errors | File | In this PR's diff? |
| ------ | ---- | ------------------ |
| 40 | `ebl/tests/factories/archaeology.py` | yes |
| 1 | `ebl/tests/fragmentarium/test_fragment_repository_updates.py` | yes |

The `archaeology.py` errors are `reportPrivateImportUsage` /
`reportIncompatibleVariableOverride` on `factory_boy` imports; the
`test_fragment_repository_updates.py` error is a real typing mismatch
(`tuple[Literal['aklu I']]` passed where `Lemma | None` is expected — the
element type should be `WordId`).

Because the task is diff-scoped, touching a file pulls its pre-existing errors
into the gate. That is exactly the standard the instructions set ("a
pre-existing error in a file you touched is not acceptable; fix it").

Note CI runs only ruff, pyre, pytest and coverage — it does **not** run
`type-pyright`, so this will not turn the build red. It still fails locally
for anyone running `task test-all`, which undercuts the stated purpose of
adding the gate.

### Finding 3 — The PR description contradicts the shipped behaviour

Severity: **Medium**

The description states:

> No `try`/`except` was added around resolution — a realia lookup failure
> propagates rather than being silently swallowed into `[]`.

The shipped code does the opposite. `_find_by_realia_ids` catches
`PyMongoError` and returns `[]`
([realia_info.py:30-42](ebl/fragmentarium/application/realia_info.py#L30-L42)),
which is the right call and is what resolves Fabdulla1's post-write-failure
concern — but the description was not updated when `ec77d757` changed the
behaviour. A reviewer trusting the description would reach the wrong
conclusion about error semantics.

**Recommendation:** update the PR body to describe the graceful-degradation
semantics that actually ship.

### Finding 4 — mypy gate not satisfied on touched files

Severity: **Low**

`poetry run mypy <changed modules> --ignore-missing-imports` reports 5 errors
located in files this PR changes:

- `fragment_metadata.py:9` — `lark_parser` has no attribute `PARSE_ERRORS`
  *(relocated by this PR)*
- `fragment_metadata.py:9` — `lark_parser` has no attribute
  `parse_markup_paragraphs` *(relocated by this PR)*
- `text_line.py:120` — unexpected keyword argument `unique_lemma` for
  `evolve` *(pre-existing)*
- `text_line.py:144` — return type of `merge` incompatible with supertype
  *(pre-existing)*
- `word_tokens.py:106` — incompatible return value type (`AbstractWord` vs
  `T`) *(pre-existing)*

I confirmed against a worktree at the merge-base which of these pre-existed.
Two of them are **relocated** by this PR: they were on `fragment.py:29-30` at
the base and moved into the newly created `fragment_metadata.py`. Moved lines
are in scope for the gate.

To the PR's credit, it also *fixed* one mypy error that existed at the base
(`Invalid index type "int" for "LineLemmaAnnotation"`, now correctly
`TokenIndex(index)`).

### Finding 5 — Degraded `realiaInfo` is indistinguishable from "no realia"

Severity: **Low**

On a realia-store failure the response carries `realiaInfo: []` while the
`realia` array still lists the annotations. The client cannot tell "this
fragment has no realia" from "the realia store is down", and will silently
render raw `realia_000846` ids — the exact symptom this PR set out to fix. The
only signal is a server-side `logger.warning`.

Note the asymmetry, which I believe is deliberate and correct but undocumented:
`_validate_realia_ids` calls `find_by_realia_ids` **directly**
([named_entities.py:101](ebl/fragmentarium/web/named_entities.py#L101)), so a
store failure during pre-write validation fails hard with no partial write,
while the post-write DTO path degrades. Worth a comment or a note in the PR
body so the split is not "fixed" later by someone who reads it as an
oversight.

### Finding 6 — Out-of-scope drive-by fix with no test

Severity: **Low**

[mongo_fragment_repository.py:112](ebl/fragmentarium/infrastructure/mongo_fragment_repository.py#L112)
changes `"ocredSigns": ("ocredSigns")` to `"ocredSigns": ("ocred_signs",)`.

The old value was missing a comma, so it was a **string**, not a tuple. I
confirmed the old form always raised:

```text
'ocredSigns'      -> StringNotCollectionError "only" should be a list of strings
('ocredSigns',)   -> ValueError Invalid fields for FragmentSchema
('ocred_signs',)  -> OK
```

So this is a genuine latent-bug fix and the snake_case rename was required
(`only=` takes attribute names, not `data_key`s). However: nothing calls
`update_field("ocredSigns", …)` anywhere in the codebase — `update_ocred_signs.py`
writes to the collection directly — and no test exercises this branch. It is
dead code being fixed in a PR about realia.

**Recommendation:** either add a test alongside the other `update_field` cases
in `test_fragment_repository_updates.py`, or drop the hunk from this PR.

### Finding 7 — 12 unaddressed qlty inline comments

Severity: **Low**

None have been replied to or resolved:

10 × `qlty:function-parameters`, all in test code, listed in full so none is
dropped silently:

| Params | Location |
| ------ | -------- |
| 6 | `fragment_updater_test_helpers.py:13` `expect_changelog` |
| 8 | `test_fragment_updater.py:132` `test_update_metadata_field` |
| 6 | `test_fragment_updater_annotations.py:19` `test_update_lemmatization` |
| 7 | `test_fragment_updater_annotations.py:65` `test_update_references` |
| 7 | `test_fragment_updater_annotations.py:111` `..._edition_metadata_field` |
| 6 | `test_fragment_updater_annotations.py:126` `..._lemma_annotation` |
| 7 | `test_fragment_updater_annotations.py:161` `..._named_entities` |
| 6 | `test_introduction_route.py:22` `test_update_introduction` |
| 9 | `test_introduction_route.py:79` `test_update_multiple_fields` |
| 6 | `test_notes_route.py:17` `test_update_notes` |

These are pytest fixture parameters, which is idiomatic and not a real defect;
my rationale for not treating them as blocking is that collapsing them would
mean bundling fixtures into a container purely to satisfy a counter. They
should still be acknowledged on the PR rather than left unanswered.

2 × `qlty:similar-code`, at
[token_schemas_words.py:72](ebl/transliteration/application/token_schemas_words.py#L72)
and `:90` — 20 duplicated lines, mass 145. This one is real: `make_token` in
`AbstractWordSchema`, `AkkadianWordSchema` and `GreekWordSchema` are
near-identical argument-forwarding bodies.

Fixing the duplication would likely also resolve Finding 1, since the
`word_class` indirection exists only to share that body.

Sourcery declined to review the PR at all ("larger than the review limit of
150000 diff characters"), so there is no automated logic review on this
change. At 98 files / +5499 −1987 the PR is large enough that splitting the
`token_schemas.py` and `text.py` refactors out from the realia feature would
have improved reviewability.

### Finding 8 — Annotations are dropped on transliteration update

Severity: **Informational** — pre-existing, extended to realia by this PR

`AbstractWord._merge_word`
([word_tokens.py:110-121](ebl/transliteration/domain/word_tokens.py#L110-L121))
carries `unique_lemma` and alignment across a merge but not `named_entities`
or `realia`, and `update_transliteration` re-runs `set_token_ids()`. The
fragment-level `named_entities` / `realia` arrays are **not** cleared, so after
a transliteration update the fragment still lists the entities while no word
references them, and `GET /named-entities` returns them with empty `span`s.

This is existing behaviour for named entities and the PR makes realia behave
identically — consistent, and arguably out of scope. Flagging only to confirm
it is intended.

### Finding 9 — Task tracking files are committed on the branch

Severity: **Housekeeping — must be resolved before merge**

Nine tracking files are tracked in git on this branch and appear in the diff:

```text
TASK-740-fix-log.md      TASK-740-review-log.md    TASK-740-split-log.md
TASK-740-fix-todo.md     TASK-740-review-todo.md   TASK-740-split-todo.md
TASK-740-log.md          TASK-740-review.md        TASK-740-todo.md
```

Plus the three files from this review (`TASK-740-review2-todo.md`,
`TASK-740-review2-log.md`, `TASK-740-review2.md`), which are currently
untracked. All must be removed before the PR is merged.

## Severity

| # | Finding | Severity |
| - | ------- | -------- |
| 1 | pyre error `word_class` uninitialized — CI red | **Blocker** |
| 2 | `task type-pyright` fails on two changed files | **Blocker** |
| 3 | PR description contradicts shipped error semantics | Medium |
| 4 | mypy errors remain in touched/relocated files | Low |
| 5 | Degraded `realiaInfo` indistinguishable from empty | Low |
| 6 | `ocredSigns` drive-by fix, dead code, untested | Low |
| 7 | 12 unaddressed qlty comments; no Sourcery review | Low |
| 8 | Annotations dropped on transliteration update | Info |
| 9 | Task tracking files committed on the branch | Housekeeping |

## Reproduction Steps

### Finding 1 — pyre failure

```bash
gh run view 30028549040 --log-failed | grep "Uninitialized attribute"
```

Local reproduction was **not possible in this container**: pyre initialises an
8 GB shared-memory heap and this environment has 2 CPUs / ~2 GB free RAM.
`task type`, then `--number-of-workers 2`, then
`--number-of-workers 1 --shared-memory-heap-size 2147483648` all aborted with
`Worker_exited_abnormally` / `End_of_file`. The CI result on the exact
reviewed SHA is the authoritative evidence and is quoted verbatim above.

### Finding 2 — pyright failure

```bash
task type-pyright   # 41 errors, exit status 123
```

### Findings verified against the running service

I started the **modified** service (real routes, real `FragmentDtoFactory`,
real `MongoRealiaRepository`, real `MongoFragmentRepository`) against a local
`mongod` on a scratch database. Only the auth backend was swapped, via
`attr.evolve(context, auth_backend=NoneAuthBackend(...))`, so write routes were
reachable without an Auth0 token. The configured `MONGODB_URI` points at a
remote production cluster and was deliberately **not** used.

Seeded: realia `realia_000846` → `Babylon` and `realia_000123` → `Assur`, and
fragment `REV.740` with `Entity-1` on `Word-1` and `Realia-1` on `Word-2`.

1. `GET /fragments/REV.740` → 200; `realiaInfo` resolved to `Babylon`;
   `namedEntities` and `realia` separate; per-word `namedEntities` and
   `realia` arrays separate.
2. `GET /fragments/REV.740/named-entities` → 200; object form with `span`s
   for both types.
3. `POST …/named-entities` with both arrays → 200; `realiaInfo` resolved to
   `Assur`.
4. `POST` with `realiaId` inside `namedEntities` → **422**
   `'realiaId': ['Unknown field.']`.
5. `POST` with an unknown `realiaId` → **422**
   `Unknown realiaId: realia_999999.`
6. `POST` with the same `id` in both arrays → **422**
   `Conflicting annotation ids: SAME.`
7. `POST /fragments/REV.740/genres` → 200; **`realiaInfo` present** — this is
   the defect being fixed.
8. `POST /fragments/REV.740/edition` → 200; **`realiaInfo` present**.

Case 4 confirms the data gate's claim that mixing becomes an unknown-field
error for free: marshmallow 3.26.2 defaults to `unknown=RAISE`, so no
discriminator or bespoke validator is needed. Cases 5 and 6 confirm that
existence and uniqueness invariants are still enforced across the **union** of
the two separated arrays.

Case 7 is the regression proof. At the merge-base,
`ebl/fragmentarium/web/fragment_genre.py:24` reads
`create_response_dto(updated_fragment, user, has_photo)` — no realia argument,
so `filter_none` stripped the key entirely.

### Finding 6 — `ocredSigns` mapping

```bash
poetry run python -c "
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
FragmentSchema(only='ocredSigns')"   # StringNotCollectionError
```

## Gates run for this review

- `task format` (ruff format --check) — **PASS**, 775 files already formatted
- `task lint` (ruff check) — **PASS**, all checks passed
- `task type` (pyre) — **FAIL**, 1 error per CI; not reproducible locally
  (see Reproduction Steps)
- `task type-pyright` — **FAIL**, 41 errors across 2 changed files
- `task test` (full suite) — **PASS**, 3938 passed, 2 skipped, 1 xfailed,
  0 failures
- Coverage on all 38 changed source modules — **PASS**, 2033 statements,
  0 missed, **100%**, every module individually at 100%
- flake8 `--max-line-length=120` on changed source — **PASS**, 0 errors
- mypy on changed source — **FAIL**, 5 errors in touched files (Finding 4)
- `task lint-md` — **PASS**, 0 errors
- 250-line file limit, all changed `*.py` — **PASS**, 0 files exceed;
  longest is 239
- Data hard gate (mixed-type arrays) — **PASS**, verified at runtime,
  cases 1–6
- Runtime verification of affected routes — **PASS**, 8 requests, all as
  expected
- Existing GitHub feedback incorporated — **DONE**, 3 reviews, 12 inline
  comments, 0 issue comments

## Recommendation

**Request changes.** The design is right and the feature works, but the branch
must not merge while it fails the checker CI enforces.

Required before merge:

1. **Fix the pyre error** (Finding 1) and re-run `task type` — this is what is
   turning CI red and preventing the suite from completing on 3.12 and pypy.
2. **Fix `task type-pyright`** (Finding 2), or explicitly scope the gate so it
   does not fail on the files this PR touches.
3. **Correct the PR description** (Finding 3) to describe the graceful
   degradation that actually ships.
4. **Remove the nine committed `TASK-740-*.md` files** (Finding 9).

Recommended, not blocking:

1. Clear the remaining mypy errors in touched files (Finding 4).
2. Either test or drop the `ocredSigns` hunk (Finding 6).
3. Respond to or resolve the 12 qlty comments; collapsing the three duplicated
   `make_token` bodies (Finding 7) would likely also resolve Finding 1.
4. Confirm the transliteration-update annotation behaviour is intended
   (Finding 8).

Fabdulla1's `CHANGES_REQUESTED` review can be marked resolved: the post-write
failure window is closed by the `PyMongoError` handler, and
`test_write_commits_and_degrades_realia_info_on_infrastructure_failure`
covers exactly the infrastructure-failure case that review asked for,
asserting both the degraded 200 response and that the write persisted.
