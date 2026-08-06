# TASK-743-merge — Work Log

## Task

Merge `master` into branch `fix-type-checker-blind-spots` (PR #743,
"Make the ATF parser visible to the type checkers") and resolve conflicts.

## Pre-merge state

- Current branch: `fix-type-checker-blind-spots`, up to date with its remote.
- Branch commits ahead of local `master`: 1 — `e3150b3d Make the ATF parser
  visible to the type checkers`.
- Local `master` was 2 commits behind `origin/master`.
- After `git fetch origin --prune`, `origin/master` head is
  `32f6ddae Add Sum as genre (#748)`.
- Commits to be merged in (`HEAD..origin/master`, 6 total):
  - `32f6ddae Add Sum as genre (#748)`
  - `3fd44b2f Collate uppercase forms and stop matching a literal pipe (#747)`
  - `a238304d Realia annotation API: resolve realiaInfo on every
    fragment-returning route (#740)`
  - `d98274ef dev: added alias (#727)`
  - `9bc96c49 Add various museums in Turkey (#745)`
  - `9792e24b Add HARVEY_CUSHING_WHITNEY_MEDICAL_LIBRARY (#744)`
- Dirty worktree at start: `docs/ebl-atf.md` (uncommitted, pre-existing, not
  authored as part of this task) and untracked `.qlty/`.
- `master` does not touch `docs/ebl-atf.md` in the range being merged, so the
  dirty file does not block the merge.

## Notes

- `.github/instructions/copilot.instructions.md` differs between `HEAD` and
  `origin/master` — re-read it after the merge in case the gates changed.

## Progress

- Read `.github/instructions/copilot.instructions.md` and confirmed gates.
- Created this log and `TASK-743-merge-todo.md`.

### Blocker encountered and recovered

`git checkout master` aborted: the uncommitted `docs/ebl-atf.md` edit would
have been overwritten, because `32f6ddae (#748)` also modifies that file.

- Recovery 1: updated the local `master` ref without a checkout using
  `git fetch origin master:master` (fast-forward `a238304d..32f6ddae`).
- Recovery 2: the same dirty file would have blocked the merge, so it was
  stashed non-destructively as
  `stash@{0} "TASK-743-merge: pre-existing uncommitted docs/ebl-atf.md edit"`.
  Nothing was discarded; it is restorable with `git stash pop`.

### Merge

`git merge master --no-commit --no-ff` → 2 conflicts:

1. `ebl/transliteration/domain/text_line.py`
2. `ebl/tests/factories/archaeology.py`

Auto-merged without conflict: `docs/ebl-atf.md`,
`ebl/tests/fragmentarium/test_fragment_repository_updates.py`,
`ebl/transliteration/domain/word_tokens.py`.

### Conflict 1 — `text_line.py` (formatting only)

Both sides import the same two names from
`ebl.fragmentarium.domain.token_annotation`; only the wrapping differed. The
single-line form is 84 characters, inside the formatter's limit, so master's
form is what the formatter produces. **Resolved to master's single line.**
No semantic content on either side was lost.

### Conflict 2 — `archaeology.py` (substantive; both sides refactored it)

Both branches independently attacked the *same* problem — `factory_boy` names
being invisible to the type checkers when reached through the `factory`
namespace — and solved it differently.

- Ours (`e3150b3d`): kept class-based factories, imported `Factory` from
  `factory.base` and `Maybe`/`List`/… from `factory.declarations`.
- Master (`a238304d`, #740): converted to `make_factory(...)`, replaced
  `Maybe` with `LazyAttribute(_random_day)` over `factory.random.randgen`,
  replaced the `TupleFactory` import with the `TUPLE_FACTORY` string path,
  and changed the excavation-number prefix from `"X"` to `"EX"`.

**Resolved to master's version wholesale** (`git checkout --theirs`). Rationale:
master already achieves our branch's goal for this file and goes further, and
master carries behavioural changes (`"EX"` prefix, the `LazyAttribute` day
rule) that must not be reverted by the merge. Our side held no content that
master's version does not already supersede — its only changes to this file
were the import-style rewrite. Taking ours would have silently reverted #740.

### Verification of the merged tree

- The branch's rename of the grammar directory
  `atf_parsers/lark_parser/*.lark` → `atf_parsers/atf_grammar/*.lark`
  survived: `atf_grammar/` holds all 16 `.lark` files and `lark_parser/` is
  gone.
- No conflict markers remain anywhere in the tree.
- Master rewrote `.github/instructions/copilot.instructions.md`
  substantially; it was re-read after the merge. Pre-commit gates went from
  5 to 8 (adding `task lint`, `task type`/pyre, `task type-pyright`), and
  `git merge` is now itself an explicit-permission command.

## Gate results (merge staged, NOT committed)

1. `task format` — **PASS**. 801 files already formatted, exit 0, no
   unstaged changes left behind.
2. `task lint` (ruff) — **PASS**. All checks passed.
3. `task type` (pyre, the CI-enforced gate) — **PASS**. No type errors found.
4. `task type-pyright` — **PASS**. 0 errors, 0 warnings, 0 informations.
5. `task test` — **PASS**. 4245 passed, 2 skipped, 1 xfailed, **0 failures**
   in 322s, exit 0.
6. Coverage on changed files — **PASS**. 100%, 0 lines missed. Detail below.
7. `flake8 --max-line-length=120` — 1 error, pre-existing on master.
8. `mypy --ignore-missing-imports` — 42 errors, all pre-existing on master.

Additional gates:

- `task lint-md` — **PASS**. 6 files, 0 errors.
- 250-line hard gate — no new violation; 3 pre-existing, detailed below.

### Pre-existing debt inherited from master (NOT introduced by this merge)

Each item below was verified byte-identical to `master`, so the merge neither
creates nor worsens it. None of it is in a file this branch touched. It was
left untouched deliberately: editing master's files inside a merge commit
would put unrelated changes in the merge and is outside the requested scope.

- **flake8**: `ebl/fragmentarium/domain/museum.py:130` E501 (167 > 120) — a
  long URL. Confirmed to fail identically on `master` in isolation.
- **mypy**: 42 errors across 31 files. Every one of the 31 files was checked
  with `git diff --quiet master -- <file>` and is identical to master. **Zero
  mypy errors occur in any of the 11 `.py` files this branch touched**, and
  neither conflict-resolved file has any error.
- **250-line gate**: `lookup_reservations.py` (253),
  `museum.py` (412), `test_bibliography_lookup_reservations.py` (282) — all
  identical to master. The two conflict-resolved files are well under the
  limit: `archaeology.py` 86, `text_line.py` 186.

### Error made during verification, and its recovery

The first coverage run was invoked as `--cov=<path/to/file.py>`. `--cov`
takes an **importable module name**, not a filesystem path, so coverage
reported "Module … was never imported" for all 11 targets, collected no data,
and emitted "No data to report" — while pytest itself still exited 0. Exit 0
therefore did **not** mean the gate had passed; the run proved nothing.

Recovered by converting each path to a dotted module name (strip `.py`,
`/` → `.`) and re-running. Recorded here because a green exit code on a
misconfigured coverage run is exactly the kind of false pass the gates exist
to catch.

### Coverage result (gate 6)

Full suite run under coverage scoped to the modules this branch touches.
**521 statements, 0 missed, 100%.**

| Module | Stmts | Miss | Cover |
| --- | --- | --- | --- |
| `atf_importer/domain/legacy_atf_converter.py` | 139 | 0 | 100% |
| `atf_importer/domain/legacy_atf_line_validator.py` | 28 | 0 | 100% |
| `transliteration/.../atf_parsers/lark_parser.py` | 141 | 0 | 100% |
| `transliteration/.../atf_parsers/lark_parser_errors.py` | 27 | 0 | 100% |
| `transliteration/domain/text_line.py` | 79 | 0 | 100% |
| `transliteration/domain/word_tokens.py` | 107 | 0 | 100% |
| **TOTAL** | **521** | **0** | **100%** |

The remaining branch-touched files are themselves test modules
(`ebl/tests/...`, including the conflict-resolved
`ebl/tests/factories/archaeology.py`) and are omitted from the coverage
report by the project's coverage configuration, not by this run's scoping.
Both conflict-resolved files are exercised by the passing suite:
`text_line.py` reports 100% above, and `archaeology.py` is the factory behind
the archaeology/findspot tests.

### Runtime verification (HARD GATE: run the service, not just tests)

The merged tree was booted as a real Falcon application and exercised over
HTTP, using `falcon.testing.TestClient` against an app built by the actual
`create_context()` / `create_app()` code path.

Safety measures taken, given that `.env`'s `MONGODB_URI` points at the live
production cluster:

- `.env` was **never** sourced. `MONGODB_URI` was set explicitly to
  `mongodb://127.0.0.1:27017` (a local `mongod`), into a throwaway database
  `ebl_merge_smoke`, which was dropped afterwards.
- `get_app()` was deliberately **not** used, because it calls
  `sentry_sdk.init(dsn=os.environ["SENTRY_DSN"])` and would have reported to
  the production Sentry project. `create_app()` was called directly instead.
- `AUTH0_PEM` was a freshly generated throwaway RSA key, so no real
  credential was read.

Results:

- App booted; all route modules registered without error.
- `GET /signs/transliteration/ku-nu-szi` → **200 OK**. This is the ATF parser
  route, the branch's own runtime surface.
- The relocated grammar directory resolves at runtime:
  `parse_atf_lark("1. ku-nu-szi")` loaded the `.lark` files from
  `atf_parsers/atf_grammar/` and returned `1. ku-nu-szi`. This is the
  strongest evidence that the branch's directory rename survived the merge
  intact — a stale path would have raised at import time.
- Master's #748 change is present and live: `Genre.SUMERIAN.value == "Sum"`.
