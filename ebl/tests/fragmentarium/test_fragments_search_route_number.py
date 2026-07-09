from datetime import date, timedelta

import falcon
import pytest

from ebl.tests.factories.bibliography import BibliographyEntryFactory, ReferenceFactory
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.fragment_query_test_helpers import (
    query_item_of,
    query_result_of,
    query_summary_of,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.mark.parametrize(
    "get_number",
    [
        lambda fragment: str(fragment.number),
        lambda fragment: fragment.cdli_number,
        lambda fragment: str(fragment.accession),
        lambda fragment: str(fragment.archaeology.excavation_number),
    ],
)
def test_query_fragmentarium_number(get_number, client, fragmentarium):
    fragment = FragmentFactory.build()
    fragmentarium.create(fragment)

    result = client.simulate_get(
        "/fragments/query",
        params={"number": get_number(fragment)},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([query_item_of(fragment)], 0)


def test_query_fragmentarium_number_summary_only(client, fragmentarium):
    fragment = FragmentFactory.build(number=MuseumNumber.of("K.1"))
    fragmentarium.create(fragment)

    result = client.simulate_get(
        "/fragments/query",
        params={"number": str(fragment.number), "limit": "1"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([query_summary_of(fragment, has_photo=True)], 0)
    assert result.json["items"][0]["matchingLinePreview"]["lines"] == []
    assert result.json["items"][0]["matchingLinePreview"]["parserVersion"] is not None
    assert "text" not in result.json["items"][0]
    assert "record" not in result.json["items"][0]
    assert "atf" not in result.json["items"][0]


def test_query_fragmentarium_number_not_found(client):
    result = client.simulate_get("/fragments/query", params={"number": "K.1"})

    assert result.json == query_result_of([], 0)


def test_query_fragmentarium_empty_query_includes_count_metadata(client):
    result = client.simulate_get("/fragments/query")

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([], 0)


def test_query_fragmentarium_pagination_index_only_matches_empty_query(client):
    result = client.simulate_get("/fragments/query", params={"paginationIndex": 999})

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([], 0)


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
        params={"bibId": fragment.references[0].id, "pages": fragment.references[0].pages},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([query_item_of(fragment)], 0)
