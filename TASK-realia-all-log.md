# TASK-realia-all — Work Log (fix: reallexikon reference null-check)

## Problem found via live verification

Ran the committed rule against the live `ebldev` collection (24,361 docs) and
compared its included set against the domain/frontend rule:

- domain rule → excluded 21 stubs
- committed `$expr` → excluded **0** (included everything)

Root cause: `reallexikon.reference` is stored in three shapes —
`dict_with_id` (9222), `dict_without_id` (510), and null. The frontend/domain
deserializer (`ReallexikonReferenceField._from_id`) treats a reference **dict
without an `id`** (and an empty string) as **null**, but the committed Mongo
check `reference != null` counted those 510 dicts as real references. Each of
the 21 true stubs owns such a dict, so the rule saw "own content" and kept them.

## Fix

`_reallexikon_reference_count` now counts a reference as resolvable only when it
matches the domain rule, via `_is_resolvable_reference`:

- string → non-empty, or
- object → has a non-empty `id`,
- otherwise not a reference.

## Verification

Re-ran the same diff over all 24,361 live docs:

- domain rule → 24,340 included / 21 excluded
- fixed `$expr` → 24,340 included
- disagreements: **0 kept-stubs, 0 dropped-real** (exact parity both directions)

## Tests

Extended `test_list_all_realia_excludes_redirect_stubs` with the shapes that
caused the bug: reallexikon reference as a dict without `id` and as an empty
string are stubs (excluded); reallexikon reference as a non-empty string is own
content (included). Existing null / dict-with-id cases retained.

## Gates

- `ruff format` unchanged · `flake8` clean · `mypy` clean on changed files ·
  100% coverage on all 4 realia modules · files < 250 lines · `task lint-md`
  clean · `task test` full suite (see terminal).

> Remove this file (and `TASK-realia-all-todo.md`) before the PR is merged.
