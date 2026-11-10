# Fragment media uploads and management

This extends the authenticated retrieval foundation in backend #786. It does
not run migration #787, rewrite legacy photographs, or prepare indexes on startup.
The frontend upload PR uses the gallery foundation in frontend #839.

## HTTP contract

All paths use `?fragment=` with a URL-encoded museum identifier. Every request
checks fragment read access. Writes additionally require a stable authenticated
Auth0 subject and a dedicated restricted permission.

| Request | Body | Result |
| --- | --- | --- |
| `GET /media?fragment=...` | none | Published gallery `{media: [...]}` |
| `GET /media?fragment=...&view=management` | none | Published media and permitted submissions |
| `POST /media?fragment=...` | one raw raster image | `201` new submission; `200` same retry |
| `PATCH /media/{id}?fragment=...` | JSON metadata patch | `{media: [savedItem]}` |
| `POST /media/{id}/primary?fragment=...` | `{}` | `{media: [savedItem]}` |
| `POST /media/{id}/publish?fragment=...` | `{reason?: string}` | `{media: [savedItem]}` |
| `POST /media/{id}/reject?fragment=...` | `{reason?: string}` | `{media: [savedItem]}` |
| `DELETE /media/{id}?fragment=...` | empty | `204`, metadata tombstone only |

`publish` and `reject` require `If-Match`; `PATCH`, `primary`, and `DELETE`
accept it optionally. See [Concurrency](#concurrency).

Upload headers: `Content-Type: image/jpeg`, `image/png`, or `image/webp`;
`Idempotency-Key`: a canonical UUID; `X-Media-Metadata`:
`encodeURIComponent(JSON.stringify(metadata))`, at most 16 KiB. Standard bearer
authentication is mandatory. Falcon CORS preflight permits requested custom
headers; reverse proxies must preserve them and the `Authorization` header.

Required upload metadata: `originalFilename`, `type` (`PHOTO` or `COPY`),
`caption`, `rightsStatement`, and `permissionAttested: true`. `sourceInstitution`
is supplied where applicable. Optional fields: `creator`, `copyrightHolder`,
`attribution`, `description`, `references: [{id: bibliographyId}]`, and
`projects: [ResearchProject enum name]`. Text fields have a 4000-character cap;
filenames have a 255-character cap. Original filenames/bytes cannot be replaced.
SVG ingestion and animated images are deliberately unsupported.

Metadata, bibliography identifiers, and review reasons must be valid UTF-8 text.
Malformed Unicode is rejected with 422 before creating upload reservations or
writing files; valid non-BMP characters remain supported.

Canonical responses retain existing gallery representations, sort order, caption,
attribution, and references. New records expose `publicationStatus`, `creator`,
`sourceInstitution`, `copyrightHolder`, and `rightsStatement`. Management
responses additionally expose `originalFilename`, `uploaderId`, `uploadedAt`,
`permissionAttested`, `description`, `projects`, `reviewerId`, `reviewedAt`,
`reviewReason`, and `revision`. Management fields are returned only for items the
caller uploaded, or for every listed item when the caller has
`manage:fragment_media`; other items in a `view=management` listing use the
canonical shape. Managers additionally receive `revision` on legacy items
(which have no submission), since they may edit, select, or remove them. Legacy
records lacking a submission field retain their existing published visibility.
Malformed explicit submission metadata fails closed.
Managers may annotate legacy creator, source, copyright, rights, and contextual
description without changing original provenance or publication. Only annotated
legacy responses include `rightsAnnotated: true` and the corresponding text
fields; no uploader, review identity, or upload attestation is fabricated.
When a removed canonical legacy photograph suppresses fallback, listings include
`legacyFallbackAllowed: false`. Other listings retain the existing envelope.

While `MEDIA_API_ENABLED=true`, fragment and fragment-search/query DTOs for a
fragment with a removed legacy photograph report `legacyHasPhoto: false`;
`hasPhoto` then reflects only published managed media of type `PHOTO`, and
`thumbnailPath` is the published primary media thumbnail URL or `null`.
Clients must decide whether to call `GET /fragments/{number}/photo` from
`legacyHasPhoto ?? hasPhoto`, not from `hasPhoto` alone: a fragment can have a
published managed photo while its legacy route returns 404.

Errors use standard Falcon JSON errors: 403 permission denial, 404 inaccessible
media/context or disabled routes, 409 duplicate payload mismatch/in-progress
upload/invalid primary selection, 412 stale `If-Match` revision, 413 oversized
content, 422 invalid metadata, image content, or malformed `If-Match`, 428
review without `If-Match`, and 503 decoder capacity exhausted
(`Retry-After: 10`). Keep the same idempotency key and metadata when retrying a failed transport; changing the
file or metadata requires a new key. An interrupted process reservation requires
explicit offline recovery before retry, rather than unsafe automatic lease expiry.

## Concurrency

Every media item carries an integer `revision` (>= 0). New uploads start at 0;
stored records written before the field existed read as 0, so no migration is
needed. Each successful `PATCH`, `publish`, `reject`, `primary`, or `DELETE`
increments the target item's revision by 1 in the same write. Selecting a primary
also clears the flag on other items of the fragment without advancing their
revisions. A replacement outside these mutations (such as an import in replace
mode) never moves a stored revision backwards, but it does not bump an equal
revision either; the repository-level `set_primary` used by
`DefaultMediaService.set_primary_media` likewise leaves revisions unchanged.
Neither path is reachable over HTTP, so do not run replace-mode imports while
managers are reviewing the affected fragments.

Clients send the revision they loaded as `If-Match: "<revision>"` (the quotes are
optional; anything other than one decimal revision, including `*` and weak
`W/` tags, is rejected with 422):

- `POST /media/{id}/publish` and `POST /media/{id}/reject` require it; without it
  they fail with `428 Precondition Required`. A manager can therefore never
  publish or reject text that an uploader changed after it was reviewed.
- `PATCH /media/{id}`, `POST /media/{id}/primary`, and `DELETE /media/{id}` verify
  it when present.

A revision that differs from the stored one fails with `412 Precondition Failed`
("Media changed since it was loaded; reload and review again.") and changes
nothing; clients should reload the management listing and review again. The
comparison runs inside the mutation's transaction and media write lock, after the
fragment, association, and edit-permission checks, so 404 and 403 take
precedence and a mismatch is only revealed to callers allowed to act. Successful
non-`DELETE` mutation responses also carry `ETag: "<revision>"` (exposed to CORS
clients); the body's `revision` field carries the same value.

## Permissions and publication

Configure these exact Auth0 API permissions manually; this change does not modify
production roles or Auth0 settings:

- `upload:fragment_media`: assign only to authorized contributors.
- `manage:fragment_media`: assign only to authorized reviewers/managers.
- Retain the existing `read:...-fragments` permissions for restricted fragments.

Readers receive published imagery only, including summaries and binary UUID
retrieval. Contributors can inspect their own unpublished submissions and, while
an item they uploaded is `PENDING_REVIEW`, edit every metadata field except the
rights fields `rightsStatement`, `copyrightHolder`, and `permissionAttested`
(`RIGHTS_FIELDS` in `ebl/media/application/media_metadata.py`). Editable fields
are `type`, `caption` (nonblank), `description`, `creator`, `sourceInstitution`,
`attribution`, `references`, and `projects`; `originalFilename` is never
editable. Because contributors can change `creator`, `sourceInstitution`, and
`attribution` after attesting rights, managers must re-check attribution
against the rights statement before publishing. Contributors cannot publish,
reject, remove, or select primary media, nor edit others' or reviewed items.
Managers may upload without the contributor scope, review all media they can
access, correct new-upload rights, publish, reject, select a published primary
image, and remove media. Mutations involving multiple associated fragments also
require access to every association. Legacy
import provenance and original files remain unchanged when managers annotate
rights; legacy upload attestation is rejected and rights are never inferred from EXIF.

New uploads always start `PENDING_REVIEW`, including manager uploads. Publishing
is explicit and requires nonblank rights and permission attestation. Review
identity/time and optional reason are persisted. Rejection clears primary flags.
Primary selection and metadata/publication updates use the existing transaction
and media write lock. Changelog entries record the authenticated subject and
upload, edit, publication, rejection, primary, and removal events.

## Storage, database, and limits

MongoDB must support transactions (replica set or sharded cluster). Before the
first write, an operator must explicitly run the foundation's
`MongoMediaRepository.create_indexes()` and
`GridFsMediaRepresentationStore.create_indexes()` for the intended database.
There is no automatic index initialization on application startup.

New metadata adds the optional `submission` document to `media` and an optional
`rights` annotation document for manager corrections to legacy imagery. Existing records
need no migration. `mediaUploadRequests` uses MongoDB's implicit unique `_id`
index for actor/fragment/idempotency identity; it retains the content-and-metadata
fingerprint, lease, canonical media ID, staged handles, and state. No TTL index
expires uncertain writes. Existing media ownership/source reservation indexes
remain authoritative. Audit events use the existing `changelog` collection.
`mediaLegacyVisibility` uses its implicit unique fragment `_id` to retain a
suppression marker across media cleanup. No additional index preparation is needed.

New originals and generated files use only owned `media` GridFS storage, never
the legacy `photos` bucket. Original bytes/checksums are unchanged. Decoding
verifies actual JPEG/PNG/WebP content, full frames, dimensions, frame count, byte
size, and checksum. EXIF orientation is normalized only for derived JPEG previews.
Display maximum dimension is 2560; thumbnail maxima are 240/480/720, preserving
aspect ratio. Original EXIF attribution evidence is retained; it grants no rights.

Defaults: `MEDIA_UPLOAD_MAX_BYTES=26214400`,
`MEDIA_UPLOAD_MAX_PIXELS=40000000`, `MEDIA_UPLOAD_MAX_DIMENSION=20000`,
`MEDIA_UPLOAD_DECODE_SLOTS=1`. Decode slots may be 1 or 2 per process. Size/pixel
limits and process/container memory must be sized together. Multiple processes
each have their own decode pool. Staging spills to temporary disk after 1 MiB.
Provision bounded temporary disk, request timeouts, and a proxy body limit aligned
with the upload limit; the existing 64 MiB Waitress cap remains an outer limit.

## Recovery and safe removal

HTTP removal hides metadata immediately and retains all bytes and the deletion
token, so active readers can finish. Borrowed legacy originals are never physically
deleted. New staged handles are journaled; an uncertain metadata commit quarantines
them rather than risking deletion of successfully committed bytes.
Removing a recognized borrowed `gridfs`/`photos` original also records persistent
legacy suppression for associations whose actual GridFS filename is the canonical
`{fragment}.jpg`. The domain filename is not trusted for this decision. This blocks
both legacy photograph and thumbnail routes while media-aware reads are enabled,
and removes stale legacy flags and paths from fragment/search summaries. Removing
an unrelated imported file or an owned upload does not suppress another legacy
photograph. Cleanup preserves these visibility markers and all borrowed bytes.

Offline annotation tooling reads `mediaLegacyVisibility` directly, independent of
`MEDIA_API_ENABLED`: `python -m ebl.fragmentarium.retrieve_annotations` omits
fragments with a removed legacy photograph from the exported images, ground-truth
files, and fragment list, and `python -m ebl.fragmentarium.migrate_cropped_images`
regenerates no `cropped_sign_images` for them. Without visibility markers both
tools behave as before.

To inspect recovery work, run with the intended operator-provided `MONGODB_URI`:

```sh
python -m ebl.media.infrastructure.media_recovery --database TEST_DATABASE
```

Before applying cleanup, stop/drain **all** media writers and binary readers,
take a backup, and inspect the dry run. Then add `--apply --quiescent`. This
explicit offline guarantee is essential: cleanup does not infer that readers
have finished from a timer. Cleanup uses exact generation/owner handles and
tombstone tokens, preserves any existing current metadata, and never deletes
borrowed originals. Incomplete reservations become retryable only after their
unreferenced owned handles are cleaned. Failed cleanup can be retried safely.

## Rollout and rollback

1. Merge/deploy retrieval #786 after its persistence foundation; #787 remains an
   independent optional legacy migration and is not included in this branch.
2. Merge/deploy this backend and the frontend upload PR on its #839 foundation.
   Keep `MEDIA_UPLOAD_ENABLED=false` and frontend
   `REACT_APP_MEDIA_UPLOAD_ENABLED=false` initially.
3. Prepare foundational indexes explicitly, allocate storage/resources, configure
   Auth0 role assignments, and verify nonproduction upload/publication/denial.
4. Enable backend `MEDIA_API_ENABLED=true`, then `MEDIA_UPLOAD_ENABLED=true`,
   then frontend gallery and upload flags for the intended environment.

Rollback: disable the frontend upload flag, then backend `MEDIA_UPLOAD_ENABLED`.
Read-only gallery remains independent. Keep `MEDIA_API_ENABLED` enabled for
published retrieval and persistent legacy removal enforcement. Disabling the media
read foundation also disables its legacy visibility guard and can restore historical
fallback access, so it is not a visibility-safe rollback after canonical removals.
Retain submission and idempotency metadata, visibility markers, and owned files;
do not restore an older reader that would ignore publication metadata while new
unpublished records remain in its database. No production flags or data are
changed by this PR.

## Local verification

Run `pytest ebl/tests/media` against a disposable transactional MongoDB, then
`ruff check ebl`, `ruff format --check ebl`, and the repository type/full test
checks. `ebl.tests.media.e2e_server` provides a separate browser-test harness
that binds `0.0.0.0:8000` (all interfaces, for container networking; expose it
only on an isolated test network) with fixed test bearer roles, a dedicated
disposable Mongo host check, real media routes/storage, and a random isolated
database. It must never be deployed as the application server.
