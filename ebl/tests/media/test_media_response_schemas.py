from typing import Sequence, cast

from ebl.media.application.media_dtos import FragmentMediaResponseDto
from ebl.media.application.media_schemas import FragmentMediaResponseDtoSchema
from ebl.media.domain import Media, MediaRepresentations, MediaType, ThumbnailSize
from ebl.tests.media.factories import (
    DEFAULT_COPY_MEDIA_ID,
    DEFAULT_MEDIA_ID,
    association,
    copy_media,
    display_representation,
    large_thumbnail_representation,
    media_reference,
    medium_thumbnail_representation,
    original_representation,
    photo_media,
    representations,
    thumbnail_representation,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def dump_response(
    fragment_id: MuseumNumber, media: Sequence[Media]
) -> dict[str, object]:
    return cast(
        dict[str, object],
        FragmentMediaResponseDtoSchema().dump(
            FragmentMediaResponseDto.of(fragment_id, media)
        ),
    )


def dump_media(
    fragment_id: MuseumNumber, media: Sequence[Media]
) -> list[dict[str, object]]:
    return cast(list[dict[str, object]], dump_response(fragment_id, media)["media"])


def mapped(value: object) -> dict[str, object]:
    return cast(dict[str, object], value)


def test_fragment_media_response_serializes_fragment_context() -> None:
    fragment_id = MuseumNumber.of("K.1")
    item = photo_media(
        references=(media_reference(),),
        caption="Obverse",
        attribution="The British Museum",
    )

    result = dump_response(fragment_id, (item,))

    assert result == {
        "media": [
            {
                "id": DEFAULT_MEDIA_ID,
                "type": "PHOTO",
                "sortOrder": 0,
                "isPrimary": True,
                "caption": "Obverse",
                "attribution": "The British Museum",
                "references": [{"id": "bibliography-id"}],
                "representations": {
                    "original": {
                        "url": f"/fragments/K.1/media/{DEFAULT_MEDIA_ID}/file",
                        "mimeType": "image/jpeg",
                        "width": 4000,
                        "height": 3000,
                    },
                    "thumbnails": {
                        "small": {
                            "url": (
                                f"/fragments/K.1/media/{DEFAULT_MEDIA_ID}"
                                "/thumbnail/small"
                            ),
                            "mimeType": "image/jpeg",
                            "width": 240,
                            "height": 180,
                        }
                    },
                },
            }
        ]
    }


def test_fragment_media_response_serializes_display_representation() -> None:
    fragment_id = MuseumNumber.of("K.1")
    item = photo_media(
        media_representations=representations(
            display=display_representation("image/webp")
        )
    )

    [result] = dump_media(fragment_id, (item,))

    assert mapped(result["representations"])["display"] == {
        "url": f"/fragments/K.1/media/{DEFAULT_MEDIA_ID}/display",
        "mimeType": "image/webp",
        "width": 2560,
        "height": 1920,
    }


def test_fragment_media_response_encodes_future_media_urls() -> None:
    fragment_id = MuseumNumber("A/B", "1")
    item = photo_media(associations=(association(fragment_id=fragment_id),))

    [result] = dump_media(fragment_id, (item,))

    representations = mapped(result["representations"])
    assert mapped(representations["original"])["url"] == (
        f"/fragments/A%2FB.1/media/{DEFAULT_MEDIA_ID}/file"
    )
    thumbnails = mapped(representations["thumbnails"])
    assert mapped(thumbnails["small"])["url"] == (
        f"/fragments/A%2FB.1/media/{DEFAULT_MEDIA_ID}/thumbnail/small"
    )


def test_fragment_media_response_omits_optional_empty_fields() -> None:
    fragment_id = MuseumNumber.of("K.1")

    [result] = dump_media(fragment_id, (photo_media(),))

    assert "caption" not in result
    assert "attribution" not in result
    assert "references" not in result
    assert "display" not in mapped(result["representations"])


def test_fragment_media_response_excludes_internal_fields() -> None:
    fragment_id = MuseumNumber.of("K.1")

    [result] = dump_media(fragment_id, (photo_media(),))

    assert "originalFilename" not in result
    original = mapped(mapped(result["representations"])["original"])
    assert "checksum" not in original
    assert "fileSize" not in original
    assert "importSource" not in result
    assert "projects" not in result


def test_fragment_media_response_serializes_multiple_thumbnail_sizes() -> None:
    fragment_id = MuseumNumber.of("K.1")
    item = photo_media(
        media_representations=representations(
            thumbnails=(
                (ThumbnailSize.SMALL, thumbnail_representation()),
                (ThumbnailSize.MEDIUM, medium_thumbnail_representation()),
                (ThumbnailSize.LARGE, large_thumbnail_representation()),
            )
        )
    )

    [result] = dump_media(fragment_id, (item,))

    thumbnails = mapped(mapped(result["representations"])["thumbnails"])

    assert set(thumbnails) == {"small", "medium", "large"}
    assert thumbnails["small"] == {
        "url": f"/fragments/K.1/media/{DEFAULT_MEDIA_ID}/thumbnail/small",
        "mimeType": "image/jpeg",
        "width": 240,
        "height": 180,
    }
    assert thumbnails["medium"] == {
        "url": f"/fragments/K.1/media/{DEFAULT_MEDIA_ID}/thumbnail/medium",
        "mimeType": "image/jpeg",
        "width": 480,
        "height": 360,
    }
    assert thumbnails["large"] == {
        "url": f"/fragments/K.1/media/{DEFAULT_MEDIA_ID}/thumbnail/large",
        "mimeType": "image/jpeg",
        "width": 960,
        "height": 720,
    }


def test_fragment_media_response_supports_svg_original_with_raster_display() -> None:
    fragment_id = MuseumNumber.of("K.1")
    item = copy_media(
        media_representations=MediaRepresentations(
            original_representation("image/svg+xml"),
            ((ThumbnailSize.SMALL, thumbnail_representation()),),
            display=display_representation(),
        ),
    )

    [result] = dump_media(fragment_id, (item,))

    assert result["id"] == DEFAULT_COPY_MEDIA_ID
    assert result["type"] == MediaType.COPY.name
    representations = mapped(result["representations"])
    assert mapped(representations["original"])["mimeType"] == "image/svg+xml"
    assert mapped(representations["display"])["mimeType"] == "image/jpeg"
