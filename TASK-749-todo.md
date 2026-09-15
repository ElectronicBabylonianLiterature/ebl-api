<!-- markdownlint-disable MD013 -->
# TASK-749 — TODO: write a standalone frontend brief

User asked for **one** `.md` file holding all context, the tasks, and the PR
body, so the frontend work can be picked up without access to this conversation
or the ebl-api repo.

## 1. Decide placement

- [x] Outside both repositories, alongside the other frontend artefacts, so it
      pollutes neither PR and survives the gate 3 cleanup

## 2. Content — must be self-contained

- [x] Why the change exists: the backend wire-format split, with evidence
- [x] Why it matters: silent wrong reading, not a crash
- [x] Repo facts: yarn not npm, Node 20 not 22, the three production sites
- [x] The design, with the actual code
- [x] The seven tests
- [x] Gates and how to run them
- [x] Commit message and the full PR body
- [x] Traps
- [x] Note that the work is already done and a patch exists

## 3. Verify

- [x] Code in the brief matches the committed `a9df351` exactly
- [x] `task lint-md` clean

## 4. Close-out

- [ ] Ask before committing
