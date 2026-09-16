<!-- markdownlint-disable MD013 MD041 -->

# TASK-764 Review — PR #764 "Add the nameParts/nameBreaks migration"

| Field | Value |
| --- | --- |
| **Review date** | 2026-09-16 |
| **Pull request** | [#764](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/764) — *Add the nameParts/nameBreaks migration* |
| **Repository** | `ElectronicBabylonianLiterature/ebl-api` |
| **Branch** | `migrate-name-breaks` → `master` |
| **Commit reviewed** | `aaffba18836e78411f3eae9f15cf4d37bd9c4695` (single commit) |
| **Diff** | +355 / −0 across 2 files |
| **Files** | `ebl/transliteration/migrate_name_breaks.py` (132 lines), `ebl/tests/transliteration/test_migrate_name_breaks.py` (223 lines) |
| **Depends on** | [#743](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743) (open) — must merge **and deploy** first |
| **CI status** | All checks green — CodeQL "No new alerts", qlty check "No blocking issues", qlty coverage diff 100.0%, full suite green on 3.11 / 3.12 / pypy-3.11 |
| **Merge state** | `BLOCKED` / `REVIEW_REQUIRED` — waiting on an approving review only, not on a failing check |
| **Existing feedback incorporated** | 1 Sourcery review (2 blocking findings), 2 Sourcery inline comments, 1 Sourcery Reviewer's Guide, 3 qlty commit statuses, CodeQL check output. No human reviews, no other bots. |
| **Dev container changes** | **None** — see the dev container note below |
| **New `.md` files in the PR** | **None** |
| **Verdict** | **Request changes** — *resolved*: every finding was addressed on 2026-09-16, see [Resolution](#resolution) |
| **Findings status** | 12 of 12 addressed in the working tree (uncommitted) |
| **Reviewer** | Claude Opus 5 (automated review, run locally against a throwaway database) |

## At a glance

Nice piece of work — the design is the right one and the guard against a non-alternating array is exactly the instinct you want in something that writes to production. I ran it for real against a throwaway database seeded from the current serializer, and it does what the PR body says: dry run touches nothing, `--apply` splits correctly, recombining the two arrays gives back the original byte for byte, and a second run reports zero. The positional split also matches the grammar exactly, so the "even/odd" assumption is not a guess.

Four things to fix before anyone types `--apply` on production. Sourcery caught the first two; the other two are mine and neither is hard. The big one is that the write is a whole-document `$set`, so anything a user edits while the scan is running gets quietly rolled back — I reproduced that. The dry run also ignores `BATCH_SIZE` entirely and keeps every pending update in memory, and when the guard fires it tells you which token is wrong but not which document it is in, which is not much help across tens of thousands of fragments.

None of this blocks the merge itself — nothing runs on merge. It blocks the run.

## Resolution

Every finding below was addressed on 2026-09-16, in the working tree on this branch. The changes are uncommitted.

| Finding | Status | What changed |
| --- | --- | --- |
| F1 | Fixed | `_migrate_copy` migrates a deep copy, `_update_for` `$set`s only the top-level keys that differ and filters on their pre-migration values, `_apply_updates` sums `matched_count`, `_report_skipped` warns with a re-run instruction |
| F2 | Documented | The module docstring now states the script is resumable and that the response to an abort is to repair the document the error names and re-run. No buffering was introduced, so F3 stays fixed |
| F3 | Fixed | `migrate_collection` counts in dry-run mode without building a batch at all; only `_apply_updates` batches |
| F4 | Fixed | `_migrate_copy` re-raises `NonAlternatingName` prefixed with the collection name and document `_id` |
| F5 | Fixed | `_validate_is_an_array` raises `NonAlternatingName` for anything that is not a non-`str` sequence |
| F6 | Fixed | `migrate` warns, naming the database, for every missing collection |
| F7 | Fixed | The duplicated `mongo_client` / `database` fixtures are gone; the tests use the ones in `ebl/tests/conftest.py` |
| F8 | Fixed | The unused `database` parameter is gone and the client is closed |
| F9 | Fixed | `NameToken = Mapping[str, Any]` replaces `Any` where the shape is known |
| F10 | Partly | `collections.abc` and PEP 585 built-in generics were tried and reverted — see the pyre note below. `typing` spellings are kept so all three checkers pass |
| F11 | Fixed | Renamed to `test_a_refused_name_names_the_collection_and_the_document` |
| F12 | Fixed | `get_database` reads `os.environ["MONGODB_DB"]`, matching the documented contract |

The test file reached 264 lines, over the 250-line hard gate, so it was split into `test_migrate_name_breaks.py` (pure functions and the CLI), `test_migrate_name_breaks_database.py` (database-backed) and `legacy_named_sign.py` (the shared legacy shape). The PR now touches five files.

### A pyre crash worth knowing about

The F1 rewrite made `task type` die with `Pyre encountered an internal exception: Worker_exited_abnormally`, and on another run `End_of_file` — a crash, not a type error, so it reported no location. Bisecting against a pristine tree found the construct:

```python
UpdateOne({"_id": original["_id"], **unchanged_since_read}, {"$set": changed})
```

A `**` unpack inside a dict literal in that position crashes pyre. Building the filter explicitly instead makes all three checkers pass. Nothing was suppressed and no configuration was changed. This is the same class of problem as the `zip(..., strict=)` example in the repository instructions, and it is why F10's PEP 585 suggestion was not taken: the `typing` spellings are the ones that survive all three checkers here.

A second, smaller case: `assert set(update._doc["$set"]) == {"text"}` passed pyright and mypy but pyre rejected it. Rather than cast or ignore, the assertion was replaced with a behavioural test — edit an unrelated field mid-scan, then assert both that the edit survives and that the document is still migrated — which proves the write is narrow without touching a pymongo private at all.

### Re-verification

The original runtime run in [Reproduction Steps](#reproduction-steps) is **void**: the implementation was reworked after it. Re-run against a fresh throwaway database on `127.0.0.1:27017` after the rewrite:

```text
dry run                                fragments 2, texts 0, chapters 1; database unchanged
--apply                                24 named signs split; recombination lossless;
                                       unrelated field preserved; chapter signs migrated
second dry run                         0 / 0 / 0, idempotent
F1: edit to another field mid-scan     user's edit preserved, document still migrated
F1: edit to the migrated field         stale write refused, user's edit preserved,
                                       document left legacy, re-run migrates it
F3: batch held, 1200 docs, SIZE 500    dry run 0, apply 499
F4: non-alternating document           NonAlternatingName: fragments document 'K.7': ...
F6: database without the collections   WARNING: fragments: no such collection in database
                                       'ebl_refix_764_typo'; skipping it
```

Gates after the rewrite: `task format` clean, `task lint` clean, `task type` (pyre) no errors, `task type-pyright` 0/0/0, flake8 clean, mypy clean, migration tests 27 passed at **100%** coverage (103 statements, 0 missed), file lengths 206 / 141 / 122 / 29 — all within 250.

## Summary

The PR adds a one-off, dry-run-by-default migration that splits the legacy interleaved `nameParts` array on named signs into two arrays, `nameParts` (value tokens) and `nameBreaks` (the brackets that fall inside the name), across the `fragments`, `texts` and `chapters` collections. It is the "migrate" step of an expand–migrate–contract sequence whose "expand" step is #743 and whose "contract" step (deleting the `@pre_load` adapter) is a later PR.

What I verified and can confirm:

- **The positional split is correct by construction, not by luck.** The grammar rule is `value_name: value_name_part (broken_away value_name_part)*` (likewise `number_name` and `logogram_name`) in `ebl/transliteration/domain/atf_parsers/lark_parser/ebl_atf_text_line.lark:190-192`, and `broken_away` resolves only to `[` or `]`. Every name the parser can emit therefore has odd length, starts and ends with a `ValueToken`, and alternates. I confirmed this against real serialized output: `k[u]r` dumps as `ValueToken, BrokenAway, ValueToken, BrokenAway, ValueToken`, and in `[ku] ku-nu-u₂` the leading `[` lands at word level, outside `nameParts`.
- **The migration and #743's adapter agree exactly.** `separate_legacy_name_parts` in `ebl/transliteration/application/token_schemas_signs.py` at #743's head uses the same `legacy_parts[0::2]` / `[1::2]` split and the same "skip if `nameBreaks` is already present" guard. Migrated documents will therefore load to exactly what the adapter would have produced from the legacy shape.
- **The recursion targets exactly the right documents.** `data_key="nameParts"` appears on `NamedSignSchema` only (so `Reading`, `Logogram`, `Number`); `GraphemeSchema` and `CompoundGraphemeSchema` derive from `BaseTokenSchema` and carry no `nameParts`. No other stored shape in the codebase uses that key, so keying the recursion on the key name cannot hit an unrelated field.
- **The collection list is complete.** `fragments` (via `text`, `notes`, `introduction`), `chapters` (via `reconstruction`, manuscript lines, `intertext`, notes) and `texts` (via `chapters[].translation[].parts[].tokens[]`, which really can contain a `Reading`) are the only collections that can hold `nameParts`. I seeded a `texts` document with `@akk{k[u]r}` markup and confirmed both that it stores a legacy `nameParts` array and that the migration finds and splits it. `signs` stores no `nameParts`; `annotations`, `joins`, `dossiers`, `findspots`, `realia`, `bibliography` and `cropped_sign_images` hold no transliteration tokens.
- **Every local gate passes**, and the full suite reproduces the PR body's number exactly: 4547 passed.

The problems are all in the write path and the operator experience, not in the split itself.

## Findings

| ID | Severity | Where | Summary | Source |
| --- | --- | --- | --- | --- |
| F1 | **High** | `migrate_name_breaks.py:77-82` | The whole-document `$set` silently discards any concurrent edit to any other field | Sourcery, confirmed and reproduced |
| F2 | **Medium** | `migrate_name_breaks.py:85-96` | `--apply` writes batches before the collection has been fully validated, so the guard can leave a partly migrated run | Sourcery, confirmed — but less severe than rated, and the suggested patch would regress F3 |
| F3 | **Medium** | `migrate_name_breaks.py:87-95` | A dry run ignores `BATCH_SIZE` and retains one `UpdateOne` per changed document for the whole scan | New — not reported by any bot |
| F4 | **Medium** | `migrate_name_breaks.py:45-53`, `77-82` | The guard's error identifies the offending token but neither the document nor the collection | New |
| F5 | Low | `migrate_name_breaks.py:45-46` | A `nameParts` that is not a sequence raises a bare `TypeError`, diverging from #743's adapter | New |
| F6 | Low | `migrate_name_breaks.py:99-111` | A mistyped `MONGODB_DB` produces no output and exit 0, indistinguishable from "nothing to do" | New |
| F7 | Low | `test_migrate_name_breaks.py:104-126` | `mongo_client` and `database` duplicate fixtures that already exist in `ebl/tests/conftest.py`, and shadow them with a second in-memory server | New |
| F8 | Nit | `test_migrate_name_breaks.py:174-178` | Unused `database` fixture parameter; the `MongoClient` created in the test is never closed | New |
| F9 | Nit | `migrate_name_breaks.py:45-58` | `Any` is used where the shape is known to be `Mapping[str, Any]` | New |
| F10 | Nit | `migrate_name_breaks.py:17`, `48` | `typing.Mapping` as an `isinstance` target, and `typing.List/Dict/Tuple` where the neighbouring migrations use PEP 585 built-ins | New |
| F11 | Nit | `test_migrate_name_breaks.py:72` | `test_a_refused_name_stops_the_document` — it stops the whole collection scan, not the document | New |
| F12 | Nit | `migrate_name_breaks.py:1-12` | The docstring and PR body say `MONGODB_DB` must be set explicitly; the code makes it optional | New |

### Details

#### F1 — The whole-document `$set` silently discards concurrent edits (High)

```python
def _pending_updates(collection: Collection) -> Iterator[UpdateOne]:
    for document in collection.find({}):
        document_id = document["_id"]
        if migrate_document(document):
            del document["_id"]
            yield UpdateOne({"_id": document_id}, {"$set": document})
```

The document is read at the top of a scan that may run for many minutes, then written back in full — every top-level field, not just the one that changed. Anything a user edits in between is overwritten by the stale snapshot. There is no version predicate and no write freeze mentioned anywhere in the PR body or the module docstring.

I reproduced this deterministically: read the pending updates, edit an unrelated `notes` field the way a user would, then let the bulk write run. The edit is gone and `notes` is back to its pre-migration value. This is not a theoretical race — the scan window is the whole collection, and `fragments` is the collection people edit all day.

Sourcery's suggested direction (targeted updates or an optimistic-concurrency predicate) is right, and the second half of it is the easy one here. Because the split is deep inside arrays a targeted path expression is awkward, but a predicate is not:

```python
UpdateOne({"_id": document_id, "text": original_text}, {"$set": {"text": migrated_text}})
```

That both narrows the write to the one top-level key that actually changed and refuses to apply to a document that moved underneath the scan. `bulk_write` then reports `matched_count`, and any shortfall is exactly the set of documents that were edited concurrently — re-run the script and they get picked up, because it is idempotent.

It is also worth noting that the existing migration next door, `ebl/dictionary/migrate_named_entity_tags.py:38-44`, already does the narrow thing: `{"$set": {"pos": grammatical, "namedEntityTags": merged}}`. This PR is the one that deviates from the house pattern.

If a predicate is more surgery than you want, the alternative is to say plainly in the module docstring and the PR body that the site must be read-only for the duration. Right now neither the code nor the documentation protects against this, which is the part that makes it High rather than Medium.

#### F2 — `--apply` can stop half-done (Medium; Sourcery rated it blocking)

`migrate_collection` flushes a batch every `BATCH_SIZE` documents, but `NonAlternatingName` can be raised by any later document in the same scan. If it fires after at least one flush, the collection is partly migrated and the process exits with a traceback.

This is real, and I reproduced the abort. But two things make it less severe than Sourcery's rating suggests, and they should be said out loud rather than patched around:

- The partial state is **not corrupt**. Every document that was written is fully and correctly migrated, and every document that was not is untouched legacy. Because the script skips documents that already carry `nameBreaks`, fixing the offending document and re-running resumes cleanly. This is a *partial* run, not a *damaged* one.
- The dry run is already a complete validation pass. Running the dry run first — which the script's default makes the natural thing to do — surfaces the guard before `--apply` writes anything. I confirmed this end to end: the dry run exits 1 on a non-alternating document with the database unchanged.

I would **not** take Sourcery's suggested patch as written:

```python
updates: List[UpdateOne] = list(_pending_updates(collection))
```

Materialising the whole collection fixes the ordering but makes F3 unconditional — it would retain every pending update in both modes, not just the dry run. The better shape is the one already implied by the design: keep streaming, and make the failure legible (F4) so that a partial run tells the operator where it stopped and what to fix. If you do want a hard guarantee, gate `--apply` on a validation pass over the same collection first, rather than on buffering the writes.

Worth adding to the PR body either way: a sentence saying that `--apply` is resumable and that the correct response to an abort is to fix the document and re-run.

#### F3 — A dry run keeps every pending update in memory (Medium; not reported by any bot)

```python
batch: List[UpdateOne] = []
for update in _pending_updates(collection):
    migrated += 1
    batch.append(update)
    if len(batch) >= BATCH_SIZE and not dry_run:
        collection.bulk_write(batch)
        batch = []
```

`batch.append(update)` is unconditional, but both places that reset `batch` are guarded by `not dry_run`. In a dry run the list is therefore never cleared: it grows to one `UpdateOne` per changed document, and each of those holds a full copy of the mutated document. `BATCH_SIZE` has no effect at all in the mode that is the default and the one people will run first, on the largest collections, on a laptop.

Measured by reading `migrate_collection`'s own `batch` local at every yield, over 1200 documents with `BATCH_SIZE = 500`:

```text
dry run: 1200 documents changed, largest `batch` list held = 1200
apply  : 1200 documents changed, largest `batch` list held = 499
```

The fix is one line:

```python
for update in _pending_updates(collection):
    migrated += 1
    if dry_run:
        continue
    batch.append(update)
    if len(batch) >= BATCH_SIZE:
        collection.bulk_write(batch)
        batch = []
if batch:
    collection.bulk_write(batch)
```

That also removes the two `and not dry_run` conditions, which is what made the bug easy to miss in the first place.

#### F4 — The guard does not say which document it refused (Medium; not reported by any bot)

The error message is careful about *what* is wrong and silent about *where*:

```text
NonAlternatingName: Expected a BrokenAway at position 1 of nameParts, found {'type': 'ValueToken', 'value': 'b'}. Splitting by position would move it into the wrong array; refusing to migrate.
```

I confirmed that the collection name and the `_id` appear nowhere in the traceback. The guard's whole purpose is to hand a human a problem to go and fix, and across tens of thousands of fragments a token value of `'b'` is not enough to find it. This is also what turns F2 from an annoyance into a real operational problem: after a partial `--apply` you know the run stopped, but not what to repair before resuming.

`_pending_updates` is the natural place to add the context, since it is the only layer that knows both:

```python
for document in collection.find({}):
    document_id = document["_id"]
    try:
        changed = migrate_document(document)
    except NonAlternatingName as error:
        raise NonAlternatingName(f"{collection.name}/{document_id}: {error}") from error
```

#### F5 — A non-sequence `nameParts` raises the wrong error (Low)

`migrate_document({"nameParts": None})` raises `TypeError: 'NoneType' object is not iterable` from `enumerate`, not `NonAlternatingName`. #743's adapter deliberately handles this case — `if not isinstance(legacy_parts, Sequence) or isinstance(legacy_parts, str): return data` — so the two disagree on malformed input. Neither shape should exist, but the point of the guard is that the migration fails *legibly* on data that surprises it, and a bare `TypeError` out of a comprehension is not that. Validate that the value is a non-`str` `Sequence` and raise `NonAlternatingName` with the same "refusing to migrate" wording.

#### F6 — A mistyped database name looks like success (Low)

`migrate` logs one line per collection it finds and nothing at all for collections it does not:

```python
for name in COLLECTIONS:
    if name in existing:
        counts[name] = migrate_collection(database[name], dry_run)
        logger.info(...)
```

Point it at `ebl_prod` instead of `ebl` and you get no output whatsoever and exit 0. For a script whose entire safety story is "run the dry run first and read the counts", silence that means "wrong database" and silence that means "nothing to do" should not look identical. Log a warning per missing collection, or fail outright when none of the three exist.

#### F7 — The test fixtures duplicate, and shadow, the ones in `conftest.py` (Low)

```python
@pytest.fixture(scope="module")
def mongo_client():
    if os.getenv("CI") == "true":
        return MongoClient(os.environ["MONGODB_URI"])
    os.environ.setdefault("PYMONGOIM__OPERATING_SYSTEM", "ubuntu")
    ...
```

`ebl/tests/conftest.py:104-121` already defines `mongo_client` (session-scoped) and a `database` fixture with an identical body, and that conftest applies to `ebl/tests/transliteration/`. The local copies are line-for-line the same apart from the scope, so they add roughly twenty duplicated lines and start a second `pymongo_inmemory` mongod for this one module during a full-suite run. Deleting both and relying on the conftest fixtures loses nothing.

#### F8 — Unused fixture and an unclosed client (Nit)

```python
def test_get_database_uses_the_environment(monkeypatch, database) -> None:
    monkeypatch.setenv("MONGODB_URI", "mongodb://127.0.0.1:27017")
```

`database` is never used in the body, so the test pays for an in-memory server it does not touch. The `MongoClient` that `get_database()` returns is also never closed. Drop the parameter; optionally close the client.

#### F9 — `Any` where the shape is known (Nit)

`separate_name_parts(name_parts: Sequence[Any]) -> Tuple[List[Any], List[Any]]` and `_validate_alternating(name_parts: Sequence[Any])` are looser than the code's own knowledge: `_validate_alternating` asserts every element is a `Mapping` with a `type` key. `Sequence[Mapping[str, Any]]` and `Tuple[List[Mapping[str, Any]], List[Mapping[str, Any]]]` document the contract and cost nothing. `migrate_document(document: Any)` is genuinely polymorphic over raw BSON and is fine as it is.

#### F10 — Deprecated and inconsistent typing spellings (Nit)

`Mapping` is imported from `typing` and used as an `isinstance` target at line 48; `collections.abc.Mapping` is the non-deprecated spelling for that use. Separately, the two migrations this one says it follows — `ebl/dictionary/migrate_named_entity_tags.py` and `ebl/fragmentarium/migrate_cropped_images.py` — use PEP 585 built-in generics (`list[str]`, `tuple[...]`), while this file uses `typing.List/Dict/Tuple`. Worth matching the neighbours.

#### F11 — Test name overstates the scope (Nit)

`test_a_refused_name_stops_the_document` asserts that `migrate_collection` raises — the refusal stops the whole collection scan, not one document. `test_a_refused_name_stops_the_migration` reads truer, and matters because F2 is precisely about how much the refusal stops.

#### F12 — Docstring overstates the configuration requirement (Nit)

The module docstring and the PR body both say the script "needs `MONGODB_URI` and `MONGODB_DB` set explicitly", but `get_database` uses `os.environ.get("MONGODB_DB")` and falls back to the database embedded in the URI. Either require it (`os.environ["MONGODB_DB"]`, which would also give F6 for free) or soften the wording.

### Dev container note

**No dev container configuration is touched by this PR.** The diff is exactly two Python files. I checked explicitly because dev container changes deserve close scrutiny: `.devcontainer/devcontainer.json`, `.devcontainer/setup.sh`, `.devcontainer/sync-env.py` and `.devcontainer/README.md` all exist in the repo and none appears in `git diff --name-only master...HEAD`. #743, which must merge first, does not touch them either. Nothing to warn about here.

### Data-shape hard-gate check

The repository rule that two data types must never share one array is the reason this PR exists, so it deserves an explicit verdict rather than a silent pass.

- **Mixed arrays introduced:** none. The PR removes one — the legacy `nameParts` held `ValueToken` and `BrokenAway` objects in a single array, and a reader had to inspect each element's `type` to know which it had. After this runs, `nameParts` holds only value tokens and `nameBreaks` only brackets. I verified this on real migrated documents: every `nameParts` entry is a `ValueToken` and every `nameBreaks` entry is a `BrokenAway`.
- **Split in the domain, merged on the wire?** No. #743 splits both: `name_parts` / `name_breaks` on `NamedSignArguments`, `nameParts` / `nameBreaks` as data keys. Two fields in the domain, two keys on the wire.
- **Shared id space:** not applicable — neither array holds ids, and no invariant spans the two.
- **Discrimination by probing:** worth naming, because the migration does test for a field's presence — `if "nameParts" in document and "nameBreaks" not in document`. That is a *format-version* probe inside a throwaway script, not a *type* discriminator in a model: it asks "has this document been migrated yet", not "what type is this value". The same probe is what makes the script idempotent, and #743's adapter uses the identical test. It does not re-introduce the pattern the gate forbids, and it disappears along with the adapter when the contract step lands.

### Markdown files

**No `.md` files are added by this PR** — the diff is `ebl/transliteration/migrate_name_breaks.py` and `ebl/tests/transliteration/test_migrate_name_breaks.py` only.

One thing to flag about the ordering rather than about this PR: #743, which has to merge before this one runs, currently carries 24 `.md` files, 23 of them `TASK-74*` todo/log/review/handoff files. Those want removing before #743 merges, or they land on `master` ahead of this migration.

### Existing feedback, itemised

Every unresolved item from the PR is addressed above:

| Source | Item | Disposition |
| --- | --- | --- |
| Sourcery inline, `migrate_name_breaks.py:82` | Stale snapshot written back with `$set` on every top-level field | **Agreed and confirmed**, reproduced — F1. Raised to High because neither code nor documentation guards against it. |
| Sourcery inline, `migrate_name_breaks.py:96` | `--apply` flushes batches before the collection is fully validated | **Agreed in substance** — F2. Rated Medium rather than blocking: the partial state is correct-but-incomplete and the script is resumable. The suggested patch is **not** recommended as written, because `list(_pending_updates(...))` would make F3 unconditional. |
| Sourcery assessment | "Needs a human reviewer… a faulty split would survive reverting the migration code" | **Agreed**, and the assessment's own caveat is right: the split is losslessly reversible by recombining the arrays. I verified that recombination reproduces the original arrays exactly. |
| Sourcery Reviewer's Guide | Flow diagram and file-level change summary | Informational; accurate. No action. |
| qlty check | "No blocking issues" | No findings to address. |
| qlty coverage | 96.0% overall, 0.0% change; coverage diff 100.0% against a 75% threshold | Confirmed locally: 74 statements, 0 missed, 100% on the changed module. |
| CodeQL | "No new alerts in code changed by this pull request", 0 annotations | No findings to address. The repository-level alert list is not readable with this token (HTTP 403 on `/code-scanning/alerts`), so this rests on the check's own output rather than on an enumeration of alerts. |
| GitGuardian | Both scans pass | No findings to address. |
| `Analyze (python)` check | Passes overall, but carries one **failure-level annotation**: "CodeQL Action major versions v1 and v2 have been deprecated", plus a Node 20 deprecation warning | **Pre-existing and out of scope for this PR.** `.github/workflows` still pins `github/codeql-action/{init,autobuild,analyze}@v2` and `actions/checkout@v3`. Worth a separate PR; this PR touches no workflow files. |
| `docker` check | "skipping" | By design for a PR from a branch; not a failure. |
| Human reviewers | None yet — `reviewDecision: REVIEW_REQUIRED` is the only reason `mergeStateStatus` is `BLOCKED` | No feedback to incorporate. |

## Severity

| Severity | Findings | Meaning |
| --- | --- | --- |
| **High** | F1 | Data loss on a live database. Must be fixed, or a write freeze must be documented, before `--apply` is run against production. |
| **Medium** | F2, F3, F4 | No data loss, but they make a production run hard to execute safely or to recover from. Fix before running. |
| **Low** | F5, F6, F7 | Robustness, operator safety and test hygiene. Fix in this PR; none of them blocks a run. |
| **Nit** | F8, F9, F10, F11, F12 | Polish. Take or leave. |

Nothing here blocks **merging**. The migration executes only when someone runs the module, so merging the branch changes no behaviour. Every Medium and the High are about the moment `--apply` is typed.

## Reproduction Steps

All of the following were run locally against a throwaway database on `127.0.0.1:27017` — never the URI in `.env`, which points at the live cluster — seeded with documents produced by the current serializer so the legacy shapes are genuine rather than hand-written.

### Setup

```bash
poetry run python - <<'PY'
from ebl.transliteration.application.text_schema import TextSchema
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
legacy = TextSchema().dump(parse_atf_lark("1. k[u]r ki-[i]b KU[R] 1[4]"))
PY
```

### F1 — concurrent edit lost

1. Insert a fragment carrying a legacy `nameParts` array and an unrelated field, `{"notes": "original"}`.
2. `pending = list(migrate_name_breaks._pending_updates(db.fragments))` — the migration's read.
3. `db.fragments.update_one({"_id": "K.1"}, {"$set": {"notes": "edited by a user"}})` — a user's edit, mid-scan.
4. `db.fragments.bulk_write(pending)` — the migration's write.

Observed: `notes` is `'original'`. Expected: `'edited by a user'`. The user's edit is gone.

### F2 — partial apply

1. Seed more than `BATCH_SIZE` valid documents, then one whose `nameParts` is `[ValueToken, ValueToken]`.
2. Run `--apply`.

Observed: earlier batches are written, the run exits 1 on the invalid document, and the collection is partly migrated. Re-running after fixing the document completes cleanly — the partial state is recoverable, which is why this is Medium.

### F3 — dry run retains every update

Read `migrate_collection`'s own `batch` local at each yield, 1200 documents, `BATCH_SIZE = 500`:

```text
dry run: 1200 documents changed, largest `batch` list held = 1200
apply  : 1200 documents changed, largest `batch` list held = 499
```

### F4 — guard does not name the document

Set one document's `nameParts` to `[{"type": "ValueToken", "value": "a"}, {"type": "ValueToken", "value": "b"}]` and run the dry run. The traceback contains the token and the position; it contains neither `K.2` nor `fragments`.

### F5 — wrong error type

```python
migrate_document({"nameParts": None})
# TypeError: 'NoneType' object is not iterable   <- not NonAlternatingName
```

### Happy path, for completeness

This all behaved exactly as the PR body claims.

```text
$ migrate_name_breaks (dry run)  -> exit 0
fragments: 2 documents would be migrated
texts: 0 documents would be migrated
chapters: 1 documents would be migrated
database unchanged by dry run: True
nameBreaks absent after dry run: True

$ migrate_name_breaks --apply  -> exit 0
fragments: 2 documents migrated / texts: 0 / chapters: 1
named signs found: 24 (originally 24)
every migrated sign has nameBreaks: True
every nameParts entry is a ValueToken: True
every nameBreaks entry is a BrokenAway: True
recombining reproduces the original arrays: True
unrelated top-level field preserved: True

$ migrate_name_breaks (dry run)  -> exit 0
fragments: 0 / texts: 0 / chapters: 0        # idempotent
```

And separately, confirming the `texts` collection is legitimately in scope:

```text
legacy named signs stored in `texts`: 1
legacy nameParts: ['ValueToken', 'BrokenAway', 'ValueToken', 'BrokenAway', 'ValueToken']
texts: 1 documents migrated
nameParts now: ['ValueToken', 'ValueToken', 'ValueToken']
nameBreaks now: ['BrokenAway', 'BrokenAway']
```

### Gates run locally on `aaffba18`

| Gate | Result |
| --- | --- |
| `task format` | 828 files already formatted, clean |
| `task lint` (ruff) | All checks passed |
| `task type` (pyre — the gate CI enforces) | No type errors found |
| `task type-pyright` | 0 errors, 0 warnings, 0 informations |
| `poetry run flake8 <changed files> --max-line-length=120` | clean |
| `poetry run mypy <changed files> --ignore-missing-imports` | Success: no issues found in 2 source files |
| `poetry run pytest <migration tests> --cov=ebl.transliteration.migrate_name_breaks --cov-report=term-missing` | 18 passed, 74 statements, 0 missed, **100%** |
| `task test` | **4547 passed**, 2 skipped, 1 xfailed, exit 0 |
| File length limit (250 lines) | 132 and 223 — both within |
| Mixed-type array gate | Passes, and is the point: this PR removes one such array; it introduces none |

## Recommendation

**Request changes.** Merge whenever you like — nothing executes on merge — but do not run `--apply` against production until F1 through F4 are in.

In order:

1. **F1** — narrow the write to the top-level keys that actually changed and add the old value as an update predicate, then report `matched_count` against the number of pending updates. Or, if that is more than you want to build, state the write freeze explicitly in both the module docstring and the PR body. Right now nothing anywhere says the site must be quiet while this runs, and that is the gap.
2. **F3** — the one-line `if dry_run: continue`, which also lets both `and not dry_run` conditions go away.
3. **F4** — wrap the guard in `_pending_updates` so the error carries the collection and `_id`. This is what makes F2 survivable in practice.
4. **F2** — no code change needed beyond F4, but add a sentence to the PR body saying `--apply` is resumable and that the response to an abort is to fix the document and re-run. If you want the stronger guarantee, validate the collection in a pass of its own before writing — not by buffering every update, which would undo F3.
5. **F5, F6, F7** in this PR; **F8–F12** at your discretion.

Two things worth keeping as they are, because they are better than they look:

- Recursing on the `nameParts` key rather than walking known paths is the right call. It picks up named signs in fragment notes and introductions, in chapter `intertext`, and in text-level translation markup, none of which the `text.lines[].content[].parts[]` path in the PR body would have reached. The PR body undersells the code here — worth correcting, since a reader checking the path against the implementation will think one of them is wrong.
- The guard itself. Refusing rather than mis-splitting is exactly right for a script that writes to production, and it is what makes everything else in this review a fixable detail rather than a data-integrity question.

Also worth adding to the PR body: the evidence that the even/odd assumption is guaranteed rather than observed. The grammar rule `value_name: value_name_part (broken_away value_name_part)*` is a stronger argument than "everything the parser produces today", and it is the sentence a future reader will want when they are deciding whether the guard can be deleted.

### Before merging

Per the task-tracking rule, remove `TASK-764-todo.md`, `TASK-764-log.md` and this file before this PR is merged. They are local and uncommitted; none of them appears in the PR.
