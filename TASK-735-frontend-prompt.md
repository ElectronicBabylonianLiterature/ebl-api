# Frontend prompt — consume `GET /realia/ids` (backend PR #735)

Hand this file to the agent or developer working in `ebl-frontend`. It is
written to be pasted as a task prompt verbatim.

## Prompt

> The `ebl-api` backend has added an endpoint that lists Realia
> identifiers. Implement the frontend side of it.
>
> Backend PR: ElectronicBabylonianLiterature/ebl-api#735, branch
> `add-realia-slugs-endpoint`.
>
> Before writing any code, read this repository's contributing and
> Copilot instructions and follow the existing conventions for API
> clients, typing, and tests. Do not restructure unrelated code.

### API contract

The backend schema is the source of truth. Align the client to it; do
not ask the backend for aliases or alternate field names.

| Property | Value |
| --- | --- |
| Method and path | `GET /realia/ids` |
| Request parameters | none |
| Response body | JSON array of strings |
| Response on empty collection | `[]` |
| Status | `200 OK` |
| `Cache-Control` | `public, max-age=600` |
| Authentication | as other `/realia` reads: no scope check, guests allowed |

Example response:

```json
["Adad", "Ähre", "apsu", "(Heiliger) Hügel", "Enlil, Ellil", "Zikkurat"]
```

Each string is a Realia entry's `_id` — the headword itself, not a slug
and not a numeric ID. Values are German lemmata and routinely contain
spaces, commas, parentheses, and umlauts. They are returned verbatim;
URL-encode them when building links.

### Two behaviours to get right

**1. Do not re-sort the list.** The backend already sorts it accent- and
case-insensitively (NFKD decomposition, combining marks stripped, case
folded, tie-broken on the original string) so that `Ähre` files under
`A` and lowercase headwords interleave with uppercase ones. Render the
array in the order received.

If a component genuinely must re-sort — for example after merging in
locally added items — use a comparator that matches, and add a test
proving the two agree on `["Zikkurat", "Ähre", "apsu", "Adad"]`:

```ts
const collator = new Intl.Collator('de', { sensitivity: 'base' })
const sorted = [...ids].sort(
  (left, right) => collator.compare(left, right) || (left < right ? -1 : 1)
)
```

**2. The list is deliberately not every Realia entry.** The backend
excludes redirect stubs: entries that carry exactly one cross-reference
and no content of their own. Do not describe this list as "all Realia"
in UI copy or identifier names. `realiaIds` is a good name;
`allRealia` is misleading.

### What to implement

1. An API client function in the existing Realia service module, typed
   to return `Promise<readonly string[]>`, calling `GET /realia/ids`
   through this repo's usual API client so authentication, error
   handling, and base URL are handled the established way.
2. Wire it into whichever component needs the index. If a Realia
   browse or navigation list already exists, feed it from this endpoint;
   otherwise expose the client function and leave integration to a
   follow-up, but say so in the PR description.
3. Handle the loading and error states the same way sibling Realia
   views do — do not invent a new pattern.
4. Do not add a client-side cache layer. The response already carries
   `Cache-Control: public, max-age=600`, so the browser handles it.

### If the code already calls `/realia/all`

An earlier revision of the backend PR exposed this list at
`/realia/all`. That path is gone. It now resolves to the ordinary
single-entry route, so a Realia entry whose `_id` is literally `"all"`
is reachable again at `GET /realia/all` and returns an entry object, not
an array.

Any existing call to `/realia/all` that expects an array must be changed
to `/realia/ids`. Grep for both `realia/all` and `realia/ids` before you
finish.

### Tests

Add tests alongside the existing Realia service tests covering:

- a successful call returning a list of IDs, asserting the request URL
  is exactly `/realia/ids`
- an empty array response
- an error response propagating the way sibling services propagate it
- if you added a component, that it renders IDs in the order received
  rather than a re-sorted order — seed with
  `["Adad", "Ähre", "apsu", "Zikkurat"]` and assert that exact order
- if you added a re-sorting comparator, that it agrees with the backend
  ordering on the shuffled input above

Keep to the repo's coverage requirements; every line you add or touch
should end covered.

### Acceptance criteria

- `GET /realia/ids` is called through the repo's standard API client
- return type is `readonly string[]`, no `any`
- no `/realia/all` array call remains anywhere in the codebase
- IDs are URL-encoded wherever they are put into a link
- rendering order matches the server's order
- naming and UI copy do not claim the list is exhaustive
- lint, type check, tests, and coverage all pass per the repo's gates

## Notes for the reviewer of the frontend PR

- The two things most likely to go wrong are silent client-side
  re-sorting and unencoded IDs in links — `(Heiliger) Hügel` and
  `Enlil, Ellil` are real headword shapes and both break naive URL
  building.
- If the backend list ever needs to include redirect stubs, that is a
  backend change; do not filter or extend the list client-side.
