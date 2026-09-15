<!-- markdownlint-disable MD013 MD041 -->
Reads the `nameBreaks` array the backend adds in
[ebl-api#743](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743).

A named sign's name used to arrive as one interleaved array. It is now two: the
value tokens stay in `nameParts`, and the brackets that fall *inside* a name
move to a sibling array, `nameBreaks`. Rendering the name as written means
interleaving them back.

```text
before  "nameParts":  [ValueToken("k"), BrokenAway("]"), ValueToken("u")]

after   "nameParts":  [ValueToken("k"), ValueToken("u")]
        "nameBreaks": [BrokenAway("]")]

interleave: parts[0], breaks[0], parts[1], ...  ->  k ] u
```

## Why this matters

Ignoring `nameBreaks` does not break rendering — names still appear. They appear
**without the brackets inside them**, which is a wrong reading of the text
rather than a cosmetic loss. Brackets *around* a name were never in `nameParts`
and are unaffected.

## What changed

`nameTokens()` in `src/transliteration/domain/token.ts` does the interleave, and
returns `nameParts` untouched when `nameBreaks` is absent or `null`.

Reading **both** shapes is deliberate: it means the two repositories do not have
to deploy in lock-step, and it is why `nameParts` keeps its union type rather
than being narrowed to `ValueToken[]`. Narrowing it would break the legacy
fallback.

Both places that walked the name now go through it:

- `extractEnclosureTypes` in `token.ts`
- `addAccents` in `accents.ts`, which is what `DisplayToken` calls to build the
  tokens it renders

## Matching the backend

The interleave was checked against the backend rather than assumed.
`NamedSign._interleaved` zips the two arrays and yields the part, then the break
when there is one; `_validate_name_breaks` enforces at most as many breaks as
parts. The trailing-break case agrees.

## Tests

Five on `nameTokens`: a split name, no breaks, a trailing break, a legacy
already-interleaved payload, and an explicit `null`.

Two more go through `addAccents` with a realistic backend-shaped payload, so a
name is asserted to *render* as `k ] u` rather than only to come back as a list.

`tsc --noEmit` clean, `yarn lint` clean, full suite **435 suites / 4180 tests**
passing.

> [!NOTE]
> This repo needs Node 20, not 22 — `yarn install` and husky's pre-commit hook
> both fail on 22 with `The engine "node" is incompatible`.
