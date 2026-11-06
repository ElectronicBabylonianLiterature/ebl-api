from typing import Mapping, Sequence, cast

import pytest
from marshmallow import ValidationError

from ebl.sumerian_dictionary.infrastructure.sumerian_word_schemas import (
    SumerianWordDocumentSchema,
    SumerianWordSchema,
)
from ebl.tests.factories.sumerian_dictionary import build_complete_word
from ebl.tests.sumerian_dictionary.test_sumerian_word_schemas import MINIMAL_DOCUMENT

RENDERING_KEYS = {
    "spelling",
    "cuneiform",
    "complete",
    "signLists",
    "unrendered",
    "knownWrongCharacters",
}


def _dumped_renderings(field: str) -> Sequence[Mapping[str, object]]:
    dumped = cast(dict, SumerianWordSchema().dump(build_complete_word()))
    return dumped[field]


@pytest.mark.parametrize(
    "field,expected_keys",
    [
        ("attingerKeyRenderings", RENDERING_KEYS),
        ("attingerVariantRenderings", {*RENDERING_KEYS, "printed"}),
        ("epsd2FormRenderings", RENDERING_KEYS),
    ],
)
def test_each_rendering_array_holds_one_shape(field: str, expected_keys: set) -> None:
    renderings = _dumped_renderings(field)

    assert renderings
    assert all(set(rendering) == expected_keys for rendering in renderings)


def test_printed_is_kept_on_attinger_variants() -> None:
    assert _dumped_renderings("attingerVariantRenderings")[0]["printed"] == (
        "˹lu˺-ga-al"
    )


def test_the_old_mixed_renderings_array_is_rejected() -> None:
    split_fields = (
        "attingerKeyRenderings",
        "attingerVariantRenderings",
        "epsd2FormRenderings",
    )
    document = {
        **{
            key: value
            for key, value in MINIMAL_DOCUMENT.items()
            if key not in split_fields
        },
        "renderings": [
            {
                "spelling": "a",
                "source": "attinger",
                "kind": "key",
                "cuneiform": ["𒀀"],
                "complete": True,
            }
        ],
    }

    with pytest.raises(ValidationError):
        SumerianWordDocumentSchema().load(document)
