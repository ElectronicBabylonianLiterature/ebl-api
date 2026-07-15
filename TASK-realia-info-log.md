# TASK realia-info — Work Log

## Context

- Frontend consumes `FragmentDto.realiaInfo?: RealiaInfoEntry[]`
  (`{ realiaId, lemma, type }`) to label realia annotations without per-id
  `/realia/by-id` calls. Absent field degrades gracefully.
- Realia annotations live on `fragment.realia: Sequence[RealiaEntity]`
  (`id`, `realia_id`). The realia entry's `_id` is the lemma, `type` is the
  classification array; lookup key is `realiaId`.

## Design decisions

- `realiaInfo` is read-only display data added **only on the GET full-fragment
  path** (`GET /fragments/{number}`). Writes reuse the shared
  `create_response_dto` without it, so it is never emitted or stored on writes.
- Threaded via a context var + `fields.Function` on `FragmentDtoSchema`, mirroring
  `hasPhoto`/user. `None` default is dropped by the existing `filter_none`
  `post_dump`, so writes stay unchanged; GET passes a list (possibly `[]`).
- Batch load mirrors #735 / `find_by_realia_id`: one `$in` query, projected to
  `{realiaId, _id, type}` (no bibliography injection needed).
- Distinct + dangling handled by the query itself: dedup input ids; missing ids
  simply return no document and are omitted.

## Progress

- Explored fragment/realia domain, schemas, repository, DTO, bootstrap, tests.
- Implemented all files; ran full gate suite.

## Changes

Source:

- `ebl/fragmentarium/domain/realia_info.py` — new `RealiaInfo` value object.
- `ebl/fragmentarium/application/realia_info.py` — `RealiaInfoSchema` +
  `resolve_realia_info(fragment, realia_repository)`.
- `ebl/realia/application/realia_repository.py` — abstract `find_by_realia_ids`.
- `ebl/realia/infrastructure/mongo_realia_repository.py` — batch `$in` impl,
  projected to `{realiaId, _id, type}` (no bibliography injection).
- `ebl/fragmentarium/web/dtos.py` — `realiaInfo` context var + `fields.Function`
  on `FragmentDtoSchema`; optional `realia_info` arg on `create_response_dto`
  (omitted via existing `filter_none` when `None`). Also typed
  `fragment_user_context` to clear a pre-existing mypy error in this file.
- `ebl/fragmentarium/web/fragments.py` — `FragmentsResource` resolves and passes
  `realia_info` on GET.
- `ebl/fragmentarium/web/bootstrap.py` — inject `realia_repository`.

Tests:

- New: `test_realia_info_route.py`, `test_realia_info.py` (schema + resolver),
  batch cases in `test_realia_repository.py`.
- Updated GET-after-write assertions (archaeology, transliterations, date,
  dates-in-text, script, scope, genre, references, lemmatization) and `test_get`
  to expect the new GET-only `realiaInfo: []`.

## Gate results

- `ruff format --check ebl`: clean (746 files formatted).
- Full `poetry run pytest`: 3908 passed, 2 skipped, 1 xfailed, 0 failed.
- flake8 (`--max-line-length=120`) on changed files: clean.
- mypy (`--ignore-missing-imports`) on changed files: no self-errors. Remaining
  project-wide errors are pre-existing debt in untouched files (corpus,
  transliteration, ebl_ai_client, ...) and were not introduced here.
- Coverage: `dtos.py` and `fragments.py` now at **100%**. Added tests for the
  pre-existing branches in the touched files: `parse_excavation_number`
  (test_dtos.py), `_parse_skip` non-numeric/negative/too-large + retrieve-all
  serialization loop + `/fragments/all-signs` (test_fragments_route.py), and
  invalid-scope `on_post` (test_fragment_scope.py). Realia/new modules already
  at 100%.
- Lint: project gate is `ruff check ebl` (ignores E203/E231/E501) — clean on all
  changed files. `flake8 --max-line-length=120` also clean once the project's
  documented E203/E231 ignores are applied (the lone E203 hit is a pre-existing,
  untouched slice line identical on HEAD, one of 12 repo-wide).

## Status

Work complete; changes are UNCOMMITTED. Awaiting review / commit instruction.
