# TASK-realia-fragment-debug — Work Log

## Headline

`GET /fragments/VAT.5047` returns **200 OK** with a complete, correct payload,
against the real `ebldev` database, on `add-realia-annotation-api`. There is no
500 and no traceback. The reported symptom is **not** an application-code fault.

## Environment findings

- Nothing is listening on `localhost:8001` in this workspace; the API process is
  not running here. Mongo (`mongod`) is up on `27017`.
- `Taskfile.dist.yml:51` → `waitress-serve --port=8001` — so 8001 is the correct
  dev port for `task serve`. `Dockerfile` and `docker-compose-api-only.yml` use
  **8000**. Port depends on how the API was started.
- `.env` sets `EBL_AI_API=http://localhost:8001` — the AI API is pointed at the
  same port the eBL API itself serves on under `task serve`. Config smell,
  unrelated to this bug (affects only ebl-ai calls).

## Step 1 — Server-side reproduction

Driven through the app's own stack (`create_context()` + `create_app()` +
`falcon.testing.TestClient`) against the real `MONGODB_URI` / `ebldev`, so the
route, middleware, repositories and schemas are all real. Auth resolves to
`Guest` via `NoneAuthBackend`, which is the same fallback production uses.

`GET /fragments/VAT.5047` → **200 OK**

```json
"namedEntities": [{"id": "Entity-1", "type": "GEOGRAPHICAL_NAME"}]
"realia": [{"id": "Realia-1", "realiaId": "realia_001514"},
           {"id": "Realia-2", "realiaId": "realia_001302"}]
"realiaInfo": [{"realiaId": "realia_001302", "lemma": "Assur", "type": []},
               {"realiaId": "realia_001514", "lemma": "Babylon",
                "type": ["Geographical names"]}]
```

Per-word tokens carry the id arrays:

```text
TOKEN DIR      | namedEntities=[]           | realia=['Realia-2']
TOKEN KALAG-ma | namedEntities=['Entity-1'] | realia=['Realia-1']
```

`GET /fragments/VAT.5047/named-entities` → **200 OK**

```json
{"namedEntities": [{"id": "Entity-1", "type": "GEOGRAPHICAL_NAME",
                    "span": ["Word-128"]}],
 "realia": [{"id": "Realia-1", "realiaId": "realia_001514", "span": ["Word-128"]},
            {"id": "Realia-2", "realiaId": "realia_001302", "span": ["Word-127"]}]}
```

Every clause of the stated frontend contract is satisfied on the wire.

## Step 2 — Prime suspect eliminated

The `_id`-is-an-`ObjectId` hypothesis is dead on this data:

```text
{'_id': 'Assur',   'realiaId': 'realia_001302',
 'type': []}                       | _id type: str
{'_id': 'Babylon', 'realiaId': 'realia_001514',
 'type': ['Geographical names']}   | _id type: str
```

Both realia VAT.5047 references exist and both `_id`s are `str`, so
`RealiaEntrySchema(required=True, data_key="_id")` loads cleanly. Calling
`MongoRealiaRepository.find_by_realia_ids(['realia_001302','realia_001514'])`
directly against the real DB returns both entries without error.

The narrow `projection={"realiaId": True, "type": True}` is safe: every other
field on `RealiaEntrySchema` declares a `load_default`, and `_id` is returned by
Mongo by default. `find_many` passes `**kwargs` through to pymongo unmodified.

Realia-free fragments are already covered by
`test_realia_info_empty_without_annotations` (`realiaInfo == []`), and
`resolve_realia_info` early-returns before touching the repository.

## Step 3 — Divergence

`git rev-list --left-right --count origin/master...HEAD` → **4 behind, 8 ahead**.
No open PR. Full fragmentarium suite run in progress.

## Step 4 — Where the fault actually is

Since the route returns 200 server-side, "Failed to load response data" in
DevTools is a transport/reachability fault, per the prompt's own triage. Nothing
was bound to 8001 in this workspace. The frontend devcontainer forwards only port
3000, and the browser resolves `localhost:8001` on the host, so the API must be
both running and published to the host for the page to load. A CORS conclusion is
not supported: with a 200 and no 5xx, there are no missing CORS headers to
explain, and `create_api` sets `cors_enable=True`.

## Step 5 — Real bug confirmed (with a correction to the prompt)

`ebl/fragmentarium/web/named_entities.py:115` calls
`create_response_dto(updated_fragment, user, has_photo)` without `realia_info`.

Correction: the response does **not** carry `realiaInfo: null`.
`FragmentSchema.filter_none` is a `@post_dump` that runs
`pydash.omit_by(data, pydash.is_none)`, so the `None` is stripped and the key is
**absent** entirely. The user-visible consequence is identical (the frontend
treats it as optional and degrades the label to the raw `realia_000846` id), but
the wire shape differs from the prompt's description.

### Broader than reported

`create_response_dto` has 12 call sites. **Only** `FragmentsResource.on_get`
passes `realia_info`. The other 11 all omit it:

- `named_entities.py:115` (the reported one)
- `fragments.py:171` (`FragmentAuthorizedScopesResource.on_post`)
- `references.py:33`, `fragment_date.py:25`, `fragment_date.py:43`
- `lemmatizations.py:38`, `fragment_genre.py:24`, `archaeology.py:46`
- `lemma_annotation.py:48`, `colophons.py:27`, `edition.py:70`
- `fragment_script.py:25`

Every one returns a fragment DTO the frontend feeds back into its state, so realia
labels degrade after *any* of these edits, not only after saving annotations.

Root design defect: `realia_info` is an **optional parameter defaulting to
`None`** on a shared DTO builder. Forgetting it is silent — no type error, no
test failure, and `filter_none` erases the evidence.

### Conflicting existing test

`ebl/tests/fragmentarium/test_realia_info_route.py::test_write_neither_requires_nor_stores_realia_info`
currently asserts:

```python
assert "realiaInfo" not in post_result.json
```

This pins the buggy behaviour and **will fail** once the POST resolves
`realiaInfo`. It is not a useless test — its intent is that a client-supplied
`realiaInfo` (`lemma: "WRONG"`) is neither required nor persisted. That intent is
better served by asserting the server-resolved value is returned instead of the
client's. Per the repo test gate, proposing this change and awaiting explicit
approval before touching it.

## Fix applied (user approved: structural, all routes)

`realia_info` is now a **required** parameter of `create_response_dto`, and a new
`FragmentDtoFactory` in `ebl/fragmentarium/web/dtos.py` owns resolution:

```python
class FragmentDtoFactory:
    def __init__(self, realia_repository: RealiaRepository) -> None:
        self._realia_repository = realia_repository

    def create(self, fragment: Fragment, user: User, has_photo: bool) -> dict:
        return create_response_dto(
            fragment, user, has_photo,
            resolve_realia_info(fragment, self._realia_repository),
        )
```

Deviation from the previewed design, flagged for review: rather than repeating
`resolve_realia_info(fragment, self._realia_repository)` at 12 call sites, the
resolution lives in one place and each resource is injected with the factory.
The type-checker gate the user asked for is preserved — `realia_info` has no
default, so no call site can silently omit it — but the duplication is not.

Every fragment-returning resource now calls
`self._dto_factory.create(fragment, user, has_photo)`:
`fragments.py` (both `FragmentsResource` and `FragmentAuthorizedScopesResource`),
`named_entities.py`, `references.py`, `fragment_date.py` (×2),
`lemmatizations.py`, `fragment_genre.py`, `fragment_script.py`, `colophons.py`,
`archaeology.py`, `lemma_annotation.py`, `edition.py`. The factory is constructed
once in `bootstrap.py` and injected.

`NamedEntityResource` keeps its `realia_repository` — it still needs it for
`_validate_realia_ids`.

### Side effect: `realiaInfo` is now always present

The contextvar default changed from `None` to `()`, so `realiaInfo` is always a
list and `FragmentSchema.filter_none` no longer strips it. Previously the key was
absent on every write route. It is now `[]` for realia-free fragments and the
resolved list otherwise, on **every** fragment-returning route. This makes the
wire shape uniform and removes the frontend's silent degradation path.

No `try/except` was added anywhere: a realia resolution failure still propagates,
per the prompt's explicit instruction not to paper over a 500.

## Tests

- Updated the 18 `create_response_dto` call sites across 13 test files to pass
  the now-required `realia_info` (all use `[]`; those factories build realia-free
  fragments).
- `test_dtos.py::expected_dto` gained `"realiaInfo": []`, since the key is now
  always emitted.
- `test_references_route.py`: the GET assertion was
  `{**expected_json, "realiaInfo": []}` — a workaround for the POST lacking the
  key. Now simply `== expected_json`, because both routes agree.
- **Approved change** to `test_write_neither_requires_nor_stores_realia_info`:
  `assert "realiaInfo" not in post_result.json` →
  `assert post_result.json["realiaInfo"] == resolved`. Intent preserved and
  strengthened: it still proves the client's `lemma: "WRONG"` is neither required
  nor stored, and now also proves the server resolves the real lemma.
- **New** `test_write_response_realia_info_matches_get` — pins `realiaInfo` in the
  POST response and asserts POST and GET agree. This is the regression test for
  the reported defect.
- **New** `test_write_response_realia_info_empty_without_realia` — pins `[]` when
  the fragment has no realia.

## Gate results

- `task format` — clean (746 files; `references.py` reformatted by `ruff format`)
- `poetry run flake8 ebl/fragmentarium/web ... --max-line-length=120` — 0 errors
- `poetry run mypy ebl/fragmentarium/web --ignore-missing-imports` — 0 errors in
  changed files. 63 errors exist repo-wide in 37 **untouched** files
  (`ebl_ai_client.py`, `corpus/web/chapter_schemas.py`, etc.) — pre-existing, not
  introduced here, and outside the changed-module scope.
- `ebl/tests/fragmentarium` + `ebl/tests/realia` — **932 passed**, 0 failures
  (862 on the pre-change fragmentarium suite alone; branch was already green).
- **Full suite: 3920 passed, 2 skipped, 1 xfailed, 0 failures.** The branch was
  green before the change and is green after.
- Coverage on changed modules: `dtos.py`, `fragments.py`, `named_entities.py`,
  `bootstrap.py`, `archaeology.py`, `fragment_date.py`, `fragment_genre.py`,
  `fragment_script.py`, `lemma_annotation.py`, `lemmatizations.py`,
  `references.py` all **100%**.

### Coverage gate: one pre-existing gap found and filled

`colophons.py` came back at **82%** (lines 20-28 uncovered) — `ColophonResource.on_post`
had **no test whatsoever**; only `ColophonNamesResource` (the names GET) was
tested. Line 28 of that method is a line this change modified, and the gate
requires any touched line to reach 100% even if it was uncovered beforehand. Added
`test_update_colophon` to `test_colophon_route.py`, which pins the round-trip and
`realiaInfo == []`. `colophons.py` is now **100%**.

While writing it, an assertion modelled on the genre route
(`database["changelog"].find_one(...)`) failed: `FragmentUpdater.update_colophon`
calls `self._repository.update_field("colophon", updated_fragment)` directly and
**records no changelog entry**, unlike other update paths. The assertion was
removed rather than weakened, since it asserted behaviour that does not exist.
This looks like a genuine pre-existing inconsistency in the colophon write path
and is **reported, not fixed** — it is outside this task's scope.

## Pylance / pyright

The repo gate specifies `mypy`, which was clean. Pylance uses **pyright**, a
different checker, and `.vscode/settings.json` sets
`"python.analysis.typeCheckingMode": "standard"` — so the IDE surfaces errors the
gate never runs.

Measured properly by running pyright 1.1.411 over the same file set in a clean
`HEAD` worktree and diffing by (file, message):

- **Baseline (HEAD): 55 errors** on these files. **1333 errors repo-wide.**
- **Exactly one error was introduced by this change**, in `dtos.py`: adding the
  `-> dict` return annotation to `create_response_dto` made pyright object that
  `FragmentDtoSchema().dump(fragment)` returns a union, not a `dict`.
- Fixed with `return cast(dict, FragmentDtoSchema().dump(fragment))`, matching
  the existing convention at `named_entities.py:49`
  (`**cast(dict, entity_schema().dump(entity))`).
- After the fix: **0 new errors**, `dtos.py` at 0, file set down to **42**
  from a 55 baseline.

The `-> dict` annotation is a net win: it *removed* 13 pre-existing
`Expected mapping for dictionary unpack operator` errors across the test files,
because `**create_response_dto(...)` now type-checks.

### The other 42 were pre-existing — then fixed on request

They were on lines this change never authored (verified against the `HEAD`
worktree), but the user asked for them to be fixed. **All 27 changed files are now
at 0 pyright errors and 0 warnings**, down from 55 baseline.

Three idioms were used, each already established in this codebase — no config was
weakened, no rule disabled, no `type: ignore` added:

1. **`user: User = req.context["user"]`** replaces `req.context.user`.
   `falcon.util.structures.Context` implements `__getitem__` against `__dict__`
   ("object attributes are linked to dictionary items"), so the two are exactly
   equivalent at runtime. The subscript form is what pyright can see, and it is
   already the idiom at `named_entities.py:103`, which was the only route file at
   0 errors before this. The explicit `: User` annotation keeps the value typed
   rather than leaking `Any`.
2. **`cast(DomainType, Schema().load(...))`** — marshmallow's `load` is typed as
   a union, so every `update_*` call site reported an argument error. Matches
   `named_entities.py:64` (`cast(List, schema().load(...))`).
3. **`cast(dict, Schema().dump(...))`** — same for `dump`. Matches
   `named_entities.py:49`.

Test files: `simulate_post_with_retry` in `test_transliterations_route.py` was
declared with an implicit `result = None`, so pyright inferred `Result | None` and
every caller's `.status` / `.json` errored — 10 of the 16 test errors from one
root cause. Fixed by annotating `-> Result`, casting the untyped client call, and
asserting non-`None` before the (unreachable) trailing return.

Note this expands the diff into pre-existing debt that is unrelated to the realia
fix. If the PR should stay focused, these are cleanly separable — they touch only
type annotations and casts, never behaviour, and the suite is green either way.

## The gate gap — found and closed

This repo runs **three** type checkers, and they disagree:

| Checker | Where | Status |
| --- | --- | --- |
| pyre | `task type` (in `test-all`) | green, 0 errors |
| mypy | `copilot.instructions.md` step 5 | green on changed files |
| pyright | Pylance (`.vscode/settings.json`) | **in no gate at all** |

That is precisely how a Pylance error survived a "passing" gate: mypy and pyre
genuinely reported zero. The IDE ran a checker nothing enforced.

### Correction: the "1278 errors" figure was wrong

An earlier measurement claimed 1278 pyright errors across the branch diff, and
that number was used to argue a gate was infeasible. **It was an artifact of a
buggy command**: the `sed 's|[^ ]*|/workspaces/ebl-api/&|g'` used to absolutise
paths also matched the empty string at the trailing space, emitting a bare
`/workspaces/ebl-api/` — the repo root — as a 50th argument. Pyright then scanned
the entire repository (~1333 errors) instead of the 49 changed files.

The true count for the branch diff was **11 errors**, all in realia code added by
this branch:

- `ebl/realia/infrastructure/mongo_realia_repository.py` (5) — the same
  marshmallow `load` union, in `find_by_realia_ids`, `_load_entry`, `search`.
- `ebl/tests/fragmentarium/test_realia_info.py` (6) — `FakeRealiaRepository` did
  not implement `RealiaRepository`, and `SimpleNamespace` stood in for `Fragment`.

All 11 fixed. `FakeRealiaRepository` now genuinely subclasses the `RealiaRepository`
ABC and implements all five abstract methods, so the fake breaks if the interface
changes — a real improvement over duck typing, not a silencer.

### Gate added

`task type-pyright` runs pinned `pyright@1.1.411` over Python files changed vs
master, mirroring the existing `npx markdownlint-cli2@0.22.1` precedent in
`lint-md`. It is wired into **`test-all`**, because the branch diff is now at
**0 pyright errors** — so the gate is enforceable today, not aspirational.

Scope note: the gate is deliberately diff-scoped. The repo carries ~1333
pre-existing pyright errors overall; gating the whole tree would be red forever.
Diff-scoping enforces "new code stays clean" without demanding a repo-wide
cleanup first.

## The display bug — root cause found

The API **was** running on 8001 (pid 108367) and served `GET /fragments/VAT.5047`
with **200 OK**, a 127KB body, `Access-Control-Allow-Origin: *`, and an `OPTIONS`
preflight returning 200 with `Access-Control-Allow-Headers: authorization`. So
neither the application nor CORS was ever at fault.

The defect is a port mismatch in the devcontainer:

```jsonc
"forwardPorts": [8000],   // .devcontainer/devcontainer.json
```

```yaml
start:  poetry run waitress-serve --port=8001 ...   # Taskfile.dist.yml
```

`task start` — the documented dev command — binds **8001**, but the devcontainer
forwarded only **8000**. The browser resolves `localhost:8001` on the host, finds
nothing published there, and DevTools reports "Failed to load response data": no
response body, because there was no response.

Fixed by forwarding both ports and labelling them by how the API is started:

```jsonc
"forwardPorts": [8000, 8001],
"portsAttributes": {
  "8000": {"label": "API (Docker)",     "onAutoForward": "ignore"},
  "8001": {"label": "API (task start)", "onAutoForward": "ignore"}
}
```

8000 is kept because the `Dockerfile` (`EXPOSE 8000`) and
`docker-compose-api-only.yml` (`8000:8000`) use it. **This change requires a
devcontainer rebuild to take effect.** For an immediate unblock without
rebuilding, forward 8001 from the VS Code Ports panel.

### Remaining known gap (untouched line)

`edition.py:57` — `raise DataError(error) from error` inside
`_create_transliteration`, 97% coverage. This line's **content is untouched**;
it only shifted from line 55 to 57 because the change adds a `dto_factory`
parameter to the constructor above it. Renumbering is not modification, so the
coverage gate does not bite here. Flagged for visibility.

### File-length gate note

`ebl/tests/fragmentarium/test_transliterations_route.py` is **396 lines**, over
the 250 limit. It was **391 lines on the base branch** — already over before this
task; the change adds 5 lines (`[]` arguments). The gate triggers on "a change
[that] pushes a file past this limit", which this is not. 54 `.py` files in the
repo already exceed 250. Flagged for a user decision rather than silently split,
since splitting it is unrelated pre-existing debt and touches tests.

## Verification

Re-ran the live reproduction against the real `ebldev` DB after the refactor:
`GET /fragments/VAT.5047` still **200 OK** with `realiaInfo` correctly resolved
to Assur/Babylon, and `/named-entities` still 200 with spans intact.

## Status

Changes are complete and **uncommitted**. No commit or push has been made.
