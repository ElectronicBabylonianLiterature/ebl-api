from typing import cast

import falcon
import pytest

from ebl.common.domain.period import Period
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.fragmentarium.domain.fragment import Script
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.tests.fragmentarium.stored_line_shapes import legacy_shape, sparse_shape
from ebl.transliteration.domain.museum_number import MuseumNumber

MATCHING_LINE_INDEX = 3


@pytest.fixture
def full_fragment_lines(fragmentarium, sign_repository, signs, database) -> list:
    fragment = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.1"), script=Script(Period.LATE_BABYLONIAN)
    )
    fragmentarium.create(fragment)
    for sign in signs:
        sign_repository.create(sign)
    lines = cast(dict, FragmentSchema().dump(fragment))["text"]["lines"]
    database["fragments"].update_one(
        {"_id": "X.1"},
        {"$set": {"text.lines": sparse_shape(legacy_shape(lines))}},
    )
    return lines


def test_preview_of_a_legacy_sparse_fragment_is_the_full_api_shape(
    client, full_fragment_lines
):
    result = client.simulate_get(
        "/fragments/query", params={"transliteration": "ma-tu₂", "limit": "10"}
    )
    detail = client.simulate_get("/fragments/X.1").json
    preview_line = result.json["items"][0]["matchingLinePreview"]["lines"][0]
    expected_line = full_fragment_lines[MATCHING_LINE_INDEX]

    assert result.status == falcon.HTTP_OK
    assert sparse_shape(legacy_shape(expected_line)) != expected_line
    assert preview_line == {**expected_line, "index": MATCHING_LINE_INDEX}
    assert detail["text"]["lines"][MATCHING_LINE_INDEX] == expected_line
