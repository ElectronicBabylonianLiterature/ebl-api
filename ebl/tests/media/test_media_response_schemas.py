from ebl.media.application.media_schemas import (
    FragmentMediaResponseDto,
    FragmentMediaResponseDtoSchema,
)
from ebl.media.domain import MediaRepresentations, MediaType, ThumbnailSize
from ebl.tests.media.factories import (
    DEFAULT_COPY_MEDIA_ID,
    DEFAULT_MEDIA_ID,
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


def test_fragment_media_response_serializes_fragment_context() -> None:
    fragment_id = MuseumNumber.of("K.1")
    item = photo_media(
        references=(media_reference(),),
        caption="Obverse",
        attribution="The British Museum",
    )

    result = FragmentMediaResponseDtoSchema().dump(
        FragmentMediaResponseDto.of(fragment_id, (item,))
    )

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

    [result] = FragmentMediaResponseDtoSchema().dump(
        FragmentMediaResponseDto.of(fragment_id, (item,))
    )["media"]

    assert result["representations"]["display"] == {
        "url": f"/fragments/K.1/media/{DEFAULT_MEDIA_ID}/display",
        "mimeType": "image/webp",
        "width": 2560,
        "height": 1920,
    }


def test_fragment_media_response_omits_optional_empty_fields() -> None:
    fragment_id = MuseumNumber.of("K.1")

    [result] = FragmentMediaResponseDtoSchema().dump(
        FragmentMediaResponseDto.of(fragment_id, (photo_media(),))
    )["media"]

    assert "caption" not in result
    assert "attribution" not in result
    assert "references" not in result
    assert "display" not in result["representations"]


def test_fragment_media_response_excludes_internal_fields() -> None:
    fragment_id = MuseumNumber.of("K.1")

    [result] = FragmentMediaResponseDtoSchema().dump(
        FragmentMediaResponseDto.of(fragment_id, (photo_media(),))
    )["media"]

    assert "originalFilename" not in result
    assert "checksum" not in result["representations"]["original"]
    assert "fileSize" not in result["representations"]["original"]
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

    [result] = FragmentMediaResponseDtoSchema().dump(
        FragmentMediaResponseDto.of(fragment_id, (item,))
    )["media"]

    thumbnails = result["representations"]["thumbnails"]

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

    [result] = FragmentMediaResponseDtoSchema().dump(
        FragmentMediaResponseDto.of(fragment_id, (item,))
    )["media"]

    assert result["id"] == DEFAULT_COPY_MEDIA_ID
    assert result["type"] == MediaType.COPY.name
    assert result["representations"]["original"]["mimeType"] == "image/svg+xml"
    assert result["representations"]["display"]["mimeType"] == "image/jpeg"
