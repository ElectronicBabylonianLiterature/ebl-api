from ebl.common.domain.period import Period
import attr
import falcon
import pytest

from ebl.fragmentarium.domain.genres import genres
from ebl.fragmentarium.domain.fragment import Genre, Script
from ebl.tests.factories.bibliography import BibliographyEntryFactory, ReferenceFactory
from ebl.tests.factories.fragment import (
    FragmentFactory,
    InterestingFragmentFactory,
    LemmatizedFragmentFactory,
    TransliteratedFragmentFactory,
)
from ebl.tests.fragmentarium.fragment_query_test_helpers import (
    expected_fragment_info_dto,
    query_item_of,
    query_result_of,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_query_fragmentarium_transliteration_without_limit_returns_all_lean_items(
    client, fragmentarium, sign_repository, signs
):
    fragments = [
        TransliteratedFragmentFactory.build()
        for _ in range(101)
    ]
    for fragment in fragments:
        fragmentarium.create(fragment)
    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂"},
    )

    assert result.status == falcon.HTTP_OK
    assert len(result.json["items"]) == 101
    assert result.json["matchCountTotal"] == 101
    assert "matchingLinePreview" not in result.json["items"][0]


def test_query_fragmentarium_lemmas_not_found(client, fragmentarium):
    fragment = LemmatizedFragmentFactory.build()
    fragmentarium.create(fragment)

    result = client.simulate_get(
        "/fragments/query",
        params={"lemmaOperator": "phrase", "lemmas": "u I+u I+u I"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([], 0)


def test_query_fragmentarium_combined_query(
    client, fragmentarium, sign_repository, signs, bibliography, user
):
    bib_entry_1 = BibliographyEntryFactory.build(id="RN.0", pages="254")
    bib_entry_2 = BibliographyEntryFactory.build(id="RN.1")
    bibliography.create(bib_entry_1, user)
    bibliography.create(bib_entry_2, user)
    fragment = LemmatizedFragmentFactory.build(
        references=(
            ReferenceFactory.build(id="RN.0", pages="254"),
            ReferenceFactory.build(id="RN.1"),
        )
    )
    fragmentarium.create(fragment)
    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={
            "number": str(fragment.number),
            "transliteration": "ma-tu₂",
            "bibId": fragment.references[0].id,
            "pages": fragment.references[0].pages,
            "lemmas": "ana I+mu I",
            "lemmaOperator": "or",
        },
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [query_item_of(fragment, matching_lines=[1, 3])],
        2,
    )


def test_query_fragmentarium_ignores_pagination_index(client, fragmentarium):
    genre = Genre(["CANONICAL", "Technical"], False)
    fragments = FragmentFactory.build_batch(2, genres=(genre,), script=Script())
    for index, fragment in enumerate(fragments):
        fragmentarium.create(fragment, sort_key=index)

    result = client.simulate_get(
        "/fragments/query",
        params={"genre": ":".join(genre.category), "paginationIndex": 999},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([query_item_of(fragment) for fragment in fragments], 0)


def test_query_signs_invalid(client, fragmentarium, sign_repository, signs):
    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "$ invalid"},
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_random(client, fragmentarium):
    fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(fragment)

    result = client.simulate_get("/fragments", params={"random": True})

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(fragment)]
    assert "Cache-Control" not in result.headers


def test_interesting(client, fragmentarium):
    fragment = InterestingFragmentFactory.build(number=MuseumNumber("K", "1"))
    fragmentarium.create(fragment)

    result = client.simulate_get("/fragments", params={"interesting": True})

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(fragment)]
    assert "Cache-Control" not in result.headers


def test_needs_revision(client, fragmentarium):
    fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(fragment)
    expected_dto = [expected_fragment_info_dto(attr.evolve(fragment, genres=()))]
    if "acquisition" in expected_dto[0]:
        del expected_dto[0]["acquisition"]

    result = client.simulate_get("/fragments", params={"needsRevision": True})

    assert result.status == falcon.HTTP_OK
    assert result.json == expected_dto
    assert result.headers["Cache-Control"] == "private, max-age=600"


def test_search_fragment_no_query(client):
    result = client.simulate_get("/fragments")

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "parameters",
    [
        {},
        {"random": True, "interesting": True},
        {"random": True, "interesting": True, "pages": "254"},
        {"invalid": "parameter"},
        {"a": "a", "b": "b", "c": "c"},
    ],
)
def test_search_invalid_params(client, parameters):
    result = client.simulate_get("/fragments", params=parameters)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize(
    "endpoint,expected",
    [
        ("/genres", list(map(list, genres))),
        (
            "/periods",
            [period.long_name for period in Period if period is not Period.NONE],
        ),
    ],
)
def test_get_options(client, endpoint, expected):
    result = client.simulate_get(endpoint)

    assert result.status == falcon.HTTP_OK
    assert result.json == expected
