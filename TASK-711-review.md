# TASK-711 — Review: Extend date metadata (PR #711)

- PR: <https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/711>
- Branch: `date-structure-revision` → `master`
- Head commit reviewed: `78286d6c` ("Format & clean up")
- Review decision on GitHub: **CHANGES_REQUESTED** (Fabdulla1)
- Local verification: `poetry run pytest ebl/tests/fragmentarium/test_date.py ebl/tests/fragmentarium/test_fragment_date_route.py ebl/tests/fragmentarium/test_dates_in_text_route.py` → **25 passed**, coverage on [ebl/fragmentarium/domain/date.py](ebl/fragmentarium/domain/date.py) = **100%**.

---

## Summary

The PR adds two structured metadata flags (`is_reconstructed`, `is_emended`) to the `Year` domain object and its Marshmallow schema, plus a parser that strips wrapper symbols (`<…>`, `[…]`, `(…)`) and trailing markers (`!`, `?`) from the raw `value` string and lifts them into the corresponding boolean flags. Test factory and unit tests are updated; coverage on the changed file is 100%.

The PR previously included three working `TASK-001-*.md` files at the repo root; the most recent commit (`78286d6c`) deleted them. The mandatory PR-task documentation (todo / log / review) per the project instructions is therefore currently absent from the branch and needs to be re-added (this review file is one of them).

---

## Findings

### F1 — `<5>?` / `<5>!` / `[5]?` mixed markers are not normalized (CARRY-OVER, unresolved)

Original review: Fabdulla1, [PR #711 comment r3194933127](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/711#discussion_r3194933127), 2026-05-06. Status: **NOT addressed**.

**Severity: High (correctness / data integrity).**

The wrapper rules are evaluated first, then the trailing-marker rules. Because the wrapper match requires the string to *both* `startswith(start)` *and* `endswith(end)`, a value like `<5>?` does not match any wrapper rule (it ends with `?`, not `>`). The trailing-marker pass then strips `?` and sets `is_uncertain=True`, leaving `value="<5>"` with the `<…>` brackets still embedded and `is_reconstructed` never set. The wrapper pass is not re-run after stripping the trailing marker.

**Reproduction (locally executed):**

```python
from ebl.fragmentarium.domain.date import YearSchema

YearSchema().load({"value": "<5>?"})
# Year(value='<5>', is_broken=None, is_uncertain=True, is_reconstructed=None, is_emended=None)

YearSchema().load({"value": "<5>!"})
# Year(value='<5>', is_broken=None, is_uncertain=None, is_reconstructed=None, is_emended=True)

YearSchema().load({"value": "[5]?"})
# Year(value='[5]', is_broken=None, is_uncertain=True, is_reconstructed=None, is_emended=None)
```

Per the (deleted) [TASK-001-BUG-3-api-instructions.md](TASK-001-BUG-3-api-instructions.md) the API "should detect the wrapper or symbol in the string value" and "store the cleaned numeric value (with wrapper/symbol removed) in the value field." The current behavior leaves a half-cleaned, half-flagged `Year` and persists the bracketed string to MongoDB, which is exactly the inconsistency the structured metadata model was meant to eliminate.

**Recommendation:** replace the two ordered passes with a single **iterative peel loop** that strips one layer per iteration (trailing marker *or* matched wrapper) until no rule fires. This handles arbitrary nesting/order — `[(5!)]?`, `([5?])!`, `[<(5)>]`, `<<5>>` — uniformly, and is *more compact* than the current six-helper design. Concretely:

```python
_WRAPPERS = {
    "<": (">", "is_reconstructed"),
    "[": ("]", "is_broken"),
    "(": (")", "is_uncertain"),
}
_TRAILING_MARKERS = {"!": "is_emended", "?": "is_uncertain"}


def _parse_year_value(data: dict) -> dict:
    data = dict(data)
    value = data.get("value", "")
    while value:
        if len(value) > 1 and value[-1] in _TRAILING_MARKERS:
            key = _TRAILING_MARKERS[value[-1]]
            value = value[:-1]
            if data.get(key) is None:
                data[key] = True
            continue
        if len(value) > 2 and value[0] in _WRAPPERS:
            end, key = _WRAPPERS[value[0]]
            if value.endswith(end):
                value = value[1:-1]
                if data.get(key) is None:
                    data[key] = True
                continue
        break
    data["value"] = value
    return data
```

Verified locally with a prototype — all of the following yield `value="5"` plus the expected union of flags:

| Input        | Flags set                                       |
| ------------ | ----------------------------------------------- |
| `<5>?`       | `is_reconstructed`, `is_uncertain`              |
| `<5>!`       | `is_reconstructed`, `is_emended`                |
| `[5]?`       | `is_broken`, `is_uncertain`                     |
| `[(5!)]?`    | `is_broken`, `is_uncertain`, `is_emended` (+ outer `?` → `is_uncertain` already set) |
| `([5?])!`    | `is_uncertain`, `is_broken`, `is_emended`       |
| `[<(5)>]`    | `is_broken`, `is_reconstructed`, `is_uncertain` |
| `<<5>>`      | `is_reconstructed` (idempotent)                 |
| `<>` `[]` `()` `!` `?` `""` | left unchanged, no flags set     |

Why **not** a single regex:

- A single non-iterative regex such as `^([<\[(])?(.*?)([>\])])?([!?])?$` only handles **one** wrapper layer + **one** trailing marker, so `[(5!)]?` is still mis-parsed.
- The wrappers form **matched pairs** (`<…>`, `[…]`, `(…)`); honouring "match" requires either a back-reference table (Python's `re` cannot conditionally pair `<` with `>` only and `[` with `]` only without alternation explosion) or an iterative pattern. Iterating *with regex* gives no gain over the string-slicing version above and adds compile cost.
- Recursive regex (`regex` module) would work but introduces a non-stdlib dependency for a 10-line problem.

The iterative-peel approach is therefore both the most compact *and* the most efficient (`O(n)` slicing, one pass per layer, no regex compilation).

Add explicit unit tests for the table above plus the degenerate inputs (`<>`, `[]`, `()`, `!`, `?`, `""`) and the explicit-`False` override case from F4. Fabdulla1's request for mixed-marker tests is satisfied by this set.

---

### F2 — Legacy DB values are silently rewritten on read (NEW)

**Severity: High (data integrity / spec violation).**

`DateSchema().load(...)` is invoked not only on incoming HTTP payloads but also when fragments are read from MongoDB — see [ebl/fragmentarium/infrastructure/mongo_fragment_repository_get_extended.py:182](ebl/fragmentarium/infrastructure/mongo_fragment_repository_get_extended.py#L182):

```python
return DateSchema(unknown=EXCLUDE).load(date)
```

Because `_parse_year_value` mutates `data["value"]` and sets the new flags during `@post_load`, every existing legacy fragment whose stored year value is e.g. `"<5>"`, `"5!"`, `"[5]"`, `"(5)"`, or `"5?"` is transformed into `value="5" + flag` the moment it is loaded. Any subsequent re-save of that fragment (via the existing fragment update flow that round-trips through `DateSchema().dump(...)`) writes the cleaned form back to MongoDB, irreversibly overwriting the original raw value.

This directly contradicts the explicit migration policy stated in the (deleted) [TASK-001-BUG-3-api-instructions.md](TASK-001-BUG-3-api-instructions.md):

> Do **not** remove or overwrite legacy raw values in this migration. Only add support for the new fields and ensure robust parsing.

**Reproduction:** load any legacy fragment whose `date.year.value` contains a wrapper symbol; observe that `Date.year.value` is the stripped form. Trigger any fragment update; the `fragments` MongoDB document is rewritten with the stripped year value.

**Recommendation:** either

1. Restrict parsing to the inbound HTTP boundary (e.g. perform `_parse_year_value` only inside the route layer, not in `YearSchema.@post_load`), so DB reads stay byte-faithful; or

2. Preserve the original raw string in a separate field (e.g. `original_value`) and emit it back on dump until an explicit one-time migration script converts the data [<-- implement this]; or
3. Provide and run the migration script the original task description called for, *then* enable on-load parsing.

A test should be added that loads a fragment containing a legacy `value` with wrappers via `MongoFragmentRepository.query_by_…` (or the schema directly mimicking the read path) and asserts the round-trip behavior matches the chosen policy.

---

### F3 — Sourcery review feedback not addressed (CARRY-OVER, unresolved)

Sourcery-AI review on commit `de4694cf`, 2026-04-30. Status: **NOT addressed**.

**Severity: Medium.**

a. `_parse_year_value` mutates the `data` dict provided by Marshmallow. Marshmallow does not currently re-share the dict, but the function is also exported as a free helper; using a shallow copy (`data = dict(data)`) is a small, safe defensive change.

b. The precedence and short-circuit semantics of the wrapper- and trailing-marker rules are encoded only by the order of items in the two lists. There is no docstring explaining that ordering matters, and re-ordering the lists silently changes behavior. Add a short docstring to `_parse_year_value` (and to the two helpers) stating the intended evaluation order and the guarantee that only the first matching rule of each pass is applied.

c. Sourcery noted the `TASK-001-*.md` files at the repo root might not belong in the source tree long-term. They have since been deleted in `78286d6c`, removing the project's own work-log/todo trail required by [.github/instructions/copilot.instructions.md](.github/instructions/copilot.instructions.md). The repo *requires* those files for any task; the right fix is not to delete them but to keep them under a consistent location (or `.gitignore` if you maintain them only locally during the PR life-cycle and remove pre-merge).

---

### F4 — `isReconstructed: false` still strips wrappers (NEW)

**Severity: Medium (semantics / surprising behavior).**

`_set_flag_if_missing` only writes the flag when it is `None`, but the value-rewriting branch in `_apply_wrapped_value_rule` runs unconditionally. As a result:

```python
YearSchema().load({"value": "<5>", "isReconstructed": False})
# Year(value='5', ..., is_reconstructed=False, ...)
```

The caller explicitly disclaimed the reconstruction flag, yet the value `"<5>"` is silently mutated into `"5"`. Either both the strip and the flag should be skipped when an explicit `False` is provided, or `False` should be treated as an explicit override and the brackets retained. The current test [ebl/tests/fragmentarium/test_date.py](ebl/tests/fragmentarium/test_date.py) `test_year_schema_structured_metadata_takes_priority_over_wrapper` *asserts* this surprising behavior, so the test would need updating along with the fix.

**Recommendation:** in each rule, perform the strip **only** if `data.get(key) is None`; if the caller has set the flag (true *or* false), leave `value` untouched.

---

### F5 — Empty/missing `value` silently accepted (NEW, low)

**Severity: Low.**

`_parse_year_value` writes `data["value"] = data.get("value", "")` before any rule runs. Combined with `value = fields.String()` (no `required=True`), `YearSchema().load({})` succeeds and produces `Year(value='')`. This was previously also true (the old code accepted `{}` because `value` is not required), but the new helper now also forcibly *materialises* the empty string into the dict, ensuring it is passed to `Year(...)`. If the API contract requires `value`, mark the field `required=True`. Otherwise, document that an empty string is the canonical "no value".

---

### F6 — Marker rules are positional but not anchored to digits (NEW, low)

**Severity: Low.**

`_apply_trailing_marker_rule` only checks that the value `endswith(marker)` and is longer than the marker. It will therefore "parse" inputs that the (deleted) instructions list as legitimate non-numeric spellings — for example `n+!`, `x?`, `n-n!`, `n[a-z]!`. The cleaned value retained after stripping is itself non-numeric, so no validation catches the case. Consider either (a) only parsing when the residual value matches a digit pattern, or (b) explicitly documenting that the parser is intentionally lenient and any string ending in `!`/`?` is interpreted as emended/uncertain.

---

### F7 — Test coverage gaps (NEW, medium)

**Severity: Medium.**

Although line coverage on [ebl/fragmentarium/domain/date.py](ebl/fragmentarium/domain/date.py) is 100%, the *behavioral* coverage misses cases that the implementation would otherwise have exercised:

- Mixed-marker patterns (`<n>?`, `<n>!`, `[n]?`, `[n]!`, `(n)?`, `(n)!`) — see F1.
- The `value > len(start) + len(end)` guard in `_apply_wrapped_value_rule`: degenerate inputs `"<>"`, `"[]"`, `"()"`, `"!"`, `"?"` are not asserted.
- Round-trip via `DateSchema().load` on a payload representing legacy DB shape (see F2).
- The `_parse_year_value` empty/missing-`value` case (F5).
- `MonthSchema` / `DaySchema` should *not* accept `isReconstructed`/`isEmended`. A negative test would lock that contract.

Per [.github/instructions/copilot.instructions.md](.github/instructions/copilot.instructions.md) the project requires "100% coverage on affected code" — that bar is met for line coverage but the request from Fabdulla1 to add mixed-marker tests is still outstanding.

---

### F8 — Mandatory task documentation files were removed (PROCESS, blocking for merge gate)

**Severity: Medium (process gate).**

The last commit (`78286d6c`) deletes `TASK-001-BUG-3-api-instructions.md`, `TASK-001-log.md`, and `TASK-001-todo.md`. The repository's own [.github/instructions/copilot.instructions.md](.github/instructions/copilot.instructions.md) mandates a `TASK-<id>-todo.md` and `TASK-<id>-log.md` per task and a `TASK-<id>-review.md` per review, and asks for those to be present until just before merge. They should be reinstated (or recreated under the PR id, e.g. `TASK-711-todo.md` / `TASK-711-log.md`) and a final reminder added to delete them as part of the merge step.

---

## Severity summary

| ID  | Title                                                     | Severity | Status                          |
| --- | --------------------------------------------------------- | -------- | ------------------------------- |
| F1  | Mixed wrapper + trailing marker not normalized            | High     | Carry-over (Fabdulla1) — open   |
| F2  | Legacy DB values silently rewritten on read               | High     | New                             |
| F3  | Sourcery review feedback (mutation, ordering, doc layout) | Medium   | Carry-over (Sourcery-AI) — open |
| F4  | `isReconstructed: false` still strips wrappers            | Medium   | New                             |
| F5  | Empty/missing `value` silently accepted                   | Low      | New                             |
| F6  | Trailing markers not anchored to digit content            | Low      | New                             |
| F7  | Behavioral test gaps (mixed markers, edge cases, RT)      | Medium   | Carry-over (Fabdulla1) — open   |
| F8  | Required task documentation files removed                 | Medium   | Process                         |

---

## Reproduction Steps (consolidated)

```bash
poetry run pytest \
  ebl/tests/fragmentarium/test_date.py \
  ebl/tests/fragmentarium/test_fragment_date_route.py \
  ebl/tests/fragmentarium/test_dates_in_text_route.py \
  --cov=ebl.fragmentarium.domain.date --cov-report=term-missing
# 25 passed; coverage 100% on date.py

poetry run python - <<'PY'
from ebl.fragmentarium.domain.date import YearSchema
for v in ["<5>?", "<5>!", "[5]?", "(5)?", "<5>"]:
    print(v, "->", YearSchema().load({"value": v}))
print("explicit-False:", YearSchema().load({"value": "<5>", "isReconstructed": False}))
print("missing-value:", YearSchema().load({}))
PY
```

The first script confirms tests/coverage as currently committed. The second reproduces F1, F4, and F5.

---

## Recommendation

**Request changes — do not merge as-is.** Required before merge:

1. **Fix F1**: replace the two ordered passes with the iterative peel loop shown in F1 (handles arbitrary nested/mixed combinations such as `[(5!)]?` and `([5?])!` in one place). Add unit tests for every mixed combination plus the degenerate inputs (`<>`, `[]`, `()`, `!`, `?`, `""`).
2. **Decide and document F2**: either restrict parsing to the HTTP boundary, preserve the legacy raw value, or land an explicit migration script; whichever is chosen, add a regression test on the DB-read path.
3. **Fix F4**: respect explicit `False` for the new flags by skipping value rewriting when the flag is non-`None`. Update the existing test that locks the surprising behavior.
4. **Address Sourcery feedback (F3)**: shallow-copy `data`, add a short docstring describing rule precedence; restore (or reformulate) the task documentation files.
5. **Reinstate task-tracking docs (F8)**: add `TASK-711-todo.md` and `TASK-711-log.md`, keep them current, and remove just before merge along with this review file.

Optional but recommended: F5 (require `value` or document empty-string semantics) and F6 (anchor trailing-marker parsing to numeric content). Maintain 100% coverage after the fixes.

---

**Reminder:** Per [.github/instructions/copilot.instructions.md](.github/instructions/copilot.instructions.md), this review file (`TASK-711-review.md`) and the corresponding `TASK-711-todo.md` / `TASK-711-log.md` should be deleted from the repository immediately before the PR is merged.
