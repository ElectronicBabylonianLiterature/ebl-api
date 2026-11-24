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

## Step 3: light, revision-checked import and manuscripts saves

- `POST {chapter}/import` and `POST {chapter}/manuscripts` accept
  `view=outline` and `revision` with the same meaning as on
  `POST {chapter}/lines`: the outline with the new revision instead of the
  full chapter, and 409 when the chapter has changed. Without the
  parameters both respond exactly as before.
- `ChapterLinesWriter` became `ChapterEditWriter` with `save_lines`,
  `save_imported_lines` and `save_manuscripts`; the response switch is
  shared in `web/saved_chapter.py`.
- With a revision the revision is checked before bibliography references
  are injected, so a stale revision with an unknown reference gives 409.
- `Corpus.update_manuscripts` uses the shared reference injection; its
  behaviour is unchanged.
- Gates: `ruff`, `flake8`, `pyre`, `pyright` clean; qlty no findings;
  `task lint-md` 0 errors; corpus tests 875 passed with 100 % coverage of
  the new and changed modules; full suite 6858 passed, 2 skipped,
  1 xfailed.
- Short `pytest -n 3` runs of one or two files sometimes fail with
  `CursorNotFound`; this also happens on the unchanged tree.

## Step 4: move a line

- `POST {chapter}/lines/move?view=outline&revision=` with the body
  `{"from": i, "to": j}` removes the stored line at `from` and inserts it
  at `to`. The line is not rebuilt: variants, manuscript lines, alignment
  and lemmatization stay as stored, and line numbers do not change. Signs
  are recomputed; the parser version is untouched.
- The revision is required (422 without one); a stale one answers 409.
  A position out of range, an unchanged position and a move that breaks a
  translation extent answer 422; a malformed body answers 400. In all
  these cases nothing is stored and no changelog entry is written.
- A move records a compact changelog entry in the usual dictdiffer
  format: remove the line at `from`, add it at `to`, plus the changed
  signs. It replays with `dictdiffer.patch`. On a chapter the size of
  Enūma eliš I it takes 0.19 to 0.28 MB; the generic diff took 28.8 MB
  and did not fit MongoDB's 16 MB limit.
- `dictdiffer.revert` does not undo a move entry;
  `patch(reversed(swap(diff)))` does. A test pins this.
- Every save with a revision now builds its changelog entry and checks
  it against the 16 MB limit before the update. An entry that does not
  fit answers 422 and nothing is stored. Before, the chapter was stored
  and the request answered 500 without an entry. Until step 7 this can
  refuse a delete or insert near the start of a very large chapter.
- A save with a revision reads the chapter and its revision in one read
  and checks that revision, so content from a lagging replica set member
  cannot overwrite a newer edit.
- Reviews, each finding re-checked: stored-data integrity (no defect in
  the move), rules and test strength (three test gaps, fixed: the
  changelog entry of every save with a revision is replayed in a test;
  the move test chapter has uncertain fragments; shared move constants).
- A move takes 11 to 12 s on a chapter the size of Enūma eliš I (full
  load, signs, full rewrite): step 7.
- Tests: the move test chapter uses a fixed text id, because
  `TextIdFactory` runs past the Roman numeral 4999 in long serial runs.
  Short `pytest -n` runs can end with a server selection timeout when two
  workers share one in-memory MongoDB; CI uses a real MongoDB.
- Gates: `ruff`, `flake8`, `pyre`, `pyright` clean; qlty no findings;
  `task lint-md` 0 errors; full suite 7227 passed, 2 skipped, 1 xfailed;
  100 % line and branch coverage of the 11 new and changed modules.
- Browser run with the frontend against this API, seeded chapter with
  alignment and lemmas: 27 checks passed; every full line object is
  identical before and after each move.

## Step 5: alignment and lemmatization per line

- `POST {chapter}/lines/{number}/alignment?view=outline&revision=` and
  `POST {chapter}/lines/{number}/lemmatization?view=outline&revision=`
  save one line. The body is the entry of that line in the whole-chapter
  request: `{"alignment": [[manuscript alignment]]}`, one list per
  variant, or `{"lemmatization": [variant lemmatization]}`.
- The effect is exactly that of the whole-chapter updater for that one
  line; the per-line logic is shared with `AlignmentUpdater` and
  `LemmatizationUpdater`. A test compares both for every line. The
  whole-chapter endpoints behave as before.
- Both go through `_save_at_revision`: the revision is required (422
  "revision is required"), a stale one answers 409, and one replayable
  changelog entry is written after the update.
- Refused with 422 and nothing stored: a position out of range
  ("Invalid line: N is not a line position (number of lines: M)."), a
  wrong number of variants, manuscripts or tokens ("Invalid number of
  ... Got X, expected Y."), a value that does not match ("Invalid
  alignment" / "Invalid lemmatization"), duplicate alignment indices.
  A position that is not a number answers 404; a malformed body 400.
- `POST /lemmas/batch` with `{"words": [{"word", "isNormalized"}]}`, 1
  to 200 entries, answers in request order `{"word", "isNormalized",
  "lemmas"}`, where `lemmas` is exactly the answer of `GET /lemmas` for
  that word. It runs one aggregation per `isNormalized` value and one
  dictionary query for the whole batch.
- `GET /lemmas` now orders lemmas with equal counts by lemma id; before,
  their order was whatever the database returned.
- Lemma query: every part first selects the chapters, then the lines,
  variants and manuscript lines that contain a requested word, and keeps
  only the token arrays, before unwinding tokens. Before, every token of
  every chapter was unwound for each request. A test compares the counts
  with the same pipeline without the selections. The chapters are still
  scanned once per request: indexes or a precomputed table are a
  separate pull request.
- Gates: `ruff`, `flake8`, `pyre`, `pyright` clean; qlty no findings;
  full suite 7633 passed, 2 skipped, 1 xfailed; 100 % line and branch
  coverage of the 13 new and changed modules; no file over 250 lines.
- Browser run with the frontend against this API: 22 checks passed. A
  save of one line changes only that line.

## Step 5, follow-up: one lemma for every instance of a word

- `GET {chapter}/lemmatization/instances?word=&revision=` counts the
  instances of a word: lemmatizable word tokens with that clean value in
  the reconstructions and manuscript lines of every variant. It answers
  `{"word", "words", "lemmatized", "lines", "revision"}`.
- `POST {chapter}/lemmatization/instances?view=outline&revision=` with
  `{"word", "uniqueLemma"}` gives every instance that lemma, whatever it
  had before (user decision), through `_save_at_revision`. Only instance
  tokens change.
- Refused with 422 and nothing stored: no instance of the word; every
  instance already has exactly that lemma. An empty lemma id is refused
  with 400. Lemma ids are not checked against the dictionary, as in the
  other lemmatization saves.
- The count loads the whole chapter, so that count and save use one
  definition of an instance; on a very large chapter it takes seconds.
- Step 6 (keep existing alignments per manuscript line) is dropped by the
  user.
- Gates: `ruff`, `flake8`, `pyre`, `pyright` clean; qlty no findings (the
  move and word-instances handlers share `RevisionSaveResponder`); full
  suite 7819 passed, 2 skipped, 1 xfailed; 100 % line and branch
  coverage of the new and changed modules.
- Browser run with the frontend, keys only: 24 checks passed; the
  chapter-wide update changed 24 instances in 12 lines and nothing else.
