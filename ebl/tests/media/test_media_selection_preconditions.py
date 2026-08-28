from typing import Callable, Sequence

import pytest

from ebl.media.application.media_selection import (
    fragment_media_in_order,
    has_photo,
    primary_media_for,
    primary_photo_for,
)
from ebl.media.application.media_summary_dtos import (
    FragmentMediaSummaryDto,
    MediaSummaryDto,
)
from ebl.media.domain import Media
from ebl.tests.media.factories import DEFAULT_MEDIA_ID, association, photo_media
from ebl.transliteration.domain.museum_number import MuseumNumber

FRAGMENT_ID = MuseumNumber.of("K.1")
OTHER_FRAGMENT_ID = MuseumNumber.of("K.2")
NOT_ASSOCIATED = f"Media {DEFAULT_MEDIA_ID} is not associated with fragment K.2."


def other_fragments_photo() -> tuple[Media, ...]:
    return (photo_media(associations=(association(sort_order=0, is_primary=True),)),)


Selection = Callable[[MuseumNumber, Sequence[Media]], object]


@pytest.mark.parametrize(
    "select",
    [fragment_media_in_order, has_photo, primary_media_for, primary_photo_for],
)
def test_selection_rejects_media_of_another_fragment(select: Selection) -> None:
    with pytest.raises(ValueError, match=NOT_ASSOCIATED):
        select(OTHER_FRAGMENT_ID, other_fragments_photo())


def test_media_summary_rejects_media_of_another_fragment() -> None:
    with pytest.raises(ValueError, match=NOT_ASSOCIATED):
        MediaSummaryDto.of(OTHER_FRAGMENT_ID, other_fragments_photo())


def test_fragment_media_summary_rejects_media_of_another_fragment() -> None:
    with pytest.raises(ValueError, match=NOT_ASSOCIATED):
        FragmentMediaSummaryDto.of(OTHER_FRAGMENT_ID, other_fragments_photo())


def test_selection_accepts_media_shared_by_both_fragments() -> None:
    shared_photo = photo_media(
        associations=(
            association(sort_order=1, is_primary=True),
            association(fragment_id=OTHER_FRAGMENT_ID, sort_order=0, is_primary=True),
        )
    )

    summary = FragmentMediaSummaryDto.of(OTHER_FRAGMENT_ID, (shared_photo,))

    assert summary.has_photo is True
    assert summary.media_summary.count == 1
