# Media architecture foundation

## Status

Accepted for staged implementation. This document defines the backend media
architecture and contracts only. It does not introduce persistence, GridFS
integration, route registration, migrations, importers, or response changes.

## Problem statement

Fragment images are currently derived from legacy filename and GridFS behavior.
That model supports the existing `hasPhoto`, `thumbnailPath`, photo routes, and
thumbnail routes, but it does not provide stable media identity, multiple media
items per fragment, shared media across fragments, fragment-specific ordering,
fragment-specific primary selection, SVG hand-copies, research-project metadata,
bibliography references, or auditable import provenance.

The redesign introduces an explicit media model before any database or route
implementation so later PRs can be reviewed against stable contracts.

## Goals

- Represent scholarly media as stable UUID-addressed domain objects.
- Support `PHOTO` and `COPY` media types.
- Treat SVG hand-copies as `COPY` media whose original MIME type is
  `image/svg+xml`.
- Support original, optional display, and thumbnail representations.
- Support multiple media items per fragment.
- Support one media item associated with multiple fragments.
- Keep ordering and primary selection on each fragment association.
- Preserve original filename metadata for audit and reconciliation only.
- Support optional research projects, bibliography reference IDs, captions,
  attribution, and import provenance.
- Define compact fragment media summaries for future query results.
- Preserve compatibility with current `hasPhoto`, `thumbnailPath`, photo routes,
  and thumbnail routes during migration.
- Define a non-destructive future GridFS backfill and administrative importer.

## Non-goals

This architecture PR must not:

- create a MongoDB media collection;
- add MongoDB indexes;
- connect the media model to MongoDB or GridFS;
- create GridFS buckets;
- insert media documents;
- update fragment documents;
- modify existing GridFS files or metadata;
- implement a real importer or backfill;
- run migrations;
- register new Falcon routes;
- change fragment queries, DTOs, `hasPhoto`, `thumbnailPath`, photo routes,
  thumbnail routes, or annotation image retrieval.

## Domain model

The pure domain layer owns only persistence-independent concepts:

- `MediaId`: one UUID string used as domain ID, future MongoDB `_id`, and public
  API media ID.
- `MediaType`: `PHOTO` or `COPY`.
- `MediaAssociation`: fragment ID, `sortOrder`, and `isPrimary`.
- `MediaReference`: bibliography ID only.
- `MediaChecksum`: SHA-256 checksum metadata.
- `MediaRepresentation`: MIME type, width, height, file size, and optional
  checksum.
- `MediaRepresentations`: required original representation, optional display
  representation, and optional thumbnails.
- `ThumbnailSize`: `small`, `medium`, and `large`.
- `Media`: aggregate containing identity, type, filename metadata, optional
  projects, associations, references, caption, attribution, and import source.

Domain validation is pure. It may validate UUID shape, checksum algorithm and
value, positive dimensions, positive file size, valid museum number shape,
presence of at least one association, no duplicate fragment associations,
non-negative sort order, deterministic association ordering, canonical MIME
shape, supported raster preview MIME types, `PHOTO` originals as supported
raster image MIME types, and SVG only as `COPY` originals. It must not query
fragment existence or import PyMongo, GridFS, Falcon, application context, or
environment configuration.

## Future persistence proposal

A later PR will introduce a dedicated MongoDB media collection containing
canonical media metadata. GridFS remains the binary store. The collection will be
the source of truth for identity, fragment associations, media type, original
display, and thumbnail representations, projects, references, captions,
attribution, and import provenance.

Proposed document shape, for documentation only:

```json
{
  "_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "PHOTO",
  "originalFilename": "BM-12345-obverse.jpg",
  "projects": ["CAIC"],
  "associations": [
    {
      "fragmentId": "K.1",
      "sortOrder": 0,
      "isPrimary": true
    }
  ],
  "references": [
    {
      "id": "bibliography-id"
    }
  ],
  "caption": null,
  "attribution": null,
  "representations": {
    "original": {
      "storedHandle": "...",
      "mimeType": "image/jpeg",
      "checksum": {
        "algorithm": "sha256",
        "value": "..."
      },
      "width": 4000,
      "height": 3000,
      "fileSize": 5242880
    },
    "display": {
      "storedHandle": "...",
      "mimeType": "image/jpeg",
      "width": 2560,
      "height": 1920,
      "fileSize": 1179648
    },
    "thumbnails": {
      "small": {
        "storedHandle": "...",
        "mimeType": "image/jpeg",
        "width": 240,
        "height": 180,
        "fileSize": 15360
      }
    }
  },
  "importSource": {
    "system": "legacy-gridfs",
    "bucket": "photos",
    "fileId": "legacy-gridfs-id"
  },
  "createdAt": "...",
  "updatedAt": "..."
}
```

`storedHandle` is the serialized form of the application-layer
`StoredRepresentationHandle`. It is server-internal metadata, not a domain field
or API field. Infrastructure-specific values such as GridFS ObjectIds, bucket
names, S3 keys, filesystem paths, or provider version IDs must remain hidden
behind that opaque handle contract. Domain representations only need MIME type,
dimensions, file size, and checksum metadata.

Future indexes, not created in this PR:

```javascript
{ "associations.fragmentId": 1 }
{ "associations.fragmentId": 1, "type": 1 }
{ "representations.original.checksum.value": 1 }
{
  "importSource.system": 1,
  "importSource.bucket": 1,
  "importSource.fileId": 1
}
```

The checksum index must be non-unique. Import-source identity may become unique
for migrated source records. Association ordering may be sorted in application
code. No index should be added before an implemented query requires it.

## Future application boundaries

Application contracts may define these responsibilities:

- `MediaRepository`: persistence-agnostic domain reads plus handle-aware stored
  metadata create, replace, delete, and stored-state reads.
- `MediaRepresentationStore`: future binary representation retrieval and storage
  boundaries without GridFS types in the domain.
- `MediaService`: fragment-context orchestration and batch media reads for
  future summary construction.
- `MediaImporter`: future administrative importer coordination.
- `MediaBackfill`: future non-destructive legacy backfill reporting.

No production implementation is introduced by the architecture foundation.

Stored media metadata is represented by application-layer `StoredMedia`, which
pairs pure `Media` domain metadata with current `StoredMediaRepresentations`.
The stored representation state contains one required original
`StoredRepresentationHandle`, an optional display handle, and typed thumbnail
handles keyed by `ThumbnailSize`. Repository create receives complete
`StoredMedia`. Repository replace atomically switches from previous stored state
to new stored state from the application contract's perspective and returns the
previous `StoredMedia` so the caller can target superseded handles for cleanup.
Domain-oriented read methods continue to return `Media`; stored-state read
methods allow future binary routes to resolve current handles without exposing
them on the wire.

## Future routes

Future fragment-scoped routes:

```text
GET /fragments/{number}/media
GET /fragments/{number}/media/{mediaId}/file
GET /fragments/{number}/media/{mediaId}/display
GET /fragments/{number}/media/{mediaId}/thumbnail/{size}
```

Every future request must verify:

1. The user may read the fragment.
2. The media is associated with that fragment.
3. The requested representation exists.

After authorization, binary routes resolve the current stored version by loading
`StoredMedia` for the fragment/media pair, selecting the requested original,
display, or typed thumbnail handle from `StoredMediaRepresentations`, and then
opening that handle through `MediaRepresentationStore.open_representation`.

Fragment-scoped routes reuse existing fragment authorization, avoid ambiguous
media-only authorization, support media shared by several fragments, reduce IDOR
risk, and keep legacy route delegation straightforward.

Future media-route URL helpers percent-encode each dynamic path segment.
Legacy `thumbnailPath` keeps the existing raw museum-number path for compatibility
until that public contract is intentionally migrated.

## Future DTO contracts

### Query/list summary

```json
{
  "mediaSummary": {
    "count": 3,
    "types": ["PHOTO", "COPY"],
    "primary": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "PHOTO",
      "thumbnail": {
        "url": "/fragments/K.1/media/550e8400-e29b-41d4-a716-446655440000/thumbnail/small",
        "mimeType": "image/jpeg",
        "width": 240,
        "height": 180
      }
    }
  },
  "hasPhoto": true,
  "thumbnailPath": "/fragments/K.1/thumbnail/small"
}
```

Rules:

- `count` counts media objects, not representations.
- `types` contains distinct media types.
- `primary` may be omitted.
- A primary photograph is preferred when available.
- A fragment containing only copies has `hasPhoto: false`.
- `hasPhoto` and `thumbnailPath` remain during migration.
- Current production DTOs must not change in this architecture PR.

### Fragment media response

```json
{
  "media": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "PHOTO",
      "sortOrder": 0,
      "isPrimary": true,
      "caption": "Obverse",
      "attribution": "The British Museum",
      "references": [
        {
          "id": "bibliography-id"
        }
      ],
      "representations": {
        "original": {
          "url": "/fragments/K.1/media/550e8400-e29b-41d4-a716-446655440000/file",
          "mimeType": "image/jpeg",
          "width": 4000,
          "height": 3000
        },
        "display": {
          "url": "/fragments/K.1/media/550e8400-e29b-41d4-a716-446655440000/display",
          "mimeType": "image/jpeg",
          "width": 2560,
          "height": 1920
        },
        "thumbnails": {
          "small": {
            "url": "/fragments/K.1/media/550e8400-e29b-41d4-a716-446655440000/thumbnail/small",
            "mimeType": "image/jpeg",
            "width": 240,
            "height": 180
          }
        }
      }
    }
  ]
}
```

The fragment-context response flattens the matching association into `sortOrder`
and `isPrimary`.

The API must not expose stored handles, GridFS ObjectIds, checksums, import
source, internal filenames, storage buckets, or authorization scopes.

## Future query-performance contract

Future fragment query integration must use this strategy:

```text
fragment query
-> collect all museum numbers on the page
-> one indexed media query using MediaService.find_media_by_fragments and $in
-> narrow projection
-> group in application code
-> attach media summaries
```

The batch media result remains raw domain media. Future fragment-query
integration constructs summaries from that batch result in application code
rather than coupling repository or service access to web DTOs.

Future implementations must not introduce:

- one media query per fragment;
- one GridFS existence query per fragment;
- one media route request per frontend result;
- automatic denormalization into fragment documents without measurements.

## Authorization and binary access

The frontend currently uses bearer-authenticated API requests. A normal
`<img src>` cannot reliably send a bearer token for restricted media. The first
future implementation should support authenticated Blob fetching for media
representations.

Requirements:

- no tokens in URLs;
- no authorization decisions based on `projects`;
- media authorization inherited from fragment context;
- protected media fetched through the authenticated API client;
- possible later optimization for explicitly public representations.

`projects` are metadata such as `["CAIC"]`, not authorization scopes. The
frontend must never infer authorization from project values.

## SVG security

Future SVG behavior is mandatory:

- SVG is accepted only for `COPY`.
- SVG is validated and sanitized server-side.
- Scripts are removed or rejected.
- Event attributes are removed or rejected.
- External references are removed or rejected.
- `foreignObject` is removed or rejected.
- Dangerous processing instructions and entity declarations are rejected.
- A safe XML parser is required.
- Raster display previews are generated when conversion succeeds.
- Raster preview thumbnails are generated.
- Display and thumbnail metadata accepts only supported raster MIME types:
  `image/jpeg`, `image/png`, and `image/webp`.
- `PHOTO` originals accept only supported raster MIME types.
- `COPY` originals accept supported raster MIME types or `image/svg+xml`.
- The initial frontend displays raster previews.
- Original SVG is download-only.
- The frontend never injects raw SVG markup.
- MIME type is determined server-side.
- Filename extension alone is never trusted.

For inline viewing, future clients should prefer `display` when present. If a
display representation is absent and the original is a browser-compatible
raster, the original may still be used inline. SVG originals remain
download-only and require raster display or thumbnail previews for inline use.

The sanitizer and its dependencies are not introduced in this architecture PR.

## Compatibility plan

During migration:

- Existing GridFS-only images remain operational.
- Existing `/fragments/{number}/photo` remains operational.
- Existing `/fragments/{number}/thumbnail/{size}` remains operational.
- Existing `hasPhoto` remains operational.
- Existing `thumbnailPath` remains operational.
- New metadata reads will eventually prefer media records.
- Legacy filename-based behavior remains a fallback until migration verification
  is complete.
- No legacy code is removed in the architecture PR.

## Rollout and rollback overview

Future rollout order:

1. Land persistence-agnostic contracts.
2. Add Mongo media repository and indexes with focused query tests.
3. Add GridFS representation storage and authenticated fragment-scoped reads.
4. Add administrative importer in dry-run mode.
5. Add non-destructive backfill and audit reports.
6. Compare legacy and new media summaries in production-like data.
7. Enable frontend gallery reads behind a feature flag or equivalent rollout
   control.
8. Prefer media records, then retain legacy fallback until verification passes.

Rollback is compatibility-based: disable new media reads and continue serving
legacy photo and thumbnail routes. Since early migration is non-destructive,
legacy GridFS files and fragment documents remain unchanged.

## Future PR boundaries

Later PRs must keep infrastructure, route registration, importer execution,
backfill execution, and migration changes separate enough for review. Any PR
that can write to MongoDB, GridFS, fragments, or production services must state
the side effects explicitly and include rollback or cleanup behavior.
