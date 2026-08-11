from typing import cast

import pytest
from marshmallow import Schema, fields

from ebl.media.application.media_dtos import FragmentMediaItemDto
from ebl.media.application.media_schemas import (
    FragmentMediaItemDtoSchema,
    OmitEmptyMixin,
)
from ebl.media.domain import Media, MediaAssociation, MediaId, MediaType
from ebl.tests.media.factories import contract_media
from ebl.transliteration.domain.museum_number import MuseumNumber

K1 = MuseumNumber.of("K.1")
PHOTO_ID = MediaId("550e8400-e29b-41d4-a716-446655440000")


def dump_item(media: Media) -> dict[str, object]:
    return cast(
        dict[str, object],
        FragmentMediaItemDtoSchema().dump(FragmentMediaItemDto.of(K1, media)),
    )


class OmitEmptyProbeSchema(OmitEmptyMixin, Schema):
    text = fields.String()
    number = fields.Integer()
    flag = fields.Boolean()
    tags = fields.List(fields.String())
    mapping = fields.Dict()


@pytest.mark.parametrize(
    "field_name,value,is_omitted",
    [
        ("text", None, True),
        ("text", "", False),
        ("text", "value", False),
        ("number", None, True),
        ("number", 0, False),
        ("number", 1, False),
        ("flag", None, True),
        ("flag", False, False),
        ("flag", True, False),
        ("tags", (), True),
        ("tags", ("a",), False),
        ("mapping", {}, True),
        ("mapping", {"a": "b"}, False),
    ],
)
def test_omit_empty_only_drops_none_and_empty_collections(
    field_name: str, value: object, is_omitted: bool
) -> None:
    result = OmitEmptyProbeSchema().dump({field_name: value})

    assert (field_name not in result) is is_omitted


def test_omit_empty_preserves_declared_empty_collections() -> None:
    class PreservingSchema(OmitEmptyProbeSchema):
        preserve_empty_collections = frozenset({"tags"})

    assert PreservingSchema().dump({"tags": (), "mapping": {}}) == {"tags": []}


def test_zero_sort_order_and_false_is_primary_survive_serialization() -> None:
    media = contract_media(PHOTO_ID, MediaType.PHOTO, (MediaAssociation(K1, 0, False),))

    result = dump_item(media)

    assert result["sortOrder"] == 0
    assert result["isPrimary"] is False


def test_absent_optional_media_metadata_is_omitted() -> None:
    media = contract_media(PHOTO_ID, MediaType.PHOTO, (MediaAssociation(K1, 0, True),))

    result = dump_item(media)

    assert "caption" not in result
    assert "attribution" not in result
    assert "references" not in result
    assert "display" not in cast(dict[str, object], result["representations"])
