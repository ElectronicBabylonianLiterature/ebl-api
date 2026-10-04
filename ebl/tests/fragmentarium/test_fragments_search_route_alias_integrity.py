import falcon

from ebl.bibliography.application.partner_identity import create_partner_alias
from ebl.tests.factories.bibliography import BibliographyEntryFactory, ReferenceFactory
from ebl.tests.fragmentarium.test_fragments_search_route_bibliography import (
    build_fragment,
)
from ebl.tests.fragmentarium.fragment_alias_search_test_helpers import (
    equivalent_bibliography as _equivalent_bibliography,
)

equivalent_bibliography = _equivalent_bibliography


def test_ambiguous_secondary_alias_is_omitted(
    client, fragmentarium, bibliography_repository
):
    for id_ in ("TARGET", "UNRELATED"):
        bibliography_repository.create(
            BibliographyEntryFactory.build(
                id=id_, aliases=[create_partner_alias("STALE")]
            )
        )
    fragmentarium.create(build_fragment("X.1", ReferenceFactory.build(id="TARGET")))
    fragmentarium.create(build_fragment("X.2", ReferenceFactory.build(id="STALE")))
    result = client.simulate_get(
        "/fragments/query", params={"bibId": "TARGET", "limit": "10"}
    )
    assert result.status == falcon.HTTP_OK
    assert [item["museumNumber"]["number"] for item in result.json["items"]] == ["1"]


def test_reverse_lookup_read_is_bounded(
    client, bibliography_repository, equivalent_bibliography, monkeypatch
):
    calls = []
    original = bibliography_repository.query_by_redirect_target

    def query(id_, limit=None):
        calls.append(limit)
        return original(id_, limit=limit)

    monkeypatch.setattr(bibliography_repository, "query_by_redirect_target", query)
    result = client.simulate_get(
        "/fragments/query", params={"bibId": "UBHD-1718224", "limit": "10"}
    )
    assert result.status == falcon.HTTP_OK
    assert calls == [1001, 1001, 1001]


def test_canonical_and_alias_references_return_fragment_once(
    client, fragmentarium, equivalent_bibliography
):
    fragmentarium.create(
        build_fragment(
            "X.1",
            ReferenceFactory.build(id="UBHD-1718224"),
            ReferenceFactory.build(id="RN1971axx"),
        )
    )
    for bib_id in ("UBHD-1718224", "RN1971axx"):
        result = client.simulate_get(
            "/fragments/query", params={"bibId": bib_id, "limit": "10"}
        )
        assert result.status == falcon.HTTP_OK
        assert [item["museumNumber"]["number"] for item in result.json["items"]] == [
            "1"
        ]
        assert len(result.json["items"][0]["references"]) == 2


def test_predecessor_alias_and_citation_key_contribute_matches(
    client, fragmentarium, bibliography_repository
):
    bibliography_repository.create(BibliographyEntryFactory.build(id="CANONICAL"))
    bibliography_repository.create(
        BibliographyEntryFactory.build(
            id="PREDECESSOR",
            deprecated=True,
            redirectTo="CANONICAL",
            aliases=[create_partner_alias("HistoricalAlias")],
            citationKey="HistoricalCitationKey",
        )
    )
    for index, id_ in enumerate(
        ["CANONICAL", "PREDECESSOR", "HistoricalAlias", "HistoricalCitationKey"]
    ):
        fragmentarium.create(
            build_fragment(f"X.{index}", ReferenceFactory.build(id=id_)), sort_key=index
        )
    for bib_id in ("CANONICAL", "HistoricalAlias", "HistoricalCitationKey"):
        result = client.simulate_get(
            "/fragments/query", params={"bibId": bib_id, "limit": "10"}
        )
        assert result.status == falcon.HTTP_OK
        assert [item["museumNumber"]["number"] for item in result.json["items"]] == [
            "0",
            "1",
            "2",
            "3",
        ]


def test_nondeprecated_stray_redirect_is_not_an_equivalent_identity(
    client, fragmentarium, bibliography_repository
):
    bibliography_repository.create(BibliographyEntryFactory.build(id="CANONICAL"))
    bibliography_repository.create(
        BibliographyEntryFactory.build(
            id="UNRELATED",
            deprecated=False,
            redirectTo="CANONICAL",
            aliases=[create_partner_alias("UnrelatedAlias")],
            citationKey="UnrelatedCitationKey",
        )
    )
    for index, id_ in enumerate(
        ["CANONICAL", "UNRELATED", "UnrelatedAlias", "UnrelatedCitationKey"]
    ):
        fragmentarium.create(
            build_fragment(f"X.{index}", ReferenceFactory.build(id=id_)), sort_key=index
        )
    result = client.simulate_get(
        "/fragments/query", params={"bibId": "CANONICAL", "limit": "10"}
    )
    assert result.status == falcon.HTTP_OK
    assert [item["museumNumber"]["number"] for item in result.json["items"]] == ["0"]


def test_malformed_secondary_aliases_do_not_broaden_search(
    client, fragmentarium, bibliography_repository
):
    bibliography_repository.create(
        BibliographyEntryFactory.build(
            id="CANONICAL", aliases=[None, "invalid", {}, {"value": 7}]
        )
    )
    fragmentarium.create(build_fragment("X.1", ReferenceFactory.build(id="CANONICAL")))
    fragmentarium.create(build_fragment("X.2", ReferenceFactory.build(id="invalid")))
    result = client.simulate_get("/fragments/query", params={"bibId": "CANONICAL"})
    assert result.status == falcon.HTTP_OK
    assert [item["museumNumber"]["number"] for item in result.json["items"]] == ["1"]


def test_reverse_lookup_overflow_returns_no_partial_matches(
    client, bibliography_repository, monkeypatch
):
    monkeypatch.setattr(
        "ebl.bibliography.application.reference_search.MAX_REFERENCE_SEARCH_ENTRIES", 2
    )
    bibliography_repository.create(BibliographyEntryFactory.build(id="CANONICAL"))
    for index in range(3):
        bibliography_repository.create(
            BibliographyEntryFactory.build(
                id=f"OLD{index}", deprecated=True, redirectTo="CANONICAL"
            )
        )

    result = client.simulate_get(
        "/fragments/query", params={"bibId": "CANONICAL", "limit": "10"}
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert "items" not in result.json


def test_reverse_lookup_detects_a_graph_changed_during_search(
    client, bibliography_repository, monkeypatch
):
    canonical = BibliographyEntryFactory.build(id="CANONICAL")
    predecessor = BibliographyEntryFactory.build(
        id="OLD", deprecated=True, redirectTo="CANONICAL"
    )
    bibliography_repository.create(canonical)
    bibliography_repository.create(predecessor)

    def changed_incoming(id_, limit=None):
        if id_ == "CANONICAL":
            return [predecessor]
        return [{**canonical, "deprecated": True, "redirectTo": "OLD"}]

    monkeypatch.setattr(
        bibliography_repository, "query_by_redirect_target", changed_incoming
    )
    result = client.simulate_get(
        "/fragments/query", params={"bibId": "CANONICAL", "limit": "10"}
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert "items" not in result.json
