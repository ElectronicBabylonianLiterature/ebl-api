from typing import Dict

import attr
import falcon
import pytest

from ebl.fragmentarium.application.fragment_info_schema import (
    ApiFragmentInfoSchema,
    ApiFragmentInfosPaginationSchema,
)
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.fragment_info import FragmentInfo
from ebl.fragmentarium.domain.fragment_infos_pagination import FragmentInfosPagination
from ebl.tests.factories.bibliography import ReferenceFactory, BibliographyEntryFactory
from ebl.tests.factories.fragment import (
    FragmentFactory,
    InterestingFragmentFactory,
    TransliteratedFragmentFactory,
)
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.transliteration.domain.museum_number import MuseumNumber


def expected_fragment_info_dto(fragment: Fragment, text=None) -> Dict:
    return ApiFragmentInfoSchema().dump(FragmentInfo.of(fragment, text))


def expected_fragment_infos_pagination_dto(
    fragment_infos_pagination: FragmentInfosPagination,
) -> Dict:
    return ApiFragmentInfosPaginationSchema().dump(fragment_infos_pagination)


@pytest.mark.parametrize(
    "get_number",
    [
        lambda fragment: str(fragment.number),
        lambda fragment: fragment.cdli_number,
        lambda fragment: fragment.accession,
    ],
)
def test_search_fragmentarium_number(get_number, client, fragmentarium):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)
    result = client.simulate_get(
        "/fragments",
        params={
            "number": get_number(fragment),
            "transliteration": "",
            "bibliographyId": "",
            "pages": "",
            "paginationIndex": 0,
        },
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == expected_fragment_infos_pagination_dto(
        FragmentInfosPagination([FragmentInfo.of(fragment)], 1)
    )

    assert "Cache-Control" not in result.headers


def test_search_fragmentarium_number_not_found(client):
    result = client.simulate_get(
        "/fragments",
        params={
            "number": "K.1",
            "transliteration": "",
            "bibliographyId": "",
            "pages": "",
            "paginationIndex": 0,
        },
    )

    assert result.json == expected_fragment_infos_pagination_dto(
        FragmentInfosPagination([], 0)
    )


def test_search_fragmentarium_references(client, fragmentarium, bibliography, user):
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
        "/fragments",
        params={
            "number": "",
            "transliteration": "",
            "bibliographyId": fragment.references[0].id,
            "pages": fragment.references[0].pages,
            "paginationIndex": 0,
        },
    )

    assert result.status == falcon.HTTP_OK

    fragment_expected = fragment.set_references(
        [
            fragment.references[0].set_document(bib_entry_1),
            fragment.references[1].set_document(bib_entry_2),
        ]
    )
    assert result.json == expected_fragment_infos_pagination_dto(
        FragmentInfosPagination([FragmentInfo.of(fragment_expected)], 1)
    )
    assert "Cache-Control" not in result.headers


def test_search_fragmentarium_invalid_references_query(client, fragmentarium):
    fragment = FragmentFactory.build(
        references=(ReferenceFactory.build(), ReferenceFactory.build())
    )
    fragmentarium.create(fragment)
    reference_id = fragment.references[0].id
    reference_pages = "should be a number"
    result = client.simulate_get(
        "/fragments",
        params={
            "number": "",
            "transliteration": "",
            "bibliographyId": reference_id,
            "pages": reference_pages,
            "paginationIndex": 0,
        },
    )
    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_fragmentarium_transliteration(
    client, fragmentarium, sign_repository, signs
):
    transliterated_fragment_1 = TransliteratedFragmentFactory.build(script="A")
    transliterated_fragment_2 = TransliteratedFragmentFactory.build(
        number=MuseumNumber.of("X.123"), script="B"
    )
    for transliterated_fragment in [
        transliterated_fragment_1,
        transliterated_fragment_2,
    ]:
        fragmentarium.create(transliterated_fragment)

    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments",
        params={
            "number": "",
            "transliteration": "ma-tu₂",
            "pages": "",
            "bibliographyId": "",
            "paginationIndex": 0,
        },
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == expected_fragment_infos_pagination_dto(
        FragmentInfosPagination(
            [
                FragmentInfo.of(
                    transliterated_fragment_1,
                    parse_atf_lark("6'. [...] x# mu ta-ma;-tu₂"),
                ),
                FragmentInfo.of(
                    transliterated_fragment_2,
                    parse_atf_lark("6'. [...] x# mu ta-ma;-tu₂"),
                ),
            ],
            2,
        )
    )

    assert "Cache-Control" not in result.headers


def test_search_fragmentarium_combined_query(
    client, fragmentarium, sign_repository, signs, bibliography, user
):
    bib_entry_1 = BibliographyEntryFactory.build(id="RN.0", pages="254")
    bib_entry_2 = BibliographyEntryFactory.build(id="RN.1")
    bibliography.create(bib_entry_1, user)
    bibliography.create(bib_entry_2, user)

    fragment = TransliteratedFragmentFactory.build(
        references=(
            ReferenceFactory.build(id="RN.0", pages="254"),
            ReferenceFactory.build(id="RN.1"),
        )
    )
    fragmentarium.create(fragment)

    for sign in signs:
        sign_repository.create(sign)

    result = client.simulate_get(
        "/fragments",
        params={
            "number": str(fragment.number),
            "transliteration": "ma-tu₂",
            "bibliographyId": fragment.references[0].id,
            "pages": fragment.references[0].pages,
            "paginationIndex": 0,
        },
    )

    assert result.status == falcon.HTTP_OK

    fragment_expected = fragment.set_references(
        [
            fragment.references[0].set_document(bib_entry_1),
            fragment.references[1].set_document(bib_entry_2),
        ]
    )
    assert result.json == expected_fragment_infos_pagination_dto(
        FragmentInfosPagination(
            [
                FragmentInfo.of(
                    fragment_expected, parse_atf_lark("6'. [...] x# mu ta-ma;-tu₂")
                )
            ],
            1,
        )
    )
    assert "Cache-Control" not in result.headers


def test_search_signs_invalid(client, fragmentarium, sign_repository, signs):
    result = client.simulate_get(
        "/fragments",
        params={
            "number": "",
            "transliteration": "$ invalid",
            "bibliographyId": "",
            "pages": "",
            "paginationIndex": 0,
        },
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "Cache-Control" not in result.headers


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
