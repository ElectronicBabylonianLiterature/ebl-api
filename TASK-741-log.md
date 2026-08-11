# TASK-741 Work Log

## Task

Review PR #741 (*Fix AfO Register texts-numbers match for references containing
spaces*). Fetch all reviews and comments from bots and humans, check failing
checks and qlty issues, and add a short friendly summary plus a detailed
`Details` subsection to the review document.

## Entries

### Start — create tracking artefacts

The previous task's `TASK-741-*.md` files were deleted in commit `9d269b6c`
("Remove PR #741 task tracking and review docs before merge"). Per the task
tracking hard gate, removal settles the previous task only, so this task starts
by creating them again. Created `TASK-741-todo.md` and this log before doing any
review work.

### PR identification

`gh pr view` — PR #741, open, author `khoidt`, head
`fix-afo-register-texts-numbers-split`, base `master`, mergeable,
`reviewDecision: CHANGES_REQUESTED`, `mergeStateStatus: BLOCKED`.

### Fetching all PR feedback

- `gh api repos/.../pulls/741/reviews --paginate` — 2 reviews:
  `sourcery-ai[bot]` (`COMMENTED`, id `4734372789`) and `Fabdulla1`
  (`CHANGES_REQUESTED`, id `4753124320`, 3 points).
- `gh api repos/.../pulls/741/comments --paginate` — **0** inline diff comments.
- `gh api repos/.../issues/741/comments --paginate` — 1 comment, the Sourcery
  Reviewer's Guide (id `5021576863`).
- GraphQL `reviewThreads` — **0** threads, so no resolved/unresolved split to
  report; all feedback is top-level review bodies.
- Merged-in branches: the branch has two `origin/master` merges (`7a2d3285`,
  `7fc44160`). `git log <merge-base>..origin/master -- ebl/afo_register/` is
  empty, so no merged-in PR (#740, #747, #748, #749) touches this code and none
  of their feedback applies. Recorded that reasoning in the review rather than
  silently skipping the gate.

### Checks and qlty

`gh pr checks 741`: CodeQL pass, Analyze (python) pass, GitGuardian pass,
`Test Python pypy-3.11` pass, `Test Python 3.11/3.12` still in progress, Sourcery
review `skipping`, `qlty check` **pass — no blocking issues**. Two duplicate
workflow runs (`31512085808`, `31512087915`) are queued against the same head,
which is why each test job appears twice. **No failing checks.**

Attempted to corroborate qlty locally: the `qlty` binary exists at
`~/.qlty/bin/qlty` but `qlty check` exits with "Qlty must be set up in this
repository. Try: qlty init" — the repo has `.qlty/` (caches + `configs/`) but no
tracked `qlty.toml`. Did **not** run `qlty init`, since that writes config the
user did not ask for (the rule against modifying lint/format configuration).
Reported the CI result and this limitation explicitly in the review.

### Verifying each piece of feedback against the current tree

All three of Fabdulla1's points and Sourcery's point are addressed:

1. Bounds — `MAX_TEXTS_AND_NUMBERS_QUERIES=1000`, `MAX_QUERY_LENGTH=500`,
   `MAX_QUERY_TOKENS=24` (route) and `MAX_CANDIDATES=10000` (repository).
2. Ambiguous-match test — `test_search_by_texts_and_numbers_returns_all_ambiguous_matches`.
3. Dedup — `seen: Set[Tuple[str, str]]` in `_build_candidate_query`.
4. Sourcery's file-removal request — old `TASK-afo-register-link-*.md` removed
   in `388a96aa`.

### Gate runs

| Gate | Result |
| ---- | ------ |
| `task format` | 802 files already formatted |
| `task lint` (ruff) | All checks passed |
| `task type` (pyre) | No type errors found |
| `task type-pyright` | 0 errors, 0 warnings, 0 informations |
| `mypy` on the 5 changed files | Success: no issues found in 5 source files |
| `flake8 --max-line-length=120` | exit 0, no output |
| `pytest` + `--cov` on `afo_register` | 44 passed, **100%** coverage |
| 250-line file limit | 160, 80, 72, 205, 188 — all pass |
| `task lint-md` | 0 errors across 7 files |
| Full suite (`pytest -q`) | **4319 passed, 2 skipped, 1 xfailed, 0 failed** |

### Runtime verification (hard gate)

Tests alone are not evidence, so I ran the modified service. Wrote
`serve_afo.py` in the scratchpad: wires `MongoAfoRegisterRepository` and the
three real AfO routes into a Falcon app with the project error handler, seeds a
scratch mongo database with the `OrNS`/`59, 17` shape, a `59, 170` decoy,
`*Bit meseri*`/`59, 17`, and the ambiguous `A`/`B C` + `A B`/`C` pair, then
serves it with waitress on `127.0.0.1:8123`.

Pointed it at `mongodb://127.0.0.1:27017` explicitly and launched with
`env -u MONGODB_URI`, because `.env` in this repo points at the **production**
cluster.

Exercised `POST /afo-register/texts-numbers` with 16 bodies. All results are in
the review's `Reproduction Steps`. Key confirmations: the reported bug case now
returns the record, the `59, 170` decoy stays out, ambiguity returns both
records, duplicates are deduplicated, and all five limits return `422`.

Also ran `explain` on a two-branch candidate `$or`: `SUBPLAN → FETCH → OR` over
two `IXSCAN` stages (`text_1_textNumber_1` and `text_1`), no `COLLSCAN` — which
substantiates the PR description's claim that the rewrite keeps the indexed
lookup.

### Errors made and recovered

1. **First service launch failed** — `ModuleNotFoundError: No module named
   'ebl'`, because the script runs from the scratchpad directory. Recovered by
   setting `PYTHONPATH=/workspaces/ebl-api`.
2. **First probe script printed tracebacks** — I assumed the response records
   carried `fragmentNumbers`; the dumped schema uses different keys. Recovered by
   re-probing on `text`/`textNumber`. No conclusions were drawn from the broken
   run.
3. **First candidate-explosion probe was invalid** — I sent 25-token queries, so
   the request was rejected by `MAX_QUERY_TOKENS` before ever reaching
   `MAX_CANDIDATES`, which would have wrongly "confirmed" the wrong limit.
   Recovered by rebuilding the probe with exactly 24 tokens × 435 queries, and
   added the 434-query control case that returns `200` — that pair is what
   actually establishes finding L1.
4. **`pkill -f serve_afo.py` killed its own shell** (exit 144). Harmless; the
   server did stop. Re-ran the follow-up command separately.
5. **First markdownlint pass on the review had 7 errors** — MD036 (bold used as
   a heading) on the finding titles and MD024 (duplicate `Findings` heading).
   Recovered by promoting the finding titles to `#####` headings and renaming the
   inner one to `Findings from this review`. Re-ran: 0 errors.

### Review document

Wrote `TASK-741-review.md`. Structure per the user's request: a short, friendly
`Review Summary` section first, with a `### Details` subsection carrying every
finding in full. The line-length limit is lifted **only** inside `Details` via an
inline `<!-- markdownlint-disable MD013 -->` comment, so the section can be
pasted into GitHub without hard wraps. I did **not** touch `.markdownlint.json`
or `.markdownlintignore` — there is no tracked markdownlint config in this repo,
and editing lint configuration is prohibited without an explicit request. The
required template sections (`Summary`, `Findings`, `Severity`,
`Reproduction Steps`, `Recommendation`) follow.

Findings raised: 3 low (L1 route/repository limit inconsistency, L2 `object`
annotation on `candidate_splits`, L3 task-file housekeeping), 2 informational
(I1 validation layering, I2 query-side-only whitespace normalization), 3 positive
confirmations (P1 index use, P2 no payload echoed in errors, P3 no behavioural
regression). No correctness defect found.

### Data hard gate check

Checked the diff against the mixed-type-array gate: `query_list` is
`Sequence[str]`, `candidate_splits` returns `List[Tuple[str, str]]`, and the
`$or` array holds only same-shaped `Dict[str, str]` entries. No mixed id list, no
type discriminated by probing an optional field, and the wire shape matches the
domain shape. Passes.

### Not committed

No `git commit`, `push`, or any history-changing command was run. The working
tree carries only the three untracked `TASK-741-*.md` files; no source file was
modified by this review.
