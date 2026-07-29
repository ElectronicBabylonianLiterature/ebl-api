# TASK-740-qlty LOG — Address all qlty issues on PR #740

## Context

- Branch: `add-realia-annotation-api`, base `master` (`5967652a`), PR #740.
- Task: address all qlty issues.
- The preceding task (Fabdulla1's review) is complete and **uncommitted**. A
  commit request was interrupted before it was acted on, so no commit
  authorization is in force and nothing was committed.

## Work log

- Created `TASK-740-qlty-todo.md` and `TASK-740-qlty-log.md` before starting.
- Established the current qlty state from three independent sources.

### 1. PR check status

`gh pr checks 740`:

- `qlty check` — **pass**, "No blocking issues"
- `qlty coverage` — pass, 95.7% (+0.2% change)
- `qlty coverage diff` — pass, 100.0% (75% threshold)

### 2. Review-thread resolution state

`gh api graphql` over `pullRequest(740).reviewThreads` returned 14 threads, all
authored by `qltysh[bot]`, and **every one is `isResolved: true`**:

- 10 `function-parameters` threads (fragment updater / introduction / notes
  test files) — cleared by commit `080706a9`.
- 4 `similar-code` threads (`token_schemas_words.py`,
  `test_introduction_route.py`, `test_notes_route.py`) — cleared by commit
  `d6208283`.

The 2026-07-27T21:04 qlty review was posted between commits `080706a9`
(20:59) and `d6208283` (21:31); `d6208283` is what cleared its two findings.

### 3. Local qlty run + master baseline diff

`.qlty/` is gitignored, so `qlty init` was run locally to obtain a config
without adding any tracked file; the generated `.qlty/qlty.toml` was **deleted
afterwards**, leaving the repo exactly as found. A detached worktree of
`origin/master` was created under the scratchpad as a baseline and removed
after use.

`qlty smells --include-tests --upstream origin/master` on the branch, compared
against the same files on `origin/master`:

- Unchanged, pre-existing on master (**not** introduced here):
  `fragment_updater.py update_edition` (6 params);
  `test_dates_in_text_route.py` / `test_fragment_date_route.py` duplication
  (mass 121); `test_fragments_route.py test_get` (6);
  `test_transliterations_route.py
  test_update_transliteration_merge_lemmatization` (8).
- Findings the branch **removes** that master still has: 8
  `function-parameters` and 2 `similar-code` findings in
  `test_fragment_updater.py`, 3 in `test_transliterations_route.py`, and 2
  `similar-code` findings in `token_schemas.py`.
- Findings the branch **worsens** — the only qlty metric this PR moves the
  wrong way:
  - `ebl/transliteration/domain/word_tokens.py:141` `of` — 11 → **12** params
  - `ebl/transliteration/domain/greek_tokens.py:65` `of` — 10 → **11** params
  - `ebl/transliteration/domain/normalized_akkadian.py:49` `of` — 9 → **10**

  Each is caused by the single added `realia: Sequence[str] = ()` parameter,
  i.e. by the separate-array design the data hard gate requires. All three were
  already far above qlty's 5-parameter threshold on master, so no new issue is
  created and qlty cloud does not flag them — `qlty check` passes.

The uncommitted change from the previous task
(`ebl/tests/fragmentarium/test_realia_info_route.py`) was included in the local
scan and produces **no** qlty finding.

`qlty check` run locally reports 243 issues, but that run used the
`qlty init` **default** plugin set (mostly `bandit:B101` "assert used in
tests" and `mypy:call-arg` false positives). The project has no committed
`qlty.toml`; its real configuration lives in the qlty Cloud project, whose
verdict is the passing `qlty check` on the PR. The local numbers were therefore
treated as non-authoritative and not acted on.

## Conclusion

**There are no outstanding qlty issues on PR #740.** All 14 qlty findings are
resolved and the qlty gate passes.

The one open question is whether the three worsened `of` signatures should be
refactored. This is not a qlty-blocking issue, cannot be fully cleared without
bundling parameters into value objects across the transliteration domain (12
params → 11 is still above the threshold of 5), and would touch a large number
of call sites. Raised with the user rather than actioned unrequested.

## Status

No code changes made in this task. The working tree still holds only the
previous task's uncommitted test change. Nothing was committed or pushed.
