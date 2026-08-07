from typing import Any, Dict, cast

from ebl.media.application.media_schemas import (
    FragmentMediaSummaryDto,
    FragmentMediaSummaryDtoSchema,
)
from ebl.media.domain import ThumbnailSize
from ebl.tests.media.factories import (
    DEFAULT_COPY_MEDIA_ID,
    DEFAULT_MEDIA_ID,
    SECOND_PHOTO_MEDIA_ID,
    association,
    copy_media,
    medium_thumbnail_representation,
    photo_media,
    representations,
)
from ebl.transliteration.domain.museum_number import MuseumNumber

FRAGMENT_ID = MuseumNumber.of("K.1")
LEGACY_THUMBNAIL_PATH = "/fragments/K.1/thumbnail/small"


def dump(media) -> Dict[str, Any]:
    return cast(
        Dict[str, Any],
        FragmentMediaSummaryDtoSchema().dump(
            FragmentMediaSummaryDto.of(FRAGMENT_ID, media)
        ),
    )


def test_media_summary_serializes_primary_photo_and_legacy_fields() -> None:
    copy = copy_media(associations=(association(sort_order=0, is_primary=True),))
    photo = photo_media(associations=(association(sort_order=1, is_primary=True),))

    assert dump((copy, photo)) == {
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
        "thumbnailPath": LEGACY_THUMBNAIL_PATH,
    }


def test_media_summary_for_copy_only_fragment_has_no_legacy_photo_flag() -> None:
    copy = copy_media(associations=(association(sort_order=0, is_primary=True),))

    result = dump((copy,))

    assert result["hasPhoto"] is False
    assert result["thumbnailPath"] == LEGACY_THUMBNAIL_PATH
    assert result["mediaSummary"]["primary"] == {
        "id": DEFAULT_COPY_MEDIA_ID,
        "type": "COPY",
        "thumbnail": {
            "url": f"/fragments/K.1/media/{DEFAULT_COPY_MEDIA_ID}/thumbnail/small",
            "mimeType": "image/jpeg",
            "width": 240,
            "height": 180,
        },
    }


def test_media_summary_without_primary_keeps_legacy_thumbnail_path() -> None:
    photo = photo_media(associations=(association(sort_order=0, is_primary=False),))

    result = dump((photo,))

    assert result["mediaSummary"] == {"count": 1, "types": ["PHOTO"]}
    assert result["hasPhoto"] is True
    assert result["thumbnailPath"] == LEGACY_THUMBNAIL_PATH


def test_media_summary_without_media_still_emits_legacy_fields() -> None:
    assert dump(()) == {
        "mediaSummary": {"count": 0, "types": []},
        "hasPhoto": False,
        "thumbnailPath": LEGACY_THUMBNAIL_PATH,
    }


def test_media_summary_without_small_photo_thumbnail_omits_primary_thumbnail() -> None:
    photo = photo_media(
        media_representations=representations(
            thumbnails=((ThumbnailSize.MEDIUM, medium_thumbnail_representation()),)
        )
    )

    result = dump((photo,))

    assert result["hasPhoto"] is True
    assert result["mediaSummary"]["primary"] == {
        "id": DEFAULT_MEDIA_ID,
        "type": "PHOTO",
    }
    assert result["thumbnailPath"] == LEGACY_THUMBNAIL_PATH


def test_media_summary_never_promotes_medium_thumbnail_to_small() -> None:
    photo = photo_media(
        media_representations=representations(
            thumbnails=((ThumbnailSize.MEDIUM, medium_thumbnail_representation()),)
        )
    )

    primary = dump((photo,))["mediaSummary"]["primary"]

    assert "thumbnail" not in primary


def test_media_summary_legacy_thumbnail_path_ignores_primary_selection() -> None:
    copy = copy_media(associations=(association(sort_order=0, is_primary=True),))
    photo = photo_media(associations=(association(sort_order=1, is_primary=False),))

    result = dump((copy, photo))

    assert result["hasPhoto"] is True
    assert result["mediaSummary"]["primary"]["type"] == "COPY"
    assert result["thumbnailPath"] == LEGACY_THUMBNAIL_PATH


def test_media_summary_selects_first_primary_photo_by_sort_order() -> None:
    later_photo = photo_media(
        media_id_=SECOND_PHOTO_MEDIA_ID,
        associations=(association(sort_order=5, is_primary=True),),
    )
    earlier_photo = photo_media(
        associations=(association(sort_order=1, is_primary=True),)
    )

    result = dump((later_photo, earlier_photo))

    assert result["mediaSummary"]["count"] == 2
    assert result["mediaSummary"]["primary"]["id"] == DEFAULT_MEDIA_ID
    assert result["thumbnailPath"] == LEGACY_THUMBNAIL_PATH
