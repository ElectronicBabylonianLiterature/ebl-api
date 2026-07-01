# TASK-723 — Realia lemma lookup with slash in `_id`

## Goal

Make `GET /realia/<lemma>` work when the lemma (`_id`) contains a `/` (encoded
as `%2F`), backend-only, keeping human-readable URLs.

## TODO

- [x] Read relevant realia web/repository/test files
- [x] Confirm Falcon 3.1.3 route-vs-sink precedence (routes first) in source
- [x] Confirm sink named groups become kwargs
- [x] Confirm deployment WSGI stack (waitress) and absence of reverse proxy
- [x] VERIFY `%2F` passes decoded through the stack (waitress + Falcon)
- [x] Add sink resource in `ebl/realia/web/realia.py` (GET; OPTIONS preflight;
      405 otherwise)
- [x] Register sink in `ebl/realia/web/bootstrap.py` on prefix `/realia/`
- [x] Diagnose + fix second symptom: CORS preflight OPTIONS on the sink
- [x] Add tests in `ebl/tests/realia/test_realia_route.py`
      - slash-in-id 200 + correct `_id`
      - multi-segment not-found 404
      - non-GET method rejected (405 + Allow)
      - CORS preflight OPTIONS succeeds (200 + Access-Control-Allow-Methods)
      - regression: single-segment, `/realia/by-id/...`, `/realia` search,
        single-segment not-found, `by-id` lemma not shadowed (existing tests)
- [x] Gates: format, lint (ruff+flake8), type (pyre clean; mypy clean on
      changed files), coverage 100% on changed files, full suite green
- [ ] Remind to remove TASK-723 files before merge
