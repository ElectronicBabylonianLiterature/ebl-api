# Media importer, backfill, and security contracts

This document defines future operational contracts for media import, legacy
backfill, binary access, and SVG security. It is architecture-only. No CLI,
database migration, GridFS bucket, sanitizer, route, or production dependency is
introduced here.

## Future administrative importer

The importer will be an administrative tool for creating or replacing media
records and binary representations after the persistence and representation
store layers exist.

Expected modes:

```text
--dry-run
--skip-existing
--replace
```

### Responsibilities

- Validate MIME type from server-side inspection, not filename extension.
- Validate image dimensions and decoded pixel count before storage.
- Enforce configurable limits for file size, dimensions, decoded pixels,
  thumbnail generation time, and batch size.
- Calculate SHA-256 for every original representation.
- Resolve fragment aliases to canonical museum numbers before creating
  associations.
- Upload the original representation.
- Generate and upload raster thumbnails.
- Insert the media document last.
- Preserve stable media identity during replacement.
- Preserve `originalFilename` for audit and reconciliation.
- Record optional import provenance for idempotency.
- Report checksum duplicates without silently merging records.
- Clean up files created during a normal failed attempt.
- Produce structured results with created, skipped, replaced, warning, and error
  counts.

### Insert-last lifecycle

```text
validate
-> calculate checksum
-> upload original
-> generate and upload thumbnails
-> insert media document last
```

The media document is inserted last so a document never points at missing binary
representations during normal failures. If a normal failure happens after one or
more files were written, the future implementation must delete the files created
for that failed attempt.

A hard crash can still leave orphaned representation files. That case is handled
by a future orphan audit, not by introducing `PENDING`, `READY`, or `FAILED`
media states in the initial model.

### Replacement behavior

Replacement changes representation metadata and storage references while
preserving the media ID. The media ID must never be derived from filename,
museum number, checksum, or GridFS ObjectId. Replacement must verify the
requested media is associated with the target fragment when invoked in a
fragment-scoped administrative flow.

### Duplicate checksums

Checksum supports duplicate detection, auditing, future ETags, and replacement
verification. It does not define identity and must not be treated as globally
unique. Duplicate reports should include enough source context for an
administrator to decide whether files are intentional duplicates, shared media,
or import mistakes.

## Future non-destructive backfill

The backfill will create media metadata for legacy GridFS files without
modifying existing fragments or legacy files.

### Responsibilities

- Iterate GridFS metadata using cursors.
- Avoid loading all files into memory.
- Parse current filename conventions.
- Resolve aliases to canonical museum numbers.
- Pair originals and thumbnails.
- Use original GridFS source identity for idempotency.
- Support dry-run.
- Support bounded batches.
- Support restart and resume.
- Avoid modifying fragment documents.
- Avoid deleting or renaming GridFS files.
- Produce audit reports.

### Source idempotency

Future media records may include:

```json
{
  "importSource": {
    "system": "legacy-gridfs",
    "bucket": "photos",
    "fileId": "legacy-gridfs-id"
  }
}
```

The source identity lets the backfill distinguish already migrated files from
new candidates. A future import-source identity index may become unique for
migrated legacy source records, but no index is added until the query exists.

### Required reports

The backfill must report:

- ambiguous filenames;
- unknown fragments;
- orphaned originals;
- orphaned thumbnails;
- missing thumbnails;
- multiple originals per fragment;
- duplicate checksums;
- unsupported MIME types;
- legacy/new `hasPhoto` mismatches;
- orphaned new-media GridFS files.

### Backfill boundaries

The backfill must not:

- update fragment documents;
- rewrite legacy GridFS metadata;
- delete or rename legacy files;
- assume filename-derived identity is canonical;
- silently merge checksum duplicates;
- require all source files to fit in memory.

## Orphan audit

A later orphan audit command will identify representation files that do not have
corresponding media metadata. It exists to handle hard crashes and interrupted
administrative operations. It should report candidates first and require a
separate explicit cleanup action if deletion is ever introduced.

The audit should cover:

- files created by failed imports;
- files created by failed replacements;
- thumbnails without originals;
- originals without thumbnails;
- storage references not reachable from media records.

## Binary authentication

Future binary routes remain fragment-scoped:

```text
GET /fragments/{number}/media/{mediaId}/file
GET /fragments/{number}/media/{mediaId}/thumbnail/{size}
```

Each request must verify:

1. The user may read the fragment.
2. The media is associated with that fragment.
3. The requested representation exists.

The frontend currently uses bearer-authenticated API requests. A normal
`<img src>` cannot reliably send bearer tokens for restricted media. The initial
future implementation should therefore fetch protected representations through
the authenticated API client as Blobs.

Requirements:

- no tokens in URLs;
- no authorization decisions based on `projects`;
- fragment-scoped authorization;
- protected media fetched through the authenticated API client;
- possible later optimization for explicitly public representations.

`projects` remain descriptive research-project metadata such as `["CAIC"]`.
They are not authorization scopes, and frontend code must never infer access
from them.

## SVG security

SVG hand-copies are represented as:

```text
type = COPY
original.mimeType = image/svg+xml
```

SVG is not a third media type.

### Mandatory future behavior

- SVG is accepted only for `COPY`.
- SVG is validated and sanitized server-side.
- Scripts are removed or rejected.
- Event attributes are removed or rejected.
- External references are removed or rejected.
- `foreignObject` is removed or rejected.
- Dangerous processing instructions and entity declarations are rejected.
- A safe XML parser is required.
- Raster preview thumbnails are generated.
- The initial frontend displays raster previews.
- Original SVG is download-only.
- The frontend never injects raw SVG markup.
- MIME type is determined server-side.
- Filename extension alone is never trusted.

No sanitizer implementation or dependency is added by this architecture PR.

## MIME and image validation

Future infrastructure must validate media by inspecting content. Filename
extension and user-provided MIME type are advisory only.

Validation should include:

- accepted MIME allowlist;
- decoded image dimensions;
- decoded pixel count;
- file size;
- thumbnail generation compatibility;
- SVG sanitization for copies;
- checksum calculation after reading canonical bytes.

Unsupported MIME types should be rejected by import and reported by backfill.

## Performance and resource limits

Future import and backfill work must expose explicit resource controls:

- maximum original file size;
- maximum image width and height;
- maximum decoded pixel count;
- maximum SVG byte size;
- thumbnail size set;
- batch size;
- cursor page size;
- dry-run output limit;
- resume token or source cursor position.

Backfill must stream source metadata and process bounded batches. It must not
load all GridFS files, decoded images, or generated thumbnails into memory at
once.

## Production rollout ownership

Recommended future ownership split:

1. Persistence PR: Mongo media repository, indexes, and repository tests.
2. Representation PR: GridFS representation store and orphan audit report mode.
3. API PR: fragment-scoped read routes and authenticated Blob-compatible binary
   responses.
4. Importer PR: administrative importer with dry-run first.
5. Backfill PR: non-destructive legacy metadata backfill with reports.
6. Verification PR: legacy/new summary comparison and `hasPhoto` mismatch
   reporting.
7. Frontend PR: media gallery reads behind a rollout control.

Each PR that writes to MongoDB, GridFS, or fragment documents must state side
effects, cleanup behavior, and rollback behavior explicitly.
