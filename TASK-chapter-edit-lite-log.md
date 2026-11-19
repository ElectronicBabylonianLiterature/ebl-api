# TASK chapter-edit-lite: log

## Findings

- The edit page's chapter GET returns 12 MB in 31 s on production for
  Enūma eliš I (162 lines, 75 manuscripts). The time is spent on the server.
- Replayed locally from production data, the same call takes 20.2 s and
  returns 11.9 MB.
- The whole chapter text is about 115 KB of ATF; token trees are the rest.

## Decisions

- New endpoints are additive; every existing response is unchanged.
- No caching for the new GETs: `ChapterCache.delete_chapter` would never
  purge their keys.
- New code lives in new modules because `web/chapters.py` and
  `application/corpus.py` are at the 250-line limit.
- The outline is built from a Mongo projection that never reads manuscript
  line tokens or signs; a dedicated loader reads that projection.
- No commit or push without explicit permission.

## Results on Enūma eliš I (local server, data replayed from production)

- `GET {chapter}`: 11.9 MB in 20.2 s
- `GET {chapter}/outline`: 78 KB in 0.42 s
- `GET {chapter}/lines?offset=0&limit=1`: 1.8 KB in 0.06 s
- `GET {chapter}/lines?offset=0&limit=10`: 20 KB in 0.4 to 0.7 s
- `GET {chapter}/lines?offset=0&limit=50`: 90 KB in 3.6 s
- `GET {chapter}/lines?offset=0&limit=10&tokens=true`: 839 KB in 1.3 s
- All 162 outline lines equal the full chapter's fields; every compared
  lines page equals the same slice of the full response.

## Gates

- `ruff format --check ebl scripts`: clean
- `ruff check ebl scripts`: clean
- `pyre check`: no type errors
- Full `pytest` with the CI environment variables: 6758 passed, 2 skipped,
  1 xfailed, 0 failed
- Coverage of every new or changed corpus module: 100 %
- `mypy`: errors only in files this task did not touch
  (`fragmentarium` schemas and two test factories)
- `qlty smells --include-tests` on every changed file: no findings
- `task lint-md` (markdownlint-cli2 on all Markdown files): 0 errors
- `pyright` and `flake8` on the changed files: clean

## Deviations and limits

- A one-line save took about 61 s locally on Enūma eliš I. The cost is in
  the existing update path (full load, merge, changelog, full rewrite), not
  in the response. `view=outline` only makes the response small.
- Saving could not be exercised on real data: the local database has no
  sign list, so the update is rejected with "Invalid signs". Saving is
  covered by the route tests on factory data.
- Mongo still reads the whole chapter document on the server for both new
  GETs; only the projection or slice leaves the database.

## Work log

- Branch renamed to `chapter-edit-performance-eoip5l`.
- Dependencies installed; in-memory MongoDB works for the tests with
  `PYMONGOIM__OS_VERSION=22` and `PYMONGOIM__MONGO_VERSION=7.0`.
- Domain layer, schemas and pagination written with Mongo-free tests.
- Repository mixin, reader, resources and routes written with
  Mongo-backed tests.
- Independent review: no defect found in the API code; duplicated helpers
  in the new test files were reported and removed.

## Step 1: review notes on pull request #827

- qlty, many parameters: the responders in `web/lines.py` and
  `web/chapter_outline.py` take `**chapter` and pass it to
  `create_chapter_id`; the two flagged tests take one case object.
- Sourcery, concurrent and stale saves: a chapter revision (the stored
  `_cacheRevision`, or `legacy` when absent) is returned by the outline and
  by every lines page. `POST {chapter}/lines?revision=` writes with one
  conditional update and answers 409 when the chapter has changed;
  `GET {chapter}/lines?revision=` answers 409 the same way. Without a
  revision both behave as before.
- With a revision the changelog entry is written after the update, so a
  rejected save leaves no entry. Saves without a revision keep the old
  order.
- A conditional update whose reply was lost and retried is recognised by
  its own new revision and not reported as a conflict.
- Sourcery, token trees with `tokens=false`: not changed. The ATF strings
  of the response are produced by `convert_to_atf` from the token objects,
  so the tokens must be loaded; only their serialisation is skipped.
- `mypy` from the system install reports `context=` errors under
  marshmallow 4; with the project interpreter it reports errors only in
  files this task did not touch.
