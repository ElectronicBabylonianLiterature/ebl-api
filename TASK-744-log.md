# TASK-744 Work Log — Frontend PR for the `nameBreaks` split

<!-- markdownlint-disable MD013 -->

## Metadata

- Task: client-side support for the `nameParts` / `nameBreaks` split
- Repository: `ElectronicBabylonianLiterature/ebl-frontend` (TypeScript)
- Related: ebl-api PR #743, commit `2b3b0668` (local, unpushed)
- Started: 2026-09-02
- Constraint: ask before committing and before pushing, every time

## Entries

### 1. Task artefacts created

Created before any work, per the tracking hard gate. This is a new task and
does not inherit the TASK-743 files.

### 2. Environment

`ebl-frontend` is not checked out in this container; only `ebl-api` is. The
frontend will need cloning. `gh repo list` confirms
`ElectronicBabylonianLiterature/ebl-frontend`, TypeScript.

### 3. Backend state this depends on

ebl-api commit `2b3b0668` is **local and unpushed** — the remote branch is
still `16a84e20`. The frontend change therefore cannot be integration-tested
against a deployed backend yet.

### 4. User decisions

Asked two questions before writing code, because both changed the deliverable:

1. **Compatibility.** Answer: **read both shapes.** A `nameTokens(namedSign)`
   helper returns the interleaved list, using `nameBreaks` when present and
   falling back to treating `nameParts` as already interleaved when it is
   absent or null. The frontend therefore works against a backend on either
   side of ebl-api #743, so the two repositories do not have to deploy in
   lock-step.
2. **The migration script.** Answer: **prepare it as a temp file in the backend
   branch; it must not be merged to master, hard-gated in the PR docs.** Done
   in the ebl-api repository — see `TASK-743-fix-log.md` section 17 and
   blocking gate 3 in `TASK-743-fix-pr-body.md`.

### 5. Frontend survey

`ebl-frontend`, default branch `master`, HEAD `cccacb0`. `nameParts` appears in
17 files but only **three** are production code:

| File | Use |
| --- | --- |
| `src/transliteration/domain/token.ts:116` | the `NamedSign` type — `readonly (ValueToken \| Enclosure)[]`, the mixed array itself |
| `src/transliteration/domain/token.ts:217` | `extractEnclosureTypes` maps over it |
| `src/transliteration/domain/accents.ts:117` | `addAccents` reduces over it |

Everything else is test fixtures.

### 6. Change made

Branch `add-name-breaks` off `master`.

- `NamedSign` gains `nameBreaks?: readonly Enclosure[] | null`. `nameParts`
  keeps its existing union type, because in the legacy shape it still holds
  both — narrowing it would break the fallback.
- New exported `nameTokens(namedSign)` returns the interleaved sequence.
- `extractEnclosureTypes` and `addAccents` both read through it, so the two
  places that render or inspect a name see the same order they did before.
- `src/transliteration/domain/nameTokens.test.ts` covers five cases: split
  input, no breaks, a trailing break, a legacy interleaved payload, and an
  explicit `null`.
