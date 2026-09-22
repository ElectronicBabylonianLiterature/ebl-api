# TASK-743-r14 — Review of PR #743

| Field | Value |
| --- | --- |
| **Pull request** | [#743 — Make the ATF parser visible to the type checkers](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743) |
| **Repository** | `ElectronicBabylonianLiterature/ebl-api` |
| **Branch** | `fix-type-checker-blind-spots` → `master` |
| **Head reviewed** | `a0b74092c6df5d4350bbdfee939dfba4b26d2ddc` (local tree identical to `origin/refs/heads/fix-type-checker-blind-spots`) |
| **Base (merge-base)** | `e92b43d23791e398487e8a6904f482bb7ec37348` |
| **Diff size** | 214 files, +16 046 / −6 928 |
| **Review round** | 14 |
| **Review date** | 2026-09-17 |
| **Reviewed by** | Claude Code (automated review) |
| **Verdict (2026-09-17)** | **Code approved — do not merge yet.** No correctness defect found. Three release gates are still open, and one of them (the task documents) is a repository-hygiene blocker that can be closed on this branch today. |
| **Blocking to merge** | R14-1 (34 stray files), R14-2 (frontend `nameBreaks`), R14-3 (#764 migration dry run) |
| **Status 2026-09-22** | **All three closed.** R14-1 in `6e627647`; R14-3 by a clean dry run and census; R14-2 by `ebl-frontend` #817. Nothing blocking remains on #743. |
| **Non-blocking findings** | 4 low, 3 informational |
| **Dev container configuration** | **No changes.** Verified — see "Dev container check" below. |
| **CI at head** | All green: Test Python 3.11 / 3.12 / pypy-3.11, CodeQL, Analyze (python), GitGuardian ×2. `qlty check` — *No blocking issues*. |
| **Existing review feedback** | 16 submitted reviews, 42 inline comments, 2 conversation comments — all fetched and reconciled below |
| **Review decision on GitHub** | `APPROVED` (Fabdulla1, 2026-09-01, on `16a84e20`) — 12 commits behind the reviewed head |

---

## Review

Everything I could check, I checked, and it holds up. The full suite passes (4773 tests), all three type checkers are clean, ruff / flake8 / markdownlint are clean, and qlty comes out 25 findings *lighter* than master. I ran the real service on both this branch and master side by side and confirmed the behaviour changes end to end — three routes that returned 500 on master now return 422 or a proper body, and a fragment stored in the *old* `nameParts` shape reads back correctly through the new schema with every name, value and clean value identical to master's.

Every finding from the earlier rounds is genuinely resolved. I re-checked each one against the current tree rather than taking the log's word for it: the `/signs/transliteration` 422 is there, the five `Museum` entries are back to their 3-tuple form (I diffed all 75 enum members between master and head — byte-identical), `NamePart` is properly split into two typed arrays at the domain, Mongo and wire levels, `__all__` in `tokens.py` is whole again with a regression test behind it, and both `# type: ignore` suppressions are gone.

What is holding it up is not code. The branch still carries 34 files that must not reach `master` — the PR's own Gate 3 says so, but it says 28, and the real number has grown. That one is fixable on this branch right now. The other two gates, the frontend change and the #764 migration dry run, are outside this repository and I cannot close them from here.

One thing worth flagging separately: **no dev container, Docker, CI workflow, `pyproject.toml`, `Taskfile` or linter configuration file is touched by this PR.** I checked explicitly because that is the category you asked to be warned about, and it came back empty.

### Details

#### R14-1 — 34 files that must not reach `master` (Blocker · process) — *fixed in round 15*

The branch adds 33 `TASK-*.md` files plus `TASK-749-frontend.patch` at the repository root. The PR description's Gate 3 already forbids this, but quotes **28**; the real count is **34**. The groups added since that number was written are `TASK-745-*`, `TASK-746-*`, `TASK-747-*`, `TASK-748-*` and `TASK-749-*`.

Full list: `TASK-743-fix-handoff.md`, `TASK-743-fix-log.md`, `TASK-743-fix-pr-body.md`, `TASK-743-fix-todo.md`, `TASK-743-log.md`, `TASK-743-r13-codeql-log.md`, `TASK-743-r13-codeql-todo.md`, `TASK-743-r13-fix-log.md`, `TASK-743-r13-fix-todo.md`, `TASK-743-r13-handoff.md`, `TASK-743-r13-qlty-log.md`, `TASK-743-r13-qlty-todo.md`, `TASK-743-r13-watch-log.md`, `TASK-743-r13-watch-todo.md`, `TASK-743-review-log.md`, `TASK-743-review-todo.md`, `TASK-743-review.md`, `TASK-743-todo.md`, `TASK-744-log.md`, `TASK-744-todo.md`, `TASK-745-handoff.md`, `TASK-745-log.md`, `TASK-745-todo.md`, `TASK-746-log.md`, `TASK-746-todo.md`, `TASK-747-log.md`, `TASK-747-todo.md`, `TASK-748-log.md`, `TASK-748-todo.md`, `TASK-749-frontend-brief.md`, `TASK-749-frontend-pr-body.md`, `TASK-749-frontend.patch`, `TASK-749-log.md`, `TASK-749-todo.md`.

This round's own files — `TASK-743-r14-review-todo.md`, `TASK-743-r14-review-log.md` and this document — are untracked and must go the same way. Nothing else in the diff lives outside `ebl/` except `docs/ebl-atf.md` and `.github/instructions/copilot.instructions.md`, both of which are legitimate edits to existing tracked files.

The PR's stated verification command still works and must come back empty before merge:

```bash
git diff --diff-filter=A --name-only -M origin/master...HEAD | grep -v '^ebl/'
```

**Action:** `git rm 'TASK-*.md' TASK-749-frontend.patch`, delete the round-14 files, and update the "28" in the PR description to 34 so the gate text matches reality.

#### R14-2 — The frontend must read `nameBreaks` before this merges (Blocker · external) — *closed 2026-09-16*

Confirmed live rather than from the description. The same fragment document, read through both services:

| Service | Named signs | `nameParts` arrays mixing token types | Signs carrying `nameBreaks` |
| --- | --- | --- | --- |
| `master` (`e92b43d2`) | 24 | **3** | 0 |
| `HEAD` (`a0b74092`) | 24 | **0** | 24 (3 non-empty) |

The three affected signs were `šu` → parts `['š','u']` / breaks `['[']`, `ki` → `['k','i']` / `[']']`, `ti` → `['t','i']` / `['[']`. On master each was a single `nameParts` array interleaving `ValueToken` and `BrokenAway`. A client that reads only `nameParts` will now render `šu`, `ki`, `ti` — silently dropping the break, which is a wrong reading of the text, not a cosmetic loss.

`name`, `value` and `cleanValue` were identical across all 24 signs on both services, so the separation itself is lossless. Nothing to fix here; this is a cross-repository sequencing gate.

**Closed.** `ebl-frontend` #817 merged on 2026-09-16 as `e281f7ba`, verified to be `master`. Its `nameTokens()` returns `nameParts` untouched when `nameBreaks` is absent or `null`, so it renders both shapes and the two repositories no longer have to deploy in lock-step. With R14-1 and R14-3 already closed, **#743 has no blocking findings left.**

#### R14-3 — The #764 migration must be dry-run against production first (Blocker · external)

The `@pre_load` adapter in `NamedSignSchema.separate_legacy_name_parts` does work end to end — I stored a fragment in the pure legacy shape (interleaved `nameParts`, no `nameBreaks` key) and the running service returned 200 with correct separated arrays. So the deploy will not break on old documents.

The risk the PR description names is a stored `nameParts` array that does *not* alternate, which the positional split would mis-read. Supporting evidence in favour of the migration coming back clean: I probed the parser across 17 broken-away shapes (`k]u`, `[ku]`, `k[u]r`, `[k]u[r]`, `bu[l]u[g]`, `{d}[e]n`, `[1]0`, and others) and in every case breaks fell strictly *between* parts, never leading or trailing, and a break-free name always had exactly one part. Every one round-tripped through `[0::2]` / `[1::2]` intact. That is the invariant the adapter needs, and the parser appears to guarantee it — but a dry run against real data is still the only proof, because documents predating the current parser could exist.

#### R14-4 — The `copilot.instructions.md` change is out of scope for this PR (Low) — *partly withdrawn; decided 2026-09-17: keep it in #743*

`.github/instructions/copilot.instructions.md` gains 45 lines — a new `qlty` gate in the pre-commit list and a full `HARD GATE: qlty Must Be Clean` section. It is good content and it is clearly the product of the round-13 qlty investigation, but it is repository governance, not "make the ATF parser visible to the type checkers", and it will be reviewed by whoever reviews a 214-file typing PR rather than by whoever should be reviewing a policy change.

**Suggestion:** split it into its own one-file PR.

**Decision (2026-09-17): the change stays in #743.** Splitting it into its own PR was considered and declined. It is already disclosed in the description, which asks for it to be reviewed as a rules change, so it will not be merged unnoticed. No action follows; this finding is closed.

**Correction (round 15):** the second half of this finding was wrong. The PR description *already* calls the change out explicitly and asks for it to be reviewed as a rules change rather than slipping through inside a typing PR. I missed that paragraph when reading the body. The only open question is whether to split it out, which is a judgement call.

#### R14-5 — `_StartParser.options` has no production consumer (Low) — *fixed in round 15, with approval*

`ebl/transliteration/domain/atf_parsers/lark_parser.py:76-77` keeps an `options` property forwarding to the wrapped `Lark` parser. The only references anywhere are `ebl/tests/transliteration/test_start_parser.py:30-31`. The property exists solely to preserve an attribute the removed `__getattr__` used to forward, and the test exists solely to cover the property.

Related: `test_an_uninitialised_wrapper_raises_attribute_error` (`test_start_parser.py:39-43`) was written against the old `__getattr__`, which looked up `self.__dict__["_parser"]` and re-raised `AttributeError` on a partially built object. With `__getattr__` gone, that test now asserts nothing more than Python's default attribute lookup on an object with no `_parser`. It cannot fail for any change to this class.

**Suggestion:** drop `options` and the two tests that only exist for it, or — if something outside `ebl` really needs it — say so in a comment. Note that removing a test needs explicit approval under the repository rules, so this is a suggestion to raise, not to act on unilaterally.

#### R14-6 — The facade test does not cover the regression it was written for (Low) — *confirmed real, fixed in round 15*

`ebl/tests/test_module_facades.py` was added in response to `tokens.py`'s `__all__` dropping nine locally defined classes, and `test_facade_exports_every_name_it_defines` closes exactly that hole. But the original symptom was that `from ... import *` **lost re-exported names**, and a facade that forgets a re-export still passes all three assertions: `_defined_names` only walks `ClassDef`, `FunctionDef`, `Assign` and `AnnAssign` at module level, so a name that arrives via `from x import y` is invisible to it.

Concretely: removing `"ErasureState"` from `tokens.py`'s `__all__` would break `import *` for every consumer and the suite would stay green.

**Suggestion:** add a fourth assertion that every module-level `ImportFrom` alias bound in a facade module also appears in `__all__`.

**Round 15:** done, and it was not hypothetical. The new `test_facade_exports_every_name_it_re_exports` immediately found a genuine lost re-export — `OrderedSignSchema`, a public class in `mongo_sign_repository` on `master`, moved to `sign_schemas` and dropped from the facade's `__all__`, so `import *` no longer provided it. Restored, along with `get_unicode_from_atf`, `LEMMATIZED_FRAGMENT_TEXT` and `TRANSLITERATED_FRAGMENT_TEXT`.

#### R14-7 — Nothing pins the parser invariant the legacy adapter depends on (Low) — *fixed in round 15*

`separate_legacy_name_parts` (`ebl/transliteration/application/token_schemas_signs.py:72-85`) splits a legacy array positionally with `legacy_parts[0::2]` and `legacy_parts[1::2]`. That is correct if and only if breaks strictly alternate with parts and never lead or trail — the property I verified by probing above. The repository tests pin specific examples (`test_a_legacy_interleaved_payload_is_separated_on_load`, `test_absent_name_breaks_is_read_as_the_legacy_interleaved_format`) but nothing asserts the invariant itself, and `#764`'s `NonAlternatingName` guard lives in another PR.

The failure mode is safe — a hand-built payload with two break-free parts and no `nameBreaks` produces `ValidationError: {'nameBreaks': {0: {'type': ['Must be equal to BrokenAway.']}}}`, i.e. a 422, not silent corruption — so this is about keeping the invariant from drifting, not about a present bug.

**Suggestion:** a property-style test over a table of broken-away ATF shapes asserting `tuple(sign.name_tokens)[0::2] == tuple(sign.name_parts)` and `[1::2] == tuple(sign.name_breaks)`.

**Round 15:** done — `ebl/tests/transliteration/test_named_sign_alternation.py`, 48 cases over 16 shapes, mutation-checked against both `_interleaved` and the legacy splitter.

#### R14-8 — `MemoizingSignRepository` is test-only (Informational)

This PR widens the `SignRepository` ABC with `find_signs_by_order` and `get_unicode_from_atf` and adds the two delegating implementations to `MemoizingSignRepository`, which is right — without them the class would not satisfy its own base. Worth knowing that the class has no production consumer: `create_context` wires `MongoSignRepository` directly, and every reference outside the class is in `ebl/tests/signs/test_memoizing_sign_repository.py`. Not this PR's problem, and not a reason to change anything here.

#### R14-9 — `TextLine`'s cast soundness now rests on `@final` alone (Informational)

Sourcery's only finding was that `merge` returns `cast(L, TextLine.of_iterable(...))` while `L` is bound to `Line`, so a `TextLine` subclass would receive the wrong runtime type. The answer taken — `@final` on `TextLine` — is the right one and all three checkers enforce it, so a future subclass would fail `task type` rather than fail at runtime. There is no runtime or test guard, but there does not need to be; recording it so the reasoning is not lost.

#### R14-10 — `annotations.json` gains no trailing newline (Informational) — *fixed in round 15*

`ebl/fragmentarium/annotations.json` is genuinely fixed: on master the file ends `...],\n}` and `json.load` rejects it with `Expecting property name enclosed in double quotes: line 3 column 1`. Head parses cleanly. The new file has no final newline (`...\"].}` with no `\n` after `}`). Cosmetic, and not worth a round trip on its own.

### Resolved since the last round

Each re-checked against the working tree, not taken from the log.

| Source | Finding | Status |
| --- | --- | --- |
| Fabdulla1, 2026-08-07 | `/signs/transliteration` 422 fix missing | **Resolved.** `ebl/signs/web/signs.py:61-64` catches `LINE_PARSE_ERRORS` → `DataError`. Verified live: master 500, head 422. |
| Fabdulla1, 2026-08-07 | 169-character URL in `annotations_service.py` | **Resolved.** Comment wrapped at `annotations_service.py:133-136`; `flake8 --max-line-length=120` across all 161 changed files reports 0. |
| Fabdulla1, 2026-08-07 | Five `Museum` entries changed `.value` shape | **Resolved.** All five are back to the 3-tuple form in `museum_entries_m_s.py:104-128`. Verified mechanically: all 75 members' `value`, `museum_name`, `city`, `country` and `url` are identical between master and head. |
| Fabdulla1, 2026-08-07 | No focused `SignsVisitor.reset()` test | **Resolved.** `test_signs_visitor.py:118` and `:131`. |
| Fabdulla1, 2026-08-07 | No `_StartParser.parse(start=...)` test | **Resolved by removal**, answered in the PR thread on 2026-08-25 — `parse` no longer takes `start`. `test_parse_uses_default_start` pins the behaviour. See R14-5 for the leftovers. |
| Fabdulla1, 2026-09-01 | `NamePart` violates the one-array/one-type gate | **Resolved.** `sign_token_base.py` now holds `name_parts: Sequence[ValueToken]` and `name_breaks: Sequence[BrokenAway]` with per-array validators; the wire carries `nameParts` / `nameBreaks` through `NameValueTokenSchema` / `NameBreakSchema`, each pinned to one `type`. No `OneOfTokenSchema` on either. Verified live — 0 mixed arrays in 24 signs. |
| Fabdulla1, 2026-09-01 | `tokens.py` `__all__` drops nine classes | **Resolved.** All nine restored; `ebl/tests/test_module_facades.py` guards it. See R14-6 for the residual gap. |
| Fabdulla1, 2026-09-01 | Two `# type: ignore` in `test_fragment_pattern_matcher_site.py` | **Resolved.** No `type: ignore`, `pyre-fixme` or `pyright: ignore` anywhere in the 161 changed files. The only suppressions the branch *adds* are `# noqa: B024` / `# noqa: B027` on `TokenVisitor` in `token_base.py:15-16`, for flake8-bugbear's "abstract base class with no abstract methods" — a false positive for a visitor base whose methods are deliberately concrete no-ops. |
| Sourcery, 2026-07-23 | `TextLine.merge` cast unsound for subclasses | **Resolved** via `@final`. See R14-9. |
| CodeQL — `signs_transformer.py:27` | Unnecessary lambda | **Resolved.** Replaced by the `name_arguments` function. |
| CodeQL — `token_base.py:98,102`, `legacy_transformer_base.py:38,40`, `provenance_lookup.py:8,10,12` | Statement has no effect | **Resolved.** Every `...` body is now `raise NotImplementedError`. |
| CodeQL — `test_named_sign_name.py:5` | Unused import of `ebl` | **Resolved.** Not present. |
| CodeQL — `test_named_sign_name.py:37,71,39,76`, `test_named_sign_errors.py:72` | Assert with a side effect | **Resolved.** Commit `6d0f2829` moved the calls out of the asserts; line 72 of `test_named_sign_errors.py` is now a dict literal. |
| CodeQL — `task_743_migrate_name_breaks_test.py:138` | Mixed `import` / `import from` | **Resolved by removal.** Both migration scripts moved to #764 and no longer exist on this branch. |
| qlty — 18 inline findings across rounds | `similar-code`, `identical-code`, `function-parameters`, `return-statements` | **Resolved or justified.** `qlty check` on the pushed head reports *No blocking issues*. My own reconciliation below. |

### Gate results

All commands run at `a0b74092`, with `MONGODB_URI` unset so nothing could reach the production cluster.

| Gate | Command | Result |
| --- | --- | --- |
| Format | `task format` | 912 files already formatted |
| Lint | `task lint` (ruff) | All checks passed |
| Types — pyre | `task type` | **No type errors found** |
| Types — pyright | `task type-pyright` | 0 errors, 0 warnings, 0 informations (161 files) |
| Types — mypy | `poetry run mypy <161 changed files> --ignore-missing-imports` | Success, no issues |
| Lint — flake8 | `poetry run flake8 <161 changed files> --max-line-length=120` | 0 errors |
| Tests | `poetry run pytest` | **4773 passed, 2 skipped, 1 xfailed** in 609.89 s |
| Markdown | `task lint-md` | 0 errors |
| File length | every changed `*.py` | All ≤ 250 lines. The 29 files over 250 in the repo are all untouched by this PR. |
| Coverage | `poetry run pytest --cov=ebl --cov-report=term-missing` | **All 68 changed source files at 100%**, none below. Repo-wide 97% (18 231 statements, 611 missed) from pre-existing gaps in untouched files. |
| qlty | `qlty smells --all --include-tests`, head vs `origin/master` worktree | 107 findings at head vs **132** at master: 28 removed, 3 introduced |

**Coverage note.** `.coveragerc` sets `omit = ebl/tests/*`, so the 93 changed test files are not measured — that is the project's own configuration, not a gap introduced here. Every changed file that coverage does measure is at 100%, so the touched-lines gate is met without exception.

**qlty reconciliation.** The three introduced findings are all `similar-code` between `__all__` export lists: `transliteration/domain/tokens.py` ↔ `fragmentarium/domain/fragment.py` (mass 64, counted once per file) and `tests/factories/fragment.py` ↔ `tests/fragmentarium/test_museum_number.py` (mass 84). `TASK-743-r13-qlty-log.md` already records the investigation — `__all__` cannot be deleted (3 ruff F401 errors prove it load-bearing), the PEP 484 redundant-alias form is rejected by flake8 outside `__init__.py`, and the only real fix costs 53 consumer rewrites — and records that leaving them justified was an explicit decision. That is precisely the carve-out the instructions allow. qlty Cloud agrees: *No blocking issues* on the pushed head.

### Dev container check

You asked to be warned about dev container configuration changes. There are none, and I verified rather than assumed:

```bash
git diff --name-only $(git merge-base HEAD origin/master) HEAD \
  | grep -Ei 'devcontainer|docker|\.github/workflows|Taskfile|pyproject|poetry.lock|\.vscode|setup\.cfg|mypy\.ini|ruff|qlty|markdownlint|\.gitignore'
```

The only hits are two filenames that happen to contain the string `qlty` (`TASK-743-r13-qlty-log.md`, `TASK-743-r13-qlty-todo.md`). No file under `.devcontainer/`, no `Dockerfile`, no `docker-compose*.yml`, no `.github/workflows/*`, no `pyproject.toml`, no `poetry.lock`, no `Taskfile.dist.yml`, no `.markdownlint.json`, no `ruff.toml`, no `mypy.ini`, no `.gitignore`. The complete set of non-`ebl/` files the PR touches is `docs/ebl-atf.md` (one URL, following the grammar directory rename), `.github/instructions/copilot.instructions.md` (see R14-4) and the 34 stray files in R14-1.

**Separate, and not a PR finding:** while setting up the local run I found that this dev container exports `MONGODB_URI` pointing at the production replica set (`badwcai-ebl0{1,2,3}.srv.mwn.de`, with credentials). `ebl/tests/conftest.py:105-107` only reads it when `CI=true`, so the suite is safe locally, but any script or `poetry run` invocation that reads `MONGODB_URI` will hit production. I ran every gate under `env -u MONGODB_URI` and pinned the service runs to `127.0.0.1:27017`. Worth deciding whether that variable belongs in the container at all — and the credential is now in this session's transcript, so rotating it would be prudent.

---

## Summary

PR #743 renames `atf_parsers/lark_parser/` to `atf_parsers/atf_grammar/` so the `lark_parser` module name stops resolving to a namespace package, then pays down the typing, lint, file-size and modelling debt that became visible once the checkers could see the parser. The largest single modelling change splits `NamedSign.name_parts` — previously `Sequence[Union[ValueToken, BrokenAway]]` — into two typed arrays, `name_parts` and `name_breaks`, structurally separate at the domain, Mongo and wire levels, satisfying the project's one-array/one-type hard gate. Alongside this, several oversized modules and test files are split under the 250-line limit, three routes that returned 500 on malformed input now return 422, and `GET /signs?listAll=true` — which raised `KeyError: '_id'` inside `SignDtoSchema` on master — now returns the sign-name array.

I found no correctness defect. Every prior reviewer finding, from Fabdulla1, Sourcery, qlty and CodeQL, is resolved in the reviewed tree, verified individually. All eleven local gates pass, CI is green at the head commit, and qlty is 25 findings lighter than master. Behaviour was confirmed against the running service on both branches, including reading a fragment stored in the legacy `nameParts` shape.

The PR is not mergeable yet, for reasons that are procedural rather than technical: 34 task-tracking files would land in `master`, the matching frontend change must ship or be queued, and #764's migration must be dry-run against production. The first is fixable on this branch immediately; the other two are cross-repository sequencing.

## Findings

| ID | Finding | Category | Severity | Blocking |
| --- | --- | --- | --- | --- |
| R14-1 | 34 non-`ebl/` files added (33 `TASK-*.md` + `TASK-749-frontend.patch`); the PR's own gate says 28 | Repository hygiene | High | **Yes** |
| R14-2 | `nameParts` wire format changed; a client that ignores `nameBreaks` renders a wrong reading | API contract | High | ~~Yes~~ **Closed 2026-09-16** — `ebl-frontend` #817 (`e281f7ba`) merged |
| R14-3 | #764's migration must be dry-run against production before merge | Data migration | High | **Yes** (external) |
| R14-4 | `.github/instructions/copilot.instructions.md` (+45) is unrelated to this PR's purpose | Scope | Low | No — **decided: keep in #743** |
| R14-5 | `_StartParser.options` has no production consumer; two tests pin behaviour that no longer exists | Dead code / test value | Low | No |
| R14-6 | `test_module_facades.py` does not catch a dropped **re-export**, the original regression | Test coverage | Low | No |
| R14-7 | No test pins the strict-alternation invariant the legacy `@pre_load` split relies on | Test coverage | Low | No |
| R14-8 | `MemoizingSignRepository` has no production consumer | Dead code | Info | No |
| R14-9 | `TextLine`'s `cast(L, ...)` is sound only because of `@final`, which nothing pins at runtime | Type safety | Info | No |
| R14-10 | `annotations.json` (now valid JSON — a fix) has no trailing newline | Nit | Info | No |

## Severity

- **High / blocking (3).** R14-1 is the only one closable inside this repository, and it should be closed before the next review round rather than at merge time — the count has already drifted once. R14-2 and R14-3 are release sequencing and need an owner's confirmation on the PR, not a code change.
- **Low (4).** None affects runtime behaviour. R14-6 and R14-7 are the two worth doing, because both are gaps in tests that exist specifically to prevent a regression that already happened once. R14-4 is a reviewability concern. R14-5 is cleanup and touches test removal, so it needs explicit approval.
- **Informational (3).** Recorded so the reasoning survives; no action expected.

## Reproduction Steps

All commands from the repository root at `a0b74092`, with `MONGODB_URI` unset.

### R14-1 — stray files

```bash
git diff --diff-filter=A --name-only -M origin/master...HEAD | grep -v '^ebl/' | wc -l   # 34, must be 0
```

### R14-2 / R14-3 — wire format and the legacy read path, against the running service

```bash
# head on 8099, master worktree on 8098, both against a scratch local Mongo
git worktree add --detach /tmp/ebl-base "$(git merge-base HEAD origin/master)"
export MONGODB_URI=mongodb://127.0.0.1:27017/ebl_r14_review MONGODB_DB=ebl_r14_review
export EBL_AI_API=http://127.0.0.1:9/unused AUTH0_AUDIENCE=x AUTH0_ISSUER=https://x.invalid/ CACHE_TYPE=null
export AUTH0_PEM="$(poetry run python -c 'import base64;from Cryptodome.PublicKey import RSA;print(base64.b64encode(RSA.generate(2048).publickey().exportKey("PEM")).decode())')"
# seed a fragment whose stored nameParts are interleaved and whose nameBreaks key is absent,
# then GET /fragments/X.0 from both ports and compare nameParts token types
```

Observed: master returns 3 signs whose `nameParts` mix `ValueToken` with `BrokenAway` and carries no `nameBreaks`; head returns 0 mixed arrays and `nameBreaks` on all 24 signs. `name`, `value` and `cleanValue` identical across both.

### Route behaviour, head (8099) vs master (8098)

```text
GET /signs?listAll=true              master 500        head 200 ["KU","NA"]
GET /signs/transliteration/[[[       master 500        head 422 Invalid transliteration: "[[["
GET /signs/transliteration/ku-       master 500        head 422 Invalid transliteration: "ku-"
GET /markup?text=@i{unclosed         master 500        head 422 Invalid markup: "@i{unclosed"
GET /signs/transliteration/ku        master 200        head 200 (identical body)
GET /signs?value=ku&subIndex=abc     master 422        head 422
GET /signs?listAll=true&value=ku     master 422        head 422
```

### R14-6 — the facade test's blind spot

Remove `"ErasureState"` from `__all__` in `ebl/transliteration/domain/tokens.py`, then:

```bash
poetry run pytest ebl/tests/test_module_facades.py -q   # still passes
poetry run python -c "exec('from ebl.transliteration.domain.tokens import *'); ErasureState"  # NameError
```

### R14-7 — the alternation invariant

```bash
poetry run python -c "
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_line
from ebl.transliteration.domain.sign_token_base import NamedSign
def walk(t):
    yield t
    for p in t.parts: yield from walk(p)
for atf in ['1. k]u','1. [ku]','1. k[u]r','1. [k]u[r]','1. bu[l]u[g]','1. {d}[e]n','1. [1]0']:
    for token in parse_line(atf).content:
        for s in walk(token):
            if isinstance(s, NamedSign):
                i = tuple(s.name_tokens)
                assert i[0::2] == tuple(s.name_parts) and i[1::2] == tuple(s.name_breaks), atf
print('alternation holds for every probed shape')
"
```

### Museum value preservation

```bash
poetry run python -c "
from ebl.fragmentarium.domain.museum import Museum
print(len(list(Museum)), 'members')
print({m.name: (m.value, m.museum_name, m.city, m.country, m.url) for m in Museum} is not None)
"
```

Run the same under `PYTHONPATH` pointing at the base worktree and diff: identical for all 75 members.

### qlty reconciliation

```bash
qlty smells --all --include-tests                       # at HEAD → 107 findings
cd /tmp/ebl-base && qlty init --yes --skip-plugins && qlty smells --all --include-tests   # → 132
```

## Recommendation

**Do not merge yet. The code is ready; the release gates are not.**

Before the next round:

1. **Close R14-1 on this branch.** `git rm 'TASK-*.md' TASK-749-frontend.patch`, remove the round-14 files, and correct "28" to "34" in the PR description so the gate text matches what the gate actually finds. This is the one blocker fully under this repository's control, and the count has already drifted once.
2. **Get R14-2 and R14-3 answered on the PR by an owner** — the frontend change merged or queued, and #764's migration dry-run result posted. Both are stated as blocking in the PR's own description; neither can be discharged from this repository.
3. **Consider R14-6 and R14-7.** Two small test additions. Both close gaps in tests whose whole purpose is to prevent a regression that has already happened once on this branch.
4. **Decide on R14-4.** Either split the instructions change into its own PR or name it in the description so it is not merged unnoticed inside a 214-file typing PR.
5. **Leave R14-5, R14-8, R14-9 and R14-10 alone** unless you want the cleanup. R14-5 involves deleting tests, which needs explicit approval under the repository rules.

A note for whoever merges: `reviewDecision` on GitHub reads `APPROVED`, but that approval was given on `16a84e20`, twelve commits before the reviewed head, and it listed three findings as conditions. All three are resolved in the current tree, but the approval predates the fixes rather than confirming them.

**Before merge, delete this file along with the other task documents** — `TASK-743-r14-review.md`, `TASK-743-r14-review-todo.md` and `TASK-743-r14-review-log.md` fall under R14-1 too.

<!-- markdownlint-configure-file { "MD013": false } -->
