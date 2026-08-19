from typing import cast

import attr

from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQuerySummarySchema,
)
from ebl.fragmentarium.domain.fragment import Script
from ebl.fragmentarium.domain.fragment_query_summary import FragmentQuerySummary
from ebl.media.application.media_urls import legacy_fragment_thumbnail_url
from ebl.media.domain import ThumbnailSize
from ebl.transliteration.domain.museum_number import MuseumNumber


def summary(museum_number: MuseumNumber, has_photo: bool) -> FragmentQuerySummary:
    return FragmentQuerySummary(
        museum_number=museum_number,
        description="",
        script=Script(),
        matching_lines=(),
        match_count=0,
        has_photo=has_photo,
    )


def dump(item: FragmentQuerySummary) -> dict[str, object]:
    return cast(dict[str, object], FragmentQuerySummarySchema().dump(item))


def test_production_summary_keeps_the_raw_legacy_thumbnail_path() -> None:
    result = dump(summary(MuseumNumber("A/B", "1"), True))

    assert result["thumbnailPath"] == "/fragments/A/B.1/thumbnail/small"


def test_production_summary_emits_thumbnail_path_without_a_photo() -> None:
    result = dump(summary(MuseumNumber.of("K.1"), False))

    assert result["hasPhoto"] is False
    assert result["thumbnailPath"] == "/fragments/K.1/thumbnail/small"


def test_shared_helper_reproduces_the_production_thumbnail_path() -> None:
    museum_number = MuseumNumber.of("K.1")

    assert dump(summary(museum_number, True))[
        "thumbnailPath"
    ] == legacy_fragment_thumbnail_url(museum_number, ThumbnailSize.SMALL)


def test_production_thumbnail_path_ignores_photo_state_entirely() -> None:
    with_photo = summary(MuseumNumber.of("K.1"), True)
    without_photo = attr.evolve(with_photo, has_photo=False)

    assert dump(with_photo)["thumbnailPath"] == dump(without_photo)["thumbnailPath"]
