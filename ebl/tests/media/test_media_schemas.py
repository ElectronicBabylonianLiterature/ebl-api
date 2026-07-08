from ebl.media.application.media_schemas import (
    FragmentMediaResponseDto,
    FragmentMediaResponseDtoSchema,
    FragmentMediaSummaryDto,
    FragmentMediaSummaryDtoSchema,
)
from ebl.media.domain import (
    Media,
    MediaAssociation,
    MediaChecksum,
    MediaReference,
    MediaRepresentation,
    MediaRepresentations,
    MediaType,
    ThumbnailSize,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


PHOTO_ID = "550e8400-e29b-41d4-a716-446655440000"
COPY_ID = "550e8400-e29b-41d4-a716-446655440001"


def original(mime_type="image/jpeg") -> MediaRepresentation:
    return MediaRepresentation(
        mime_type, 4000, 3000, 5242880, MediaChecksum(value="a" * 64)
    )


def thumbnail(mime_type="image/jpeg") -> MediaRepresentation:
    return MediaRepresentation(mime_type, 240, 180, 15360)


def media(
    media_id=PHOTO_ID,
    media_type=MediaType.PHOTO,
    associations=(MediaAssociation("K.1", 0, True),),
    references=(MediaReference("bibliography-id"),),
    caption="Obverse",
    attribution="The British Museum",
) -> Media:
    return Media(
        id=media_id,
        type=media_type,
        original_filename="BM-12345-obverse.jpg",
        representations=MediaRepresentations(
            original(),
            ((ThumbnailSize.SMALL, thumbnail()),),
        ),
        associations=associations,
        references=references,
        caption=caption,
        attribution=attribution,
    )


def test_fragment_media_response_serializes_fragment_context() -> None:
    fragment_id = MuseumNumber.of("K.1")

    result = FragmentMediaResponseDtoSchema().dump(
        FragmentMediaResponseDto.of(fragment_id, (media(),))
    )

    assert result == {
        "media": [
            {
                "id": PHOTO_ID,
                "type": "PHOTO",
                "sortOrder": 0,
                "isPrimary": True,
                "caption": "Obverse",
                "attribution": "The British Museum",
                "references": [{"id": "bibliography-id"}],
                "representations": {
                    "original": {
                        "url": f"/fragments/K.1/media/{PHOTO_ID}/file",
                        "mimeType": "image/jpeg",
                        "width": 4000,
                        "height": 3000,
                    },
                    "thumbnails": {
                        "small": {
                            "url": f"/fragments/K.1/media/{PHOTO_ID}/thumbnail/small",
                            "mimeType": "image/jpeg",
                            "width": 240,
                            "height": 180,
                        }
                    },
                },
            }
        ]
    }


def test_fragment_media_response_omits_optional_empty_fields() -> None:
    fragment_id = MuseumNumber.of("K.1")
    item = media(references=(), caption=None, attribution=None)

    [result] = FragmentMediaResponseDtoSchema().dump(
        FragmentMediaResponseDto.of(fragment_id, (item,))
    )["media"]

    assert "caption" not in result
    assert "attribution" not in result
    assert "references" not in result


def test_fragment_media_response_excludes_internal_fields() -> None:
    fragment_id = MuseumNumber.of("K.1")

    [result] = FragmentMediaResponseDtoSchema().dump(
        FragmentMediaResponseDto.of(fragment_id, (media(),))
    )["media"]

    assert "originalFilename" not in result
    assert "checksum" not in result["representations"]["original"]
    assert "fileSize" not in result["representations"]["original"]
    assert "importSource" not in result
    assert "projects" not in result


def test_media_summary_serializes_primary_photo_and_legacy_fields() -> None:
    fragment_id = MuseumNumber.of("K.1")
    copy = media(
        media_id=COPY_ID,
        media_type=MediaType.COPY,
        associations=(MediaAssociation("K.1", 0, True),),
    )
    photo = media(
        media_id=PHOTO_ID,
        media_type=MediaType.PHOTO,
        associations=(MediaAssociation("K.1", 1, True),),
    )

    result = FragmentMediaSummaryDtoSchema().dump(
        FragmentMediaSummaryDto.of(fragment_id, (copy, photo))
    )

    assert result == {
        "mediaSummary": {
            "count": 2,
            "types": ["COPY", "PHOTO"],
            "primary": {
                "id": PHOTO_ID,
                "type": "PHOTO",
                "thumbnail": {
                    "url": f"/fragments/K.1/media/{PHOTO_ID}/thumbnail/small",
                    "mimeType": "image/jpeg",
                    "width": 240,
                    "height": 180,
                },
            },
        },
        "hasPhoto": True,
        "thumbnailPath": "/fragments/K.1/thumbnail/small",
    }


def test_media_summary_for_copy_only_fragment_has_no_legacy_photo_flag() -> None:
    fragment_id = MuseumNumber.of("K.1")
    copy = media(
        media_id=COPY_ID,
        media_type=MediaType.COPY,
        associations=(MediaAssociation("K.1", 0, True),),
    )

    result = FragmentMediaSummaryDtoSchema().dump(
        FragmentMediaSummaryDto.of(fragment_id, (copy,))
    )

    assert result["hasPhoto"] is False
    assert "thumbnailPath" not in result
    assert result["mediaSummary"]["primary"]["type"] == "COPY"


def test_media_summary_without_primary_omits_primary() -> None:
    fragment_id = MuseumNumber.of("K.1")
    photo = media(associations=(MediaAssociation("K.1", 0, False),))

    result = FragmentMediaSummaryDtoSchema().dump(
        FragmentMediaSummaryDto.of(fragment_id, (photo,))
    )

    assert result["mediaSummary"] == {
        "count": 1,
        "types": ["PHOTO"],
    }
