<!-- markdownlint-disable MD013 -->
# TASK-743 Review — PR #743 "Make the ATF parser visible to the type checkers"

## Metadata

| Field | Value |
| --- | --- |
| PR | [#743](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743) — Make the ATF parser visible to the type checkers |
| Repository | `ElectronicBabylonianLiterature/ebl-api` |
| Branch | `fix-type-checker-blind-spots` → `master` |
| Commit reviewed | `549d45ae922b2f090cb4938ebfba113b3f897916` ("Add a standalone brief for the frontend change") |
| Merge base | `c2b0a5ef4210ba83652e26d9852e1866fd6e430a` ("Add new manuscript types (#749)") |
| `origin/master` now | `e92b43d23791e398487e8a6904f482bb7ec37348` — master has moved 4 commits past the merge base (#763–#766) |
| Local tree vs remote | identical — local `HEAD` and `git ls-remote` both at `549d45ae`. Nothing unpushed, so the qlty and CodeQL verdicts on the PR page are **current**, not stale |
| Size | 202 files, +15047 / −6910 (108 added, 78 modified, 16 renames) — of which **23 files and 4507 lines are stray task artefacts** |
| Commits | 26 (9 since the round-12 review) |
| Review date | 2026-09-16 |
| Review round | 13 |
| Mergeability | **`MERGEABLE: false`, `mergeStateStatus: dirty`** — conflict in `ebl/fragmentarium/domain/museum.py` |
| CI | all 14 check runs `success` or `skipped`; `qlty check` status `success` with description "2 blocking issues" |
| Last human review | `Fabdulla1`, **APPROVED** 2026-09-01 at `16a84e20` — **9 commits stale** |
| **Verdict** | **Request changes** at `549d45ae`. **B2 and B3 have since been addressed locally** (see Resolution); B1 is deferred to merge time by the author's decision. The work is **not pushed**, so the PR page still shows the pre-fix state. |
| Blocking findings | B1, B2, B3 |
| Non-blocking findings | N1 – N6 |
| Informational | I1 – I4 |

## Summary

Good news first: every one of the three blocking findings from round 12 is genuinely fixed, and I checked each against the tree rather than taking the commit messages on trust. The `nameParts` array really is split now — `name_parts` and `name_breaks` are two separate fields with a validator each, the wire has two keys, and `OneOfTokenSchema` is gone from that path. `tokens.py`'s `__all__` is whole again. Both `# type: ignore` comments are gone, and the branch adds no new suppressions anywhere. Two bonus fixes landed too: `/signs?listAll=true` and `/markup` on bad input both used to return 500 and now return 200 and 422.

The thing I liked most is the `@final` on `TextLine`. Sourcery's old complaint about the `cast` in `merge` was that it would lie for a subclass; marking the class final means the compiler now guarantees there can't be one. That's fixing the cause instead of the symptom, and it quietly closes a thread that had been open since July.

I wanted hard evidence that splitting the array didn't change what the parser produces, so I built a 60-case ATF probe — broken-away brackets in every position, determinatives, `⸢⸣`, `<>`, `<<>>`, flags, sub-indices, compound graphemes — and ran it at the merge base and at this commit. The output is byte-for-byte identical on both sides. Then I booted the service against a throwaway database, seeded a fragment in the **old** interleaved format that production still holds, and fetched it: HTTP 200, split correctly, values preserved. The compatibility shim works on a real route, not just in unit tests.

What's holding it up is mostly housekeeping rather than code. The branch now carries 22 `TASK-*.md` files and a `.patch` into `master` — 4507 lines of working notes that the PR's own Gate 3 says must never land, and the cleanup command written in the description only covers about half of them. The PR has also gone into conflict since the museum PRs merged this morning. And there's one real code gap: a malformed `nameBreaks` array raises a bare `ValueError` that nothing maps, so it surfaces as a 500 where every neighbouring validation error gives a 422.

None of that is hard to fix, and none of it undoes the work. Clear the artefacts, rebase, register `ValueError`, and I think this is ready.

### Specifically checked

| Check | Result |
| --- | --- |
| **Dev container configuration** | **No warning needed — nothing changed.** `git diff c2b0a5ef..HEAD -- .devcontainer` is empty. All five files (`README.md`, `devcontainer.json`, `setup.sh`, `sync-env.py`, `test_sync_env.py`) are byte-identical to the merge base. No `Dockerfile`, `docker-compose`, `.github/workflows/`, `pyproject.toml`, `Taskfile` or lockfile change either. The only config-adjacent edit is `.github/instructions/copilot.instructions.md`, and it is disclosed in the description. |
| **New `.md` files** | **Failed — 22 added, plus `TASK-749-frontend.patch`.** See B1. Round 12 reported none; this is a regression. |
| **Failing checks** | None. All 14 check runs on `549d45ae` are `success` or `skipped`. |
| **qlty** | 2 blocking issues, both `similar-code`, both justified and both genuinely false positives — see N3. Reconciled against the base: the branch **introduces 2** duplications and **removes 24**. |
| **CodeQL** | No open alerts observable. `CodeQL` and `Analyze (python)` check runs pass; all 14 CodeQL review threads are resolved. Caveat in I3. |
| **Mergeability** | **Failed** — conflict with master. See B2. |
| **Data hard gate** | Passed for everything this PR touches. Two pre-existing mixed arrays remain elsewhere, untouched — see I1. |
| **File length (250 lines)** | Passed. Longest changed file is `legacy_atf_converter.py` at 249. |
| **Tests removed** | None. 1647 → 1823 test functions; 3 apparent losses are renames with assertions intact. |

## Findings

### Details

#### B1 — the branch carries 23 task artefacts into `master`

**Severity: High (blocking).**

`git diff --diff-filter=A --name-only c2b0a5ef..HEAD` lists 23 added files at the repository root that are not code:

`TASK-743-fix-handoff.md`, `TASK-743-fix-log.md`, `TASK-743-fix-pr-body.md`, `TASK-743-fix-todo.md`, `TASK-743-log.md`, `TASK-743-review.md`, `TASK-743-todo.md`, `TASK-744-log.md`, `TASK-744-todo.md`, `TASK-745-handoff.md`, `TASK-745-log.md`, `TASK-745-todo.md`, `TASK-746-log.md`, `TASK-746-todo.md`, `TASK-747-log.md`, `TASK-747-todo.md`, `TASK-748-log.md`, `TASK-748-todo.md`, `TASK-749-frontend-brief.md`, `TASK-749-frontend-pr-body.md`, `TASK-749-frontend.patch`, `TASK-749-log.md`, `TASK-749-todo.md`.

That is 4507 lines of markdown — roughly a third of the PR's insertions — and it is exactly what the PR's own **Gate 3** forbids: *"A merge that carries any of them into `master` is a defect, regardless of whether everything else is green."*

Two compounding problems:

1. **The documented cleanup command is now incomplete.** Gate 3 says:

   ```bash
   git rm task_743_migrate_name_breaks.py task_743_migrate_name_breaks_test.py
   git rm TASK-743*.md TASK-744*.md TASK-745*.md
   ```

   The migration scripts are already gone (moved to #764), so that first line is a no-op. The second line misses **TASK-746, TASK-747, TASK-748 and TASK-749 entirely** — 8 markdown files — and misses `TASK-749-frontend.patch`, which is not a `.md` file and no glob in that command would catch.

2. **`TASK-743-review.md` — this file — is itself among them.** A review document committed to the branch it reviews will land in `master` alongside the code it was meant to gate.

At round 12 this query returned nothing. The artefacts were introduced by the nine commits since.

#### B2 — the PR is in conflict with `master`

**Severity: High (blocking).**

The GitHub API reports `mergeable: false`, `mergeable_state: dirty`. Reproduced locally:

```text
$ git merge-tree --write-tree --name-only origin/master HEAD
ebl/fragmentarium/domain/museum.py
CONFLICT (content): Merge conflict in ebl/fragmentarium/domain/museum.py
```

`master` moved to `e92b43d2` on 2026-09-16 when **#765 (Erimtan and Marash Museums)** and **#766 (Gaziantep)** merged, both adding `Museum` entries. This branch restructured `museum.py` during the split, so the two edits collide.

This also means every green check on the PR page describes `549d45ae` in isolation, not the merge result. After resolving, re-run at minimum `task type` and `task test` — the conflict is in the file whose enum shape a previous review round already raised questions about.

#### B3 — a malformed `nameBreaks` array returns 500, not 422

**Severity: Medium-High (blocking).**

`_validate_name_breaks` in [ebl/transliteration/domain/sign_token_base.py:56-63](ebl/transliteration/domain/sign_token_base.py#L56-L63) raises a bare `ValueError`:

```python
def _validate_name_breaks(instance, _attribute, value):
    if len(value) > len(instance.name_parts):
        raise ValueError(
            f"A name with {len(instance.name_parts)} parts takes at most "
            f"{len(instance.name_parts)} breaks, not {len(value)}."
        )
```

It fires inside marshmallow's `@post_load`, which does not convert `ValueError`. [ebl/error_handler.py](ebl/error_handler.py) registers `AlignmentError`, `DispatchError`, `LemmatizationError`, `NotFoundError`, `DuplicateError` and `DataError` — **not `ValueError`** — so it falls through to the catch-all `unexpected_error` and becomes `500 Internal Server Error`.

Verified against the running service (seeded document `K.3`, `nameBreaks` of length 3 against `nameParts` of length 1):

```text
GET /fragments/K.3  ->  HTTP 500
ValueError: A name with 1 parts takes at most 1 breaks, not 3.
```

Every sibling validation failure in the same schema gives a clean 422 — `nameParts` holding a `BrokenAway`, a non-alternating legacy array, a missing field. This one is the odd one out, and `name_breaks` is new in this PR, so the path is new too.

The neighbouring `_validate_sub_index` has the same shape but predates the PR (`_check_sub_index` at the merge base), so a negative `subIndex` already 500s today. Fixing both together would be natural: raise `DataError` instead of `ValueError`, or register `ValueError` in `error_handler.py`.

#### N1 — the legacy shim rejects a valid new-format payload that omits `nameBreaks`

**Severity: Low.**

`separate_legacy_name_parts` in [ebl/transliteration/application/token_schemas_signs.py:72-84](ebl/transliteration/application/token_schemas_signs.py#L72-L84) decides a payload is legacy by the **absence of `nameBreaks`**, then splits `nameParts` by even/odd index.

`name_breaks` declares `load_default=()`, which advertises the key as optional. But a new-format payload with two or more `nameParts` and no `nameBreaks` is a legal domain object (`_validate_name_parts` permits any number of `ValueToken`s, `_validate_name_breaks` permits zero breaks) — and the shim splits it anyway:

```text
{"nameParts": [ValueToken("ku"), ValueToken("r")]}   ->  422
  nameBreaks: {0: {'side': ['Missing data for required field.'],
                   'type': ['Must be equal to BrokenAway.']}}
```

Low reachability in practice: `dump` always emits `nameBreaks`, so anything the backend wrote round-trips correctly, and the parser never produces two adjacent `ValueToken`s. It bites only a hand-written client payload. Worth either making `nameBreaks` `required=True` on load so the optionality is honest, or keying the shim on something other than absence.

#### N2 — a non-alternating legacy document now 500s where master reads it

**Severity: Low (mitigated).**

The even/odd split assumes legacy `nameParts` strictly alternates `ValueToken, BrokenAway, …` starting with a `ValueToken`. I probed the merge-base parser across every broken-away position I could construct and it does, always — so the assumption holds for parser-produced data. But master's type was `Sequence[Union[ValueToken, BrokenAway]]` with no ordering constraint, so a document with a leading `BrokenAway` is *valid* on master and unreadable here:

```text
GET /fragments/K.2  ->  HTTP 500
ValidationError: {'text': {'lines': {0: {'content': {0: {'parts': {0:
  {'nameParts': {0: {'type': ['Must be equal to ValueToken.']}}, ...
```

**This is properly mitigated**, and credit where it's due: PR #764's migration raises `NonAlternatingName` naming the offending collection and `_id` rather than guessing. So the safe sequence is to dry-run #764's migration against production first — if it reports nothing, this risk is empirically zero. Worth stating that ordering explicitly in Gate 2 of the description, since right now the two PRs describe the dependency from opposite ends.

#### N3 — qlty's "2 blocking issues" are real findings but not real defects

**Severity: Low.**

The `qlty check` commit status reads `success` with the description **"2 blocking issues"**. I reconciled it properly, per the repo rule that a changed-files run cannot see a duplication against an untouched file: `qlty smells --all --include-tests` at `HEAD` gives **106** findings, the same command in a detached worktree at `c2b0a5ef` gives **126**. Diffed, the branch **introduces 2 duplications spanning 4 files and removes 24 findings** — a net improvement of 20.

| Duplication | Files | What it is |
| --- | --- | --- |
| A, 17 lines, mass 64 | `ebl/transliteration/domain/tokens.py` ↔ `ebl/fragmentarium/domain/fragment.py` | Two unrelated `__all__` export lists that happen to be the same length and shape |
| B, 22 lines, mass 84 | `ebl/tests/factories/fragment.py` ↔ `ebl/tests/fragmentarium/test_museum_number.py` | An `__all__` list against `PREFIXES`, a list of museum-number prefix strings |

Both are lists of bare string literals with no shared meaning and nothing extractable — precisely the carve-out the instructions name ("two unrelated `__all__` lists that happen to have the same shape"). I agree with accepting them. The justification is recorded in the PR description, which survives the artefact cleanup — that was the right call.

One stale claim to fix: the description's gate table still says `qlty smells` | **"0 findings in any file this PR touches"**. That is no longer true, and it sits above a later section that correctly reports 2. Delete the earlier row.

#### N4 — the description contradicts itself on the wire format

**Severity: Low.**

The description has accreted round by round and now states both:

- line 6: *"This PR changes the `nameParts` wire format **and** the stored MongoDB shape."* — correct.
- line 187: *"**The `nameParts` wire format is unchanged** — verified by diffing the …"* — a round-5 statement, now false.

A reader can't tell which is current without reading the code. Round 11's headline finding was a description that had drifted from the branch; this is the same failure mode, just from staleness rather than error. Prune the superseded round sections, or mark them as historical.

#### N5 — the approval is nine commits old

**Severity: Low (process).**

`Fabdulla1` approved on 2026-09-01 at `16a84e20`. Nine commits have landed since, including the `nameParts`/`nameBreaks` split itself, a CodeQL round, a qlty round, and the removal of the migration. The approving review's three named items are all fixed, but the approval predates the change that most deserves a second human look. Worth a re-request before merge.

#### N6 — the companion PR has the same artefact problem

**Severity: Low.**

[#764](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/764) (`migrate-name-breaks`, the migration this PR depends on) adds **14 `TASK-764-*.md` files** alongside its 4 code files. Same cleanup is needed there before it merges. Flagging it here because the two PRs must be sequenced together and it would be easy to clean one and forget the other.

#### I1 — two pre-existing mixed arrays remain, untouched

**Severity: Informational.**

Sweeping the diff for the data hard gate, two mixed-type sequences survive in changed files:

- [ebl/corpus/domain/manuscript_line.py:26](ebl/corpus/domain/manuscript_line.py#L26) — `paratext: Sequence[Union[DollarLine, NoteLine]]`, with an `isinstance(line, DollarLine)` probe at line 61 to tell them apart.
- [ebl/corpus/domain/chapter_query.py:41](ebl/corpus/domain/chapter_query.py#L41) — `Sequence[Union["TextLine", L]]`.

Both are **byte-identical at the merge base** and untouched by this PR, so they fall outside the gate's "new models and any model you touch" scope. No action requested here. But `paratext` is the same defect class this PR just spent 26 commits fixing for `nameParts`, down to the `isinstance` probe, so it is the obvious next candidate if anyone wants a follow-up issue.

`Branch = Union[str, Tree]` and `TreeChild = Optional[Union[Tree, Token]]` in `legacy_transformer_base.py` are new, but they describe lark's own parse-tree shape rather than a domain model. Fine as they are.

#### I2 — `_StartParser` no longer delegates arbitrary attributes

**Severity: Informational.**

The wrapper's `__getattr__` was replaced by an explicit `options` property — which is the whole point of the PR, since `__getattr__` is exactly what a type checker cannot see through. The three tests that covered the old behaviour were renamed, not dropped, with assertions intact:

| Base | HEAD |
| --- | --- |
| `test_getattr_delegates_to_wrapped_parser` | `test_options_are_the_wrapped_parsers_options` |
| `test_getattr_raises_for_missing_attribute` | `test_the_wrapper_does_not_delegate_unknown_attributes` |
| `test_getattr_without_initialised_parser_raises_attribute_error` | `test_an_uninitialised_wrapper_raises_attribute_error` |

Consequence worth knowing: `WORD_PARSER`, `MARKUP_PARSER` and their siblings now expose only `parse` and `options`. Any future code reaching for another Lark method on them gets an `AttributeError` instead of silent delegation — which is the improvement, but it is a behaviour change.

#### I3 — CodeQL was verified indirectly

**Severity: Informational.**

`GET /repos/.../code-scanning/alerts?ref=refs/heads/fix-type-checker-blind-spots` returns `403 Resource not accessible by integration` for the token available here, so I could not enumerate alerts directly. What I could verify: the `CodeQL` and `Analyze (python)` check runs on `549d45ae` both conclude `success`; all 14 `github-advanced-security` review threads are resolved; and the most recent advanced-security review (2026-09-15, at `2a772298`) carries an empty body, whereas the one that found problems (2026-08-27) carried the "found more than 20 potential problems" text. Consistent with zero open alerts, but stated as inference rather than as a direct reading.

#### I4 — the diff is very large for what it does

**Severity: Informational.**

202 files and +15047/−6910. Removing B1's artefacts takes 4507 insertions off that immediately. The rest is genuine: 16 renames from the module/directory split, 108 new files mostly from splitting oversized modules and test files to satisfy the 250-line gate. Not a request to change anything — just context for whoever does the final read-through, and one more reason to land B1 first so the file list reflects the actual work.

### Feedback already on the PR — disposition

Fetched via `gh api` for reviews, inline diff comments and issue comments, per the review gate. 15 submitted reviews, 41 inline comments across 41 threads, 2 issue comments.

| Source | Item | Status |
| --- | --- | --- |
| `Fabdulla1` (2026-08-07, CHANGES_REQUESTED) | `/signs/transliteration` 422 missing | **Fixed** — verified live: valid → 200, garbage → 422 |
| `Fabdulla1` | 169-char URL line in `annotations_service.py` | **Fixed** — flake8 at 120 cols is clean over all 160 changed files |
| `Fabdulla1` | Five `Museum` enum `.value` shapes changed | **Fixed** — 72 members verified value-identical in round 12 |
| `Fabdulla1` | `SignsVisitor.reset()` and `_StartParser.parse(start=…)` need focused tests | **Fixed** — both present |
| `Fabdulla1` (2026-09-01, APPROVED) | `NamePart` violates the one-array/one-type gate | **Fixed** — see below |
| `Fabdulla1` | `tokens.py` `__all__` drops nine classes | **Fixed** — all 16 names present |
| `Fabdulla1` | Two `# type: ignore` in `test_fragment_pattern_matcher_site.py` | **Fixed** — none in the file; PR adds zero new suppressions repo-wide |
| `sourcery-ai` (2026-07-23) | `TextLine.merge` cast unsound for subclasses | **Resolved structurally** — `@final` added to `TextLine`. Thread still shows unresolved on GitHub; worth closing it manually |
| `qltysh` ×26 | duplication / parameter-count findings | 24 resolved; 2 open and justified — see N3 |
| `github-advanced-security` ×14 | CodeQL findings | All 14 resolved |
| Author issue comment (2026-08-25) | — | No open request |

Round-12 findings re-verified against `549d45ae`:

| Round 12 | Status at `549d45ae` |
| --- | --- |
| **F1** mixed `nameParts`, `isinstance` probe, `OneOfTokenSchema` on the wire | **Fixed.** `NamePart` wrapper gone. `name_parts: Sequence[ValueToken]` and `name_breaks: Sequence[BrokenAway]` are separate fields with a validator each; wire keys `nameParts` / `nameBreaks` use `NameValueTokenSchema` / `NameBreakSchema`. No discriminator, no probe, domain split matches wire split. A payload putting one type in the other array is a 422, as the gate requires |
| **F2** narrowed `__all__` | **Fixed.** All 16 names listed, including the nine locally defined classes |
| **F3** load-bearing suppressions | **Fixed.** Zero in the file; zero new suppression comments added by the PR |
| **F4** instruction file undisclosed | **Fixed.** Disclosed at description line 324 |
| **F5** `GET /signs?listAll=true` → 500 | **Fixed.** Now 200 |
| **F6** `GET /markup` unparsable → 500 | **Fixed.** Now 422, `Invalid markup: "@i@kur@i@"` |
| **F7** redundant inner cast | **Fixed.** Removed; `@final` added on top |

## Severity

| Severity | Meaning | Findings |
| --- | --- | --- |
| High | Must not merge as-is | B1, B2 |
| Medium-High | A new code path returns the wrong status | B3 |
| Low | Contract sharpness, stale description, process | N1, N2, N3, N4, N5, N6 |
| Informational | Noted for awareness; no action requested | I1, I2, I3, I4 |

Overall risk: **low**. No runtime regression that this PR causes is reachable from parser-produced data — I tested that rather than assuming it. B1 and B2 are hygiene; B3 is a wrong status code on an input that should not occur but is not currently impossible.

## Reproduction Steps

All commands run from `fix-type-checker-blind-spots` at `549d45ae`, with `.env` deliberately **not** sourced — it points at the production cluster.

### B1 — the artefacts

```bash
git diff --diff-filter=A --name-only -M c2b0a5ef..HEAD | grep -v '^ebl/'     # 23 files
git diff --numstat c2b0a5ef..HEAD -- 'TASK-*.md' | awk '{a+=$1} END {print a}'  # 4507
```

### B2 — the conflict

```bash
git fetch origin
git merge-tree --write-tree --name-only origin/master HEAD
# CONFLICT (content): Merge conflict in ebl/fragmentarium/domain/museum.py
gh api repos/ElectronicBabylonianLiterature/ebl-api/pulls/743 -q '.mergeable, .mergeable_state'
# false / dirty
```

### B3, N1, N2 — schema behaviour

```bash
poetry run python - <<'PY'
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
VT = lambda v: {"type":"ValueToken","value":v,"enclosureType":[],"erasure":"NONE"}
BA = lambda v,s: {"type":"BrokenAway","value":v,"side":s,"enclosureType":[],"erasure":"NONE"}
def reading(parts, breaks=None):
    d = {"type":"Reading","value":"kur","name":"kur","nameParts":parts,"subIndex":1,
         "modifiers":[],"flags":[],"sign":None,"enclosureType":[],"erasure":"NONE"}
    if breaks is not None: d["nameBreaks"] = breaks
    return d
OneOfTokenSchema().load(reading([VT("ku"),BA("[","LEFT"),VT("r")]))   # legacy -> OK
OneOfTokenSchema().load(reading([BA("[","LEFT"),VT("kur")]))          # N2 -> ValidationError
OneOfTokenSchema().load(reading([VT("ku"),VT("r")]))                  # N1 -> ValidationError
OneOfTokenSchema().load(reading([VT("kur")], [BA("[","LEFT")]*2))     # B3 -> bare ValueError
PY
```

### Live service verification

```bash
export PYTHONPATH=/workspaces/ebl-api
export MONGODB_URI="mongodb://127.0.0.1:27017"          # local; NOT the URI in .env
export MONGODB_DB="ebl_t743_r13"
export EBL_AI_API="http://127.0.0.1:9/unused"
export AUTH0_PEM="$(base64 -w0 <throwaway RSA public key PEM>)"
export AUTH0_AUDIENCE="https://example.invalid/api"
export AUTH0_ISSUER="https://example.invalid/"
export SENTRY_DSN="" CACHE_TYPE="NullCache"
poetry run python -c "
import os; from waitress import serve; from ebl.app import create_context, create_app
serve(create_app(create_context(), os.environ['AUTH0_ISSUER'], os.environ['AUTH0_AUDIENCE']),
      host='127.0.0.1', port=8123, threads=4)"
```

Seed `K.1` from `FragmentFactory` with `nameParts` re-interleaved into the legacy shape, `K.2` with a leading `BrokenAway`, `K.3` with more breaks than parts. Then, with an RS256 JWT signed by the throwaway key (`scope: read:fragments read:words read:bibliography`):

```text
GET /fragments/K.1                       200   nameParts=[VT,VT]  nameBreaks=[BA]   values ku[r, k[u]r, K]UR
GET /fragments/K.2                       500   ValidationError (N2)
GET /fragments/K.3                       500   ValueError (B3)
GET /signs/transliteration/kur           200
GET /signs/transliteration/%24%24%24      422   <- the headline fix
GET /signs?listAll=true                  200   <- was 500 at round 12 (F5)
GET /markup --data-urlencode 'text=@i{italic text}'  200
GET /markup --data-urlencode 'text=@i@kur@i@'        422  <- was 500 at round 12 (F6)
```

Note: seed without `archaeology`, or seed the `provenances` collection — otherwise every fragment GET fails with `Invalid provenance: Assyria`, which is an artefact of the empty throwaway database and nothing to do with this PR.

### Parser equivalence — 60 ATF cases, both sides

```bash
git worktree add --detach /tmp/base c2b0a5ef
# run the same probe in each tree, dumping value / clean_value / name / Line.atf as JSON
diff /tmp/equiv_base.json /tmp/equiv_head.json    # -> identical (51 parsed, 9 rejected, both sides)
```

Cases covered: `kur`, `ku[r]`, `[k]ur`, `[kur]`, `k[u]r`, `[ku]r`, `ku[r`, `k]ur`, `[k]u[r]`, `[k]u[r]a`, `KUR`, `[K]UR`, `KU[R]`, `1`, `10`, `1[0]`, `[1]0`, `{d}kur`, `{d}[k]ur`, `{[d]}kur`, `kur{d}`, `[k]ur#`, `[k]ur!`, `[k]ur?`, `[k]ur*`, `kur(KUR)`, `[k]ur(KUR)`, `⸢kur⸣`, `⸢k⸣ur`, `<kur>`, `<<kur>>`, `kur-ra`, `kur.ra`, `°kur\ra°`, `...`, `[...]`, `x`, `X`, `n`, `|KUR.RA|`, `kur₂`, `kurₓ`, `4(diš)`, `1/2(diš)` and others.

### qlty reconciliation

```bash
qlty smells --all --include-tests                          # HEAD  -> 106 findings
git worktree add --detach /tmp/base c2b0a5ef && cd /tmp/base
qlty smells --all --include-tests                          # base  -> 126 findings
# diff the two -> introduces 2 duplications (4 files), removes 24
```

### Local gates

| Gate | Command | Result |
| --- | --- | --- |
| format | `task format` (`ruff format --check ebl`) | 886 files already formatted |
| lint | `task lint` (`ruff check ebl`) | All checks passed |
| **pyre** | `task type` | **No type errors found** |
| pyright | `task type-pyright` | 0 errors, 0 warnings, 0 informations |
| test | `task test` | **4530 passed, 2 skipped, 1 xfailed** in 282s |
| lint-md | `task lint-md` | 0 errors over 28 files |
| flake8 | `flake8 <160 changed> --max-line-length=120` | exit 0 |
| mypy | `mypy <160 changed> --ignore-missing-imports` | Success, no issues in 160 files |

`task test-all` exits 0. The 2 skips and 1 xfail are all pre-existing at the merge base; none added here.

### No test was lost

```bash
git grep -h -oE '^\s*def (test_[A-Za-z0-9_]+)' c2b0a5ef -- 'ebl/tests/*.py' | sed 's/.*def //' | sort -u > /tmp/base.txt
git grep -h -oE '^\s*def (test_[A-Za-z0-9_]+)' HEAD      -- 'ebl/tests/*.py' | sed 's/.*def //' | sort -u > /tmp/head.txt
wc -l /tmp/base.txt /tmp/head.txt        # 1647 -> 1823
comm -23 /tmp/base.txt /tmp/head.txt     # 3 names, all renames (see I2)
```

## Recommendation

**Request changes.** The engineering is done and it is good. Three things stand between this and merge, and two of them are not code.

1. **B1 — remove all 23 artefacts, and fix the command in Gate 3.** The current one misses TASK-746 through TASK-749 and the `.patch`:

   ```bash
   git rm 'TASK-*.md' TASK-749-frontend.patch
   ```

   Then re-check with `git diff --diff-filter=A --name-only -M c2b0a5ef..HEAD | grep -v '^ebl/'` and confirm it is empty. Do the same on **#764** (N6), which has 14 of its own.

2. **B2 — resolve the `museum.py` conflict against `origin/master`.** #765 and #766 added museum entries this morning. After resolving, re-run `task test-all`; the green checks on the PR page describe `549d45ae` alone, not the merge result.

3. **B3 — map the `ValueError` to a 422.** Either raise `DataError` from `_validate_name_breaks` and `_validate_sub_index`, or register `ValueError` in `error_handler.py`. Today a malformed `nameBreaks` is the only validation failure in this schema that returns 500.

Worth doing in this PR, all small:

- **N3** — delete the stale `qlty smells | 0 findings` row from the description's gate table; the accurate count is already stated further down.
- **N4** — prune or date-stamp the superseded description sections, so "the wire format is unchanged" no longer sits 180 lines below "this PR changes the wire format".
- **N2** — state the deploy order in Gate 2 explicitly: dry-run #764's migration first; if `NonAlternatingName` reports nothing, the compatibility risk is empirically zero.
- Close Sourcery's `text_line.py` thread by hand — `@final` answered it, but GitHub still shows it open.

Worth a follow-up issue rather than more scope here:

- **N1** — make `nameBreaks` `required=True` on load, or key the legacy shim on something other than the field's absence.
- **I1** — `manuscript_line.paratext` is the same mixed-array defect this PR just fixed for `nameParts`, `isinstance` probe included.

**Before merging:** delete `TASK-743-review.md` (this file), `TASK-743-review-todo.md` and `TASK-743-review-log.md` along with everything in B1. They are review artefacts and must not reach `master`.

## Resolution — what was done after this review (2026-09-16)

Work applied locally on top of `549d45ae`. **Nothing is pushed**, so every verdict on the PR page still describes `549d45ae` and is stale with respect to the state below.

| Finding | Status | What was done |
| --- | --- | --- |
| **B1** artefacts | **Deferred by decision, and now larger** | The author chose to leave them until merge time. The round-13 task and handoff documents add five more, so the branch now carries **28** root artefacts, not 23. The `git rm 'TASK-*.md'` glob still covers them all. Gate 3's cleanup command in the description was wrong — it covered 12 files — and has been **corrected** to `git rm 'TASK-*.md' TASK-749-frontend.patch`, with the reviewer's verification query and a note that #764 needs the same for its 14 files. |
| **B2** conflict | **Fixed locally** (commit `5935b154`) | `origin/master` merged in. The conflict was structural: the branch moved museum entries into `museum_entries_a_l/m_s/t_y.py`, master added three museums inline. Resolved by keeping the branch's structure and folding master's `ERIMTAN_MUSEUM`, `GAZIANTEP_MUSEUM` and `KAHRAMANMARAS_MUZESI` into it. Verified by building the enum on all three sides: **identical to `origin/master`** (75 members, identical values), and against the branch only those three added — nothing removed, nothing changed. |
| **B3** 500 not 422 | **Fixed** | All three validators in `sign_token_base.py` now raise `DataError`, already mapped to 422, instead of a bare `ValueError`. This also fixes the pre-existing negative-`subIndex` 500. Confirmed on the running service: `GET /fragments/K.3` went **500 → 422**, and the legacy fragment still returns 200. |
| **N1** shim contract | **Fixed** | `nameBreaks` is now `required=True`, so the schema states what the adapter already assumed. No content-probing was added — the data hard gate forbids it, and an ambiguous payload is invalid under both readings anyway. |
| **N2** deploy order | **Fixed in the description** | Gate 2 now spells out the order: dry-run #764's migration **before** merging this PR, since `NonAlternatingName` is what proves no un-splittable document exists; then merge; then apply. |
| **N3** stale qlty row | **Fixed in the description** | The gate table's "0 findings in any file this PR touches" is replaced by the reconciled figure — 2 accepted `similar-code` findings, repo-wide 126 → 106. |
| **N4** contradiction | **Fixed in the description** | The round-5 "the `nameParts` wire format is unchanged" passage is marked **Superseded**, pointing at the breaking-change notice at the top. |
| **N5** stale approval | **Not done** | Re-requesting review was offered and not selected. |
| **N6** #764's artefacts | **Noted only** | Another branch; recorded in this PR's description rather than changed from here. |
| **I1–I4** | **No action** | Informational, as stated. |
| Sourcery thread | **Resolved** | `text_line.py` thread resolved on GitHub; `@final` had answered it structurally. The two `qltysh` threads were left open on purpose — they are the accepted-with-justification duplications, and leaving them visible is more honest than resolving them. |

### Tests added

`ebl/tests/transliteration/test_named_sign_errors.py`, five tests: the `DataError` class itself, **422 on a real falcon route** through the real error handler for both the breaks-over-parts and the negative-sub-index cases, the legacy interpretation of an absent `nameBreaks`, and the required-field message. Three existing tests moved from `ValueError` to `DataError` to match the new contract — none removed, skipped or disabled.

### Gates after the merge and the fixes

| Gate | Result |
| --- | --- |
| `ruff format --check ebl` | 912 files already formatted |
| `ruff check ebl` | All checks passed |
| **pyre** | **No type errors found** |
| pyright (run directly on the changed files) | 0 errors, 0 warnings, 0 informations |
| `pytest` | **4773 passed**, 2 skipped, 1 xfailed |
| Coverage | `sign_token_base.py` and `token_schemas_signs.py` both **100%** |
| flake8 (120 cols) | clean |
| mypy | Success |
| `qlty smells --all --include-tests` | 106 findings, unchanged; zero on the two resolved files |
| `task lint-md` | 0 errors |
| ATF equivalence probe | still byte-for-byte identical to the merge base across 60 cases |

Two gate caveats worth carrying forward:

- **`task type-pyright` diffs `origin/master...HEAD`, so it only sees committed files.** It passed while checking none of the uncommitted work. Running pyright directly on the changed files found 6 real errors, fixed with a `cast` rather than a suppression.
- **Pyre failed once with an internal `End_of_file`**, which was contention with a parallel pytest run, not a type error. Clean on a quiet re-run.

### State

Local `HEAD` is `5935b154` (the merge commit). The remote branch is still `549d45ae`, and **the B3/N1 fixes and the new tests are uncommitted in the working tree**. Nothing has been pushed. Until it is, the PR's mergeability and all its check verdicts describe the pre-fix commit.
