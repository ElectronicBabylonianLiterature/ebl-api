# TASK-743 — Review of PR #743

**PR:** [#743 Make the ATF parser visible to the type
checkers](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743)
**Branch:** `fix-type-checker-blind-spots` -> `master`
**Head:** `19a2f464` · **Base:** `32f6ddae` · 82 files changed

## Status: all findings addressed

Every finding below has been fixed on the working tree (uncommitted). The
original review text is kept for the record; the resolution follows each
finding.

| Gate | Before | After |
| --- | --- | --- |
| `task type-pyright` | **149 errors** | **0 errors** |
| `task type` (pyre) | pass | pass |
| `task test` | 4251 passed | **4308 passed** |
| Uncovered lines on PR-touched code | 30 | **0** |
| 250-line gate | pass | pass |
| `task format` / `task lint` / flake8 | pass | pass |
| `mypy` (changed files) | pass | pass |
| Committed `TASK-743-*` tracking files | 6 | **0** |

Resolutions, in short:

- **F1** — pyright driven to zero structurally: factories moved to the
  `make_factory` convention already clean in `archaeology.py`; the visitor
  decorators made signature-preserving; attrs validators moved to module
  level; explicit `cast` at the pymongo/marshmallow boundaries. No
  suppressions, no config changes.
- **F2** — PR description rewritten on GitHub to cover the file-splitting
  work, and the incorrect "pyre could not be run" claim removed.
- **F3** — the six committed tracking files deleted.
- **F4** — tests added for every relocated module; the two remaining lines
  were provably unreachable defensive guards and were removed.
- **F5** — `TokenVisitor.result` no longer lies; `SignsCollectingVisitor`
  declares `reset()` and `result_string` abstractly.
- **F6** — `__all__` facades added to `retrieve_annotations.py` and
  `chapter_schemas.py`, matching the other split modules.
- **F7** — the unreachable filter is gone; `check_errors` returns the
  validated lines.
- **F8** — no action needed; recorded for the record.
- **F9** — domain-only `NamePart` wrapper. `nameParts` JSON verified
  byte-identical before and after, so the API contract is untouched.
- **F10** — the signs route returns 422 instead of 500, with a test.

Two follow-ups surfaced while fixing, both resolved here:
`mongo_sign_repository.py` (403 lines) and `test_sign_tokens.py` (491 lines)
were pre-existing oversized files pulled into the changed set by F9, so both
were split.

## Summary

The core idea is right and the diagnosis is excellent. A directory named
`atf_parsers/lark_parser/` sitting next to a module `atf_parsers/lark_parser.py`
made mypy and pyright resolve the dotted name to the directory, so the ATF
parser and everything importing it had never been type-checked. Renaming the
grammar directory to `atf_grammar/` and fixing what the checkers then found is
a real and well-argued improvement, and the resulting typing changes are
almost all faithful.

Verified independently, against `origin/master` as the baseline:

| Check | Result |
| --- | --- |
| `task format` (ruff format) | pass |
| `task lint` (ruff) | pass |
| `task type` (**pyre**) | **pass — "No type errors found"** |
| `task type-pyright` | **FAIL — 149 errors** (master baseline: 173) |
| `task test` | pass — 4251 passed, 2 skipped, 1 xfailed |
| `mypy` (changed files) | pass — 5 errors, none in a changed file |
| `flake8 --max-line-length=120` (changed files) | pass — 0 errors |
| 250-line file gate | pass — largest changed file is 249 lines |
| Coverage on changed modules | 97% — 30 gaps in files this PR created |
| Running service, affected routes | pass — see Reproduction Steps |
| CI | green except one `Test Python 3.11` job still pending |

Two structural problems dominate: the PR does far more than its description
says, and it does not satisfy the project's own pre-commit gate 4.

## Findings

### F1. `task type-pyright` fails with 149 errors — Severity: High

Pre-commit gate 4 requires zero pyright errors on changed files. `task
test-all` aborts here with exit 123 and never reaches `test` or `lint-md`.

This is **not a regression**. I built a baseline by checking out
`origin/master` into a worktree, symlinking the project `.venv` (there is no
`pyrightconfig.json` or `[tool.pyright]`, so pyright relies on `.venv`
discovery) and running the same pyright version on master's copies of the
40 changed files that exist there:

- master: **173 errors**
- this branch: **149 errors**

No file regressed. The PR clears pyright in its target files —
`lark_parser.py` 5→0, `legacy_atf_converter.py` 7→0,
`legacy_atf_line_validator.py` 3→0, `sign_tokens.py` 3→0,
`chapter_schemas.py` 4→0, `corpus_search_aggregations.py` 2→0,
`test_app_bootstrap.py` 1→0. The rest are relocations: `fragment.py` 106 →
`fragment.py` 19 + `fragment_metadata_factories.py` 87, exactly 106.

So the branch improves pyright by 24 errors while still failing the
zero-error gate, and 87 of the survivors now sit in a file this PR **created**
(`fragment_metadata_factories.py`). CI does not run pyright — `main.yml`
runs only `ruff check`, `ruff format --check` and `pyre check` — so nothing
mechanical will stop this merging.

**Recommendation:** either drive pyright to zero on the changed set, or record
an explicit, agreed exception for the factory_boy `reportPrivateImportUsage`
family (which the commit message already identifies as needing a suppression
or a pyright setting). Leaving gate 4 silently red is the worst of the three.

### F2. Scope and description are badly out of sync — Severity: Medium

The title, body and Sourcery's guide all describe a focused ~10-file typing
fix. The branch is 82 files. Commit `19a2f464` ("Fix type-checker, lint and
file-size debt across PR #743") added a large body of undocumented work:

- `museum.py` split into `museum_entries_a_l/m_s/t_y.py` (386 lines removed)
- `tokens.py` → `token_base.py`; `sign_tokens.py` → `sign_token_base.py` +
  `named_signs.py`; `enclosure_visitor.py` → `enclosure_state.py` +
  `enclosure_updater.py`
- `tests/factories/fragment.py` (717 lines) split into four modules
- `retrieve_annotations.py` → `retrieve_annotations_helpers.py`
- `chapter_schemas.py` → `chapter_manuscript_schemas.py`
- `lookup_reservations.py` → `lookup_reservation_reconciliation.py`
- new public members on `TokenVisitor` and `@singledispatchmethod` on
  `ChapterVisitor.visit`

None of it appears in the PR body. A reviewer reading the description will
not know to look at any of it.

The body is also wrong on one point: it states `task type` (pyre) "could not
be run" because of a `Worker_exited_abnormally` crash. **Pyre runs clean
here** — `task type` reports "No type errors found". That claim should be
corrected, since it is the gate CI actually enforces.

**Recommendation:** rewrite the description to cover the file-size work, or
split `19a2f464` into its own PR. Correct the pyre claim either way.

### F3. Six task-tracking files are committed to the branch — Severity: Medium

`TASK-743-fixes-{log,todo}.md`, `TASK-743-merge-{log,todo}.md` and
`TASK-743-size-{log,todo}.md` — 1089 lines — are part of the diff. Per the
project instructions these must be removed before the PR is merged. (This
review adds `TASK-743-review{,-todo,-log}.md`, which must go the same way.)

### F4. 30 uncovered statements in files this PR created — Severity: Medium

The coverage gate reads "any line you add, modify, move, or **relocate** must
end at 100% coverage, even if it was uncovered before you touched it."

Running the suite with `--cov` over the changed source modules gives 97%
(81 uncovered of 2878). Thirty of those sit in files this PR created:

| New file | Uncovered |
| --- | --- |
| `ebl/fragmentarium/retrieve_annotations_helpers.py` | 17 |
| `ebl/corpus/web/chapter_manuscript_schemas.py` | 7 |
| `ebl/transliteration/domain/token_base.py` | 5 |
| `ebl/transliteration/domain/sign_token_base.py` | 1 |

I intersected every uncovered line with the diff's added-line ranges: **no
uncovered line in a merely-modified file falls on a line this PR touched.**
The 30 are all relocated code, and the relocation is coverage-neutral —
a targeted run on both trees gives `retrieve_annotations.py` 146 statements /
31 missing on master versus 65+85 statements / 14+17 missing on the branch,
the same 31 lines in two files. qlty agrees: coverage 95.9%, **+0.1%**.

So there is no regression, but the gate as written is not met on relocated
lines.

**Recommendation:** add the missing tests for the four new modules, or agree
explicitly that relocation-only lines are exempt. Do not leave it implicit.

### F5. `TokenVisitor` gained a lying default `result` — Severity: Low

`transliteration_query.py` previously reached into a private attribute:

```python
self.visitor._standardizations = []   # master
self.visitor.reset()                  # branch
```

`self.visitor` is declared `TokenVisitor` (line 35), so both `reset()` and
the pre-existing `self.visitor.result` were type errors. The fix adds to the
`TokenVisitor` ABC in `token_base.py`:

```python
@property
def result(self) -> Sequence:
    return []

def reset(self) -> None:
    return None
```

Replacing the private poke with a real method is the right instinct. But
`result` returning `[]` on the base means any subclass that forgets to
override it silently produces an empty sign list rather than failing — and
an empty sign list feeds `_regexp()`, which builds a search pattern. It is
not reachable today (`TransliterationQueryEmpty` overrides `regexp` and its
`__attrs_post_init__` is a no-op), so this is design risk, not a bug.

The two new tests in `test_token_visitor.py` only assert these trivial
defaults, which is coverage rather than confidence.

**Recommendation:** prefer narrowing the attribute to `SignsVisitor`, or make
`result` `@abstractmethod`, over a base class that answers `[]` for
everything.

### F6. Module surfaces narrowed inconsistently, with no facade — Severity: Low

The splits use two different conventions. `sign_tokens.py` and
`enclosure_visitor.py` keep an `__all__` re-export facade, so their public
names still import from the original path. `retrieve_annotations.py` and
`chapter_schemas.py` do not, and lose names they themselves defined:

- `retrieve_annotations` — `create_annotations`, `write_annotations`,
  `write_fragment_numbers`, `match`, `parse_annotations`,
  `prepare_annotations`, `filter_annotation`, `filter_empty_annotation`,
  `sign_to_sign_ground_truth`, `create_directory`, plus `BoundingBox`
- `chapter_schemas` — `ApiManuscriptSchema`, `ApiManuscriptLineSchema`,
  `ApiOldSiglumSchema`, `MuseumNumberString`

In-repo callers were updated and the suite is green — the PR's own
`test_retrieve_annotations.py` had to be rewritten to chase the new module,
which is the tell. `retrieve_annotations.py` is a CLI entry point, so any
external importer breaks silently.

**Recommendation:** pick one convention. Either add `__all__` facades to both,
or drop them from `sign_tokens.py` and `enclosure_visitor.py` too.

### F7. Unreachable `is not None` filter in `parse_atf_lark` — Severity: Low

```python
check_errors(parsed_pairs)
lines = tuple(line for line, _ in parsed_pairs if line is not None)
```

`parse_line_` returns `(None, error)` only on failure, and `check_errors`
raises if any error is present. After `check_errors` returns, no pair can
have `line is None`, so the guard is never false. Master's
`tuple(pair[0] for pair in lines)` had no guard. The filter is harmless now
but converts a future invariant break into silently dropped lines rather than
a crash.

**Recommendation:** drop the guard, or make the invariant explicit and let it
fail loudly.

### F8. `_StartParser.parse` drops arbitrary Lark options — Severity: Low

`parse(self, text: str, **kwargs: object)` became
`parse(self, text: str, start: Optional[str] = None)`. I grepped every
`*_PARSER.parse(` call site: none passes anything but `text` and `start`, so
this is correct today. It does remove the ability to forward Lark options
such as `on_error` without touching the wrapper. The commit message states
this deliberately; noting it for the record only.

### F9. Data hard gate: `NameParts` is a two-type array — Severity: Info

`sign_token_base.py` (new) contains:

```python
NameParts = Sequence[Union[ValueToken, BrokenAway]]
```

Under the hard gate this is two data types in one array. It is **pre-existing
verbatim** — master has it at `sign_tokens.py:67` — and this PR only
relocated it, but the gate covers "any model you touch".

The honest counter-argument: this is an ordered token stream where the
interleaving *is* the data. A broken reading like `š[u` is
`[ValueToken("š"), BrokenAway.open(), ValueToken("u")]`; two parallel arrays
would lose the positions. Dispatch is by visitor, not by probing an optional
field, so the failure mode the gate targets does not occur here.

**Recommendation:** a decision, not an automatic split. If the gate is to be
applied literally, the fix is a sequence of a single wrapper type carrying the
distinction structurally — a larger change than this PR should absorb.

### F10. Pre-existing 500 on the signs route — Severity: Info (out of scope)

Found while exercising the running service:

```text
GET /signs/transliteration/(((((   ->   HTTP 500
```

`TransliterationError` escapes `get_unicode_from_atf` and is not mapped by
the error handler, so bad input returns 500 instead of 422.
`ebl/signs/web/signs.py`, `mongo_sign_repository.py` and `error_handler.py`
are **untouched** by this PR, and `check_errors` is textually identical to
master, so this is not a regression. Worth a separate issue.

## Existing PR feedback — status

The instructions require every unresolved external finding to be addressed or
acknowledged with a rationale.

### Sourcery (1 issue) — stale for this PR

`text_line.py:151`: "The new `merge` return type and cast can be unsound for
subclasses of `TextLine`" — `merge(self, other: L) -> L` returning
`cast(L, TextLine.of_iterable(...))`.

- **`text_line.py` is not in this PR's diff.** `git diff
  origin/master...HEAD -- ebl/transliteration/domain/text_line.py` is empty.
  The change was made in `e3150b3d` but reached `master` independently
  through #740, which #743 was split out of. It is now baseline code.
- The concern is also **not reachable**: there are no `TextLine` subclasses
  in the repo (every `cast(TextLine, ...)` hit is a cast, not a subclass), so
  `L` binding to a `TextLine` subclass cannot happen today.

**Disposition:** acknowledged, no action in this PR. Worth a note on master if
`TextLine` is ever subclassed.

### qlty — 5 blocking issues, all pre-existing relocations

Each was verified against `git show origin/master:...`:

| qlty finding | Status |
| --- | --- |
| `retrieve_annotations_helpers.py:53` `match` | `retrieve_annotations.py:43` |
| `named_signs.py:68` `of`, 6 params | On master in `sign_tokens.py` |
| `named_signs.py:88` `of_name`, 6 params | On master in `sign_tokens.py` |
| `lemmatized_fragment_text.py:111`, 46 dup | Master `fragment.py:349` |
| `transliterated_fragment_lines.py:70`, 46 dup | Master `fragment.py:567` |

Both halves of the duplicate pair sat **inside master's single
`fragment.py`**, at lines 349 and 567. The split moved one copy into each new
file, so qlty now reports it as two files rather than one.

**Disposition:** none are new debt. The duplication is genuine and predates
the PR; the split made qlty report it as two files instead of one. Fixing it
is optional here, but the duplicated fixture block is a reasonable follow-up.

### Human reviewers

None. No human review has been submitted on #743.

### Merged-in branches

The only merge into this branch is `525c4979` (master). No unmerged feature
branch was merged in, so there is no sibling PR whose feedback needs pulling.
Related PR #740 is MERGED; its open qlty comments concern files not in this
diff.

## Severity

| ID | Finding | Severity |
| --- | --- | --- |
| F1 | `task type-pyright` fails, 149 errors | High |
| F2 | Scope and description out of sync; pyre claim wrong | Medium |
| F3 | Six task-tracking `.md` files committed | Medium |
| F4 | 30 uncovered statements in files this PR created | Medium |
| F5 | `TokenVisitor.result` returns `[]` on the base | Low |
| F6 | Module surfaces narrowed inconsistently, no facade | Low |
| F7 | Unreachable `is not None` filter in `parse_atf_lark` | Low |
| F8 | `_StartParser.parse` no longer forwards Lark options | Low |
| F9 | `NameParts` is a two-type array (relocated) | Info |
| F10 | Pre-existing 500 on the signs route | Info |

## Reproduction Steps

### F1 — pyright gate and baseline

```bash
poetry run task type-pyright        # 149 errors, 1 warning, exit 123
poetry run task type                # pyre: "No type errors found"

# Baseline
git worktree add --detach /tmp/master-wt origin/master
ln -s /workspaces/ebl-api/.venv /tmp/master-wt/.venv
cd /tmp/master-wt
gh pr view 743 --json files -q '.files[].path' | grep '\.py$' \
  | while read f; do [ -f "$f" ] && echo "$f"; done \
  | xargs npx --yes pyright@1.1.411          # 173 errors
```

### F4 — coverage on changed modules

```bash
poetry run pytest $(gh pr view 743 --json files -q '.files[].path' \
  | grep -E '^ebl/' | grep -v '^ebl/tests/' | grep '\.py$' \
  | sed 's|\.py$||; s|/|.|g; s|^|--cov=|' | tr '\n' ' ') \
  --cov-report=term-missing
# TOTAL 2878 statements, 81 missing, 97%

# Relocation is coverage-neutral:
poetry run pytest ebl/tests/fragmentarium/test_retrieve_annotations.py \
  --cov=ebl.fragmentarium.retrieve_annotations \
  --cov=ebl.fragmentarium.retrieve_annotations_helpers --cov-report=term-missing
# branch: 14 + 17 missing;  master: 31 missing in one file
```

### Runtime verification (all routes below were exercised)

`.env` was **never** sourced — it points at the production cluster.
`MONGODB_URI` was pinned to `mongodb://127.0.0.1:27017`, database
`ebl_review_743_smoke` (dropped afterwards). `create_app()` was called
directly instead of `get_app()`, which would have initialised the production
Sentry DSN. `AUTH0_PEM` was a freshly generated throwaway RSA key. Served
with waitress on `127.0.0.1:8123`.

| Request | Result | Exercises |
| --- | --- | --- |
| `GET /signs/transliteration/ku-nu-szi` | 200 `[]` | via `atf_grammar/` |
| `GET /markup?text=@i{italic} and plain` | 200 | `parse_markup_paragraphs` |
| `GET /fragments/query?transliteration=ku-nu-szi` | 200 | `visitor.reset()` |
| `GET /fragments?random=true` | 200 | `create_dispatcher` generics |
| `GET /fragments?needsRevision=true` | 200 | same |
| `GET /fragments?interesting=true` | 200 | same |
| `GET /fragments?bogus=1` | 422 `DispatchError` | dispatcher error path |
| `GET /signs/transliteration/(((((` | **500** | F10, pre-existing |

In-process checks against the running tree:

- `SignsVisitor.reset()` clears `_standardizations` exactly as the old direct
  assignment did.
- `parse_line("1. ku-nu-szi")` round-trips; `atf_grammar/` exists and the old
  `lark_parser/` directory is gone.
- The `Museum` enum is **byte-identical** across the 3-way split — all 72
  members, names, cities, countries and URLs match master exactly.

## Recommendation

**Request changes**, on three points only:

1. **F3 — remove the six `TASK-743-*` tracking files.** Blocking for merge.
2. **F2 — rewrite the PR description** to cover the file-splitting work in
   `19a2f464`, and correct the claim that pyre could not be run. Better still,
   split that commit into its own PR: the ATF-parser fix is a clean,
   well-argued change and does not deserve to be reviewed through 70 files of
   mechanical relocation.
3. **F1 — decide on pyright.** Drive the changed set to zero, or record an
   explicit exception for the factory_boy errors. It must not stay silently
   red, since CI will not catch it.

F4 needs an explicit decision (fill the coverage or agree relocation-only
lines are exempt). F5-F8 are follow-ups; none blocks. F9 is a judgement call
on the data hard gate. F10 deserves its own issue.

Once the description matches the diff, the underlying work is good: the
root-cause analysis is correct, the typing changes are faithful (I checked
`pydash.flow(set_enclosure_type, set_language)` against
`prepare_reconstruction`, the `_update_omitted_words` extraction, and
`convert_token_sequence` versus `tuple` — all behaviour-preserving), pyre and
the full suite are green, and every relocation I sampled preserves its data
exactly.
