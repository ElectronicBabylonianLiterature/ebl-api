# TASK-735-align Work Log

Task: align the backend redirect-stub rule with the frontend's
`hasOwnContent`, so `/realia/all` lists exactly the pages that do not
redirect.

## Entries

### 1. Task start

- User approved the recommendation to change the backend rather than the
  frontend, and confirmed with "Do that".
- Tracking files created before any code change.
- Commit authorisation from the earlier task was single-use and is spent;
  this task makes no commits.

### 2. Verified the reallexikon equivalence before relying on it

The frontend redirect test uses `entry.reference !== null`. Checked
`RealiaRepository.ts` line 60: `reference: dto.reference ?
createReference(dto.reference) : null`, and the DTO field is
`ReferenceDto | null`. The backend serialises via
`ReallexikonReferenceField._serialize`, which emits `null` exactly when
the deserialised reference was `None` — i.e. for a missing id, an empty
string, or an object without an `id`. So the backend's
`_is_resolvable_reference` is genuinely equivalent to the frontend's
`reference !== null`; no change needed there.

### 3. Changes

- `OWN_CONTENT_ARRAY_FIELDS` reduced to `afoRegister`, `references`,
  `afoCrossReferences`. `relatedTerms`, `type` and `wikidataId` are
  metadata and no longer count as content, matching the frontend.
- Added the frontend's `reallexikon.length > 1` condition via
  `SINGLE_REALLEXIKON_ENTRY`, so two title-only reallexikon entries count
  as content on both sides.
- `realia_document_shape.ARRAY_FIELDS` no longer derives from
  `OWN_CONTENT_ARRAY_FIELDS`; it now lists every array field in
  `RealiaEntrySchema` explicitly. This matters: shrinking the content
  list must not shrink the malformed-shape guard, or a scalar `type`
  would slip through and 500 the entry route.

### 4. Test updates

Four tests encoded the old rule and were updated rather than deleted:

- `test_list_non_redirect_ids_lists_entries_with_own_content` narrowed to
  the three real content fields.
- New `test_list_non_redirect_ids_treats_metadata_only_entries_as_redirects`
  asserts the opposite for `relatedTerms`, `type`, `wikidataId`.
- The two-null-reference reallexikon case moved from the "excluded" to
  the "listed" parametrisation, matching `reallexikon.length > 1`.

### 5. Equivalence proved exhaustively

The ten hand-picked shapes all agreed, but that is weak evidence, so I
generated the full cross-product: 3 cross-reference counts x 7
reallexikon shapes x 2^6 content-field combinations = **1344 documents**,
inserted together, listed in one query, and compared against a Python
port of `getRedirectTarget`.

Result: **1344 shapes compared, 0 mismatches.** The backend listing rule
and the frontend redirect rule are now equivalent.

### 6. Gates

`task format` 810 files, `task lint` clean, `task type` (pyre) no errors,
`task type-pyright` 0/0/0, `task test` **4416 passed**, 2 skipped,
1 xfailed, realia coverage **100%** over 153 tests, flake8 exit 0,
mypy 0 errors in changed files, `task lint-md` 0 errors. All changed
files well under 250 lines.

### 7. Service re-verification (previous run void after the rewrite)

Seeded an extra metadata-only redirect entry
(`crossReferences: [Enlil]`, `type: ["Divine names"]`) and re-ran:

- `GET /realia/all` → 200, `Cache-Control: public, max-age=600`,
  `["(Heiliger) Hügel", "Ähre", "Anu", "Enlil, Ellil", "ids", "Pig"]`.
- `Metadata-Only` is **absent from the list** — the frontend would have
  redirected it — while `GET /realia/Metadata-Only` still returns 200,
  which is correct: the entry exists, it just does not deserve a sitemap
  URL.
- Every listed ID fetched individually → all 200.
