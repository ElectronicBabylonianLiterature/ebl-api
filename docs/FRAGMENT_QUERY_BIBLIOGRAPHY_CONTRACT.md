# `/fragments/query` — `bibliographyDocuments` contract

Applies to `GET /fragments/query` when a `limit` parameter is present, so
the response is a `FragmentQueryResult` rather than a plain `QueryResult`.

## What the field is

`bibliographyDocuments` maps a **reference id** — the `id` of a
`Reference` on any item in `items` — to the CSL-JSON bibliography document
that reference resolves to. It exists so a page of search results can be
rendered without one `/bibliography/{id}` call per reference.

The map is keyed by the id **as it appears on the reference**, not by the
canonical id. When a deprecated entry redirects to a canonical one, the
canonical document is stored under the original reference id, and appears
once per aliasing id.

## Resolution rules

For each distinct reference id on the page:

- **Stored entry, not deprecated** — the canonical document.
- **Deprecated, with a resolvable `redirectTo` chain** — the document at
  the end of the chain.
- **No stored entry** — the key is omitted from the map.
- **`redirectTo` target does not exist** — the last document reached,
  still `deprecated: true`.
- **Chain forms a cycle** — the last document reached, still
  `deprecated: true`.
- **Chain longer than `MAX_REDIRECT_DEPTH` (5)** — the last document
  reached, still `deprecated: true`.

## The deprecated-record rule

**A document returned in `bibliographyDocuments` may carry
`deprecated: true`.** A client that renders a citation from this map must
check the `deprecated` flag; it is not safe to assume every value is a
canonical record.

This is a deliberate divergence from `GET /bibliography/{id}`, which
resolves the same three unresolvable cases by raising — `NotFoundError`
for a dangling `redirectTo`, `DuplicateError` for a cycle or an
over-depth chain (`Bibliography._follow_redirect`). The same entity can
therefore be a `404` on `/bibliography/{id}` and a `200` payload with
`deprecated: true` here.

The reason is that `bibliographyDocuments` is a bulk render aid for a
whole page of results. One unresolvable reference among hundreds must not
fail the search, and returning the last known record lets a client show
something and flag it, rather than showing nothing.

Two flavours of "unresolvable" are answered differently on purpose:

- **No stored entry at all** — nothing to return, so the key is omitted.
  A client that needs it falls back to `/bibliography/{id}` and gets the
  authoritative `404`.
- **A stored entry whose redirect cannot be followed** — the stored entry
  itself is real data, so it is returned, flagged `deprecated: true`.

## Cost

One batched `$in` query per redirect hop, ids deduplicated in first-seen
order. A page with no references issues no bibliography query at all. The
typical page costs exactly one extra query; the per-hop batches only fire
when deprecated entries are present, to a maximum of `MAX_REDIRECT_DEPTH`
additional sequential queries.
