import falcon
import pytest

from ebl.common.domain.period import Period
from ebl.fragmentarium.domain.fragment import Script
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.tests.fragmentarium.fragment_query_test_helpers import (
    query_item_of,
    query_result_of,
    query_summary_of,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_query_fragmentarium_transliteration_count_none(
    client, fragmentarium, sign_repository, signs
):
    fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            script=Script(Period.LATE_BABYLONIAN),
        )
        for index in range(3)
    ]
    for fragment in fragments:
        fragmentarium.create(fragment)
    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂", "limit": "2", "count": "none"},
    )

    assert result.status == falcon.HTTP_OK
    assert len(result.json["items"]) == 2
    assert result.json["matchCountTotal"] is None
    assert result.json["isMatchCountTotalExact"] is False
    assert result.json["hasNextPage"] is None


def test_query_fragmentarium_transliteration_count_page(
    client, fragmentarium, sign_repository, signs
):
    fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            script=Script(Period.LATE_BABYLONIAN),
        )
        for index in range(3)
    ]
    for index, fragment in enumerate(fragments):
        fragmentarium.create(fragment, sort_key=index)
    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂", "limit": "2", "count": "page"},
    )
    last_page_result = client.simulate_get(
        "/fragments/query",
        params={
            "transliteration": "ma-tu₂",
            "limit": "2",
            "offset": "2",
            "count": "page",
        },
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [query_summary_of(fragment, matching_lines=[3]) for fragment in fragments[:2]],
        None,
        False,
        True,
    )
    assert last_page_result.status == falcon.HTTP_OK
    assert last_page_result.json == query_result_of(
        [query_summary_of(fragments[2], matching_lines=[3])],
        None,
        False,
        False,
    )


def test_query_fragmentarium_transliteration_limit_with_offset(
    client, fragmentarium, sign_repository, signs
):
    fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            script=Script(Period.LATE_BABYLONIAN),
        )
        for index in range(4)
    ]
    for index, fragment in enumerate(fragments):
        fragmentarium.create(fragment, sort_key=index)
    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂", "limit": "2", "offset": "1"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [query_summary_of(fragment, matching_lines=[3]) for fragment in fragments[1:3]],
        4,
    )
    assert result.json["items"][0]["matchingLinePreview"]["parserVersion"] is not None


def test_query_fragmentarium_transliteration_offset_without_limit_returns_lean_items(
    client, fragmentarium, sign_repository, signs
):
    fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            script=Script(Period.LATE_BABYLONIAN),
        )
        for index in range(4)
    ]
    for index, fragment in enumerate(fragments):
        fragmentarium.create(fragment, sort_key=index)
    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂", "offset": "2"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [query_item_of(fragment, matching_lines=[3]) for fragment in fragments[2:]],
        4,
    )


def test_query_fragmentarium_transliteration_offset_zero_is_accepted(
    client, fragmentarium, sign_repository, signs
):
    fragment = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.0"),
        script=Script(Period.LATE_BABYLONIAN),
    )
    fragmentarium.create(fragment)
    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂", "limit": "1", "offset": "0"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [query_summary_of(fragment, matching_lines=[3])],
        1,
    )


@pytest.mark.parametrize("offset", ["invalid", "-1"])
def test_query_fragmentarium_offset_invalid(client, offset):
    result = client.simulate_get(
        "/fragments/query",
        params={"number": "K.1", "offset": offset},
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("count", ["false", "0", "random", "approx"])
def test_query_fragmentarium_count_invalid(client, count):
    result = client.simulate_get(
        "/fragments/query",
        params={"number": "K.1", "count": count},
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
