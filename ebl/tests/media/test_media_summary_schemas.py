from ebl.media.application.media_schemas import (
    FragmentMediaSummaryDto,
    FragmentMediaSummaryDtoSchema,
)
from ebl.media.domain import ThumbnailSize
from ebl.tests.media.factories import (
    DEFAULT_MEDIA_ID,
    SECOND_PHOTO_MEDIA_ID,
    association,
    copy_media,
    medium_thumbnail_representation,
    photo_media,
    representations,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_media_summary_serializes_primary_photo_and_legacy_fields() -> None:
    fragment_id = MuseumNumber.of("K.1")
    copy = copy_media(associations=(association(sort_order=0, is_primary=True),))
    photo = photo_media(associations=(association(sort_order=1, is_primary=True),))

    result = FragmentMediaSummaryDtoSchema().dump(
        FragmentMediaSummaryDto.of(fragment_id, (copy, photo))
    )

    assert result == {
        "mediaSummary": {
            "count": 2,
            "types": ["COPY", "PHOTO"],
            "primary": {
                "id": DEFAULT_MEDIA_ID,
                "type": "PHOTO",
                "thumbnail": {
                    "url": f"/fragments/K.1/media/{DEFAULT_MEDIA_ID}/thumbnail/small",
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
    copy = copy_media(associations=(association(sort_order=0, is_primary=True),))

    result = FragmentMediaSummaryDtoSchema().dump(
        FragmentMediaSummaryDto.of(fragment_id, (copy,))
    )

    assert result["hasPhoto"] is False
    assert "thumbnailPath" not in result
    assert result["mediaSummary"]["primary"]["type"] == "COPY"


def test_media_summary_without_primary_keeps_legacy_thumbnail_path() -> None:
    fragment_id = MuseumNumber.of("K.1")
    photo = photo_media(associations=(association(sort_order=0, is_primary=False),))

    result = FragmentMediaSummaryDtoSchema().dump(
        FragmentMediaSummaryDto.of(fragment_id, (photo,))
    )

    assert result["mediaSummary"] == {
        "count": 1,
        "types": ["PHOTO"],
    }
    assert result["hasPhoto"] is True
    assert result["thumbnailPath"] == "/fragments/K.1/thumbnail/small"


def test_media_summary_without_media_keeps_empty_types() -> None:
    fragment_id = MuseumNumber.of("K.1")

    result = FragmentMediaSummaryDtoSchema().dump(
        FragmentMediaSummaryDto.of(fragment_id, ())
    )

    assert result == {
        "mediaSummary": {
            "count": 0,
            "types": [],
        },
        "hasPhoto": False,
    }


def test_media_summary_without_small_photo_thumbnail_omits_thumbnail_path() -> None:
    fragment_id = MuseumNumber.of("K.1")
    photo = photo_media(
        media_representations=representations(
            thumbnails=((ThumbnailSize.MEDIUM, medium_thumbnail_representation()),)
        )
    )

    result = FragmentMediaSummaryDtoSchema().dump(
        FragmentMediaSummaryDto.of(fragment_id, (photo,))
    )

    assert result["hasPhoto"] is True
    assert result["mediaSummary"]["primary"]["type"] == "PHOTO"
    assert "thumbnail" not in result["mediaSummary"]["primary"]
    assert "thumbnailPath" not in result


def test_media_summary_uses_non_primary_photo_for_legacy_thumbnail_path() -> None:
    fragment_id = MuseumNumber.of("K.1")
    copy = copy_media(associations=(association(sort_order=0, is_primary=True),))
    photo = photo_media(associations=(association(sort_order=1, is_primary=False),))

    result = FragmentMediaSummaryDtoSchema().dump(
        FragmentMediaSummaryDto.of(fragment_id, (copy, photo))
    )

    assert result["hasPhoto"] is True
    assert result["mediaSummary"]["primary"]["type"] == "COPY"
    assert result["thumbnailPath"] == "/fragments/K.1/thumbnail/small"


def test_media_summary_uses_first_photo_with_small_thumbnail() -> None:
    fragment_id = MuseumNumber.of("K.1")
    photo_without_small = photo_media(
        associations=(association(sort_order=0, is_primary=False),),
        media_representations=representations(
            thumbnails=((ThumbnailSize.MEDIUM, medium_thumbnail_representation()),)
        ),
    )
    photo_with_small = photo_media(
        media_id_=SECOND_PHOTO_MEDIA_ID,
        associations=(association(sort_order=1, is_primary=False),),
    )

    result = FragmentMediaSummaryDtoSchema().dump(
        FragmentMediaSummaryDto.of(fragment_id, (photo_with_small, photo_without_small))
    )

    assert result["mediaSummary"] == {
        "count": 2,
        "types": ["PHOTO"],
    }
    assert result["hasPhoto"] is True
    assert result["thumbnailPath"] == "/fragments/K.1/thumbnail/small"
