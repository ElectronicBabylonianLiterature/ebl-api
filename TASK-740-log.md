# TASK-740 Work Log — Fix pyre error and gate against it

Date: 2026-07-16. Branch: `add-realia-annotation-api`.

## 1. Trigger

CI failed on the pushed commit `52292208`:

```text
ebl/fragmentarium/web/fragments.py:92:46 Unexpected keyword [28]:
Unexpected keyword argument `strict` to call `zip.__new__`.
Process completed with exit code 1
```

## 2. Why the gates missed it

The pre-commit gate list named format, test, coverage, flake8 and mypy. I ran
those plus pyright and treated the list as exhaustive, so I never ran
`task type` — pyre, the checker CI actually enforces. Green mypy and pyright
were taken as evidence the code type-checked. They are not: pyre ships its own
typeshed and rejects constructs the others accept. `f36ed7d9`'s commit message
had already stated the repo runs three type checkers; I read it and still did
not run pyre.

## 3. Root cause of the error

`strict=True` was my own addition. Ruff `B905` flags a bare `zip`, so I added
`strict=` without checking pyre, whose typeshed predates the Python 3.10
parameter. The result was a genuine contradiction: ruff demands `strict=`,
pyre rejects it, so no `zip` call could satisfy both.

## 4. Fix

Rather than break one checker to satisfy the other, removed the `zip`.
`resolve_realia_info_for_documents` had returned a list positionally parallel
to the documents — precisely the fragile coupling `strict=True` was papering
over. Replaced with:

- `resolve_realia_info_map(documents, repo) -> Dict[str, RealiaInfo]`
- `document_realia_info(document, info_by_realia_id) -> List[RealiaInfo]`

Each fragment now looks up its own realia by key. No parallel arrays, no
`zip`, no `strict`. The single batched `find_by_realia_ids` per page is
preserved, and `fragments.py` fell to 249 lines, back under the 250 gate.

## 5. Verification

- `task type` (pyre): No type errors found.
- pyright on changed files: 0 errors. mypy: 0 in changed files.
- `task lint` (ruff): all checks passed — B905 no longer applies.
- Coverage: `realia_info.py` and `fragments.py` both 100%.
- `task test-all` (format, lint, type, type-pyright, test, lint-md): exit 0,
  3923 passed.
- Service re-run: see section 7 — the resolution logic was rewritten after
  the previous service verification, so test-only evidence was insufficient.

## 6. Prevention

Updated `.github/instructions/copilot.instructions.md`:

- Pre-commit gates now include `task lint`, `task type` and
  `task type-pyright` ahead of the tests.
- New hard gate "All Three Type Checkers Must Pass": pyre is what CI
  enforces; a green mypy or pyright is never evidence pyre passes; when two
  checkers contradict, the code is wrong — restructure, never suppress. The
  `zip`/`strict` incident is recorded as the worked example.
- Elevated task tracking to a hard gate requiring the TODO and log to exist
  **before** work starts, since "for every task" was being read as advisory.

While drafting, I claimed `task check` runs everything. It does not exist —
the real task is `task test-all`. Caught by running it rather than trusting
memory. An instruction file naming a non-existent command is worse than none.

## 7. Errors made during this task

- **Did not create these task docs at the start.** The same violation the
  user corrected earlier in this session; I fixed it once when caught and
  then reverted on the next task. Created retrospectively, and the rule is
  now a hard gate plus a persisted memory so it does not depend on my
  remembering.
- **Reported the rewritten resolution on test evidence alone.** The map-based
  logic replaced the code verified in the earlier service run, so that
  verification no longer covered what shipped. Re-ran the service (below).

## 8. State

Nothing committed. CI stays red until the fix is committed and pushed.
