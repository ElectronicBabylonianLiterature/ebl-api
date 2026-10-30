import uuid
from typing import BinaryIO, Mapping

import attr
from bson import ObjectId

from ebl.media.application.backfill_plan import (
    BackfillPolicy,
    PlannedPhoto,
    SourceRejected,
)
from ebl.media.application.media_repository import MediaReader
from ebl.media.domain import (
    Media,
    MediaAssociation,
    MediaId,
    MediaRepresentations,
    MediaType,
)
from ebl.media.infrastructure.backfill_images import inspect_image, preview_bytes
from ebl.media.infrastructure.backfill_sources import (
    LegacyPhotoSources,
    encode_source_id,
    decode_source_id,
    metadata_snapshot,
)
from ebl.media.infrastructure.legacy_media_handles import legacy_import_source
from ebl.transliteration.domain.museum_number import MuseumNumber


def candidate_media(candidate: PlannedPhoto) -> Media:
    representation = candidate.representation
    fragment_id = candidate.fragment_id
    if representation is None or fragment_id is None:
        raise ValueError("Only an inspected, mapped original can become media.")
    file_id = decode_source_id(candidate.source_id)
    if not isinstance(file_id, (ObjectId, str)):
        raise ValueError("Migration source identity must be an ObjectId or string.")
    source = legacy_import_source("photos", file_id)
    media_id = MediaId(
        str(uuid.uuid5(uuid.NAMESPACE_URL, f"ebl:gridfs:photos:{source.file_id}"))
    )
    return Media(
        media_id,
        MediaType.PHOTO,
        candidate.filename,
        MediaRepresentations(representation),
        (MediaAssociation(MuseumNumber.of(fragment_id), 0, False),),
        attribution=candidate.attribution,
        import_source=source,
    )


def initial_candidate(document: Mapping) -> PlannedPhoto:
    return PlannedPhoto(
        source_id=encode_source_id(document["_id"]),
        snapshot=metadata_snapshot(document),
        filename=str(document.get("filename", "")),
        fragment_id=None,
        outcome="blocked",
    )


def inspect_candidate(
    document: Mapping,
    content: BinaryIO,
    sources: LegacyPhotoSources,
    policy: BackfillPolicy,
) -> PlannedPhoto:
    fragment = sources.mapping(document)
    representation, evidence = inspect_image(content, document["length"], policy)
    preview_deferred = (
        policy.generate_previews
        and representation.width * representation.height > policy.max_pixels
    )
    if policy.generate_previews and not preview_deferred:
        preview_bytes(content, 2560)
    attribution = (
        "\n".join(f"{name}: {value}" for name, value in evidence.items()) or None
        if policy.map_attribution
        else None
    )
    if not sources.unchanged(document):
        raise SourceRejected("conflicting", "source-metadata-changed")
    sources.mapping(document)
    return attr.evolve(
        initial_candidate(document),
        fragment_id=str(fragment),
        outcome="candidate",
        reason="preview-deferred-pixel-limit" if preview_deferred else None,
        representation=representation,
        attribution=attribution,
        attribution_evidence=evidence,
        binary_validation=(
            "jpeg-structure-only"
            if representation.width * representation.height > policy.max_pixels
            else "decoded"
        ),
    )


def existing_outcome(candidate: PlannedPhoto, repository: MediaReader) -> str | None:
    media = candidate_media(candidate)
    assert media.import_source is not None
    existing = repository.find_by_import_source(media.import_source)
    if existing is not None:
        return (
            "already-present"
            if existing.representations.original == media.representations.original
            and existing.original_filename == media.original_filename
            and existing.is_associated_with(candidate.fragment_id or "")
            else "conflicting"
        )
    return "conflicting" if repository.find_by_id(media.id) is not None else None
