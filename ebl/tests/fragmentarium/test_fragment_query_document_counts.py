from typing import Sequence

import attr
import falcon
import pytest

from ebl.common.domain.period import Period
from ebl.common.domain.project import ResearchProject
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.domain.fragment import Fragment, Genre, Script
from ebl.fragmentarium.domain.museum import Museum
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.fragment import FragmentFactory, TransliteratedFragmentFactory
from ebl.tests.factories.provenance import DEFAULT_NON_STANDARD_PROVENANCES
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.fixture
def counted_fragments(fragment_repository) -> Sequence[Fragment]:
    fragments = [
        FragmentFactory.build(
            number=MuseumNumber.of(f"X.{index}"),
            museum=Museum.ASHMOLEAN_MUSEUM,
            script=Script(Period.NEO_ASSYRIAN),
            genres=(Genre(["CANONICAL", "Technical"], False),),
            projects=(ResearchProject.CAIC,),
            references=(ReferenceFactory.build(id="COUNTED"),),
        )
        for index in range(4)
    ]
    for index, fragment in enumerate(fragments):
        fragment = attr.evolve(
            fragment,
            archaeology=attr.evolve(
                fragment.archaeology, site=DEFAULT_NON_STANDARD_PROVENANCES[0]
            ),
            authorized_scopes=(
                [Scope.READ_ITALIANNINEVEH_FRAGMENTS] if index == 3 else []
            ),
        )
        fragment_repository.create(fragment, sort_key=index)
    return fragments


@pytest.mark.parametrize(
    "filters",
    [
        {"bibId": "COUNTED"},
        {"genre": ["CANONICAL"]},
        {"project": "CAIC"},
        {"museum": "ASHMOLEAN_MUSEUM"},
        {"scriptPeriod": "Neo-Assyrian"},
        {"site": DEFAULT_NON_STANDARD_PROVENANCES[0].long_name},
        {"bibId": "COUNTED", "genre": ["Technical"], "project": "CAIC"},
    ],
)
@pytest.mark.parametrize("offset,expected_size", [(0, 2), (2, 1), (3, 0), (99, 0)])
def test_metadata_counts_documents_before_pagination(
    fragment_repository, counted_fragments, filters, offset, expected_size
) -> None:
    result = fragment_repository.query({**filters, "limit": 2, "offset": offset})

    assert result.total_documents == 3
    assert result.match_count_total == 0
    assert len(result.items) == expected_size


@pytest.mark.parametrize("count", ["exact", "page", "none"])
def test_document_totals_follow_access_scopes(
    client, guest_client, counted_fragments, count
) -> None:
    parameters = {"bibId": "COUNTED", "limit": "2", "count": count}
    for current_client, expected_total in [(client, 4), (guest_client, 3)]:
        response = current_client.simulate_get("/fragments/query", params=parameters)
        assert response.status == falcon.HTTP_OK
        assert len(response.json["items"]) == 2
        assert response.json["totalDocuments"] == (
            expected_total if count == "exact" else None
        )
        assert response.json["hasNextPage"] == (True if count == "page" else None)


@pytest.mark.parametrize("number,expected", [("X.0", 1), ("X.100", 0)])
def test_zero_and_one_document_totals(
    fragment_repository, counted_fragments, number, expected
) -> None:
    result = fragment_repository.query({"number": number, "limit": 1})
    assert result.total_documents == expected
    assert len(result.items) == expected


def test_document_total_is_separate_from_line_matches(fragment_repository) -> None:
    fragment_repository.create(TransliteratedFragmentFactory.build())
    result = fragment_repository.query({"transliteration": ["X"], "limit": 1})
    assert result.total_documents == 1
    assert result.match_count_total == 2


def test_large_exact_count_only_hydrates_the_requested_page(
    fragment_repository, monkeypatch
) -> None:
    fragment_repository.create_many(
        [
            FragmentFactory.build(number=MuseumNumber.of(f"X.{index}"))
            for index in range(237)
        ]
    )
    hydrated_ids: list[str] = []
    original_find = fragment_repository._find_fragment_query_summary_data

    def find_summaries(fragment_ids: Sequence[str]) -> dict:
        hydrated_ids.extend(fragment_ids)
        return original_find(fragment_ids)

    monkeypatch.setattr(
        fragment_repository, "_find_fragment_query_summary_data", find_summaries
    )
    result = fragment_repository.query({"limit": 50, "offset": 100, "count": "exact"})
    assert result.total_documents == 237
    assert len(result.items) == len(hydrated_ids) == 50


def test_empty_search_has_known_zero_documents(client) -> None:
    result = client.simulate_get("/fragments/query")
    assert result.status == falcon.HTTP_OK
    assert result.json["items"] == []
    assert result.json["totalDocuments"] == 0
