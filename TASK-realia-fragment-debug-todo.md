# TASK-realia-fragment-debug — TODO

## Step 1 — Reproduce server-side

- [x] Check whether API is listening on 8001 — it is **not** (nothing bound)
- [x] Drive `GET /fragments/VAT.5047` against the real DB via the app itself
- [x] Drive `GET /fragments/VAT.5047/named-entities`
- [x] Capture status + body — **200 OK on both, no traceback**

## Step 2 — Prime suspect: `resolve_realia_info`

- [x] Verify `_id` type of realia docs VAT.5047 references — both `str`, not `ObjectId`
- [x] Verify DB has the realia — both present (`Assur`, `Babylon`)
- [x] Verify `projection=` reaches pymongo intact — yes
- [x] Exercise `find_by_realia_ids` directly against real data — clean
- [x] Compare a realia-free fragment — covered (`realiaInfo == []`)
- [x] **Hypothesis dead** — route returns 200 with correct `realiaInfo`

## Step 3 — Divergence from master

- [x] Confirm 8 ahead / 4 behind, no open PR — confirmed
- [x] Run full suite as-is — green before the change (862 fragmentarium)
- [ ] Merge current `master` in — **NOT DONE**, needs user authorisation (`git merge`)

## Step 4 — Transport / CORS / reachability

- [x] Establish curl-equivalent succeeds while browser fails → transport fault
- [x] `task serve` binds 8001; Dockerfile / compose bind 8000
- [ ] **User to confirm**: how the API was started, and whether 8001 is published
      to the host

## Step 5 — POST `realiaInfo` bug (fixed)

- [x] Confirm `named_entities.py::on_post` omitted `realia_info`
- [x] Establish real wire behaviour: key **absent**, not `null` (`filter_none`)
- [x] Find all `create_response_dto` callers — 11 more with the same omission
- [x] Get user decision on scope + conflicting test
- [x] Make `realia_info` required; add `FragmentDtoFactory`
- [x] Convert all 12 call sites; wire factory in `bootstrap.py`
- [x] Update 18 test call sites across 13 files
- [x] Update the conflicting assertion (approved)
- [x] Add route tests pinning `realiaInfo` in the POST response

## Contract verification

- [x] `namedEntities: [{id, type}]` — verified live + pinned
- [x] `realia: [{id, realiaId}]` — verified live + pinned
- [x] `realiaInfo: [{realiaId, lemma, type: [str]}]` — verified live + pinned
- [x] per-word `namedEntities: [str]` / `realia: [str]` — verified live
- [x] `/named-entities` object with `span: [wordIds]` — verified live

## Gates

- [x] `task format` — clean (746 files)
- [x] `task test` / full suite — 3920 passed, 2 skipped, 1 xfailed, 0 failures
- [x] Coverage 100% on changed modules (`colophons.py` gap found and filled)
- [x] `flake8 --max-line-length=120` — 0 errors
- [x] `mypy --ignore-missing-imports` — 0 errors in changed files
- [ ] `task lint-md` — pending (this task's `.md` files)

## Open items for the user

- [ ] Decide on `test_transliterations_route.py` (396 lines, over the 250 gate;
      was already 391 on base — this change did not push it past)
- [ ] Pre-existing: `update_colophon` writes no changelog entry (reported only)
- [ ] Pre-existing: `edition.py:57` uncovered (untouched line)
- [ ] Config smell: `.env` sets `EBL_AI_API=http://localhost:8001`, the same port
      `task serve` binds
- [ ] **Remove `TASK-realia-fragment-debug-*.md` before the PR is merged**

## Commit status

Working tree holds verified changes. **Nothing committed or pushed** — awaiting
explicit instruction.
