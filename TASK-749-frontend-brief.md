<!-- markdownlint-disable MD013 -->
# Brief — `ebl-frontend` must read `nameBreaks`

**Repository:** `ElectronicBabylonianLiterature/ebl-frontend`, default branch `master`
**Branch to create:** `add-name-breaks`
**Blocks:** `ebl-api` [PR #743](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/743)

This document is self-contained. You do not need access to the `ebl-api` repo,
its pull request, or any prior conversation.

Three files belong together, all in the root of the `ebl-api` repository on
branch `fix-type-checker-blind-spots`:

| File | What it is |
| --- | --- |
| `TASK-749-frontend-brief.md` | this document |
| `TASK-749-frontend.patch` | the finished change, ready for `git am` |
| `TASK-749-frontend-pr-body.md` | the PR description on its own, for `--body-file` |

> [!TIP]
> **The work is already done.** It exists as commit `a9df351`, exported to
> `TASK-749-frontend.patch`, beside this file. To use it, skip to
> [Shortcut](#10-shortcut--apply-the-existing-patch). Everything below is here so the
> change can be reconstructed from scratch if the patch is lost — which has
> already happened once, when a scratchpad clone was cleared.

---

## 1. What changed on the backend

A named sign — a `Reading`, `Logogram` or `Number` — used to send its name as
**one interleaved array**, mixing the value tokens with the brackets that fall
*inside* the name. The backend has split that into **two arrays**.

```text
before  "nameParts":  [ValueToken("k"), BrokenAway("]"), ValueToken("u")]

after   "nameParts":  [ValueToken("k"), ValueToken("u")]
        "nameBreaks": [BrokenAway("]")]

interleave: parts[0], breaks[0], parts[1], breaks[1], ...  ->  k ] u
```

This is a real payload from the new backend, for the reading `k[ur`:

```text
nameParts : ['k', 'ur']
nameBreaks: ['[']
```

There are never more breaks than parts, and they strictly alternate, so position
alone reconstructs the written order. Element shapes are otherwise unchanged.

Brackets *around* a name were never in `nameParts` and are unaffected. Only
brackets **inside** a name moved.

## 2. Why this matters

A client that reads only `nameParts` renders `kur` where the text says `k[ur`.

`[` is not decoration. It marks where the tablet is broken away — an editorial
statement about how much of the sign actually survives. Rendering `kur` asserts
a complete reading of something partly destroyed. That is a **wrong reading of
the source**, not a cosmetic loss.

It also fails **silently**. TypeScript types do not exist at runtime, so nothing
throws; `nameParts` is simply a shorter array and the existing code maps over it
happily. Wrong text, no error anywhere.

It is not only display. `effectiveEnclosure` also feeds
`src/fragmentarium/ui/image-annotation/annotation-tool/mapTokensToAnnotationTokens.ts`,
which branches on `BROKEN_AWAY` to decide how a token is annotated.

## 3. Ordering — this must ship first

The change below **reads both shapes**: it returns `nameParts` untouched when
`nameBreaks` is absent or `null`. That is deliberate.

- **This frontend change can deploy first, safely.** Against today's backend it
  behaves exactly as now.
- **The backend cannot deploy first.** The moment ebl-api #743 is live, any
  un-updated client starts dropping brackets.

So this PR should be merged and deployed **before** ebl-api #743.

## 4. Repository facts you will need

| | |
| --- | --- |
| Package manager | **yarn**, not npm. There is no `package-lock.json` |
| Node | **20**, not 22. `.nvmrc` says `20.0.0` |
| Install time | ~200s |

> [!WARNING]
> On Node 22, `yarn install` fails with
> `The engine "node" is incompatible with this module. Expected version "^20.0.0"`.
> **The same trap breaks `git commit`** — husky's pre-commit hook shells out to
> yarn and dies before running anything. If a Node 20 is present, put it on
> `PATH` first, for example:
> `export PATH="/usr/local/share/nvm/versions/node/v20.19.1/bin:$PATH"`

`nameParts` appears in 17 files, but only **three** are production code. The
rest are test fixtures under `src/test-support/`, which do not need changing —
they are legacy-shaped payloads and the fallback handles them.

| File | Use |
| --- | --- |
| `src/transliteration/domain/token.ts` (~line 116) | the `NamedSign` type |
| `src/transliteration/domain/token.ts` (~line 217) | `extractEnclosureTypes` maps over it |
| `src/transliteration/domain/accents.ts` (~line 117) | `addAccents` reduces over it |

## 5. The task

### 5.1 `src/transliteration/domain/token.ts`

Add the optional field to `NamedSign`:

```ts
export interface NamedSign extends Sign {
  readonly type: 'Reading' | 'Logogram' | 'Number'
  readonly name: string
  readonly nameParts: readonly (ValueToken | Enclosure)[]
  readonly nameBreaks?: readonly Enclosure[] | null
  readonly subIndex?: number | null
  readonly sign?: Token | null
  readonly surrogate?: readonly Token[] | null
}
```

> [!IMPORTANT]
> **Keep `nameParts` typed as the union.** Narrowing it to
> `readonly ValueToken[]` looks tidier and breaks the legacy fallback, because a
> legacy payload really does contain `Enclosure`s in that array.

Add the helper, exported, just above `extractEnclosureTypes`:

```ts
export function nameTokens(
  namedSign: NamedSign,
): readonly (ValueToken | Enclosure)[] {
  const nameBreaks = namedSign.nameBreaks
  if (!nameBreaks) {
    return namedSign.nameParts
  }
  return namedSign.nameParts.flatMap((part, index) =>
    index < nameBreaks.length ? [part, nameBreaks[index]] : [part],
  )
}
```

Route the existing function through it:

```ts
function extractEnclosureTypes(
  namedSign: NamedSign,
): readonly (readonly EnclosureType[])[] {
  return nameTokens(namedSign).map((part) => part.enclosureType)
}
```

### 5.2 `src/transliteration/domain/accents.ts`

Add `nameTokens` to the existing import from `transliteration/domain/token`:

```ts
import {
  AkkadianWord,
  NamedSign,
  Token,
  ValueToken,
  nameTokens,
} from 'transliteration/domain/token'
```

Then route `addAccents` through it:

```ts
export function addAccents(
  namedSign: NamedSign,
): readonly [readonly Token[], boolean] {
  return nameTokens(namedSign).reduce(
    (acc, token) => acc.addToken(token),
    new Accumulator(namedSign.subIndex),
  ).result
}
```

### 5.3 Tests

**`src/transliteration/domain/token.test.ts`** — five cases on `nameTokens`.
Add `nameTokens` to the existing import.

```ts
function name(nameParts: string[], nameBreaks?: string[] | null): NamedSign {
  return {
    nameParts: nameParts.map((value) => ({ value })),
    ...(nameBreaks === undefined
      ? {}
      : { nameBreaks: nameBreaks?.map((value) => ({ value })) ?? nameBreaks }),
  } as unknown as NamedSign
}

function values(namedSign: NamedSign): string[] {
  return nameTokens(namedSign).map((token) => token.value)
}

describe('nameTokens', () => {
  it('interleaves the breaks back between the parts', () => {
    expect(values(name(['k', 'u'], [']']))).toEqual(['k', ']', 'u'])
  })

  it('returns the parts unchanged when there are no breaks', () => {
    expect(values(name(['k', 'u'], []))).toEqual(['k', 'u'])
  })

  it('keeps a trailing break after its part', () => {
    expect(values(name(['ku'], [']']))).toEqual(['ku', ']'])
  })

  it('passes a legacy already-interleaved payload through untouched', () => {
    expect(values(name(['k', ']', 'u']))).toEqual(['k', ']', 'u'])
  })

  it('treats an explicit null as the legacy shape', () => {
    expect(values(name(['k', ']', 'u'], null))).toEqual(['k', ']', 'u'])
  })
})
```

**`src/transliteration/domain/accents.test.ts`** — two more, through the
function the UI actually calls. `DisplayToken.tsx` builds the tokens it renders
with `addAccents`, so asserting here proves a name *renders* as written rather
than merely that a helper returns a list. Change the imports to
`import { addAccents, addBreves } from './accents'` and
`import { AkkadianWord, Enclosure, NamedSign, ValueToken } from './token'`.

```ts
function valuePart(value: string): ValueToken {
  return {
    value,
    cleanValue: value,
    enclosureType: [],
    erasure: 'NONE',
    type: 'ValueToken',
  }
}

const closingBreak = {
  value: ']',
  cleanValue: '',
  enclosureType: ['BROKEN_AWAY'],
  erasure: 'NONE',
  type: 'BrokenAway',
  side: 'RIGHT',
} as unknown as Enclosure

function reading(
  nameParts: readonly (ValueToken | Enclosure)[],
  nameBreaks?: readonly Enclosure[] | null,
): NamedSign {
  return {
    value: 'k]u',
    cleanValue: 'ku',
    enclosureType: [],
    erasure: 'NONE',
    type: 'Reading',
    name: 'ku',
    nameParts,
    nameBreaks,
    subIndex: 1,
    modifiers: [],
    flags: [],
  } as unknown as NamedSign
}

describe('addAccents', () => {
  it('puts a name break back between the parts it separates', () => {
    const [parts] = addAccents(
      reading([valuePart('k'), valuePart('u')], [closingBreak]),
    )

    expect(parts.map((part) => part.value)).toEqual(['k', ']', 'u'])
  })

  it('renders a legacy already-interleaved name unchanged', () => {
    const [parts] = addAccents(
      reading([valuePart('k'), closingBreak, valuePart('u')]),
    )

    expect(parts.map((part) => part.value)).toEqual(['k', ']', 'u'])
  })
})
```

## 6. Gates — all must pass

```bash
export PATH="/usr/local/share/nvm/versions/node/v20.19.1/bin:$PATH"   # Node 20
yarn install --frozen-lockfile
./node_modules/.bin/tsc --noEmit
yarn lint
CI=true yarn test --watchAll=false
```

Expected: `tsc` 0 errors, lint clean, **435 suites / 4180 tests passing**.

## 7. Correctness note

The interleave matches the backend's own implementation rather than being
guessed. On the backend, `NamedSign._interleaved` zips the two arrays with
`zip_longest` and yields the part, then the break when there is one; a validator
enforces at most as many breaks as parts. The trailing-break case therefore
agrees: `parts=['ku'], breaks=[']']` renders `ku]`.

## 8. Commit message

```text
Read nameBreaks alongside nameParts

The backend has split a named sign's name into two arrays. nameParts keeps the
value tokens; the brackets that fall inside a name now live in a sibling array,
nameBreaks. Rendering a name as written means interleaving the two.

    before  nameParts:  [ValueToken("k"), BrokenAway("]"), ValueToken("u")]
    after   nameParts:  [ValueToken("k"), ValueToken("u")]
            nameBreaks: [BrokenAway("]")]

nameTokens() does that interleave, and returns nameParts untouched when
nameBreaks is absent or null. Reading both shapes means the two repositories do
not have to deploy in lock-step, and it is why nameParts keeps its union type
rather than being narrowed to ValueToken.

Both places that walked the name go through it: extractEnclosureTypes in
token.ts and addAccents in accents.ts. A client that ignored nameBreaks would
still render names, but would silently drop brackets inside them, which is a
wrong reading of the text rather than a cosmetic loss.

The interleave matches the backend's own: NamedSign._interleaved zips the two
arrays and yields the part then the break when there is one, with at most as
many breaks as parts.

Tests cover a split name, no breaks, a trailing break, a legacy already
interleaved payload, and an explicit null. Two more go through addAccents,
which is what DisplayToken actually calls, so a name is asserted to render as
written rather than only to come back as a list.
```

## 9. PR body

Title: **Read nameBreaks alongside nameParts**

Everything between the markers is the description. Cross-link ebl-api #743.

<!-- PR BODY START -->

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

### Why this matters

Ignoring `nameBreaks` does not break rendering — names still appear. They appear
**without the brackets inside them**, which is a wrong reading of the text
rather than a cosmetic loss. Brackets *around* a name were never in `nameParts`
and are unaffected.

### What changed

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

### Matching the backend

The interleave was checked against the backend rather than assumed.
`NamedSign._interleaved` zips the two arrays and yields the part, then the break
when there is one; `_validate_name_breaks` enforces at most as many breaks as
parts. The trailing-break case agrees.

### Tests

Five on `nameTokens`: a split name, no breaks, a trailing break, a legacy
already-interleaved payload, and an explicit `null`.

Two more go through `addAccents` with a realistic backend-shaped payload, so a
name is asserted to *render* as `k ] u` rather than only to come back as a list.

`tsc --noEmit` clean, `yarn lint` clean, full suite **435 suites / 4180 tests**
passing.

> [!NOTE]
> This repo needs Node 20, not 22 — `yarn install` and husky's pre-commit hook
> both fail on 22 with `The engine "node" is incompatible`.

<!-- PR BODY END -->

## 10. Shortcut — apply the existing patch

`TASK-749-frontend.patch` reproduces commit `a9df351`
exactly, message and authorship included:

```bash
git clone https://github.com/ElectronicBabylonianLiterature/ebl-frontend
cd ebl-frontend
git checkout -b add-name-breaks
git am /path/to/TASK-749-frontend.patch
git push -u origin add-name-breaks
gh pr create --base master --head add-name-breaks \
  --title "Read nameBreaks alongside nameParts" \
  --body-file /path/to/TASK-749-frontend-pr-body.md
```

## 11. Known blocker

The branch could not be pushed from the Codespace where it was written. Its
token is scoped to `ebl-api`, the repo the Codespace was created from, so
`ebl-frontend` returns `403 Permission denied` and the Git Data API returns
`Resource not accessible by integration`. `gh api repos/.../ebl-frontend
--jq .permissions` reporting `push: true` is misleading — that describes the
**user's** rights, not the token's scope.

Push from an environment with credentials for `ebl-frontend`. A local IDE
signed in as the user generally can, even when the terminal in the same
Codespace cannot.
