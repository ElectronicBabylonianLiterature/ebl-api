# TASK-740-review2 — Work Log

Task: review PR #740 (`add-realia-annotation-api` -> `master`).
Log records what was actually done, including every error and its recovery.

## Entries

### 1. Read the instructions

Read `.github/instructions/copilot.instructions.md` in full before acting, at
the user's explicit request. Confirmed the binding gates for a review task:
existing-GitHub-feedback gate, data hard gate, 250-line gate, three type
checkers, runtime verification, task tracking, review-file template, and the
never-commit gate.

### 2. Identified the PR

- Branch: `add-realia-annotation-api`
- Repo: `ElectronicBabylonianLiterature/ebl-api`
- PR: #740 — "Realia annotation API: resolve realiaInfo on every
  fragment-returning route", OPEN, not draft, base `master`
- Working tree clean at start.
- Diff vs merge-base: 98 files, +5499 / -1987.

### 3. Task artefacts created

Created `TASK-740-review2-todo.md` and `TASK-740-review2-log.md` **before**
starting review work. A previous review task left `TASK-740-review*.md` on the
branch; per the task-tracking gate those do not carry forward, so this task uses
its own `review2` files.

Noted for step 12: nine `TASK-740-*.md` files are tracked and committed on the
branch and must be removed before merge.

### 4. GitHub feedback gate (mandatory before finalizing)

Fetched all three feedback surfaces on PR #740:

- `pulls/740/reviews` — 3 reviews:
  - sourcery-ai[bot] (COMMENTED): declined, diff exceeds the 150000-character
    review limit. No findings.
  - **Fabdulla1 (CHANGES_REQUESTED)** — two substantive concerns:
    1. In `web/dtos.py` the mutation is persisted before
       `FragmentDtoFactory.create()` performs the realia lookup; a lookup
       failure returns 500 after the write already committed, leaving the
       request ambiguous and encouraging an unsafe retry.
    2. Tests cover *missing* realia records but not an *infrastructure*
       failure from `find_by_realia_ids` (Mongo timeout / connection error).
  - qltysh[bot] (COMMENTED): empty body, findings delivered inline.
- `pulls/740/comments` — 12 inline comments, all from qltysh[bot]:
  - 10 x `qlty:function-parameters` (test helpers/tests with 6-9 params)
  - 2 x `qlty:similar-code` at `token_schemas_words.py:72` and `:90`
    (20 duplicated lines, mass 145)
- `issues/740/comments` — none.

`reviewDecision: CHANGES_REQUESTED`, `mergeStateStatus: BLOCKED`.

Merged-in branches: the only merge on this branch is `0b62f9fc` from
`origin/master`, not a feature PR, so there is no additional PR whose feedback
must be pulled in.

### 5. CI status — RED at the reviewed SHA

`gh pr view` shows **Test Python 3.11 FAILURE** at `84acd6f7`, which is exactly
the local HEAD. Pulled the failing job log (run 30028549040). The failure is
**pyre**, the checker CI enforces:

```text
ebl/transliteration/application/token_schemas_words.py:52:0
Uninitialized attribute [13]: Attribute `word_class` is declared in class
`AbstractWordSchema` to have type `Type[Word]` but is never initialized.
```

Python 3.12 and pypy-3.11 jobs were CANCELLED as a consequence, so the suite
never ran to completion on this SHA in CI.

### 6. Error made and recovered: could not run pyre locally

Attempted `task type` — pyre aborted with
`Worker.Worker_exited_abnormally` / `End_of_file` internal exceptions. Retried
with `--number-of-workers 2`, then `--number-of-workers 1
--shared-memory-heap-size 2147483648`; both still aborted.

Cause: this container has **2 CPUs and ~2 GB free RAM**, while pyre initializes
an 8 GB shared-memory heap. This is an environment limit, not evidence about
the code. Recorded honestly rather than reported as a pass: the authoritative
pyre result is CI's, on the exact SHA under review, and it is one error.

A first pytest run and a pyre run were also lost when the previous session's
background tasks were torn down; restarted pytest writing to a persistent log
outside the task directory so the result survives.

### 7. 250-line gate — PASS

Checked every changed `*.py` file (source and test) against the 250-line hard
gate. **Zero files exceed it.** Longest changed files:

| Lines | File |
| ----- | ---- |
| 239 | `ebl/tests/fragmentarium/test_fragments_route.py` |
| 239 | `ebl/fragmentarium/domain/fragment.py` |
| 231 | `ebl/tests/fragmentarium/test_realia_info_route.py` |
| 214 | `ebl/transliteration/domain/word_tokens.py` |
| 214 | `ebl/tests/fragmentarium/test_fragment_repository_updates.py` |

### 8. Data hard gate audit — PASS

- `Fragment.named_entities: Sequence[NamedEntity]` and
  `Fragment.realia: Sequence[RealiaEntity]` are structurally separate
  (`domain/fragment.py:107-110`).
- `AbstractWord.named_entities` and `AbstractWord.realia` are separate id
  arrays (`word_tokens.py:29-30`); wire keys `namedEntities` / `realia` are
  separate too (`token_schemas_words.py:38-49`). Domain split == wire split.
- No discriminator, no probing for an optional field, no `OneOfSchema`.
- marshmallow 3.26.2 defaults to `unknown=RAISE`, so putting `realiaId` in a
  `namedEntities` element is a 422 for free, as the gate describes.
- **Shared id space is still enforced across the union**:
  `NamedEntityResource._validate_unique_ids` counts ids over
  `chain(entity_spans, realia_spans)` and rejects collisions, and
  `_word_ids_by_annotation` resolves both through one lookup. This is exactly
  what the gate mandates ("separation is structural, not relational").

Verified `realia` was inserted in the correct positional slot in every attrs
constructor call — `Word.of`, `GreekWord.of`, `AkkadianWord.of` all pass
`named_entities, realia` immediately before the trailing
`language`/`modifier` argument, matching the `AbstractWord` attribute order.
`LoneDeterminative` inherits `Word.of`, so it is covered.

### 9. Gate results

- `task format` — PASS (775 files already formatted)
- `task lint` — PASS
- `task type` (pyre) — FAIL per CI; not runnable locally (see entry 6)
- `task type-pyright` — FAIL, 41 errors on 2 changed files
- `task test` — PASS, 3938 passed / 2 skipped / 1 xfailed / 0 failures
- Coverage on 38 changed source modules — PASS, 100% (2033 stmts, 0 missed)
- flake8 `--max-line-length=120` — PASS, 0 errors
- mypy on changed source — FAIL, 5 errors in touched files
- `task lint-md` — PASS, 0 errors
- 250-line limit — PASS

### 10. Error made and recovered: stray worktree inside the repo

To separate pre-existing mypy errors from new ones I created a git worktree at
the merge-base. I passed a **relative** path to `git -C /workspaces/ebl-api
worktree add`, which resolved against the repo root and created
`/workspaces/ebl-api/basecheck` — polluting the user's working tree. Spotted it
immediately when markdownlint's file count jumped from 15 to 19.

Recovered with `git worktree remove --force basecheck`, confirmed the
directory was gone and `git status` was clean again, then recreated the
worktree under the scratchpad with an absolute path. No commit was made at any
point, so nothing leaked into history.

### 11. Error made and recovered: wrong `--cov` argument form

First coverage run passed file paths (`--cov=ebl/.../realia_info.py`).
Coverage emitted `Module ... was never imported (module-not-imported)` for
every one and produced no report. Re-ran with dotted module names
(`--cov=ebl.fragmentarium.application.realia_info`), which produced the real
table: 100% on every changed module.

### 12. Runtime verification

Started the modified service against the **local** mongod on a scratch
database `ebl_review_740`. The configured `MONGODB_URI` points at a remote
production cluster (`badwcai-ebl0{1,2,3}.srv.mwn.de`) and was deliberately
overridden — I did not connect to it. Only the auth backend was swapped
(`attr.evolve(context, auth_backend=NoneAuthBackend(...))`) so write routes
were reachable without an Auth0 token; routes, DTO factory and repositories
were the real modified code.

Eight requests exercised: fragment GET, named-entities GET, named-entities
POST, three validation cases (unknown field / unknown realiaId / duplicate id
across the union), and two non-annotation write routes (genres, edition) which
are the actual defect. All behaved as expected; details in the review file.

Cleanup afterwards: server stopped, port 8099 free, scratch database dropped,
worktree removed, `git status` shows only this task's three new `.md` files.

### 13. Review file written

`TASK-740-review2.md` created with the required template sections — Summary,
Findings, Severity, Reproduction Steps, Recommendation — plus a gates table.
Nine findings; two blockers. `task lint-md` passes across all 16 markdown
files after fixing MD012, MD013, MD029 and MD036 violations in my own files.

### 14. Nothing committed

No `git commit`, `push`, `merge`, `rebase`, `reset` or `gh pr` command was
run. The user did not ask for one. The three review artefacts are untracked in
the working tree.
