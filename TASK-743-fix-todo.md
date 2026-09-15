# TASK-743-fix TODO — Address the findings in `TASK-743-review.md`

Task: apply the fixes for findings F1-F14 raised in the round-12 review of
PR #743. Branch `fix-type-checker-blind-spots`, base `master`.

Status legend: `[ ]` pending, `[~]` in progress, `[x]` done, `[!]` blocked

## 0. Task artefacts (hard gate)

- [x] Create `TASK-743-fix-todo.md` before starting work
- [x] Create `TASK-743-fix-log.md` before starting work
- [x] Keep both updated as each step completes
- [x] Remind user to remove all six TASK files before the PR is merged

## 1. Scope the blocking findings

- [x] F1 — establish what `name_parts` actually holds and how interleaving
      works, so the split is designed rather than guessed
- [x] F1 — confirm with the user which of the three valid readings to
      implement, since they differ materially (wire break vs. domain-only vs.
      deferral)

## 2. Blocking findings

- [x] F1 — `NamePart` one-array/one-type gate
- [x] F2 — restore the nine locally defined classes to `tokens.py`'s `__all__`
- [x] F2 — add a facade regression test covering all four split modules
- [x] F3 — remove both `# type: ignore[arg-type]` via a `Protocol`
- [x] F3 — annotate `_site_filter`'s `service` parameter

## 3. Non-blocking findings

- [x] F4 — describe the instruction-file change in the PR body
- [x] F5 — `GET /signs?listAll=true` 500 (`KeyError: '_id'`)
- [x] F6 — `/markup` and `/cached-markup` 500 on unparsable input
- [x] F7 — drop the redundant `cast(TextLine, other)`
- [x] F8 — type `update_alignment` against `AlignmentMap` at both ends
- [x] F9 — `_StartParser.__getattr__` no longer returns `object`
- [x] F10 — `attr.Factory(NullSignsCollectingVisitor)` instead of a shared
      class-body instance
- [x] F11 — annotate the three touched `make_token` hooks
- [x] F12 — delete the duplicated `Divider.string_flags`
- [x] F13 — informational, no action
- [x] F14 — informational; keep `lark_parser.py` within 250 lines

## 4. Description corrections (raised in the review)

- [x] Correct the "the `NamePart` converter no longer probes" passage
- [x] Correct the "touches no configuration file at all" passage
- [x] Reflect whatever F1 resolution is chosen

## 4b. Extra work the findings required

- [x] Legacy `@pre_load` adapter so existing Mongo documents keep loading
- [x] `task_743_migrate_name_breaks.py` migration script, branch-only temp
      file (dry-run by default, not run)
- [x] Migrate 37 interleaved-name test call sites
- [x] Rewrite `test_name_part.py` as `test_named_sign_name.py`

## 5. Gates before reporting complete

- [x] `task format`
- [x] `task lint`
- [x] `task type` (pyre — the CI gate)
- [x] `task type-pyright`
- [x] `task test`
- [x] `poetry run flake8 <changed modules> --max-line-length=120`
- [x] `poetry run mypy <changed modules> --ignore-missing-imports`
- [x] 100% coverage on every changed source module
- [x] `qlty smells` and `qlty check --no-fix` on changed files
- [x] `task lint-md`
- [x] 250-line limit on every changed `*.py`
- [x] Runtime verification: boot the service and re-exercise every affected
      route (re-verify from scratch — the earlier run is void once code changes)
- [x] Committed at your explicit request (`2b3b0668`), code only.
      **Not pushed** — remote is still at `16a84e20`

## 6. Documentation and handoff

- [x] `TASK-743-fix-handoff.md` — status, both blocking gates, all fourteen
      findings with their resolution, decisions taken, next steps
- [x] `TASK-743-fix-pr-body.md` — corrected PR description with the two
      blocking gates as a warning callout at the top and a new Part 7
- [x] qlty findings each fixed or justified in the log
- [x] `task lint-md` clean across all task documents
