<!-- markdownlint-disable MD013 -->
# TASK-743-r13-watch — Work Log

Tracking PR #743's remote status and checks after the push.

## 2026-09-17

### Step 1 — task files created before any work

- Created `TASK-743-r13-watch-todo.md` and `TASK-743-r13-watch-log.md` before any tracking work.

### Step 2 — push confirmed

- `git fetch origin`; local `HEAD` and `git ls-remote` both at **`13b80d92`**. `git rev-list --count origin/…..HEAD` = **0**. Nothing unpushed.
- Working tree held only the two new tracking files at that point.

### Steps 3–4 — PR state on the new head

| Field | Value |
| --- | --- |
| head | `13b80d92` |
| **mergeable** | **`true`** — B2 is resolved on GitHub, the conflict is gone |
| mergeable_state | `blocked` |
| commits / files | 28 / 208, +15656 / −6928 |
| `qlty check` | `success`, "2 blocking issues" — the two justified duplications, unchanged |
| GitGuardian ×3 | success |
| `Analyze (python)` | success |
| Sourcery review | skipped |
| Test Python 3.11 / 3.12 / pypy-3.11 (×2 each) | in progress |
| **CodeQL** | **failure — "1 new alert including 1 error"** |

### Step 7 — the CodeQL failure is mine

Fetched the check run's annotations (the alerts API is 403 for this token, but `repos/…/check-runs/<id>/annotations` works):

```text
ebl/tests/transliteration/test_named_sign_errors.py:72  failure
An assert statement has a side-effect
```

That is the test file I added in the round-13 fix. Line 72 was:

```python
assert loaded.name_breaks == (BrokenAway.close(),)
```

`BrokenAway.close()` is a call inside an `assert`. The rule is not pedantry: under `python -O` the whole statement is stripped, so anything with an effect silently stops happening. Three CodeQL threads on `test_named_sign_name.py` had already been raised and resolved for this same rule earlier on this branch, and that file avoids it by hoisting the calls into module constants (`CLOSE = BrokenAway.close()`). I did not follow the existing pattern, so I reintroduced the alert.

**Fixed** by matching the sibling file: module-level `K`, `U`, `CLOSE` constants, and the asserts compare against those.

**Two more that CodeQL did not flag but would break the same way.** `test_more_breaks_than_parts_is_unprocessable_on_a_route` and `test_a_negative_sub_index_is_unprocessable_on_a_route` both had `assert _status_for(payload) == …`, and `_status_for` builds a falcon app and simulates a request. Under `-O` those two tests would assert nothing *and* never exercise the route. Hoisted into a `status` local first. This was not reported — I found it while checking whether the fix was complete.

Left alone: the pre-existing `assert`-with-call lines in `test_named_sign_name.py` and `test_named_sign_validation.py`. CodeQL did not flag them on this run, they are not new, and rewriting them would be churn beyond this task.

Gates after the fix: pytest 5 passed, ruff format, ruff, flake8, mypy, pyright all clean.

### Tracking after the push of `6d0f2829` (2026-09-17)

`git ls-remote` = local `HEAD` = `6d0f2829`, 0 unpushed.

**Every check run completed:**

| Conclusion | Checks |
| --- | --- |
| success | **CodeQL**, `Analyze (python)`, GitGuardian Security Checks, GitGuardian scan ×2, Test Python 3.11 ×2, 3.12 ×2, pypy-3.11 ×2 |
| skipped | Sourcery review, docker ×2 |
| failure | **none** |

**Commit statuses:** overall `success` — `qlty check` success ("2 blocking issues", the two justified duplications), `qlty coverage diff` **100.0%** against a 75% threshold, `qlty coverage` 96.7% (+0.7%).

**PR:** `mergeable: true`, `mergeable_state: **clean**` — up from `blocked`, so branch protection is satisfied. 29 commits, 212 files, +15868/−6928.

**CodeQL went from failure to success**, confirming the assert fix cleared the alert. No new alert appeared.

**Review threads:** two unresolved, both `qltysh` (`tests/factories/fragment.py`, `transliteration/domain/tokens.py`) — the accepted duplications, left open on purpose. No new reviews or inline comments since the push.

**Noted from the push output, not this PR's doing:** GitHub reports 1 high-severity Dependabot alert on the **default branch** (alert 75). Out of scope here; raised with the user.
