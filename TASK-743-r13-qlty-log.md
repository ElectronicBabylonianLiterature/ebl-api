<!-- markdownlint-disable MD013 -->
# TASK-743-r13-qlty — Work Log

Removing the two qlty blocking issues on PR #743.

## 2026-09-17

### Step 1 — task files created before work

### Step 0 — the decision

I had justified both findings in earlier rounds, and the copilot instructions do
carve out exactly this case. The user has decided they must be addressed anyway.
That is their call; I am fixing them. The constraint I will not bend is the rule
against silencing qlty — no config edit, no ignore comment, and no reshuffling a
list purely to drop below the detector threshold.

### Steps 2–5 — what the two findings actually are, and what it costs to remove them

Both are `__all__` export lists that happen to have the same AST shape as another list of string literals.

| | Pair | Mass |
| --- | --- | --- |
| A | `transliteration/domain/tokens.py` `__all__` ↔ `fragmentarium/domain/fragment.py` `__all__` | 64 |
| B | `tests/factories/fragment.py` `__all__` ↔ `tests/fragmentarium/test_museum_number.py` `PREFIXES` | 84 |

**Established by experiment, not assumption:**

1. **`__all__` is load-bearing.** Deleting it from `fragment.py` produces **3 ruff F401 errors** — the re-exported imports become "unused". So it cannot simply go.
2. **`tokens.py` and `tests/factories/fragment.py` must keep theirs** — both are in `FACADE_MODULES` in `ebl/tests/test_module_facades.py`, whose three parametrized assertions would have to be deleted otherwise. Removing tests needs explicit approval and was not on the table.
3. **Nothing does `import *` anywhere in `ebl`**, so `__all__` here exists purely to mark re-exports for the linters.
4. Of the 15 names in `fragment.py`'s `__all__`, **1 is local (`Fragment`) and 14 are re-exports**. Of the 20 in `tests/factories/fragment.py`, 10 local and 10 re-exports.

**Attempt 1 — the PEP 484 redundant-alias form** (`from x import y as y`), which states each re-export once at the import and lets `__all__` shrink to locally-defined names. This is the standard, statically-checkable way to mark a re-export, and it removes the drift class that F2 had to fix in `tokens.py`.

Result: **ruff, pyright and mypy all accept it. flake8 does not** — pyflakes only honours the redundant alias in `__init__.py`, so it reported 8 F401 errors. Gate 7 requires zero. Per the rule that contradictory checkers mean the code is wrong, I did not paper over it with `# noqa` (that is silencing a linter) and **reverted the half-finished change** rather than leave the tree failing a gate.

**Attempt 2 — remove the re-export indirection entirely**, so consumers import from the module that actually defines the symbol and no unused import exists for any linter to flag. This is the genuinely correct fix. Measured cost:

| Module | Consumers to rewrite |
| --- | --- |
| `fragmentarium/domain/fragment.py` (14 re-exports) | **37 files** |
| `tests/factories/fragment.py` (10 re-exports) | **16 files** |
| | **53 files total** |

All pure import-path edits, mechanical and verifiable. But it grows a 212-file PR by another 53 files, pulls files into the diff that the PR does not currently touch, and would land on a branch that is finally green and `mergeable: clean` after 13 review rounds.

**A partial shrink is not an option.** Dropping only *some* re-exports to slip under qlty's mass threshold is detector-dodging, which the instructions forbid as firmly as editing `qlty.toml`. The principled rule is "this facade re-exports nothing" — which is all 53 files, or none.

### Incidental finding

While the change was in place, qlty surfaced a different pair: `tests/fragmentarium/test_museum_number.py` ↔ `tests/transliteration/test_reconstructed_text_parser.py`, 22 lines, mass 81. Checked it in a detached worktree at `origin/master`: **it exists there too**, and both files are byte-identical to master. Pre-existing, not introduced here, and not attributable to this PR.

Repo-wide during the attempt: 106 → 104 findings.

### Decision (user, 2026-09-17)

Presented the measured cost; the user chose to **leave both findings justified**. The branch stays as it is.

That is the outcome the instructions' own carve-out anticipates — "two unrelated `__all__` lists that happen to have the same shape" — and it is now backed by evidence rather than assertion:

- `__all__` cannot be deleted (3 ruff F401 errors prove it is load-bearing).
- The redundant-alias alternative is rejected by flake8, which only honours it in `__init__.py`.
- The only honest remaining fix is removing the re-export facades, costing 53 consumer rewrites.
- Nothing here can be silenced: no `qlty.toml` edit, no `# qlty-ignore`, no `# noqa`, no threshold-dodging reshuffle.

**Working tree restored.** `ebl/fragmentarium/domain/fragment.py` and `ebl/tests/factories/fragment.py` reverted with `git checkout --`; flake8 and ruff confirmed clean afterwards. No source file is left modified by this task.

### Steps not needed given the decision

Steps 6–9 (implement, re-verify qlty, full gates, runtime re-verification) fall away — there is no code change to verify. Step 10 is done below: the justification already sits in the PR description, and the handoff now carries the cost analysis so the next person does not re-derive it.

### Committing the documents (user-authorized, 2026-09-17)

Ran the pre-commit gates in order. Every one passed except pyre.

| Gate | Result |
| --- | --- |
| `task format` | 912 files already formatted |
| `task lint` | All checks passed |
| **`task type` (pyre)** | **FAILED — `Pyre encountered an internal exception: End_of_file`** |
| pyright (direct) | 0 errors, 0 warnings, 0 informations |
| `task test` | **4773 passed**, 2 skipped, 1 xfailed |
| Coverage | vacuous — no Python file changed |
| flake8 | clean |
| mypy | Success |
| qlty / `task lint-md` | clean; 0 errors over 37 files |

#### Correction to what I told the user earlier

I twice attributed a pyre `End_of_file` to CPU contention and said a quiet re-run cleared it. **That explanation was wrong.** It has now failed three consecutive times with nothing else running, crashing at roughly the same point (~5808 of 7739 functions). The evidence points to memory: 7.8Gi total, **no swap**, ~3.2Gi available, with VS Code's node processes holding ~1.8Gi. I also found a leftover waitress service of mine from an earlier runtime verification still resident and killed it; it did not change the outcome.

I had also written a "pyre can fail spuriously — re-run with nothing else going" trap into the handoff on that mistaken basis. That guidance is wrong and is corrected below.

#### Why committing is nonetheless sound here

- The Python tree is **byte-identical to the pushed commit `6d0f2829`**: `git diff HEAD -- '*.py'` returns nothing and there are no untracked `.py` files. This commit contains **markdown only**.
- **CI runs pyre on every push** — `poetry run pyre check`, the "Type Check" step of the Test Python jobs, `.github/workflows/main.yml:80`. All six Test Python jobs passed on `6d0f2829`. So pyre passed on exactly this source in a clean environment.
- A markdown-only commit cannot change a type-check result.

I did not treat the red gate as green on my own initiative: I reported it, explained the limitation, and the user decided to proceed.
