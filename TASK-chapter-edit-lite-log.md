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
- Full `pytest` with the CI environment variables: 6661 passed, 2 skipped,
  1 xfailed, 0 failed
- Coverage of every new or changed corpus module: 100 %
- `mypy`: errors only in files this task did not touch
  (`fragmentarium` schemas and two test factories)
- `qlty smells --include-tests`: not run, qlty is not installed

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
