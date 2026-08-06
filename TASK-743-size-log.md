# TASK-743-size — Work Log

## Task

Two follow-ups requested by the user:

1. Decide the best way to address mypy **without** involving the project
   virtualenv.
2. Split the oversized files, since they are touched by PR #743.

Starting point: `4ab29000` plus the uncommitted `TASK-743-fixes` work. Nothing
is to be committed.

## 1. mypy without touching the venv — resolved

The two remaining `Library stubs not installed for "requests"` errors came
from `mypy` being a global pipx install that cannot see the project
virtualenv. The earlier attempt to fix this by adding `mypy` to the project's
dev dependencies was reverted, because the venv copy of mypy resolves `lark`
and `marshmallow` and so surfaced 24 additional errors that were never part of
the request.

**Chosen solution: inject the stubs into the pipx mypy environment.**

```sh
pipx inject mypy types-requests
```

Result, verified:

- The 2 `import-untyped` errors are gone.
- **No new errors appeared.** mypy across the original 31-file error set is
  now **0 errors, down from the 42 baseline.**
- Nothing in the repository changes — no `pyproject.toml`, no `poetry.lock`,
  no `mypy.ini`. The project toolchain is untouched, so the gate still means
  exactly what it meant before.

Across all 46 files PR #743 touches, mypy reports **0 errors**. Five errors do
appear in `ebl/atf_importer/**`, but each was checked against the PR file list
and is a transitively-imported module the PR does not touch, so they are
outside the "changed modules" gate. They are pre-existing.

Trade-off worth stating: this is a **machine-local** fix. It is not recorded
in the repo, so CI and other developers do not inherit it. The reproducible
alternative is to adopt mypy as a project dependency — but that is a genuine
toolchain change that surfaces 24 further errors, and it should be a separate,
deliberate decision rather than a side effect of this PR. It is reversible
with `pipx uninject mypy types-requests`.

## 2. Oversized files touched by the PR

Determined from the union of the committed branch diff (`master...HEAD`) and
the uncommitted working tree — 46 `.py` files in total, of which six exceed
250 lines:

| file | lines |
| --- | --- |
| `ebl/tests/factories/fragment.py` | 718 |
| `ebl/transliteration/domain/tokens.py` | 368 |
| `ebl/fragmentarium/retrieve_annotations.py` | 323 |
| `ebl/corpus/web/chapter_schemas.py` | 286 |
| `ebl/transliteration/domain/sign_tokens.py` | 278 |
| `ebl/transliteration/domain/enclosure_visitor.py` | 268 |

## Progress

- Created `TASK-743-size-todo.md` and this log before starting work.

## How each file was split

Every split follows the same rule: **the public import path keeps working**,
so no caller outside the file had to change unless it was genuinely wrong.
Two mechanisms achieve that, and neither is a suppression:

1. Where the parent module still *uses* a moved name (e.g. `tokens.py` uses
   `TokenVisitor` in every `accept()` signature), the import is genuinely
   live, so re-export happens naturally and ruff sees no unused import.
2. Where it does not, the module declares an explicit `__all__`. Pyflakes and
   ruff both treat names in `__all__` as used, so this is a documented public
   surface rather than a silenced warning.

Layering was chosen to avoid circular imports in every case: the base module
never imports its dependants.

### `tokens.py` 368 → 192

- `token_base.py` (186) — `TokenVisitor`, `ErasureState`, `Token`,
  `ValueToken` and the `T`/`VT` type variables.
- `tokens.py` (192) — the concrete tokens. It imports the base names, all of
  which it actually uses, so every existing `from ...tokens import X` still
  resolves.

This started as a three-way split with `TokenVisitor` in its own
`token_visitor.py`. That module needed `Token` for one annotation, which meant
a `TYPE_CHECKING` import — **a line that can never execute, and therefore a
new uncovered line that I had introduced.** Rather than hide it behind a
`# pragma: no cover`, `TokenVisitor` was merged into `token_base.py` beside
`Token`, so the forward reference resolves in-module and the unexecutable
import disappears. `token_base.py` is 186 lines, comfortably inside the gate.

One real fix fell out: `EnclosureType` used to leak out of `tokens.py` as an
incidental re-export. `test_note_line.py` now imports it from its real home,
`enclosure_type.py`.

### `sign_tokens.py` 278 → 126

- `sign_token_base.py` (70) — `AbstractSign`, `NamedSign`, `NameParts`.
- `named_signs.py` (120) — `Reading`, `Logogram`, `Number`.
- `sign_tokens.py` (126) — `Divider`, `Grapheme`, `CompoundGrapheme`, plus an
  `__all__` re-export. `Reading` alone has 42 importers, so preserving the
  import path mattered more than moving 42 call sites.

### `enclosure_visitor.py` 268 → 114

- `enclosure_state.py` (46) — `EnclosureVisitorState`.
- `enclosure_updater.py` (149) — `EnclosureUpdater` and `set_enclosure_type`.
- `enclosure_visitor.py` (114) — `EnclosureValidator`, re-exporting the other
  two through `__all__`.

### `chapter_schemas.py` 286 → 169

- `chapter_manuscript_schemas.py` (139) — the manuscript-side schemas.
- `chapter_schemas.py` (169) — the line and chapter schemas. It genuinely uses
  `ApiManuscriptLineSchema`, `ApiManuscriptSchema` and `MuseumNumberString`.

### `retrieve_annotations.py` 323 → 148

- `retrieve_annotations_helpers.py` (188) — the annotation processing.
- `retrieve_annotations.py` (148) — `main()` and the `__main__` guard, which
  deliberately stayed put so
  `python -m ebl.fragmentarium.retrieve_annotations` keeps working.

`test_retrieve_annotations.py` needed two real updates: it imported
`BoundingBox` from this module (an incidental re-export — now imported from
`fragmentarium.domain.annotation`), and it stubbed
`when(retrieve_annotations).write_annotations(...)`. Since `create_annotations`
now calls `write_annotations` from the helpers module's namespace, the stub had
to move to that module or it would no longer intercept the call. That test
failed first and was fixed — it was a genuine consequence of the move, not a
flake.

### `ebl/tests/factories/fragment.py` 718 → 147

This file was dominated by two 195-line `text = Text(...)` fixtures.

- `fragment_metadata_factories.py` (164) — join, script, date, external
  number, dossier and acquisition factories.
- `transliterated_fragment_lines.py` (160) — the first 4 of the 22 text lines.
- `transliterated_fragment_text.py` (110) — assembles
  `TRANSLITERATED_FRAGMENT_TEXT`.
- `lemmatized_fragment_text.py` (249) — `LEMMATIZED_FRAGMENT_TEXT`.
- `fragment.py` (147) — the four factories, plus `__all__` re-exports so all
  49 importers of `FragmentFactory` and 32 of
  `TransliteratedFragmentFactory` are untouched.

The transliterated text needed the extra `_lines` module because the constant
plus its imports came to 254 lines — 4 over the gate.

**Verified equal, not merely passing:** the pre-split file was loaded
side-by-side with the new one and compared attribute by attribute.
`TransliteratedFragmentFactory.text`, `LemmatizedFragmentFactory.text`,
`signs`, `line_to_vec` and `InterestingFragmentFactory.uncurated_references`
are all `== True` against the originals.

## Gate results

- `task format` — **PASS**, 821 files, exit 0.
- `task lint` (ruff) — **PASS**.
- `task type` (pyre, the CI gate) — **PASS**, no type errors found.
- `task type-pyright` — **PASS**, 0 errors / 0 warnings.
- `task test` — **PASS**, **4251 passed**, 2 skipped, 1 xfailed, 0 failures —
  the same count as before the splits, so nothing was lost or silently skipped.
- `flake8 --max-line-length=120` over all 60 PR-touched files — **PASS**.
- `mypy --ignore-missing-imports` over all 60 PR-touched files — **0 errors**.
- `task lint-md` — **PASS**.
- **No `.py` file touched by PR #743 exceeds 250 lines.**

Broad pyright over the PR-touched files still reports 149 errors — exactly the
same number as before this task began (and down from 158 at `HEAD`). The
splits introduced none.

## Runtime verification

Booted the real Falcon app against a locally-pinned Mongo, with `get_app()`
bypassed so Sentry never initialises, and the throwaway database dropped after.

- App boots; all route modules register.
- `/signs?value=ku&subIndex=1` → 200, `?listAll=true` → 200,
  `?subIndex=notanumber` → 422, `/signs/transliteration/ku-nu-szi` → 200.
- Every public name still imports from `tokens`, `sign_tokens`,
  `enclosure_visitor` and `chapter_schemas`.
- The ATF parser — which exercises all the split token modules together —
  parses `1. ku-nu-szi`, `2. |KU.NU|`, `3. {d}INANNA`, `4. [ku]-nu-szi`.
- `set_enclosure_type` still works through its re-export.
- The factories build: 22 text lines for both the transliterated and
  lemmatized fixtures.

**Nothing has been committed.**

## Reminder

All six TASK docs (`TASK-743-merge-*`, `TASK-743-fixes-*`, `TASK-743-size-*`)
must be removed before PR #743 is merged.

## Coverage: the splits introduced no new uncovered lines

Moving code moves its coverage with it, so the check that matters is whether
the **miss count per group** is unchanged. It is, exactly:

| group | before the split | after |
| --- | --- | --- |
| `tokens` (+ `token_base`) | 244 stmts / 7 miss | 247 / **7** |
| `sign_tokens` (+ `sign_token_base`, `named_signs`) | 149 / 1 | 163 / **1** |
| `enclosure_visitor` (+ `state`, `updater`) | 170 / 0 | 186 / **0** |
| `chapter_schemas` (+ `chapter_manuscript_schemas`) | 129 / 9 | 135 / **9** |
| `retrieve_annotations` (+ helpers) | 146 / 31 | 150 / **31** |

Statement counts rise slightly because each new module adds import statements,
and those execute on import, so they are covered. Every remaining uncovered
line is a pre-existing gap that simply moved to a new file; none is a line this
task wrote.

The single exception was caught and removed rather than excused: the
`TYPE_CHECKING` import in the original `token_visitor.py` took the `tokens`
group from 7 misses to 8. Merging `TokenVisitor` into `token_base.py` brought
it back to 7.

Final full suite: **4251 passed**, 2 skipped, 1 xfailed, **0 failures** — the
same count as before any of this work.
