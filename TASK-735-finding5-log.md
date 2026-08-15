# TASK-735-finding5 Work Log

Task: explain Finding 5 (the redirect-stub rule) so the user can decide.

## Entries

### 1. Task start

- Created tracking files before investigating, per the task-tracking gate.
- No code change is in scope until a decision is given.

### 2. Truth table of the current backend rule

Built against a real local MongoDB. An entry is excluded from
`/realia/all` only when it has **exactly one** cross-reference **and** no
own content. Everything else is listed, including a completely empty
document.

### 3. The frontend already has its own definition

`ebl-frontend` master, `src/realia/domain/RealiaEntry.ts`:

```ts
function hasOwnContent(entry) {
  return [
    entry.afoRegister.length > 0,
    entry.references.length > 0,
    entry.afoCrossReferences.length > 0,
    entry.reallexikon.length > 1,
    !isStubReallexikon(entry.reallexikon),
  ].some(Boolean)
}

export function getRedirectTarget(entry) {
  return !hasOwnContent(entry) && entry.crossReferences.length === 1
    ? entry.crossReferences[0]
    : null
}
```

Two conclusions:

- The **"exactly one cross-reference" test is correct** — it mirrors
  `crossReferences.length === 1` exactly. My original Finding 5 concern
  about 2+ cross-references is a non-issue: the frontend does not
  redirect those, it renders a page with a "See also" list, so listing
  them is right.
- The **own-content field lists do not match**. The backend counts
  `type`, `relatedTerms` and `wikidataId` as content; the frontend does
  not. The backend requires a *resolvable* reallexikon reference; the
  frontend counts `reallexikon.length > 1` regardless.

### 4. Mismatches confirmed empirically

Ported `getRedirectTarget` to Python and compared it against the real
Mongo query for ten entry shapes:

- 1 cross-ref + only `type` → listed, but the frontend redirects away
- 1 cross-ref + only `relatedTerms` → same
- 1 cross-ref + only `wikidataId` → same
- 1 cross-ref + 2 reallexikon with null references → excluded, but the
  frontend renders a real page
- all other shapes agree

So the real decision is about the definition of "own content", not about
the cross-reference count. A completely empty entry is also listed by
both rules, which is a separate question.
