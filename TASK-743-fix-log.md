# TASK-743-fix — Address the review findings on PR #743 — Work Log

## Task

Apply every finding from `TASK-743-review.md` to the working tree:
F1 (nameParts schema per call), F2 (qlty 6-parameter regression),
F3 (CodeQL `...` regression), F4 (nine unparameterized generics),
F5 (PR description overstates the `__all__` facades), F6 (no action),
F7 (`_tree_to_string` silent `"None"`), F8 (`NamePart` invariant),
F9 (three nits).

## Log

### Step 1 — Task tracking files created

Created before touching any code, per the task-tracking hard gate. This is a
separate task from the review, so it gets its own pair of files rather than
reusing `TASK-743-todo.md` / `TASK-743-log.md`.

Starting state: working tree clean apart from the three TASK-743 review docs.
Branch `fix-type-checker-blind-spots` at `b5d807ed`.

### Step 2 — Config inspected before touching bodies/branches

`.coveragerc`: `omit = ebl/tests/*`, `exclude_lines = @abstractmethod,
@abc.abstractmethod`. **No `branch = true`** — statement coverage only, so a
new `if` filter needs its statements executed but not both arms. Abstract
method bodies are excluded, which is why `token_base.py`'s
`raise NotImplementedError` blocks do not cost coverage.

No `.qlty/qlty.toml` — qlty runs on defaults. Observed threshold: `of` with
5 parameters is not flagged, `_create` with 6 is, so the limit is 5.

### Step 3 — F1 applied, and MY REVIEW NUMBER WAS WRONG

Applied the fix: `token_schemas_signs` now holds one lazily-created
module-level schema behind `_get_token_schema()`, so `_dump_name_parts` and
`_load_name_parts` no longer construct `OneOfTokenSchema()` (or re-execute an
import) per named sign.

**Error in my review, found while verifying the fix.** I reported F1 as a
2.65x slowdown. That number was an artefact of my benchmark. To build the
"cached" comparison I replaced `type_schemas["Reading"]` — a schema *class* —
with a pre-built *instance*. `marshmallow_oneofschema` instantiates a
sub-schema on every dump when a class is registered, so my "fix" side was
also getting that unrelated optimisation for free.

Re-measured with the confound removed (identical structure on both sides,
differing only in whether `_get_token_schema()` rebuilds):

| Variant | ms / 200 readings |
| --- | --- |
| schema rebuilt per named sign (as merged) | 43.46 |
| one cached instance (as fixed) | 41.86 |
| **true speed-up from F1** | **1.04x** |

Separately measured, and **pre-existing on master, not caused by PR #743**:

| Variant | ms / 200 readings |
| --- | --- |
| `OneOfSchema` with the sub-schema class | 40.33 |
| `OneOfSchema` with a sub-schema instance | 17.69 |
| ratio | 2.28x |

So the real 2.3x sits in `OneOfSchema`'s per-call sub-schema construction,
which master does too and which this PR does not touch.

**Consequence:** F1 keeps its fix (it is still strictly better code and drops
a per-call import) but is downgraded Medium -> Low, and the review document
must be corrected. The 2.28x observation is recorded as out-of-scope
information, not as a finding against this PR.

### Step 4 — F2, verified with the qlty CLI

A classmethod was my first attempt. I ran the local qlty binary
(`~/.qlty/bin/qlty smells`) against it and **qlty counts `cls`**, so
`cls` + 5 parameters still reported `count = 6`. Rather than guess, I
switched to a bundled `NamedSignArguments` frozen attrs value object;
`NamedSign._create(cls, arguments)` is 2 parameters and qlty now reports
nothing for either module.

`.qlty/qlty.toml` had to exist for the CLI to run. The root `.gitignore`
ignores `.qlty/` entirely, so creating it was invisible to git; it was
deleted again afterwards. No tracked configuration file was created or
modified.

### Step 5 — F3, F4, F7, F8, F9a, F9b applied

- **F3**: the two `TransformerInternals` protocol members now carry
  `@abstractmethod` and `raise NotImplementedError`, matching how round 2
  resolved the identical CodeQL alert on `SignsCollectingVisitor`. I checked
  `.coveragerc` first: `exclude_lines` contains `@abstractmethod`, so the
  bodies are excluded and this costs no coverage — the same mechanism that
  keeps `token_base.py` at 100%.
- **F4**: all nine unparameterized generics replaced with precise types
  (`Sequence[Token]`, `List[Dict[str, Any]]`, `Dict[str, Any]`,
  `List[object]`). `List[object]` for `_flatten_grapheme_elements` is
  deliberate: the elements are genuinely heterogeneous lark products, and
  `object` forces callers to narrow where bare `list` (implicit `Any`) did
  not.
- **F7**: `_tree_to_string` now skips `None` children.
- **F8**: `name_contribution_of` extracted, and `NamePart.name_contribution`
  validates against its token, so the invariant is structural.
- **F9a**: `commit_value` -> `_commit_value`.
- **F9b**: the two `domain.fragment` imports merged.

### Step 6 — Tests added

- `ebl/tests/atf_importer/test_atf_indexing_visitor.py` (new): five tests
  covering `_tree_to_string`, including the placeholder case F7 fixes, plus
  `reset`.
- `ebl/tests/transliteration/test_name_part.py`: two tests for the F8
  validator.

**Error and recovery.** My first version of the indexing-visitor test built
lark objects with `Tree(...)` / `Token(...)` directly and produced 12 pyright
errors — lark ships `py.typed` with constructor signatures the library does
not honour. That is precisely why this PR added `create_token` / `create_tree`.
Rewrote the test to use those factories: 0 pyright errors, and it dogfoods the
new module.

### Step 7 — F5 and F9c: asked the user, both approved

- **F5**: user chose "I edit the PR body". Patched the description via
  `gh api repos/.../pulls/743 -X PATCH -F body=@file` (the `gh pr edit --body`
  path fails silently in this environment). Verified the new text is live.
- **F9c**: user explicitly approved deleting
  `test_base_visitor_visiting_a_manuscript_is_a_no_op`. The surviving test
  visits both a `Manuscript` and a `ManuscriptLine`, so no assertion is lost.

### Step 8 — F6: no action, by design

Recorded as flagged-and-accepted. `Branch`/`TreeChild` describe lark's own
`Tree.children`, a third-party shape this project does not own.

### Step 9 — Gates after the changes

| Gate | Result |
| --- | --- |
| `task format` | 844 files already formatted |
| `task lint` (ruff) | All checks passed |
| `task type` (pyre) | No type errors found |
| `pyright` on the 15 touched files | 0 errors, 0 warnings, 0 informations |
| `task test` | 4385 passed, 2 skipped, 1 xfailed (553 s) |
| diff coverage | 100% — 0 uncovered among 1145 added/modified lines |
| `flake8 --max-line-length=120` | 0 errors |
| `mypy --ignore-missing-imports` | 0 errors |
| `task lint-md` | 0 errors |
| 250-line limit | largest touched file 216 lines |
| >120-char lines | none |
| qlty (local CLI) | no smells on the touched sign modules |

### Step 10 — Re-verification after the rewrite

The earlier verification run is void once code is reworked, so all of it was
repeated against the current tree:

- `nameParts` wire format over 20 ATF inputs: **identical to master**.
- `Museum` enum: **identical to master**, 72 members.
- Service rebooted on 127.0.0.1:8001 against a throwaway local Mongo
  (`.env` not sourced). 20 routes re-exercised, all matching the pre-fix
  results: 422 on unparsable transliteration, 200 on the erasure case, three
  dispatcher keys, dispatcher error path, sign search/order, markup, corpus
  query, `/texts`, `/provenances`.
- A fragment with `k[ur]`, a surrogate logogram, a determinative and an
  erasure inserted and fetched via `GET /fragments/X.1`: `nameParts` served
  with `ValueToken, BrokenAway, ValueToken` ordering intact.

### Step 11 — Review document corrected

`TASK-743-review.md` updated: F1 rewritten with the corrected magnitude and a
corrected reproduction script (the old one is explicitly marked as not to be
used), severity moved Medium -> Low, summary/findings/severity/recommendation
tables adjusted, and a `Resolution` section added recording what happened to
each finding.

### Step 12 — Cleanup

Server stopped, throwaway database dropped, master worktree removed,
`.coverage` deleted, temporary `.qlty/qlty.toml` deleted. Working tree holds
only the intended source changes plus the five TASK-743 markdown files.

**Nothing has been committed or pushed.** The only outward-facing action was
the PR description edit, which the user explicitly approved.
