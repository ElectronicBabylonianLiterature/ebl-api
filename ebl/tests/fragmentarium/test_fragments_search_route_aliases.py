import falcon
import pytest

from ebl.bibliography.application.partner_identity import create_partner_alias
from ebl.common.domain.scopes import Scope
from ebl.tests.factories.bibliography import BibliographyEntryFactory, ReferenceFactory
from ebl.tests.fragmentarium.test_fragments_search_route_bibliography import (
    build_fragment,
)
from ebl.tests.fragmentarium.fragment_alias_search_test_helpers import (
    equivalent_bibliography as _equivalent_bibliography,
)

equivalent_bibliography = _equivalent_bibliography


@pytest.mark.parametrize(
    "bib_id",
    [
        "UBHD-1718224",
        "RN1971axx",
        "LS276",
        "Rawlinson1870",
        "DEPRECATED",
        "OLDER",
        "rn1971axx",
    ],
)
def test_search_equivalent_ids_combines_historical_references(
    client, fragmentarium, equivalent_bibliography, bib_id
):
    for index, id_ in enumerate(
        ["UBHD-1718224", "RN1971axx", "LS276", "Rawlinson1870", "DEPRECATED", "OLDER"]
    ):
        fragmentarium.create(
            build_fragment(f"X.{index}", ReferenceFactory.build(id=id_)), sort_key=index
        )
    result = client.simulate_get(
        "/fragments/query", params={"bibId": bib_id, "limit": "2", "offset": "1"}
    )
    assert result.status == falcon.HTTP_OK
    assert [item["museumNumber"]["number"] for item in result.json["items"]] == [
        "1",
        "2",
    ]
    assert result.json["matchCountTotal"] == 0
    assert result.json["hasNextPage"] is None
    full_result = client.simulate_get(
        "/fragments/query", params={"bibId": bib_id, "limit": "10"}
    )
    assert len(full_result.json["items"]) == 6


def test_alias_pages_match_the_same_reference(
    client, fragmentarium, equivalent_bibliography
):
    fragmentarium.create(
        build_fragment("X.1", ReferenceFactory.build(id="RN1971axx", pages="12"))
    )
    fragmentarium.create(
        build_fragment("X.2", ReferenceFactory.build(id="UBHD-1718224", pages="112"))
    )
    fragmentarium.create(
        build_fragment(
            "X.3",
            ReferenceFactory.build(id="RN1971axx", pages="34"),
            ReferenceFactory.build(id="UNRELATED", pages="12"),
        )
    )
    result = client.simulate_get(
        "/fragments/query",
        params={"bibId": "UBHD-1718224", "pages": "12", "limit": "10"},
    )
    assert result.status == falcon.HTTP_OK
    assert [item["museumNumber"]["number"] for item in result.json["items"]] == ["1"]


def test_alias_search_preserves_scope_and_other_filters(
    client, guest_client, fragmentarium, equivalent_bibliography
):
    import attr

    fragment = build_fragment("X.1", ReferenceFactory.build(id="RN1971axx"))
    fragmentarium.create(
        attr.evolve(fragment, authorized_scopes=[Scope.READ_ITALIANNINEVEH_FRAGMENTS])
    )
    assert (
        len(
            client.simulate_get(
                "/fragments/query", params={"bibId": "UBHD-1718224", "limit": "10"}
            ).json["items"]
        )
        == 1
    )
    assert (
        guest_client.simulate_get(
            "/fragments/query", params={"bibId": "UBHD-1718224", "limit": "10"}
        ).json["items"]
        == []
    )
    assert (
        client.simulate_get(
            "/fragments/query",
            params={"bibId": "UBHD-1718224", "number": "X.2", "limit": "10"},
        ).json["items"]
        == []
    )


def test_unknown_id_remains_literal_and_internal_query_is_untrusted(
    client, fragmentarium
):
    fragmentarium.create(build_fragment("X.1", ReferenceFactory.build(id="MISSING")))
    fragmentarium.create(build_fragment("X.2", ReferenceFactory.build(id="OTHER")))
    result = client.simulate_get(
        "/fragments/query",
        params={"bibId": "MISSING", "_bibliographyIds": "OTHER", "limit": "10"},
    )
    assert result.status == falcon.HTTP_OK
    assert [item["museumNumber"]["number"] for item in result.json["items"]] == ["1"]
    result = client.simulate_get(
        "/fragments/query", params={"_bibliographyIds": "OTHER", "limit": "10"}
    )
    assert len(result.json["items"]) == 2


def test_unrelated_active_id_wins_over_stale_alias(
    client, fragmentarium, bibliography_repository
):
    bibliography_repository.create(
        BibliographyEntryFactory.build(
            id="TARGET", aliases=[create_partner_alias("UNRELATED")]
        )
    )
    bibliography_repository.create(BibliographyEntryFactory.build(id="UNRELATED"))
    fragmentarium.create(build_fragment("X.1", ReferenceFactory.build(id="TARGET")))
    fragmentarium.create(build_fragment("X.2", ReferenceFactory.build(id="UNRELATED")))
    result = client.simulate_get(
        "/fragments/query", params={"bibId": "TARGET", "limit": "10"}
    )
    assert [item["museumNumber"]["number"] for item in result.json["items"]] == ["1"]


@pytest.mark.parametrize("kind", ["ambiguous", "dangling", "cycle", "deep"])
def test_corrupt_id_resolution_fails_closed(
    client, fragmentarium, bibliography_repository, kind
):
    if kind == "ambiguous":
        entries = [
            BibliographyEntryFactory.build(
                id=id_, aliases=[create_partner_alias("BAD")]
            )
            for id_ in ("A", "B")
        ]
    elif kind == "dangling":
        entries = [
            BibliographyEntryFactory.build(
                id="BAD", deprecated=True, redirectTo="ABSENT"
            )
        ]
    elif kind == "cycle":
        entries = [
            BibliographyEntryFactory.build(
                id="BAD", deprecated=True, redirectTo="OTHER"
            ),
            BibliographyEntryFactory.build(
                id="OTHER", deprecated=True, redirectTo="BAD"
            ),
        ]
    else:
        entries = [
            BibliographyEntryFactory.build(
                id=f"R{index}", deprecated=True, redirectTo=f"R{index + 1}"
            )
            for index in range(6)
        ] + [BibliographyEntryFactory.build(id="R6")]
    for entry in entries:
        bibliography_repository.create(entry)
    fragmentarium.create(build_fragment("X.1", ReferenceFactory.build(id="BAD")))
    result = client.simulate_get(
        "/fragments/query",
        params={"bibId": "R6" if kind == "deep" else "BAD", "limit": "10"},
    )
    assert result.status_code in {404, 409, 422}


def test_duplicate_id_parameter_is_rejected(client):
    result = client.simulate_get(
        "/fragments/query", params={"bibId": ["FIRST", "SECOND"], "limit": "10"}
    )
    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("count", ["exact", "page", "none"])
def test_alias_count_modes(client, fragmentarium, equivalent_bibliography, count):
    for index, id_ in enumerate(["UBHD-1718224", "RN1971axx", "LS276"]):
        fragmentarium.create(
            build_fragment(f"X.{index}", ReferenceFactory.build(id=id_)), sort_key=index
        )
    result = client.simulate_get(
        "/fragments/query", params={"bibId": "RN1971axx", "limit": "1", "count": count}
    )
    assert result.status == falcon.HTTP_OK
    assert len(result.json["items"]) == 1
    assert result.json["matchCountTotal"] == (0 if count == "exact" else None)
    assert result.json["hasNextPage"] == (True if count == "page" else None)


def test_alias_unlimited_query_keeps_legacy_shape(
    client, fragmentarium, equivalent_bibliography
):
    for index, id_ in enumerate(["UBHD-1718224", "RN1971axx"]):
        fragmentarium.create(
            build_fragment(f"X.{index}", ReferenceFactory.build(id=id_))
        )
    result = client.simulate_get("/fragments/query", params={"bibId": "RN1971axx"})
    assert result.status == falcon.HTTP_OK
    assert len(result.json["items"]) == 2
    assert "bibliographyDocuments" not in result.json


@pytest.mark.parametrize(
    "limit_name", ["MAX_REFERENCE_SEARCH_ENTRIES", "MAX_REFERENCE_SEARCH_VALUES"]
)
def test_alias_expansion_limits_return_no_partial_results(
    client, fragmentarium, equivalent_bibliography, monkeypatch, limit_name
):
    monkeypatch.setattr(
        f"ebl.bibliography.application.reference_search.{limit_name}", 2
    )
    fragmentarium.create(
        build_fragment("X.1", ReferenceFactory.build(id="UBHD-1718224"))
    )
    result = client.simulate_get(
        "/fragments/query", params={"bibId": "UBHD-1718224", "limit": "10"}
    )
    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "items" not in result.json
