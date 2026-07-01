# TASK-723 — Work Log

## Investigation

- Routing today: `create_realia_routes` registers
  `/realia/by-id/{realia_id}`, `/realia/{realia_id}`, `/realia`. The
  single-segment template cannot match a decoded multi-segment path, so a
  lemma containing `/` produces a routing miss.

## Critical assumption verification — `%2F` survives the stack

Deployment server (Dockerfile): `waitress-serve --call ebl.app:get_app`. No
reverse proxy / WAF present in the repo (docker-compose has only api + mongo +
mongo-express).

- Waitress: parsed `GET /realia/Ninurta%2FNin%C4%9Dirsu` →
  `parser.error is None` (NOT rejected) and `parser.path` already contains the
  decoded `/`. `PATH_INFO` is built from this unquoted path (task.py:542);
  waitress collapses only *leading* duplicate slashes, internal slashes are
  preserved.
- Falcon 3.1.3 `_get_responder` (app.py:909-953): tries `_router_search`
  first; only when no route matches does it iterate `_sink_and_static_routes`.
  → Routes always take precedence over sinks. Sink named groups become kwargs
  (`params = m.groupdict()`).
- End-to-end Falcon test client: a sink on `/realia/(?P<realia_id>.+)`
  receives `req.path == '/realia/Ninurta/Ninĝirsu'` and
  `realia_id == 'Ninurta/Ninĝirsu'`; single-segment `/realia/Foo` still hits
  the route (sink not invoked).

Conclusion: a backend sink CAN fix this; proxy does not strip/reject `%2F`.

## Implementation

- `ebl/realia/web/realia.py`: added `RealiaLemmaSink` (callable sink). Handles
  `GET` via `realia_repository.find(realia_id)` + `RealiaEntrySchema` (identical
  to `RealiaResource`); answers `OPTIONS` with `200` + `Allow: GET, OPTIONS`;
  rejects other methods with `405` (`HTTPMethodNotAllowed`).
- `ebl/realia/web/bootstrap.py`: registered the sink with
  `api.add_sink(realia_lemma_sink, prefix=r"/realia/(?P<realia_id>.+)")`. Routes
  are added as before and take precedence, so the sink only catches
  multi-segment (slash-containing) paths.

## Second symptom: browser still "Failed to fetch" after the routing fix

Root cause: eBL sends an `Authorization: Bearer` header, so every realia GET is
preceded by a CORS **preflight `OPTIONS`**. For routed resources Falcon
auto-generates `on_options` (returns 200 + `Allow`), and the built-in
`CORSMiddleware` (enabled via `cors_enable=True`) copies `Allow` into
`Access-Control-Allow-Methods` — but only when `req_succeeded` is true. A sink
has no auto-OPTIONS; the first version raised `405` on OPTIONS, so
`req_succeeded` was false, the preflight block was skipped, and the browser saw
`405` with no `Access-Control-Allow-*` headers → "Failed to fetch". Reproduced
with `cors_enable=True`: single-segment preflight → `200`/`GET`; sink preflight
→ `405`/none.

Fix: the sink now answers `OPTIONS` with `200` + `Allow: GET, OPTIONS`, so
CORSMiddleware emits `Access-Control-Allow-Methods` and the preflight succeeds.

## Tests added (`ebl/tests/realia/test_realia_route.py`)

- `test_get_realia_with_slash_in_id` — slash `_id` returns 200 + correct `_id`
- `test_get_realia_with_slash_in_id_not_found` — multi-segment 404 preserved
- `test_realia_lemma_sink_rejects_non_get` — POST → 405 with `Allow`
- `test_realia_lemma_sink_allows_cors_preflight` — OPTIONS preflight → 200 with
  `Access-Control-Allow-Methods` + `Access-Control-Allow-Origin`
- Existing tests guard the regression surface (single-segment, `/realia/by-id`,
  `/realia` search, single-segment not-found, `by-id` lemma not shadowed).

## Gates

- `ruff format` — clean; `ruff check` + `flake8 --max-line-length=120` — clean
- `mypy --ignore-missing-imports` — no errors in changed files (pre-existing
  errors elsewhere are unrelated; project type gate is `pyre`)
- `pyre check` — No type errors found
- realia route tests: 14 passed, 100% coverage on both changed source files
- full suite: 3765 passed, 2 skipped, 1 xfailed
- file sizes within the 250-line gate (realia.py 49, bootstrap.py 21,
  test 183)
