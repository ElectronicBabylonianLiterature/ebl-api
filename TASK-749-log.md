<!-- markdownlint-disable MD013 -->

# TASK-749 — Work log

## 2026-09-15

### Start

- Created this log and `TASK-749-todo.md` before starting. TASK-748's files do
  not carry forward.
- Trigger: "There should be a detailed prompt saved to a single .md file that
  contains all the context, tasks and PR body. Create one now."
- Audience is **not** the user: it is whoever picks up the frontend work, with
  no access to this conversation, the ebl-api repo, or PR #743. Written to be
  self-contained.

### Entries

#### Written and verified

Created **`/workspaces/ebl-frontend-nameBreaks-BRIEF.md`** (15 KB, 11 sections).
Placed outside both repositories, alongside the other frontend artefacts, so it
pollutes neither pull request and is not swept up by #743's gate 3 cleanup.

Contents: the backend change with a real payload, why it matters (silent wrong
reading, and that it also feeds the image-annotation tool), the deploy ordering
and why the frontend must ship first, repository facts (yarn, Node 20, the three
production sites out of seventeen files), the full task with copy-able code, all
seven tests, the gates, the correctness note tying the interleave to the
backend's `zip_longest`, the commit message, the complete PR body between
markers, the patch shortcut, and the push blocker.

**Verified rather than assumed.** Extracted every added source line from
`git diff master..add-name-breaks` and checked each appears in the brief, and
did the same for every `it('...')` test name. One gap surfaced: the `accents.ts`
import was described in prose but not shown as code, so the reader could not
copy it. Added the import block; re-ran both checks clean.

`markdownlint` clean. One fix needed on the way: the internal link to the
Shortcut section used the wrong anchor, since the numbered heading generates
`#10-shortcut--apply-the-existing-patch`.

Also exported `/workspaces/ebl-frontend-nameBreaks.patch` earlier in the session,
which reproduces `a9df351` exactly. The brief points at it.

#### Moved into the repository

The codespace is remote, so files under `/workspaces/` outside the repo cannot be
downloaded from the IDE. Moved all three into the repository root:

| Was | Is |
| --- | --- |
| `/workspaces/ebl-frontend-nameBreaks-BRIEF.md` | `TASK-749-frontend-brief.md` |
| `/workspaces/ebl-frontend-nameBreaks.patch` | `TASK-749-frontend.patch` |
| `/workspaces/ebl-frontend-pr-body.md` | `TASK-749-frontend-pr-body.md` |

Named with the `TASK-` prefix deliberately, so gate 3's verification
(`git ls-files | grep -E '^(TASK-|task_743_)'` must print nothing) catches them.

Fixed up on the way:

- The brief referenced the old filenames in four places; all updated, and a
  table added near the top listing the three files that belong together, since
  the brief is now one of several rather than a lone document.
- `TASK-749-frontend-pr-body.md` starts with prose, which trips
  `MD041/first-line-heading`. Added the same
  `<!-- markdownlint-disable MD013 MD041 -->` header that `TASK-743-fix-pr-body.md`
  already carries — an HTML comment, invisible when GitHub renders the body.
- **Two write attempts were aborted by their own assertions** before touching
  anything, because the strings I expected did not match the file's line
  wrapping. Found the real text with `grep -n` and redid it. No partial writes.

#### Gate 3 grew

`TASK-745-handoff.md` section 7 updated: **sixteen files to twenty-three**, which
matches the 23 `TASK-*` files now on disk. The deletion command no longer globs
`*.md`, since `TASK-749-frontend.patch` is not markdown. The three frontend
artefacts are flagged **save a copy before deleting** — unlike the task logs they
are still needed after the merge, because the frontend PR may not be open yet.

`task lint-md`: 0 errors across 26 files.
