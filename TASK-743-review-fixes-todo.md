# TASK-743-review-fixes — TODO

Address every finding raised in `TASK-743-review.md` for PR #743.

## Findings to address

- [x] **F1 (High)** — `task type-pyright`: 149 errors -> 0. Structurally, with
      no `# type: ignore`, no `# pyright: ignore`, no config change (the
      instructions forbid silencing).
- [x] **F2 (Medium)** — PR description out of sync with the 82-file diff; the
      pyre claim in the body is wrong. Rewrite the body.
- [x] **F3 (Medium)** — remove the six committed `TASK-743-*` tracking files.
- [x] **F4 (Medium)** — 30 uncovered statements in the four files this PR
      created; add the missing tests.
- [x] **F5 (Low)** — `TokenVisitor.result` returns `[]` on the ABC base.
      Remove the lying default.
- [x] **F6 (Low)** — module surfaces narrowed inconsistently; make the facade
      convention uniform.
- [x] **F7 (Low)** — unreachable `if line is not None` filter in
      `parse_atf_lark`.
- [x] **F8 (Low)** — no action; recorded in the review for the record only.
- [x] **F9 (Info)** — `NameParts = Sequence[Union[ValueToken, BrokenAway]]`.
      Needs a user decision (splitting destroys token ordering).
- [x] **F10 (Info)** — pre-existing 500 on the signs route. Out of this PR's
      scope; needs a user decision.

## Gates to re-run before reporting complete

- [x] `task format`
- [x] `task lint`
- [x] `task type` (pyre — the gate CI enforces)
- [x] `task type-pyright` (must reach zero)
- [x] `task test`
- [x] coverage on changed modules
- [x] `flake8 --max-line-length=120`
- [x] `mypy --ignore-missing-imports`
- [x] 250-line-per-file gate
- [x] `task lint-md`
- [x] runtime verification — re-run after the rewrites, since prior evidence
      is void once the implementation changes
- [x] update `TASK-743-review.md` to reflect what was fixed

## Constraints

- **No commits, no pushes.** Report and stop when the tree is verified.
- No linting/formatting config changes, no suppressions.
- No `.py` file over 250 lines.

## Status

**Complete.** All ten findings addressed; every gate green.

| Gate | Before | After |
| --- | --- | --- |
| `task type-pyright` | 149 errors | **0** |
| `task type` (pyre) | pass | pass |
| `task test` | 4251 passed | **4308 passed** |
| Uncovered lines on PR-touched code | 30 | **0** |
| Committed `TASK-743-*` files | 6 | **0** |

F9 was implemented as a domain-only wrapper after the `nameParts` wire
contract came to light; the JSON payload is verified byte-identical.
F4's last two lines were provably unreachable guards and were removed.
Two pre-existing oversized files (`mongo_sign_repository.py`,
`test_sign_tokens.py`) entered the changed set and were split.

**Nothing is committed.** The PR body on GitHub was updated, as approved.
