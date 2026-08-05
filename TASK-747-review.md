# TASK-747 — Review of PR #747

## Summary

PR #747 (`add-uppercase-h-collation`, commit `f9f58296`) adds `H`, `Ḫ` and `Ḥ`
to the `"collation H"` entry of `WILDCARD_AND_COLLATION_MATCHERS` so uppercase
H-initial queries collate the way their lowercase counterparts already did,
plus tests.

**Verdict: the change is correct, surgical and well covered.** All 19 CI checks
pass, qlty reports no blocking issues, and a regression sweep shows no query
without an H-group character produces a different regex than before.

One unresolved external finding exists (Sourcery, `bug_risk`): the `|`
characters inside the character classes are matched literally. It is **real
and confirmed**, but **pre-existing across all 29 collation entries** and not
introduced or worsened by this PR. It is addressed in the Findings below with
a recommendation, not silently dismissed.

### External feedback gathered

| Source | Type | Content | Status |
| --- | --- | --- | --- |
| sourcery | review | remove `TASK-747-*.md` before merge | valid, open |
| sourcery | inline `:73` | `\|` inside `[...]` is literal | valid, Finding 1 |
| sourcery | comment | Reviewer's Guide (descriptive) | no action |
| humans | — | none submitted | — |
| other bots | — | none | — |

No PR has been merged into this branch (`git log master..HEAD` is the single
commit `f9f58296`), so there is no upstream PR feedback to pull in.

### CI and qlty state

All green on `f9f58296`:

- `Test Python 3.11`, `3.12`, `pypy-3.11` — pass (both workflow runs)
- `Analyze (python)` / `CodeQL` — pass
- `GitGuardian scan` / `GitGuardian Security Checks` — pass
- `Sourcery review` — pass
- `qlty check` — pass, **no blocking issues**
- `qlty coverage` — pass, 95.8% (0.0% change)
- `qlty coverage diff` — pass, "Not applicable. No executable lines in diff"
- `docker` — skipped (expected for a non-`master` branch)

Locally: `ebl/common/query/query_collation.py` is at **100%** line coverage
(342 tests across the collation, realia, dictionary and AfO-Register suites).

## Findings

### Finding 1 — `|` inside the character classes is matched literally

**Raised by:** Sourcery (`bug_risk`), inline on `query_collation.py:73`.
**Confirmed.** Inside `[...]`, `|` is an ordinary member, so
`[h|ḫ|ḥ|H|Ḫ|Ḥ|ʕ|ʾ|ʿ]` also accepts a literal `|`. Every one of the 29
collation entries is written this way, including the ones this PR does not
touch.

Two observable consequences, both **pre-existing**:

1. A `|` typed in a query is treated as a collation character. `_segmentize`
   isolates it and the first matching entry — `"collation S"` — claims it, so
   `a|b` emits `[a|ā|â|á|à|ä|α][s|š|ṣ|ś|σ]b`: the `|` searches for an *s*.
2. Stored text containing `|` is matched by unrelated queries. A realia entry
   with id `|attusa` is returned for both `hattusa` (via the H class) and
   `sattusa` (via the S class, which this PR never touches).

This PR does not introduce or widen the defect: the pre-patch class
`[h|ḫ|ḥ|ʕ|ʾ|ʿ]` already matched `|`, and the S-group demonstration involves
no changed code.

A caution for whoever fixes it: the naive rewrite is **not** uniformly safe.
`"collation SS": {"wildcard": r"[ss|ß]"}` is a class of `{s, |, ß}`, not the
two-character sequence `ss`. Turning it into `[ssß]` silently keeps today's
(broken) behaviour; turning it into `(ss|ß)` changes it, and
`_segmentize`/`_is_regex` assume single-character matches. The `SS` entry is
also effectively unreachable for `ss` input, because `"collation S"` precedes
it in the dict and claims each `s` first.

### Finding 2 — task tracking files must be removed before merge

**Raised by:** Sourcery (overall comment). **Valid and already tracked.**
`TASK-747-todo.md` and `TASK-747-log.md` are committed on the branch, and
this review adds `TASK-747-review.md`. All three must go before merge.
(Removal was started at
the user's request and then reverted at the user's request; nothing was
committed.)

### Finding 3 — behavioural note: ASCII `H` broadens more than `Ḫ`/`Ḥ` alone

**Raised by:** this review. **Not a defect — intended, but worth stating.**
Including plain `H` means an ASCII `H` query now reaches `ḫ`, `ḥ`, `ʕ`, `ʾ`
and `ʿ`. That is the point (otherwise `Hattusa` could not find `Ḫattusa`), but
it widens results for every collated field — dictionary `word`/`meaning`/
`root`, AfO-Register `text`, colophon `names`, realia `_id`/`relatedTerms` —
not only realia. Confirmed benign for the non-H corpus by the regression sweep
below.

### Finding 4 — the sibling collation groups still have the case gap

**Raised by:** this review, and acknowledged in the PR body. **Accepted scope
decision.** `Š`, `Ṣ`, `Ṭ`, `Ā`, `Ē`, … remain case-sensitive on the input
side, so `Šamaš` still emits a literal `Š`. The PR answers the request for
`Ḫ`/`Ḥ` and documents this explicitly rather than silently.

### Checks that found nothing

- **Data hard gate** — no array, id list or wire shape is touched; the
  collation table is a homogeneous `Dict[str, Dict[str, str]]`. No mixed-type
  array, no discriminator-by-probing, no domain/wire split mismatch.
- **Security** — the emitted pattern is character classes plus `re.escape`d
  literals, with no nesting or backtracking risk; CodeQL and GitGuardian pass.
  `test_search_treats_regex_metacharacters_literally` still passes.
- **Regressions** — none for input without an H-group character (sweep below).
- **File length** — 209 / 62 / 159 lines, all under the 250 limit.
- **Test removal** — none removed, skipped or disabled.

## Severity

| # | Finding | Severity | Introduced by this PR? |
| --- | --- | --- | --- |
| 1 | `\|` literal in char classes | Low | No — pre-existing, all 29 |
| 2 | Task files on the branch | Blocks merge | Yes |
| 3 | ASCII `H` broadens collated fields | Info | Yes, intentional |
| 4 | Other groups keep the case gap | Info | No — pre-existing |

Nothing here blocks the change itself. Finding 2 blocks the *merge* and is a
one-command fix.

## Reproduction Steps

All run from the repo root with
`PYTHONPATH=/workspaces/ebl-api poetry run python`.

### The fix works (regex level, no MongoDB)

```python
from ebl.common.query.query_collation import CollatedFieldQuery
for query in ["ḫattusa", "Ḫattusa", "Ḥattusa", "Hattusa", "ḥattuša"]:
    print(query, CollatedFieldQuery(query, "_id", "realia").value)
```

All five emit `[h|ḫ|ḥ|H|Ḫ|Ḥ|ʕ|ʾ|ʿ][a|…]…` and match each other **without**
`re.IGNORECASE`; `Battusa` matches none of them. Before the patch, the four
uppercase-initial forms emitted a literal `Ḫ` / `Ḥ` / `H`.

### The fix works (running service)

Local MongoDB on `127.0.0.1:27017` (**not** the `.env` URI, which is
production), database `ebl_task747` seeded with `Ḫattusa` and `Battusa`;
service started with
`poetry run waitress-serve --port=8002 --call ebl.app:get_app`.

| `GET /realia?query=` | result |
| --- | --- |
| `Ḫattusa` | `["Ḫattusa"]` |
| `Ḥattusa` | `["Ḫattusa"]` |
| `Hattusa` | `["Ḫattusa"]` |
| `ḥattusa` | `["Ḫattusa"]` |
| `H` | `["Ḫattusa"]` |
| `Battusa` | `["Battusa"]` |
| `Xattusa` | `[]` |

### Finding 1 (the `|` defect), through the API

With an extra entry whose id is `|attusa`:

| `GET /realia?query=` | result |
| --- | --- |
| `hattusa` | `["\|attusa", "Ḫattusa"]` |
| `sattusa` | `["\|attusa"]` |

The second row uses `"collation S"`, which this PR does not touch — the defect
is systemic and pre-existing.

### Regression sweep

For each sample, the emitted regex was compared against the same call with
`"collation H"` restored to its pre-patch value:

`marduk`, `Marduk`, `Šamaš`, `Ṭāb`, `enki`, `ANU`, `a*b`, `a?b`,
`Amêl-Marduk`, `Löwe`, `Pferd`, `0123`, `x+y`, `"quoted"`, `Battusa` — **all
unchanged**. Only input containing one of `h ḫ ḥ H Ḫ Ḥ ʕ ʾ ʿ` differs, as
intended.

## Recommendation

**Approve and merge, after removing the task files.**

Required before merge:

1. Delete `TASK-747-todo.md`, `TASK-747-log.md` and `TASK-747-review.md`
   (Finding 2).

For Finding 1, the maintainer's call — three defensible options:

- **Reply to Sourcery and leave it.** The defect is pre-existing, low impact
  (it needs a literal `|` in a query or in stored text), and this PR followed
  the established style of the table it edits. Cleanest scope-wise.
- **Fix the H entry only** (`[hḫḥHḪḤʕʾʿ]`). Small and safe, but makes one row
  of the table inconsistent with the other 27, which is the opposite of what
  Sourcery asked for.
- **Fix all 28 entries in a separate PR.** The right end state, but it is a
  behaviour change for `|` input and needs a decision on `"collation SS"`,
  which cannot be mechanically converted. Should not ride along here.

My recommendation is the first for this PR plus the third as a follow-up
issue, so the collation table gets cleaned deliberately rather than as a
side effect of an unrelated fix.

Findings 3 and 4 need no action; they are recorded so the scope decision is
explicit.

## Resolution

Applied on top of `f9f58296`, uncommitted at the time of writing.

| # | Finding | Resolution |
| --- | --- | --- |
| 1 | `\|` literal in char classes | Fixed across all 29 collation entries |
| 2 | Task files on the branch | Removed as the final step |
| 3 | ASCII `H` broadens collated fields | No action — intended |
| 4 | Other groups keep the case gap | Deferred — needs a decision |

### Finding 1 — fixed

Every collation class had its literal `|` removed, keeping each character set
otherwise identical (`[s|š|ṣ|ś|σ]` becomes `[sšṣśσ]`). The edit was applied by
script rather than retyped, and each class was then compared against the
pre-change table: all character sets are preserved and no pipe remains.

`"collation SS"` was `[ss|ß]`, i.e. the set `{s, |, ß}`, so its faithful
de-piped form is `[sß]`. It was *not* converted to `(ss|ß)`; making that entry
mean the two-character sequence `ss` is a separate design question, and
`_segmentize`/`_is_regex` assume single-character matches.

`markdown_escape = r"(\*|\^)*"` was deliberately left alone — that `|` is a
real alternation inside a group, not a character class.

The `"collation H"` and `"collation O"` rows fit on one line again once the
pipes were gone, so they were collapsed to match the other 29 rows.

Equivalence evidence: 4332 query/stored comparisons across realia, dictionary
and colophon fields over pipe-free data produced **zero** behaviour changes.
The only difference is the intended one:

| input | before | after |
| --- | --- | --- |
| query `\|` | `[s\|š\|ṣ\|ś\|σ]` | `\\\|` (escaped) |
| query `a\|b` | `[a…][s…]b` | `[aāâáàäα]\\\|b` |
| query `hattusa` vs stored `\|attusa` | matched | no match |
| query `sattusa` vs stored `\|attusa` | matched | no match |

Confirmed through the running service: `?query=hattusa` no longer returns
`\|attusa`, `?query=\|attusa` now finds the literal entry, and every H
spelling still returns `Ḫattusa`.

New tests: a parametrized guard that no entry in
`WILDCARD_AND_COLLATION_MATCHERS` contains a `|`, plus cases for a literal
pipe being escaped, a pipe query not matching a collated letter, and an
h-query not matching a stored pipe.

### Finding 4 — deferred, with new evidence

Runtime check on the same service made the gap concrete: `?query=Samas`
returns **nothing** for a stored `Šamaš`, exactly as `Hattusa` failed to find
`Ḫattusa` before this PR. Closing it means adding uppercase forms to the
other 27 collation groups, which broadens search behaviour well beyond the
"add Ḫ and Ḥ" request. Left for the user to decide.

### Gates after the fix

`task format`, `task lint`, `task type` (pyre), `task type-pyright`,
`task test` (4175 passed, 2 skipped, 1 xfailed), 100% coverage on
`query_collation.py`, `flake8`, `mypy`, `task lint-md` — all green. Files are
209 / 87 / 159 lines, under the 250 limit.

Note: pyre first failed with `Worker_exited_abnormally` while the full test
suite was running concurrently; re-run on an idle machine it reports no type
errors. That was resource contention, not a type error.

### Finding 4 — closed

Uppercase counterparts were added to every collation group, applied with
`str.upper()` rather than typed by hand. `"collation H"` was already complete
and is unchanged; `ß` is skipped because its uppercase `SS` is two characters;
caseless characters (`ᵈ`, `ₓ`, `ʕ`, `ʾ`, `ʿ`, digits, `+`) are untouched.

Every class is a strict superset of its previous self and every added
character is the uppercase of one already present, so no match can be lost.
A parametrized test now asserts that invariant across all 29 entries.

Confirmed on the running service: `?query=Samas` returns `Šamaš`,
`?query=Tab` returns `Ṭāb`, `?query=Lowe` returns `Łowe`, `?query=Ekur`
returns `ékur`, and `Xattusa` / `Zzz` still return nothing.

Limitation worth recording: this only helps letters that have a collation
group. `b`, `f`, `j`, `m`, `p`, `q`, `v`, `w`, `z` have none, so an uppercase
one stays literal — `Amel-Marduk` still will not match `amêl-marduk` at the
regex level, and those cases keep relying on `$options: "i"`.

Gates after this change: format, lint, pyre, pyright, `task test` (4242
passed), 100% coverage, flake8, mypy, lint-md — all green.
