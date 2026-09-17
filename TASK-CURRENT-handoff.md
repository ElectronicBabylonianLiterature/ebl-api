<!-- markdownlint-disable MD013 -->

# Handoff — PRs #743 and #764, as of 2026-09-17

One document for both pull requests. It supersedes `TASK-743-r15-handoff.md`.

**These documents are tracked on `migrate-name-breaks`, by explicit request, and
must be deleted before PR #764 merges.** Both branches were cleaned of task
documents so that none reaches `master`, and committing these puts a set back on
one of them. That is a deliberate choice to keep the working record with the
branch, not an oversight — but it means the merge-time cleanup applies to them
too. The same rule as before: no `TASK-*.md` may reach `master`.

## The two pull requests

| | #743 | #764 |
| --- | --- | --- |
| Title | Make the ATF parser visible to the type checkers | Add the nameParts/nameBreaks migration |
| Branch | `fix-type-checker-blind-spots` | `migrate-name-breaks` |
| Local head | `6e627647` | `d83582a2` |
| Pushed head | `a0b74092` — **local commit not pushed** | `31929977` |
| Review decision | `APPROVED`, but given 12 commits back | `REVIEW_REQUIRED` |
| CI | all green | all green, qlty clean, coverage diff 100% |

They ship together. #743 teaches the backend to read both the old and the new
shape; #764 converts the stored data afterwards. **#743 must be deployed before
PR #764's migration is applied** — older code rejects an unknown `nameBreaks`
field.

## What remains to address

### 1. The frontend must read `nameBreaks` — the only real blocker

Brackets that fall *inside* a sign name are no longer in `nameParts`; they are in
a sibling `nameBreaks` array, and the client must interleave the two.

Verified on the running service, this branch against `master`, same document:
24 named signs on both, identical `name`, `value` and `cleanValue` throughout —
but on `master` three of them carry one mixed array. A client that reads only
`nameParts` renders `šu`, `ki`, `ti` where the text says `š[u`, `k]i`, `t[i`.
That is a **wrong reading**, not a cosmetic loss.

**Next step:** merge or queue the matching frontend change, and say so on #743.
Nothing in this repository can close this.

### 2. Push what is already committed

`6e627647` on `fix-type-checker-blind-spots` is local only. GitHub still shows
the 34 stray files it removes.

**Next step:** push it, then confirm #743's CI is still green.

### 3. Push the #764 work

Committed as `d83582a2` — the 14 stray `TASK-764-*.md` deletions and the F10
typing change. Local only.

**Next step:** push it, then confirm CI.

### 4. Informational, no action expected

- **R14-8** — `MemoizingSignRepository` has no production consumer; every
  reference outside the class is in its own test file. Not this PR's problem.
- **R14-9** — `TextLine.merge`'s `cast(L, ...)` is sound only because of
  `@final`, which is static-only. All three checkers enforce it, so a future
  subclass fails `task type` rather than failing at runtime.

### 5. Environment, not a PR finding

This dev container exports `MONGODB_URI` for the **production replica set, with
credentials**. `ebl/tests/conftest.py` reads it only when `CI=true`, so the suite
is safe, but any script that reads the variable hits production. Every gate here
was run under `env -u MONGODB_URI`; the two read-only scans were pointed at it
deliberately.

**Next step:** decide whether the variable belongs in the container, and
**rotate the credential** — it has been in a session transcript since the first
round.

## What is already done

### PR #743 — all ten round-14 findings closed or accounted for

| | |
| --- | --- |
| R14-1 34 stray files | Fixed, in `6e627647` |
| R14-2 frontend `nameBreaks` | **Open — see above** |
| R14-3 migration dry run | Done, clean — see below |
| R14-4 instructions-file scope | **Decided 2026-09-17: stays in #743** |
| R14-5 dead `_StartParser.options` | Removed, with approval, plus its two tests |
| R14-6 facade test blind spot | Fixed — and it caught a real lost re-export, `OrderedSignSchema` |
| R14-7 alternation invariant | Pinned by `test_named_sign_alternation.py` |
| R14-8, R14-9 | Informational, recorded above |
| R14-10 `annotations.json` newline | Fixed |

### PR #764 — all findings closed

Sourcery's two (whole-document `$set`, partial apply) confirmed resolved in
`31929977`. The branch's own F1–F12 checked one by one against the tree:
F1–F8, F11, F12 already fixed; **F10 fixed this round** (PEP 585 built-ins and
`collections.abc` isinstance targets, matching
`ebl/dictionary/migrate_named_entity_tags.py`); **F9 justified, not changed** —
`Any` is correct where the function's whole job is to validate arbitrary stored
data. The 14 stray `TASK-764-*.md` files are removed.

### The migration dry run — clean

Run 2026-09-17 from `31929977` against **`ebldev`** with
`readPreference=secondaryPreferred`, no `--apply`. Exit 0, no
`NonAlternatingName` abort.

| Collection | Would be migrated |
| --- | --- |
| `fragments` | 38 284 |
| `texts` | 0 |
| `chapters` | 220 |

The script stops at the *first* bad document, so a clean run proves less than it
looks. A separate read-only census checked every name array through the script's
own `separate_name_parts`: **5 508 869 name arrays across 328 804 documents,
250 218 breaks, zero non-alternating.** `texts: 0` is confirmed as "holds no
named signs", not a false negative. Nothing was written.

Both were re-run after the F10 change: same counts, byte-identical census.

If the production deployment sets a `MONGODB_DB` other than `ebldev`, that
database needs its own run.

## The right order

1. Push `6e627647` and `d83582a2`.
2. Frontend change merged or queued.
3. Merge #743 and deploy it.
4. `poetry run python -m ebl.transliteration.migrate_name_breaks --apply`.
5. Merge #764, which deletes the migration.
6. Rotate the Mongo credential.

## Merge checklist

- [ ] Frontend `nameBreaks` change merged or queued, confirmed on #743
- [x] #764 migration dry run executed, clean
- [x] Dry-run result recorded in #743's description
- [x] Decision recorded on the `copilot.instructions.md` change — keep in #743
- [ ] `6e627647` pushed
- [x] #764 work committed as `d83582a2`
- [ ] `d83582a2` pushed
- [ ] `git diff --diff-filter=A --name-only -M origin/master...HEAD | grep -v '^ebl/'` empty on **both** branches (currently non-empty on `migrate-name-breaks` by choice, see above)
- [ ] No `TASK-*.md` tracked on either branch — **note: the session's task
      documents are now committed on `migrate-name-breaks` and must be removed
      with `git rm 'TASK-*.md'` before #764 merges**
- [ ] Production Mongo credential rotated
