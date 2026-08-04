---
applyTo: '**'
---

# Copilot Instructions

Project context and coding rules to follow when generating code, answering
questions, or reviewing changes.

## HARD GATE: Every Instruction In This File Is A Hard Gate

**Nothing in this file is advisory. Nothing may ever be skipped.** Every
section below carries the same binding force as the sections whose headings
say `HARD GATE` explicitly — those headings mark emphasis, not a higher tier.
There is no such thing as a minor point here.

- **Read "should", "avoid", "prefer" and "by default" as "must".** No point is
  a suggestion, a nice-to-have, or something to apply when convenient.
- **A checklist is exhaustive, never illustrative.** Running the named items is
  not evidence the list is complete — check this file for gates the list omits.
  Do not infer that one check passing means another would.
- **Skipping is failure, and so is deferring.** "I'll do it if asked", "it
  seemed like churn", "the work is obviously done" and "it was already like
  that" are not reasons. If a point genuinely cannot be satisfied, stop and say
  so before acting — never proceed and mention it afterwards.
- **A correction is a standing rule, not a one-off.** When corrected for
  skipping a point, the fix applies to every later task in the session and
  beyond, not just the task in hand.
- **Comply first, argue second.** Follow the instruction as written; raise
  disagreement separately. Never reinterpret a point so it no longer binds.

Before reporting any task complete, re-read this file and confirm every
section was honoured. State which gates ran and their results.

## Scope and Project Context

- This is a backend Python API project. Use backend-appropriate patterns,
  architecture, and tooling.
- Do not make any changes to the codebase unless explicitly requested.

## API Contract Authority

- The backend API schema is the source of truth for request and response
  field names.
- When a client/backend field naming mismatch exists, align the client to
  the backend schema by default.
- Do not introduce backend aliases for alternate client field names unless
  explicitly requested as a backward-compatibility requirement.

## HARD GATE: Different Data Types Never Intermix in One Array

**Two different types of data must never share one array.** They are held in
structurally separate arrays — a separate field per type — at every level:
domain object, Mongo document, and request/response body.

The type of a value must be knowable from **which array it is in**, never by
inspecting the value itself.

This is non-negotiable. It applies to new models and to any model you touch.

### The rules

- **One array, one data type.** A list, tuple, array field, or id list holds
  exactly one type. `Sequence[Foo | Bar]` is a defect, not a design.
- **Two types of id never share an id list.** This is the most common form of the
  mistake, because ids are all strings and so a mixed list still "type-checks".
  `["Entity-1", "Realia-1"]` is two data types in one array.
- **Never discriminate by probing.** If code must ask "does this object have
  `type`, or does it have `realiaId`?" to learn which type it is, the data is
  modelled wrong. Fix the model; do not write a smarter probe.
- **An optional field present for one type and absent for another means you have
  two types in one array.** Split the array.
- **Separate structurally, not just logically.** Two arrays (`named_entities`,
  `realia`), not one array plus a discriminator. Do not separate at one level and
  merge at another — if the domain has two fields, the wire has two keys.

### Worked example (the realia annotation defect)

```python
# WRONG — two types of id in one array; two types of object in one array
word.named_entities   = ["Entity-1", "Entity-2", "Realia-1"]
fragment.named_entities: Sequence[NamedEntity | RealiaEntity]
# a reader must join back and probe for `type` vs `realiaId` to know what it has

# RIGHT — structurally separate, one type per array
word.named_entities   = ["Entity-1", "Entity-2"]   # tag ids only
word.realia           = ["Realia-1"]               # realia ids only
fragment.named_entities: Sequence[NamedEntity]
fragment.realia:         Sequence[RealiaEntity]
```

Once each array holds one type, mixing becomes an unknown-field error for free
under `unknown=RAISE` — no discriminator, no bespoke validator, no polymorphic
dispatch. **Reaching for a `OneOfSchema` to tell two types apart inside one array
is the signal to split the array instead.** A payload that puts one type's field
on the other is a `422`, never a silent coercion.

### Separation is structural, not relational

Separating the arrays must not sever real relationships between the data:

- Two types may still describe the **same** thing. A named-entity tag and a
  realia may legitimately annotate the same token range — that is the feature.
  Separate arrays, overlapping references.
- **Splitting the arrays does not split a shared id space.** When two separated
  types are resolved through the same lookup, invariants over that namespace —
  uniqueness, existence, referential integrity — must still be enforced across
  the **union** of both arrays.

### Why

A mixed array pushes the type question onto every reader, forever. Each consumer
re-derives the type, each one can get it wrong, and the type checker cannot help
any of them. Separate arrays answer the question once, in the shape of the data,
and turn a class of runtime bug into a type error.

## Coding Standards

- Follow the existing coding style and conventions used in the project.
- Always use full variable and function names for clarity.
- Ensure that all functions and methods have appropriate type hints.
  Avoid using `Any` unless very necessary.
- Functions should be small and focused on a single task.
- Refactor long and complex code automatically.
- Do not add comments to the code unless explicitly requested.
- HARD GATE: no `*.py` file may exceed 250 total lines. If a change pushes a
  file past this limit, refactor by extracting modules or splitting test files
  before completing the task. This is non-negotiable and applies to both
  source and test files.

## Commands and Tooling

- When running shell commands for project tasks, always use `poetry run`
  unless using `task`.

## HARD GATE: Never Commit or Push Unless Explicitly Told To

This is the highest-priority rule in this file. It overrides every other
instruction, including any instruction to "complete", "finish", or "ship" a task.

- **Committing and pushing are NEVER part of a task.** Finishing the code,
  passing every gate, and updating the task log is the *whole* job. The task is
  complete when the working tree holds verified changes — not when it is
  committed.
- Run `git commit`, `git push`, `git merge`, `git rebase`, `git reset`,
  `git cherry-pick`, `git revert`, `git tag`, or `gh pr create` / `gh pr merge`
  **only** when the user asks for that action in that message, in their own
  words ("commit this", "push it", "open the PR").
- Approval is **single-use and does not carry forward.** "Commit now" authorizes
  exactly one commit, of exactly the changes under discussion. It does not
  authorize the next commit, a push, or a follow-up task's commit. When in
  doubt, you do not have permission.
- **Never force-push, and never rewrite pushed history** — no
  `git push --force`, `--force-with-lease`, `git reset --hard`, or amending a
  pushed commit — without the user explicitly asking for that specific
  operation, having been told what it will destroy.
- Never infer consent from a previous message, from momentum, from the work
  being "obviously done", or from a passing test suite.
- When the work is finished, **stop and report.** State what changed, that the
  gates pass, and that the changes are uncommitted. Then wait. Offer to commit;
  do not commit.
- This gate is enforced mechanically by `.claude/settings.json`, which denies
  force-push outright and requires explicit approval for every commit, push, and
  history-rewriting command. Never weaken, bypass, or work around those rules
  (e.g. by shelling out differently to dodge a pattern). If a git action is
  blocked, that is the gate doing its job: ask the user.

Violating this gate is a serious failure even if the code itself is correct.

## Pre-Commit Hard Gates (only once the user has asked you to commit)

These are prerequisites for a commit the user has **already** authorized. They
are not permission to commit. Run all of the following in order and confirm each
passes before committing:

1. `task format` — auto-format code (must exit 0 with no unstaged changes left)
2. `task lint` — ruff (must exit 0)
3. `task type` — **pyre; this is the gate CI enforces. Zero errors.**
4. `task type-pyright` — pyright on changed files. Zero errors.
5. `task test` — full test suite (must pass with 0 failures)
6. `poetry run pytest <changed modules> --cov=<changed modules>
   --cov-report=term-missing` — 100% coverage on all changed files
7. `poetry run flake8 <changed modules> --max-line-length=120` — zero lint
   errors
8. `poetry run mypy <changed modules> --ignore-missing-imports` — zero type
   errors in the changed files (a pre-existing error in a file you touched is
   not acceptable; fix it)

Never commit if any gate fails or was skipped. Never commit if the user did not
ask you to — see the hard gate above.

### HARD GATE: All Three Type Checkers Must Pass

The repo runs **three** type checkers and they do not agree. Passing one says
nothing about the others. All three are blocking:

- `task type` (**pyre**) — the checker CI runs. A pyre error fails the build.
- `task type-pyright` (**pyright**) — the checker behind Pylance / the IDE.
- `poetry run mypy` — as scoped in gate 8 above.

Never treat a green mypy or pyright as evidence that pyre passes. Pyre ships its
own typeshed and rejects constructs the others accept — `zip(..., strict=True)`
(a Python 3.10 parameter) is one real example that reached CI. **Run `task type`
before every commit, and never infer its result from another checker.**

When two checkers give contradictory demands, **the code is wrong, not the
checkers.** Restructure until all three pass. Do not satisfy one by breaking
another, and do not silence either with a config change, an ignore comment, or a
suppression — see the rule against disabling lint rules. Worked example: ruff
`B905` requires `zip(..., strict=)` while pyre rejects `strict`; the resolution
was to remove the parallel-array `zip` entirely in favour of a keyed lookup,
which satisfied every checker and produced a better design.

`task test-all` runs format, lint, type, type-pyright, test and lint-md together
and is the cheapest way to confirm every gate at once.

## Testing and Quality

- Add / update tests for any new functionality or significant changes.
- When writing tests, ensure they are isolated and do not depend on
  external state (pytest conventions).
- Ensure that coverage is 100% after changes in affected code.
- HARD GATE: verify changed behaviour by **running the modified backend
  service** and exercising the affected route, not by tests alone, whenever the
  change has a runtime surface. A passing suite is not evidence the running
  service behaves correctly.
- HARD GATE: **re-verify after every rewrite.** Evidence gathered before a
  change does not cover what replaced it. If the implementation is reworked
  after a verification run, that run is void — do it again against the code
  that will actually ship, and confirm the process you are testing is running
  the current tree.
- HARD GATE: pre-existing coverage gaps must be filled, not preserved. Any
  line you add, modify, move, or relocate must end at 100% coverage, even if
  it was uncovered before you touched it. "It was already uncovered on the
  base branch" is not an acceptable justification for leaving a touched line
  uncovered — add the missing tests as part of the change. This is
  non-negotiable.
- Never remove, disable, skip, or comment out existing tests without
  explicit user confirmation.
- Only propose removing a test when the underlying code path was removed
  or changed such that the assertion is no longer meaningful.
- If test removal is proposed, provide detailed justification first and
  wait for explicit user approval before making that change.
- Run `task lint-md` as a quality gate; zero errors and warnings are
  required before committing any markdown changes.
- Never modify linting or formatting configuration files
  (`.markdownlint.json`, `.markdownlintignore`, `pyproject.toml` linting
  sections, `mypy.ini`, `ruff.toml`, etc.) without an explicit user
  request. Fix real content issues instead of disabling rules.

## HARD GATE: Task Tracking and Cleanup

**Create the TODO and the log BEFORE starting work — not at the end, not when
reminded.** They are the first artefacts of a task, not a write-up of it.

- For every task, create a mandatory detailed TODO list in a `.md` file.
- For every task, create and maintain a detailed work log in a `.md`
  file.
- Use a consistent naming convention for these files:
  `TASK-<id>-todo.md` and `TASK-<id>-log.md`.
- Keep both the task TODO list and task log constantly updated while
  working. "Constantly" means as each step completes, not in one pass at the
  end.
- **Every task means every task.** A fix, a review, a one-line change, a
  follow-up to the task just finished — each is a task and each needs both
  files. Small, obvious, or urgent is not an exemption. Being mid-session or
  continuing earlier work does not carry the previous task's files forward.
- The log records what was actually done, including **every error made and
  how it was recovered**, not a sanitised account.
- Removing these files at a user's request settles that PR only. The **next**
  task starts by creating them again.
- Before a PR is merged, check for these task TODO/log `.md` files and
  remind to remove them.

## Review Guidelines

- HARD GATE: before finalizing any PR review, fetch and incorporate all
  existing GitHub feedback on the PR — submitted reviews, inline (diff)
  review comments, and issue/conversation comments — including from bots
  (e.g. Sourcery, qlty, Codex). Also fetch feedback for any PR whose branch
  has been merged into the one under review. Use the GitHub CLI, e.g.:
  `gh api repos/<owner>/<repo>/pulls/<n>/reviews`,
  `gh api repos/<owner>/<repo>/pulls/<n>/comments`, and
  `gh api repos/<owner>/<repo>/issues/<n>/comments`. Every unresolved finding
  must be explicitly addressed or acknowledged with a rationale in the review
  file. A review that ignores existing PR feedback is incomplete and must not
  be finalized. This is non-negotiable.
- Keep review comments short, specific, and actionable.
- Prioritize correctness, regressions, security, and test coverage in
  every review.
- Check every data-shape change against the data hard gate above. Flag any array
  holding more than one data type — id lists especially, since mixed ids are all
  strings and still "type-check" — any type discriminated by probing for an
  optional field, and any shape split in the domain but merged on the wire (or
  the reverse). Confirm that invariants over a shared id space are still enforced
  across the union of the separated arrays.
- Verify changed behavior locally by running the modified backend service
  and related tests before finalizing review conclusions.
- Export every detailed review to a `.md` file using the same
  convention: `TASK-<id>-review.md`.
- Use a consistent review template with these sections: `Summary`,
  `Findings`, `Severity`, `Reproduction Steps`, and `Recommendation`.
- Keep the review file updated as findings change, and remind to remove
  it before a PR is merged.
