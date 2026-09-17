<!-- markdownlint-disable MD013 -->
# TASK-743-r13-codeql — Work Log

Addressing the findings open after pushing `13b80d92`.

## 2026-09-17

### Step 1 — task files created before work

- Created `TASK-743-r13-codeql-todo.md` and `TASK-743-r13-codeql-log.md` before work.

### Steps 2–3 — the CodeQL finding and one it did not report

The only failing check on the pushed head `13b80d92` is **CodeQL**: "1 new alert including 1 error". Located via the check-run annotations endpoint (the code-scanning alerts API is 403 for this token):

```text
ebl/tests/transliteration/test_named_sign_errors.py:72   An assert statement has a side-effect
```

That is my file, from the round-13 fix. The line was `assert loaded.name_breaks == (BrokenAway.close(),)`. The rule is not cosmetic — under `python -O` the whole `assert` is stripped, so the call stops happening. The sibling `test_named_sign_name.py` already avoids it with module constants, and three CodeQL threads for this same rule had been raised and resolved on that file earlier in the branch. I did not follow the established pattern and reintroduced it.

**Fixed** by hoisting to module constants `K`, `U`, `CLOSE`, matching the sibling file.

**Also fixed, though CodeQL did not flag it:** `test_more_breaks_than_parts_is_unprocessable_on_a_route` and `test_a_negative_sub_index_is_unprocessable_on_a_route` both read `assert _status_for(payload) == ...`. `_status_for` builds a falcon app and simulates a request, so under `-O` those two tests would assert nothing *and* never exercise the route — a worse instance of the same defect than the one reported. Both now assign to a `status` local first. Found while checking whether the reported fix was complete, not reported by any tool.

Deliberately left alone: the pre-existing `assert`-with-call lines in `test_named_sign_name.py` and `test_named_sign_validation.py`. Not new, not flagged on this run, and rewriting them is churn outside this task.

### Step 4–6 — CI on `13b80d92`, now fully settled

| Conclusion | Checks |
| --- | --- |
| success | `Analyze (python)`, GitGuardian ×3, **Test Python 3.11 ×2, 3.12 ×2, pypy-3.11 ×2** |
| skipped | Sourcery review, docker ×2 |
| **failure** | **CodeQL** — the alert above, and the only failure |

- `qlty check` status: `success`, "2 blocking issues" — the two justified duplications, unchanged.
- **`mergeable: true`** — the merge resolved the conflict on GitHub. `mergeable_state: blocked` is branch protection awaiting checks/review, not a merge problem.
- New feedback since the push: one `github-advanced-security` review and one inline comment, both the CodeQL alert above. **No** new human or Sourcery feedback.

### Step 8 — runtime re-verification (previous run void after the rewrite)

Rebuilt the throwaway rig (the scratchpad had been cleared), booted the service on a fresh db `ebl_t743_r13c`, re-seeded, and re-ran:

| Route | Result |
| --- | --- |
| `GET /fragments/K.1` (legacy interleaved) | **200** |
| `GET /fragments/K.3` (breaks > parts) | **422** |
| `GET /signs/transliteration/kur` | 200 |
| `GET /signs/transliteration/$$$` | 422 |
| `GET /markup` invalid | 422 |

Unchanged, as expected — the fix touches only test code — but measured rather than assumed.

### Step 7 — gates before the authorized commit

| Gate | Result |
| --- | --- |
| `task format` | 912 files already formatted |
| `task lint` | All checks passed |
| **pyre** | **No type errors found** |
| pyright (direct — the task only sees committed files) | 0 errors, 0 warnings, 0 informations |
| `task test` | **4773 passed**, 2 skipped, 1 xfailed |
| Coverage | `sign_token_base.py` and `token_schemas_signs.py` both **100%** |
| flake8 (120 cols) | clean |
| mypy | Success |
| `qlty smells --include-tests` | no findings |
| `task lint-md` | 0 errors over 35 files |

Checked the suite actually post-dates the fix rather than assuming: the test file was last written at 10:19:38, the suite log finished at 10:33:35.

### Steps 9–10 — commit and push

The user asked, in their own words, to commit all changes and push. That authorizes exactly one commit and one push of the changes under discussion. Continued this task's existing TODO/log rather than opening new ones: this is step 10 of the TODO already written, and new task files would only add to the B1 artefact count, which is itself an open finding.
