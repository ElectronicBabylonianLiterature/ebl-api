# Frontend prompt: separate named-entity tags from realia

Paste the section below into the `ebl-frontend` repo (branch
`add-realia-annotation`). It describes a **breaking** backend contract change.

---

## Task

The backend named-entities API changed shape. Named-entity **tags** (`PN`, `DN`,
…) and **realia** are now two separate layers that are never mixed in one list.
Update the frontend to the new contract. The backend schema is the source of
truth — align the client to it. Do not add aliases for the old shape.

## What changed and why

Previously both kinds shared a single list, and you had to probe an object for
`type` vs `realiaId` to discover which kind it was:

```jsonc
// OLD — kinds intermixed
{ "annotations": [
  { "id": "Entity-1", "type": "PERSONAL_NAME",     "span": ["Word-2"] },
  { "id": "Realia-1", "realiaId": "realia_000846", "span": ["Word-2"] }
]}
```

`word.namedEntities` was likewise a flat id list holding **both** kinds
(`["Entity-1", "Realia-1"]`), resolvable only by joining against
`fragment.namedEntities`.

The two kinds are now separated everywhere.

## New contract

### `POST` and `GET /fragments/{number}/named-entities`

Both use the **same** two-list body. There is no `annotations` key any more.

```jsonc
{
  "namedEntities": [
    { "id": "Entity-1", "type": "PERSONAL_NAME", "span": ["Word-2", "Word-3"] }
  ],
  "realia": [
    { "id": "Realia-1", "realiaId": "realia_000846", "span": ["Word-2"] }
  ]
}
```

- A `namedEntities` entry has `id`, `type`, `span` — **never** `realiaId`.
- A `realia` entry has `id`, `realiaId`, `span` — **never** `type`.
- Either key may be omitted; a missing key means an empty list.
- `GET` returns exactly this shape, with both keys always present.

### Fragment DTO (`GET /fragments/{number}`)

```jsonc
{
  "namedEntities": [ { "id": "Entity-1", "type": "PERSONAL_NAME" } ],
  "realia":        [ { "id": "Realia-1", "realiaId": "realia_000846" } ]
}
```

### Word tokens

`Word` now carries **two** id lists instead of one:

```jsonc
{ "namedEntities": ["Entity-1", "Entity-2"], "realia": ["Realia-1"] }
```

Resolve `word.namedEntities` against `fragment.namedEntities`, and
`word.realia` against `fragment.realia`. **Never** look up an id from one layer
in the other. `word.realia` defaults to `[]` on fragments with no realia.

## Rules the backend now enforces

- **Sending a `realiaId` inside `namedEntities` (or a `type` inside `realia`) is
  a `422`.** The kinds cannot be mixed, even by accident.
- Any unknown key on an annotation is a `422` — this still includes the
  client-derived `tier` and `name`, which `omitDerivedSpanFields` must keep
  stripping.
- `realiaId` must match `^realia_\d+$` and must exist, else `422`.
- **`id` must be unique across BOTH lists together.** Reusing `Entity-1` as a
  realia id is a `422`. Keep generating `Entity-N` / `Realia-N` with independent
  counters — that already satisfies this.
- **Duplicates are silently dropped** (`200`), keeping the first occurrence. A
  duplicate is the *same value on the same token range*: the same `type` on one
  span, or the same `realiaId` on one span. Span **order is irrelevant** —
  `["Word-2","Word-3"]` and `["Word-3","Word-2"]` are the same range.

## Still allowed — do not "fix" these

- Many different tags, and many different realia, on the same fragment.
- The **same** token range carrying **both** a tag and a realia — that is the
  whole point of the feature.
- Two *different* tags on the same token range.
- The same realia (or tag) at two *different* token ranges — a tablet can
  mention one object in two places.

## Suggested work

1. Change the POST body builder to emit `{ namedEntities, realia }` instead of
   `{ annotations }`, partitioning by kind at the point where spans are
   collected rather than at serialization time.
2. Change the GET parser to read the two lists.
3. Split the annotation-span type so a tag and a realia are distinct types
   rather than one union discriminated by an optional `realiaId`. This lets the
   compiler enforce non-intermixing instead of runtime probing.
4. In the read-only view, resolve `word.realia` against `fragment.realia` for
   the realia links, and `word.namedEntities` against `fragment.namedEntities`
   for the tag chips.
5. Keep `omitDerivedSpanFields` — `tier` and `name` are still rejected.
