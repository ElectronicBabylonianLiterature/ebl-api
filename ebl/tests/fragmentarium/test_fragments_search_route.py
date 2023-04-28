from typing import Dict, List, Optional

import attr
import falcon
import pytest
from ebl.common.domain.period import Period, PeriodModifier

from ebl.fragmentarium.application.fragment_info_schema import (
    ApiFragmentInfoSchema,
    ApiFragmentInfosPaginationSchema,
)
from ebl.fragmentarium.domain.fragment import Fragment, Script
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.fragment_infos_pagination import FragmentInfosPagination
from ebl.tests.factories.bibliography import ReferenceFactory, BibliographyEntryFactory
from ebl.tests.factories.fragment import (
    FragmentFactory,
    InterestingFragmentFactory,
    TransliteratedFragmentFactory,
    LemmatizedFragmentFactory,
)
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.fragmentarium.domain.genres import genres
from ebl.common.domain.scopes import Scope


def expected_fragment_info_dto(fragment: Fragment, text=None) -> Dict:
    return ApiFragmentInfoSchema().dump(FragmentInfo.of(fragment, text))


def expected_fragment_infos_pagination_dto(
    fragment_infos_pagination: FragmentInfosPagination,
) -> Dict:
    return ApiFragmentInfosPaginationSchema().dump(fragment_infos_pagination)


def query_item_of(
    fragment: Fragment,
    matching_lines: Optional[List[int]] = None,
    match_count: Optional[int] = None,
) -> Dict:
    lines = [] if matching_lines is None else matching_lines

    return {
        "museumNumber": MuseumNumberSchema().dump(fragment.number),
        "matchingLines": lines,
        "matchCount": match_count or len(lines),
    }


@pytest.mark.parametrize(
    "get_number",
    [
        lambda fragment: str(fragment.number),
        lambda fragment: fragment.cdli_number,
        lambda fragment: fragment.accession,
    ],
)
def test_query_fragmentarium_number(get_number, client, fragmentarium):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    result = client.simulate_get(
        "/fragments/query",
        params={
            "number": get_number(fragment),
        },
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == {
        "items": [query_item_of(fragment)],
        "matchCountTotal": 0,
    }


def test_query_fragmentarium_number_not_found(client):
    result = client.simulate_get(
        "/fragments/query",
        params={"number": "K.1"},
    )

    assert result.json == {"items": [], "matchCountTotal": 0}


def test_query_fragmentarium_references(client, fragmentarium, bibliography, user):
    bib_entry_1 = BibliographyEntryFactory.build(id="RN.0", pages="254")
    bib_entry_2 = BibliographyEntryFactory.build(id="RN.1")
    bibliography.create(bib_entry_1, user)
    bibliography.create(bib_entry_2, user)

    fragment = FragmentFactory.build(
        references=(
            ReferenceFactory.build(id="RN.0", pages="254"),
            ReferenceFactory.build(id="RN.1"),
        )
    )
    fragmentarium.create(fragment)
    result = client.simulate_get(
        "/fragments/query",
        params={
            "bibId": fragment.references[0].id,
            "pages": fragment.references[0].pages,
        },
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == {
        "items": [query_item_of(fragment)],
        "matchCountTotal": 0,
    }


def test_query_fragmentarium_invalid_references(client, fragmentarium):
    fragment = FragmentFactory.build(
        references=(ReferenceFactory.build(), ReferenceFactory.build())
    )
    fragmentarium.create(fragment)
    reference_id = fragment.references[0].id
    reference_pages = "should be a number"
    result = client.simulate_get(
        "/fragments/query",
        params={"bibId": reference_id, "pages": reference_pages},
    )
    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_query_fragmentarium_transliteration(
    client, fragmentarium, sign_repository, signs
):
    transliterated_fragments = [
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of("X.123"), script=Script(Period.MIDDLE_ASSYRIAN)
        ),
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of("X.5"), script=Script(Period.LATE_BABYLONIAN)
        ),
        TransliteratedFragmentFactory.build(
            number=MuseumNumber.of("X.42"), script=Script(Period.LATE_BABYLONIAN)
        ),
    ]
    for fragment in transliterated_fragments:
        fragmentarium.create(fragment)

    fragmentarium._repository._create_sort_index()

    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "ma-tu₂"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == {
        "items": [
            query_item_of(fragment, matching_lines=[3])
            for fragment in transliterated_fragments
        ],
        "matchCountTotal": 3,
    }


@pytest.mark.parametrize(
    "lemma_operator,lemmas,expected_lines",
    [
        ("and", "ana I+ginâ I", [1]),
        ("or", "ginâ I+bamātu I+mu I", [1, 2, 3]),
        ("line", "u I+kīdu I", [2]),
        ("phrase", "mu I+tamalāku I", [3]),
    ],
)
def test_query_fragmentarium_lemmas(
    client, fragmentarium, lemma_operator, lemmas, expected_lines
):
    fragment = LemmatizedFragmentFactory.build()
    fragmentarium.create(fragment)

    result = client.simulate_get(
        "/fragments/query",
        params={"lemmaOperator": lemma_operator, "lemmas": lemmas},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == {
        "items": [query_item_of(fragment, matching_lines=expected_lines)],
        "matchCountTotal": len(expected_lines),
    }


def test_query_fragmentarium_lemmas_not_found(client, fragmentarium):
    fragment = LemmatizedFragmentFactory.build()
    fragmentarium.create(fragment)

    result = client.simulate_get(
        "/fragments/query",
        params={"lemmaOperator": "phrase", "lemmas": "u I+u I+u I"},
    )
    assert result.status == falcon.HTTP_OK
    assert result.json == {
        "items": [],
        "matchCountTotal": 0,
    }


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

    assert result.json == {
        "items": [query_item_of(fragment, matching_lines=[1, 3])],
        "matchCountTotal": 2,
    }


def test_query_signs_invalid(client, fragmentarium, sign_repository, signs):
    result = client.simulate_get(
        "/fragments/query",
        params={"transliteration": "$ invalid"},
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_random(client, fragmentarium):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)

    result = client.simulate_get("/fragments", params={"random": True})

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(transliterated_fragment)]
    assert "Cache-Control" not in result.headers


def test_interesting(client, fragmentarium):
    interesting_fragment = InterestingFragmentFactory.build(
        number=MuseumNumber("K", "1")
    )
    fragmentarium.create(interesting_fragment)

    result = client.simulate_get("/fragments", params={"interesting": True})

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(interesting_fragment)]
    assert "Cache-Control" not in result.headers


def test_latest(client, fragmentarium):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)

    result = client.simulate_get("/fragments", params={"latest": True})

    assert result.status == falcon.HTTP_OK
    assert result.json == [expected_fragment_info_dto(transliterated_fragment)]
    assert result.headers["Cache-Control"] == "private, max-age=600"


def test_needs_revision(client, fragmentarium):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragmentarium.create(transliterated_fragment)

    result = client.simulate_get("/fragments", params={"needsRevision": True})

    assert result.status == falcon.HTTP_OK
    assert result.json == [
        expected_fragment_info_dto(attr.evolve(transliterated_fragment, genres=tuple()))
    ]
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


def test_search_with_scopes(client, guest_client, fragmentarium):
    fragment = FragmentFactory.build(
        authorized_scopes=[Scope.READ_ITALIANNINEVEH_FRAGMENTS]
    )
    params = {
        "number": str(fragment.number),
    }

    fragmentarium.create(fragment)

    result = client.simulate_get("/fragments/query", params=params)
    guest_result = guest_client.simulate_get("/fragments/query", params=params)

    assert result.status == falcon.HTTP_OK
    assert result.json == {
        "items": [query_item_of(fragment)],
        "matchCountTotal": 0,
    }

    assert guest_result.status == falcon.HTTP_OK
    assert guest_result.json == {
        "items": [],
        "matchCountTotal": 0,
    }


@pytest.mark.parametrize(
    "params,expected",
    [
        ({"scriptPeriod": Period.NEO_BABYLONIAN.long_name}, [0]),
        ({"scriptPeriod": Period.OLD_ASSYRIAN.long_name}, [1, 2]),
        (
            {
                "scriptPeriod": Period.OLD_ASSYRIAN.long_name,
                "scriptPeriodModifier": PeriodModifier.LATE.value,
            },
            [2],
        ),
        ({"scriptPeriod": Period.NEO_BABYLONIAN.long_name}, [0]),
    ],
)
def test_search_script_period(client, fragmentarium, params, expected):
    scripts = [
        Script(Period.NEO_BABYLONIAN),
        Script(Period.OLD_ASSYRIAN, PeriodModifier.EARLY),
        Script(Period.OLD_ASSYRIAN, PeriodModifier.LATE),
    ]
    fragments = [FragmentFactory.build(script=script) for script in scripts]

    for fragment in fragments:
        fragmentarium.create(fragment)

    expected_json = {
        "items": [query_item_of(fragments[i]) for i in expected],
        "matchCountTotal": 0,
    }

    result = client.simulate_get("/fragments/query", params=params)

    assert result.status == falcon.HTTP_OK
    assert result.json == expected_json
